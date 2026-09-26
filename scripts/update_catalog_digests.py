#!/usr/bin/env python3
"""Update or verify immutable package digests in the capability catalog."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package_sync", ROOT / "scripts/sync_plugin_packages.py")
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)


def git(repository: Path, *arguments: str, binary: bool = False):
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=not binary,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode() if binary else completed.stderr
        raise ValueError(f"git {' '.join(arguments)} failed in {repository}: {detail.strip()}")
    return completed.stdout


def git_tree_digest(repository: Path, revision: str, package_path: str, excluded: list[str]) -> str:
    listing = git(repository, "ls-tree", "-r", "-z", revision, "--", package_path, binary=True)
    prefix = package_path.rstrip("/") + "/"
    excluded_paths = {PurePosixPath(value).as_posix() for value in excluded}
    members: list[tuple[str, bytes]] = []
    for record in listing.split(b"\0"):
        if not record:
            continue
        header, raw_path = record.split(b"\t", 1)
        mode, kind, object_id = header.decode("ascii").split()
        path = raw_path.decode("utf-8")
        if kind != "blob" or mode == "120000":
            raise ValueError(f"Package trees may contain only regular files: {path}")
        relative = path[len(prefix):]
        if relative in excluded_paths:
            continue
        data = git(repository, "cat-file", "blob", object_id, binary=True)
        members.append((relative, data))
    digest = hashlib.sha256()
    for relative, data in sorted(members):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(len(data)).encode("ascii"))
        digest.update(b"\0")
        digest.update(data)
    return "sha256:" + digest.hexdigest()


def validate_package_version(plugin: dict, manifest: dict, revision: str) -> None:
    actual = manifest.get("version")
    expected = plugin.get("version")
    if actual != expected:
        raise ValueError(
            f"{plugin['id']}: catalog version {expected!r} disagrees with "
            f"{revision} manifest version {actual!r}"
        )


def parse_sources(values: list[str]) -> dict[str, Path]:
    sources: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Expected MARKETPLACE=REPOSITORY: {value}")
        marketplace, raw_path = value.split("=", 1)
        path = Path(raw_path).expanduser().resolve()
        if marketplace in sources or not path.is_dir():
            raise ValueError(f"Invalid source mapping: {value}")
        sources[marketplace] = path
    return sources


def parse_revisions(values: list[str]) -> dict[str, str]:
    revisions: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Expected MARKETPLACE=REVISION: {value}")
        marketplace, revision = value.split("=", 1)
        if marketplace in revisions or not revision:
            raise ValueError(f"Invalid revision mapping: {value}")
        revisions[marketplace] = revision
    return revisions


def update(root: Path, source_values: list[str], revision_values: list[str], check: bool) -> None:
    catalog_path = root / ".agents/catalog/catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    sources = parse_sources(source_values)
    revisions = parse_revisions(revision_values)
    _, output, _, _ = SYNC.build(root, validate_catalog_digests=False)
    changed: list[str] = []
    for release in catalog["releases"]:
        marketplace = release["marketplace"]
        for plugin in release["plugins"]:
            if marketplace in sources:
                revision = revisions.get(marketplace, release["revision"])
                manifest = json.loads(
                    git(
                        sources[marketplace],
                        "show",
                        f"{revision}:{plugin['package_path']}/.codex-plugin/plugin.json",
                    )
                )
                validate_package_version(plugin, manifest, revision)
                actual = git_tree_digest(
                    sources[marketplace],
                    revision,
                    plugin["package_path"],
                    plugin.get("digest_excludes", []),
                )
            elif marketplace == "base-agents":
                actual = SYNC.output_tree_digest(
                    output, plugin["package_path"], plugin.get("digest_excludes", [])
                )
            else:
                continue
            if plugin["digest"] != actual:
                changed.append(plugin["id"])
                plugin["digest"] = actual
    if check and changed:
        raise ValueError("Stale catalog digests: " + ", ".join(changed))
    if not check:
        catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    action = "Checked" if check else "Updated"
    print(f"{action} catalog digests; {len(changed)} changed.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--source", action="append", default=[], metavar="MARKETPLACE=REPOSITORY")
    parser.add_argument("--source-revision", action="append", default=[], metavar="MARKETPLACE=REVISION")
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        update(arguments.root.resolve(), arguments.source, arguments.source_revision, arguments.check)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Catalog digest update failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
