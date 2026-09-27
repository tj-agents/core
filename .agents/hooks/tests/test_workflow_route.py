import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".agents/hooks/workflow_route.py"


class WorkflowRouteSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="workflow route ")
        self.addCleanup(self.temp.cleanup)
        self.cwd = Path(self.temp.name)

    def write_goal(self, status="in progress"):
        (self.cwd / "GOAL.md").write_text(
            f"# Goal\n\nStatus: {status}\n\nComplete all three phases.\n",
            encoding="utf-8",
        )

    def run_hook(self, prompt, event="UserPromptSubmit"):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT)],
            input=json.dumps({"hook_event_name": event, "cwd": str(self.cwd), "prompt": prompt}),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=20,
        )

    def test_active_goal_and_execution_prompt_load_the_full_canonical_workflow(self):
        self.write_goal()
        result = self.run_hook("Continue and complete the active goal through all three phases.")
        self.assertEqual(0, result.returncode, result.stderr)
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        canonical = (ROOT / ".agents/engineering/workflow/plan-execution/SKILL.md").read_text(
            encoding="utf-8"
        ).strip()
        self.assertIn("engineering:plan-execution automatically selected", context)
        self.assertIn("source SHA-256", context)
        self.assertEqual(canonical, context.split("\n\n", 1)[1])

    def test_resume_the_active_plan_routes_as_execution(self):
        self.write_goal()
        result = self.run_hook("Resume the plan and carry it through delivery.")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("engineering:plan-execution", result.stdout)

    def test_active_side_workstream_handoff_loads_the_full_canonical_workflow(self):
        self.write_goal()
        result = self.run_hook(
            "Hand off this distinct side task while keeping the active goal in this session."
        )
        self.assertEqual(0, result.returncode, result.stderr)
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        canonical = (ROOT / ".agents/engineering/workflow/handoff/SKILL.md").read_text(
            encoding="utf-8"
        ).strip()
        self.assertIn("engineering:handoff automatically selected", context)
        self.assertNotIn("engineering:plan-execution automatically selected", context)
        self.assertEqual(canonical, context.split("\n\n", 1)[1])

    def test_side_workstream_handoff_with_an_explicit_active_task_routes_without_a_goal(self):
        result = self.run_hook(
            "Delegate the separate workstream and retain the original task in this session."
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("engineering:handoff automatically selected", result.stdout)

    def test_side_thing_handoff_routes_with_the_requested_wording(self):
        result = self.run_hook(
            "This is a side thing; do a handoff and retain the current task in this session."
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("engineering:handoff automatically selected", result.stdout)
    def test_planning_only_prompt_stays_silent_even_with_an_active_goal(self):
        self.write_goal()
        result = self.run_hook("Planning only: revise the plan, but do not implement it.")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def test_planning_only_side_workstream_prompt_stays_silent(self):
        self.write_goal()
        result = self.run_hook(
            "Planning only: hand off this side task, but do not implement it."
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def test_quick_task_without_a_goal_stays_silent(self):
        result = self.run_hook("Fix the spelling mistake in README.md.")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def test_explicit_multi_phase_execution_routes_without_a_goal(self):
        result = self.run_hook("Implement this multi-phase migration through completion.")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("engineering:plan-execution", result.stdout)

    def test_completed_goal_does_not_capture_an_unrelated_continuation(self):
        self.write_goal("complete")
        result = self.run_hook("Continue with this quick follow-up.")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def test_non_prompt_event_is_ignored(self):
        self.write_goal()
        result = self.run_hook("Complete the active goal.", event="SessionStart")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def test_selected_route_fails_loudly_when_its_contract_is_missing(self):
        missing = self.cwd / "hooks/workflow_route.py"
        missing.parent.mkdir()
        missing.write_bytes(SCRIPT.read_bytes())
        self.write_goal()
        result = subprocess.run(
            [sys.executable, "-B", str(missing)],
            input=json.dumps({
                "hook_event_name": "UserPromptSubmit",
                "cwd": str(self.cwd),
                "prompt": "Complete the active goal.",
            }),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=20,
        )
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("cannot read plan-execution contract", result.stderr)


if __name__ == "__main__":
    unittest.main()
