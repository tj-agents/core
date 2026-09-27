"""Package harness declarations stay bound to their authored source and hook wiring."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("harness_sync", ROOT / "scripts/sync_harness_manifests.py")
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


class HarnessManifestTests(unittest.TestCase):
    def test_core_manifests_are_current_and_catalog_is_core_only(self):
        manifests = HARNESS.synchronize(ROOT, check=True)
        self.assertEqual({"base", "engineering", "machine"}, set(manifests))
        catalog = HARNESS.load(ROOT / ".agents/catalog/catalog.json")
        self.assertEqual({"tj-agents/core"}, {release["owner_repository"] for release in catalog["releases"]})
        for release in catalog["releases"]:
            for plugin in release["plugins"]:
                self.assertEqual(manifests[plugin["name"]]["requires"], plugin["harness"])

    def test_source_digest_changes_when_owned_source_changes(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / ".agents/base/example.txt"
            source.parent.mkdir(parents=True)
            source.write_text("first", encoding="utf-8")
            config = {
                "scopes": [{"plugin": "base", "root": ".agents/base"}],
                "host_adapter_roots": {},
                "host_manifest_roots": {},
                "host_hook_sources": {},
                "resources": [],
                "prerequisites": {"base": []},
            }
            manifest = {"source_roots": [".agents/base"], "source_excludes": []}
            first = HARNESS.source_digest(root, manifest, config, "base")
            source.write_text("second", encoding="utf-8")
            self.assertNotEqual(first, HARNESS.source_digest(root, manifest, config, "base"))

    def test_declared_hook_hosts_must_match_host_wiring(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / ".agents/plugins/manifests/claude/base-hooks.json"
            source.parent.mkdir(parents=True)
            source.write_text(json.dumps({"hooks": {"SessionStart": [{"hooks": [{
                "command": 'python "${CLAUDE_PLUGIN_ROOT}/hooks/start.py"',
            }]}]}}), encoding="utf-8")
            config = {"host_hook_sources": {"base": {"claude": ".agents/plugins/manifests/claude/base-hooks.json"}}}
            self.assertEqual(
                [{"path": "hooks/start.py", "hosts": ["claude"]}],
                HARNESS.expected_hooks(root, config, "base"),
            )

    def test_foreign_marketplace_owner_is_rejected(self):
        catalog = HARNESS.load(ROOT / ".agents/catalog/catalog.json")
        config = HARNESS.load(ROOT / ".agents/plugins/sources.json")
        requires = json.loads((ROOT / ".agents/plugins/harness/base.json").read_text(encoding="utf-8"))["requires"]
        requires["marketplaces"][0]["repository"] = "another-org/core"
        with self.assertRaisesRegex(ValueError, "disagrees with catalog"):
            HARNESS.validate_requires(ROOT, config, catalog, "base", requires)


if __name__ == "__main__":
    unittest.main()
