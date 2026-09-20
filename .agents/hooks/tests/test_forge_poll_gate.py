import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path


HOOK = Path(__file__).resolve().parents[1] / "forge_poll_gate.py"
sys.path.insert(0, str(HOOK.parent))


def load_gate():
    spec = importlib.util.spec_from_file_location("forge_poll_gate", HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load_gate()


class ExtractCommandTests(unittest.TestCase):
    """Claude sends a string; Codex exec_command / unified-exec send a list, a `cmd`, an `input`,
    or a nested `action.command`. A shape the hook cannot read is a poll it waves through."""

    def test_claude_bash_string(self):
        self.assertEqual("gh pr checks 9", gate.extract_command("Bash", {"command": "gh pr checks 9"}))

    def test_powershell_string(self):
        self.assertEqual("gh pr checks 9", gate.extract_command("PowerShell", {"command": "gh pr checks 9"}))

    def test_codex_shell_argv_list_unwraps_the_script(self):
        self.assertEqual(
            "gh pr checks 9",
            gate.extract_command("shell", {"command": ["bash", "-lc", "gh pr checks 9"]}),
        )

    def test_codex_exec_command_cmd_field(self):
        self.assertEqual(
            "gh run list", gate.extract_command("exec_command", {"cmd": "gh run list"})
        )

    def test_codex_unified_exec_input_list(self):
        self.assertEqual(
            "gh pr view 9 --json state",
            gate.extract_command("unified_exec", {"input": ["bash", "-c", "gh pr view 9 --json state"]}),
        )

    def test_codex_local_shell_nested_action(self):
        self.assertEqual(
            "gh pr checks",
            gate.extract_command(
                "local_shell", {"action": {"type": "exec", "command": ["bash", "-lc", "gh pr checks"]}}
            ),
        )

    def test_a_non_shell_tool_is_ignored(self):
        self.assertIsNone(gate.extract_command("Write", {"command": "gh pr checks 9"}))

    def test_a_plain_argv_without_a_shell_wrapper_is_joined(self):
        self.assertEqual("gh pr checks 9", gate.extract_command("shell", {"command": ["gh", "pr", "checks", "9"]}))


class CodexDetectionTests(unittest.TestCase):
    def test_a_turn_id_marks_a_codex_payload(self):
        self.assertTrue(gate.is_codex_invocation({"turn_id": "t1"}))
        self.assertTrue(gate.is_codex_invocation({"turnId": "t1"}))

    def test_a_claude_payload_has_no_turn_id(self):
        self.assertFalse(gate.is_codex_invocation({"session_id": "s1"}))


class ForgePollClassificationTests(unittest.TestCase):
    def test_gh_pr_checks_is_a_poll(self):
        self.assertTrue(gate.is_forge_poll("gh pr checks 912"))

    def test_gh_pr_status_is_a_poll(self):
        self.assertTrue(gate.is_forge_poll("gh pr status"))

    def test_gh_pr_view_with_status_fields_is_a_poll(self):
        self.assertTrue(gate.is_forge_poll("gh pr view 912 --json state,statusCheckRollup"))

    def test_bare_gh_pr_view_is_a_poll(self):
        self.assertTrue(gate.is_forge_poll("gh pr view 912"))

    def test_gh_pr_view_for_title_only_is_not_a_poll(self):
        self.assertFalse(gate.is_forge_poll("gh pr view 912 --json title,body,url"))

    def test_gh_run_list_is_a_poll(self):
        self.assertTrue(gate.is_forge_poll("gh run list --event merge_group -L 15"))

    def test_gh_run_view_is_a_poll(self):
        self.assertTrue(gate.is_forge_poll("gh run view 123456"))

    def test_gh_run_view_log_is_diagnosis_not_a_poll(self):
        self.assertFalse(gate.is_forge_poll("gh run view 123456 --log-failed"))
        self.assertFalse(gate.is_forge_poll("gh run view 123456 --log"))

    def test_graphql_merge_queue_probe_is_a_poll(self):
        self.assertTrue(
            gate.is_forge_poll("gh api graphql -f query='{repository{pullRequest(number:9){mergeQueueEntry{state}}}}'")
        )

    def test_check_runs_api_is_a_poll(self):
        self.assertTrue(gate.is_forge_poll("gh api repos/o/r/commits/abc123/check-runs"))

    def test_pr_diff_is_not_a_poll(self):
        self.assertFalse(gate.is_forge_poll("gh pr diff 912"))

    def test_a_non_gh_command_is_not_a_poll(self):
        self.assertFalse(gate.is_forge_poll("git fetch origin --prune"))

    def test_a_repo_declared_extra_pattern_is_a_poll(self):
        import re

        self.assertTrue(gate.is_forge_poll("buildkite status 912", [re.compile(r"buildkite status")]))


class MonitorShapeTests(unittest.TestCase):
    def test_the_shared_workflow_monitor_is_a_monitor(self):
        self.assertTrue(gate.is_monitor_shape("python .agents/workflows/workflow_ops.py --workflow-run-id x monitor --kind pr --id 9"))

    def test_mentioning_the_monitor_does_not_bypass_the_gate(self):
        for command in (
            "echo workflow_ops.py monitor; gh pr checks 9",
            "python .agents/workflows/workflow_ops.py --workflow-run-id x monitor --kind pr --id 9 | gh pr checks 9",
            "python C:\\untrusted\\workflow_ops.py --workflow-run-id x monitor --kind pr --id 9",
            "python .agents/workflows/workflow_ops.py --workflow-run-id x monitor --kind pr --id 9 <(gh pr checks 9)",
        ):
            with self.subTest(command=command):
                self.assertFalse(gate.is_monitor_shape(command))

    def test_a_while_loop_that_sleeps_around_a_gh_read_is_forbidden(self):
        command = "while true; do gh pr checks 9 || true; sleep 60; done"
        self.assertFalse(gate.is_monitor_shape(command))
        self.assertTrue(gate.is_forbidden_monitor_shape(command))

    def test_gh_run_watch_is_forbidden(self):
        command = "gh run watch 123456 --exit-status"
        self.assertFalse(gate.is_monitor_shape(command))
        self.assertTrue(gate.is_forbidden_monitor_shape(command))

    def test_a_bare_poll_is_not_a_monitor(self):
        self.assertFalse(gate.is_monitor_shape("gh pr checks 9"))

    def test_a_loop_without_sleep_is_not_a_monitor(self):
        self.assertFalse(gate.is_monitor_shape("for pr in 1 2 3; do gh pr checks $pr; done"))


class IdentityTests(unittest.TestCase):
    def test_explicit_pr_number(self):
        self.assertEqual("o/r#pr912", gate.identity_key("gh pr checks 912", "o/r", None))

    def test_graphql_pr_number(self):
        self.assertEqual(
            "o/r#pr912",
            gate.identity_key("gh api graphql -f query='{pullRequest(number: 912){x}}'", "o/r", None),
        )

    def test_run_id(self):
        self.assertEqual("o/r#run55", gate.identity_key("gh run view 55", "o/r", None))

    def test_branch_fallback_when_no_number(self):
        self.assertEqual("o/r#pr:feature-x", gate.identity_key("gh pr checks", "o/r", "feature-x"))

    def test_run_list_identity(self):
        self.assertEqual("o/r#runs", gate.identity_key("gh run list -L 5", "o/r", None))

    def test_missing_slug_falls_back_to_local(self):
        self.assertEqual("local#pr912", gate.identity_key("gh pr checks 912", None, None))


class DecideTests(unittest.TestCase):
    """The core state machine. ``signature_fn`` is a stub returning whatever the test wants the
    hook's own authoritative read to see."""

    IDENT = "o/r#pr912"

    def sig(self, value):
        return lambda: value

    def test_the_first_read_of_an_identity_is_allowed(self):
        verdict, state, message = gate.decide(
            "gh pr checks 912", self.IDENT, None,
            now=1000, marker="m0", monitor_shape=False, signature_fn=self.sig("PENDING"),
        )
        self.assertEqual("allow", verdict)
        self.assertEqual("PENDING", state["sig"])
        self.assertEqual("m0", state["marker"])
        self.assertIsNone(message)

    def test_a_repeated_read_with_unchanged_state_and_no_wake_is_blocked(self):
        prior = {"ts": 1000, "marker": "m0", "sig": "PENDING"}
        verdict, state, message = gate.decide(
            "gh pr checks 912", self.IDENT, prior,
            now=1030, marker="m0", monitor_shape=False, signature_fn=self.sig("PENDING"),
        )
        self.assertEqual("block", verdict)
        self.assertIn("repeated forge read of o/r#pr912", message)
        self.assertIn("workflow_ops.py", message)

    def test_a_repeated_read_after_a_new_external_turn_is_allowed_once(self):
        prior = {"ts": 1000, "marker": "m0", "sig": "PENDING"}
        verdict, state, _ = gate.decide(
            "gh pr checks 912", self.IDENT, prior,
            now=1030, marker="m1", monitor_shape=False, signature_fn=self.sig("PENDING"),
        )
        self.assertEqual("allow", verdict)
        self.assertEqual("m1", state["marker"])
        # ...and the very next read, still at m1 with unchanged state, is blocked again.
        verdict2, _, _ = gate.decide(
            "gh pr checks 912", self.IDENT, state,
            now=1040, marker="m1", monitor_shape=False, signature_fn=self.sig("PENDING"),
        )
        self.assertEqual("block", verdict2)

    def test_a_repeated_read_after_the_observed_state_moved_is_allowed(self):
        prior = {"ts": 1000, "marker": "m0", "sig": "PENDING"}
        verdict, state, _ = gate.decide(
            "gh pr checks 912", self.IDENT, prior,
            now=1030, marker="m0", monitor_shape=False, signature_fn=self.sig("FAILURE:build"),
        )
        self.assertEqual("allow", verdict)
        self.assertEqual("FAILURE:build", state["sig"])

    def test_a_repeated_read_the_hook_cannot_verify_fails_closed(self):
        prior = {"ts": 1000, "marker": "m0", "sig": "PENDING"}
        verdict, _, message = gate.decide(
            "gh pr checks 912", self.IDENT, prior,
            now=1030, marker="m0", monitor_shape=False, signature_fn=self.sig(None),
        )
        self.assertEqual("block", verdict)

    def test_idle_long_enough_without_a_transcript_is_treated_as_a_fresh_turn(self):
        prior = {"ts": 1000, "marker": None, "sig": "PENDING"}
        verdict, _, _ = gate.decide(
            "gh pr checks 912", self.IDENT, prior,
            now=1000 + gate.IDLE_RESUME_SECONDS + 1, marker=None,
            monitor_shape=False, signature_fn=self.sig("PENDING"),
        )
        self.assertEqual("allow", verdict)

    def test_a_first_monitor_is_registered_and_allowed(self):
        verdict, state, _ = gate.decide(
            "while :; do gh pr checks 912; sleep 60; done", self.IDENT, None,
            now=1000, marker="m0", monitor_shape=True, signature_fn=self.sig("PENDING"),
        )
        self.assertEqual("allow", verdict)
        self.assertEqual(1000, state["monitor"])

    def test_a_second_concurrent_monitor_for_the_same_identity_is_blocked(self):
        prior = {"ts": 1000, "marker": "m0", "sig": None, "monitor": 1000}
        verdict, _, message = gate.decide(
            "while :; do gh pr checks 912; sleep 60; done", self.IDENT, prior,
            now=1100, marker="m0", monitor_shape=True, signature_fn=self.sig("PENDING"),
        )
        self.assertEqual("block", verdict)
        self.assertIn("a background monitor already owns o/r#pr912", message)

    def test_a_monitor_for_a_different_identity_is_untouched(self):
        # Different identity => the caller loads no state => first monitor => allowed.
        verdict, _, _ = gate.decide(
            "while :; do gh pr checks 5; sleep 60; done", "o/r#pr5", None,
            now=1100, marker="m0", monitor_shape=True, signature_fn=self.sig("PENDING"),
        )
        self.assertEqual("allow", verdict)

    def test_the_read_after_a_monitor_was_registered_is_the_allowed_post_wake_read(self):
        prior = {"ts": 1000, "marker": "m0", "sig": None, "monitor": 1000}
        verdict, state, _ = gate.decide(
            "gh pr checks 912", self.IDENT, prior,
            now=1400, marker="m1", monitor_shape=False, signature_fn=self.sig("SUCCESS"),
        )
        self.assertEqual("allow", verdict)
        self.assertNotIn("monitor", state)
        self.assertEqual("SUCCESS", state["sig"])

    def test_a_stale_monitor_registration_does_not_block_a_new_monitor(self):
        prior = {"ts": 1, "marker": "m0", "sig": None, "monitor": 1}
        verdict, _, _ = gate.decide(
            "while :; do gh pr checks 912; sleep 60; done", self.IDENT, prior,
            now=1 + gate.MONITOR_TTL_SECONDS + 1, marker="m0",
            monitor_shape=True, signature_fn=self.sig("PENDING"),
        )
        self.assertEqual("allow", verdict)


class TranscriptMarkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "transcript.jsonl"

    def write(self, entries):
        self.path.write_text("\n".join(json.dumps(e) for e in entries), encoding="utf-8")

    def test_a_pure_tool_result_turn_is_not_an_external_turn(self):
        self.write(
            [
                {"type": "user", "uuid": "u1", "message": {"role": "user", "content": "check PR 912"}},
                {"type": "assistant", "uuid": "a1", "message": {"role": "assistant", "content": "ok"}},
                {"type": "user", "uuid": "tr1", "message": {"content": [{"type": "tool_result", "content": "x"}]}},
            ]
        )
        self.assertEqual("u1", gate.latest_external_turn_marker(str(self.path)))

    def test_a_new_user_message_moves_the_marker(self):
        self.write(
            [
                {"type": "user", "uuid": "u1", "message": {"content": "check PR 912"}},
                {"type": "assistant", "uuid": "a1", "message": {"content": "ok"}},
                {"type": "user", "uuid": "tr1", "message": {"content": [{"type": "tool_result", "content": "x"}]}},
                {"type": "user", "uuid": "u2", "message": {"content": "any update?"}},
            ]
        )
        self.assertEqual("u2", gate.latest_external_turn_marker(str(self.path)))

    def test_a_system_notification_counts_as_an_external_turn(self):
        self.write(
            [
                {"type": "user", "uuid": "u1", "message": {"content": "go"}},
                {"type": "system", "uuid": "sys1", "subtype": "background_task_complete", "content": "done"},
            ]
        )
        self.assertEqual("sys1", gate.latest_external_turn_marker(str(self.path)))

    def test_a_missing_transcript_is_none(self):
        self.assertIsNone(gate.latest_external_turn_marker(str(self.path / "nope")))
        self.assertIsNone(gate.latest_external_turn_marker(None))

    def test_a_codex_rollout_shape_is_understood(self):
        # Codex rollout entries carry `role`/`id` and a function-call-output content type.
        self.write(
            [
                {"type": "message", "role": "user", "id": "c1", "content": [{"type": "input_text", "text": "land it"}]},
                {"type": "message", "role": "assistant", "id": "c2", "content": [{"type": "output_text", "text": "ok"}]},
                {"type": "message", "role": "user", "id": "c3",
                 "content": [{"type": "function_call_output", "output": "checks: pending"}]},
            ]
        )
        self.assertEqual("c1", gate.latest_external_turn_marker(str(self.path)))
        self.write(
            [
                {"type": "message", "role": "user", "id": "c1", "content": [{"type": "input_text", "text": "land it"}]},
                {"type": "message", "role": "user", "id": "c4", "content": [{"type": "input_text", "text": "any update?"}]},
            ]
        )
        self.assertEqual("c4", gate.latest_external_turn_marker(str(self.path)))


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / ".agents").mkdir()

    def write(self, body):
        path = self.root / gate.CONFIG_FILE
        path.write_text(body if isinstance(body, str) else json.dumps(body), encoding="utf-8")
        return path

    def test_an_empty_table_is_valid(self):
        self.assertEqual([], gate.extra_poll_patterns(self.write({})))

    def test_a_declared_pattern_compiles(self):
        patterns = gate.extra_poll_patterns(self.write({"extra_poll_patterns": [r"buildkite build"]}))
        self.assertTrue(patterns[0].search("buildkite build 9"))

    def test_malformed_json_raises(self):
        with self.assertRaises(gate.ConfigUnusable):
            gate.extra_poll_patterns(self.write("{ not json"))

    def test_a_non_list_raises(self):
        with self.assertRaises(gate.ConfigUnusable):
            gate.extra_poll_patterns(self.write({"extra_poll_patterns": "buildkite"}))

    def test_an_uncompilable_pattern_raises(self):
        with self.assertRaises(gate.ConfigUnusable):
            gate.extra_poll_patterns(self.write({"extra_poll_patterns": ["("]}))

    def test_find_config_walks_up(self):
        nested = self.root / "a" / "b"
        nested.mkdir(parents=True)
        expected = self.write({})
        self.assertTrue(os.path.samefile(expected, gate.find_config(nested)))

    def test_find_config_absent_is_none(self):
        self.assertIsNone(gate.find_config(self.root))


