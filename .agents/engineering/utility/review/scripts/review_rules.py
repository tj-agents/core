#!/usr/bin/env python3
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys


IDENTITY = re.compile(r"[a-z][a-z0-9-]*@[a-z][a-z0-9-]*\Z")


def tier_gate():
    here = Path(__file__).resolve().parent
    for parent in (here.parents[2], here.parents[3]):
        path = parent / "hooks/tier_gate.py"
        if path.is_file():
            spec = importlib.util.spec_from_file_location("review_tier_gate", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    raise ValueError("The installed review package is missing hooks/tier_gate.py")


def metadata(path):
    text = path.read_text(encoding="utf-8-sig")
    if not text.startswith("---\n"):
        return {}
    front = text.split("---", 2)[1]
    return dict(re.findall(r"^(name|kind):[ \t]*([a-z][a-z0-9-]*)[ \t]*$", front, re.MULTILINE))


def conventions(declaration):
    payload = declaration.payload_dir.resolve()
    result = {}
    for path in sorted((payload / "skills").glob("*/SKILL.md")):
        if not path.resolve().is_relative_to(payload):
            raise ValueError(f"Skill escapes its selected payload: {path}")
        fields = metadata(path)
        if fields.get("kind") not in ("convention", "contract") or fields.get("name") != path.parent.name:
            continue
        canonical = []
        for candidate in (payload / ".agents").rglob("SKILL.md"):
            if candidate.resolve().is_relative_to(payload) and metadata(candidate) == fields:
                canonical.append(candidate)
        if len(canonical) > 1:
            raise ValueError(f"Ambiguous canonical definition for {declaration.plugin}:{fields['name']}")
        source = canonical[0] if canonical else path
        name = declaration.plugin + ":" + fields["name"]
        result[name] = {
            "name": name,
            "plugin": declaration.id,
            "path": str(source),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        }
    return result


def host_declarations(gate, host):
    if host not in ("codex", "claude"):
        raise ValueError("Specify the reviewing host with --host codex or --host claude")
    variable = "CODEX_HOME" if host == "codex" else "CLAUDE_CONFIG_DIR"
    profile = Path(os.environ.get(variable) or Path.home() / ("." + host))
    cache = (profile / "plugins/cache").resolve()
    entries = gate.native_plugins(host)
    if not entries:
        raise ValueError("The reviewing host's enabled plugin inventory is unavailable or empty")
    found = []
    for entry in entries:
        if host == "codex":
            parts = [entry.get(key) for key in ("marketplaceName", "name", "version")]
            if not all(isinstance(part, str) and part for part in parts):
                continue
            payload = cache.joinpath(*parts).resolve()
        else:
            location = entry.get("installPath")
            if not isinstance(location, str) or not location:
                continue
            payload = Path(location).resolve()
        if not payload.is_relative_to(cache) or len(payload.relative_to(cache).parts) != 3:
            raise ValueError("Enabled plugin escapes the reviewing host's cache: " + str(payload))
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
    path = project / ".agents/plugins.json"
    if not path.is_file():
        return {"selection": None, "rules": [], "diagnostics": [
            "No repository plugin selection; use its injected native instructions and explicit skill references only."
        ]}
    raw = path.read_bytes()
    document = json.loads(raw.decode("utf-8-sig"))
    identities = document.get("plugins") if isinstance(document, dict) else None
    marketplaces = document.get("marketplaces") if isinstance(document, dict) else None
    if (not isinstance(document, dict) or document.get("schema_version") != 1 or not isinstance(identities, list) or not identities
            or not isinstance(marketplaces, dict)
            or any(not isinstance(item, str) or not IDENTITY.fullmatch(item)
                   or item.partition("@")[2] not in marketplaces for item in identities)
            or len(set(identities)) != len(identities)):
        raise ValueError("Invalid repository plugin selection in " + str(path))
    gate = gate or tier_gate()
    declarations = list(host_declarations(gate, host) if found is None else found)
    selected = [item for item in declarations if item.id in identities]
    missing = sorted(set(identities) - {item.id for item in selected})
    if missing:
        raise ValueError("Selected standards are not available in this host: " + ", ".join(missing))
    if len({item.plugin for item in selected}) != len(selected):
        raise ValueError("Selected marketplaces provide conflicting plugin namespaces")
    selection = gate.assess(project, selected)
    if selection.diagnostics:
        raise ValueError("Selected standards have unresolved applicability: " + json.dumps(selection.diagnostics))
    if len(selection.employers) > 1:
        raise ValueError("Multiple selected employer profiles apply; resolve the review's employer scope")
    available = {}
    for declaration in [*selection.ubiquitous, *(item for item, _ in selection.applicable)]:
        if declaration.orphaned:
            raise ValueError("Selected standards payload is orphaned: " + declaration.id)
        available.update(conventions(declaration))
    effective = {
        gate.replacement_skill(selection, name, lambda candidate: candidate in available)
        for name in available
    }
    return {
        "selection": {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "plugins": sorted(identities)},
        "rules": [available[name] for name in sorted(effective)],
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
