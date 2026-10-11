"""Offline loader and schema checks for Unix shell option fixtures."""

import json
from pathlib import Path


FIXTURES = Path(__file__).parent
PROFILE_PATH = FIXTURES / "shell_option_profiles.json"
SOURCE_PATH = FIXTURES / "shell_profile_sources.json"
EXPECTED_COUNTS = {"bash": 105, "dash": 19, "zsh-name": 197, "zsh-letter": 73}


def load_json(path):
    with path.open(encoding="utf-8") as fixture:
        return json.load(fixture)


def load_oracle():
    return load_json(PROFILE_PATH), load_json(SOURCE_PATH)


def records(profiles):
    for group in profiles["groups"]:
        source = group["source"]
        for name in group.get("names", []):
            yield {
                "id": f"{group['id']}:{name}",
                "group": group["id"],
                "shell": group["shell"],
                "meaning": group["meaning"],
                "source": source,
                "name": name,
                "condition": group.get("variants", {}).get(name, group.get("condition")),
            }
        for letter, signed_option in group.get("map", {}).items():
            yield {
                "id": f"{group['id']}:{letter}",
                "group": group["id"],
                "shell": group["shell"],
                "meaning": group["meaning"],
                "source": source,
                "letter": letter,
                "signed_option": signed_option,
            }


def validate(profiles, source_data):
    if not isinstance(profiles, dict) or not isinstance(source_data, dict):
        raise ValueError("fixture roots must be objects")
    sources = source_data.get("sources")
    groups = profiles.get("groups")
    if not isinstance(sources, dict) or not isinstance(groups, list):
        raise ValueError("fixture containers are malformed")
    seen_groups = set()
    for group in groups:
        required = {"id", "shell", "meaning", "source", "arity"}
        if not isinstance(group, dict) or required - group.keys():
            raise ValueError("profile group is malformed")
        if group["id"] in seen_groups or group["source"] not in sources:
            raise ValueError("profile group identity or source is invalid")
        seen_groups.add(group["id"])
        names = group.get("names", [])
        mapping = group.get("map", {})
        if bool(names) == bool(mapping) or len(names) != len(set(names)):
            raise ValueError("profile group must contain one unique record kind")
        if not all(isinstance(name, str) and name for name in names):
            raise ValueError("profile name is invalid")
        if not all(len(letter) == 1 and signed for letter, signed in mapping.items()):
            raise ValueError("letter map is invalid")
    expanded = list(records(profiles))
    ids = [record["id"] for record in expanded]
    if len(ids) != len(set(ids)):
        raise ValueError("record IDs are not unique")
    return expanded


def count_records(records_to_count):
    counts = {key: 0 for key in EXPECTED_COUNTS}
    for record in records_to_count:
        if record["shell"] == "bash":
            counts["bash"] += 1
        elif record["shell"] == "dash":
            counts["dash"] += 1
        elif record["meaning"] == "signed native letter map" or record["meaning"] == "signed sh/ksh letter map":
            counts["zsh-letter"] += 1
        else:
            counts["zsh-name"] += 1
    return counts
