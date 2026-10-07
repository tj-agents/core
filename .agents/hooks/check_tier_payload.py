r"""Enforce the canonical built-payload shape every tier repository must ship.

The review and the tier gate both read installed payloads, so their shape is a cross-repository
contract: `tier.json` beside flat `skills/<name>/SKILL.md` bodies whose front matter carries the
`kind:` marker, indexed by `INDEX.md` and `selection.json`. A repo that drifts from this ships
standards the gate cannot gate and conventions the review cannot find - silently. So each tier
repository runs this check in its own CI against its generated `plugins/` output and fails loudly.

Checks, per payload named in `.agents/plugins/payloads.json` — or, for a repository authored directly
as its payloads with no generator and no payloads.json, per directory found under `plugins/`:

- the payload directory exists, and no undeclared directory sits in `plugins/` (stale generator
  output looks exactly like a real plugin to an installer);
- `tier.json` exists and satisfies the shipped schema contract - a payload without one is a tier
  the gate can never see, which is how `cpp` spent a year ungated;
- every `skills/*/SKILL.md` has front matter whose `name:` matches its directory and whose `kind:`
  is one lowercase word (the taxonomy is open; the shape is not);
- `INDEX.md` lists exactly the skills that exist;
- `selection.json` parses and names only skills that exist.

Exit 0 when everything holds; exit 1 with one line per violation. No dependencies beyond stdlib,
so any repo's CI can run it straight from the installed base plugin or a checkout of core.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import runpy
import sys


PAYLOADS_FILE = Path(".agents") / "plugins" / "payloads.json"
PLUGINS_DIR = "plugins"
TIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
KIND_PATTERN = re.compile(r"[a-z]+")
OWNER_PATTERN = re.compile(r"^[^/ ]+/[^/ ]+$")
FRONT_FIELD = r"^{0}:[ \t]*(\S[^\r\n]*?)[ \t]*$"
INDEX_ENTRY = re.compile(r"^- `([^`]+)`", re.MULTILINE)
SCHEMA_VERSIONS = (1, 2, 3)
IGNORED_PAYLOAD_ENTRIES = {".gitkeep"}


def front_matter(text):
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[:end] if end != -1 else ""


def front_field(block, field):
    match = re.search(FRONT_FIELD.format(field), block, re.MULTILINE)
    return match.group(1) if match else None


def check_tier_declaration(payload, problems):
    path = payload / "tier.json"
    if not path.is_file():
        problems.append(f"{payload.name}: no tier.json - the gate cannot see this plugin anywhere")
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, ValueError) as error:
        problems.append(f"{payload.name}: tier.json is unreadable: {error}")
        return
    if not isinstance(data, dict):
        problems.append(f"{payload.name}: tier.json is not an object")
        return

    if data.get("schema_version") not in SCHEMA_VERSIONS:
        problems.append(f"{payload.name}: tier.json schema_version must be one of {SCHEMA_VERSIONS}")
    tier = data.get("tier")
    if not isinstance(tier, str) or not TIER_PATTERN.match(tier):
        problems.append(f"{payload.name}: tier.json tier must match {TIER_PATTERN.pattern}")
    applies = data.get("applies")
    if applies not in ("always", "stack-present"):
        problems.append(f"{payload.name}: tier.json applies must be 'always' or 'stack-present'")

    owner = data.get("owner_repository")
    owners = [owner] if isinstance(owner, str) else owner if isinstance(owner, list) else []
    if owner is not None and not isinstance(owner, (str, list)):
        problems.append(f"{payload.name}: tier.json owner_repository must be a string or list")
    for name in owners:
        if not isinstance(name, str) or not OWNER_PATTERN.match(name):
            problems.append(f"{payload.name}: tier.json owner_repository entry {name!r} is not owner/name")

    detect = data.get("detect")
    if data.get("schema_version") == 3:
        validator = runpy.run_path(str(Path(__file__).with_name("tier_gate.py")))["v3_declaration_diagnostics"]
        problems.extend(f"{payload.name}: {item['path']}: {item['message']}"
                        for item in validator(data, payload_dir=payload))
        return
    for field in ("employer", "session_context"):
        if field in data:
            problems.append(f"{payload.name}: tier.json {field} requires schema_version 3")
    if applies == "stack-present":
        if not isinstance(detect, dict) or not any(detect.get(key) for key in ("files", "globs", "content", "remote")):
            problems.append(f"{payload.name}: tier.json applies=stack-present but detect has no matcher")
    if isinstance(detect, dict):
        unknown = set(detect) - {"files", "globs", "content", "remote"}
        if unknown:
            problems.append(f"{payload.name}: tier.json detect has unknown matcher(s) {sorted(unknown)}")
        for key in ("files", "globs"):
            for value in detect.get(key) or []:
                if not isinstance(value, str) or not value:
                    problems.append(f"{payload.name}: tier.json detect.{key} entry {value!r} is not a non-empty string")
        for value in detect.get("remote") or []:
            if not isinstance(value, str) or not value:
                problems.append(f"{payload.name}: tier.json detect.remote entry {value!r} is not a non-empty string")
                continue
            try:
                re.compile(value)
            except re.error as error:
                problems.append(f"{payload.name}: tier.json detect.remote pattern {value!r} does not compile: {error}")
        if detect.get("remote") and data.get("schema_version") == 1:
            problems.append(f"{payload.name}: tier.json uses detect.remote but declares schema_version 1")
        for rule in detect.get("content") or []:
            if not isinstance(rule, dict) or not rule.get("glob") or not rule.get("pattern"):
                problems.append(f"{payload.name}: tier.json detect.content entry needs glob and pattern")
                continue
            try:
                re.compile(rule["pattern"])
            except re.error as error:
                problems.append(f"{payload.name}: tier.json detect.content pattern {rule['pattern']!r} does not compile: {error}")


def check_skills(payload, problems):
    skills_dir = payload / "skills"
    if not skills_dir.is_dir():
        problems.append(f"{payload.name}: no skills/ directory")
        return set()
    names = set()
    for entry in sorted(skills_dir.iterdir()):
        if not entry.is_dir():
            continue
        names.add(entry.name)
        skill = entry / "SKILL.md"
        if not skill.is_file():
            problems.append(f"{payload.name}: skills/{entry.name} has no SKILL.md")
            continue
        try:
            text = skill.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as error:
            problems.append(f"{payload.name}: skills/{entry.name}/SKILL.md is unreadable: {error}")
            continue
        block = front_matter(text)
        if not block:
            problems.append(f"{payload.name}: skills/{entry.name}/SKILL.md has no front matter")
            continue
        name = front_field(block, "name")
        if name != entry.name:
            problems.append(
                f"{payload.name}: skills/{entry.name}/SKILL.md front-matter name is {name!r}, not its directory"
            )
        kind = front_field(block, "kind")
        if not kind or not KIND_PATTERN.fullmatch(kind):
            problems.append(
                f"{payload.name}: skills/{entry.name}/SKILL.md kind {kind!r} is not one lowercase word"
            )
    if not names:
        problems.append(f"{payload.name}: skills/ is empty")
    return names


def check_index(payload, skills, problems):
    path = payload / "INDEX.md"
    if not path.is_file():
        problems.append(f"{payload.name}: no INDEX.md")
        return
    try:
        listed = set(INDEX_ENTRY.findall(path.read_text(encoding="utf-8-sig")))
    except (OSError, UnicodeError) as error:
        problems.append(f"{payload.name}: INDEX.md is unreadable: {error}")
        return
    for name in sorted(skills - listed):
        problems.append(f"{payload.name}: INDEX.md does not list shipped skill {name!r}")
    for name in sorted(listed - skills):
        problems.append(f"{payload.name}: INDEX.md lists {name!r} which is not shipped")


def selection_names(data):
    names = []
    if isinstance(data.get("skills"), list):
        names.extend(name for name in data["skills"] if isinstance(name, str))
    profiles = data.get("profiles")
    if isinstance(profiles, dict):
        for grouped in profiles.values():
            if isinstance(grouped, list):
                names.extend(name for name in grouped if isinstance(name, str))
    return names


def check_selection(payload, skills, problems):
    path = payload / "selection.json"
    if not path.is_file():
        problems.append(f"{payload.name}: no selection.json")
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, ValueError) as error:
        problems.append(f"{payload.name}: selection.json is unreadable: {error}")
        return
    if not isinstance(data, dict):
        problems.append(f"{payload.name}: selection.json is not an object")
        return
    for name in sorted(set(selection_names(data)) - skills):
        problems.append(f"{payload.name}: selection.json names {name!r} which is not shipped")


def declared_payloads(root, problems):
    """The payloads the repo declares, or None for a repo authored directly as its payloads.

    A generator-backed repo carries payloads.json, which also proves no stale generator output sits in
    plugins/. A repo without one ships whatever plugins/ holds, and every directory there is checked.
    """
    path = root / PAYLOADS_FILE
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, ValueError) as error:
        problems.append(f"{PAYLOADS_FILE.as_posix()} is unreadable: {error}")
        return []
    payloads = data.get("payloads") if isinstance(data, dict) else None
    if not isinstance(payloads, dict) or not payloads:
        problems.append(f"{PAYLOADS_FILE.as_posix()} has no usable 'payloads' mapping")
        return []
    return sorted(payloads)


def check(root):
    problems = []
    expected = declared_payloads(root, problems)
    if problems:
        return problems

    plugins_dir = root / PLUGINS_DIR
    if not plugins_dir.is_dir():
        problems.append(f"{PLUGINS_DIR}/ does not exist")
        return problems

    actual = {
        entry.name
        for entry in plugins_dir.iterdir()
        if entry.is_dir() and entry.name not in IGNORED_PAYLOAD_ENTRIES
    }
    if expected is None:
        expected = sorted(actual)
        if not expected:
            problems.append(f"{PLUGINS_DIR}/ contains no payload directory")
            return problems
    for name in sorted(actual - set(expected)):
        problems.append(
            f"{PLUGINS_DIR}/{name} is not declared in {PAYLOADS_FILE.as_posix()} - stale output an "
            "installer would treat as a real plugin"
        )
    for name in expected:
        payload = plugins_dir / name
        if not payload.is_dir():
            problems.append(f"{PLUGINS_DIR}/{name} is declared but does not exist")
            continue
        check_tier_declaration(payload, problems)
        skills = check_skills(payload, problems)
        check_index(payload, skills, problems)
        check_selection(payload, skills, problems)
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    arguments = parser.parse_args()

    root = Path(arguments.root).resolve()
    problems = check(root)
    if problems:
        print(f"tier payload check failed for {root} - {len(problems)} problem(s):", file=sys.stderr)
        for problem in problems:
            print("  " + problem, file=sys.stderr)
        return 1
    print(f"tier payload check passed for {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
