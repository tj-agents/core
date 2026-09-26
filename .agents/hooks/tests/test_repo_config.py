import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[2] / "machine" / "bootstrap-capabilities" / "scripts" / "repo_config.py"
sys.path.insert(0, str(SCRIPT.parent))
spec = importlib.util.spec_from_file_location("repo_config", SCRIPT)
repo_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repo_config)
CATALOG = Path(__file__).resolve().parents[2] / "catalog" / "catalog.json"


class RepoConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.lock = self.root / ".agents" / "capabilities.lock.json"
        self.lock.parent.mkdir()
        self.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        release = next(r for r in self.catalog["releases"] if r["marketplace"] == "base-agents")
        self.selections = [
            {
                "id": plugin["id"], "release": release["id"], "commit": "a" * 40,
                "required_skills": [], "path_scopes": [], "exceptions": [],
            }
            for plugin in release["plugins"]
        ]
        self.save_lock()

    def save_lock(self):
        self.lock.write_text(json.dumps({"schema_version": 1, "plugins": self.selections}), encoding="utf-8")

    def test_generates_both_hosts_preserving_unrelated_settings_and_checks_drift(self):
        claude = self.root / ".claude" / "settings.json"
        codex = self.root / ".codex" / "config.toml"
        claude.parent.mkdir()
        codex.parent.mkdir()
        claude.write_text(json.dumps({"env": {"MODE": "test"}, "enabledPlugins": {"old@other": True}}), encoding="utf-8")
        codex.write_text('model = "test"\n\n[plugins."old@other"]\nenabled = true\n', encoding="utf-8")
        self.assertEqual([".claude/settings.json", ".codex/config.toml"], repo_config.run(self.lock, CATALOG, "check"))
        repo_config.run(self.lock, CATALOG, "write")
        self.assertEqual([], repo_config.run(self.lock, CATALOG, "check"))
        c = json.loads(claude.read_text(encoding="utf-8"))
        self.assertEqual("test", c["env"]["MODE"])
        self.assertEqual("tj-agents/core", c["extraKnownMarketplaces"]["base-agents"]["source"]["repo"])
        self.assertEqual(3, len(c["enabledPlugins"]))
        self.assertNotIn("old@other", c["enabledPlugins"])
        d = codex.read_text(encoding="utf-8")
        self.assertIn('model = "test"', d)
        self.assertIn('source = "https://github.com/tj-agents/core.git"', d)
        self.assertEqual(3, d.count('[plugins."'))

    def test_rejects_foreign_source(self):
        self.catalog["releases"][0]["source"] = "https://github.com/foreign/core.git"
        catalog = self.root / "catalog.json"
        catalog.write_text(json.dumps(self.catalog), encoding="utf-8")
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "Unapproved marketplace source"):
            repo_config.run(self.lock, catalog, "write")
        self.assertFalse((self.root / ".claude").exists())

    def test_requires_core_selection(self):
        self.selections.pop()
        self.save_lock()
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "omits core plugins"):
            repo_config.run(self.lock, CATALOG, "write")


if __name__ == "__main__":
    unittest.main()
