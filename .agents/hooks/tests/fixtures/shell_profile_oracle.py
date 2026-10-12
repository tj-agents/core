"""Offline loader and schema checks for shell option fixtures."""

import json
from pathlib import Path


FIXTURES = Path(__file__).parent
PROFILE_PATH = FIXTURES / "shell_option_profiles.json"
SOURCE_PATH = FIXTURES / "shell_profile_sources.json"
EXPECTED_COUNTS = {
    "bash": 105,
    "dash": 19,
    "zsh-name": 197,
    "zsh-letter": 73,
    "powershell": 42,
}
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
    "powershell-descriptors": (
        "powershell",
        "ordered command-line descriptor",
        "pwsh-7.6.0-parser",
        "descriptor",
    ),
}
EXPECTED_SOURCES = {
    "gnu-bash-5.2.37-shell": (
        "5.2.37",
        "https://ftp.gnu.org/gnu/bash/bash-5.2.37.tar.gz",
        "shell.c",
        "69a6622c9460b228632cf4deb57233e59159f2bac8a600baa3c1f72635fbeff0",
    ),
    "gnu-bash-5.2.37-flags": (
        "5.2.37",
        "https://ftp.gnu.org/gnu/bash/bash-5.2.37.tar.gz",
        "flags.c",
        "62b377da2431b15843a4d13a2814b387eb95bed789e2a0c618efce7c1646719f",
    ),
    "gnu-bash-5.2.37-set": (
        "5.2.37",
        "https://ftp.gnu.org/gnu/bash/bash-5.2.37.tar.gz",
        "builtins/set.def",
        "60cc498e28d4e9edd49a1415f1b5f92cfd326c6cb0d17d0d0827757f23580793",
    ),
    "gnu-bash-5.2.37-shopt": (
        "5.2.37",
        "https://ftp.gnu.org/gnu/bash/bash-5.2.37.tar.gz",
        "builtins/shopt.def",
        "c1bb281be9ac815fce0ab20022689d8ca8702e63c0de2cae94ebc9b4e812d91d",
    ),
    "gfw-bash-5.3.015-cygwin": (
        "5.3.015",
        "https://raw.githubusercontent.com/git-for-windows/MSYS2-packages/39014c49183d3635c93151c390604318d2655da1/bash/0001-bash-4.4-cygwin.patch",
        "0001-bash-4.4-cygwin.patch",
        "81f5fcb0990199e555f78ecf57dd6874d4b0ca781d4e7d26eac5a76ba729ac59",
    ),
    "dash-0.5.13.5-options": (
        "v0.5.13.5",
        "https://kernel.googlesource.com/pub/scm/utils/dash/dash/+/refs/tags/v0.5.13.5/src/options.c",
        "src/options.c",
        "267289ec56fa51d6a21ec4b0eb91b1ebae66e9310007670d8eb6eef65b08fff4",
    ),
    "debian-dash-0.5.12-2": (
        "0.5.12-2",
        "https://ftp.debian.org/debian/pool/main/d/dash/dash_0.5.12-2.debian.tar.xz",
        "derived src/options.c",
        "1824c933e413c5518d018b8d308bc5e49153fbbe59487a68a0545304c9dc26db",
    ),
    "zsh-5.9-init": (
        "5.9",
        "https://raw.githubusercontent.com/zsh-users/zsh/zsh-5.9/Src/init.c",
        "Src/init.c",
        "cdbe96fe80e4c56af6101d2837ef1bdaab7f1aa79f0d61206081c82395e4ce12",
    ),
    "zsh-5.9-options": (
        "5.9",
        "https://raw.githubusercontent.com/zsh-users/zsh/zsh-5.9/Src/options.c",
        "Src/options.c",
        "d3c5d5095922f5b42087e37512b6ae966b70dd32bc84926bd4a65d388cc85de0",
    ),
    "pwsh-7.6.0-parser": (
        "v7.6.0",
        "https://raw.githubusercontent.com/PowerShell/PowerShell/v7.6.0/src/Microsoft.PowerShell.ConsoleHost/host/msh/CommandLineParameterParser.cs",
        "src/Microsoft.PowerShell.ConsoleHost/host/msh/CommandLineParameterParser.cs",
        "a7fc6b5c391bb8cbd06b78edd6e3b9867f3b89c1e634a610e7eddc7086a49783",
    ),
    "windows-powershell-5.1-cli-doc": (
        "5.1",
        "https://raw.githubusercontent.com/MicrosoftDocs/PowerShell-Docs/f09ce0b678c2da1ae0fa70f0b4789a607183cc63/reference/5.1/Microsoft.PowerShell.Core/About/about_PowerShell_exe.md",
        "about_powershell_exe-5.1-f09ce0.md",
        "cdbaa30b2186ebedf4c78e21c529f2691c2bedf105faa7ebe7f420c2b6b1e4da",
    ),
    "pwsh-7.5-cli-doc": (
        "7.5",
        "https://raw.githubusercontent.com/MicrosoftDocs/PowerShell-Docs/9fc54e7fc4954f7b4af134def74ba8e8cac7e23c/reference/7.5/Microsoft.PowerShell.Core/About/about_Pwsh.md",
        "about_pwsh-7.5-9fc54e.md",
        "6237731762df03b74e9768c30a228d9f03ab6ba98c39b03d6635e7e237cc3bb2",
    ),
}
EXPECTED_SOURCE_METADATA = {
    "gfw-bash-5.3.015-cygwin": {
        "condition": "__CYGWIN__",
        "derivation": "separate vendor variant; no installed-5.2.37 equivalence",
    },
    "debian-dash-0.5.12-2": {
        "derivation": "zero-offset application of the documented Debian quilt series",
    },
    "pwsh-7.6.0-parser": {
        "byte_form": "UTF-8 no BOM; existing CRLF cache",
        "normalized_lf_sha256": "abf566b2768f65586cab9e77cb0330fb8926950c9e7720b46f0fc0a69ebed6fe",
        "resolved_commit": None,
        "provenance": "Existing attributed cache, v7.6.0 tag not resolved/verified; no5.1 parser equivalence.",
        "locations": {
            "normalization": [709, 737],
            "matching": [797, 805],
            "descriptors": [901, 1246],
            "policy_enum": [756, 792],
            "format_enum": [1293, 1325],
            "file": [1344, 1435],
            "command": [1493, 1554],
        },
    },
    "windows-powershell-5.1-cli-doc": {
        "revision": "f09ce0b678c2da1ae0fa70f0b4789a607183cc63",
        "ms_date": "2024-07-23T00:00:00Z",
        "updated_at": "2025-09-29T22:08:00Z",
        "observed_utc": "2026-10-11T11:52:12.832991+00:00",
        "locations": [[25, 267, 269, 270, 271, 272], [112, 148], [193, 218], [219, 253], [255, 259], [275, 290]],
    },
    "pwsh-7.5-cli-doc": {
        "revision": "9fc54e7fc4954f7b4af134def74ba8e8cac7e23c",
        "ms_date": "2026-01-18T00:00:00Z",
        "updated_at": "2026-04-08T22:08:00Z",
        "observed_utc": "2026-10-11T11:52:12.838975+00:00",
        "locations": [[59, 61, 62, 64, 65, 68, 69, 70], [128, 131, 159, 160, 161], [209, 211, 212, 214, 215, 217, 218], [410, 412, 413], [295, 307], [377, 380], [415, 419]],
    },
}
EXPECTED_POWERSHELL_DESCRIPTORS = [
    ("version", "v", 0, "exit"), ("help", "h", 0, "exit"), ("?", "?", 0, "exit"),
    ("login", "l", 0, "continue"), ("noexit", "noe", 0, "continue"),
    ("noprofile", "nop", 0, "continue"), ("nologo", "nol", 0, "continue"),
    ("noninteractive", "noni", 0, "continue"), ("socketservermode", "so", 0, "opaque"),
    ("v2socketservermode", "v2so", 0, "opaque"), ("servermode", "s", 0, "opaque"),
    ("namedpipeservermode", "nam", 0, "opaque"), ("sshservermode", "sshs", 0, "opaque"),
    ("noprofileloadtime", "noprofileloadtime", 0, "continue"), ("interactive", "i", 0, "continue"),
    ("configurationfile", "configurationfile", 1, "continue"), ("configurationname", "config", 1, "continue"),
    ("custompipename", "cus", 1, "continue"), ("commandwithargs", "commandwithargs", 1, "cwa"),
    ("cwa", "cwa", 1, "cwa"), ("command", "c", "remainder", "command"),
    ("windowstyle", "w", 1, "continue"), ("file", "f", 1, "file"), ("isswait", "isswait", 0, "continue"),
    ("outputformat", "o", 1, "continue"), ("of", "o", 1, "continue"),
    ("inputformat", "inp", 1, "continue"), ("if", "if", 1, "continue"),
    ("executionpolicy", "ex", 1, "continue"), ("ep", "ep", 1, "continue"),
    ("encodedcommand", "e", 1, "opaque"), ("ec", "e", 1, "opaque"),
    ("encodedarguments", "encodeda", 1, "continue"), ("ea", "ea", 1, "continue"),
    ("settingsfile", "settings", 1, "continue"), ("sta", "sta", 0, "continue"),
    ("mta", "mta", 0, "continue"), ("workingdirectory", "wo", 1, "continue"),
    ("wd", "wd", 1, "continue"),
    ("removeworkingdirectorytrailingcharacter", "removeworkingdirectorytrailingcharacter", 0, "continue"),
    ("token", "to", 1, "continue"), ("utctimestamp", "utc", 1, "continue"),
]
EXPECTED_POWERSHELL_ALIASES = {
    "?": "help",
    "cwa": "commandwithargs",
    "of": "outputformat",
    "if": "inputformat",
    "ep": "executionpolicy",
    "ec": "encodedcommand",
    "ea": "encodedarguments",
    "wd": "workingdirectory",
}
EXPECTED_POWERSHELL_SOURCE_LINES = {
    "version": 901, "help": 912, "?": 912, "login": 919, "noexit": 925,
    "noprofile": 931, "nologo": 936, "noninteractive": 941, "socketservermode": 946,
    "v2socketservermode": 953, "servermode": 960, "namedpipeservermode": 966,
    "sshservermode": 972, "noprofileloadtime": 978, "interactive": 983,
    "configurationfile": 988, "configurationname": 1001, "custompipename": 1014,
    "commandwithargs": 1041, "cwa": 1041, "command": 1054, "windowstyle": 1063,
    "file": 1092, "isswait": 1102, "outputformat": 1107, "of": 1107,
    "inputformat": 1113, "if": 1113, "executionpolicy": 1118, "ep": 1118,
    "encodedcommand": 1133, "ec": 1133, "encodedarguments": 1143, "ea": 1143,
    "settingsfile": 1152, "sta": 1162, "mta": 1182, "workingdirectory": 1202,
    "wd": 1202, "removeworkingdirectorytrailingcharacter": 1216, "token": 1220,
    "utctimestamp": 1235,
}
EXPECTED_POWERSHELL_CONDITIONS = {
    "v2socketservermode": ["!UNIX"],
    "isswait": ["DEBUG"],
    "removeworkingdirectorytrailingcharacter": ["!UNIX"],
    "token": ["!UNIX"],
    "utctimestamp": ["!UNIX"],
}
EXPECTED_WINDOWS_COMMON_NAMES = [
    "help", "?", "noexit", "noprofile", "nologo", "noninteractive",
    "configurationname", "command", "windowstyle", "file", "outputformat", "of",
    "inputformat", "if", "executionpolicy", "ep", "encodedcommand", "ec",
    "encodedarguments", "ea", "sta", "mta",
]
EXPECTED_WINDOWS_EXTRA = [{
    "name": "psconsolefile",
    "minimum_prefix": "psconsolefile",
    "arity": 1,
    "action": "continue",
    "source": "windows-powershell-5.1-cli-doc",
}]
EXPECTED_WINDOWS_OVERRIDES = {
    "version": {
        "minimum_prefix": "v",
        "arity": 1,
        "action": "continue",
        "source": "windows-powershell-5.1-cli-doc",
    }
}
EXPECTED_POWERSHELL_ENUMS = {
    "executionpolicy": ["default", "remotesigned", "bypass", "allsigned", "restricted", "unrestricted", "undefined"],
    "inputformat": ["text", "xml"],
    "outputformat": ["text", "xml"],
    "windowstyle": ["normal", "minimized", "maximized", "hidden"],
}


