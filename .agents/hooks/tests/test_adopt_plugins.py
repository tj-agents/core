import contextlib
import importlib.util
import io
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


adopt_plugins = load("adopt_plugins")
LockError = adopt_plugins.lock_io.LockError


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
        self.assertEqual(["cpp", "msvc"], self.plugins())
        claude = json.loads((self.root / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertTrue(claude["extraKnownMarketplaces"]["tj-agents"]["autoUpdate"])
        self.assertNotIn("ref", claude["extraKnownMarketplaces"]["tj-agents"]["source"])
        self.assertEqual([], adopt_plugins.run(self.root, ["cpp-msvc"], [], "check"))

    def test_existing_selection_is_extended_and_unknown_packages_are_kept(self):
        self.selection.parent.mkdir()
        self.selection.write_text(json.dumps({"schema_version": 1, "marketplace": {"repository": "tj-agents/marketplace"}, "plugins": ["newcomer"]}), encoding="utf-8")
        adopt_plugins.run(self.root, [], ["react"], "write")
        self.assertEqual(["newcomer", "react"], self.plugins())

    def test_schema_two_lock_is_migrated_once_and_discards_its_pin(self):
        legacy = self.root / ".agents" / "plugins.lock.json"
        legacy.parent.mkdir()
        legacy.write_text(json.dumps({"schema_version": 2, "marketplace": {"repository": "tj-agents/marketplace", "revision": "v1.2.3"}, "plugins": ["base"]}), encoding="utf-8")
        adopt_plugins.run(self.root, [], ["react"], "write")
        selection = json.loads(self.selection.read_text(encoding="utf-8"))
        self.assertEqual({"repository": "tj-agents/marketplace"}, selection["marketplace"])
        self.assertNotIn("revision", json.dumps(selection))
        self.assertFalse(legacy.exists())
        self.assertEqual([], adopt_plugins.run(self.root, [], ["react"], "check"))

    def test_default_adoption_selects_the_core_packages(self):
        adopt_plugins.run(self.root, [], [], "write")
        self.assertEqual(["base", "engineering", "machine"], self.plugins())

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
