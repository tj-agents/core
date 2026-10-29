"""Validate Claude and Codex coverage records for agent behavior work."""

import argparse
import json
import re
from pathlib import Path


HOSTS = ("claude", "codex")
LEVELS = ("planned", "source", "installed")
RESULTS = ("pending", "passed", "limited")
PLACEHOLDERS = {"", "-", "...", "tbd", "todo", "pending", "n/a", "na", "none", "unknown"}
FENCE = re.compile(r"```agent-host-coverage[ \t]*\r?\n(.*?)\r?\n```", re.DOTALL)


def is_text(value):
    return isinstance(value, str) and value.strip() and value.strip().casefold() not in PLACEHOLDERS


def agent_surface_paths(paths):
    selected = []
    for value in paths:
        path = str(value).replace("\\", "/")
        if path.startswith("./"):
            path = path[2:]
        name = path.rsplit("/", 1)[-1]
        if path.startswith((".agents/", ".codex/", ".claude/", ".claude-plugin/", ".codex-plugin/", "plugins/")) or name in {"AGENTS.md", "CLAUDE.md", "SKILL.md"}:
            selected.append(path)
    return sorted(set(selected))


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key %s" % key)
        value[key] = item
    return value


def parse_records(text):
    records = []
    errors = []
    for index, match in enumerate(FENCE.finditer(text), start=1):
        try:
            records.append(json.loads(match.group(1), object_pairs_hook=unique_object))
        except (json.JSONDecodeError, ValueError) as error:
            errors.append("record %d is not valid JSON: %s" % (index, error))
    return records, errors


def validate_record(record, stage, expected_head=None):
    errors = []
    base_fields = {"schema_version", "shared_source", "hosts"}
    expected_fields = base_fields | ({"candidate_head"} if stage == "review" else set())
    if not isinstance(record, dict) or set(record) != expected_fields:
        return ["record has an invalid shape for its stage"]
    if type(record["schema_version"]) is not int or record["schema_version"] != 1:
        errors.append("schema_version must be 1")
    if not is_text(record["shared_source"]):
        errors.append("shared_source must be a non-placeholder string")
    if stage == "review":
        candidate_head = record["candidate_head"]
        if not isinstance(candidate_head, str) or not re.fullmatch(r"[0-9a-f]{40}", candidate_head):
            errors.append("candidate_head must be a full lowercase commit SHA")
        elif expected_head is not None and candidate_head != expected_head:
            errors.append("candidate_head does not match the frozen candidate")
    hosts = record["hosts"]
    if not isinstance(hosts, list) or len(hosts) != 2:
        return errors + ["hosts must contain exactly Claude and Codex"]
    seen = set()
    for entry in hosts:
        if not isinstance(entry, dict):
            errors.append("host entries must be objects")
            continue
        allowed = {"host", "behavior", "source", "mapping", "verification", "exception"}
        required = {"host", "behavior", "source", "mapping", "verification"}
        if set(entry) - allowed or not required.issubset(entry):
            errors.append("host entries have an invalid shape")
            continue
        host = entry["host"]
        if host not in HOSTS:
            errors.append("host must be claude or codex")
        elif host in seen:
            errors.append("host entries must not be duplicated")
        else:
            seen.add(host)
        for field in ("behavior", "source", "mapping"):
            if not is_text(entry[field]):
                errors.append("%s %s must be a non-placeholder string" % (host, field))
        verification = entry["verification"]
        if not isinstance(verification, dict) or set(verification) != {"level", "result", "evidence"}:
            errors.append("%s verification must contain only level, result, and evidence" % host)
            continue
        level = verification["level"]
        result = verification["result"]
        if level not in LEVELS:
            errors.append("%s verification level is invalid" % host)
        if result not in RESULTS:
            errors.append("%s verification result is invalid" % host)
        if not is_text(verification["evidence"]):
            errors.append("%s verification evidence must be a non-placeholder string" % host)
        if stage == "review" and (level == "planned" or result == "pending"):
            errors.append("%s review evidence must be source or installed and passed or limited" % host)
        exception = entry.get("exception")
        if result == "limited":
            if not isinstance(exception, dict) or set(exception) != {"constraint_evidence", "supported_other_host_outcome"}:
                errors.append("%s limited verification requires constraint evidence and the other host outcome" % host)
            elif not is_text(exception["constraint_evidence"]) or not is_text(exception["supported_other_host_outcome"]):
                errors.append("%s exception fields must be non-placeholder strings" % host)
        elif exception is not None:
            errors.append("%s exception is only valid for limited verification" % host)
    if seen != set(HOSTS):
        errors.append("hosts must contain one claude and one codex entry")
    return errors


def validate_documents(documents, stage, expected_head=None):
    if stage not in {"plan", "review"}:
        raise ValueError("stage must be plan or review")
    errors = []
    records = []
    for document in documents:
        path = Path(document)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append("cannot read %s: %s" % (path, error))
            continue
        parsed, parse_errors = parse_records(text)
        errors.extend("%s: %s" % (path, error) for error in parse_errors)
        records.extend((path, record) for record in parsed)
    if len(records) != 1:
        errors.append("exactly one agent-host-coverage record is required")
    for path, record in records:
        errors.extend("%s: %s" % (path, error) for error in validate_record(record, stage, expected_head))
    return {"stage": stage, "valid": not errors, "errors": errors, "record_count": len(records)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("plan", "review"), required=True)
    parser.add_argument("--document", type=Path, action="append", required=True)
    parser.add_argument("--expected-head")
    arguments = parser.parse_args(argv)
    result = validate_documents(arguments.document, arguments.stage, arguments.expected_head)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
