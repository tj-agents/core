import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "work_item_sessions", ROOT / ".agents/machine/scripts/work_item_sessions.py"
)
WIS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WIS)

REAL_RECOVERY = WIS._agent_recovery()
GIT = shutil.which("git")


def fake_recovery(liveness_result="live", open_session=None):
    return types.SimpleNamespace(
        SESSION_ID=REAL_RECOVERY.SESSION_ID,
        liveness=mock.Mock(return_value=liveness_result),
        open_session=open_session if open_session is not None else mock.Mock(return_value={"ok": True}),
    )


def valid_fields(role="owner", host="codex", session_id="01a12aa7-5b58-7312-9400-ef710762147f", **overrides):
    worktree = r"C:\abs\worktree" if os.name == "nt" else "/abs/worktree"
    fields = {
        "Role": role,
        "State": "active",
        "Machine": "test-machine",
        "Profile": "default",
        "Title": "none",
        "Worktree": worktree,
        "Branch": "main",
        "PR": "not opened",
        "Head": "a" * 40,
        "Predecessor": "none",
        "Successor": "none",
        "Verified": "2026-10-12T19:30:00Z",
        "Resume": WIS._resume_command(host, session_id),
    }
    fields.update(overrides)
    return fields


class ParseRenderValidateTests(unittest.TestCase):
    def test_round_trip(self):
        records = [
            ("codex:01a12aa7-5b58-7312-9400-ef710762147f", valid_fields()),
            ("claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875", valid_fields(
                role="bounded: docs", host="claude", session_id="a2bcd5c4-bf6d-4087-95e3-d7ba7f711875",
            )),
        ]
        self.assertEqual([], WIS.validate(records))
        text = WIS.render(records)
        parsed, errors = WIS.parse(text)
        self.assertEqual([], errors)
        self.assertEqual(records, parsed)

    def test_absent_file_is_valid_with_zero_sessions(self):
        with tempfile.TemporaryDirectory(prefix="work item é ") as raw:
            result = WIS.cmd_validate(Path(raw))
        self.assertEqual({"valid": True, "errors": [], "sessions": []}, result)

    def test_bad_handle_is_rejected(self):
        records = [("not-a-handle", valid_fields())]
        errors = WIS.validate(records)
        self.assertTrue(any("invalid session handle" in error for error in errors))

    def test_duplicate_handle_is_rejected(self):
        handle = "codex:01a12aa7-5b58-7312-9400-ef710762147f"
        records = [(handle, valid_fields()), (handle, valid_fields())]
        errors = WIS.validate(records)
        self.assertTrue(any("duplicate session handle" in error for error in errors))

    def test_missing_field_is_rejected(self):
        fields = valid_fields()
        del fields["Head"]
        errors = WIS.validate([("codex:01a12aa7-5b58-7312-9400-ef710762147f", fields)])
        self.assertTrue(any("missing field 'Head'" in error for error in errors))

    def test_unknown_field_is_rejected(self):
        fields = valid_fields()
        fields["Bogus"] = "value"
        errors = WIS.validate([("codex:01a12aa7-5b58-7312-9400-ef710762147f", fields)])
        self.assertTrue(any("unknown field 'Bogus'" in error for error in errors))

    def test_two_owners_is_rejected(self):
        records = [
            ("codex:01a12aa7-5b58-7312-9400-ef710762147f", valid_fields(role="owner")),
            ("claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875", valid_fields(
                role="owner", host="claude", session_id="a2bcd5c4-bf6d-4087-95e3-d7ba7f711875",
            )),
        ]
        errors = WIS.validate(records)
        self.assertTrue(any("multiple owner rows" in error for error in errors))

    def test_bad_state_is_rejected(self):
        fields = valid_fields(State="paused")
        errors = WIS.validate([("codex:01a12aa7-5b58-7312-9400-ef710762147f", fields)])
        self.assertTrue(any("invalid State" in error for error in errors))

    def test_bad_head_is_rejected(self):
        fields = valid_fields(Head="not-hex")
        errors = WIS.validate([("codex:01a12aa7-5b58-7312-9400-ef710762147f", fields)])
        self.assertTrue(any("invalid Head" in error for error in errors))

    def test_bad_resume_is_rejected(self):
        fields = valid_fields(Resume="machine:open-codex --id 01a12aa7-5b58-7312-9400-ef710762147f")
        errors = WIS.validate([("codex:01a12aa7-5b58-7312-9400-ef710762147f", fields)])
        self.assertTrue(any("invalid Resume" in error for error in errors))

    def test_empty_field_is_rejected(self):
        fields = valid_fields(Branch="")
        errors = WIS.validate([("codex:01a12aa7-5b58-7312-9400-ef710762147f", fields)])
        self.assertTrue(any("empty field 'Branch'" in error for error in errors))


