"""Validate and evaluate finite, source-owned selection profiles."""

import json
import math
import re
from pathlib import Path, PurePosixPath


MAX_DOCUMENT_BYTES = 1024 * 1024
_MISSING = object()
_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _keys(value, required, optional=()):
    _require(isinstance(value, dict), "metadata must be an object")
    _require(set(required) <= value.keys() and value.keys() <= set(required) | set(optional),
             "missing or unknown metadata keys")


def _equal(left, right):
    same_type = type(left) is type(right) or (
        type(left) in (int, float) and type(right) in (int, float))
    return same_type and left == right


def _scalar(value):
    return value is None or type(value) in (str, bool, int) or (
        type(value) is float and math.isfinite(value))


def _domain(values):
    _require(isinstance(values, list) and values and all(_scalar(v) for v in values),
             "domain must be a nonempty finite scalar list")


def _member(value, domain):
    return any(_equal(value, candidate) for candidate in domain)


def _relative(value):
    _require(isinstance(value, str) and value and "\\" not in value and ":" not in value,
             "path must be canonical and relative")
    path = PurePosixPath(value)
    _require(path.parts and not path.is_absolute() and str(path) == value and
             all(part not in (".", "..") for part in path.parts),
             "path must be canonical and relative")
    return path


def _path(value):
    _require(isinstance(value, list) and all(isinstance(v, str) and v for v in value),
             "JSON path must contain nonempty object keys")


def _valid(value, field):
    if field["type"] == "scalar":
        return _scalar(value) and _member(value, field["values"])
    return isinstance(value, list) and all(_scalar(v) and _member(v, field["members"]) for v in value)


def validate_metadata(metadata, owner_package, candidate_ids):
    """Bind metadata to a verified owner and its explicitly supplied candidate roster."""
    _keys(metadata, ("schema_version", "owner_package", "document", "markers",
                     "valid_profile_plugins", "forms"))
    _require(type(metadata["schema_version"]) is int and metadata["schema_version"] == 1,
             "unsupported schema_version")
    _require(isinstance(owner_package, str) and len(owner_package.split("/")) == 2 and
             all(_SLUG.fullmatch(v) for v in owner_package.split("/")), "invalid owner_package")
    _require(metadata["owner_package"] == owner_package, "owner_package mismatch")
    marketplace = owner_package.split("/")[0]
    candidates = set(candidate_ids)
    _require(owner_package in candidates, "owner_package is not a candidate")
    _relative(metadata["document"])

    def outputs(value, nonempty=False):
        _require(isinstance(value, list) and (value or not nonempty), "invalid plugin outputs")
        _require(all(isinstance(v, str) and _SLUG.fullmatch(v) and
                     marketplace + "/" + v in candidates for v in value),
                 "output must be an actual candidate in the owning marketplace")

    markers = metadata["markers"]
    _keys(markers, ("suffixes", "basenames", "plugins"))
    _require(isinstance(markers["suffixes"], list) and all(
        isinstance(v, str) and v.startswith(".") and len(v) > 1 and
        not any(c in v for c in "/\\:") for v in markers["suffixes"]), "invalid marker suffix")
    _require(isinstance(markers["basenames"], list) and all(
        isinstance(v, str) and v and v not in (".", "..") and
        not any(c in v for c in "/\\:") for v in markers["basenames"]), "invalid marker basename")
    outputs(markers["plugins"])
    outputs(metadata["valid_profile_plugins"])
    forms = metadata["forms"]
    _require(isinstance(forms, list) and forms, "forms must be a nonempty list")
    names = set()
    for form in forms:
        _keys(form, ("name", "select", "fields", "selection_groups"))
        name = form["name"]
        _require(isinstance(name, str) and name and name not in names, "invalid or duplicate form name")
        names.add(name)
        selector = form["select"]
        _keys(selector, ("path", "type"), ("values",))
        _path(selector["path"])
        _require(selector["type"] in ("object", "array", "scalar"), "unknown selector type")
        if "values" in selector:
            _require(selector["type"] == "scalar", "only scalar selectors have values")
            _domain(selector["values"])
        fields = form["fields"]
        _require(isinstance(fields, dict) and fields and all(isinstance(v, str) and v for v in fields),
                 "invalid fields")
        for field in fields.values():
            _require(isinstance(field, dict) and field.get("type") in ("scalar", "array"),
                     "unknown field type")
            domain_key = "values" if field["type"] == "scalar" else "members"
            _keys(field, ("path", "type", domain_key), ("default",))
            _path(field["path"])
            _domain(field[domain_key])
            if "default" in field:
                _require(_valid(field["default"], field), "default outside field domain")
        _require(isinstance(form["selection_groups"], list), "invalid selection_groups")
        for group in form["selection_groups"]:
            _keys(group, ("rules",))
            _require(isinstance(group["rules"], list), "invalid rules")
            for rule in group["rules"]:
                _require(isinstance(rule, dict), "invalid rule")
                operator = "equals" if "equals" in rule else "intersects"
                _keys(rule, ("field", operator, "plugins"))
                _require(isinstance(rule["field"], str) and rule["field"] in fields, "unknown rule field")
                field = fields[rule["field"]]
                if operator == "equals":
                    _require(field["type"] == "scalar" and _valid(rule[operator], field),
                             "equals must use a declared scalar")
                else:
                    _domain(rule[operator])
                    _require(field["type"] == "array" and _valid(rule[operator], field),
                             "intersects must use declared array members")
                outputs(rule["plugins"], True)
    return metadata


