import json
import math
import re
from pathlib import Path


CONFIGURATION_PATH = Path(".agents") / "configuration.json"
NAMESPACE_NAME = re.compile(r"^[a-z][a-z0-9-]*$")


class ConfigurationViolation(ValueError):
    pass


def _object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ConfigurationViolation(f"duplicate configuration key {key!r}")
        value[key] = item
    return value


def _constant(value):
    raise ConfigurationViolation(f"configuration contains invalid JSON constant {value!r}")


def _float(value):
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ConfigurationViolation("configuration contains a non-finite number")
    return parsed


def load(root):
    root = Path(root)
    if not root.is_absolute():
        raise ConfigurationViolation("configuration root must be absolute")
    path = root / CONFIGURATION_PATH
    try:
        path.lstat()
    except FileNotFoundError:
        return None
    except OSError as error:
        raise ConfigurationViolation(f"configuration could not be inspected: {error}") from error
    if path.is_symlink() or not path.is_file():
        raise ConfigurationViolation("configuration must be a regular file")
    try:
        parsed = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_object,
            parse_constant=_constant,
            parse_float=_float,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ConfigurationViolation) as error:
        raise ConfigurationViolation(f"configuration could not be read: {error}") from error
    if not isinstance(parsed, dict) or set(parsed) != {"schema_version", "configuration"}:
        raise ConfigurationViolation("configuration requires exactly schema_version and configuration")
    if type(parsed["schema_version"]) is not int or parsed["schema_version"] != 1:
        raise ConfigurationViolation("configuration schema_version must be integer 1")
    configuration = parsed["configuration"]
    if not isinstance(configuration, dict):
        raise ConfigurationViolation("configuration must be an object")
    for namespace, value in configuration.items():
        if not isinstance(namespace, str) or not NAMESPACE_NAME.fullmatch(namespace):
            raise ConfigurationViolation(f"configuration namespace {namespace!r} is invalid")
        if not isinstance(value, dict):
            raise ConfigurationViolation(f"configuration namespace {namespace!r} must be an object")
    return configuration


def auto_merge(root, legacy_policy):
    configuration = load(root)
    if configuration is None:
        return legacy_policy.get("auto_merge", False)
    core = configuration.get("core")
    if core is None:
        return False
    unknown = set(core) - {"auto_merge"}
    if unknown:
        raise ConfigurationViolation(f"core configuration has unknown keys {sorted(unknown)!r}")
    if "auto_merge" not in core:
        return False
    if type(core["auto_merge"]) is not bool:
        raise ConfigurationViolation("core auto_merge must be a boolean")
    return core["auto_merge"]
