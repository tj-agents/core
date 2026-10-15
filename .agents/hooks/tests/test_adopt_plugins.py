import contextlib
import importlib.util
import io
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


adopt_plugins = load("adopt_plugins")
LockError = adopt_plugins.lock_io.LockError


class AdoptPluginsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "project"
        self.root.mkdir()
        self.lock = self.root / ".agents" / "plugins.lock.json"

    def plugins(self):
        return json.loads(self.lock.read_text(encoding="utf-8"))["plugins"]

    def test_stack_resolves_to_plugins_and_adds_core_without_a_catalog(self):
        adopt_plugins.run(self.root, "v1.0.0", ["cpp-msvc"], [], "write")
        self.assertEqual(["base", "cpp", "engineering", "machine", "msvc"], self.plugins())
        self.assertFalse((self.root / ".agents" / "catalog").exists())
        claude = json.loads((self.root / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertTrue(claude["enabledPlugins"]["msvc@tj-agents"])
        self.assertEqual("v1.0.0", claude["extraKnownMarketplaces"]["tj-agents"]["source"]["ref"])
        self.assertEqual([], adopt_plugins.run(self.root, None, ["cpp-msvc"], [], "check"))

    def test_required_plugins_are_added_for_an_explicit_plugin(self):
        adopt_plugins.run(self.root, "v1.0.0", [], ["azure"], "write")
        self.assertIn("dotnet", self.plugins())

    def test_extending_keeps_existing_plugins_and_revision(self):
        adopt_plugins.run(self.root, "v1.0.0", ["dotnet"], [], "write")
        adopt_plugins.run(self.root, None, ["react"], [], "write")
        document = json.loads(self.lock.read_text(encoding="utf-8"))
        self.assertEqual("v1.0.0", document["marketplace"]["revision"])
        self.assertEqual(["base", "dotnet", "engineering", "machine", "react"], document["plugins"])

    def test_preview_changes_nothing(self):
        drift = adopt_plugins.run(self.root, "v1.0.0", ["dotnet"], [], "preview")
        self.assertEqual([".agents/plugins.lock.json", ".claude/settings.json", ".codex/config.toml"], sorted(drift))
        self.assertFalse((self.root / ".agents").exists())

    def test_unknown_stack_and_plugin_are_rejected_with_choices(self):
        with self.assertRaisesRegex(LockError, "Unknown stack: cobol; choose from .*dotnet"):
            adopt_plugins.run(self.root, "v1.0.0", ["cobol"], [], "write")
        with self.assertRaisesRegex(LockError, "Unknown plugin: cobol"):
            adopt_plugins.run(self.root, "v1.0.0", [], ["cobol"], "write")
        self.assertFalse((self.root / ".agents").exists())

    def test_new_lock_needs_a_revision_and_an_old_schema_is_not_extended(self):
        with self.assertRaisesRegex(LockError, "needs --marketplace-revision"):
            adopt_plugins.run(self.root, None, ["dotnet"], [], "write")
        self.lock.parent.mkdir()
        self.lock.write_text(json.dumps({"schema_version": 1, "plugins": []}), encoding="utf-8")
        with self.assertRaisesRegex(LockError, "not a schema 2 plugin lock"):
            adopt_plugins.run(self.root, "v1.0.0", ["dotnet"], [], "write")

    def test_cli_reports_drift_and_exit_status(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(1, adopt_plugins.main(["--root", str(self.root), "--marketplace-revision", "v1.0.0", "--stack", "react", "--mode", "check"]))
            self.assertEqual(0, adopt_plugins.main(["--root", str(self.root), "--marketplace-revision", "v1.0.0", "--stack", "react", "--mode", "write"]))
            self.assertEqual(0, adopt_plugins.main(["--root", str(self.root), "--stack", "react", "--mode", "check"]))
        self.assertIn("Drift in: .agents/plugins.lock.json", output.getvalue())

    def test_every_stack_and_requirement_names_a_roster_plugin(self):
        roster = adopt_plugins.load_roster()
        for name, requires in roster["plugins"].items():
            self.assertLessEqual(set(requires), set(roster["plugins"]), name)
        for stack, names in roster["stacks"].items():
            self.assertLessEqual(set(names), set(roster["plugins"]), stack)


    def test_extending_keeps_a_plugin_the_roster_does_not_know(self):
        self.lock.parent.mkdir()
        document = {"schema_version": 2, "marketplace": {"repository": "tj-agents/marketplace", "revision": "v1.0.0"},
                    "plugins": ["base", "engineering", "machine", "newcomer"]}
        self.lock.write_text(json.dumps(document), encoding="utf-8")
        adopt_plugins.run(self.root, None, ["react"], [], "write")
        self.assertEqual(["base", "engineering", "machine", "newcomer", "react"], self.plugins())

    def test_malformed_existing_lock_is_a_reported_error_not_a_crash(self):
        self.lock.parent.mkdir()
        for text in ('{"schema_version": 2}', '{"schema_version": 2, "plugins": [], "marketplace": null}'):
            with self.subTest(text=text):
                self.lock.write_text(text, encoding="utf-8")
                with self.assertRaises(LockError):
                    adopt_plugins.run(self.root, None, ["react"], [], "write")


    def test_existing_plugins_get_their_roster_dependencies_on_extension(self):
        self.lock.parent.mkdir()
        document = {"schema_version": 2, "marketplace": {"repository": "tj-agents/marketplace", "revision": "v1.0.0"},
                    "plugins": ["azure", "base", "engineering", "machine"]}
        self.lock.write_text(json.dumps(document), encoding="utf-8")
        adopt_plugins.run(self.root, None, ["react"], [], "write")
        self.assertIn("dotnet", self.plugins())

    def test_a_lock_missing_core_plugins_is_repaired(self):
        self.lock.parent.mkdir()
        document = {"schema_version": 2, "marketplace": {"repository": "tj-agents/marketplace", "revision": "v1.0.0"}, "plugins": ["react"]}
        self.lock.write_text(json.dumps(document), encoding="utf-8")
        adopt_plugins.run(self.root, None, [], [], "write")
        self.assertEqual(["base", "engineering", "machine", "react"], self.plugins())

    def test_a_local_scope_clone_is_refused(self):
        self.lock.parent.mkdir()
        (self.root / ".agents" / "repo-capabilities.local.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(LockError, "adopted with --scope local"):
            adopt_plugins.run(self.root, "v1.0.0", ["react"], [], "write")


if __name__ == "__main__":
    unittest.main()