def _resolve(value, path):
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return _MISSING
        value = value[key]
    return value


def _read_document(root, relative):
    root = Path(root).resolve(strict=True)
    _require(root.is_dir(), "scope root must be a directory")
    target = root.joinpath(*_relative(relative).parts)
    _require(target.resolve().is_relative_to(root), "document escapes scope root")
    if not target.exists():
        return None
    _require(target.is_file(), "document must be a file")
    with target.open("rb") as stream:
        data = stream.read(MAX_DOCUMENT_BYTES + 1)
    _require(len(data) <= MAX_DOCUMENT_BYTES, "document exceeds 1 MiB")
    value = json.loads(data.decode("utf-8"), parse_constant=lambda v: (_require(False, "nonfinite JSON number")))
    _require(isinstance(value, dict), "document must be a JSON object")
    return value


def evaluate(metadata, owner_package, candidate_ids, scope_root, filenames):
    """Evaluate against an explicit root and a complete list of relative filenames."""
    validate_metadata(metadata, owner_package, candidate_ids)
    filenames = sorted({_relative(v).as_posix() for v in filenames})
    markers = metadata["markers"]
    matches = [v for v in filenames if PurePosixPath(v).name in markers["basenames"] or
               any(PurePosixPath(v).name.lower().endswith(s.lower()) for s in markers["suffixes"])]
    selected = set(markers["plugins"] if matches else [])
    result = {"selected_ids": [], "marker_matches": matches, "selected_form": None,
              "fields": {}, "matched_rules": [], "diagnostics": []}
    try:
        document = _read_document(scope_root, metadata["document"])
        if document is not None:
            for form in metadata["forms"]:
                selector = form["select"]
                value = _resolve(document, selector["path"])
                kind = selector["type"]
                if value is _MISSING or not (isinstance(value, dict) if kind == "object" else
                    isinstance(value, list) if kind == "array" else _scalar(value)):
                    continue
                if "values" in selector and not _member(value, selector["values"]):
                    continue
                result["selected_form"] = form["name"]
                values = {}
                for name, field in form["fields"].items():
                    field_value = _resolve(value, field["path"])
                    if field_value is _MISSING:
                        field_value = field.get("default", _MISSING)
                    _require(_valid(field_value, field), f"form {form['name']}: invalid field {name}")
                    values[name] = field_value
                result["fields"] = values
                selected.update(metadata["valid_profile_plugins"])
                for index, group in enumerate(form["selection_groups"]):
                    for rule_index, rule in enumerate(group["rules"]):
                        field_value = values[rule["field"]]
                        matched = _equal(field_value, rule["equals"]) if "equals" in rule else any(
                            _member(v, rule["intersects"]) for v in field_value)
                        if matched:
                            selected.update(rule["plugins"])
                            result["matched_rules"].append([index, rule_index])
                            break
                break
    except (OSError, ValueError, UnicodeError, RecursionError, RuntimeError) as exc:
        result["diagnostics"].append(str(exc))
    marketplace = owner_package.split("/")[0]
    result["selected_ids"] = sorted(marketplace + "/" + v for v in selected)
    return result
