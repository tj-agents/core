"""Offline loader and schema checks for Unix shell option fixtures."""

import json
from pathlib import Path


FIXTURES = Path(__file__).parent
PROFILE_PATH = FIXTURES / "shell_option_profiles.json"
SOURCE_PATH = FIXTURES / "shell_profile_sources.json"
EXPECTED_COUNTS = {"bash": 105, "dash": 19, "zsh-name": 197, "zsh-letter": 73}
EXPECTED_GROUPS = {
    "bash-long": ("bash", "long option", "gnu-bash-5.2.37-shell", "flag"),
    "bash-long-value": ("bash", "long option", "gnu-bash-5.2.37-shell", "value"),
    "bash-o": ("bash", "set -o name", "gnu-bash-5.2.37-set", "name"),
    "bash-o-cygwin": ("bash", "set -o name", "gfw-bash-5.3.015-cygwin", "name"),
    "bash-O": ("bash", "shopt -O name", "gnu-bash-5.2.37-shopt", "name"),
    "bash-O-cygwin": ("bash", "shopt -O name", "gfw-bash-5.3.015-cygwin", "name"),
    "dash-upstream": ("dash", "named option", "dash-0.5.13.5-options", "name"),
    "dash-debian": ("dash", "named option", "debian-dash-0.5.12-2", "name"),
    "zsh-names": ("zsh", "named option or alias", "zsh-5.9-options", "name"),
    "zsh-native-letters": ("zsh", "signed native letter map", "zsh-5.9-init", "letter"),
    "zsh-sh-ksh-letters": ("zsh", "signed sh/ksh letter map", "zsh-5.9-init", "letter"),
}
EXPECTED_SOURCES = {
    "gnu-bash-5.2.37-shell": ("5.2.37", "https://ftp.gnu.org/gnu/bash/bash-5.2.37.tar.gz", "shell.c", "69a6622c9460b228632cf4deb57233e59159f2bac8a600baa3c1f72635fbeff0"),
    "gnu-bash-5.2.37-flags": ("5.2.37", "https://ftp.gnu.org/gnu/bash/bash-5.2.37.tar.gz", "flags.c", "62b377da2431b15843a4d13a2814b387eb95bed789e2a0c618efce7c1646719f"),
    "gnu-bash-5.2.37-set": ("5.2.37", "https://ftp.gnu.org/gnu/bash/bash-5.2.37.tar.gz", "builtins/set.def", "60cc498e28d4e9edd49a1415f1b5f92cfd326c6cb0d17d0d0827757f23580793"),
    "gnu-bash-5.2.37-shopt": ("5.2.37", "https://ftp.gnu.org/gnu/bash/bash-5.2.37.tar.gz", "builtins/shopt.def", "c1bb281be9ac815fce0ab20022689d8ca8702e63c0de2cae94ebc9b4e812d91d"),
    "gfw-bash-5.3.015-cygwin": ("5.3.015", "https://raw.githubusercontent.com/git-for-windows/MSYS2-packages/39014c49183d3635c93151c390604318d2655da1/bash/0001-bash-4.4-cygwin.patch", "0001-bash-4.4-cygwin.patch", "81f5fcb0990199e555f78ecf57dd6874d4b0ca781d4e7d26eac5a76ba729ac59"),
    "dash-0.5.13.5-options": ("v0.5.13.5", "https://kernel.googlesource.com/pub/scm/utils/dash/dash/+/refs/tags/v0.5.13.5/src/options.c", "src/options.c", "267289ec56fa51d6a21ec4b0eb91b1ebae66e9310007670d8eb6eef65b08fff4"),
    "debian-dash-0.5.12-2": ("0.5.12-2", "https://ftp.debian.org/debian/pool/main/d/dash/dash_0.5.12-2.debian.tar.xz", "derived src/options.c", "1824c933e413c5518d018b8d308bc5e49153fbbe59487a68a0545304c9dc26db"),
    "zsh-5.9-init": ("5.9", "https://raw.githubusercontent.com/zsh-users/zsh/zsh-5.9/Src/init.c", "Src/init.c", "cdbe96fe80e4c56af6101d2837ef1bdaab7f1aa79f0d61206081c82395e4ce12"),
    "zsh-5.9-options": ("5.9", "https://raw.githubusercontent.com/zsh-users/zsh/zsh-5.9/Src/options.c", "Src/options.c", "d3c5d5095922f5b42087e37512b6ae966b70dd32bc84926bd4a65d388cc85de0"),
}


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
    if set(sources) != set(EXPECTED_SOURCES):
        raise ValueError("source provenance is invalid")
    for source_id, expected in EXPECTED_SOURCES.items():
        source = sources[source_id]
        fields = ("edition", "url", "member", "sha256")
        if not isinstance(source, dict) or any(not isinstance(source.get(field), str) for field in fields):
            raise ValueError("source provenance is malformed")
        if tuple(source[field] for field in fields) != expected:
            raise ValueError("source provenance is invalid")
    seen_groups = set()
    for group in groups:
        required = {"id", "shell", "meaning", "source", "arity"}
        if not isinstance(group, dict) or required - group.keys():
            raise ValueError("profile group is malformed")
        if any(not isinstance(group[field], str) or not group[field] for field in required):
            raise ValueError("profile group is malformed")
        if group["id"] in seen_groups:
            raise ValueError("profile group identity or source is invalid")
        expected = EXPECTED_GROUPS.get(group["id"])
        if expected is None or tuple(group[field] for field in ("shell", "meaning", "source", "arity")) != expected:
            raise ValueError("profile group identity or source is invalid")
        seen_groups.add(group["id"])
        names = group.get("names", [])
        mapping = group.get("map", {})
        if not isinstance(names, list) or not all(isinstance(name, str) and name for name in names):
            raise ValueError("profile name is invalid")
        if not isinstance(mapping, dict):
            raise ValueError("letter map is invalid")
        if bool(names) == bool(mapping) or (group["arity"] == "letter") != bool(mapping) or len(names) != len(set(names)):
            raise ValueError("profile group must contain one unique record kind")
        if not all(isinstance(letter, str) and len(letter) == 1 and isinstance(signed, str) and signed for letter, signed in mapping.items()):
            raise ValueError("letter map is invalid")
        condition = group.get("condition")
        variants = group.get("variants", {})
        if condition is not None and (not isinstance(condition, str) or not condition):
            raise ValueError("profile condition is invalid")
        if not isinstance(variants, dict) or any(name not in names or not isinstance(value, str) or not value for name, value in variants.items()):
            raise ValueError("profile variants are invalid")
    if seen_groups != set(EXPECTED_GROUPS):
        raise ValueError("profile groups are incomplete")
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
