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
        print(json.dumps({"hookSpecificOutput": {"hookEventName": data.get("hook_event_name") or data["hookEventName"],
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

    def dispatch(self, gates, event="PreToolUse", tool="Bash", event_field="hook_event_name", **extra):
        payload = {event_field: event, "tool_name": tool, "marker": "m1", **extra}
        result = subprocess.run(
            [sys.executable, "-B", str(self.hooks / DISPATCH.name), *gates],
            input=json.dumps(payload), capture_output=True, text=True, encoding="utf-8",
            timeout=60,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        output = json.loads(result.stdout) if result.stdout.strip() else {}
        return output, result.stderr

    def test_most_restrictive_decision_wins_and_every_context_is_kept(self):
        output, _ = self.dispatch(["--hook", "allow.py", "--hook", "ask.py", "--hook", "context.py",
                                   "--hook", "deny.py", "--hook", "echo.py"])
        specific = output["hookSpecificOutput"]
        self.assertEqual("deny", specific["permissionDecision"])
        self.assertEqual("deny reason", specific["permissionDecisionReason"])
        self.assertEqual("context from Bash\n\necho m1", specific["additionalContext"])

        output, _ = self.dispatch(["--hook", "allow.py", "--hook", "ask.py"])
        self.assertEqual("ask", output["hookSpecificOutput"]["permissionDecision"])
        self.assertEqual("ask reason", output["hookSpecificOutput"]["permissionDecisionReason"])

    def test_each_gate_reads_the_full_payload_even_after_a_sibling_rebinds_stdin(self):
        output, _ = self.dispatch(["--hook", "rebind.py", "--hook", "echo.py", "--hook", "crash.py",
                                   "--hook", "echo.py"])
        self.assertEqual("echo m1\n\necho m1", output["hookSpecificOutput"]["additionalContext"])

    def test_a_crashing_gate_is_reported_and_its_siblings_still_run(self):
        output, stderr = self.dispatch(["--hook", "crash.py", "--hook", "context.py"])
        self.assertIn("crash.py", stderr)
        self.assertIn("gate exploded", stderr)
        self.assertEqual("context from Bash", output["hookSpecificOutput"]["additionalContext"])
        self.assertEqual("deny", output["hookSpecificOutput"]["permissionDecision"])

    def test_failed_required_startup_never_acknowledges_readiness(self):
        token = "verified-startup-token-that-is-long-enough"
        environment = dict(os.environ, TJ_AGENTS_STARTUP_ACK_DIRECTORY=self.temp.name,
                           TJ_AGENTS_STARTUP_ACK_TOKEN=token, TJ_AGENTS_STARTUP_REQUIRED_HOOKS='[]')
        for failed in ("crash.py", "missing.py"):
            with self.subTest(failed=failed):
                result = subprocess.run(
                    [sys.executable, "-B", str(self.hooks / DISPATCH.name), "--hook", failed],
                    input=json.dumps({"hook_event_name": "SessionStart"}), capture_output=True,
                    text=True, env=environment, timeout=20,
                )
                self.assertEqual(0, result.returncode)
                self.assertFalse(json.loads(result.stdout)["continue"])
                self.assertFalse((Path(self.temp.name) / token).exists())

    def test_one_successful_startup_hook_cannot_conceal_a_required_sibling_failure(self):
        token = 'aggregate-startup-token-that-is-long-enough'
        environment = dict(os.environ, TJ_AGENTS_STARTUP_ACK_DIRECTORY=self.temp.name,
                           TJ_AGENTS_STARTUP_ACK_TOKEN=token,
                           TJ_AGENTS_STARTUP_REQUIRED_HOOKS=json.dumps(['base@tj-agents', 'workflow@tj-agents']))
        for name, gate in [('base', 'plain.py'), ('workflow', 'crash.py')]:
            plugin = Path(self.temp.name) / name
            shutil.copytree(self.hooks, plugin / 'hooks')
            (plugin / 'harness.json').write_text(json.dumps({'plugin': 'tj-agents/' + name}), encoding='utf-8')
            result = subprocess.run([sys.executable, '-B', str(plugin / 'hooks/hook_dispatch.py'),
                                     '--hook', gate], input=json.dumps({'hook_event_name': 'SessionStart'}),
                                    capture_output=True, text=True, env=environment, timeout=20)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertFalse((Path(self.temp.name) / token).exists())
        failure = (Path(self.temp.name) / (token + '.failed')).read_text(encoding='utf-8')
        self.assertIn('workflow@tj-agents', failure)
        self.assertIn('gate exploded', failure)

    def test_startup_acknowledgement_waits_for_every_required_dispatcher(self):
        token = 'complete-startup-token-that-is-long-enough'
        environment = dict(os.environ, TJ_AGENTS_STARTUP_ACK_DIRECTORY=self.temp.name,
                           TJ_AGENTS_STARTUP_ACK_TOKEN=token,
                           TJ_AGENTS_STARTUP_REQUIRED_HOOKS=json.dumps(['base@tj-agents', 'workflow@tj-agents']))
        for index, name in enumerate(('base', 'workflow')):
            plugin = Path(self.temp.name) / name
            shutil.copytree(self.hooks, plugin / 'hooks')
            (plugin / 'harness.json').write_text(json.dumps({'plugin': 'tj-agents/' + name}), encoding='utf-8')
            result = subprocess.run([sys.executable, '-B', str(plugin / 'hooks/hook_dispatch.py'),
                                     '--hook', 'plain.py'], input=json.dumps({'hook_event_name': 'SessionStart'}),
                                    capture_output=True, text=True, env=environment, timeout=20)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(index == 1, (Path(self.temp.name) / token).exists())

    def test_a_gate_raising_a_base_exception_is_a_crash_not_an_overrun(self):
        for deadline in ([], ["--deadline", "20"]):
            output, stderr = self.dispatch([*deadline, "--hook", "interrupt.py", "--hook", "context.py"])
            self.assertIn("gate interrupted", stderr)
            self.assertEqual("context from Bash", output["hookSpecificOutput"]["additionalContext"])
            self.assertNotIn("systemMessage", output)

    def test_stop_blocks_combine_exit_code_and_json_reasons(self):
        output, _ = self.dispatch(["--hook", "block.py", "--hook", "deny.py", "--hook", "imports.py"],
                                  event="Stop", tool="")
        self.assertEqual("block", output["decision"])
        self.assertEqual("keep working\n\ndeny reason", output["reason"])
        self.assertEqual("sibling import resolved", output["systemMessage"])
        self.assertNotIn("hookSpecificOutput", output)

    def test_stop_nonblocking_gate_failures_block_and_preserve_siblings(self):
        cases = (
            ("crash.py", "gate exploded", [[]]),
            ("silent_failure.py", "exited with status 1", [[]]),
            ("missing.py", "FileNotFoundError", [[]]),
            ("interrupt.py", "gate interrupted", [[], ["--deadline", "20"]]),
        )
        for failed, diagnostic, deadlines in cases:
            for deadline in deadlines:
                for event_field in ("hook_event_name", "hookEventName"):
                    with self.subTest(failed=failed, deadline=deadline, event_field=event_field):
                        output, stderr = self.dispatch(
                            [*deadline, "--hook", "block.py", "--hook", "context.py",
                             "--hook", "imports.py", "--hook", failed],
                            event="Stop", tool="Bash", event_field=event_field,
                        )
                        self.assertEqual("block", output["decision"])
                        self.assertIn("keep working", output["reason"])
                        self.assertIn(f"{failed} failed with exit status 1", output["reason"])
                        self.assertIn("Repair the gate and retry this Stop event.", output["reason"])
                        self.assertIn(diagnostic, stderr)
                        self.assertEqual("context from Bash",
                                         output["hookSpecificOutput"]["additionalContext"])
                        self.assertEqual("sibling import resolved", output["systemMessage"])

    def test_stop_deadline_blocks_with_and_without_finished_siblings(self):
        output, _ = self.dispatch(["--deadline", "1", "--hook", "hang.py"], event="Stop", tool="")
        self.assertEqual("block", output["decision"])
        self.assertIn("hang.py did not finish within 1s", output["reason"])
        self.assertIn("hang.py did not finish within 1s", output["systemMessage"])

        output, _ = self.dispatch(
            ["--deadline", "1", "--hook", "block.py", "--hook", "context.py", "--hook", "imports.py",
             "--hook", "hang.py", "--hook", "deny.py"],
            event="Stop", tool="Bash",
        )
        self.assertEqual("block", output["decision"])
        self.assertIn("keep working", output["reason"])
        self.assertIn("hang.py did not finish within 1s", output["reason"])
        self.assertIn("these gates did not run: deny.py", output["reason"])
        self.assertEqual("context from Bash", output["hookSpecificOutput"]["additionalContext"])
        self.assertIn("sibling import resolved", output["systemMessage"])

    def test_torn_stop_install_fails_closed_when_a_sibling_import_is_missing(self):
        hooks = Path(self.temp.name) / "torn" / "hooks"
        hooks.mkdir(parents=True)
        shutil.copy2(DISPATCH, hooks / DISPATCH.name)
        (hooks / "torn.py").write_text("from missing_dependency import VALUE\n", encoding="utf-8")
        isolated = Path(self.temp.name) / "isolated"
        isolated.mkdir()
        environment = dict(os.environ, PYTHONPATH="")
        result = subprocess.run(
            [sys.executable, "-B", str(hooks / DISPATCH.name), "--hook", "torn.py"],
            input=json.dumps({"hookEventName": "Stop", "cwd": str(isolated), "sessionId": "session"}),
            capture_output=True, text=True, encoding="utf-8", cwd=isolated, env=environment, timeout=20,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual("block", output["decision"])
        self.assertIn("torn.py failed with exit status 1", output["reason"])
        self.assertIn("Repair the gate and retry this Stop event.", output["reason"])
        self.assertIn("ModuleNotFoundError", result.stderr)
        self.assertIn("missing_dependency", result.stderr)

    def test_a_gate_past_the_deadline_keeps_finished_verdicts_and_reports_the_rest(self):
        started = time.monotonic()
        output, _ = self.dispatch(["--deadline", "2", "--hook", "deny.py", "--hook", "context.py",
                                   "--hook", "hang.py", "--hook", "ask.py"])
        self.assertLess(time.monotonic() - started, 30)
        specific = output["hookSpecificOutput"]
        self.assertEqual("deny", specific["permissionDecision"])
        self.assertEqual("deny reason", specific["permissionDecisionReason"])
        self.assertIn("context from Bash", specific["additionalContext"])
        self.assertIn("hang.py did not finish within 2s", specific["additionalContext"])
        self.assertIn("these gates did not run: ask.py", output["systemMessage"])

    def test_silent_gates_produce_no_output(self):
        output, stderr = self.dispatch(["--hook", "rebind.py"])
        self.assertEqual({}, output)
        self.assertEqual("", stderr)

    def test_malformed_pretool_output_does_not_supply_a_successful_verdict(self):
        output, stderr = self.dispatch(["--hook", "plain.py", "--hook", "allow.py"])
        self.assertEqual("deny", output["hookSpecificOutput"]["permissionDecision"])
        self.assertIn("plain.py", stderr)

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

    def test_required_hook_timeout_denies_allow_ask_defer_and_missing_decisions(self):
        for first in ("allow.py", "ask.py", "defer.py", "context.py"):
            with self.subTest(first=first):
                output, _ = self.dispatch(["--deadline", "2", "--hook", first,
                                           "--hook", "hang.py"])
                specific = output["hookSpecificOutput"]
                self.assertEqual("deny", specific["permissionDecision"])
                self.assertIn("hang.py", specific["permissionDecisionReason"])
                self.assertIn("hang.py did not finish within 2s", specific["additionalContext"])
                self.assertIn("hang.py did not finish within 2s", output["systemMessage"])

    def test_required_hook_timeout_before_deny_names_stalled_and_skipped_gates(self):
        output, _ = self.dispatch(["--deadline", "2", "--hook", "hang.py",
                                   "--hook", "deny.py"])
        specific = output["hookSpecificOutput"]
        self.assertEqual("deny", specific["permissionDecision"])
        self.assertIn("hang.py did not finish", specific["permissionDecisionReason"])
        self.assertIn("these gates did not run: deny.py", specific["permissionDecisionReason"])

    def test_required_hook_timeout_preserves_completed_deny_reason_and_context(self):
        output, _ = self.dispatch(["--deadline", "2", "--hook", "deny.py",
                                   "--hook", "context.py", "--hook", "hang.py"])
        specific = output["hookSpecificOutput"]
        self.assertEqual("deny", specific["permissionDecision"])
        self.assertEqual("deny reason", specific["permissionDecisionReason"])
        self.assertIn("context from Bash", specific["additionalContext"])
        self.assertIn("hang.py did not finish within 2s", output["systemMessage"])

    def test_timeout_blocks_by_default_and_stops_other_events(self):
        output, _ = self.dispatch(["--deadline", "2", "--hook", "allow.py", "--hook", "hang.py"])
        self.assertEqual("deny", output["hookSpecificOutput"]["permissionDecision"])
        output, _ = self.dispatch(["--deadline", "2", "--hook", "context.py",
                                   "--hook", "hang.py"], event="PostToolUse")
        specific = output["hookSpecificOutput"]
        self.assertNotIn("permissionDecision", specific)
        self.assertIn("context from Bash", specific["additionalContext"])
        self.assertIn("hang.py did not finish within 2s", output["systemMessage"])
        self.assertFalse(output["continue"])
        output, _ = self.dispatch(["--deadline", "2", "--hook", "allow.py"])
        self.assertEqual("allow", output["hookSpecificOutput"]["permissionDecision"])


if __name__ == "__main__":
    unittest.main()
