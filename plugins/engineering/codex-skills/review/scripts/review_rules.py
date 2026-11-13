#!/usr/bin/env python3
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


def tier_gate():
    here = Path(__file__).resolve().parent
    for parent in (here.parents[2], here.parents[3]):
        path = parent / "hooks/tier_gate.py"
        if path.is_file():
            sys.path.insert(0, str(path.parent))
            try:
                spec = importlib.util.spec_from_file_location("review_tier_gate", path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            finally:
                del sys.path[0]
            return module
    raise ValueError("The installed review package is missing hooks/tier_gate.py")


def effective_claude_entries(entries, project):
    scopes = {"local": 2, "project": 1}
    effective = {}
    for entry in entries:
        scope, owner = entry.get("scope"), entry.get("projectPath")
        if scope in ("user", "managed"):
            rank = (sys.maxsize, 0) if scope == "managed" else (-1, 0)
        elif scope in scopes and isinstance(owner, str) and owner:
            owner = Path(owner).resolve()
            if not project.is_relative_to(owner):
                continue
            rank = (len(owner.parts), scopes[scope])
        else:
            continue
        if entry.get("id") not in effective or rank > effective[entry.get("id")][0]:
            effective[entry.get("id")] = (rank, entry)
    return [entry for _, entry in effective.values()]


def host_declarations(gate, host, identities, project):
    if host not in ("codex", "claude"):
        raise ValueError("Specify the reviewing host with --host codex or --host claude")
    variable = "CODEX_HOME" if host == "codex" else "CLAUDE_CONFIG_DIR"
    profile = Path(os.environ.get(variable) or Path.home() / ("." + host))
    cache = (profile / "plugins/cache").resolve()
    entries = gate.native_plugins(host, str(project))
    if not entries:
        raise ValueError("The reviewing host's enabled plugin inventory is unavailable or empty")
    if host == "claude":
        entries = effective_claude_entries(entries, project)
    found = []
    for entry in entries:
        if host == "codex":
            parts = [entry.get(key) for key in ("marketplaceName", "name", "version")]
            if not all(isinstance(part, str) and part for part in parts):
                continue
            if parts[1] + "@" + parts[0] not in identities:
                continue
            payload = cache.joinpath(*parts).resolve()
        else:
            location = entry.get("installPath")
            if not isinstance(location, str) or not location:
                continue
            payload = Path(location).resolve()
        if not payload.is_relative_to(cache) or len(payload.relative_to(cache).parts) != 3:
            raise ValueError("Enabled plugin escapes the reviewing host's cache: " + str(payload))
        if payload.parent.name + "@" + payload.parent.parent.name not in identities:
            continue
        declaration = payload / "tier.json"
        if not declaration.is_file():
            continue
        data = json.loads(declaration.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise ValueError("Malformed selected standards declaration: " + str(declaration))
        found.append(gate.Declaration(payload.parent.name, payload.parent.parent.name, data, payload,
                                      (payload / gate.ORPHAN_MARKER).exists()))
    return found


def resolve(project, gate=None, found=None, host=None):
    project = Path(project).resolve()
    gate = gate or tier_gate()
    selection = gate.PluginSelection.read(project)
    if selection is None:
        return {"selection": None, "rules": [], "diagnostics": [
            "No repository plugin selection; use its injected native instructions and explicit skill references only."
        ]}
    declarations = list(host_declarations(gate, host, selection.identities, project) if found is None else found)
    assessment = gate.selected_assessment(project, selection, declarations)
    standards = gate.applicable_standards(
        assessment, [*assessment.ubiquitous, *(item for item, _ in assessment.applicable)])
    return {
        "selection": {"path": str(selection.path), "sha256": selection.sha256, "plugins": sorted(selection.identities)},
        "rules": [{"name": standard.name, "plugin": standard.plugin, "path": str(standard.path),
                   "sha256": hashlib.sha256(standard.path.read_bytes()).hexdigest()} for standard in standards],
        "diagnostics": [],
    }


def main():
    if sys.version_info < (3, 10):
        print(json.dumps({"error": "Review standards resolution requires Python 3.10 or newer"}))
        return 1
    parser = argparse.ArgumentParser(description="List review conventions from the repository's selected applicable plugins.")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--host", choices=("codex", "claude"), required=True)
    arguments = parser.parse_args()
    try:
        result = resolve(arguments.project, host=arguments.host)
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps({"error": str(error)}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
