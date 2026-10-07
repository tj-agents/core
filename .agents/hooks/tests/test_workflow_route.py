from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".agents/hooks/workflow_route.py"
PLANNING_INTENT_CASES = (
    ("Implement phase 2 of the plan only, not phase 3", "plan-execution", "plan-execution"),
    ("Don't only plan it, implement it", None, "plan-execution"),
    ("Don’t only plan it, implement it", None, "plan-execution"),
    ("Don't only plan it; implement phase 2 of the plan", "plan-execution", "plan-execution"),
    ("Draft the plan without implementing it", "plan-authoring", "plan-authoring"),
    ("Draft the plan only", "plan-authoring", "plan-authoring"),
    ("Please revise the current plan only", "plan-authoring", "plan-authoring"),
    ("Continue with the plan only", "plan-execution", "plan-execution"),
    ("Do not implement any changes yet", None, None),
    ("Review the plan branch without implementing it", None, None),
    ("Only plan the migration", "plan-authoring", "plan-authoring"),
    ("Planning only: revise the plan", "plan-authoring", "plan-authoring"),
    ("Resume planning the migration", "plan-authoring", "plan-authoring"),
    ("Continue planning the migration", "plan-authoring", "plan-authoring"),
    ("Implement the plan-authoring fix", "plan-execution", "plan-execution"),
    ("Do not draft a plan; implement it", None, "plan-execution"),
    ("I want to continue planning the migration", "plan-authoring", "plan-authoring"),
    ("I want you to only plan the migration", "plan-authoring", "plan-authoring"),
    ("Please continue with planning only", "plan-authoring", "plan-authoring"),
    ("Please resume with planning only", "plan-authoring", "plan-authoring"),
    ("I want to draft the plan only", "plan-authoring", "plan-authoring"),
    ("I don't want to continue planning the migration", None, None),
    ("I don’t want you to continue with planning only", None, None),
    ("I want you not to continue planning the migration", None, None),
    ("I want you to not continue planning the migration", None, None),
    ("Don't continue with planning only", None, None),
    ("We discussed whether I want to only plan the migration", None, None),
    ("I do not want you to only plan it; implement phase 2 of the plan",
     "plan-execution", "plan-execution"),
    ("I want to continue with the plan only", "plan-execution", "plan-execution"),
    ("I want to implement the plan-authoring fix", "plan-execution", "plan-execution"),
    ("I never want to only plan it; implement it", None, "plan-execution"),
)


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
            input=json.dumps({"hook_event_name": event, "cwd": str(self.cwd), "prompt": prompt,
                              "session_id": str(uuid.uuid4())}),
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

    def test_planning_intent_routes_with_and_without_an_active_goal(self):
        for active in (False, True):
            if active:
                self.write_goal()
            for prompt, without_goal, with_goal in PLANNING_INTENT_CASES:
                expected = with_goal if active else without_goal
                with self.subTest(prompt=prompt, active_goal=active):
                    result = self.run_hook(prompt)
                    self.assertEqual(0, result.returncode, result.stderr)
                    if expected is None:
                        self.assertEqual("", result.stdout)
                    else:
                        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
                        self.assertTrue(context.startswith(f"engineering:{expected} automatically selected"))

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

    def test_direct_handoff_request_routes_without_side_workstream_words(self):
        for prompt in (
            "Hand this off to another Codex session.",
            "Can you hand off the model-control investigation? Keep the current goal here.",
            "Please do a handoff of this investigation.",
        ):
            with self.subTest(prompt=prompt):
                result = self.run_hook(prompt)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertIn("engineering:handoff automatically selected", result.stdout)

    def test_handoff_questions_and_negation_do_not_launch(self):
        for prompt in (
            "Why did you not hand it off?",
            "Do not hand off this task.",
        ):
            with self.subTest(prompt=prompt):
                result = self.run_hook(prompt)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("", result.stdout)

    def test_planning_only_prompt_loads_authoring_even_with_an_active_goal(self):
        self.write_goal()
        result = self.run_hook("Planning only: revise the plan, but do not implement it.")
        self.assertEqual(0, result.returncode, result.stderr)
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        canonical = (ROOT / ".agents/engineering/workflow/plan-authoring/SKILL.md").read_text(
            encoding="utf-8"
        ).strip()
        self.assertIn("engineering:plan-authoring automatically selected", context)
        self.assertEqual(canonical, context.split("\n\n", 1)[1])

    def test_planning_only_side_workstream_does_not_select_a_launcher(self):
        self.write_goal()
        result = self.run_hook(
            "Planning only: hand off this side task, but do not implement it."
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("engineering:plan-authoring automatically selected", result.stdout)
        self.assertNotIn("engineering:handoff automatically selected", result.stdout)

    def test_resuming_planning_without_a_goal_loads_authoring(self):
        result = self.run_hook("Resume planning the taxonomy; implementation waits for approval.")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("engineering:plan-authoring automatically selected", result.stdout)

    def test_a_prohibition_alone_does_not_authorize_planning_or_execution(self):
        self.write_goal()
        result = self.run_hook("Do not implement the plan.")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def test_implementing_a_plan_authoring_fix_still_selects_execution(self):
        result = self.run_hook("Implement the plan-authoring fix across all phases.")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("engineering:plan-execution automatically selected", result.stdout)
        self.assertNotIn("engineering:plan-authoring automatically selected", result.stdout)

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


class WorkflowRouteRecoveryTests(unittest.TestCase):
    PROMPT = "Continue and complete the active goal."

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="workflow route recovery ")
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.cwd = root / "repo"
        self.cwd.mkdir()
        (self.cwd / "GOAL.md").write_text("# Goal\n\nStatus: in progress\n", encoding="utf-8")
        self.scratch = root / "temp"
        self.scratch.mkdir()
        self.transcript = root / "session.jsonl"
        self.session = "session-1"
        self.environment = dict(
            os.environ, TEMP=str(self.scratch), TMP=str(self.scratch), TMPDIR=str(self.scratch)
        )

    def write_transcript(self, prompt, *, kind="human", filler=0):
        stamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        latest = {"type": "user", "timestamp": stamp,
                  "message": {"role": "user", "content": [{"type": "text", "text": prompt}]}}
        if kind:
            latest["origin"] = {"kind": kind}
        entries = [
            {"type": "user", "origin": {"kind": "human"}, "timestamp": "2026-01-01T00:00:00.000Z",
             "message": {"role": "user", "content": "Fix the typo."}},
            latest,
            *({"type": "assistant", "message": {"content": [{"type": "text", "text": "x" * 1000}]}}
              for _ in range(filler)),
            {"type": "user", "isMeta": True, "origin": {"kind": "human"}, "timestamp": stamp,
             "message": {"role": "user", "content": "Continue and complete the active goal."}},
        ]
        self.transcript.write_text(
            "".join(json.dumps(entry) + "\n" for entry in entries), encoding="utf-8"
        )

    def run_hook(self, event, **payload):
        data = {"hook_event_name": event, "cwd": str(self.cwd), "session_id": self.session,
                "transcript_path": str(self.transcript), **payload}
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT)], input=json.dumps(data), capture_output=True,
            text=True, encoding="utf-8", env=self.environment, timeout=20,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)["hookSpecificOutput"] if result.stdout.strip() else None

    def test_a_lost_prompt_route_is_delivered_once_on_the_next_tool_call(self):
        self.write_transcript(self.PROMPT)
        recovered = self.run_hook("PreToolUse", tool_name="Read")
        self.assertEqual("PreToolUse", recovered["hookEventName"])
        context = recovered["additionalContext"]
        self.assertTrue(context.startswith("workflow-route: the UserPromptSubmit hook did not deliver"))
        self.assertIn("engineering:plan-execution automatically selected", context)
        self.assertIsNone(self.run_hook("PreToolUse", tool_name="Bash"))

    def test_planning_intent_recovery_matches_prompt_routing_and_delivers_once(self):
        for active in (False, True):
            goal = self.cwd / "GOAL.md"
            if active:
                goal.write_text("# Goal\n\nStatus: in progress\n", encoding="utf-8")
            else:
                goal.unlink()
            for prompt, without_goal, with_goal in PLANNING_INTENT_CASES:
                self.session = str(uuid.uuid4())
                expected = with_goal if active else without_goal
                with self.subTest(prompt=prompt, active_goal=active):
                    self.write_transcript(prompt)
                    recovered = self.run_hook("PreToolUse", tool_name="Read")
                    if expected is None:
                        self.assertIsNone(recovered)
                    else:
                        self.assertEqual("PreToolUse", recovered["hookEventName"])
                        self.assertIn(f"engineering:{expected} automatically selected",
                                      recovered["additionalContext"])
                    self.assertIsNone(self.run_hook("PreToolUse", tool_name="Bash"))

    def test_a_prompt_without_an_origin_marker_is_still_recovered(self):
        self.write_transcript(self.PROMPT, kind=None)
        recovered = self.run_hook("PreToolUse", tool_name="Read")
        self.assertIn("engineering:plan-execution automatically selected", recovered["additionalContext"])

    def test_host_generated_entries_are_not_treated_as_prompts(self):
        for text in (
            "<command-name>/continue</command-name>",
            "<task-notification>complete</task-notification>",
        ):
            with self.subTest(text=text):
                self.write_transcript(text, kind=None)
                self.assertIsNone(self.run_hook("PreToolUse", tool_name="Read"))

    def test_a_delivered_prompt_route_is_not_repeated(self):
        self.write_transcript(self.PROMPT)
        delivered = self.run_hook("UserPromptSubmit", prompt=self.PROMPT)
        self.assertIn("engineering:plan-execution automatically selected", delivered["additionalContext"])
        self.assertIsNone(self.run_hook("PreToolUse", tool_name="Read"))

    def test_the_prompt_id_receipt_decides_delivery_before_timestamps(self):
        self.write_transcript(self.PROMPT)
        receipts = self.scratch / "agents-workflow-route"
        receipts.mkdir()
        digest = hashlib.sha256(self.session.encode("utf-8")).hexdigest()
        (receipts / f"{digest}.json").write_text(
            json.dumps({"routed_at": 0, "prompt_id": "prompt-1"}), encoding="utf-8"
        )
        self.assertIsNone(self.run_hook("PreToolUse", tool_name="Read", prompt_id="prompt-1"))
        recovered = self.run_hook("PreToolUse", tool_name="Read", prompt_id="prompt-2")
        self.assertIn("did not deliver this prompt's route", recovered["additionalContext"])
        self.assertIsNone(self.run_hook("PreToolUse", tool_name="Read", prompt_id="prompt-2"))

    def test_parallel_tool_calls_recover_the_route_only_once(self):
        self.write_transcript(self.PROMPT)
        data = json.dumps({"hook_event_name": "PreToolUse", "cwd": str(self.cwd),
                           "session_id": self.session, "transcript_path": str(self.transcript),
                           "tool_name": "Read"})
        processes = [
            subprocess.Popen([sys.executable, "-B", str(SCRIPT)], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                             encoding="utf-8", env=self.environment)
            for _ in range(4)
        ]
        outputs = [process.communicate(data, timeout=30)[0] for process in processes]
        self.assertEqual(1, sum("did not deliver this prompt's route" in output for output in outputs))

    def test_an_unrouted_prompt_stays_silent_after_a_lost_hook(self):
        self.write_transcript("Fix the spelling mistake in README.md.")
        self.assertIsNone(self.run_hook("PreToolUse", tool_name="Read"))

    def test_subagents_and_non_human_turns_never_recover_the_parent_prompt(self):
        self.write_transcript(self.PROMPT)
        self.assertIsNone(self.run_hook("PreToolUse", tool_name="Read", agent_id="agent-1"))
        self.write_transcript(self.PROMPT, kind="task-notification")
        self.assertIsNone(self.run_hook("PreToolUse", tool_name="Read"))

    def test_recovery_reads_only_a_bounded_transcript_tail(self):
        self.write_transcript(self.PROMPT, filler=2000)
        self.assertIsNone(self.run_hook("PreToolUse", tool_name="Read"))


if __name__ == "__main__":
    unittest.main()
