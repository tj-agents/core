import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[2] / "machine" / "utility" / "plugin-selection" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


plugin_selection = load("plugin_selection")
repo_config = load("repo_config")
LockError = repo_config.lock_io.LockError


class PluginSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.selection = self.root / ".agents" / "plugins.json"
        self.selection.parent.mkdir()
        self.document = {"schema_version": 1, "marketplace": {"repository": "tj-agents/marketplace"}, "plugins": ["base", "engineering", "machine", "dotnet"]}
        self.selection.write_text(json.dumps(self.document), encoding="utf-8")

    def run_mode(self, mode, scope="project"):
        return repo_config.run(self.selection, mode, root=self.root, scope=scope)

    def test_generates_rolling_main_settings_without_a_revision(self):
        self.assertEqual([".claude/settings.json", ".codex/config.toml"], self.run_mode("check"))
        self.run_mode("write")
        self.assertEqual([], self.run_mode("check"))
        claude = json.loads((self.root / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual({"tj-agents": {"source": {"source": "github", "repo": "tj-agents/marketplace"}, "autoUpdate": True}}, claude["extraKnownMarketplaces"])
        codex = (self.root / ".codex" / "config.toml").read_text(encoding="utf-8")
        self.assertIn('source = "https://github.com/tj-agents/marketplace.git"', codex)
        self.assertNotIn("ref =", codex)
        self.assertIn('sparse_paths = [".agents/plugins", ".claude-plugin", "plugins"]', codex)

    def test_selection_allows_only_effective_packages(self):
        self.document["plugins"] = ["dotnet"]
        self.selection.write_text(json.dumps(self.document), encoding="utf-8")
        self.run_mode("write")
        claude = json.loads((self.root / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual({"dotnet@tj-agents": True}, claude["enabledPlugins"])

    def test_invalid_selection_and_legacy_pin_are_rejected_by_settings_generation(self):
        self.document["marketplace"]["revision"] = "v1.2.3"
        with self.assertRaises(LockError):
            plugin_selection.validate(self.document)
        legacy = {"schema_version": 2, "marketplace": {"repository": "tj-agents/marketplace", "revision": "v1.2.3"}, "plugins": ["base"]}
        with self.assertRaises(LockError):
            plugin_selection.validate(legacy)

    def test_local_scope_writes_local_settings(self):
        self.run_mode("write", "local")
        claude = json.loads((self.root / ".claude" / "settings.local.json").read_text(encoding="utf-8"))
        self.assertTrue(claude["extraKnownMarketplaces"]["tj-agents"]["autoUpdate"])
        self.assertEqual([], self.run_mode("check", "local"))

    def test_resolve_names_the_selection_in_agents(self):
        self.assertEqual(self.selection, plugin_selection.resolve(self.root))


if __name__ == "__main__":
    unittest.main()
