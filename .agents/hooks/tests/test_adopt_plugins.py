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
        return [item.removesuffix("@tj-agents") for item in json.loads(self.lock.read_text(encoding="utf-8"))["plugins"]]

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
        self.assertEqual("v1.0.0", document["marketplaces"]["tj-agents"]["revision"])
        self.assertEqual(["base", "dotnet", "engineering", "machine", "react"], self.plugins())

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
        with self.assertRaisesRegex(LockError, "not a schema 3 plugin lock"):
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
        document = {"schema_version": 3, "marketplaces": {"tj-agents": {"repository": "tj-agents/marketplace", "revision": "v1.0.0"}},
                    "plugins": ["base@tj-agents", "engineering@tj-agents", "machine@tj-agents", "newcomer@tj-agents"]}
        self.lock.write_text(json.dumps(document), encoding="utf-8")
        adopt_plugins.run(self.root, None, ["react"], [], "write")
        self.assertEqual(["base", "engineering", "machine", "newcomer", "react"], self.plugins())

    def test_malformed_existing_lock_is_a_reported_error_not_a_crash(self):
        self.lock.parent.mkdir()
        for text in ('{"schema_version": 3}', '{"schema_version": 3, "plugins": [], "marketplaces": null}'):
            with self.subTest(text=text):
                self.lock.write_text(text, encoding="utf-8")
                with self.assertRaises(LockError):
                    adopt_plugins.run(self.root, None, ["react"], [], "write")


    def test_existing_plugins_get_their_roster_dependencies_on_extension(self):
        self.lock.parent.mkdir()
        document = {"schema_version": 3, "marketplaces": {"tj-agents": {"repository": "tj-agents/marketplace", "revision": "v1.0.0"}},
                    "plugins": ["azure@tj-agents", "base@tj-agents", "engineering@tj-agents", "machine@tj-agents"]}
        self.lock.write_text(json.dumps(document), encoding="utf-8")
        adopt_plugins.run(self.root, None, ["react"], [], "write")
        self.assertIn("dotnet", self.plugins())

    def test_a_lock_missing_core_plugins_is_repaired(self):
        self.lock.parent.mkdir()
        document = {"schema_version": 3, "marketplaces": {"tj-agents": {"repository": "tj-agents/marketplace", "revision": "v1.0.0"}}, "plugins": ["react@tj-agents"]}
        self.lock.write_text(json.dumps(document), encoding="utf-8")
        adopt_plugins.run(self.root, None, [], [], "write")
        self.assertEqual(["base", "engineering", "machine", "react"], self.plugins())

    def test_a_local_scope_clone_is_refused(self):
        self.lock.parent.mkdir()
        (self.root / ".agents" / "repo-capabilities.local.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(LockError, "adopted with --scope local"):
            adopt_plugins.run(self.root, "v1.0.0", ["react"], [], "write")


    def test_duplicate_or_unhashable_plugin_entries_are_reported_not_normalised(self):
        self.lock.parent.mkdir()
        for plugins in (["base@tj-agents", "base@tj-agents", "engineering@tj-agents", "machine@tj-agents"], ["base@tj-agents", ["x"], "engineering@tj-agents", "machine@tj-agents"]):
            with self.subTest(plugins=plugins):
                document = {"schema_version": 3, "marketplaces": {"tj-agents": {"repository": "tj-agents/marketplace", "revision": "v1.0.0"}}, "plugins": plugins}
                self.lock.write_text(json.dumps(document), encoding="utf-8")
                with self.assertRaisesRegex(LockError, "list of unique plugin names"):
                    adopt_plugins.run(self.root, None, ["react"], [], "write")

    def test_a_second_run_with_no_request_is_stable(self):
        adopt_plugins.run(self.root, "v1.0.0", ["azure"], [], "write")
        self.assertEqual([], adopt_plugins.run(self.root, None, [], [], "check"))


    def test_a_foreign_plugin_needs_and_keeps_its_declared_marketplace(self):
        with self.assertRaisesRegex(LockError, "needs its marketplace declared"):
            adopt_plugins.run(self.root, "v1.0.0", ["dotnet"], ["concertable@agents"], "write")
        adopt_plugins.run(self.root, "v1.0.0", ["dotnet"], ["concertable@agents"], "write",
                          ["agents=Concertable/agents@cccccccccccccccccccccccccccccccccccccccc"])
        document = json.loads(self.lock.read_text(encoding="utf-8"))
        self.assertEqual({"repository": "Concertable/agents", "revision": "cccccccccccccccccccccccccccccccccccccccc"}, document["marketplaces"]["agents"])
        self.assertIn("concertable@agents", document["plugins"])
        adopt_plugins.run(self.root, None, ["react"], [], "write")
        self.assertIn("concertable@agents", self.plugins())
        self.assertEqual([], adopt_plugins.run(self.root, None, [], [], "check"))

    def test_a_marketplace_outside_the_allowed_owners_is_rejected(self):
        with self.assertRaisesRegex(LockError, "owned by tj-agents or Concertable"):
            adopt_plugins.run(self.root, "v1.0.0", [], ["x@other"], "write", ["other=someone/plugins@cccccccccccccccccccccccccccccccccccccccc"])
        self.assertFalse((self.root / ".agents").exists())


    def test_malformed_and_conflicting_arguments_are_rejected(self):
        cases = (
            (["base@tj-agents@x"], [], "--plugin must be"),
            (["react@"], [], "--plugin must be"),
            (["concertable@agents"], ["agents=Concertable/agents@cccccccccccccccccccccccccccccccccccccccc", "agents=Concertable/other@cccccccccccccccccccccccccccccccccccccccc"], "given more than once"),
            ([], ["tj-agents=tj-agents/marketplace@v1.1.0"], "either --marketplace-revision"),
        )
        for plugins, marketplaces, message in cases:
            with self.subTest(plugins=plugins, marketplaces=marketplaces):
                with self.assertRaisesRegex(LockError, message):
                    adopt_plugins.run(self.root, "v1.0.0", [], plugins, "write", marketplaces)
        self.assertFalse((self.root / ".agents").exists())


if __name__ == "__main__":
    unittest.main()