def load_json(path):
    with path.open(encoding="utf-8") as fixture:
        return json.load(fixture)


def load_oracle():
    return load_json(PROFILE_PATH), load_json(SOURCE_PATH)


def _powershell_group(profiles):
    return next(group for group in profiles["groups"] if group["id"] == "powershell-descriptors")


def _descriptor_records(group):
    for descriptor in group["descriptors"]:
        name = descriptor["name"]
        canonical_name = group["aliases"].get(name, name)
        record = {
            "id": f"pwsh:{name}",
            "group": group["id"],
            "shell": group["shell"],
            "meaning": group["meaning"],
            "source": group["source"],
            "name": name,
            "minimum_prefix": descriptor["minimum_prefix"],
            "arity": descriptor["arity"],
            "action": descriptor["action"],
            "source_line": group["source_lines"][name],
            "condition": group["conditions"].get(name),
            "canonical_name": canonical_name,
        }
        if canonical_name in group["enums"]:
            record["enum"] = canonical_name
        yield record


def iter_powershell_descriptors(profiles, profile="pwsh"):
    group = _powershell_group(profiles)
    records = list(_descriptor_records(group))
    if profile == "pwsh":
        yield from records
        return
    if profile != "windows":
        raise ValueError("PowerShell profile is invalid")
    allowed = set(group["windows_common_names"]) | set(group["windows_overrides"])
    for record in records:
        if record["name"] not in allowed:
            continue
        override = group["windows_overrides"].get(record["name"])
        if override is not None:
            record = {**record, **override}
            record.pop("source_line", None)
        yield record
    for descriptor in group["windows_extra"]:
        yield {
            "id": f"powershell:{descriptor['name']}",
            "group": group["id"],
            "shell": "powershell",
            "meaning": group["meaning"],
            "canonical_name": descriptor["name"],
            **descriptor,
        }


