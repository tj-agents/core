"""Refresh recovery uses deterministic fake launchers and real disposable processes."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/machine/scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / ".agents/machine/utility/peer-cli/scripts"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RELAUNCH = load("codex_recovery_relaunch", SCRIPTS / "session_relaunch.py")
WATCHER = load("codex_recovery_watcher", SCRIPTS / "relaunch_watcher.py")
REFRESH = load("codex_recovery_refresh", SCRIPTS / "reload_plugins.py")
SESSION = "712495a1-d46b-4dbf-b0d4-f981b82bf39d"


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="CLI refresh ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.state = self.root / "state"
        environment = {key: value for key, value in os.environ.items()
                       if not key.startswith(("CLAUDE", "CODEX_THREAD", "CODEX_SESSION"))}
        environment["AGENT_STATE_DIRECTORY"] = str(self.state)
        patcher = mock.patch.dict(os.environ, environment, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_codex_relaunch_preserves_options_but_never_a_hook_bypass(self):
        original = ["--no-daemon", "--config", "model_reasoning_effort=high", "-m", "existing-model",
                    "--add-dir", "extra dir", "-C", "old dir", "resume", "old-session", "old prompt"]
        self.assertEqual(original[:7], RELAUNCH.codex_arguments(original))
        with self.assertRaisesRegex(RuntimeError, "hook-trust bypass"):
            RELAUNCH.codex_arguments(["--dangerously-bypass-hook-trust"])

    def test_close_runtime_resolves_to_the_cli_owner(self):
        self.assertEqual(ROOT / ".agents/cli/utility/close/scripts/close_session.py",
                         RELAUNCH.utility_script("close", "close_session.py"))

    def arm(self, entry=None, close_status="armed"):
        entry = entry or {"host": "codex", "session_id": SESSION, "pid": 4242,
                          "pid_started_at": 1000.5, "launch_cwd": str(self.root),
                          "profile": str(self.root / "profile"), "title": "Existing task"}
        events = []
        shared = mock.Mock()
        shared.own_host_and_entry.return_value = entry
        shared.start_detached.side_effect = lambda script, argv: events.append(("watcher", argv))
        close = mock.Mock()

        def arm_close():
            events.append(("close", []))
            RELAUNCH.write_json(self.state / "session-close" / f"{SESSION}.armed.json", {"armed_at": 10.5})
            return {"status": close_status, "session_id": SESSION}

        close.arm.side_effect = arm_close
        result = RELAUNCH.relaunch(self.root, {}, shared=shared, close=close,
                                   arguments=lambda _: ["--no-daemon", "-m", "existing-model"], host="codex")
        return result, events

    def test_codex_arm_binds_host_profile_checkout_and_fresh_close(self):
        result, events = self.arm()
        self.assertEqual(["watcher", "close"], [event[0] for event in events])
        self.assertEqual("armed", result["relaunch"])
        argv = events[0][1]
        self.assertEqual("codex", argv[argv.index("--host") + 1])
        self.assertEqual(str(self.root / "profile"), argv[argv.index("--profile") + 1])
        record = RELAUNCH.read_json(RELAUNCH.record_path(SESSION))
        self.assertEqual((str(self.root.resolve()), "codex", 10.5),
                         (record["cwd"], record["host"], record["close_armed_at"]))

    def test_wrong_checkout_is_refused_before_either_watcher_is_started(self):
        entry = {"host": "codex", "session_id": SESSION, "launch_cwd": str(self.root / "other")}
        with self.assertRaisesRegex(RuntimeError, "checkout"):
            self.arm(entry)
        self.assertFalse(RELAUNCH.record_path(SESSION).exists())

    def test_a_close_without_armed_confirmation_cancels_relaunch(self):
        with self.assertRaisesRegex(RuntimeError, "not armed"):
            self.arm(close_status="refused")
        self.assertEqual("cancelled", RELAUNCH.read_json(RELAUNCH.record_path(SESSION))["state"])

    def run_sync(self, failure=None, extra=(), setup_errors=()):
        output = io.StringIO()
        failure = failure or REFRESH.codex_hook_trust.RestartRequired("standalone client is absent from daemon")
        with mock.patch.object(REFRESH.launch_check, "check", return_value="current"), \
                mock.patch.object(REFRESH.launch_check, "ensure_hooks", side_effect=failure), \
                mock.patch.object(REFRESH.required_plugins, "converge_setup", return_value=list(setup_errors)), \
                mock.patch.dict(sys.modules, {"session_relaunch": RELAUNCH}), \
                mock.patch.object(RELAUNCH, "relaunch", return_value={"relaunch": "armed", "session_id": SESSION}) as restart, \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            result = REFRESH.main(["--host", "codex", "--project", str(self.root), *extra])
        return result, json.loads(output.getvalue()), restart

    def test_the_actual_unloaded_daemon_failure_automatically_arms_same_session_recovery(self):
        code, report, restart = self.run_sync()
        self.assertEqual(0, code)
        self.assertEqual(("armed", "pending", SESSION),
                         (report["codex"]["relaunch"], report["codex"]["adoption"], report["codex"]["session_id"]))
        restart.assert_called_once_with(self.root, {}, host="codex")

    def test_untrusted_hooks_are_not_converted_into_a_restart_or_success(self):
        code, report, restart = self.run_sync(RuntimeError("Required hooks are modified"))
        self.assertEqual(1, code)
        self.assertIn("modified", report["hook_readiness_error"])
        restart.assert_not_called()

    def test_required_setup_failure_prevents_client_closure(self):
        code, _, restart = self.run_sync(setup_errors=["required setup failed"])
        self.assertEqual(1, code)
        restart.assert_not_called()

    def test_explicit_no_relaunch_leaves_the_client_open_and_reports_incomplete_adoption(self):
        code, report, restart = self.run_sync(extra=["--no-relaunch"])
        self.assertEqual(1, code)
        self.assertIn("--no-relaunch", report["hook_readiness_error"])
        restart.assert_not_called()

    def test_verification_only_never_arms_a_restart(self):
        with mock.patch.object(REFRESH, "executable_for", return_value="native"), \
                mock.patch.object(REFRESH, "selection", return_value=({}, [])), \
                mock.patch.object(REFRESH, "verify", return_value={"host": "codex", "problems": []}), \
                mock.patch.object(REFRESH.required_plugins, "check_setup", return_value=[]), \
                mock.patch.object(REFRESH.launch_check, "ensure_hooks") as hooks, \
                mock.patch.object(REFRESH, "relaunch_codex") as restart, \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(0, REFRESH.main(["--host", "codex", "--verify-only", "--project", str(self.root)]))
        hooks.assert_not_called()
        restart.assert_not_called()

    def test_full_refresh_uses_the_same_recovery_after_package_verification(self):
        with mock.patch.object(REFRESH, "executable_for", return_value="native"), \
                mock.patch.object(REFRESH, "selection", return_value=({}, [])), \
                mock.patch.object(REFRESH, "refresh", return_value=[]), \
                mock.patch.object(REFRESH, "verify", return_value={"host": "codex", "problems": []}), \
                mock.patch.object(REFRESH.required_plugins, "converge_setup", return_value=[]), \
                mock.patch.object(REFRESH.launch_check, "ensure_hooks", side_effect=REFRESH.codex_hook_trust.RestartRequired("restart")), \
                mock.patch.object(REFRESH, "relaunch_codex", return_value={"relaunch": "armed"}) as restart, \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(0, REFRESH.main(["--host", "codex", "--verify", "--project", str(self.root)]))
        restart.assert_called_once_with(self.root, "restart", True)

    def watcher(self):
        record = self.state / "session-relaunch" / f"{SESSION}.json"
        recovery = self.root / "fake recovery.py"
        recovery.write_text("import json, os, sys\nfrom pathlib import Path\n"
                            "Path(__file__).with_suffix('.result').write_text(json.dumps("
                            "{'argv': sys.argv[1:], 'old_thread': os.environ.get('CODEX_THREAD_ID')}), encoding='utf-8')\n",
                            encoding="utf-8")
        RELAUNCH.write_json(record, {"state": "waiting", "token": "fixture", "close_armed_at": 10.5})
        RELAUNCH.write_json(self.state / "session-close" / f"{SESSION}.armed.json", {"armed_at": 10.5})
        options = ["--host", "codex", "--session-id", SESSION, "--pid", "4242", "--pid-started-at", "1.5",
                   "--record", str(record), "--token", "fixture", "--recovery", str(recovery),
                   "--profile", str(self.root / "pröfile"), "--prompt", "Resume owned work.", "--timeout", "5"]
        return WATCHER.arguments(options), recovery

    def test_cancelled_close_never_resumes_even_if_old_process_later_exits(self):
        args, recovery = self.watcher()
        RELAUNCH.write_json(self.state / "session-close" / f"{SESSION}.json", {"status": "cancelled", "at": 11})
        self.assertFalse(WATCHER.wait_for_exit(args, exited=lambda *_: True))
        self.assertFalse(recovery.with_suffix(".result").exists())

    def test_a_stale_success_receipt_does_not_authorize_a_second_writer(self):
        args, _ = self.watcher()
        RELAUNCH.write_json(self.state / "session-close" / f"{SESSION}.json", {"status": "closed", "at": 9})
        ticks = iter((0, 1, 6))
        self.assertFalse(WATCHER.wait_for_exit(args, exited=lambda *_: True,
                                              clock=lambda: next(ticks), sleep=lambda _: None))
        self.assertEqual("expired", WATCHER.read_record(args.record)["state"])

    def test_real_dummy_frontend_exits_before_same_profile_resumption_and_peer_survives(self):
        args, recovery = self.watcher()
        host = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(0.8)"])
        peer = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        self.addCleanup(peer.wait)
        self.addCleanup(peer.kill)
        self.addCleanup(host.wait)
        args.pid = host.pid
        args.pid_started_at = WATCHER.session_close.process_info(host.pid).started_at

        def record_verified_close():
            host.wait(timeout=10)
            RELAUNCH.write_json(self.state / "session-close" / f"{SESSION}.json", {"status": "closed", "at": time.time()})

        observer = threading.Thread(target=record_verified_close)
        observer.start()
        self.addCleanup(observer.join)
        with mock.patch.dict(os.environ, {"CODEX_THREAD_ID": "old-thread"}):
            self.assertTrue(WATCHER.wait_for_exit(args))
            self.assertEqual(0, WATCHER.launch(args))
        launched = json.loads(recovery.with_suffix(".result").read_text(encoding="utf-8"))
        self.assertIsNotNone(host.poll())
        self.assertIsNone(peer.poll())
        self.assertIsNone(launched["old_thread"])
        argv = launched["argv"]
        self.assertEqual("codex", argv[argv.index("--host") + 1])
        self.assertEqual(SESSION, argv[argv.index("--id") + 1])
        self.assertEqual(str(args.profile / "sessions"), argv[argv.index("--codex-history-root") + 1])
        self.assertEqual("launched", WATCHER.read_record(args.record)["state"])

    def test_record_replacement_after_exit_check_prevents_launch(self):
        args, recovery = self.watcher()
        RELAUNCH.write_json(args.record, {"state": "cancelled", "token": "fixture"})
        self.assertEqual(1, WATCHER.launch(args))
        self.assertFalse(recovery.with_suffix(".result").exists())

    def test_ambiguous_native_pickup_is_recorded_without_retrying(self):
        args, _ = self.watcher()
        run = mock.Mock(return_value=subprocess.CompletedProcess([], 3, "tab started", "pickup unverified"))
        self.assertEqual(3, WATCHER.launch(args, run=run))
        self.assertEqual("unverified", WATCHER.read_record(args.record)["state"])
        run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
