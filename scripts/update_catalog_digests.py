#!/usr/bin/env python3
"""Update or verify current package digests in the capability catalog."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package_sync", ROOT / "scripts/sync_plugin_packages.py")
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)
HARNESS_SPEC = importlib.util.spec_from_file_location("harness_sync", ROOT / "scripts/sync_harness_manifests.py")
HARNESS = importlib.util.module_from_spec(HARNESS_SPEC)
HARNESS_SPEC.loader.exec_module(HARNESS)


def update(root: Path, check: bool) -> None:
    catalog_path = root / ".agents/catalog/catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    sources = json.loads((root / ".agents/plugins/sources.json").read_text(encoding="utf-8"))
    marketplace = SYNC.core_marketplace(root, sources)
    skills = SYNC.discover(root, sources)
    changed: list[str] = []
    configured = set(sources["prerequisites"])
    removed = [package["id"] for package in catalog["packages"] if package["name"] not in configured]
    if removed:
        catalog["packages"] = [package for package in catalog["packages"] if package["name"] in configured]
        changed.extend(removed)
    for package in catalog["packages"]:
        name = package["name"]
        expected_skills = sorted(skill["name"] for skill in skills.values() if skill["plugin"] == name)
        if package["skills"] != expected_skills:
            package["skills"] = expected_skills
            changed.append(package["id"])
        external = sources["external_prerequisites"][name]
        required = [
            *(f"{marketplace}/{dependency}" for dependency in sources["prerequisites"][name]),
            *(dependency["id"] for dependency in external),
        ]
        if package["dependencies"]["required"] != required:
            package["dependencies"]["required"] = required
            changed.append(package["id"])
        expected_external = {"required": external, "optional": []}
        if package.get("external_dependencies") != expected_external:
            package["external_dependencies"] = expected_external
            if package["id"] not in changed:
                changed.append(package["id"])
    if changed and not check:
        catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    harnesses = HARNESS.synchronize(root, check=True)
    for package in catalog["packages"]:
        required = harnesses[package["name"]]["requires"]
        if package.get("harness") != required:
            changed.append(package["id"])
            package["harness"] = required
    _, output, _, _ = SYNC.build(root, validate_catalog_digests=False, catalog=catalog)
    for package in catalog["packages"]:
        if package["owner_repository"] != "tj-agents/core":
            raise ValueError("Core catalog may contain only core packages")
        required = harnesses[package["name"]]["requires"]
        actual = SYNC.output_tree_digest(
            output, package["package_path"], []
        )
        if package.get("harness") != required or package["digest"] != actual:
            if package["id"] not in changed:
                changed.append(package["id"])
            package["harness"] = required
            package["digest"] = actual
    if check and changed:
        raise ValueError("Stale catalog packages: " + ", ".join(changed))
    if not check:
        catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(f"{'Checked' if check else 'Updated'} catalog digests; {len(changed)} changed.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        update(arguments.root.resolve(), arguments.check)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Catalog digest update failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
