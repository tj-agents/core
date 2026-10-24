import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[2] / "machine" / "utility" / "plugin-selection" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adopt_plugins = load("adopt_plugins")
plugin_selection = adopt_plugins.plugin_selection
LockError = adopt_plugins.lock_io.LockError
CORE = sorted(plugin_selection.plugin_id(name) for name in plugin_selection.CORE_PLUGINS)
CATALOG = {
    "base": [],
    "agent-store": [],
    "machine": ["base", "agent-store"],
    "workflow": ["base", "agent-store", "machine"],
    "engineering": ["base", "workflow", "agent-store", "machine"],
    "stack-a": ["engineering"],
    "stack-a-tool": ["stack-a"],
    "profile-a": ["engineering"],
}


def with_core(*plugins):
    return sorted({*CORE, *plugins})


class AdoptPluginsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "project"
        self.root.mkdir()
        self.selection = self.root / ".agents" / "plugins.json"
        catalog = mock.patch.object(adopt_plugins, "marketplace_catalog", return_value=CATALOG)
        self.catalog = catalog.start()
        self.addCleanup(catalog.stop)

    def plugins(self):
        return json.loads(self.selection.read_text(encoding="utf-8"))["plugins"]

    def write_selection(self, plugins, marketplaces=None):
        self.selection.parent.mkdir(exist_ok=True)
        self.selection.write_text(json.dumps({
            "schema_version": 1,
            "marketplaces": marketplaces or {"tj-agents": {"repository": "tj-agents/marketplace"}},
            "plugins": plugins,
        }), encoding="utf-8")

    def test_new_selection_includes_core_and_requirements_from_the_marketplace_catalog(self):
        adopt_plugins.run(self.root, ["stack-a-tool"], "write")
        self.assertEqual(with_core("stack-a@tj-agents", "stack-a-tool@tj-agents"), self.plugins())
        self.catalog.assert_called_with("tj-agents/marketplace")
        claude = json.loads((self.root / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertTrue(claude["extraKnownMarketplaces"]["tj-agents"]["autoUpdate"])
        self.assertNotIn("ref", claude["extraKnownMarketplaces"]["tj-agents"]["source"])
        for plugin in with_core("stack-a@tj-agents", "stack-a-tool@tj-agents"):
            self.assertTrue(claude["enabledPlugins"][plugin])
        codex = (self.root / ".codex" / "config.toml").read_text(encoding="utf-8")
        for plugin in with_core("stack-a@tj-agents", "stack-a-tool@tj-agents"):
            self.assertIn(f'[plugins."{plugin}"]', codex)
        self.assertEqual([], adopt_plugins.run(self.root, ["stack-a-tool"], "check"))

    def test_default_adoption_selects_only_core(self):
        adopt_plugins.run(self.root, [], "write")
        self.assertEqual(CORE, self.plugins())

    def test_only_requested_plugins_and_their_requirements_are_selected(self):
        adopt_plugins.run(self.root, ["engineering"], "write")
        self.assertEqual(CORE, self.plugins())
        adopt_plugins.run(self.root, ["profile-a"], "write")
        self.assertEqual(with_core("profile-a@tj-agents"), self.plugins())
        self.assertEqual([], adopt_plugins.run(self.root, ["profile-a"], "check"))
        self.assertEqual([], adopt_plugins.run(self.root, ["machine"], "check"))

    def test_repository_remote_does_not_select_a_plugin(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "remote", "add", "origin", "https://github.com/tj-agents/sample.git"], check=True)
        adopt_plugins.run(self.root, ["machine"], "write")
        self.assertEqual(CORE, self.plugins())

    def test_existing_selection_gains_requirements_but_not_core(self):
        self.write_selection(["stack-a@tj-agents"])
        adopt_plugins.run(self.root, ["stack-a-tool"], "write")
        self.assertEqual(with_core("stack-a@tj-agents", "stack-a-tool@tj-agents"), self.plugins())
        self.write_selection(["base@tj-agents"])
        adopt_plugins.run(self.root, [], "write")
        self.assertEqual(["base@tj-agents"], self.plugins())

    def test_existing_selection_keeps_plugins_the_catalog_no_longer_lists(self):
        self.write_selection(["retired@tj-agents"])
        adopt_plugins.run(self.root, ["profile-a"], "write")
        self.assertEqual(with_core("profile-a@tj-agents", "retired@tj-agents"), self.plugins())

    def test_unknown_plugin_is_rejected(self):
        with self.assertRaisesRegex(LockError, "Unknown plugin: missing"):
            adopt_plugins.run(self.root, ["missing"], "write")

    def test_unreadable_catalog_fails_adoption(self):
        self.catalog.side_effect = LockError("Cannot read the tj-agents/marketplace marketplace catalog")
        with self.assertRaisesRegex(LockError, "Cannot read"):
            adopt_plugins.run(self.root, ["profile-a"], "write")
        self.assertFalse(self.selection.exists())

    def test_foreign_selection_requires_a_declared_source_and_survives_later_adoption(self):
        with self.assertRaises(LockError):
            adopt_plugins.run(self.root, ["foreign@other"], "write")
        adopt_plugins.run(self.root, ["foreign@other"], "write", marketplaces=["other=tj-agents/other"])
        adopt_plugins.run(self.root, ["stack-a"], "write")
        self.assertEqual(with_core("foreign@other", "stack-a@tj-agents"), self.plugins())
        before = self.selection.read_bytes()
        with self.assertRaisesRegex(LockError, "more than once"):
            adopt_plugins.run(self.root, [], "write", marketplaces=["other=tj-agents/other"] * 2)
        self.assertEqual(before, self.selection.read_bytes())

    def test_schema_two_lock_is_migrated_once_and_discards_its_pin(self):
        legacy = self.root / ".agents" / "plugins.lock.json"
        legacy.parent.mkdir()
        legacy.write_text(json.dumps({"schema_version": 2, "marketplace": {"repository": "tj-agents/marketplace", "revision": "v1.2.3"}, "plugins": ["base"]}), encoding="utf-8")
        adopt_plugins.run(self.root, ["stack-a"], "write")
        selection = json.loads(self.selection.read_text(encoding="utf-8"))
        self.assertEqual({"repository": "tj-agents/marketplace"}, selection["marketplaces"]["tj-agents"])
        self.assertNotIn("revision", json.dumps(selection))
        self.assertFalse(legacy.exists())
        self.assertEqual([], adopt_plugins.run(self.root, ["stack-a"], "check"))

    def test_multiple_marketplaces_are_retained_and_schema_three_pins_are_discarded(self):
        legacy = self.root / ".agents" / "plugins.lock.json"
        legacy.parent.mkdir()
        legacy.write_text(json.dumps({
            "schema_version": 3,
            "marketplaces": {
                "tj-agents": {"repository": "tj-agents/marketplace", "revision": "v1.2.3"},
                "other": {"repository": "tj-agents/other", "revision": "a" * 40},
            },
            "plugins": ["base@tj-agents", "foreign@other"],
        }), encoding="utf-8")
        adopt_plugins.run(self.root, ["stack-a"], "write")
        selection = json.loads(self.selection.read_text(encoding="utf-8"))
        self.assertEqual({"other": {"repository": "tj-agents/other"},
                          "tj-agents": {"repository": "tj-agents/marketplace"}}, selection["marketplaces"])
        self.assertEqual(with_core("foreign@other", "stack-a@tj-agents"), self.plugins())
        self.assertNotIn("revision", json.dumps(selection))
        self.assertFalse(legacy.exists())
        self.assertEqual([], adopt_plugins.run(self.root, ["stack-a"], "check"))
        claude = json.loads((self.root / ".claude/settings.json").read_text(encoding="utf-8"))
        self.assertEqual("tj-agents/other", claude["extraKnownMarketplaces"]["other"]["source"]["repo"])
        codex = (self.root / ".codex/config.toml").read_text(encoding="utf-8")
        self.assertNotIn("ref =", codex)
        foreign = codex.split("[marketplaces.other]", 1)[1].split("[marketplaces.", 1)[0]
        self.assertNotIn("sparse_paths", foreign)

    def test_producer_lock_migration_moves_core_to_the_marketplace_and_discards_pins(self):
        legacy = self.root / ".agents" / "plugins.lock.json"
        legacy.parent.mkdir()
        legacy.write_text(json.dumps({
            "schema_version": 3,
            "marketplaces": {
                "base-agents": {"repository": "tj-agents/core", "revision": "v2.1.18"},
                "other": {"repository": "tj-agents/other", "revision": "a" * 40},
            },
            "plugins": [*(f"{name}@base-agents" for name in plugin_selection.CORE_PLUGINS), "foreign@other"],
        }), encoding="utf-8")
        adopt_plugins.run(self.root, [], "write")
        self.assertFalse(legacy.exists())
        document = json.loads(self.selection.read_text(encoding="utf-8"))
        self.assertEqual({"tj-agents": {"repository": "tj-agents/marketplace"}, "other": {"repository": "tj-agents/other"}},
                         document["marketplaces"])
        self.assertNotIn("revision", json.dumps(document))
        self.assertNotIn("tj-agents/core", json.dumps(document))
        self.assertEqual(with_core("foreign@other"), self.plugins())
        codex = (self.root / ".codex/config.toml").read_text(encoding="utf-8")
        self.assertNotIn("tj-agents/core", codex)
        adopt_plugins.run(self.root, ["stack-a"], "write")
        self.assertEqual(with_core("foreign@other", "stack-a@tj-agents"), self.plugins())
        self.assertEqual([], adopt_plugins.run(self.root, [], "check"))

    def test_local_scope_preserves_project_settings(self):
        adopt_plugins.run(self.root, ["stack-a"], "write", "local")
        self.assertTrue((self.root / ".claude" / "settings.local.json").is_file())
        self.assertFalse((self.root / ".claude" / "settings.json").exists())

    def test_cli_reports_drift_and_has_no_stack_shortcut(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(1, adopt_plugins.main(["--root", str(self.root), "--plugin", "stack-a", "--mode", "check"]))
            self.assertEqual(0, adopt_plugins.main(["--root", str(self.root), "--plugin", "stack-a", "--mode", "write"]))
        self.assertIn(".agents/plugins.json", output.getvalue())
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            adopt_plugins.main(["--root", str(self.root), "--stack", "stack-a", "--mode", "check"])


class CatalogReaderTests(unittest.TestCase):
    def read(self, manifest):
        response = mock.MagicMock()
        response.__enter__.return_value = io.BytesIO(json.dumps(manifest).encode("utf-8"))
        with mock.patch.object(adopt_plugins.urllib.request, "urlopen", return_value=response) as urlopen:
            catalog = adopt_plugins.marketplace_catalog("tj-agents/marketplace")
        self.assertIn("tj-agents/marketplace", urlopen.call_args.args[0])
        return catalog

    def test_entries_map_to_their_same_marketplace_dependencies(self):
        catalog = self.read({"plugins": [{"name": "base", "source": {}}, {"name": "stack-a", "dependencies": ["base"]}]})
        self.assertEqual({"base": [], "stack-a": ["base"]}, catalog)

    def test_a_cross_marketplace_dependency_is_rejected(self):
        with self.assertRaisesRegex(LockError, "invalid plugin entry"):
            self.read({"plugins": [{"name": "stack-a", "dependencies": ["base@elsewhere"]}]})

    def test_network_failure_is_reported(self):
        with mock.patch.object(adopt_plugins.urllib.request, "urlopen", side_effect=OSError("offline")):
            with self.assertRaisesRegex(LockError, "Cannot read the tj-agents/marketplace marketplace catalog"):
                adopt_plugins.marketplace_catalog("tj-agents/marketplace")


class CoreIndependenceTests(unittest.TestCase):
    def test_plugin_selection_names_only_core_packages(self):
        sources = [*SCRIPTS.parent.rglob("*"), Path(__file__)]
        named = set()
        for path in sources:
            if path.is_file() and path.suffix in {".py", ".md", ".json"}:
                named |= set(re.findall(r"\b([a-z][a-z0-9-]*)@tj-agents\b", path.read_text(encoding="utf-8")))
        fixtures = {"retired", *(name for name in CATALOG if name not in plugin_selection.CORE_PLUGINS)}
        self.assertLessEqual(named - fixtures, set(plugin_selection.CORE_PLUGINS))


if __name__ == "__main__":
    unittest.main()
