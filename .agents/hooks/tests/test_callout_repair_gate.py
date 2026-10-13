import json
import hashlib
import os
from pathlib import Path
import re
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
        self.goal.write_text("# Repair\n", encoding="utf-8")
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
        result = self.run_hook("UserPromptSubmit", prompt=prompt, **fields)
        if result:
            state = self.callout_state()
            self.goal.write_text(
                "# Repair\n\nRepair workflow: engineering:self-repair\n"
                "Source owner: engineering/handoff\n"
                f"Callout session: {self.session}\n"
                f"Callout id: {state['callout_id']}\n"
                f"Prompt SHA256: {hashlib.sha256(prompt.encode()).hexdigest()}\n\n"
                "## Authorization\n\nBounded standards-defect repair.\n",
                encoding="utf-8",
            )
        return result

    def pretool(self, name="SendFeedback", tool_input=None):
        return self.run_hook("PreToolUse", tool_name=name, tool_input=tool_input or {},
                             transcript_path=str(self.transcript))

    def write_transcript(self, records):
        self.transcript.write_text("\n".join(json.dumps(item) for item in records), encoding="utf-8")

    def callout_state(self):
        return json.loads(
            (self.base / f"callout-repair-{hashlib.sha256(self.session.encode()).hexdigest()[:20]}.json").read_text(
                encoding="utf-8"
            )
        )

    def claude_launch(self, successful=True, tool="Bash", command=None, receipt=True, prompt=PROMPT):
        output = "Launched codex-cli 0.154.0 from codex.exe on selected lane"
        if receipt:
            output += "\n" + json.dumps({
                "event": "agent-handoff-submitted",
                "worktree": str(self.source),
                "prompt_path": str(self.prompt),
            })
        return [
            {"type": "user", "message": {"role": "user", "content": prompt}},
            {"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "text", "text": "The standard caused this mistake. Here is the answer."},
                {"type": "tool_use", "name": tool, "id": "launch", "input": {"command": command or self.command}},
            ]}},
            {"type": "user", "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": "launch", "is_error": not successful,
                 "content": [{"type": "text", "text": output}]},
            ]}},
        ]

    def deferred_check(self, prompt=PROMPT, callout_id=None, record_id="B014"):
        state = self.callout_state()
        callout_id = callout_id or state["callout_id"]
        record = self.base / f"{record_id}.md"
        goal = self.source / f"{record_id}-GOAL.md"
        evidence = self.base / "missing-read.txt"
        target = self.base / "unavailable"
        evidence.write_text("required read failed", encoding="utf-8")
        goal.write_text(
            ("# Repair\\n\\n## Authorization\\n\\nBounded standards-defect repair.\\n\\n"
            "Source owner: engineering/handoff\\n"
            f"Required read capability: {target}\\n"
            f"Problem record: {record}#{record_id}\\n").replace("\\n", "\n"),
            encoding="utf-8",
        )
        value = {
            "schema_version": 1,
            "record_id": record_id,
            "kind": "bug",
            "state": "deferred",
            "callout": {
                "session_id": self.session,
                "callout_id": callout_id,
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            },
            "source_owner": "engineering/handoff",
            "repair_goal": str(goal),
            "disposition": "deferred",
            "reason": "the dependency cannot be read",
            "blocked_by": "capability",
            "resolver": "environment owner",
            "resume_condition": "the dependency is readable",
            "next_action": "recheck the dependency",
            "evidence": {
                "kind": "read-failure",
                "path": str(evidence),
                "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
                "target": str(target),
                "operation": "read",
                "error": "missing",
            },
        }
        fence = chr(96) * 3
        record.write_text(
            (fence + "agent-handoff-disposition\\n" + json.dumps(value) + "\\n" + fence + "\\n").replace(
                "\\n", "\n"
            ),
            encoding="utf-8",
        )
        command = (
            f"python '{ROOT / '.agents/engineering/workflow/handoff/scripts/admission.py'}' check "
            f"--record '{record}' --id {record_id} --session '{self.session}' "
            f"--prompt-sha256 '{value['callout']['prompt_sha256']}' --callout-id '{callout_id}'"
        )
        output = subprocess.run(
            [sys.executable, "-B", str(ROOT / ".agents/engineering/workflow/handoff/scripts/admission.py"), "check",
             "--record", str(record), "--id", record_id, "--session", self.session,
             "--prompt-sha256", value["callout"]["prompt_sha256"], "--callout-id", callout_id],
            capture_output=True, text=True, encoding="utf-8", timeout=15,
            env=dict(os.environ, TMP=self.temp.name, TEMP=self.temp.name, TMPDIR=self.temp.name),
            check=True,
        ).stdout
        return command, output

    def test_callout_blocks_automatic_feedback_and_terminal_stop(self):
        context = self.submit()["hookSpecificOutput"]["additionalContext"]
        self.assertIn("answer the user's direct question first", context)
        denied = self.pretool()["hookSpecificOutput"]
        self.assertEqual("deny", denied["permissionDecision"])
        self.assertIn("typed disposition", denied["permissionDecisionReason"])
        stopped = self.run_hook("Stop", transcript_path=str(self.transcript))
        self.assertEqual("block", stopped["decision"])

    def test_automatic_feedback_is_gated_even_when_callout_wording_is_unrecognized(self):
        self.submit("For goodness sake, what was that?")
        self.assertEqual("deny", self.pretool()["hookSpecificOutput"]["permissionDecision"])
        self.assertEqual({}, self.run_hook("Stop"))

    def test_explicit_feedback_allows_that_tool_without_discharging_a_covered_callout(self):
        self.submit("You ignored the standard. That was wrong. Please draft feedback.")
        self.assertEqual({}, self.pretool())
        self.assertEqual("deny", self.pretool("Bash", {"command": "git status"})["hookSpecificOutput"]["permissionDecision"])
        self.assertEqual("block", self.run_hook("Stop")["decision"])
        self.session = str(uuid.uuid4())
        limited = "You were wrong. Do not hand off anything; answer only."
        self.submit(limited)
        self.write_transcript([{"type": "user", "message": {"role": "user", "content": limited}}])
        self.assertEqual({}, self.pretool())
        self.assertEqual({}, self.run_hook("Stop", transcript_path=str(self.transcript)))

    def test_pending_callout_blocks_normal_tools_but_allows_repair_research_and_recording(self):
        self.submit()
        self.assertEqual({}, self.pretool("Read", {"file_path": "README.md"}))
        self.assertEqual({}, self.pretool("apply_patch", {"patch": "*** Update File: BUGS.md"}))
        self.assertEqual({}, self.pretool("Bash", {"command": "python admission.py check --record BUGS.md"}))
        self.assertEqual({}, self.pretool("exec_command", {"cmd": "rg 'Source owner' GOAL.md"}))
        self.assertEqual({}, self.pretool("Write", {"file_path": "BUGS.md", "content": "B015"}))
        self.assertEqual("deny", self.pretool("Bash", {"command": "git status"})["hookSpecificOutput"]["permissionDecision"])
        self.assertEqual("deny", self.pretool("exec_command", {"cmd": "rg 'Source owner' GOAL.md; git status"})["hookSpecificOutput"]["permissionDecision"])
        self.assertEqual("deny", self.pretool("apply_patch", {"patch": "*** Update File: src/item.py"})["hookSpecificOutput"]["permissionDecision"])
        self.assertEqual("deny", self.pretool("Write", {"file_path": "src/item.py", "content": "x"})["hookSpecificOutput"]["permissionDecision"])
        self.assertEqual("deny", self.pretool("apply_patch", {"patch": "*** Update File: GOAL.md\n*** Delete File: src/item.py"})["hookSpecificOutput"]["permissionDecision"])

    def test_a_new_prompt_cannot_reset_an_unresolved_callout(self):
        self.submit()
        self.submit("Why will the PR not merge?")
        self.assertEqual("deny", self.pretool("Bash", {"command": "git status"})["hookSpecificOutput"]["permissionDecision"])
        self.assertEqual("block", self.run_hook("Stop")["decision"])

    def test_repeated_and_multiple_callouts_keep_their_saved_obligations(self):
        first = self.submit()["hookSpecificOutput"]["additionalContext"]
        repeated = self.submit()["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(re.search(r"callout_id=([^;]+)", first).group(1), re.search(r"callout_id=([^;]+)", repeated).group(1))
        second = "You violated the handoff workflow. That was wrong."
        self.submit(second)
        self.assertEqual(2, len(self.callout_state()["obligations"]))
        self.write_transcript(self.claude_launch(prompt=second))
        self.assertEqual("deny", self.pretool()["hookSpecificOutput"]["permissionDecision"])

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
            self.claude_launch(receipt=False),
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

    def test_mismatched_goal_nonce_does_not_release_repair(self):
        self.submit()
        goal = self.goal.read_text(encoding="utf-8")
        self.goal.write_text(re.sub(r"(?m)^Callout id: .+$", "Callout id: other-callout", goal), encoding="utf-8")
        self.write_transcript(self.claude_launch())
        self.assertEqual("deny", self.pretool()["hookSpecificOutput"]["permissionDecision"])

    def test_codex_native_turn_and_paired_launch_output_release_feedback(self):
        self.submit(turn_id="turn")
        self.write_transcript([
            {"type": "response_item", "payload": {"type": "message", "role": "user",
                "content": [{"type": "input_text", "text": PROMPT}]}},
            {"type": "response_item", "payload": {"type": "custom_tool_call", "name": "exec",
                "call_id": "launch", "input": self.command}},
            {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "launch",
                "output": [{"type": "text", "text": "Script completed\nLaunched codex-cli 0.154.0 on L4\n" + json.dumps({
                    "event": "agent-handoff-submitted", "worktree": str(self.source), "prompt_path": str(self.prompt)
                })}]}},
        ])
        self.assertEqual({}, self.pretool("mcp__host__send_feedback"))

    def test_current_typed_deferred_disposition_releases_only_the_current_claude_turn(self):
        self.submit()
        command, output = self.deferred_check()
        records = self.claude_launch(command=command)
        records[-1]["message"]["content"][0]["content"][0]["text"] = output
        self.write_transcript(records)
        self.assertEqual({}, self.pretool())
        self.submit()
        self.write_transcript([{"type": "user", "message": {"role": "user", "content": PROMPT}}])
        self.assertEqual("deny", self.pretool()["hookSpecificOutput"]["permissionDecision"])

    def test_all_pending_callouts_require_current_typed_dispositions(self):
        first_prompt = PROMPT
        second_prompt = "You violated the handoff workflow. That was wrong."
        self.submit(first_prompt)
        first_id = self.callout_state()["obligations"][0]["callout_id"]
        self.submit(second_prompt)
        second_id = self.callout_state()["obligations"][1]["callout_id"]
        first_command, first_output = self.deferred_check(first_prompt, first_id, "B014")
        second_command, second_output = self.deferred_check(second_prompt, second_id, "B015")
        self.write_transcript([
            {"type": "user", "message": {"role": "user", "content": second_prompt}},
            {"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "text", "text": "The workflow caused the mistake."},
                {"type": "tool_use", "name": "Bash", "id": "first", "input": {"command": first_command}},
                {"type": "tool_use", "name": "Bash", "id": "second", "input": {"command": second_command}},
            ]}},
            {"type": "user", "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": "first", "content": [{"type": "text", "text": first_output}]},
                {"type": "tool_result", "tool_use_id": "second", "content": [{"type": "text", "text": second_output}]},
            ]}},
        ])
        self.assertEqual({}, self.pretool())

    def test_typed_disposition_requires_the_current_codex_callout_nonce(self):
        self.submit(turn_id="turn")
        command, output = self.deferred_check()
        self.write_transcript([
            {"type": "response_item", "payload": {"type": "message", "role": "user",
                "content": [{"type": "input_text", "text": PROMPT}]}},
            {"type": "response_item", "payload": {"type": "custom_tool_call", "name": "exec",
                "call_id": "admission", "input": command}},
            {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "admission",
                "output": [{"type": "text", "text": output}]}},
        ])
        self.assertEqual({}, self.pretool("mcp__host__send_feedback"))
        self.submit(turn_id="new-turn")
        self.write_transcript([{"type": "response_item", "payload": {"type": "message", "role": "user",
            "content": [{"type": "input_text", "text": PROMPT}]}}])
        self.assertEqual("deny", self.pretool()["hookSpecificOutput"]["permissionDecision"])

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

    def test_structured_launch_receipt_supports_variable_arguments_and_rejects_echoes(self):
        self.submit()
        records = self.claude_launch(command="& 'plugin/launch-codex.ps1' -WorkingDirectory $owner -PromptPath $prompt")
        result = records[-1]["message"]["content"][0]
        self.write_transcript(records)
        self.assertEqual({}, self.pretool())
        result["content"] = [{"type": "text", "text": json.dumps(
            {"output": result["content"][0]["text"], "exit_code": 0}
        )}]
        self.write_transcript(records)
        self.assertEqual({}, self.pretool())
        self.submit()
        self.write_transcript(self.claude_launch(
            command=f"echo launch-codex.ps1 -WorkingDirectory '{self.source}' -PromptPath '{self.prompt}'"
        ))
        self.assertEqual("deny", self.pretool()["hookSpecificOutput"]["permissionDecision"])

    def test_host_generated_prompts_do_not_create_or_clear_human_state(self):
        self.submit()
        for fields in ({"isMeta": True}, {"agent_id": "worker"}, {"origin": {"kind": "automation"}}):
            self.assertEqual({}, self.submit("You were wrong.", **fields))
        self.assertEqual({}, self.submit("<task-notification>You were wrong.</task-notification>"))
        self.assertEqual("block", self.run_hook("Stop")["decision"])
        self.assertEqual("block", self.run_hook("Stop", stop_hook_active=True)["decision"])

    def test_manifests_ship_only_supported_callout_events(self):
        for host in ("claude", "codex"):
            manifest = json.loads((ROOT / f".agents/plugins/manifests/{host}/engineering-hooks.json").read_text())
            for event in ("UserPromptSubmit", "PreToolUse"):
                self.assertIn("callout_repair_gate.py", json.dumps(manifest["hooks"][event]))
            self.assertIn("callout_repair_gate.py", json.dumps(manifest["hooks"]["Stop"]))
        codex = json.loads((ROOT / ".agents/plugins/manifests/codex/engineering-hooks.json").read_text())
        registration = next(group for group in codex["hooks"]["PreToolUse"]
                            if "callout_repair_gate.py" in json.dumps(group))
        self.assertEqual(".*", registration["matcher"])


if __name__ == "__main__":
    unittest.main()
