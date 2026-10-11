import re


AUTHORIZATION_KEYS = {
    "$comment",
    "standing_authorization",
    "instruction",
    "always_stop_paths",
    "hold_label",
    "authorized_stop_classes",
    "auto_merge",
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


def validate(policy):
    if not isinstance(policy, dict):
        raise PolicyViolation("standing authorization table must be an object")
    unknown = set(policy) - AUTHORIZATION_KEYS
    if unknown:
        raise PolicyViolation(f"standing authorization table has unknown keys {sorted(unknown)!r}")
    mode = policy.get("standing_authorization")
    if mode not in {"absent", "auto", "merge"}:
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
    if "auto_merge" in policy and type(policy["auto_merge"]) is not bool:
        raise PolicyViolation("`auto_merge` must be a boolean when present")
    return policy
