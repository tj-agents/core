import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOKS_DIR))

from dev_rules import find_profile, matches, resolve_rules  # noqa: E402

HOOK_SRC = HOOKS_DIR / "session_floor.py"
RUNTIME_SRC = HOOKS_DIR / "hook_runtime.py"
RULES_SRC = HOOKS_DIR / "dev_rules.py"
FLOOR_TEXT = "# The behavioral floor\n\nTake the scalable approach.\n"
RULE_TEXT = "# Nothing is live\n\nDelete the old shape.\n"


class MatchesTests(unittest.TestCase):
    def test_absent_condition_applies_everywhere(self):
        self.assertTrue(matches({}, {"lifecycle": "launched"}))
        self.assertTrue(matches(None, {}))

    def test_undeclared_key_never_matches(self):
        # A rule reaches a repo only where that repo positively declared the property.
        self.assertFalse(matches({"lifecycle": "pre-launch"}, {"stack": ["dotnet"]}))

    def test_scalar_equality(self):
        self.assertTrue(matches({"lifecycle": "pre-launch"}, {"lifecycle": "pre-launch"}))
        self.assertFalse(matches({"lifecycle": "pre-launch"}, {"lifecycle": "launched"}))

    def test_profile_list_membership(self):
        self.assertTrue(matches({"stack": "dotnet"}, {"stack": ["dotnet", "react"]}))
        self.assertFalse(matches({"stack": "python"}, {"stack": ["dotnet", "react"]}))

    def test_condition_list_is_any_of(self):
        self.assertTrue(matches({"lifecycle": ["pre-launch", "beta"]}, {"lifecycle": "beta"}))
        self.assertFalse(matches({"lifecycle": ["pre-launch", "beta"]}, {"lifecycle": "launched"}))

    def test_multiple_conditions_are_all_of(self):
        profile = {"lifecycle": "pre-launch", "stack": ["dotnet"]}
        self.assertTrue(matches({"lifecycle": "pre-launch", "stack": "dotnet"}, profile))
        self.assertFalse(matches({"lifecycle": "pre-launch", "stack": "react"}, profile))

    def test_non_dict_profile_never_matches(self):
        self.assertFalse(matches({"lifecycle": "pre-launch"}, None))


class ResolveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name).resolve()
        self.payload = base / "plugin"
        self.doc = self.payload / "standards" / "rules" / "pre-launch.md"
        self.doc.parent.mkdir(parents=True)
        self.doc.write_text(RULE_TEXT, encoding="utf-8")
        self.catalogue = self.payload / "standards" / "rules" / "catalogue.json"
        self.write_catalogue({"lifecycle": "pre-launch"})
        self.repo = base / "repo"
        (self.repo / ".agents").mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def write_catalogue(self, applies_when, doc="standards/rules/pre-launch.md"):
        self.catalogue.write_text(
            json.dumps({"schema_version": 1, "rules": [
                {"id": "pre-launch", "doc": doc, "applies_when": applies_when}]}),
            encoding="utf-8")

    def write_profile(self, profile, at=None):
        (at or self.repo / ".agents" / "profile.json").write_text(
            json.dumps(profile), encoding="utf-8")

    def test_matching_rule_is_delivered(self):
        self.write_profile({"lifecycle": "pre-launch"})
        self.assertEqual([r[0] for r in resolve_rules(self.repo, self.payload)], ["pre-launch"])

    def test_non_matching_rule_is_withheld(self):
        self.write_profile({"lifecycle": "launched"})
        self.assertEqual(resolve_rules(self.repo, self.payload), [])

    def test_no_profile_yields_nothing(self):
        self.assertEqual(resolve_rules(self.repo, self.payload), [])

    def test_profile_found_from_subdirectory(self):
        self.write_profile({"lifecycle": "pre-launch"})
        sub = self.repo / "api" / "src"
        sub.mkdir(parents=True)
        self.assertEqual([r[0] for r in resolve_rules(sub, self.payload)], ["pre-launch"])

    def test_malformed_profile_is_ignored(self):
        (self.repo / ".agents" / "profile.json").write_text("{not json", encoding="utf-8")
        self.assertIsNone(find_profile(self.repo))
        self.assertEqual(resolve_rules(self.repo, self.payload), [])

    def test_missing_rule_doc_is_skipped_not_fatal(self):
        self.write_profile({"lifecycle": "pre-launch"})
        self.write_catalogue({"lifecycle": "pre-launch"}, doc="standards/rules/absent.md")
        self.assertEqual(resolve_rules(self.repo, self.payload), [])

    def test_malformed_catalogue_is_ignored(self):
        self.write_profile({"lifecycle": "pre-launch"})
        self.catalogue.write_text("{not json", encoding="utf-8")
        self.assertEqual(resolve_rules(self.repo, self.payload), [])


class InjectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name).resolve()
        self.plugin = base / "plugin"
        (self.plugin / "hooks").mkdir(parents=True)
        for src in (HOOK_SRC, RUNTIME_SRC, RULES_SRC):
            shutil.copy(src, self.plugin / "hooks" / src.name)
        floor = self.plugin / "standards" / "process" / "FLOOR.md"
        floor.parent.mkdir(parents=True)
        floor.write_text(FLOOR_TEXT, encoding="utf-8")
        rule = self.plugin / "standards" / "rules" / "pre-launch.md"
        rule.parent.mkdir(parents=True)
        rule.write_text(RULE_TEXT, encoding="utf-8")
        (self.plugin / "standards" / "rules" / "catalogue.json").write_text(
            json.dumps({"schema_version": 1, "rules": [{
                "id": "pre-launch",
                "doc": "standards/rules/pre-launch.md",
                "applies_when": {"lifecycle": "pre-launch"}}]}),
            encoding="utf-8")
        self.hook = self.plugin / "hooks" / "session_floor.py"
        self.repo = base / "repo"
        (self.repo / ".agents").mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def run_hook(self, cwd):
        env = dict(os.environ)
        env["CLAUDE_PLUGIN_ROOT"] = str(self.plugin)
        return subprocess.run(
            [sys.executable, str(self.hook)],
            input=json.dumps({"hook_event_name": "SessionStart",
                              "session_id": str(uuid.uuid4()), "cwd": str(cwd)}),
            capture_output=True, text=True, env=env)

    def test_profile_alone_opts_a_repo_in(self):
        # No skill-routes.json: declaring a profile is enough to become standards-managed.
        (self.repo / ".agents" / "profile.json").write_text(
            json.dumps({"lifecycle": "pre-launch"}), encoding="utf-8")
        result = self.run_hook(self.repo)
        self.assertEqual(result.returncode, 0)
        self.assertIn("The behavioral floor", result.stdout)
        self.assertIn("Delete the old shape", result.stdout)

    def test_launched_profile_gets_floor_without_the_rule(self):
        (self.repo / ".agents" / "profile.json").write_text(
            json.dumps({"lifecycle": "launched"}), encoding="utf-8")
        result = self.run_hook(self.repo)
        self.assertIn("The behavioral floor", result.stdout)
        self.assertNotIn("Delete the old shape", result.stdout)

    def test_unmanaged_repo_stays_silent(self):
        result = self.run_hook(self.repo)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")