@unittest.skipUnless(GIT, "git is required for record/status/resume tests")
class RecordStatusResumeTests(unittest.TestCase):
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
        self.work_item = self.root / "work-items" / "example"
        self.work_item.mkdir(parents=True)

    def _run_git(self, cwd, *args):
        result = subprocess.run(
            ["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        return result.stdout.strip()

    def _record_claude(self, session_id="a2bcd5c4-bf6d-4087-95e3-d7ba7f711875", **kwargs):
        with mock.patch.dict(os.environ, {
            "CLAUDE_CODE_SESSION_ID": session_id,
            "CLAUDE_CONFIG_DIR": str(self.root / "claude-profile"),
        }, clear=False):
            return WIS.record(self.work_item, "claude", kwargs.pop("role", "owner"), cwd=self.repo, **kwargs)

    def _record_codex(self, session_id="01a12aa7-5b58-7312-9400-ef710762147f", **kwargs):
        with mock.patch.dict(os.environ, {
            "CODEX_THREAD_ID": session_id,
            "CODEX_HOME": str(self.root / "codex-profile"),
        }, clear=False):
            return WIS.record(self.work_item, "codex", kwargs.pop("role", "bounded: docs"), cwd=self.repo, **kwargs)

    def test_record_claude_owner_and_codex_bounded_validate(self):
        self._record_claude()
        self._record_codex()
        records = WIS.load(self.work_item)
        handles = {handle for handle, _ in records}
        self.assertEqual(
            {"claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875", "codex:01a12aa7-5b58-7312-9400-ef710762147f"},
            handles,
        )
        self.assertEqual([], WIS.validate(records))

    def test_owner_conflict_without_handoff_raises(self):
        self._record_claude()
        with self.assertRaises(ValueError):
            self._record_codex(role="owner")

    def test_handoff_removes_predecessor_on_successor_record(self):
        self._record_claude()
        self._record_claude(state="handing-off")
        result = self._record_codex(role="owner", predecessor="claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875")
        self.assertEqual("claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875", result["removed"])
        records = WIS.load(self.work_item)
        self.assertEqual({"codex:01a12aa7-5b58-7312-9400-ef710762147f"}, {handle for handle, _ in records})

    def test_remove_last_row_deletes_file(self):
        self._record_claude()
        path = WIS.sessions_path(self.work_item)
        self.assertTrue(path.is_file())
        WIS.remove(self.work_item, handle="claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875")
        self.assertFalse(path.is_file())

    def test_status_reports_foreign_machine(self):
        self._record_claude()
        records = WIS.load(self.work_item)
        modified = [(handle, {**fields, "Machine": "some-other-host"}) for handle, fields in records]
        WIS.write(self.work_item, modified)
        with mock.patch.object(WIS, "_agent_recovery", return_value=fake_recovery()):
            result = WIS.cmd_status(self.work_item)
        self.assertEqual(1, len(result["sessions"]))
        row = result["sessions"][0]
        self.assertEqual("foreign", row["liveness"])
        self.assertEqual([], row["stale"])

    def _commit(self, name):
        (self.repo / name).write_text(name + "\n", encoding="utf-8")
        self._run_git(self.repo, "add", name)
        self._run_git(self.repo, "commit", "-m", name)

    def _diverge(self):
        self._commit("recorded.txt")
        self._record_claude()
        self._run_git(self.repo, "reset", "--hard", "HEAD~1")
        self._commit("other.txt")

    def test_later_commits_on_the_branch_keep_the_row_current(self):
        self._record_claude()
        self._commit("more.txt")
        recovery = fake_recovery(liveness_result="closed")
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            result = WIS.cmd_status(self.work_item)
        self.assertEqual([], result["sessions"][0]["stale"])

    def test_status_reports_diverged_head_as_stale(self):
        self._diverge()
        recovery = fake_recovery(liveness_result="closed")
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            result = WIS.cmd_status(self.work_item)
        row = result["sessions"][0]
        self.assertIn("head-diverged", row["stale"])
        self.assertEqual("closed", row["liveness"])
        recovery.liveness.assert_called_once()

    def test_record_refuses_detached_head(self):
        self._run_git(self.repo, "checkout", "--detach")
        with self.assertRaises(ValueError):
            self._record_claude()
        self.assertFalse(WIS.sessions_path(self.work_item).is_file())

    def test_concurrent_records_keep_every_row(self):
        session_ids = [f"bounded-{index}" for index in range(6)]
        head = self._run_git(self.repo, "rev-parse", "HEAD")
        errors = []

        def record(session_id):
            try:
                WIS._record_locked(self.work_item, "claude", session_id, f"bounded: {session_id}", None, None,
                                   None, None, None, str(self.repo), "main", head)
            except Exception as error:
                errors.append(error)

        original = WIS._record_locked

        def locked(*args):
            with WIS._registry_lock(self.work_item):
                return original(*args)

        with mock.patch.object(WIS, "_record_locked", side_effect=locked):
            threads = [threading.Thread(target=record, args=(session_id,)) for session_id in session_ids]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
        self.assertEqual([], errors)
        self.assertEqual({f"claude:{session_id}" for session_id in session_ids},
                         {handle for handle, _ in WIS.load(self.work_item)})

    def test_status_never_calls_open_session(self):
        self._record_claude()
        records = WIS.load(self.work_item)
        foreign = [(handle, {**fields, "Machine": "some-other-host"}) for handle, fields in records]
        WIS.write(self.work_item, foreign)
        self._record_codex(role="bounded: docs")
        (self.repo / "more.txt").write_text("more\n", encoding="utf-8")
        self._run_git(self.repo, "add", "more.txt")
        self._run_git(self.repo, "commit", "-m", "second")
        recovery = fake_recovery(liveness_result="unknown")
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            WIS.cmd_status(self.work_item)
        recovery.open_session.assert_not_called()

    def test_resume_selects_single_owner_and_calls_open_session(self):
        self._record_claude()
        recovery = fake_recovery()
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            result = WIS.resume(self.work_item)
        self.assertEqual({"ok": True}, result)
        recovery.open_session.assert_called_once()
        args, kwargs = recovery.open_session.call_args
        self.assertEqual(("claude", "a2bcd5c4-bf6d-4087-95e3-d7ba7f711875"), args)
        self.assertIn("roots", kwargs)
        self.assertEqual({"claude"}, set(kwargs["roots"]))
        self.assertTrue(str(kwargs["roots"]["claude"]).endswith("projects"))

    def test_resume_with_multiple_rows_and_no_handle_errors(self):
        self._record_claude(role="bounded: a")
        self._record_codex(role="bounded: b")
        recovery = fake_recovery()
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            with self.assertRaises(ValueError):
                WIS.resume(self.work_item)
        recovery.open_session.assert_not_called()

    def test_resume_refuses_stale(self):
        self._diverge()
        recovery = fake_recovery()
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            with self.assertRaises(ValueError):
                WIS.resume(self.work_item)
        recovery.open_session.assert_not_called()

    def test_resume_refuses_foreign(self):
        self._record_claude()
        records = WIS.load(self.work_item)
        foreign = [(handle, {**fields, "Machine": "some-other-host"}) for handle, fields in records]
        WIS.write(self.work_item, foreign)
        recovery = fake_recovery()
        with mock.patch.object(WIS, "_agent_recovery", return_value=recovery):
            with self.assertRaises(ValueError):
                WIS.resume(self.work_item)
        recovery.open_session.assert_not_called()

    def test_find_matches_worktree_across_roots(self):
        self._record_claude()
        other_root = self.root / "other-root"
        other_item = other_root / "plans/features/other/work-items/thing"
        other_item.mkdir(parents=True)
        WIS.write(other_item, [("codex:01a12aa7-5b58-7312-9400-ef710762147f", valid_fields(
            Worktree=str(self.repo.resolve()),
        ))])
        feature_root = self.root / "feature-root"
        feature_item = feature_root / "plans/features/example-feature/work-items/example"
        feature_item.mkdir(parents=True)
        WIS.write(feature_item, WIS.load(self.work_item))

        result = WIS.cmd_find(str(self.repo), [str(other_root), str(feature_root)])
        matches = result["matches"]
        self.assertEqual(2, len(matches))
        work_items = {match["work_item"] for match in matches}
        self.assertEqual({"other/thing", "example-feature/example"}, work_items)
        self.assertEqual([], result["invalid"])

    def test_find_reports_invalid_registry_instead_of_hiding_it(self):
        broken_item = self.root / "broken-root/plans/features/broken/work-items/item"
        broken_item.mkdir(parents=True)
        WIS.sessions_path(broken_item).write_text("# Active sessions\n\n## not-a-handle\n", encoding="utf-8")
        result = WIS.cmd_find(str(self.repo), [str(self.root / "broken-root")])
        self.assertEqual([], result["matches"])
        self.assertEqual(1, len(result["invalid"]))
        self.assertTrue(result["invalid"][0]["errors"])

    def test_unverifiable_git_state_is_stale(self):
        self._record_claude()
        records = WIS.load(self.work_item)
        with mock.patch.object(WIS, "_git", return_value=None):
            self.assertEqual(["branch-unknown", "head-unknown"], WIS.stale_reasons(records[0][1]))


if __name__ == "__main__":
    unittest.main()
