#!/usr/bin/env python3
"""Report user-profile agent behavior that should be declared by a repository."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


TABLE = re.compile(r"^\s*\[\s*([^]]+)\s*\]")
ROOT_SETTING = re.compile(r"^\s*(notify|model_instructions_file)\s*=")
HOST_MARKETPLACES = {"openai-bundled", "openai-primary-runtime"}


def audit(home: Path) -> list[str]:
    findings: list[str] = []
    for claude in (home / ".claude" / "settings.json", home / ".claude" / "settings.local.json"):
        if not claude.is_file():
            continue
        try:
            settings = json.loads(claude.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            findings.append(f"{claude}: cannot inspect settings ({error})")
        else:
            if not isinstance(settings, dict):
                findings.append(f"{claude}: settings are not a JSON object")
            else:
                for key in ("enabledPlugins", "extraKnownMarketplaces", "hooks"):
                    if settings.get(key):
                        findings.append(f"{claude}: user-scope {key}")
    codex = home / ".codex" / "config.toml"
    if codex.is_file():
        try:
            lines = codex.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as error:
            findings.append(f"{codex}: cannot inspect config ({error})")
        else:
            section = ""
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                match = TABLE.match(line)
                if match:
                    section = match.group(1).strip()
                    if section.startswith("marketplaces.") and section.removeprefix("marketplaces.") not in HOST_MARKETPLACES:
                        findings.append(f"{codex}: user-scope [{section}]")
                    elif section.startswith("plugins.") and section.rsplit("@", 1)[-1].strip("'\"") not in HOST_MARKETPLACES:
                        findings.append(f"{codex}: user-scope [{section}]")
                    elif section == "hooks" or (
                        section.startswith("hooks.") and section != "hooks.state" and not section.startswith("hooks.state.")
                    ):
                        findings.append(f"{codex}: user-scope [{section}]")
                elif not section and ROOT_SETTING.match(line):
                    findings.append(f"{codex}: user-scope {line.split('=', 1)[0].strip()}")
    for relative in (
        ".codex/agents", ".codex/skills", ".codex/hooks",
        ".claude/agents", ".claude/skills", ".claude/hooks",
    ):
        directory = home / relative
        if directory.is_dir():
            try:
                children = sorted(directory.iterdir())
            except OSError as error:
                findings.append(f"{directory}: cannot inspect directory ({error})")
                continue
            for child in children:
                if child.name.startswith("."):
                    continue
                findings.append(f"{child}: user-scope agent, skill, or hook")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path.home())
    args = parser.parse_args(argv)
    findings = audit(args.home)
    for finding in findings:
        print(finding)
    if not findings:
        print("No user-scope agent behavior found.")
    return int(bool(findings))


if __name__ == "__main__":
    raise SystemExit(main())
