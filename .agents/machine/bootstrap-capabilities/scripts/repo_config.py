#!/usr/bin/env python3
"""Generate project host settings from a committed capability lock."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

import bootstrap_capabilities as bootstrap


SOURCES = {
    "base-agents": "tj-agents/core",
    "cpp-agents": "tj-agents/cpp",
    "dotagents": "tj-agents/dotnet",
    "react-agents": "tj-agents/react",
}
CORE_PLUGINS = {"base-agents/base", "base-agents/engineering", "base-agents/machine"}
MANAGED_START = "# BEGIN repo-declared agent capabilities"
MANAGED_END = "# END repo-declared agent capabilities"
TABLE = re.compile(r"^\s*\[\s*(marketplaces|plugins)(?:\.|\])")
HEADER = re.compile(r"^\s*\[")


def declarations(lock_path: Path, catalog_path: Path) -> tuple[dict[str, str], list[str]]:
    catalog = bootstrap.load_json(catalog_path)
    releases, plugins = bootstrap.catalog_index(catalog)
    selections = bootstrap.validate_lock(bootstrap.load_json(lock_path), releases, plugins)
    selected = {selection["id"] for selection in selections}
    missing = sorted(CORE_PLUGINS - selected)
    if missing:
        raise bootstrap.BootstrapError("Repository lock omits core plugins: " + ", ".join(missing))
    sources: dict[str, str] = {}
    identities: list[str] = []
    for selection in selections:
        release = plugins[selection["id"]]["_release"]
        marketplace = release["marketplace"]
        expected = SOURCES.get(marketplace)
        if expected is None or release["owner_repository"] != expected:
            raise bootstrap.BootstrapError(f"Unapproved marketplace owner: {marketplace}")
        source = release["source"].removesuffix(".git")
        if source != f"https://github.com/{expected}":
            raise bootstrap.BootstrapError(f"Unapproved marketplace source: {source}")
        sources[marketplace] = expected
        identities.append(f"{plugins[selection['id']]['name']}@{marketplace}")
    return dict(sorted(sources.items())), sorted(identities)


def claude_settings(path: Path, sources: dict[str, str], identities: list[str]) -> str:
    settings = bootstrap.load_json(path) if path.is_file() else {}
    settings["extraKnownMarketplaces"] = {
        name: {"source": {"source": "github", "repo": source}, "autoUpdate": False}
        for name, source in sources.items()
    }
    settings["enabledPlugins"] = {identity: True for identity in identities}
    return json.dumps(settings, indent=2, ensure_ascii=False) + "\n"


def unmanaged_codex(text: str) -> str:
    if text.count(MANAGED_START) != text.count(MANAGED_END) or text.count(MANAGED_START) > 1:
        raise bootstrap.BootstrapError("Malformed managed section in .codex/config.toml")
    if MANAGED_START in text:
        before, rest = text.split(MANAGED_START, 1)
        _, after = rest.split(MANAGED_END, 1)
        text = before + after.lstrip("\r\n")
    lines = text.splitlines(keepends=True)
    kept: list[str] = []
    skip = False
    for line in lines:
        if HEADER.match(line):
            skip = bool(TABLE.match(line))
        if not skip:
            kept.append(line)
    return "".join(kept).rstrip()


def codex_settings(path: Path, sources: dict[str, str], identities: list[str]) -> str:
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    prefix = unmanaged_codex(existing)
    lines = [MANAGED_START]
    for marketplace, source in sources.items():
        lines += [f"[marketplaces.{marketplace}]", 'source_type = "git"',
                  f'source = "https://github.com/{source}.git"', ""]
    for identity in identities:
        lines += [f'[plugins."{identity}"]', "enabled = true", ""]
    lines.append(MANAGED_END)
    return (prefix + "\n\n" if prefix else "") + "\n".join(lines) + "\n"


def run(lock_path: Path, catalog_path: Path, mode: str) -> list[str]:
    root = lock_path.resolve().parent.parent
    sources, identities = declarations(lock_path, catalog_path)
    targets = {
        root / ".claude" / "settings.json": claude_settings,
        root / ".codex" / "config.toml": codex_settings,
    }
    drift = []
    for path, render in targets.items():
        expected = render(path, sources, identities)
        actual = path.read_text(encoding="utf-8") if path.is_file() else None
        if actual == expected:
            continue
        drift.append(path.relative_to(root).as_posix())
        if mode == "write":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
    return drift


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", required=True, type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--mode", required=True, choices=("write", "check"))
    args = parser.parse_args(argv)
    try:
        catalog = args.catalog or bootstrap.find_catalog(Path(__file__).resolve())
        drift = run(args.lock, catalog, args.mode)
    except (bootstrap.BootstrapError, OSError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    if drift:
        print(("Updated" if args.mode == "write" else "Drift in") + ": " + ", ".join(drift))
    return int(args.mode == "check" and bool(drift))


if __name__ == "__main__":
    raise SystemExit(main())
