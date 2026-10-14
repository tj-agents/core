import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "work_item_sessions", ROOT / ".agents/machine/scripts/work_item_sessions.py"
)
WIS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WIS)

STORE = WIS._session_store()
REAL_RECOVERY = WIS._agent_recovery()
GIT = shutil.which("git")


def fake_recovery(liveness_result="closed", open_session=None):
    return types.SimpleNamespace(
        SESSION_ID=REAL_RECOVERY.SESSION_ID,
        liveness=mock.Mock(return_value=liveness_result),
        open_session=open_session if open_session is not None else mock.Mock(return_value={"ok": True}),
    )


@unittest.skipUnless(GIT, "git is required for work-item session tests")
class WorkItemSessionsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="work item sessions é ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.state = self.root / "state"
        self.environ = mock.patch.dict(os.environ, {"AGENT_STATE_DIRECTORY": str(self.state)}, clear=False)
        self.environ.start()
        self.addCleanup(self.environ.stop)
        self.repo = self.root / "repo with spaces"
        self.repo.mkdir()
        self._run_git(self.repo, "init")
        self._run_git(self.repo, "config", "user.email", "test@example.com")
        self._run_git(self.repo, "config", "user.name", "Test User")
        (self.repo / "README.md").write_text("hello\n", encoding="utf-8")
        self._run_git(self.repo, "add", "README.md")
        self._run_git(self.repo, "commit", "-m", "initial")
        self._run_git(self.repo, "remote", "add", "origin", "https://github.com/tj-agents/core.git")

    def _run_git(self, cwd, *args):
        result = subprocess.run(
            ["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        return result.stdout.strip()

    def _claim_claude(self, session_id="a2bcd5c4-bf6d-4087-95e3-d7ba7f711875", **kwargs):
        with mock.patch.dict(os.environ, {
            "CLAUDE_CODE_SESSION_ID": session_id,
            "CLAUDE_CONFIG_DIR": str(self.root / "claude-profile"),
        }, clear=False):
            return WIS.cmd_claim(
                kwargs.pop("work_item", "example-feature/example-item"), "claude",
                role=kwargs.pop("role", "owner"), predecessor=kwargs.pop("predecessor", None), cwd=self.repo,
            )

    def _claim_codex(self, session_id="01a12aa7-5b58-7312-9400-ef710762147f", **kwargs):
        with mock.patch.dict(os.environ, {
            "CODEX_THREAD_ID": session_id,
            "CODEX_HOME": str(self.root / "codex-profile"),
        }, clear=False):
            return WIS.cmd_claim(
                kwargs.pop("work_item", "example-feature/example-item"), "codex",
                role=kwargs.pop("role", "bounded: docs"), predecessor=kwargs.pop("predecessor", None), cwd=self.repo,
            )

    def _connection(self):
        return STORE.connect()

    def test_claim_creates_work_item_and_owner(self):
        self._claim_claude()
        connection = self._connection()
        try:
            item = STORE.get_work_item(connection, "github.com/tj-agents/core:example-feature/example-item")
            self.assertEqual("active", item["status"])
            row = STORE.get_session(connection, "claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875")
            self.assertEqual("owner", row["role"])
        finally:
            connection.close()

    def test_second_owner_without_handoff_is_refused(self):
        self._claim_claude()
        with self.assertRaises(ValueError):
            self._claim_codex(role="owner")

    def test_predecessor_handoff_marks_handed_off_and_successor(self):
        self._claim_claude()
        result = self._claim_codex(role="owner", predecessor="claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875")
        self.assertEqual("claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875", result["removed"])
        connection = self._connection()
        try:
            predecessor = STORE.get_session(connection, "claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875")
            successor = STORE.get_session(connection, "codex:01a12aa7-5b58-7312-9400-ef710762147f")
        finally:
            connection.close()
        self.assertEqual("handed_off", predecessor["end_reason"])
        self.assertEqual("codex:01a12aa7-5b58-7312-9400-ef710762147f", predecessor["successor"])
        self.assertEqual("owner", successor["role"])
        self.assertEqual("claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875", successor["predecessor"])

    def test_bounded_role_does_not_conflict_with_owner(self):
        self._claim_claude()
        self._claim_codex(role="bounded: docs")
        connection = self._connection()
        try:
            rows = STORE.sessions_for_work_item(connection, "github.com/tj-agents/core:example-feature/example-item")
        finally:
            connection.close()
        self.assertEqual(2, len(rows))

    def test_status_reports_live_closed_unknown_foreign_and_stale(self):
        self._claim_claude()
        recovery = fake_recovery(liveness_result="live")
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            result = WIS.cmd_status("example-feature/example-item", cwd=self.repo)
        self.assertEqual(1, len(result["sessions"]))
        self.assertEqual("live", result["sessions"][0]["status"])

        for liveness_value in ("closed", "unknown"):
            recovery = fake_recovery(liveness_result=liveness_value)
            with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
                result = WIS.cmd_status("example-feature/example-item", cwd=self.repo)
            self.assertEqual(liveness_value, result["sessions"][0]["status"])

        connection = self._connection()
        try:
            STORE.start_session(connection, "claude", "a2bcd5c4-bf6d-4087-95e3-d7ba7f711875", self.repo, pid=1, pid_started_at=1.0)
            connection.execute(
                "UPDATE sessions SET machine = 'some-other-host' WHERE handle = ?",
                ("claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875",),
            )
            connection.commit()
        finally:
            connection.close()
        result = WIS.cmd_status("example-feature/example-item", cwd=self.repo)
        self.assertEqual("foreign", result["sessions"][0]["status"])

    def test_status_reports_live_for_a_live_session_even_on_branch_mismatch(self):
        self._claim_claude()
        self._run_git(self.repo, "checkout", "-b", "other-branch")
        recovery = fake_recovery(liveness_result="live")
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            result = WIS.cmd_status("example-feature/example-item", cwd=self.repo)
        self.assertEqual("live", result["sessions"][0]["status"])

    def test_resume_selects_single_owner_and_calls_open_session(self):
        self._claim_claude()
        recovery = fake_recovery(liveness_result="closed")
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            result = WIS.cmd_resume("example-feature/example-item", cwd=self.repo)
        self.assertEqual({"ok": True}, result)
        recovery.open_session.assert_called_once()
        args, kwargs = recovery.open_session.call_args
        self.assertEqual(("claude", "a2bcd5c4-bf6d-4087-95e3-d7ba7f711875"), args)
        self.assertIn("roots", kwargs)
        self.assertEqual({"claude"}, set(kwargs["roots"]))
        self.assertTrue(str(kwargs["roots"]["claude"]).endswith("projects"))

    def test_resume_refuses_multiple_owners_without_a_handle(self):
        self._claim_claude(role="bounded: a")
        self._claim_codex(role="bounded: b")
        recovery = fake_recovery(liveness_result="closed")
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            with self.assertRaises(ValueError):
                WIS.cmd_resume("example-feature/example-item", cwd=self.repo)
        recovery.open_session.assert_not_called()

    def test_resume_refuses_foreign(self):
        self._claim_claude()
        connection = self._connection()
        try:
            connection.execute(
                "UPDATE sessions SET machine = 'some-other-host' WHERE handle = ?",
                ("claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875",),
            )
            connection.commit()
        finally:
            connection.close()
        recovery = fake_recovery(liveness_result="closed")
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            with self.assertRaises(ValueError):
                WIS.cmd_resume("example-feature/example-item", cwd=self.repo)
        recovery.open_session.assert_not_called()

    def test_resume_refuses_live_even_with_a_branch_mismatch(self):
        self._claim_claude()
        self._run_git(self.repo, "checkout", "-b", "other-branch")
        recovery = fake_recovery(liveness_result="live")
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            with self.assertRaises(ValueError):
                WIS.cmd_resume("example-feature/example-item", cwd=self.repo)
        recovery.open_session.assert_not_called()

    def test_resume_refuses_live(self):
        self._claim_claude()
        recovery = fake_recovery(liveness_result="live")
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            with self.assertRaises(ValueError):
                WIS.cmd_resume("example-feature/example-item", cwd=self.repo)
        recovery.open_session.assert_not_called()

    def test_find_matches_worktree_to_its_claimed_work_item(self):
        self._claim_claude()
        result = WIS.cmd_find(str(self.repo))
        self.assertEqual(1, len(result["matches"]))
        self.assertEqual("example-feature/example-item", result["matches"][0]["work_item"])
        self.assertEqual("claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875", result["matches"][0]["handle"])

    def test_find_reports_no_matches_for_an_unclaimed_worktree(self):
        other = self.root / "unclaimed"
        other.mkdir()
        result = WIS.cmd_find(str(other))
        self.assertEqual([], result["matches"])

    def test_interrupted_lists_only_dead_pid_not_ended_rows_grouped_by_work_item(self):
        self._claim_claude()
        connection = self._connection()
        try:
            STORE.start_session(
                connection, "claude", "a2bcd5c4-bf6d-4087-95e3-d7ba7f711875", self.repo,
                pid=999999999, pid_started_at=1234.0,
            )
            STORE.set_session_ownership(
                connection, "claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875", "owner",
                "github.com/tj-agents/core:example-feature/example-item",
            )
        finally:
            connection.close()
        register_session = WIS._register_session()
        with mock.patch.object(register_session, "build_process_lookup", return_value=lambda pid: None):
            result = WIS.cmd_interrupted(cwd=self.repo)
        self.assertIn("example-feature/example-item", result["interrupted"])
        handles = {row["handle"] for row in result["interrupted"]["example-feature/example-item"]}
        self.assertEqual({"claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875"}, handles)

    def test_interrupted_excludes_live_pids(self):
        self._claim_claude()
        connection = self._connection()
        try:
            STORE.start_session(
                connection, "claude", "a2bcd5c4-bf6d-4087-95e3-d7ba7f711875", self.repo,
                pid=os.getpid(), pid_started_at=1234.0,
            )
        finally:
            connection.close()
        register_session = WIS._register_session()
        process = types.SimpleNamespace(started_at=1234.0)
        with mock.patch.object(register_session, "build_process_lookup", return_value=lambda pid: process):
            result = WIS.cmd_interrupted(cwd=self.repo)
        self.assertEqual({}, result["interrupted"])

    def test_interrupted_resumes_only_listed_handles(self):
        self._claim_claude()
        connection = self._connection()
        try:
            STORE.start_session(
                connection, "claude", "a2bcd5c4-bf6d-4087-95e3-d7ba7f711875", self.repo,
                pid=999999999, pid_started_at=1234.0,
            )
        finally:
            connection.close()
        register_session = WIS._register_session()
        recovery = fake_recovery()
        with mock.patch.object(register_session, "build_process_lookup", return_value=lambda pid: None), \
                mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            result = WIS.cmd_interrupted(
                resume_handles=["claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875"], cwd=self.repo,
            )
        recovery.open_session.assert_called_once()
        self.assertEqual([{"ok": True}], result["resumed"])

    def test_interrupted_resume_rejects_an_unlisted_handle(self):
        self._claim_claude()
        register_session = WIS._register_session()
        with mock.patch.object(register_session, "build_process_lookup", return_value=lambda pid: None):
            with self.assertRaises(ValueError):
                WIS.cmd_interrupted(resume_handles=["claude:not-interrupted"], cwd=self.repo)

    def test_end_records_reason_for_current_session(self):
        self._claim_claude()
        with mock.patch.dict(os.environ, {"CLAUDE_CODE_SESSION_ID": "a2bcd5c4-bf6d-4087-95e3-d7ba7f711875"}, clear=False):
            WIS.cmd_end("claude", "finished")
        connection = self._connection()
        try:
            row = STORE.get_session(connection, "claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875")
        finally:
            connection.close()
        self.assertEqual("finished", row["end_reason"])
        self.assertIsNotNone(row["ended_at"])

    def test_item_updates_status_and_pr(self):
        self._claim_claude()
        WIS.cmd_item("example-feature/example-item", "done", pr="https://github.com/tj-agents/core/pull/1", cwd=self.repo)
        connection = self._connection()
        try:
            item = STORE.get_work_item(connection, "github.com/tj-agents/core:example-feature/example-item")
        finally:
            connection.close()
        self.assertEqual("done", item["status"])
        self.assertEqual("https://github.com/tj-agents/core/pull/1", item["pr"])

    def test_invalid_work_item_grammar_is_rejected(self):
        with self.assertRaises(ValueError):
            WIS._parse_work_item("Not-Valid/Item")
        with self.assertRaises(ValueError):
            WIS._parse_work_item("missing-slash")

    def test_status_reports_foreign_before_checking_an_ended_row(self):
        self._claim_claude()
        with mock.patch.dict(os.environ, {"CLAUDE_CODE_SESSION_ID": "a2bcd5c4-bf6d-4087-95e3-d7ba7f711875"}, clear=False):
            WIS.cmd_end("claude", "finished")
        connection = self._connection()
        try:
            connection.execute(
                "UPDATE sessions SET machine = 'some-other-host' WHERE handle = ?",
                ("claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875",),
            )
            connection.commit()
        finally:
            connection.close()
        result = WIS.cmd_status("example-feature/example-item", cwd=self.repo)
        self.assertEqual("foreign", result["sessions"][0]["status"])

    def test_status_and_resume_report_a_dead_not_ended_session_with_a_stale_worktree_as_stale(self):
        self._claim_claude()
        self._run_git(self.repo, "checkout", "-b", "other-branch")
        recovery = fake_recovery(liveness_result="closed")
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            result = WIS.cmd_status("example-feature/example-item", cwd=self.repo)
        self.assertEqual("stale", result["sessions"][0]["status"])
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            with self.assertRaises(ValueError):
                WIS.cmd_resume("example-feature/example-item", cwd=self.repo)
        recovery.open_session.assert_not_called()

    def test_resume_selects_an_owner_ended_closed_without_a_handle(self):
        self._claim_claude()
        with mock.patch.dict(os.environ, {"CLAUDE_CODE_SESSION_ID": "a2bcd5c4-bf6d-4087-95e3-d7ba7f711875"}, clear=False):
            WIS.cmd_end("claude", "closed")
        recovery = fake_recovery(liveness_result="closed")
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            result = WIS.cmd_resume("example-feature/example-item", cwd=self.repo)
        self.assertEqual({"ok": True}, result)
        recovery.open_session.assert_called_once()

    def test_resume_does_not_select_a_finished_owner_without_a_handle(self):
        self._claim_claude()
        with mock.patch.dict(os.environ, {"CLAUDE_CODE_SESSION_ID": "a2bcd5c4-bf6d-4087-95e3-d7ba7f711875"}, clear=False):
            WIS.cmd_end("claude", "finished")
        recovery = fake_recovery(liveness_result="closed")
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            with self.assertRaises(ValueError):
                WIS.cmd_resume("example-feature/example-item", cwd=self.repo)
        recovery.open_session.assert_not_called()

    def test_resume_refuses_a_handed_off_predecessor_handle_while_its_successor_owns_the_item(self):
        self._claim_claude()
        self._claim_codex(role="owner", predecessor="claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875")
        recovery = fake_recovery(liveness_result="closed")
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            with self.assertRaises(ValueError):
                WIS.cmd_resume(
                    "example-feature/example-item",
                    handle="claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875",
                    cwd=self.repo,
                )
        recovery.open_session.assert_not_called()

    def test_resume_refuses_a_finished_session_handle(self):
        self._claim_claude()
        with mock.patch.dict(os.environ, {"CLAUDE_CODE_SESSION_ID": "a2bcd5c4-bf6d-4087-95e3-d7ba7f711875"}, clear=False):
            WIS.cmd_end("claude", "finished")
        recovery = fake_recovery(liveness_result="closed")
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            with self.assertRaises(ValueError):
                WIS.cmd_resume(
                    "example-feature/example-item",
                    handle="claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875",
                    cwd=self.repo,
                )
        recovery.open_session.assert_not_called()

    def test_concurrent_claims_wrap_the_live_owner_check_and_write_in_one_transaction(self):
        original_live_owners = STORE.live_owners

        def slow_live_owners(connection, key):
            result = original_live_owners(connection, key)
            time.sleep(0.3)
            return result

        results = {}
        errors = {}

        def claim(name, env_key, env_value, host):
            os.environ[env_key] = env_value
            try:
                results[name] = WIS.cmd_claim(
                    "example-feature/example-item", host, role="owner", cwd=self.repo,
                )
            except ValueError as error:
                errors[name] = error
            finally:
                os.environ.pop(env_key, None)

        with mock.patch.object(STORE, "live_owners", side_effect=slow_live_owners):
            threads = [
                threading.Thread(
                    target=claim,
                    args=("a", "CLAUDE_CODE_SESSION_ID", "a2bcd5c4-bf6d-4087-95e3-d7ba7f711875", "claude"),
                ),
                threading.Thread(
                    target=claim,
                    args=("b", "CODEX_THREAD_ID", "01a12aa7-5b58-7312-9400-ef710762147f", "codex"),
                ),
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=10)

        self.assertEqual(1, len(results))
        self.assertEqual(1, len(errors))
        connection = self._connection()
        try:
            owners = STORE.live_owners(connection, "github.com/tj-agents/core:example-feature/example-item")
        finally:
            connection.close()
        self.assertEqual(1, len(owners))

    def test_invalid_role_is_rejected_before_writing_anything(self):
        for invalid in ("Owner", "owner ", "bounded:", "bounded: ", "random"):
            with self.subTest(role=invalid):
                with self.assertRaises(ValueError):
                    self._claim_claude(role=invalid)
        connection = self._connection()
        try:
            item = STORE.get_work_item(connection, "github.com/tj-agents/core:example-feature/example-item")
        finally:
            connection.close()
        self.assertIsNone(item)

    def test_valid_bounded_role_with_a_scope_is_accepted(self):
        self._claim_claude(role="bounded: docs")
        connection = self._connection()
        try:
            row = STORE.get_session(connection, "claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875")
        finally:
            connection.close()
        self.assertEqual("bounded: docs", row["role"])

    def test_claim_on_the_default_branch_does_not_record_a_branch(self):
        self._run_git(self.repo, "branch", "-M", "main")
        self._claim_claude()
        connection = self._connection()
        try:
            item = STORE.get_work_item(connection, "github.com/tj-agents/core:example-feature/example-item")
        finally:
            connection.close()
        self.assertIsNone(item["branch"])

    def test_claim_on_a_non_default_branch_records_the_branch(self):
        self._run_git(self.repo, "checkout", "-b", "feature-branch")
        self._claim_claude()
        connection = self._connection()
        try:
            item = STORE.get_work_item(connection, "github.com/tj-agents/core:example-feature/example-item")
        finally:
            connection.close()
        self.assertEqual("feature-branch", item["branch"])

    def test_default_branch_prefers_symbolic_ref_over_the_literal_fallback(self):
        with mock.patch.object(STORE, "_git", return_value="origin/trunk"):
            self.assertEqual("trunk", WIS._default_branch(self.repo, "not-trunk"))

    def test_default_branch_falls_back_to_literal_main_or_master(self):
        with mock.patch.object(STORE, "_git", return_value=None):
            self.assertEqual("main", WIS._default_branch(self.repo, "main"))
            self.assertIsNone(WIS._default_branch(self.repo, "feature"))

    def test_close_reclaim_close_then_resume_without_handle_selects_the_latest_owner(self):
        self._claim_claude()
        with mock.patch.dict(os.environ, {"CLAUDE_CODE_SESSION_ID": "a2bcd5c4-bf6d-4087-95e3-d7ba7f711875"}, clear=False):
            WIS.cmd_end("claude", "closed")
        self._claim_codex(role="owner")
        with mock.patch.dict(os.environ, {"CODEX_THREAD_ID": "01a12aa7-5b58-7312-9400-ef710762147f"}, clear=False):
            WIS.cmd_end("codex", "closed")
        connection = self._connection()
        try:
            former_owner = STORE.get_session(connection, "claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875")
        finally:
            connection.close()
        self.assertIsNone(former_owner["role"])

        recovery = fake_recovery(liveness_result="closed")
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            result = WIS.cmd_resume("example-feature/example-item", cwd=self.repo)
        self.assertEqual({"ok": True}, result)
        recovery.open_session.assert_called_once()
        args, _kwargs = recovery.open_session.call_args
        self.assertEqual(("codex", "01a12aa7-5b58-7312-9400-ef710762147f"), args)

    def test_interrupted_listing_includes_each_rows_status(self):
        self._claim_claude()
        connection = self._connection()
        try:
            STORE.start_session(
                connection, "claude", "a2bcd5c4-bf6d-4087-95e3-d7ba7f711875", self.repo,
                pid=999999999, pid_started_at=1234.0,
            )
        finally:
            connection.close()
        register_session = WIS._register_session()
        recovery = fake_recovery(liveness_result="closed")
        with mock.patch.object(register_session, "build_process_lookup", return_value=lambda pid: None), \
                mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            result = WIS.cmd_interrupted(cwd=self.repo)
        rows = result["interrupted"]["example-feature/example-item"]
        self.assertEqual(1, len(rows))
        self.assertEqual("closed", rows[0]["status"])

    def test_interrupted_resume_refuses_a_handle_that_is_not_closed(self):
        self._claim_claude()
        connection = self._connection()
        try:
            STORE.start_session(
                connection, "claude", "a2bcd5c4-bf6d-4087-95e3-d7ba7f711875", self.repo,
                pid=999999999, pid_started_at=1234.0,
            )
        finally:
            connection.close()
        self._run_git(self.repo, "checkout", "-b", "other-branch")
        register_session = WIS._register_session()
        recovery = fake_recovery(liveness_result="closed")
        with mock.patch.object(register_session, "build_process_lookup", return_value=lambda pid: None), \
                mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            with self.assertRaises(ValueError):
                WIS.cmd_interrupted(resume_handles=["claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875"], cwd=self.repo)
            recovery.open_session.assert_not_called()

    def test_item_on_the_default_branch_does_not_record_a_branch(self):
        self._run_git(self.repo, "branch", "-M", "main")
        WIS.cmd_item("example-feature/example-item", "active", cwd=self.repo)
        connection = self._connection()
        try:
            item = STORE.get_work_item(connection, "github.com/tj-agents/core:example-feature/example-item")
        finally:
            connection.close()
        self.assertIsNone(item["branch"])

    def test_claim_fills_a_null_branch_when_claimed_again_from_a_feature_branch(self):
        self._run_git(self.repo, "branch", "-M", "main")
        self._claim_claude()
        connection = self._connection()
        try:
            item = STORE.get_work_item(connection, "github.com/tj-agents/core:example-feature/example-item")
        finally:
            connection.close()
        self.assertIsNone(item["branch"])

        self._run_git(self.repo, "checkout", "-b", "feature-branch")
        self._claim_claude()
        connection = self._connection()
        try:
            item = STORE.get_work_item(connection, "github.com/tj-agents/core:example-feature/example-item")
        finally:
            connection.close()
        self.assertEqual("feature-branch", item["branch"])

    def test_claim_bounded_role_does_not_fill_a_null_branch(self):
        self._run_git(self.repo, "branch", "-M", "main")
        self._claim_claude()
        self._run_git(self.repo, "checkout", "-b", "feature-branch")
        self._claim_codex(role="bounded: docs")
        connection = self._connection()
        try:
            item = STORE.get_work_item(connection, "github.com/tj-agents/core:example-feature/example-item")
        finally:
            connection.close()
        self.assertIsNone(item["branch"])

    def test_ambiguous_tag_and_branch_name_does_not_make_the_row_stale(self):
        self._run_git(self.repo, "checkout", "-b", "shared-name")
        self._run_git(self.repo, "tag", "shared-name")
        self._claim_claude()
        recovery = fake_recovery(liveness_result="closed")
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            result = WIS.cmd_status("example-feature/example-item", cwd=self.repo)
        self.assertEqual("closed", result["sessions"][0]["status"])

    def test_item_status_fills_a_null_branch_from_a_non_default_branch(self):
        self._run_git(self.repo, "branch", "-M", "main")
        WIS.cmd_item("example-feature/example-item", "active", cwd=self.repo)
        connection = self._connection()
        try:
            item = STORE.get_work_item(connection, "github.com/tj-agents/core:example-feature/example-item")
        finally:
            connection.close()
        self.assertIsNone(item["branch"])

        self._run_git(self.repo, "checkout", "-b", "feature-branch")
        WIS.cmd_item("example-feature/example-item", "active", cwd=self.repo)
        connection = self._connection()
        try:
            item = STORE.get_work_item(connection, "github.com/tj-agents/core:example-feature/example-item")
        finally:
            connection.close()
        self.assertEqual("feature-branch", item["branch"])

    def test_interrupted_computes_each_rows_status_once_even_when_resuming(self):
        self._claim_claude()
        connection = self._connection()
        try:
            STORE.start_session(
                connection, "claude", "a2bcd5c4-bf6d-4087-95e3-d7ba7f711875", self.repo,
                pid=999999999, pid_started_at=1234.0,
            )
        finally:
            connection.close()
        register_session = WIS._register_session()
        recovery = fake_recovery(liveness_result="closed")
        original_status = WIS._read_time_status
        calls = []

        def counting_status(row, machine):
            calls.append(row["handle"])
            return original_status(row, machine)

        with mock.patch.object(register_session, "build_process_lookup", return_value=lambda pid: None), \
                mock.patch.object(WIS, "_agent_recovery", return_value=recovery), \
                mock.patch.object(WIS, "_read_time_status", side_effect=counting_status):
            WIS.cmd_interrupted(
                resume_handles=["claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875"], cwd=self.repo,
            )
        self.assertEqual(1, calls.count("claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875"))

    def test_resume_all_uses_machine_wide_rows_outside_git_and_reports_deterministic_skips(self):
        outside = self.root / "outside git"
        outside.mkdir()
        connection = self._connection()
        try:
            for session_id in ("a-ended", "b-foreign", "c-done", "d-live", "e-unknown", "f-stale", "g-eligible"):
                cwd = outside if session_id != "f-stale" else self.root / "missing"
                pid = 999999998 if session_id == "d-live" else 999999999
                STORE.start_session(connection, "claude", session_id, cwd, pid=pid, pid_started_at=1234.0)
            STORE.end_session(connection, "claude:a-ended", "closed")
            connection.execute("UPDATE sessions SET machine = 'other-machine' WHERE handle = 'claude:b-foreign'")
            STORE.upsert_work_item(connection, "done-key", "repo", "feature", "done", status="done")
            STORE.set_session_ownership(connection, "claude:c-done", "owner", "done-key")
            connection.commit()
        finally:
            connection.close()
        recovery = fake_recovery(liveness_result=lambda item: "unknown" if item["session"] == "e-unknown" else "closed")
        recovery.liveness.side_effect = recovery.liveness.return_value
        process = types.SimpleNamespace(started_at=1234.0)
        register_session = WIS._register_session()
        with mock.patch.object(register_session, "build_process_lookup", return_value=lambda pid: process if pid == 999999998 else None), \
                mock.patch.object(WIS, "_agent_recovery", return_value=recovery), \
                mock.patch.object(WIS, "_wait_for_fresh_registration", return_value={"handle": "claude:g-eligible"}):
            result = WIS.cmd_interrupted(resume_all=True, all_repos=True, cwd=outside)
        self.assertEqual(
            ["claude:a-ended", "claude:b-foreign", "claude:c-done", "claude:d-live", "claude:e-unknown", "claude:f-stale", "claude:g-eligible"],
            [entry["handle"] for entry in result["bulk"]],
        )
        self.assertEqual(
            ["ended", "foreign", "done", "unknown", "stale", "resumed"],
            [entry.get("reason", entry["outcome"]) for entry in result["bulk"] if entry["handle"] != "claude:d-live"],
        )
        self.assertEqual("live", result["bulk"][3]["reason"])
        self.assertEqual("resumed", result["bulk"][-1]["outcome"])
        recovery.open_session.assert_called_once_with(
            "claude", "g-eligible", prompt="Continue the requested work.", roots=mock.ANY,
            refresh_plugins=False,
        )

    def test_resume_all_continues_after_a_launch_failure_and_marks_unverified_launch_pending(self):
        outside = self.root / "outside git"
        outside.mkdir()
        connection = self._connection()
        try:
            for session_id in ("a-fails", "b-pending", "c-succeeds"):
                STORE.start_session(connection, "codex", session_id, outside, pid=999999999, pid_started_at=1234.0)
        finally:
            connection.close()
        recovery = fake_recovery(liveness_result="closed")
        recovery.open_session.side_effect = [RuntimeError("launch failed"), {"id": "b-pending"}, {"id": "c-succeeds"}]
        register_session = WIS._register_session()
        with mock.patch.object(register_session, "build_process_lookup", return_value=lambda _pid: None), \
                mock.patch.object(WIS, "_agent_recovery", return_value=recovery), \
                mock.patch.object(WIS, "_wait_for_fresh_registration", side_effect=[None, {"handle": "codex:c-succeeds"}]):
            result = WIS.cmd_interrupted(resume_all=True, all_repos=True, cwd=outside)
        self.assertEqual(["failed", "pending", "resumed"], [entry["outcome"] for entry in result["bulk"]])
        self.assertTrue(result["bulk_failed"])
        self.assertEqual(3, recovery.open_session.call_count)

    def test_resume_all_continues_after_a_registration_verification_failure(self):
        outside = self.root / "outside git"
        outside.mkdir()
        connection = self._connection()
        try:
            for session_id in ("a-verification", "b-next"):
                STORE.start_session(connection, "codex", session_id, outside, pid=999999999, pid_started_at=1234.0)
        finally:
            connection.close()
        recovery = fake_recovery(liveness_result="closed")
        register_session = WIS._register_session()
        with mock.patch.object(register_session, "build_process_lookup", return_value=lambda _pid: None), \
                mock.patch.object(WIS, "_agent_recovery", return_value=recovery), \
                mock.patch.object(WIS, "_wait_for_fresh_registration", side_effect=[OSError("database busy"), {"handle": "codex:b-next"}]):
            result = WIS.cmd_interrupted(resume_all=True, all_repos=True, cwd=outside)
        self.assertEqual(["pending", "resumed"], [entry["outcome"] for entry in result["bulk"]])
        self.assertTrue(result["bulk_failed"])
        self.assertEqual(2, recovery.open_session.call_count)

    def test_wait_for_fresh_registration_requires_refreshed_started_at_and_live_identity(self):
        connection = self._connection()
        try:
            STORE.start_session(connection, "claude", "fresh", self.repo, pid=11, pid_started_at=20.0)
            connection.execute("UPDATE sessions SET started_at = 30.0 WHERE handle = 'claude:fresh'")
            connection.commit()
        finally:
            connection.close()
        register_session = WIS._register_session()
        process = types.SimpleNamespace(started_at=20.0)
        with mock.patch.object(register_session, "build_process_lookup", return_value=lambda _pid: process):
            self.assertIsNone(WIS._wait_for_fresh_registration("claude:fresh", 30.0, timeout=0, wait=mock.Mock()))
            self.assertIsNotNone(WIS._wait_for_fresh_registration("claude:fresh", 29.0, timeout=0, wait=mock.Mock()))

    def test_claim_resolves_repo_branch_and_head_once(self):
        original = STORE._collect_repo_branch_head
        calls = []

        def counting(cwd, timeout=STORE.HOOK_GIT_TIMEOUT):
            calls.append(cwd)
            return original(cwd, timeout=timeout)

        with mock.patch.object(STORE, "_collect_repo_branch_head", side_effect=counting):
            self._claim_claude()
        self.assertEqual(2, len(calls))


if __name__ == "__main__":
    unittest.main()
