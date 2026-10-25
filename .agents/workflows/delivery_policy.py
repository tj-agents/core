import importlib.util
import json
import re
import sys
from pathlib import Path


AUTHORIZATION_KEYS = {
    "$comment",
    "standing_authorization",
    "instruction",
    "always_stop_paths",
    "hold_label",
    "authorized_stop_classes",
}


EXEMPTIBLE_STOP_CLASSES = frozenset(
    {
        "ci-workflow",
        "migration",
        "auth",
        "money",
        "published-contract",
    }
)


class PolicyViolation(ValueError):
    pass


def _configuration_reader():
    script = Path(__file__).resolve()
    candidates = (
        script.parents[1] / "resources" / "agent" / "runtime" / "repository_configuration.py",
        script.parents[2] / "dependencies" / "agent" / ".agents" / "agent" / "runtime" / "repository_configuration.py",
    )
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        raise PolicyViolation("the packaged Agent repository configuration runtime is unavailable")
    spec = importlib.util.spec_from_file_location("tj_agents_repository_configuration", path)
    if spec is None or spec.loader is None:
        raise PolicyViolation("repository settings reader is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate(policy):
    if not isinstance(policy, dict):
        raise PolicyViolation("standing authorization table must be an object")
    unknown = set(policy) - AUTHORIZATION_KEYS
    if unknown:
        raise PolicyViolation(f"standing authorization table has unknown keys {sorted(unknown)!r}")
    mode = policy.get("standing_authorization")
    if not isinstance(mode, str) or mode not in {"absent", "auto", "merge"}:
        raise PolicyViolation("standing authorization mode is invalid")
    instruction = policy.get("instruction")
    if mode == "absent":
        if instruction is not None:
            raise PolicyViolation("an absent standing authorization cannot carry an instruction")
    elif not isinstance(instruction, str) or not instruction.strip():
        raise PolicyViolation("a standing authorization requires its exact recorded instruction")
    declared = policy.get("always_stop_paths", [])
    if not isinstance(declared, list):
        raise PolicyViolation("`always_stop_paths` must be a list")
    for entry in declared:
        try:
            re.compile(entry)
        except (TypeError, re.error) as error:
            raise PolicyViolation(f"`always_stop_paths` entry {entry!r}: {error}") from error
    hold_label = policy.get("hold_label")
    if hold_label is not None and (not isinstance(hold_label, str) or not hold_label.strip()):
        raise PolicyViolation("`hold_label` must be a nonempty string when present")
    authorized_stop_classes = policy.get("authorized_stop_classes", [])
    if not isinstance(authorized_stop_classes, list):
        raise PolicyViolation("`authorized_stop_classes` must be a list")
    if any(not isinstance(name, str) for name in authorized_stop_classes):
        raise PolicyViolation("`authorized_stop_classes` entries must be strings")
    authorized_stop_classes = set(authorized_stop_classes)
    unknown_stop_classes = authorized_stop_classes - EXEMPTIBLE_STOP_CLASSES
    if unknown_stop_classes:
        raise PolicyViolation(
            "`authorized_stop_classes` has unknown classes "
            f"{sorted(unknown_stop_classes)!r}"
        )
    if len(authorized_stop_classes) != len(policy.get("authorized_stop_classes", [])):
        raise PolicyViolation("`authorized_stop_classes` entries must be unique")
    if authorized_stop_classes and mode not in {"auto", "merge"}:
        raise PolicyViolation(
            "`authorized_stop_classes` requires auto or merge standing authorization"
        )
    return policy


def load_policy(root):
    path = Path(root) / ".agents" / "delivery-authorization.json"
    try:
        path.lstat()
    except FileNotFoundError:
        return None
    except OSError as error:
        raise PolicyViolation(f"standing authorization could not be inspected: {error}") from error
    if path.is_symlink() or not path.is_file():
        raise PolicyViolation("standing authorization must be a regular file")
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise PolicyViolation(f"standing authorization could not be read: {error}") from error
    return validate(policy)


def auto_merge_preference(root):
    return _configuration_reader().auto_merge(root)
