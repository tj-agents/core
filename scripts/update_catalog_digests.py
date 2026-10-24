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
    harnesses = HARNESS.synchronize(root, check=True)
    changed: list[str] = []
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
            output, package["package_path"], package.get("digest_excludes", [])
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
