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
        self.assertEqual("v2.1.16", c["extraKnownMarketplaces"]["base-agents"]["source"]["ref"])
        self.assertEqual(3, len(c["enabledPlugins"]))
        self.assertNotIn("old@other", c["enabledPlugins"])
        self.assertEqual([], c["permissions"]["allow"])
        d = codex.read_text(encoding="utf-8")
        self.assertIn('model = "test"', d)
        self.assertIn('source = "https://github.com/tj-agents/core.git"', d)
        self.assertIn('ref = "v2.1.16"', d)
        self.assertEqual(3, d.count('[plugins."'))

    def test_rejects_foreign_source(self):
        self.catalog["releases"][0]["source"] = "https://github.com/foreign/core.git"
        catalog = self.root / "catalog.json"
        catalog.write_text(json.dumps(self.catalog), encoding="utf-8")
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "source disagrees with catalog owner"):
            repo_config.run(self.lock, catalog, "write")
        self.assertFalse((self.root / ".claude").exists())

    def test_uses_consumer_catalog_without_core_source_roster(self):
        local = self.catalog["releases"][0]
        external = json.loads(json.dumps(local))
        external.update({
            "id": "sample-market@1.0.0",
            "marketplace": "sample-market",
            "owner_repository": "sample-org/sample-standards",
            "source": "https://github.com/sample-org/sample-standards.git",
            "version": "1.0.0",
            "revision": "v1.0.0",
            "plugins": [external["plugins"][0]],
        })
        external["plugins"][0].update({
            "id": "sample-market/sample",
            "name": "sample",
            "version": "1.0.0",
            "package_path": "plugins/sample",
            "skills": ["sample-skill"],
            "dependencies": {"required": [], "optional": []},
            "harness": {
                "marketplaces": [{"id": "sample-market", "repository": "sample-org/sample-standards"}],
                "plugins": ["sample-market/sample"],
                "hooks": [],
                "permissions": {"claude_allow": ["Bash(sample-command)"], "codex_prefix_rules": []},
            },
        })
        optional = json.loads(json.dumps(external["plugins"][0]))
        optional.update({"id": "sample-market/optional", "name": "optional", "package_path": "plugins/optional"})
        external["plugins"].append(optional)
        self.catalog["releases"].append(external)
        project_catalog = self.root / ".agents" / "catalog" / "catalog.json"
        project_catalog.parent.mkdir()
        project_catalog.write_text(json.dumps(self.catalog), encoding="utf-8")
        self.selections.append({
            "id": "sample-market/sample", "release": external["id"], "commit": "b" * 40,
            "required_skills": [], "path_scopes": [], "exceptions": [],
        })
        self.save_lock()
        self.assertEqual(project_catalog.resolve(), repo_config.bootstrap.catalog_for_lock(self.lock, SCRIPT))
        repo_config.run(self.lock, project_catalog, "write")
        claude = json.loads((self.root / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(
            "sample-org/sample-standards",
            claude["extraKnownMarketplaces"]["sample-market"]["source"]["repo"],
        )
        self.assertIn("Bash(sample-command)", claude["permissions"]["allow"])
        self.assertIs(claude["enabledPlugins"]["sample@sample-market"], True)
        self.assertIs(claude["enabledPlugins"]["optional@sample-market"], False)
        codex = (self.root / ".codex" / "config.toml").read_text(encoding="utf-8")
        self.assertIn('[plugins."optional@sample-market"]\nenabled = false', codex)
        self.assertIn('ref = "v1.0.0"', codex)

    def test_overlay_composes_permissions_and_removes_stale_rules(self):
        overlay = self.root / ".agents" / "repository-harness.json"
        rule = {
            "pattern": ["sample", "safe"],
            "justification": "Required for a repository workflow.",
            "match": ["sample safe --check"],
            "not_match": ["sample unsafe"],
        }
        overlay.write_text(json.dumps({
            "schema_version": 1,
            "requires": {
                "marketplaces": [{"id": "base-agents", "repository": "tj-agents/core"}],
                "plugins": ["base-agents/base"],
                "hooks": [],
                "permissions": {
                    "claude_allow": ["Bash(sample safe)"],
                    "codex_prefix_rules": [rule],
                },
            },
        }), encoding="utf-8")
        self.assertIn(".codex/rules/agent-harness.rules", repo_config.run(self.lock, CATALOG, "check"))
        repo_config.run(self.lock, CATALOG, "write")
        self.assertEqual([], repo_config.run(self.lock, CATALOG, "check"))
        claude = json.loads((self.root / ".claude/settings.json").read_text(encoding="utf-8"))
        self.assertEqual(1, len(claude["permissions"]["allow"]))
        path = self.root / ".codex/rules/agent-harness.rules"
        self.assertIn('decision = "allow"', path.read_text(encoding="utf-8"))
        overlay.unlink()
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "unmanaged permissions.allow entries: Bash\\(sample safe\\)"):
            repo_config.run(self.lock, CATALOG, "check")
        claude["permissions"]["allow"].remove("Bash(sample safe)")
        (self.root / ".claude/settings.json").write_text(json.dumps(claude), encoding="utf-8")
        self.assertEqual([".claude/settings.json", ".codex/rules/agent-harness.rules"], repo_config.run(self.lock, CATALOG, "check"))
        repo_config.run(self.lock, CATALOG, "write")
        self.assertFalse(path.exists())

    def test_hand_written_allow_rule_blocks_check_and_write_without_mutation(self):
        settings = self.root / ".claude" / "settings.json"
        settings.parent.mkdir()
        original = json.dumps({"permissions": {"allow": ["Bash(hand-written-rule)"]}})
        settings.write_text(original, encoding="utf-8")
        for mode in ("check", "write"):
            with self.subTest(mode=mode):
                with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "Bash\\(hand-written-rule\\)"):
                    repo_config.run(self.lock, CATALOG, mode)
                self.assertEqual(original, settings.read_text(encoding="utf-8"))
                self.assertFalse((self.root / ".codex").exists())

    def test_overlay_required_plugin_must_be_selected(self):
        overlay = self.root / ".agents" / "repository-harness.json"
        overlay.write_text(json.dumps({
            "schema_version": 1,
            "requires": {
                "marketplaces": [{"id": "base-agents", "repository": "tj-agents/core"}],
                "plugins": ["sample-market/sample"],
                "hooks": [],
                "permissions": {"claude_allow": [], "codex_prefix_rules": []},
            },
        }), encoding="utf-8")
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "harness-required plugins"):
            repo_config.run(self.lock, CATALOG, "write")

    def test_requires_core_selection(self):
        self.selections.pop()
        self.save_lock()
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "omits core plugins"):
            repo_config.run(self.lock, CATALOG, "write")


if __name__ == "__main__":
    unittest.main()
