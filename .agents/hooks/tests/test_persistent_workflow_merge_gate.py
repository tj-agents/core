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


HOOK = Path(__file__).resolve().parents[1] / "persistent_workflow_merge_gate.py"
sys.path.insert(0, str(HOOK.parent))
M = "gh pr " + "merge"  # assembled so this file never contains the gated literal


def load_gate():
    spec = importlib.util.spec_from_file_location("persistent_workflow_merge_gate", HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load_gate()


class EnablesAutoTests(unittest.TestCase):
    def test_auto_form_is_detected(self):
        self.assertTrue(gate.enables_auto(M + " 12 --squash --auto"))

    def test_chained_auto_form_is_detected(self):
        self.assertTrue(gate.enables_auto('pushd "/x" && ' + M + " 12 --auto"))

    def test_a_plain_merge_without_auto_is_not_this_gates_business(self):
        self.assertFalse(gate.enables_auto(M + " 12 --squash"))

    def test_disable_auto_alone_is_not_an_enable(self):
        self.assertFalse(gate.enables_auto(M + " 12 --disable-auto"))

    def test_the_documented_re_assert_compound_is_an_enable(self):
        self.assertTrue(
            gate.enables_auto(M + " 12 --disable-auto && " + M + " 12 --merge --auto")
        )

    def test_merely_quoting_the_command_is_not_an_enable(self):
        self.assertFalse(gate.enables_auto('echo "run ' + M + ' 12 --auto"'))


class TerminalClassificationTests(unittest.TestCase):
    def test_clean_with_all_checks_complete_is_terminal(self):
        parsed = {
            "mergeStateStatus": "CLEAN",
            "statusCheckRollup": [
                {"status": "COMPLETED", "conclusion": "SUCCESS"},
                {"state": "SUCCESS"},
            ],
        }
        self.assertTrue(gate.pr_is_terminal(parsed))

    def test_a_running_check_is_not_terminal(self):
        parsed = {
            "mergeStateStatus": "CLEAN",
            "statusCheckRollup": [{"status": "IN_PROGRESS", "conclusion": ""}],
        }
        self.assertFalse(gate.pr_is_terminal(parsed))

    def test_a_queued_check_is_not_terminal(self):
        parsed = {
            "mergeStateStatus": "CLEAN",
            "statusCheckRollup": [{"status": "QUEUED", "conclusion": ""}],
        }
        self.assertFalse(gate.pr_is_terminal(parsed))

    def test_a_pending_legacy_status_is_not_terminal(self):
        parsed = {
            "mergeStateStatus": "CLEAN",
            "statusCheckRollup": [{"state": "PENDING"}],
        }
        self.assertFalse(gate.pr_is_terminal(parsed))

    def test_non_clean_merge_state_is_not_terminal_even_with_green_checks(self):
        parsed = {
            "mergeStateStatus": "BLOCKED",
            "statusCheckRollup": [{"status": "COMPLETED", "conclusion": "SUCCESS"}],
        }
        self.assertFalse(gate.pr_is_terminal(parsed))

    def test_unstable_merge_state_is_not_terminal(self):
        parsed = {
            "mergeStateStatus": "UNSTABLE",
            "statusCheckRollup": [{"status": "COMPLETED", "conclusion": "SUCCESS"}],
        }
        self.assertFalse(gate.pr_is_terminal(parsed))

    def test_an_unreadable_rollup_is_not_terminal(self):
        self.assertFalse(gate.pr_is_terminal({"mergeStateStatus": "CLEAN", "statusCheckRollup": None}))

    def test_a_failed_but_finished_check_is_still_terminal_when_clean(self):
        # If mergeStateStatus is CLEAN, GitHub will merge; a finished non-required failure does not
        # make the enqueue a walk-away.
        parsed = {
            "mergeStateStatus": "CLEAN",
            "statusCheckRollup": [{"status": "COMPLETED", "conclusion": "FAILURE"}],
        }
        self.assertTrue(gate.pr_is_terminal(parsed))


class BindingMismatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def binding(self, **overrides):
        base = {
            "repo": "concertable/agents",
            "pr": 42,
            "head": "abcdef1234567890abcdef1234567890abcdef12",
            "worktree": str(self.root),
        }
        base.update(overrides)
        return base

    def test_a_matching_binding_has_no_mismatch(self):
        self.assertIsNone(
            gate.binding_mismatch(
                self.binding(),
                repo="concertable/agents",
                pr="42",
                head="abcdef1234567890abcdef1234567890abcdef12",
                config_root=self.root,
            )
        )

    def test_a_prefix_length_head_still_matches(self):
        self.assertIsNone(
            gate.binding_mismatch(
                self.binding(head="abcdef1234567"),
                repo=None,
                pr="42",
                head="abcdef1234567890abcdef1234567890abcdef12",
                config_root=self.root,
            )
        )

    def test_a_different_pr_is_a_mismatch(self):
        self.assertIn(
            "PR #42",
            gate.binding_mismatch(
                self.binding(), repo=None, pr="43", head="abcdef1234567", config_root=self.root
            ),
        )

    def test_a_different_head_is_a_mismatch(self):
        reason = gate.binding_mismatch(
            self.binding(head="0000000000000000000000000000000000000000"),
            repo=None,
            pr="42",
            head="abcdef1234567890abcdef1234567890abcdef12",
            config_root=self.root,
        )
        self.assertIn("head", reason)

    def test_a_missing_head_is_a_mismatch(self):
        b = self.binding()
        del b["head"]
        self.assertIn("no head", gate.binding_mismatch(
            b, repo=None, pr="42", head="abcdef1234567", config_root=self.root
        ))

    def test_a_different_worktree_is_a_mismatch(self):
        reason = gate.binding_mismatch(
            self.binding(worktree="/somewhere/else"),
            repo=None,
            pr="42",
            head="abcdef1234567890abcdef1234567890abcdef12",
            config_root=self.root,
        )
        self.assertIn("worktree", reason)

    def test_repo_is_not_checked_when_the_local_slug_is_unknown(self):
        self.assertIsNone(
            gate.binding_mismatch(
                self.binding(repo="someone/else"),
                repo=None,
                pr="42",
                head="abcdef1234567890abcdef1234567890abcdef12",
                config_root=self.root,
            )
        )


class EndToEndTests(unittest.TestCase):
    """The hook as a subprocess with a deterministic `gh` shim (POSIX only, as in
    test_forge_poll_gate)."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)

        self.repo = base / "repo"
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(
            ["git", "-C", str(self.repo), "remote", "add", "origin",
             "https://github.com/concertable/agents.git"],
            check=True,
        )
        (self.repo / ".agents").mkdir()
        (self.repo / ".agents" / "persistent-workflow-gate.json").write_text(
            json.dumps({"$comment": "opt in"}), encoding="utf-8"
        )

        self.head = "1111111111111111111111111111111111111111"
        self.gh_payload = base / "gh_payload.json"
        self._write_pr(merge_state="BLOCKED", check_status="IN_PROGRESS")

        self.bindir = base / "bin"
        self.bindir.mkdir()
        self.has_gh_shim = os.name != "nt"
        if self.has_gh_shim:
            gh = self.bindir / "gh"
            gh.write_text(f'#!/bin/sh\ncat "{self.gh_payload}"\n', encoding="utf-8")
            gh.chmod(gh.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    def _write_pr(self, *, merge_state, check_status):
        self.gh_payload.write_text(
            json.dumps(
                {
                    "number": 42,
                    "headRefOid": self.head,
                    "mergeStateStatus": merge_state,
                    "statusCheckRollup": [{"status": check_status, "conclusion": ""}],
                }
            ),
            encoding="utf-8",
        )

    def write_binding(self, **overrides):
        binding = {
            "repo": "concertable/agents",
            "pr": 42,
            "branch": "Feature/x",
            "worktree": str(self.repo.resolve()),
            "head": self.head,
            "checks": ["c1"],
            "runs": ["r1"],
        }
        binding.update(overrides)
        (self.repo / ".agents" / "persistent-workflow-binding.json").write_text(
            json.dumps(binding), encoding="utf-8"
        )

    def run_hook(self, command=None):
        env = dict(os.environ)
        env["PATH"] = str(self.bindir) + os.pathsep + env["PATH"]
        payload = {
            "session_id": uuid.uuid4().hex,
            "hook_event_name": "PreToolUse",
            "tool_use_id": uuid.uuid4().hex,
            "tool_name": "Bash",
            "cwd": str(self.repo),
            "tool_input": {"command": command or (M + " 42 --squash --auto")},
        }
        return subprocess.run(
            [sys.executable, str(HOOK)], input=json.dumps(payload),
            capture_output=True, text=True, cwd=str(self.repo), env=env,
        )

    def test_non_terminal_pr_with_no_binding_is_blocked(self):
        if not self.has_gh_shim:
            self.skipTest("needs the POSIX gh shim")
        result = self.run_hook()
        self.assertEqual(2, result.returncode)
        self.assertIn("no persistent-workflow binding", result.stderr)

    def test_non_terminal_pr_with_a_matching_binding_is_allowed(self):
        if not self.has_gh_shim:
            self.skipTest("needs the POSIX gh shim")
        self.write_binding()
        result = self.run_hook()
        self.assertEqual(0, result.returncode, result.stderr)

    def test_non_terminal_pr_with_a_stale_head_binding_is_blocked(self):
        if not self.has_gh_shim:
            self.skipTest("needs the POSIX gh shim")
        self.write_binding(head="9999999999999999999999999999999999999999")
        result = self.run_hook()
        self.assertEqual(2, result.returncode)
        self.assertIn("bound to head", result.stderr)

    def test_non_terminal_pr_with_a_wrong_worktree_binding_is_blocked(self):
        if not self.has_gh_shim:
            self.skipTest("needs the POSIX gh shim")
        self.write_binding(worktree="/not/this/checkout")
        result = self.run_hook()
        self.assertEqual(2, result.returncode)
        self.assertIn("worktree", result.stderr)

    def test_a_terminal_pr_needs_no_binding(self):
        if not self.has_gh_shim:
            self.skipTest("needs the POSIX gh shim")
        self._write_pr(merge_state="CLEAN", check_status="COMPLETED")
        result = self.run_hook()
        self.assertEqual(0, result.returncode, result.stderr)

    def test_a_plain_merge_without_auto_is_not_gated(self):
        result = self.run_hook(M + " 42 --squash")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_a_repo_that_did_not_opt_in_is_not_gated(self):
        (self.repo / ".agents" / "persistent-workflow-gate.json").unlink()
        result = self.run_hook()
        self.assertEqual(0, result.returncode, result.stderr)

    def test_an_unresolvable_pr_state_fails_closed(self):
        if not self.has_gh_shim:
            self.skipTest("needs the POSIX gh shim")
        self.gh_payload.write_text("not json", encoding="utf-8")
        result = self.run_hook()
        self.assertEqual(2, result.returncode)
        self.assertIn("cannot resolve", result.stderr)

    def test_naming_another_repository_is_not_gated(self):
        result = self.run_hook(M + " 42 --repo other/elsewhere --squash --auto")
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