def resolve_powershell_prefix(profiles, supplied, profile="pwsh"):
    if not isinstance(supplied, str):
        raise ValueError("PowerShell prefix is invalid")
    normalized = supplied.casefold()
    for descriptor in iter_powershell_descriptors(profiles, profile):
        if len(normalized) >= len(descriptor["minimum_prefix"]) and descriptor["name"].casefold().startswith(normalized):
            return descriptor
    return None


def records(profiles):
    for group in profiles["groups"]:
        if group["id"] == "powershell-descriptors":
            yield from _descriptor_records(group)
            continue
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


def _validate_sources(sources):
    if set(sources) != set(EXPECTED_SOURCES):
        raise ValueError("source provenance is invalid")
    fields = ("edition", "url", "member", "sha256")
    for source_id, expected in EXPECTED_SOURCES.items():
        source = sources[source_id]
        expected_source = dict(zip(fields, expected))
        expected_source.update(EXPECTED_SOURCE_METADATA.get(source_id, {}))
        if source != expected_source:
            raise ValueError("source provenance is invalid")


def _validate_powershell_group(group):
    descriptors = group.get("descriptors")
    if not isinstance(descriptors, list):
        raise ValueError("PowerShell descriptors are invalid")
    actual = []
    for descriptor in descriptors:
        if not isinstance(descriptor, dict) or set(descriptor) != {"name", "minimum_prefix", "arity", "action"}:
            raise ValueError("PowerShell descriptor is invalid")
        if not isinstance(descriptor["name"], str) or not descriptor["name"]:
            raise ValueError("PowerShell descriptor is invalid")
        if not isinstance(descriptor["minimum_prefix"], str) or not descriptor["minimum_prefix"]:
            raise ValueError("PowerShell descriptor is invalid")
        if type(descriptor["arity"]) not in (int, str) or descriptor["arity"] not in (0, 1, "remainder"):
            raise ValueError("PowerShell descriptor is invalid")
        if descriptor["action"] not in {"exit", "continue", "opaque", "cwa", "command", "file"}:
            raise ValueError("PowerShell descriptor is invalid")
        actual.append((descriptor["name"], descriptor["minimum_prefix"], descriptor["arity"], descriptor["action"]))
    if actual != EXPECTED_POWERSHELL_DESCRIPTORS:
        raise ValueError("PowerShell descriptors are invalid")
    if group.get("aliases") != EXPECTED_POWERSHELL_ALIASES:
        raise ValueError("PowerShell aliases are invalid")
    if group.get("source_lines") != EXPECTED_POWERSHELL_SOURCE_LINES:
        raise ValueError("PowerShell source locations are invalid")
    if group.get("conditions") != EXPECTED_POWERSHELL_CONDITIONS:
        raise ValueError("PowerShell conditions are invalid")
    if group.get("windows_common_names") != EXPECTED_WINDOWS_COMMON_NAMES:
        raise ValueError("Windows PowerShell projection is invalid")
    if group.get("windows_extra") != EXPECTED_WINDOWS_EXTRA:
        raise ValueError("Windows PowerShell projection is invalid")
    if group.get("windows_overrides") != EXPECTED_WINDOWS_OVERRIDES:
        raise ValueError("Windows PowerShell projection is invalid")
    if group.get("enums") != EXPECTED_POWERSHELL_ENUMS:
        raise ValueError("PowerShell enums are invalid")
    by_name = {descriptor[0]: descriptor[1:] for descriptor in actual}
    for alias, canonical in group["aliases"].items():
        if by_name[alias][1:] != by_name[canonical][1:]:
            raise ValueError("PowerShell aliases are invalid")


def validate(profiles, source_data):
    if not isinstance(profiles, dict) or not isinstance(source_data, dict):
        raise ValueError("fixture roots must be objects")
    sources = source_data.get("sources")
    groups = profiles.get("groups")
    if not isinstance(sources, dict) or not isinstance(groups, list):
        raise ValueError("fixture containers are malformed")
    _validate_sources(sources)
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
        if group["id"] == "powershell-descriptors":
            _validate_powershell_group(group)
            continue
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
        elif record["shell"] == "powershell":
            counts["powershell"] += 1
        elif record["meaning"] in {"signed native letter map", "signed sh/ksh letter map"}:
            counts["zsh-letter"] += 1
        else:
            counts["zsh-name"] += 1
    return counts
