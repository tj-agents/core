r"""Resolve the conditional rules a repository has declared it is subject to.

The behavioral floor is unconditional and identical everywhere. A *rule* is conditional: true of a class
of projects rather than of every project, so it cannot be hardcoded into the floor and must not be copied
into each repository that happens to be in that class. The rule text is authored once under
``standards/rules/`` and carries an ``applies_when`` predicate in ``catalogue.json``; each repository
declares its own ``.agents/profile.json``, and this module intersects the two.

A repository therefore repeats a declaration, never a rule. When a project's circumstances change —
pre-launch becoming launched — the profile changes and every rule predicated on it deactivates at once,
with no rule rewritten and none left behind.

Anything unexpected yields no rules: a malformed profile or catalogue must never wedge a session, and an
unreadable rule is dropped rather than guessed at.
"""

import json
from pathlib import Path

PROFILE_FILE = ".agents/profile.json"
CATALOGUE = ("standards", "rules", "catalogue.json")


def _load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None


def find_profile(project_dir):
    """The nearest declared profile at or above ``project_dir``, or None."""
    try:
        current = Path(project_dir).resolve()
    except (OSError, TypeError, ValueError):
        return None
    for directory in (current, *current.parents):
        data = _load_json(directory / PROFILE_FILE)
        if isinstance(data, dict):
            return data
    return None


def _as_list(value):
    if isinstance(value, (list, tuple)):
        return [v for v in value]
    return [value]


def matches(applies_when, profile):
    """True when every declared condition holds against the profile.

    A condition names a profile key and the value(s) that satisfy it. Either side may be a list, and a
    list on either side means "any of". An absent profile key never satisfies a condition, so a rule is
    delivered only to a repository that has positively declared itself subject to it.
    """
    if not isinstance(applies_when, dict) or not applies_when:
        return True
    if not isinstance(profile, dict):
        return False
    for key, expected in applies_when.items():
        if key not in profile:
            return False
        declared = _as_list(profile.get(key))
        if not any(candidate in declared for candidate in _as_list(expected)):
            return False
    return True


def resolve_rules(project_dir, payload_root):
    """The (id, text) of every catalogued rule this repository has declared itself subject to."""
    profile = find_profile(project_dir)
    if profile is None:
        return []
    catalogue = _load_json(Path(payload_root).joinpath(*CATALOGUE))
    if not isinstance(catalogue, dict):
        return []
    entries = catalogue.get("rules")
    if not isinstance(entries, list):
        return []
    resolved = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if not matches(entry.get("applies_when"), profile):
            continue
        doc = entry.get("doc")
        if not isinstance(doc, str) or not doc:
            continue
        try:
            text = Path(payload_root).joinpath(*doc.split("/")).read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if text:
            resolved.append((entry.get("id"), text))
    return resolved
