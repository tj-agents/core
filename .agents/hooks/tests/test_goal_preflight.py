import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS = ROOT / ".agents" / "workflows"
sys.path.insert(0, str(WORKFLOWS))
import workflow_ops  # noqa: E402


class ScopePrecedenceTests(unittest.TestCase):
    """The order is Claude's own: managed beats local beats project beats user. A check that read the
    wrong one would pass on a machine whose effective evaluator is still Haiku."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / ".claude").mkdir()

    def write(self, name, model):
        path = self.root / ".claude" / name
        path.write_text(
            json.dumps({"env": {workflow_ops.GOAL_EVALUATOR_VARIABLE: model}}), encoding="utf-8"
        )

    def scopes(self):
        return [name for name, _ in workflow_ops.goal_evaluator_scopes(self.root)]

    def test_local_outranks_project_which_outranks_user(self):
        self.assertEqual(
            ["local", "project", "user"], [name for name in self.scopes() if name != "managed"]
        )

    def test_managed_is_read_before_every_writable_scope(self):
        self.assertEqual("managed", self.scopes()[0])

    def test_a_settings_file_without_the_variable_reads_as_absent(self):
        (self.root / ".claude" / "settings.json").write_text(
            json.dumps({"env": {"OTHER": "x"}}), encoding="utf-8"
        )
        self.assertIsNone(workflow_ops.settings_env(self.root / ".claude" / "settings.json"))

    def test_an_unreadable_settings_file_reads_as_absent(self):
        (self.root / ".claude" / "settings.json").write_text("{", encoding="utf-8")
        self.assertIsNone(workflow_ops.settings_env(self.root / ".claude" / "settings.json"))


class PreflightVerdictTests(unittest.TestCase):
    """The operation as a subprocess, so the exit code the skill stops on is the one asserted."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        (self.repo / ".claude").mkdir()

    def write_project(self, model):
        (self.repo / ".claude" / "settings.json").write_text(
            json.dumps({"env": {workflow_ops.GOAL_EVALUATOR_VARIABLE: model}}), encoding="utf-8"
        )

    def run_preflight(self, session=None):
        environment = dict(os.environ)
        environment.pop(workflow_ops.GOAL_EVALUATOR_VARIABLE, None)
        environment.pop("HOME", None)
        environment.pop("USERPROFILE", None)
        # An empty home keeps this machine's real user-scope setting out of the verdict.
        home = Path(self.temp.name) / "home"
        home.mkdir(exist_ok=True)
        environment["HOME"] = str(home)
        environment["USERPROFILE"] = str(home)
        if session is not None:
            environment[workflow_ops.GOAL_EVALUATOR_VARIABLE] = session
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(WORKFLOWS / "workflow_ops.py"),
                "--root",
                str(self.repo),
                "--workflow-run-id",
                "goal-preflight-test",
                "goal-preflight",
            ],
            capture_output=True,
            text=True,
            cwd=str(self.repo),
            env=environment,
        )
        return completed, json.loads(completed.stdout.strip().splitlines()[-1])

    def test_a_persisted_sonnet_mapping_passes(self):
        self.write_project("claude-sonnet-5")
        completed, result = self.run_preflight()
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertTrue(result["ready"])
        self.assertIsNone(result["stop_reason"])
        self.assertEqual("project", result["resolved_from"])

    def test_nothing_configured_anywhere_stops_the_skill(self):
        completed, result = self.run_preflight()
        self.assertEqual(1, completed.returncode)
        self.assertFalse(result["ready"])
        self.assertEqual("goal-evaluator-model-unavailable", result["stop_reason"])

    def test_a_non_sonnet_mapping_stops_the_skill(self):
        self.write_project("claude-haiku-4-5-20251001")
        completed, result = self.run_preflight()
        self.assertEqual(1, completed.returncode)
        self.assertFalse(result["evaluator_is_sonnet"])
        self.assertEqual("goal-evaluator-model-unavailable", result["stop_reason"])

    def test_a_session_value_with_nothing_persisted_stops_the_skill(self):
        # The next session reads the files, not this process's environment, so a value that lives
        # only here would be silently lost - which is the failure the stop code exists for.
        completed, result = self.run_preflight(session="claude-sonnet-5")
        self.assertEqual(1, completed.returncode)
        self.assertTrue(result["evaluator_is_sonnet"])
        self.assertFalse(result["survives_a_fresh_session"])
        self.assertEqual("goal-evaluator-model-unavailable", result["stop_reason"])

    def test_a_higher_precedence_non_sonnet_scope_beats_a_lower_sonnet_one(self):
        self.write_project("claude-sonnet-5")
        (self.repo / ".claude" / "settings.local.json").write_text(
            json.dumps({"env": {workflow_ops.GOAL_EVALUATOR_VARIABLE: "claude-haiku-4-5-20251001"}}),
            encoding="utf-8",
        )
        completed, result = self.run_preflight()
        self.assertEqual(1, completed.returncode)
        self.assertEqual("local", result["resolved_from"])
        self.assertEqual("goal-evaluator-model-unavailable", result["stop_reason"])




if __name__ == "__main__":
    unittest.main()
