import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[2] / "machine" / "utility" / "plugin-selection" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adopt_plugins = load("adopt_plugins")
LockError = adopt_plugins.lock_io.LockError
CORE = ["agent-store@tj-agents", "agent@tj-agents", "base@tj-agents", "cli@tj-agents", "engineering@tj-agents", "machine@tj-agents", "workflow@tj-agents"]


def with_core(*plugins):
    return sorted({*CORE, *plugins})


class AdoptPluginsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "project"
        self.root.mkdir()
        self.selection = self.root / ".agents" / "plugins.json"

    def plugins(self):
        return json.loads(self.selection.read_text(encoding="utf-8"))["plugins"]

    def test_stack_resolves_dependencies_without_a_release_pin(self):
        adopt_plugins.run(self.root, ["cpp-msvc"], [], "write")
        self.assertEqual(with_core("cpp@tj-agents", "msvc@tj-agents"), self.plugins())
        claude = json.loads((self.root / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertTrue(claude["extraKnownMarketplaces"]["tj-agents"]["autoUpdate"])
        self.assertNotIn("ref", claude["extraKnownMarketplaces"]["tj-agents"]["source"])
        self.assertEqual([], adopt_plugins.run(self.root, ["cpp-msvc"], [], "check"))

    def test_plugin_repository_stack_selects_template_and_python(self):
        adopt_plugins.run(self.root, ["plugin-repository"], [], "write")
        self.assertEqual(with_core("python@tj-agents", "template@tj-agents"), self.plugins())

    def test_personal_is_explicit_and_selects_only_its_capability_dependencies(self):
        adopt_plugins.run(self.root, ["react"], [], "write")
        self.assertNotIn("personal@tj-agents", self.plugins())
        adopt_plugins.run(self.root, [], ["personal"], "write")
        self.assertEqual(["agent-store@tj-agents", "agent@tj-agents", "base@tj-agents", "cli@tj-agents", "engineering@tj-agents", "machine@tj-agents", "personal@tj-agents", "react@tj-agents", "workflow@tj-agents"], self.plugins())
        self.assertEqual([], adopt_plugins.run(self.root, [], ["personal"], "check"))
        self.assertEqual([], adopt_plugins.run(self.root, [], ["machine"], "check"))
        claude = json.loads((self.root / ".claude/settings.json").read_text(encoding="utf-8"))
        self.assertTrue(claude["enabledPlugins"]["personal@tj-agents"])
        self.assertTrue(claude["enabledPlugins"]["engineering@tj-agents"])
        self.assertIn('[plugins."personal@tj-agents"]', (self.root / ".codex/config.toml").read_text(encoding="utf-8"))
        self.assertIn('[plugins."engineering@tj-agents"]', (self.root / ".codex/config.toml").read_text(encoding="utf-8"))

    def test_infonetica_selects_engineering_without_personal(self):
        adopt_plugins.run(self.root, [], ["infonetica"], "write")
        self.assertEqual(["agent-store@tj-agents", "agent@tj-agents", "base@tj-agents", "cli@tj-agents", "engineering@tj-agents", "infonetica@tj-agents", "machine@tj-agents", "work@tj-agents", "workflow@tj-agents"], self.plugins())
        claude = json.loads((self.root / ".claude/settings.json").read_text(encoding="utf-8"))
        self.assertTrue(claude["enabledPlugins"]["engineering@tj-agents"])
        codex = (self.root / ".codex/config.toml").read_text(encoding="utf-8")
        self.assertIn('[plugins."engineering@tj-agents"]', codex)
        self.assertNotIn('[plugins."personal@tj-agents"]', codex)
        self.assertEqual([], adopt_plugins.run(self.root, [], ["infonetica"], "check"))

    def test_repository_ownership_does_not_select_personal(self):
        for remote in ("git@github.com:tomjseery/Concertable.git",
                       "https://github.com/tj-agents/infonetica.git",
                       "https://github.com/Infonetica/cris-erm.git"):
            with self.subTest(remote=remote), tempfile.TemporaryDirectory() as temp:
                root = Path(temp).resolve()
                subprocess.run(["git", "init", "-q", str(root)], check=True)
                subprocess.run(["git", "-C", str(root), "remote", "add", "origin", remote], check=True)
                adopt_plugins.run(root, [], ["machine"], "write")
                selected = json.loads((root / ".agents/plugins.json").read_text(encoding="utf-8"))["plugins"]
                self.assertNotIn("personal@tj-agents", selected)

    def test_existing_selection_is_extended_and_unknown_packages_are_kept(self):
        self.selection.parent.mkdir()
        self.selection.write_text(json.dumps({"schema_version": 1, "marketplaces": {"tj-agents": {"repository": "tj-agents/marketplace"}}, "plugins": ["newcomer@tj-agents"]}), encoding="utf-8")
        adopt_plugins.run(self.root, [], ["react"], "write")
        self.assertEqual(with_core("newcomer@tj-agents", "react@tj-agents"), self.plugins())

    def test_efcore_plugin_selects_dotnet_dependency(self):
        adopt_plugins.run(self.root, [], ["efcore"], "write")
        self.assertEqual(with_core("dotnet@tj-agents", "efcore@tj-agents"), self.plugins())
        codex = (self.root / ".codex/config.toml").read_text(encoding="utf-8")
        for plugin in CORE:
            self.assertIn(f'[plugins."{plugin}"]', codex)

    def test_foreign_selection_requires_a_declared_source_and_survives_later_adoption(self):
        with self.assertRaises(LockError):
            adopt_plugins.run(self.root, [], ["concertable@agents"], "write")
        adopt_plugins.run(self.root, [], ["concertable@agents"], "write", marketplaces=["agents=Concertable/agents"])
        adopt_plugins.run(self.root, ["react"], [], "write")
        self.assertEqual(with_core("concertable@agents", "react@tj-agents"), self.plugins())
        before = self.selection.read_bytes()
        with self.assertRaisesRegex(LockError, "more than once"):
            adopt_plugins.run(self.root, [], [], "write", marketplaces=["agents=Concertable/agents"] * 2)
        self.assertEqual(before, self.selection.read_bytes())

    def test_default_adoption_selects_the_core_packages(self):
        adopt_plugins.run(self.root, [], [], "write")
        self.assertEqual(CORE, self.plugins())

    def test_engineering_does_not_select_a_recording_profile(self):
        adopt_plugins.run(self.root, [], ["engineering"], "write")
        self.assertEqual(CORE, self.plugins())
        claude = json.loads((self.root / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertNotIn("work-items@tj-agents", claude["enabledPlugins"])
        self.assertNotIn("personal@tj-agents", claude["enabledPlugins"])
        self.assertNotIn("infonetica@tj-agents", claude["enabledPlugins"])
        codex = (self.root / ".codex" / "config.toml").read_text(encoding="utf-8")
        self.assertNotIn('[plugins."work-items@tj-agents"]', codex)
        self.assertNotIn('[plugins."personal@tj-agents"]', codex)
        self.assertNotIn('[plugins."infonetica@tj-agents"]', codex)
        self.assertEqual([], adopt_plugins.run(self.root, [], ["engineering"], "check"))

    def test_local_scope_preserves_project_settings(self):
        adopt_plugins.run(self.root, [], ["react"], "write", "local")
        self.assertTrue((self.root / ".claude" / "settings.local.json").is_file())
        self.assertFalse((self.root / ".claude" / "settings.json").exists())

    def test_unknown_stack_and_plugin_are_rejected(self):
        with self.assertRaisesRegex(LockError, "Unknown stack: cobol"):
            adopt_plugins.run(self.root, ["cobol"], [], "write")
        with self.assertRaisesRegex(LockError, "Unknown plugin: cobol"):
            adopt_plugins.run(self.root, [], ["cobol"], "write")

    def test_cli_reports_drift(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(1, adopt_plugins.main(["--root", str(self.root), "--stack", "react", "--mode", "check"]))
            self.assertEqual(0, adopt_plugins.main(["--root", str(self.root), "--stack", "react", "--mode", "write"]))
        self.assertIn(".agents/plugins.json", output.getvalue())


if __name__ == "__main__":
    unittest.main()
