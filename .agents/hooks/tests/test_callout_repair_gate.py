import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".agents/hooks/callout_repair_gate.py"
PROMPT = "You ignored the standard and drafted SendFeedback instead. That was wrong."


class CalloutRepairGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="callout gate ")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.session = str(uuid.uuid4())
        self.transcript = self.base / "transcript.jsonl"
        self.source = self.base / "source-owner"
        self.source.mkdir()
        self.goal = self.source / "GOAL.md"
        self.goal.write_text("# Repair\n\n## Authorization\n\nBounded standards-defect repair.\n", encoding="utf-8")
        self.prompt = self.base / "handoff.md"
        self.prompt.write_text(f"cd {self.source}\nRead {self.goal} and execute its Next Steps.\n", encoding="utf-8")
        self.command = (f"& 'plugin/launch-codex.ps1' -WorkingDirectory '{self.source}' "
                        f"-PromptPath '{self.prompt}' -Lane L4")

    def run_hook(self, event, **fields):
        data = {"hook_event_name": event, "session_id": self.session, "cwd": str(self.base), **fields}
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT)], input=json.dumps(data), capture_output=True,
            text=True, encoding="utf-8", timeout=15,
            env=dict(os.environ, TMP=self.temp.name, TEMP=self.temp.name, TMPDIR=self.temp.name),
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else {}

    def submit(self, prompt=PROMPT, **fields):
        return self.run_hook("UserPromptSubmit", prompt=prompt, **fields)

    def pretool(self, name="SendFeedback", tool_input=None):
        return self.run_hook("PreToolUse", tool_name=name, tool_input=tool_input or {},
                             transcript_path=str(self.transcript))

    def write_transcript(self, records):
        self.transcript.write_text("\n".join(json.dumps(item) for item in records), encoding="utf-8")

    def claude_launch(self, successful=True, tool="Bash", command=None):
        return [
            {"type": "user", "message": {"role": "user", "content": PROMPT}},
            {"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "text", "text": "The standard caused this mistake. Here is the answer."},
                {"type": "tool_use", "name": tool, "id": "launch", "input": {"command": command or self.command}},
            ]}},
            {"type": "user", "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": "launch", "is_error": not successful,
                 "content": "Launched codex-cli 0.154.0 from codex.exe on selected lane"},
            ]}},
        ]

    def test_callout_blocks_automatic_feedback_and_claude_stop(self):
        context = self.submit()["hookSpecificOutput"]["additionalContext"]
        self.assertIn("answer the user's direct question first", context)
        denied = self.pretool()["hookSpecificOutput"]
        self.assertEqual("deny", denied["permissionDecision"])
        self.assertIn("source owner", denied["permissionDecisionReason"])
        stopped = self.run_hook("Stop", transcript_path=str(self.transcript))
        self.assertEqual("block", stopped["decision"])

    def test_automatic_feedback_is_gated_even_when_callout_wording_is_unrecognized(self):
        self.submit("For goodness sake, what was that?")
        self.assertEqual("deny", self.pretool()["hookSpecificOutput"]["permissionDecision"])
        self.assertEqual({}, self.run_hook("Stop"))

    def test_explicit_feedback_and_user_repair_limits_override_the_gate(self):
        for prompt in ("Please draft feedback about that mistake.",
                       "You were wrong. Do not hand off anything; answer only."):
            with self.subTest(prompt=prompt):
                self.submit(prompt)
                self.assertEqual({}, self.pretool())
                self.assertEqual({}, self.run_hook("Stop"))

    def test_regular_tools_and_neutral_questions_are_allowed(self):
        self.submit()
        self.assertEqual({}, self.pretool("Read", {"file_path": "README.md"}))
        self.submit("Why will the PR not merge?")
        self.assertEqual({}, self.run_hook("Stop"))
        self.submit("You made a mistake in that sum.")
        self.assertEqual({}, self.run_hook("Stop"))

    def test_launcher_requires_a_visible_answer_before_launch(self):
        self.submit()
        denied = self.pretool("Bash", {"command": self.command})["hookSpecificOutput"]
        self.assertEqual("deny", denied["permissionDecision"])
        self.write_transcript([
            {"type": "user", "message": {"role": "user", "content": PROMPT}},
            {"type": "assistant", "message": {"role": "assistant", "content": "Here is the answer."}},
        ])
        self.assertEqual({}, self.pretool("Bash", {"command": self.command}))

    def test_skill_loading_apology_and_failed_launch_do_not_discharge_repair(self):
        self.submit()
        for records in (
            [{"type": "assistant", "message": {"role": "assistant", "content": "Sorry; handoff is loaded."}}],
            self.claude_launch(successful=False),
            self.claude_launch(tool="Read"),
        ):
            with self.subTest(records=records):
                self.write_transcript(records)
                self.assertEqual("deny", self.pretool()["hookSpecificOutput"]["permissionDecision"])

    def test_successful_claude_source_owner_launch_releases_feedback_and_stop(self):
        self.submit()
        self.write_transcript(self.claude_launch())
        self.assertEqual({}, self.pretool())
        self.assertEqual({}, self.run_hook("Stop", transcript_path=str(self.transcript)))
        self.transcript.unlink()
        self.assertEqual({}, self.pretool())
        self.submit()
        self.assertEqual("deny", self.pretool()["hookSpecificOutput"]["permissionDecision"])

    def test_unrelated_launch_and_old_turn_launch_do_not_release_repair(self):
        self.submit()
        self.goal.write_text("# Review\n\n## Authorization\n\nReview product code.\n", encoding="utf-8")
        self.write_transcript(self.claude_launch())
        self.assertEqual("deny", self.pretool()["hookSpecificOutput"]["permissionDecision"])
        self.goal.write_text("# Repair\n\n## Authorization\n\nStandards-defect repair.\n", encoding="utf-8")
        self.write_transcript(self.claude_launch() + [
            {"type": "user", "message": {"role": "user", "content": PROMPT}},
        ])
        self.assertEqual("deny", self.pretool()["hookSpecificOutput"]["permissionDecision"])

    def test_codex_native_turn_and_paired_launch_output_release_feedback(self):
        self.submit(turn_id="turn")
        self.write_transcript([
            {"type": "response_item", "payload": {"type": "message", "role": "user",
                "content": [{"type": "input_text", "text": PROMPT}]}},
            {"type": "response_item", "payload": {"type": "custom_tool_call", "name": "exec",
                "call_id": "launch", "input": self.command}},
            {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "launch",
                "output": [{"type": "text", "text": "Script completed\nLaunched codex-cli 0.154.0 on L4"}]}},
        ])
        self.assertEqual({}, self.pretool("mcp__host__send_feedback"))

    def test_codex_failed_output_and_analysis_are_not_success_or_answer(self):
        self.submit(turn_id="turn")
        records = [
            {"type": "response_item", "payload": {"type": "message", "role": "user", "content": PROMPT}},
            {"type": "response_item", "payload": {"type": "message", "role": "assistant", "channel": "analysis",
                "content": [{"type": "output_text", "text": "The reasoning is private."}]}},
            {"type": "response_item", "payload": {"type": "custom_tool_call", "name": "exec",
                "call_id": "launch", "input": self.command}},
            {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "launch",
                "output": [{"type": "text", "text": "Script failed\nLaunched codex-cli 0.154.0"}]}},
        ]
        self.write_transcript(records)
        self.assertEqual("deny", self.pretool()["hookSpecificOutput"]["permissionDecision"])
        self.assertEqual("deny", self.pretool("exec", {"input": self.command})["hookSpecificOutput"]["permissionDecision"])

    def test_structured_launch_receipt_supports_variable_arguments(self):
        self.submit()
        records = self.claude_launch(command="& 'plugin/launch-codex.ps1' -WorkingDirectory $owner -PromptPath $prompt")
        result = records[-1]["message"]["content"][0]
        result["content"] += "\n" + json.dumps({"event": "agent-handoff-submitted",
            "worktree": str(self.source), "prompt_path": str(self.prompt)})
        self.write_transcript(records)
        self.assertEqual({}, self.pretool())
        result["content"] = json.dumps({"output": result["content"], "exit_code": 0})
        self.write_transcript(records)
        self.assertEqual({}, self.pretool())

    def test_host_generated_prompts_do_not_create_or_clear_human_state(self):
        self.submit()
        for fields in ({"isMeta": True}, {"agent_id": "worker"}, {"origin": {"kind": "automation"}}):
            self.assertEqual({}, self.submit("You were wrong.", **fields))
        self.assertEqual({}, self.submit("<task-notification>You were wrong.</task-notification>"))
        self.assertEqual("block", self.run_hook("Stop")["decision"])
        self.assertEqual({}, self.run_hook("Stop", stop_hook_active=True))

    def test_manifests_ship_only_supported_callout_events(self):
        for host in ("claude", "codex"):
            manifest = json.loads((ROOT / f".agents/plugins/manifests/{host}/engineering-hooks.json").read_text())
            for event in ("UserPromptSubmit", "PreToolUse"):
                self.assertIn("callout_repair_gate.py", json.dumps(manifest["hooks"][event]))
            if host == "claude":
                self.assertIn("callout_repair_gate.py", json.dumps(manifest["hooks"]["Stop"]))
            else:
                self.assertNotIn("callout_repair_gate.py", json.dumps(manifest["hooks"].get("Stop", [])))


if __name__ == "__main__":
    unittest.main()
