import json
import math
import re
import stat
from pathlib import Path


SETTINGS_PATH = Path(".agents") / "settings.json"
NAMESPACE_NAME = re.compile(r"^[a-z][a-z0-9-]*$")


class ConfigurationViolation(ValueError):
    pass


def _redirected(path):
    attributes = getattr(path.lstat(), "st_file_attributes", 0)
    return path.is_symlink() or bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ConfigurationViolation(f"duplicate settings key {key!r}")
        value[key] = item
    return value


def _constant(value):
    raise ConfigurationViolation(f"settings contain invalid JSON constant {value!r}")


def _float(value):
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ConfigurationViolation("settings contain a non-finite number")
    return parsed


def load(root):
    root = Path(root)
    if not root.is_absolute():
        raise ConfigurationViolation("settings root must be absolute")
    agents = root / ".agents"
    try:
        agents.lstat()
    except FileNotFoundError:
        return None
    except OSError as error:
        raise ConfigurationViolation(f"settings directory could not be inspected: {error}") from error
    if _redirected(agents) or not agents.is_dir():
        raise ConfigurationViolation("settings directory must not be redirected")
    path = root / SETTINGS_PATH
    try:
        path.lstat()
    except FileNotFoundError:
        return None
    except OSError as error:
        raise ConfigurationViolation(f"settings could not be inspected: {error}") from error
    if _redirected(path) or not path.is_file():
        raise ConfigurationViolation("settings must be a regular file")
    try:
        parsed = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_object,
            parse_constant=_constant,
            parse_float=_float,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ConfigurationViolation) as error:
        raise ConfigurationViolation(f"settings could not be read: {error}") from error
    if not isinstance(parsed, dict):
        raise ConfigurationViolation("settings must be an object")
    configuration = parsed.get("configuration", {})
    if not isinstance(configuration, dict):
        raise ConfigurationViolation("settings configuration must be an object")
    for namespace, value in configuration.items():
        if not isinstance(namespace, str) or not NAMESPACE_NAME.fullmatch(namespace):
            raise ConfigurationViolation(f"settings namespace {namespace!r} is invalid")
        if not isinstance(value, dict):
            raise ConfigurationViolation(f"settings namespace {namespace!r} must be an object")
    return configuration


def auto_merge(root, legacy_policy):
    configuration = load(root)
    if configuration is None:
        return legacy_policy is not None and legacy_policy.get("auto_merge") is True
    core = configuration.get("core")
    if core is None:
        return False
    unknown = set(core) - {"auto_merge"}
    if unknown:
        raise ConfigurationViolation(f"core settings have unknown keys {sorted(unknown)!r}")
    if "auto_merge" not in core:
        return False
    if type(core["auto_merge"]) is not bool:
        raise ConfigurationViolation("core auto_merge must be a boolean")
    return core["auto_merge"]
