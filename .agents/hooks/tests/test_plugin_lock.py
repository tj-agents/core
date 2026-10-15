import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[2] / "machine" / "utility" / "plugin-lock" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


plugin_lock = load("plugin_lock")
repo_config = load("repo_config")
LockError = repo_config.lock_io.LockError


class PluginLockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.lock = self.root / ".agents" / "plugins.lock.json"
        self.lock.parent.mkdir()
        self.document = {
            "schema_version": 2,
            "marketplaces": {"tj-agents": {"repository": "tj-agents/marketplace", "revision": "v1.2.3"}},
            "plugins": ["base@tj-agents", "engineering@tj-agents", "machine@tj-agents", "dotnet@tj-agents"],
        }
        self.save()

    def save(self):
        self.lock.write_text(json.dumps(self.document), encoding="utf-8")

    def run_mode(self, mode, scope="project"):
        return repo_config.run(self.lock, mode, root=self.root, scope=scope)

    def test_generates_both_hosts_from_the_marketplace_pin_without_a_catalog(self):
        self.assertEqual([".claude/settings.json", ".codex/config.toml"], self.run_mode("check"))
        self.run_mode("write")
        self.assertEqual([], self.run_mode("check"))
        claude = json.loads((self.root / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(
            {"tj-agents": {"source": {"source": "github", "repo": "tj-agents/marketplace", "ref": "v1.2.3"}, "autoUpdate": False}},
            claude["extraKnownMarketplaces"],
        )
        self.assertEqual({identity: True for identity in self.document["plugins"]}, claude["enabledPlugins"])
        codex = (self.root / ".codex" / "config.toml").read_text(encoding="utf-8")
        self.assertIn("[marketplaces.tj-agents]", codex)
        self.assertIn('source = "https://github.com/tj-agents/marketplace.git"', codex)
        self.assertIn('ref = "v1.2.3"', codex)
        self.assertIn('sparse_paths = [".agents/plugins", ".claude-plugin"]', codex)
        self.assertIn('[plugins."dotnet@tj-agents"]', codex)
        self.assertEqual(4, codex.count('[plugins."'))

    def test_local_scope_uses_the_same_declarations(self):
        self.run_mode("write", "local")
        claude = json.loads((self.root / ".claude" / "settings.local.json").read_text(encoding="utf-8"))
        self.assertIn("dotnet@tj-agents", claude["enabledPlugins"])
        self.assertEqual([], self.run_mode("check", "local"))

    def test_lock_must_select_every_core_plugin(self):
        self.document["plugins"].remove("machine@tj-agents")
        self.save()
        with self.assertRaisesRegex(LockError, "omits core plugins: machine@tj-agents"):
            self.run_mode("write")
        self.assertFalse((self.root / ".claude").exists())

    def test_invalid_locks_are_rejected(self):
        tj = {"repository": "tj-agents/marketplace", "revision": "v1.2.3"}
        core = ["base@tj-agents", "engineering@tj-agents", "machine@tj-agents"]
        cases = {
            "branch revision": {"marketplaces": {"tj-agents": {"repository": "tj-agents/marketplace", "revision": "main"}}},
            "foreign owner": {"marketplaces": {"tj-agents": tj, "x": {"repository": "other/marketplace", "revision": "v1.2.3"}}, "plugins": core + ["p@x"]},
            "tj-agents name on another repository": {"marketplaces": {"tj-agents": {"repository": "Concertable/agents", "revision": "v1.2.3"}}},
            "tj-agents repository under another name": {"marketplaces": {"tj-agents": tj, "other": tj}, "plugins": core + ["p@other"]},
            "missing tj-agents": {"marketplaces": {"agents": {"repository": "Concertable/agents", "revision": "cccccccccccccccccccccccccccccccccccccccc"}}},
            "repeated plugin": {"plugins": core + ["base@tj-agents"]},
            "bare plugin name": {"plugins": core + ["dotnet"]},
            "undeclared marketplace": {"plugins": core + ["concertable@agents"]},
            "unused marketplace": {"marketplaces": {"tj-agents": tj, "agents": {"repository": "Concertable/agents", "revision": "cccccccccccccccccccccccccccccccccccccccc"}}},
            "marketplace extra key": {"marketplaces": {"tj-agents": dict(tj, ref="x")}},
        }
        for label, change in cases.items():
            with self.subTest(label):
                with self.assertRaises(LockError):
                    plugin_lock.validate(dict(self.document, **change))

    def test_a_concertable_marketplace_is_generated_beside_tj_agents(self):
        self.document["marketplaces"]["agents"] = {"repository": "Concertable/agents", "revision": "cccccccccccccccccccccccccccccccccccccccc"}
        self.document["plugins"].append("concertable@agents")
        self.save()
        self.run_mode("write")
        claude = json.loads((self.root / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(
            {"source": {"source": "github", "repo": "Concertable/agents", "ref": "cccccccccccccccccccccccccccccccccccccccc"}, "autoUpdate": False},
            claude["extraKnownMarketplaces"]["agents"],
        )
        self.assertTrue(claude["enabledPlugins"]["concertable@agents"])
        self.assertTrue(claude["enabledPlugins"]["dotnet@tj-agents"])
        codex = (self.root / ".codex" / "config.toml").read_text(encoding="utf-8")
        self.assertIn("[marketplaces.agents]", codex)
        self.assertIn('source = "https://github.com/Concertable/agents.git"', codex)
        self.assertIn('[plugins."concertable@agents"]', codex)
        self.assertEqual([], self.run_mode("check"))

    def test_full_commit_revision_is_accepted(self):
        self.document["marketplaces"]["tj-agents"]["revision"] = "a" * 40
        self.assertEqual("a" * 40, plugin_lock.validate(self.document)[0]["tj-agents"]["revision"])

    def test_overlay_plugin_must_be_selected(self):
        overlay = {"schema_version": 1, "requires": {"marketplaces": [], "plugins": ["tj-agents/react"], "hooks": [], "permissions": {"claude_allow": [], "codex_prefix_rules": []}}}
        (self.lock.parent / "repository-harness.json").write_text(json.dumps(overlay), encoding="utf-8")
        with self.assertRaisesRegex(LockError, "harness-required plugins"):
            self.run_mode("write")

    def test_machine_specific_paths_still_block_generation(self):
        settings = self.root / ".claude" / "settings.json"
        settings.parent.mkdir()
        settings.write_text(json.dumps({"hooks": {"Stop": [{"command": "C:\\Users\\Someone\\hook.ps1"}]}}), encoding="utf-8")
        with self.assertRaisesRegex(LockError, "machine-specific paths"):
            self.run_mode("check")

    def test_cli_resolves_the_lock_from_the_root(self):
        self.assertEqual(0, repo_config.main(["--root", str(self.root), "--mode", "write"]))
        self.assertEqual(0, repo_config.main(["--root", str(self.root), "--mode", "check"]))

    def test_resolve_names_the_plugin_lock_in_the_agents_directory(self):
        self.assertEqual(self.lock, plugin_lock.resolve(self.root))


if __name__ == "__main__":
    unittest.main()