class EndToEndTests(unittest.TestCase):
    """The hook as a subprocess, with a fake `gh` on PATH so the authoritative read is deterministic."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)

        self.repo = base / "repo"
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "remote", "add", "origin",
                        "https://github.com/concertable/agents.git"], check=True)
        (self.repo / ".agents").mkdir()
        (self.repo / ".agents" / "forge-poll-gate.json").write_text(
            json.dumps({"extra_poll_patterns": []}), encoding="utf-8"
        )

        self.session = uuid.uuid4().hex
        self.state_dir = base / "state"
        self.gh_state = base / "gh_state.txt"
        self.gh_state.write_text("PENDING", encoding="utf-8")

        # A deterministic `gh` shim so the hook's own authoritative read has a known answer.
        # POSIX only: Python 3.12+ refuses to exec a .cmd/.bat from a subprocess arg list, and CI
        # runs on Linux. On Windows the shim is absent, `gh` resolves to nothing, and the tests
        # that do not assert a state transition still hold (an unverifiable repeat fails closed).
        bindir = base / "bin"
        bindir.mkdir()
        self.has_gh_shim = os.name != "nt"
        if self.has_gh_shim:
            gh = bindir / "gh"
            gh.write_text(f'#!/bin/sh\ncat "{self.gh_state}"\n', encoding="utf-8")
            gh.chmod(gh.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        self.bindir = bindir

    def run_hook(self, command, *, marker_lines=None, tool_name="Bash", codex=False):
        env = dict(os.environ)
        env["PATH"] = str(self.bindir) + os.pathsep + env["PATH"]
        env["FORGE_POLL_GATE_STATE_DIR"] = str(self.state_dir)
        payload = {
            "session_id": self.session,
            "hook_event_name": "PreToolUse",
            "tool_use_id": uuid.uuid4().hex,
            "tool_name": "shell" if codex else tool_name,
            "cwd": str(self.repo),
            "tool_input": (
                {"command": ["bash", "-lc", command]} if codex else {"command": command}
            ),
        }
        if codex:
            payload["turn_id"] = uuid.uuid4().hex
        if marker_lines is not None:
            transcript = Path(self.temp.name) / f"t-{abs(hash(str(marker_lines)))}.jsonl"
            transcript.write_text("\n".join(json.dumps(e) for e in marker_lines), encoding="utf-8")
            payload["transcript_path"] = str(transcript)
        return subprocess.run(
            [sys.executable, str(HOOK)], input=json.dumps(payload),
            capture_output=True, text=True, cwd=str(self.repo), env=env,
        )

    def user_turn(self, uuid):
        return [{"type": "user", "uuid": uuid, "message": {"content": "check it"}}]

    def test_first_read_allowed_then_identical_repeat_blocked(self):
        first = self.run_hook("gh pr checks 912", marker_lines=self.user_turn("u1"))
        self.assertEqual(0, first.returncode, first.stderr)

        second = self.run_hook("gh pr checks 912", marker_lines=self.user_turn("u1"))
        self.assertEqual(2, second.returncode)
        self.assertIn("repeated forge read", second.stderr)

    def test_a_repeat_for_a_different_pr_is_allowed(self):
        self.run_hook("gh pr checks 912", marker_lines=self.user_turn("u1"))
        other = self.run_hook("gh pr checks 34", marker_lines=self.user_turn("u1"))
        self.assertEqual(0, other.returncode, other.stderr)

    def test_a_codex_shell_argv_payload_is_gated_the_same_way(self):
        first = self.run_hook("gh pr checks 912", marker_lines=self.user_turn("u1"), codex=True)
        self.assertEqual(0, first.returncode, first.stderr)
        second = self.run_hook("gh pr checks 912", marker_lines=self.user_turn("u1"), codex=True)
        self.assertEqual(2, second.returncode)
        self.assertIn("repeated forge read", second.stderr)

    def test_a_state_change_between_reads_is_allowed(self):
        if not self.has_gh_shim:
            self.skipTest("needs the POSIX gh shim for a deterministic authoritative read")
        self.run_hook("gh pr checks 912", marker_lines=self.user_turn("u1"))
        self.gh_state.write_text("FAILURE", encoding="utf-8")
        moved = self.run_hook("gh pr checks 912", marker_lines=self.user_turn("u1"))
        self.assertEqual(0, moved.returncode, moved.stderr)

    def test_a_user_resumption_permits_exactly_one_read(self):
        self.run_hook("gh pr checks 912", marker_lines=self.user_turn("u1"))
        self.run_hook("gh pr checks 912", marker_lines=self.user_turn("u1"))  # blocked
        resumed = self.run_hook("gh pr checks 912", marker_lines=self.user_turn("u2"))
        self.assertEqual(0, resumed.returncode, resumed.stderr)
        again = self.run_hook("gh pr checks 912", marker_lines=self.user_turn("u2"))
        self.assertEqual(2, again.returncode)

    def test_one_background_monitor_is_permitted_and_a_second_is_blocked(self):
        loop = "python .agents/workflows/workflow_ops.py --workflow-run-id x monitor --kind pr --id 912"
        self.assertEqual(0, self.run_hook(loop, marker_lines=self.user_turn("u1")).returncode)
        second = self.run_hook(loop, marker_lines=self.user_turn("u1"))
        self.assertEqual(2, second.returncode)
        self.assertIn("a background monitor already owns", second.stderr)

    def test_direct_gh_run_watch_is_blocked(self):
        completed = self.run_hook("gh run watch 34421517660 --exit-status")
        self.assertEqual(2, completed.returncode)
        self.assertIn("not reconnect-safe", completed.stderr)

    def test_failure_diagnosis_is_never_gated(self):
        self.run_hook("gh run view 555", marker_lines=self.user_turn("u1"))
        for _ in range(3):
            result = self.run_hook("gh run view 555 --log-failed", marker_lines=self.user_turn("u1"))
            self.assertEqual(0, result.returncode, result.stderr)

    def test_an_unrelated_shell_command_is_never_gated(self):
        for _ in range(3):
            result = self.run_hook("git status", marker_lines=self.user_turn("u1"))
            self.assertEqual(0, result.returncode, result.stderr)

    def test_a_repo_without_the_opt_in_table_is_not_gated(self):
        (self.repo / ".agents" / "forge-poll-gate.json").unlink()
        self.run_hook("gh pr checks 912", marker_lines=self.user_turn("u1"))
        second = self.run_hook("gh pr checks 912", marker_lines=self.user_turn("u1"))
        self.assertEqual(0, second.returncode, second.stderr)

    def test_a_malformed_table_blocks_a_poll_loudly_but_not_other_commands(self):
        (self.repo / ".agents" / "forge-poll-gate.json").write_text("{ broken", encoding="utf-8")
        self.assertEqual(0, self.run_hook("git status", marker_lines=self.user_turn("u1")).returncode)
        poll = self.run_hook("gh pr checks 912", marker_lines=self.user_turn("u1"))
        self.assertEqual(2, poll.returncode)
        self.assertIn("could not be read", poll.stderr)


if __name__ == "__main__":
    unittest.main()
