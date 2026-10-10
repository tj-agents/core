import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents" / "machine" / "utility" / "peer-cli" / "scripts" / "register_session.py"


def load_module():
    spec = importlib.util.spec_from_file_location("register_session", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


register_session = load_module()
ProcessInfo = register_session.ProcessInfo


class ResolveRecordedPidTests(unittest.TestCase):
    def test_nearest_host_ancestor_wins(self):
        table = {
            101: ProcessInfo(pid=101, ppid=102, name="bash", started_at=1000.0),
            102: ProcessInfo(pid=102, ppid=103, name="codex", started_at=2000.0),
            103: ProcessInfo(pid=103, ppid=104, name="codex.exe", started_at=3000.0),
            104: ProcessInfo(pid=104, ppid=None, name="explorer", started_at=4000.0),
        }
        pid, host, started = register_session.resolve_recorded_pid(
            101, lookup=table.get, host_names={"codex"},
        )
        self.assertEqual(pid, 102)
        self.assertEqual(host, "codex")
        self.assertEqual(started, 2000.0)

    def test_no_match_falls_back_to_ppid(self):
        table = {
            201: ProcessInfo(pid=201, ppid=202, name="bash", started_at=10.0),
            202: ProcessInfo(pid=202, ppid=203, name="bash", started_at=20.0),
        }
        pid, host, started = register_session.resolve_recorded_pid(
            201, lookup=table.get, host_names={"claude", "codex"},
        )
        self.assertEqual(pid, 201)
        self.assertIsNone(host)
        self.assertEqual(started, 10.0)

    def test_cyclic_table_falls_back(self):
        table = {
            301: ProcessInfo(pid=301, ppid=302, name="bash", started_at=5.0),
            302: ProcessInfo(pid=302, ppid=301, name="bash", started_at=6.0),
        }
        pid, host, started = register_session.resolve_recorded_pid(
            301, lookup=table.get, host_names={"codex"},
        )
        self.assertEqual(pid, 301)
        self.assertIsNone(host)
        self.assertEqual(started, 5.0)

    def test_garbage_table_falls_back(self):
        def garbage_lookup(_pid):
            raise ValueError("garbage table")

        pid, host, started = register_session.resolve_recorded_pid(
            401, lookup=garbage_lookup, host_names={"codex"},
        )
        self.assertEqual(pid, 401)
        self.assertIsNone(host)
        self.assertIsNone(started)

    def test_depth_cap_without_match_falls_back(self):
        table = {}
        for pid in range(501, 516):
            table[pid] = ProcessInfo(pid=pid, ppid=pid + 1, name="bash", started_at=float(pid))
        pid, host, started = register_session.resolve_recorded_pid(
            501, lookup=table.get, host_names={"codex"}, depth_cap=10,
        )
        self.assertEqual(pid, 501)
        self.assertIsNone(host)
        self.assertEqual(started, 501.0)

    def test_host_names_env_override(self):
        os.environ["AGENT_CLI_HOST_NAMES"] = "my-host"
        try:
            self.assertEqual(register_session.read_host_names(), frozenset({"my-host"}))
        finally:
            del os.environ["AGENT_CLI_HOST_NAMES"]


class RecordTests(unittest.TestCase):
    def test_record_writes_resolved_pid_and_host(self):
        table = {
            10: ProcessInfo(pid=10, ppid=11, name="cmd.exe", started_at=42.5),
            11: ProcessInfo(pid=11, ppid=12, name="codex.exe", started_at=99.75),
        }
        original_getppid = os.getppid
        os.getppid = lambda: 10
        with tempfile.TemporaryDirectory() as tmp:
            original_env = os.environ.get(register_session.STATE_DIRECTORY_ENV)
            os.environ[register_session.STATE_DIRECTORY_ENV] = tmp
            try:
                entry = register_session.record(
                    {"session_id": "test-session", "cwd": "C:/somewhere"},
                    lookup=table.get,
                    host_names={"codex"},
                )
            finally:
                os.getppid = original_getppid
                if original_env is None:
                    del os.environ[register_session.STATE_DIRECTORY_ENV]
                else:
                    os.environ[register_session.STATE_DIRECTORY_ENV] = original_env

            self.assertEqual(entry["pid"], 11)
            self.assertEqual(entry["host"], "codex")
            self.assertEqual(entry["pid_started_at"], 99.75)

            written = json.loads(
                (Path(tmp) / "cli-sessions" / "test-session.json").read_text(encoding="utf-8")
            )
            self.assertEqual(written["pid"], 11)
            self.assertEqual(written["host"], "codex")
            self.assertEqual(written["pid_started_at"], 99.75)

    def test_record_without_session_id_is_noop(self):
        self.assertIsNone(register_session.record({}))


class TerminalIdentityTests(unittest.TestCase):
    def test_tmux_wins_over_outer_kitty_and_captures_original_server_socket(self):
        identity = register_session.terminal_identity({
            "TMUX": "/tmp/tmux-100/default,99,0",
            "TMUX_PANE": "%7",
            "KITTY_WINDOW_ID": "4",
            "KITTY_LISTEN_ON": "unix:/kitty",
        })
        self.assertEqual(identity, {
            "kind": "tmux",
            "pane_id": "%7",
            "socket": "/tmp/tmux-100/default",
            "session_index": "0",
        })

    def test_konsole_preserves_service_and_full_session_path(self):
        identity = register_session.terminal_identity({
            "KONSOLE_DBUS_SERVICE": "org.kde.konsole-123",
            "KONSOLE_DBUS_SESSION": "/Sessions/7",
            "KONSOLE_DBUS_WINDOW": "/Windows/1",
        })
        self.assertEqual(identity["service"], "org.kde.konsole-123")
        self.assertEqual(identity["session"], "/Sessions/7")

    def test_wt_session_does_not_select_windows_terminal_off_windows(self):
        original = register_session.os.name
        try:
            register_session.os.name = "posix"
            self.assertIsNone(register_session.terminal_identity({"WT_SESSION": "from-wsl"}))
        finally:
            register_session.os.name = original


class MainTests(unittest.TestCase):
    def _run_main_with_stdin(self, text):
        original_stdin = sys.stdin
        sys.stdin = io.StringIO(text)
        try:
            return register_session.main()
        finally:
            sys.stdin = original_stdin

    def test_main_returns_zero_on_invalid_json(self):
        self.assertEqual(self._run_main_with_stdin("not json {{{"), 0)

    def test_main_returns_zero_on_empty_stdin(self):
        self.assertEqual(self._run_main_with_stdin(""), 0)

    def test_main_returns_zero_on_non_object_json(self):
        self.assertEqual(self._run_main_with_stdin("[1, 2, 3]"), 0)


if __name__ == "__main__":
    unittest.main()
