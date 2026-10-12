import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
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
            item = STORE.get_work_item(connection, "tj-agents/core:example-feature/example-item")
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
            rows = STORE.sessions_for_work_item(connection, "tj-agents/core:example-feature/example-item")
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

    def test_status_reports_stale_on_branch_mismatch(self):
        self._claim_claude()
        self._run_git(self.repo, "checkout", "-b", "other-branch")
        recovery = fake_recovery(liveness_result="live")
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            result = WIS.cmd_status("example-feature/example-item", cwd=self.repo)
        self.assertEqual("stale", result["sessions"][0]["status"])

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

    def test_resume_refuses_stale(self):
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
                "tj-agents/core:example-feature/example-item",
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
            item = STORE.get_work_item(connection, "tj-agents/core:example-feature/example-item")
        finally:
            connection.close()
        self.assertEqual("done", item["status"])
        self.assertEqual("https://github.com/tj-agents/core/pull/1", item["pr"])

    def test_invalid_work_item_grammar_is_rejected(self):
        with self.assertRaises(ValueError):
            WIS._parse_work_item("Not-Valid/Item")
        with self.assertRaises(ValueError):
            WIS._parse_work_item("missing-slash")


if __name__ == "__main__":
    unittest.main()
