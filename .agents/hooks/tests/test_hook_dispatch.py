import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
import uuid


HOOKS = Path(__file__).resolve().parents[1]
DISPATCH = HOOKS / "hook_dispatch.py"

GATES = {
    "deny.py": """
        import sys
        print("deny reason", file=sys.stderr)
        sys.exit(2)
    """,
    "ask.py": """
        import json, sys
        json.load(sys.stdin)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
            "permissionDecision": "ask", "permissionDecisionReason": "ask reason"}}))
    """,
    "allow.py": """
        import json, sys
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
            "permissionDecision": "allow", "permissionDecisionReason": "allow reason"}}))
    """,
    "defer.py": """
        import json
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
            "permissionDecision": "defer", "permissionDecisionReason": "defer reason"}}))
    """,
    "context.py": """
        import json, sys
        data = json.load(sys.stdin)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": data["hook_event_name"],
            "additionalContext": "context from " + data["tool_name"]}}))
    """,
    "echo.py": """
        import json, sys
        data = json.loads(sys.stdin.buffer.read())
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
            "additionalContext": "echo " + data["marker"]}}))
    """,
    "rebind.py": """
        import io, sys
        sys.stdin = io.TextIOWrapper(io.BytesIO(b"{}"), encoding="utf-8")
    """,
    "crash.py": """
        raise RuntimeError("gate exploded")
    """,
    "interrupt.py": """
        raise KeyboardInterrupt("gate interrupted")
    """,
    "block.py": """
        import json
        print(json.dumps({"decision": "block", "reason": "keep working"}))
    """,
    "imports.py": """
        import json
        from sibling import VALUE
        print(json.dumps({"systemMessage": VALUE}))
    """,
    "sibling.py": """
        VALUE = "sibling import resolved"
    """,
    "hang.py": """
        import time
        time.sleep(60)
    """,
    "arguments.py": """
        import json, sys
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
            "additionalContext": json.dumps(sys.argv[1:])}}))
    """,
    "silent_failure.py": """
        raise SystemExit(1)
    """,
    "plain.py": """
        print("PowerShell launcher installed")
    """,
}


class HookDispatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="hook dispatch ")
        self.addCleanup(self.temp.cleanup)
        self.hooks = Path(self.temp.name) / "hooks"
        self.hooks.mkdir()
        shutil.copy2(DISPATCH, self.hooks / DISPATCH.name)
        for name, body in GATES.items():
            (self.hooks / name).write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")

    def dispatch(self, gates, event="PreToolUse", tool="Bash", **extra):
        payload = {"hook_event_name": event, "tool_name": tool, "marker": "m1", **extra}
        result = subprocess.run(
            [sys.executable, "-B", str(self.hooks / DISPATCH.name), *gates],
            input=json.dumps(payload), capture_output=True, text=True, encoding="utf-8",
            timeout=60,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        output = json.loads(result.stdout) if result.stdout.strip() else {}
        return output, result.stderr

    def test_most_restrictive_decision_wins_and_every_context_is_kept(self):
        output, _ = self.dispatch(["allow.py", "ask.py", "context.py", "deny.py", "echo.py"])
        specific = output["hookSpecificOutput"]
        self.assertEqual("deny", specific["permissionDecision"])
        self.assertEqual("deny reason", specific["permissionDecisionReason"])
        self.assertEqual("context from Bash\n\necho m1", specific["additionalContext"])

        output, _ = self.dispatch(["allow.py", "ask.py"])
        self.assertEqual("ask", output["hookSpecificOutput"]["permissionDecision"])
        self.assertEqual("ask reason", output["hookSpecificOutput"]["permissionDecisionReason"])

    def test_tool_matcher_selects_gates_like_the_host(self):
        output, _ = self.dispatch(["deny.py@Bash|PowerShell", "context.py"], tool="Read")
        self.assertNotIn("permissionDecision", output["hookSpecificOutput"])
        self.assertEqual("context from Read", output["hookSpecificOutput"]["additionalContext"])
        output, _ = self.dispatch([str(self.hooks / "deny.py") + "@Bash|PowerShell"], tool="PowerShell")
        self.assertEqual("deny", output["hookSpecificOutput"]["permissionDecision"])
        output, _ = self.dispatch(["deny.py@Bash"], tool="BashOutput")
        self.assertEqual({}, output)

    def test_each_gate_reads_the_full_payload_even_after_a_sibling_rebinds_stdin(self):
        output, _ = self.dispatch(["rebind.py", "echo.py", "crash.py", "echo.py"])
        self.assertEqual("echo m1\n\necho m1", output["hookSpecificOutput"]["additionalContext"])

    def test_a_crashing_gate_is_reported_and_its_siblings_still_run(self):
        output, stderr = self.dispatch(["crash.py", "context.py"])
        self.assertIn("crash.py", stderr)
        self.assertIn("gate exploded", stderr)
        self.assertEqual("context from Bash", output["hookSpecificOutput"]["additionalContext"])

    def test_a_gate_raising_a_base_exception_is_a_crash_not_an_overrun(self):
        for deadline in ([], ["--deadline", "20"]):
            output, stderr = self.dispatch([*deadline, "interrupt.py", "context.py"])
            self.assertIn("gate interrupted", stderr)
            self.assertEqual("context from Bash", output["hookSpecificOutput"]["additionalContext"])
            self.assertNotIn("systemMessage", output)

    def test_stop_blocks_combine_exit_code_and_json_reasons(self):
        output, _ = self.dispatch(["block.py", "deny.py", "imports.py"], event="Stop", tool="")
        self.assertEqual("block", output["decision"])
        self.assertEqual("keep working\n\ndeny reason", output["reason"])
        self.assertEqual("sibling import resolved", output["systemMessage"])
        self.assertNotIn("hookSpecificOutput", output)

    def test_a_gate_past_the_deadline_keeps_finished_verdicts_and_reports_the_rest(self):
        started = time.monotonic()
        output, _ = self.dispatch(["--deadline", "2", "deny.py", "context.py", "hang.py", "ask.py"])
        self.assertLess(time.monotonic() - started, 30)
        specific = output["hookSpecificOutput"]
        self.assertEqual("deny", specific["permissionDecision"])
        self.assertEqual("deny reason", specific["permissionDecisionReason"])
        self.assertIn("context from Bash", specific["additionalContext"])
        self.assertIn("hang.py did not finish within 2s", specific["additionalContext"])
        self.assertIn("these gates did not run: ask.py", output["systemMessage"])

    def test_silent_gates_produce_no_output(self):
        output, stderr = self.dispatch(["rebind.py"])
        self.assertEqual({}, output)
        self.assertEqual("", stderr)

    def test_hook_groups_preserve_arguments_and_restore_them_for_siblings(self):
        output, stderr = self.dispatch([
            "--hook", "arguments.py", "--session-context", "--project", "path with spaces",
            "--hook", "arguments.py",
        ], event="SessionStart")
        self.assertEqual('', stderr)
        self.assertEqual('["--session-context", "--project", "path with spaces"]\n\n[]',
                         output['hookSpecificOutput']['additionalContext'])

    def test_session_start_failure_missing_script_and_block_keep_sibling_context(self):
        for failed, evidence in [('crash.py', 'gate exploded'),
                                 ('missing.py', 'FileNotFoundError'),
                                 ('silent_failure.py', 'exit status 1')]:
            with self.subTest(failed=failed):
                output, stderr = self.dispatch([
                    '--hook', 'context.py', '--hook', failed, '--hook', 'deny.py',
                    '--hook', 'echo.py',
                ], event='SessionStart')
                context = output['hookSpecificOutput']['additionalContext']
                self.assertIn('context from Bash', context)
                self.assertIn('echo m1', context)
                self.assertIn(evidence, context)
                self.assertIn(evidence, output['systemMessage'])
                self.assertIn(failed, stderr)
                self.assertEqual('block', output['decision'])
                self.assertEqual('deny reason', output['reason'])

    def test_session_start_deadline_reports_stalled_and_skipped_scripts_in_context(self):
        output, _ = self.dispatch([
            '--deadline', '1', '--hook', 'context.py', '--hook', 'hang.py',
            '--hook', 'arguments.py', '--session-context',
        ], event='SessionStart')
        context = output['hookSpecificOutput']['additionalContext']
        self.assertIn('context from Bash', context)
        self.assertIn('hang.py did not finish within 1s', context)
        self.assertIn('these gates did not run: arguments.py', context)

    def test_empty_hook_group_is_rejected(self):
        result = subprocess.run(
            [sys.executable, '-B', str(self.hooks / DISPATCH.name), '--hook'],
            input='{}', capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(1, result.returncode)
        self.assertIn('each --hook requires a script', result.stderr)

    def test_session_start_plain_stdout_is_delivered_with_json_context(self):
        output, stderr = self.dispatch(['--hook', 'plain.py', '--hook', 'echo.py'],
                                       event='SessionStart')
        self.assertEqual('', stderr)
        self.assertEqual('PowerShell launcher installed\n\necho m1',
                         output['hookSpecificOutput']['additionalContext'])

    def test_opted_in_timeout_denies_allow_ask_defer_and_missing_decisions(self):
        for first in ("allow.py", "ask.py", "defer.py", "context.py"):
            with self.subTest(first=first):
                output, _ = self.dispatch(["--deadline", "2", "--deny-on-timeout", first, "hang.py"])
                specific = output["hookSpecificOutput"]
                self.assertEqual("deny", specific["permissionDecision"])
                self.assertIn("hang.py", specific["permissionDecisionReason"])
                self.assertIn("hang.py did not finish within 2s", specific["additionalContext"])
                self.assertIn("hang.py did not finish within 2s", output["systemMessage"])

    def test_opted_in_timeout_before_deny_names_stalled_and_skipped_gates(self):
        output, _ = self.dispatch(["--deadline", "2", "--deny-on-timeout", "hang.py", "deny.py"])
        specific = output["hookSpecificOutput"]
        self.assertEqual("deny", specific["permissionDecision"])
        self.assertIn("hang.py did not finish", specific["permissionDecisionReason"])
        self.assertIn("these gates did not run: deny.py", specific["permissionDecisionReason"])

    def test_opted_in_timeout_preserves_completed_deny_reason_and_context(self):
        output, _ = self.dispatch(["--deadline", "2", "--deny-on-timeout", "deny.py", "context.py", "hang.py"])
        specific = output["hookSpecificOutput"]
        self.assertEqual("deny", specific["permissionDecision"])
        self.assertEqual("deny reason", specific["permissionDecisionReason"])
        self.assertIn("context from Bash", specific["additionalContext"])
        self.assertIn("hang.py did not finish within 2s", output["systemMessage"])

    def test_timeout_keeps_default_and_other_events_unchanged(self):
        output, _ = self.dispatch(["--deadline", "2", "allow.py", "hang.py"])
        self.assertEqual("allow", output["hookSpecificOutput"]["permissionDecision"])
        output, _ = self.dispatch(["--deadline", "2", "--deny-on-timeout", "context.py", "hang.py"], event="PostToolUse")
        specific = output["hookSpecificOutput"]
        self.assertNotIn("permissionDecision", specific)
        self.assertIn("context from Bash", specific["additionalContext"])
        self.assertIn("hang.py did not finish within 2s", output["systemMessage"])
        output, _ = self.dispatch(["--deadline", "2", "--deny-on-timeout", "allow.py"])
        self.assertEqual("allow", output["hookSpecificOutput"]["permissionDecision"])


class PackagedDispatchTests(unittest.TestCase):
    ROOT = HOOKS.parents[1]

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="packaged dispatch ")
        self.addCleanup(self.temp.cleanup)
        self.cwd = Path(self.temp.name)
        self.manifest = json.loads(
            (self.ROOT / "plugins/engineering/hooks/claude.json").read_text(encoding="utf-8")
        )
        self.plugin = self.ROOT / "plugins/engineering"
        self.environment = dict(
            os.environ, CLAUDE_PLUGIN_ROOT=str(self.plugin), TEMP=self.temp.name,
            TMP=self.temp.name, TMPDIR=self.temp.name,
        )

    def run_registration(self, event, payload):
        hook = self.manifest["hooks"][event][0]["hooks"][0]
        arguments = [
            argument.replace("${CLAUDE_PLUGIN_ROOT}", str(self.plugin)) for argument in hook["args"]
        ]
        data = {"hook_event_name": event, "cwd": str(self.cwd),
                "session_id": str(uuid.uuid4()), "tool_use_id": str(uuid.uuid4()), **payload}
        return subprocess.run(
            [hook["command"], *arguments], input=json.dumps(data), capture_output=True,
            text=True, encoding="utf-8", cwd=self.cwd, env=self.environment, timeout=60,
        )

    def test_credential_widening_is_denied_and_status_passes(self):
        result = self.run_registration("PreToolUse", {
            "tool_name": "Bash", "tool_input": {"command": "gh auth refresh -s admin:org"},
        })
        self.assertEqual(0, result.returncode, result.stderr)
        specific = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual("deny", specific["permissionDecision"])
        self.assertIn("GIT-AUTH GATE", specific["permissionDecisionReason"])

        result = self.run_registration("PreToolUse", {
            "tool_name": "Bash", "tool_input": {"command": "gh auth status"},
        })
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout + result.stderr)

    def test_non_shell_tools_run_only_the_all_tool_gates(self):
        result = self.run_registration("PreToolUse", {
            "tool_name": "Read", "tool_input": {"file_path": str(self.cwd / "x")},
        })
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout + result.stderr)

    def test_only_engineering_pretooluse_enables_timeout_denial(self):
        enabled = [event for event, groups in self.manifest["hooks"].items()
                   for group in groups for hook in group["hooks"]
                   if "--deny-on-timeout" in hook.get("args", [])]
        self.assertEqual(["PreToolUse"], enabled)


if __name__ == "__main__":
    unittest.main()
