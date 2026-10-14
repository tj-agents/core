import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[2] / "machine" / "utility" / "bootstrap-capabilities" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


plugin_lock = load("plugin_lock")
repo_config = load("repo_config")
BootstrapError = repo_config.bootstrap.BootstrapError


class PluginLockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.lock = self.root / ".agents" / "plugins.lock.json"
        self.lock.parent.mkdir()
        self.document = {
            "schema_version": 2,
            "marketplace": {"repository": "tj-agents/marketplace", "revision": "v1.2.3"},
            "plugins": ["base", "engineering", "machine", "dotnet"],
        }
        self.save()

    def save(self):
        self.lock.write_text(json.dumps(self.document), encoding="utf-8")

    def run_mode(self, mode, scope="project"):
        return repo_config.run(self.lock, None, mode, root=self.root, scope=scope)

    def test_generates_both_hosts_from_the_marketplace_pin_without_a_catalog(self):
        self.assertEqual([".claude/settings.json", ".codex/config.toml"], self.run_mode("check"))
        self.run_mode("write")
        self.assertEqual([], self.run_mode("check"))
        claude = json.loads((self.root / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(
            {"tj-agents": {"source": {"source": "github", "repo": "tj-agents/marketplace", "ref": "v1.2.3"}, "autoUpdate": False}},
            claude["extraKnownMarketplaces"],
        )
        self.assertEqual({f"{name}@tj-agents": True for name in self.document["plugins"]}, claude["enabledPlugins"])
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
        self.document["plugins"].remove("machine")
        self.save()
        with self.assertRaisesRegex(BootstrapError, "omits core plugins: tj-agents/machine"):
            self.run_mode("write")
        self.assertFalse((self.root / ".claude").exists())

    def test_invalid_locks_are_rejected(self):
        cases = {
            "branch revision": ("marketplace", {"repository": "tj-agents/marketplace", "revision": "main"}),
            "foreign marketplace": ("marketplace", {"repository": "other/marketplace", "revision": "v1.2.3"}),
            "repeated plugin": ("plugins", ["base", "base", "engineering", "machine"]),
            "plugin identity": ("plugins", ["base", "engineering", "machine", "tj-agents/dotnet"]),
            "marketplace extra key": ("marketplace", {"repository": "tj-agents/marketplace", "revision": "v1.2.3", "ref": "x"}),
        }
        for label, (key, value) in cases.items():
            with self.subTest(label):
                broken = dict(self.document, **{key: value})
                with self.assertRaises(BootstrapError):
                    plugin_lock.validate(broken)

    def test_full_commit_revision_is_accepted(self):
        self.document["marketplace"]["revision"] = "a" * 40
        self.assertEqual("a" * 40, plugin_lock.validate(self.document)[0]["revision"])

    def test_overlay_plugin_must_be_selected(self):
        overlay = {"schema_version": 1, "requires": {"marketplaces": [], "plugins": ["tj-agents/react"], "hooks": [], "permissions": {"claude_allow": [], "codex_prefix_rules": []}}}
        (self.lock.parent / "repository-harness.json").write_text(json.dumps(overlay), encoding="utf-8")
        with self.assertRaisesRegex(BootstrapError, "harness-required plugins"):
            self.run_mode("write")

    def test_machine_specific_paths_still_block_generation(self):
        settings = self.root / ".claude" / "settings.json"
        settings.parent.mkdir()
        settings.write_text(json.dumps({"hooks": {"Stop": [{"command": "C:\\Users\\Someone\\hook.ps1"}]}}), encoding="utf-8")
        with self.assertRaisesRegex(BootstrapError, "machine-specific paths"):
            self.run_mode("check")

    def test_resolve_prefers_the_current_name_and_forwards_the_legacy_one(self):
        legacy = self.lock.parent / "capabilities.lock.json"
        self.assertEqual(self.lock, plugin_lock.resolve(self.root))
        self.lock.rename(legacy)
        self.assertEqual(legacy, plugin_lock.resolve(self.root))
        self.save()
        with self.assertRaisesRegex(BootstrapError, "remove the legacy lock"):
            plugin_lock.resolve(self.root)

    def test_cli_resolves_the_lock_from_the_root(self):
        self.assertEqual(0, repo_config.main(["--root", str(self.root), "--mode", "write"]))
        self.assertEqual(0, repo_config.main(["--root", str(self.root), "--mode", "check"]))


if __name__ == "__main__":
    unittest.main()
