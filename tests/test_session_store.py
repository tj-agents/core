import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "session_store", ROOT / ".agents/machine/scripts/session_store.py"
)
STORE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STORE)

GIT = shutil.which("git")


def _run_git(cwd, *args):
    result = subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=15,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()


def _init_repo(path, origin=None):
    path.mkdir(parents=True, exist_ok=True)
    _run_git(path, "init")
    _run_git(path, "config", "user.email", "test@example.com")
    _run_git(path, "config", "user.name", "Test User")
    (path / "README.md").write_text("hello\n", encoding="utf-8")
    _run_git(path, "add", "README.md")
    _run_git(path, "commit", "-m", "initial")
    if origin:
        _run_git(path, "remote", "add", "origin", origin)
    return path


class SchemaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="session store é ")
        self.addCleanup(self.temp.cleanup)
        self.db_path = Path(self.temp.name) / "state" / "sessions.db"

    def test_schema_created_with_expected_tables_and_user_version(self):
        connection = STORE.connect(self.db_path)
        self.addCleanup(connection.close)
        tables = {
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        self.assertEqual({"sessions", "work_items"}, tables)
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        self.assertEqual(1, version)

    def test_reconnecting_does_not_lose_the_schema_version(self):
        STORE.connect(self.db_path).close()
        connection = STORE.connect(self.db_path)
        self.addCleanup(connection.close)
        self.assertEqual(1, connection.execute("PRAGMA user_version").fetchone()[0])

    def test_connect_enables_wal_and_foreign_keys(self):
        connection = STORE.connect(self.db_path)
        self.addCleanup(connection.close)
        self.assertEqual("wal", connection.execute("PRAGMA journal_mode").fetchone()[0].lower())
        self.assertEqual(1, connection.execute("PRAGMA foreign_keys").fetchone()[0])


@unittest.skipUnless(GIT, "git is required for repo-identity and hook lifecycle tests")
class RepoIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="session store repo é ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_https_remote_normalises_to_owner_name(self):
        repo = _init_repo(self.root / "https-repo", origin="https://github.com/tj-agents/core.git")
        self.assertEqual("tj-agents/core", STORE.repo_identity(repo))

    def test_ssh_scp_remote_normalises_to_owner_name(self):
        repo = _init_repo(self.root / "ssh-repo", origin="git@github.com:tj-agents/core.git")
        self.assertEqual("tj-agents/core", STORE.repo_identity(repo))

    def test_ssh_url_remote_normalises_to_owner_name(self):
        repo = _init_repo(self.root / "ssh-url-repo", origin="ssh://git@github.com/tj-agents/core.git")
        self.assertEqual("tj-agents/core", STORE.repo_identity(repo))

    def test_no_remote_falls_back_to_absolute_git_common_dir(self):
        repo = _init_repo(self.root / "no-remote-repo")
        identity = STORE.repo_identity(repo)
        self.assertEqual(str((repo / ".git").resolve()), identity)

    def test_non_git_directory_returns_none(self):
        directory = self.root / "not-a-repo"
        directory.mkdir()
        self.assertIsNone(STORE.repo_identity(directory))


@unittest.skipUnless(GIT, "git is required for hook lifecycle tests")
class HookLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="session store hooks é ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / "state"
        self.environ = mock.patch.dict(os.environ, {"AGENT_STATE_DIRECTORY": str(self.state)}, clear=False)
        self.environ.start()
        self.addCleanup(self.environ.stop)
        self.repo = _init_repo(self.root / "repo with spaces", origin="https://github.com/tj-agents/core.git")

    def _invoke(self, event, host, payload):
        with mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))):
            return STORE.main(["hook", event, "--host", host])

    def _row(self, handle):
        connection = STORE.connect()
        try:
            return STORE.get_session(connection, handle)
        finally:
            connection.close()

    def test_start_prompt_stop_session_end_lifecycle(self):
        payload = {"session_id": "a2bcd5c4-bf6d-4087-95e3-d7ba7f711875", "cwd": str(self.repo)}
        self.assertEqual(0, self._invoke("session-start", "claude", payload))
        handle = "claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875"
        row = self._row(handle)
        self.assertEqual("working", row["turn_state"])
        self.assertIsNone(row["ended_at"])

        self.assertEqual(0, self._invoke("prompt", "claude", payload))
        self.assertEqual("working", self._row(handle)["turn_state"])

        self.assertEqual(0, self._invoke("stop", "claude", payload))
        row = self._row(handle)
        self.assertEqual("awaiting_input", row["turn_state"])
        self.assertEqual("tj-agents/core", row["repo"])

        self.assertEqual(0, self._invoke("session-end", "claude", payload))
        row = self._row(handle)
        self.assertIsNotNone(row["ended_at"])
        self.assertEqual("closed", row["end_reason"])

    def test_resume_start_clears_ended_at_and_end_reason(self):
        payload = {"session_id": "exact-id", "cwd": str(self.repo)}
        handle = "codex:exact-id"
        self._invoke("session-start", "codex", payload)
        self._invoke("session-end", "codex", payload)
        self.assertIsNotNone(self._row(handle)["ended_at"])

        self._invoke("session-start", "codex", payload)
        row = self._row(handle)
        self.assertIsNone(row["ended_at"])
        self.assertIsNone(row["end_reason"])
        self.assertEqual("working", row["turn_state"])

    def test_first_end_reason_wins(self):
        connection = STORE.connect()
        try:
            STORE.start_session(connection, "claude", "id-1", self.repo)
            STORE.end_session(connection, "claude:id-1", "finished")
            STORE.end_session(connection, "claude:id-1", "closed")
            row = STORE.get_session(connection, "claude:id-1")
        finally:
            connection.close()
        self.assertEqual("finished", row["end_reason"])

    def test_session_start_hook_malformed_stdin_exits_zero(self):
        with mock.patch.object(sys, "stdin", io.StringIO("not json {{{")):
            self.assertEqual(0, STORE.main(["hook", "session-start", "--host", "claude"]))

    def test_session_start_hook_unwritable_db_path_exits_zero(self):
        blocker = self.root / "blocker-file"
        blocker.write_text("not a directory", encoding="utf-8")
        with mock.patch.dict(os.environ, {"AGENT_STATE_DIRECTORY": str(blocker / "nested")}, clear=False):
            payload = {"session_id": "id", "cwd": str(self.repo)}
            with mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))):
                self.assertEqual(0, STORE.main(["hook", "session-start", "--host", "claude"]))

    def test_work_item_auto_attach_requires_exactly_one_match(self):
        connection = STORE.connect()
        try:
            repo = "tj-agents/core"
            STORE.upsert_work_item(connection, "tj-agents/core:f/a", repo, "f", "a", status="active", branch="topic")
            STORE.start_session(connection, "claude", "attach-id", self.repo)
            STORE.record_stop(connection, "claude:attach-id", self.repo)
        finally:
            connection.close()

        _run_git(self.repo, "checkout", "-b", "topic")
        connection = STORE.connect()
        try:
            STORE.record_stop(connection, "claude:attach-id", self.repo)
            row = STORE.get_session(connection, "claude:attach-id")
            self.assertEqual("tj-agents/core:f/a", row["work_item"])
        finally:
            connection.close()

        connection = STORE.connect()
        try:
            STORE.upsert_work_item(connection, "tj-agents/core:f/b", "tj-agents/core", "f", "b", status="active", branch="topic")
            STORE.start_session(connection, "claude", "attach-id-2", self.repo)
            STORE.record_stop(connection, "claude:attach-id-2", self.repo)
            row = STORE.get_session(connection, "claude:attach-id-2")
            self.assertIsNone(row["work_item"])
        finally:
            connection.close()

    def test_concurrent_writers_from_threads_keep_every_row(self):
        STORE.connect().close()
        errors = []

        def write(index):
            try:
                connection = STORE.connect()
                try:
                    STORE.start_session(connection, "claude", f"thread-{index}", self.repo)
                finally:
                    connection.close()
            except Exception as error:  # noqa: BLE001 - collected for the assertion below
                errors.append(error)

        threads = [threading.Thread(target=write, args=(index,)) for index in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual([], errors)
        connection = STORE.connect()
        try:
            handles = {row["handle"] for row in connection.execute("SELECT handle FROM sessions").fetchall()}
        finally:
            connection.close()
        self.assertEqual({f"claude:thread-{index}" for index in range(8)}, handles)


if __name__ == "__main__":
    unittest.main()
