import json
import os
from pathlib import Path
from types import SimpleNamespace
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
REAPER = ROOT / ".agents/machine/utility/peer-cli/scripts/finish_reaper.py"
CLOSE = ROOT / ".agents/machine/utility/peer-cli/scripts/close.py"
FINISH = ROOT / ".agents/machine/utility/peer-cli/scripts/finish.py"
sys.path.insert(0, str(REAPER.parent))
import session_close
import finish
import finish_reaper
import close as own_close


class HostFallbackTests(unittest.TestCase):
    def test_unavailable_terminal_can_close_verified_host_without_wrapper(self):
        entry = {"pid": 30, "pid_started_at": 3.0}
        for module in (own_close, finish):
            with self.subTest(module=module.__name__), \
                    mock.patch.dict(os.environ, {"AGENT_FINISH_CLOSE_MODE": ""}), \
                    mock.patch.object(session_close, "verified_live", return_value=True), \
                    mock.patch.object(module.close_tab, "close_entry",
                                      side_effect=module.close_tab.TerminalUnavailable("unavailable")), \
                    mock.patch.object(module.os, "kill") as killer:
                module.close_host(entry)
                killer.assert_called_once_with(30, module.signal.SIGTERM)

    def test_fallback_rechecks_host_after_terminal_inspection(self):
        entry = {"pid": 30, "pid_started_at": 3.0}
        for module in (own_close, finish):
            with self.subTest(module=module.__name__), \
                    mock.patch.dict(os.environ, {"AGENT_FINISH_CLOSE_MODE": ""}), \
                    mock.patch.object(session_close, "verified_live", side_effect=[True, False]), \
                    mock.patch.object(module.close_tab, "close_entry",
                                      side_effect=module.close_tab.TerminalUnavailable("unavailable")), \
                    mock.patch.object(module.os, "kill") as killer:
                with self.assertRaisesRegex(session_close.Refusal, "identity changed"):
                    module.close_host(entry)
                killer.assert_not_called()


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], text=True, capture_output=True, check=True).stdout.strip()


@unittest.skipUnless(sys.platform == "linux" or os.name == "nt", "Supported process backends")
class FinishReaperProcessTests(unittest.TestCase):
    def test_armed_observer_waits_for_exit_then_removes_worktree_and_obligation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); bare = root / "origin.git"; primary = root / "primary"; worktree = root / "feature"; state = root / "state"
            subprocess.run(["git", "init", "--bare", "-q", "-b", "main", str(bare)], check=True)
            subprocess.run(["git", "clone", "-q", str(bare), str(primary)], check=True)
            git(primary, "config", "user.email", "t@example.com"); git(primary, "config", "user.name", "t")
            (primary / "base").write_text("base\n", encoding="utf-8"); git(primary, "add", "."); git(primary, "commit", "-q", "-m", "base"); git(primary, "push", "-q", "-u", "origin", "main"); git(primary, "remote", "set-head", "origin", "main")
            git(primary, "branch", "feature"); git(primary, "worktree", "add", "-q", str(worktree), "feature")
            (worktree / "feature").write_text("feature\n", encoding="utf-8"); git(worktree, "add", "."); git(worktree, "commit", "-q", "-m", "feature")
            head = git(worktree, "rev-parse", "HEAD"); git(primary, "checkout", "-q", "main"); git(primary, "merge", "-q", "--squash", "feature"); git(primary, "commit", "-q", "-m", "merged"); git(primary, "push", "-q", "origin", "main")
            receipts = state / "merge-cleanup/receipts"; receipts.mkdir(parents=True)
            (receipts / "receipt.json").write_text(json.dumps({"worktree": str(worktree), "primary": str(primary), "branch": "feature", "head": head, "default": "main", "verdict": "removable", "recorded_at": time.time()}), encoding="utf-8")
            obligation = state / "merge-cleanup/obligations/one.json"; obligation.parent.mkdir(parents=True); obligation.write_text(json.dumps({"worktree": str(worktree), "session_id": "ours"}), encoding="utf-8")
            host = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], cwd=worktree)
            started = self.process_started_at(host.pid)
            result = state / "merge-cleanup/results/result.json"; env = dict(os.environ, AGENT_STATE_DIRECTORY=str(state), AGENT_FINISH_REAPER_TIMEOUT_SECONDS="10")
            invocation_id = "integration-invocation"
            observer = subprocess.Popen([
                sys.executable, str(REAPER), "--host-pid", str(host.pid),
                "--host-start", str(started), "--worktree", str(worktree),
                "--result", str(result), "--session-id", "ours",
                "--invocation-id", invocation_id, "--head", head,
                "--primary", str(primary), "--branch", "feature", "--default", "main",
            ], env=env)
            try:
                for _ in range(200):
                    if result.exists(): break
                    time.sleep(.05)
                record = json.loads(result.read_text(encoding="utf-8"))
                (Path(str(result) + ".accepted")).write_text(
                    json.dumps({
                        "host_pid": host.pid, "host_start": started,
                        "worktree": str(worktree.resolve()), "session_id": "ours",
                        "invocation_id": invocation_id, "head": head,
                        "primary": str(primary), "branch": "feature", "default": "main",
                        "accepted": time.time(), "reaper_pid": record["reaper_pid"],
                        "reaper_started_at": record["reaper_started_at"],
                        "observer_pid": record["reaper_pid"],
                        "observer_started_at": record["reaper_started_at"],
                    }),
                    encoding="utf-8",
                )
                for _ in range(200):
                    if Path(str(result) + ".armed").exists(): break
                    time.sleep(.05)
                self.assertTrue(worktree.exists())
                self.assertTrue(obligation.exists())
                host.terminate(); host.wait(5); observer.wait(10)
                self.assertFalse(worktree.exists())
                self.assertFalse(obligation.exists()); self.assertEqual(1, subprocess.run(["git", "-C", str(primary), "show-ref", "--verify", "--quiet", "refs/heads/feature"]).returncode)
                self.assertEqual("succeeded", json.loads(result.read_text(encoding="utf-8"))["status"])
            finally:
                if host.poll() is None:
                    host.kill()
                host.wait(timeout=5)
                if observer.poll() is None:
                    observer.kill()
                observer.wait(timeout=5)

    def test_close_entrypoint_records_verified_session_exit_without_removing_checkout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            worktree = root / "worktree"
            state = root / "state"
            host_executable, host_name = self.fixture_host(root)
            subprocess.run(["git", "init", "-q", "-b", "main", str(worktree)], check=True)
            subprocess.run(["git", "-C", str(worktree), "config", "user.email", "t@example.com"], check=True)
            subprocess.run(["git", "-C", str(worktree), "config", "user.name", "t"], check=True)
            (worktree / "base").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(worktree), "add", "."], check=True)
            subprocess.run(["git", "-C", str(worktree), "commit", "-q", "-m", "base"], check=True)
            env = dict(
                os.environ,
                AGENT_STATE_DIRECTORY=str(state),
                AGENT_CLI_HOST_NAMES=host_name,
                AGENT_FINISH_CLOSE_MODE="process",
                AGENT_FINISH_REAPER_TIMEOUT_SECONDS="10",
            )
            host = subprocess.Popen([
                str(host_executable), "-c",
                "import os, subprocess, sys, time; "
                "\nwhile not os.path.exists(sys.argv[2]): time.sleep(.01)"
                "\nraise SystemExit(subprocess.call([sys.executable, sys.argv[1]]))",
                str(CLOSE), str(root / "start"),
            ], cwd=worktree, env=env)
            try:
                started = self.process_started_at(host.pid)
                sessions = state / "cli-sessions"
                sessions.mkdir(parents=True)
                (sessions / "ours.json").write_text(json.dumps({
                    "session_id": "ours", "cwd": str(worktree), "pid": host.pid,
                    "pid_started_at": started, "started_at": time.time(),
                    "host": host_name,
                }), encoding="utf-8")
                (root / "start").touch()
                result_directory = state / "merge-cleanup/results"
                for _ in range(300):
                    results = list(result_directory.glob("*.json")) if result_directory.exists() else []
                    if results:
                        break
                    time.sleep(.05)
                self.assertTrue(results)
                result_path = results[0]
                for _ in range(300):
                    result = json.loads(result_path.read_text(encoding="utf-8"))
                    if result.get("status") == "session-closed":
                        break
                    time.sleep(.05)
                self.assertEqual("session-closed", result["status"])
                self.assertTrue(result["session_exited"])
                self.assertEqual("ours", result["session_id"])
                self.assertTrue(worktree.is_dir())
            finally:
                if host.poll() is None:
                    host.kill()
                host.wait(timeout=5)

    def test_finish_entrypoint_removes_verified_disposable_worktree_after_host_exit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bare = root / "origin.git"
            primary = root / "primary"
            worktree = root / "feature"
            state = root / "state"
            host_executable, host_name = self.fixture_host(root)
            subprocess.run(["git", "init", "--bare", "-q", "-b", "main", str(bare)], check=True)
            subprocess.run(["git", "clone", "-q", str(bare), str(primary)], check=True)
            for key, value in (("user.email", "t@example.com"), ("user.name", "t")):
                subprocess.run(["git", "-C", str(primary), "config", key, value], check=True)
            (primary / "base").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(primary), "add", "."], check=True)
            subprocess.run(["git", "-C", str(primary), "commit", "-q", "-m", "base"], check=True)
            subprocess.run(["git", "-C", str(primary), "push", "-q", "-u", "origin", "main"], check=True)
            subprocess.run(["git", "-C", str(primary), "remote", "set-head", "origin", "main"], check=True)
            subprocess.run(["git", "-C", str(primary), "branch", "feature"], check=True)
            subprocess.run(["git", "-C", str(primary), "worktree", "add", "-q", str(worktree), "feature"], check=True)
            head = git(worktree, "rev-parse", "HEAD")
            receipt_directory = state / "merge-cleanup/receipts"
            receipt_directory.mkdir(parents=True)
            (receipt_directory / "receipt.json").write_text(json.dumps({
                "worktree": str(worktree), "primary": str(primary), "branch": "feature",
                "head": head, "default": "main", "verdict": "removable",
                "recorded_at": time.time(),
            }), encoding="utf-8")
            obligation = state / "merge-cleanup/obligations/ours.json"
            obligation.parent.mkdir(parents=True)
            obligation.write_text(json.dumps({"worktree": str(worktree), "session_id": "ours"}), encoding="utf-8")
            env = dict(
                os.environ,
                AGENT_STATE_DIRECTORY=str(state),
                AGENT_CLI_HOST_NAMES=host_name,
                AGENT_FINISH_CLOSE_MODE="process",
                AGENT_FINISH_REAPER_TIMEOUT_SECONDS="10",
            )
            host = subprocess.Popen([
                str(host_executable), "-c",
                "import os, subprocess, sys, time; "
                "\nwhile not os.path.exists(sys.argv[2]): time.sleep(.01)"
                "\nraise SystemExit(subprocess.call([sys.executable, sys.argv[1]]))",
                str(FINISH), str(root / "start"),
            ], cwd=worktree, env=env)
            try:
                started = self.process_started_at(host.pid)
                sessions = state / "cli-sessions"
                sessions.mkdir(parents=True)
                (sessions / "ours.json").write_text(json.dumps({
                    "session_id": "ours", "cwd": str(worktree), "pid": host.pid,
                    "pid_started_at": started, "started_at": time.time(),
                    "host": host_name,
                }), encoding="utf-8")
                (root / "start").touch()
                result_directory = state / "merge-cleanup/results"
                for _ in range(300):
                    results = list(result_directory.glob("*.json")) if result_directory.exists() else []
                    if results:
                        break
                    time.sleep(.05)
                self.assertTrue(results)
                result_path = results[0]
                for _ in range(300):
                    result = json.loads(result_path.read_text(encoding="utf-8"))
                    if result.get("status") in {"succeeded", "branch-preserved", "failed"}:
                        break
                    time.sleep(.05)
                self.assertEqual("succeeded", result["status"])
                self.assertTrue(result["session_exited"])
                self.assertFalse(worktree.exists())
                self.assertFalse(obligation.exists())
                self.assertEqual(
                    1,
                    subprocess.run([
                        "git", "-C", str(primary), "show-ref", "--verify", "--quiet",
                        "refs/heads/feature",
                    ], check=False).returncode,
                )
            finally:
                if host.poll() is None:
                    host.kill()
                host.wait(timeout=5)

    @staticmethod
    def fixture_host(root):
        if os.name == "nt":
            executable = Path(sys.executable)
            return executable, executable.stem.casefold()
        executable = root / "fixture-host"
        os.symlink(sys.executable, executable)
        return executable, "fixture-host"

    @staticmethod
    def process_started_at(pid):
        process = session_close.register_session.build_process_lookup()(pid)
        if process is None or not session_close.valid_identity(pid, process.started_at):
            raise AssertionError("disposable host has no queryable process identity")
        return process.started_at


class ReceiptSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.worktree = Path(self.temp.name) / "worktree"
        self.worktree.mkdir()
        self.original_state = os.environ.get("AGENT_STATE_DIRECTORY")
        os.environ["AGENT_STATE_DIRECTORY"] = self.temp.name
        self.addCleanup(self.restore_state)
        self.original_git = session_close.git
        self.original_now = session_close.now
        def fake_git(_cwd, *args):
            if args[:3] == ("worktree", "list", "--porcelain"):
                return 0, "worktree " + str(self.worktree.resolve()), ""
            return 0, "head" if args[-1] == "HEAD" else "branch", ""

        session_close.git = fake_git
        session_close.now = lambda: 1000.0
        self.addCleanup(self.restore_helpers)

    def restore_state(self):
        if self.original_state is None: os.environ.pop("AGENT_STATE_DIRECTORY", None)
        else: os.environ["AGENT_STATE_DIRECTORY"] = self.original_state

    def restore_helpers(self):
        session_close.git = self.original_git; session_close.now = self.original_now

    def receipt(self, **changes):
        value = {"worktree": str(self.worktree), "primary": str(Path(self.temp.name) / "primary"), "branch": "branch", "head": "head", "default": "main", "verdict": "removable", "recorded_at": 999.0}
        value.update(changes)
        directory = Path(self.temp.name) / "merge-cleanup/receipts"; directory.mkdir(parents=True, exist_ok=True)
        (directory / "entry.json").write_text(json.dumps(value), encoding="utf-8")

    def test_missing_malformed_stale_future_and_nonremovable_receipts_refuse(self):
        with self.assertRaises(session_close.Refusal): session_close.fresh_removable_receipt(self.worktree)
        for name, changes in (("malformed", {}), ("stale", {"recorded_at": -9999}), ("future", {"recorded_at": 2000}), ("preserve", {"verdict": "preserve"})):
            with self.subTest(name=name):
                directory = Path(self.temp.name) / "merge-cleanup/receipts"; directory.mkdir(parents=True, exist_ok=True)
                for item in directory.iterdir(): item.unlink()
                if name == "malformed": (directory / "entry.json").write_text("[", encoding="utf-8")
                else: self.receipt(**changes)
                with self.assertRaises(session_close.Refusal): session_close.fresh_removable_receipt(self.worktree)

    def test_moved_head_and_primary_refuse(self):
        self.receipt()
        session_close.git = lambda _cwd, *args: (
            0, "moved" if args[-1] == "HEAD" else "branch", ""
        )
        with self.assertRaises(session_close.Refusal): session_close.fresh_removable_receipt(self.worktree)
        session_close.git = lambda _cwd, *args: (
            0, "head" if args[-1] == "HEAD" else "branch", ""
        )
        directory = Path(self.temp.name) / "merge-cleanup/receipts"
        (directory / "entry.json").unlink(); self.receipt(primary=str(self.worktree))
        with self.assertRaises(session_close.Refusal): session_close.fresh_removable_receipt(self.worktree)

    def test_finish_refuses_a_foreign_worktree_before_receipt_or_observer(self):
        original = (finish.session_close.own_host_and_entry, finish.session_close.worktree_from_cwd,
                    finish.session_close.under_or_equal, finish.session_close.fresh_removable_receipt)
        finish.session_close.own_host_and_entry = lambda: {"cwd": str(self.worktree), "session_id": "ours"}
        finish.session_close.worktree_from_cwd = lambda: self.worktree
        finish.session_close.under_or_equal = lambda *_args: True
        finish.session_close.fresh_removable_receipt = lambda *_args: self.fail("receipt must not be read")
        try:
            with self.assertRaises(session_close.Refusal): finish.main(["--worktree", str(Path(self.temp.name) / "foreign")])
        finally:
            (finish.session_close.own_host_and_entry, finish.session_close.worktree_from_cwd,
             finish.session_close.under_or_equal, finish.session_close.fresh_removable_receipt) = original


class ProcessIdentityTests(unittest.TestCase):
    def test_absent_zombie_reused_and_unqueryable_are_distinct(self):
        original = session_close.register_session.build_process_lookup
        self.addCleanup(setattr, session_close.register_session, "build_process_lookup", original)

        session_close.register_session.build_process_lookup = lambda: lambda _pid: None
        self.assertEqual(session_close.identity_status(101, 10.0), "exited")
        self.assertTrue(session_close.verified_exited(101, 10.0))

        reused = session_close.register_session.ProcessInfo(101, 1, "codex", 20.0)
        session_close.register_session.build_process_lookup = lambda: lambda _pid: reused
        self.assertEqual(session_close.identity_status(101, 10.0), "reused")
        self.assertFalse(session_close.verified_exited(101, 10.0))

        def unreadable(_pid):
            raise PermissionError("denied")

        session_close.register_session.build_process_lookup = lambda: unreadable
        self.assertEqual(session_close.identity_status(101, 10.0), "unknown")
        self.assertFalse(session_close.verified_exited(101, 10.0))

    def test_invalid_pid_and_timestamp_are_unknown(self):
        for pid, started in ((0, 1.0), (1, 0.0), (1, float("nan")), (True, 1.0)):
            with self.subTest(pid=pid, started=started):
                self.assertEqual(session_close.identity_status(pid, started), "unknown")
                self.assertFalse(session_close.verified_exited(pid, started))


class ClaimAndObligationSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.worktree = Path(self.temp.name) / "worktree"
        self.worktree.mkdir()
        self.original_state = os.environ.get("AGENT_STATE_DIRECTORY")
        os.environ["AGENT_STATE_DIRECTORY"] = self.temp.name
        self.addCleanup(self.restore_state)

    def restore_state(self):
        if self.original_state is None:
            os.environ.pop("AGENT_STATE_DIRECTORY", None)
        else:
            os.environ["AGENT_STATE_DIRECTORY"] = self.original_state

    def write_entry(self, name, entry):
        directory = Path(self.temp.name) / "cli-sessions"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / name).write_text(json.dumps(entry), encoding="utf-8")

    def test_unknown_attached_claimant_blocks_cleanup(self):
        worktree = self.worktree
        own = {"session_id": "ours", "pid": 98, "pid_started_at": 4.0}
        self.write_entry("unknown.json", {
            "session_id": "other", "cwd": str(worktree), "pid": 99,
            "pid_started_at": 5.0, "started_at": 6.0, "host": "codex",
        })
        with mock.patch.object(session_close, "identity_status", return_value="unknown"):
            self.assertIsNotNone(session_close.other_live_claimant(worktree, own))

    def test_only_exact_own_session_process_is_excluded(self):
        worktree = self.worktree
        own = {"session_id": "ours", "pid": 10, "pid_started_at": 1.0}
        self.write_entry("ours.json", {
            "session_id": "ours", "cwd": str(worktree), "pid": 10,
            "pid_started_at": 1.0, "started_at": 2.0, "host": "codex",
        })
        with mock.patch.object(session_close, "identity_status", return_value="live"):
            self.assertIsNone(session_close.other_live_claimant(worktree, own))
        for suffix, pid, started, status in (
                ("different-pid", 11, 1.0, "live"),
                ("different-start", 10, 3.0, "unknown"),
        ):
            with self.subTest(suffix=suffix):
                self.write_entry("ours.json", {
                    "session_id": "ours", "cwd": str(worktree), "pid": pid,
                    "pid_started_at": started, "started_at": 4.0, "host": "codex",
                })
                with mock.patch.object(session_close, "identity_status", return_value=status):
                    self.assertIsNotNone(session_close.other_live_claimant(worktree, own))

    def test_finish_preflight_passes_full_own_identity_to_claim_check(self):
        entry = {"session_id": "ours", "pid": 10, "pid_started_at": 1.0,
                 "cwd": str(self.worktree)}
        receipt = {"head": "head", "primary": "primary", "branch": "branch", "default": "main"}
        with mock.patch.object(finish.session_close, "own_host_and_entry", return_value=entry), \
                mock.patch.object(finish.session_close, "worktree_from_cwd", return_value=self.worktree), \
                mock.patch.object(finish.session_close, "under_or_equal", return_value=True), \
                mock.patch.object(finish.session_close, "fresh_removable_receipt", return_value=receipt), \
                mock.patch.object(finish.session_close, "other_live_claimant", return_value={"pid": 11}) as claimant, \
                mock.patch.object(finish.session_close, "start_observer") as observer, \
                mock.patch.object(finish.os, "kill") as killer:
            with self.assertRaisesRegex(session_close.Refusal, "another verified"):
                finish.main(["--worktree", str(self.worktree)])
        claimant.assert_called_once_with(self.worktree, entry)
        observer.assert_not_called()
        killer.assert_not_called()

    def test_refresh_cleanup_passes_full_own_identity_to_claim_check(self):
        entry = {"session_id": "ours", "pid": 10, "pid_started_at": 1.0,
                 "cwd": str(self.worktree)}
        receipt = {"head": "head", "primary": "primary", "branch": "branch", "default": "main"}
        with mock.patch.object(finish.session_close, "own_host_and_entry", return_value=entry), \
                mock.patch.object(finish.session_close, "worktree_from_cwd", return_value=self.worktree), \
                mock.patch.object(finish.session_close, "under_or_equal", return_value=True), \
                mock.patch.object(finish.session_close, "fresh_removable_receipt", return_value=receipt), \
                mock.patch.object(finish.session_close, "other_live_claimant", return_value={"pid": 11}) as claimant, \
                mock.patch.object(finish.os, "kill") as killer:
            with self.assertRaisesRegex(session_close.Refusal, "another registered"):
                finish.refresh_cleanup(entry, self.worktree, receipt)
        claimant.assert_called_once_with(self.worktree, entry)
        killer.assert_not_called()

    def test_final_preflight_blocks_same_id_successor_without_removing_or_signalling(self):
        args = SimpleNamespace(
            worktree=str(self.worktree), head="head", primary="primary", branch="branch",
            default="main", session_id="ours", host_pid=10, host_start=1.0,
        )
        receipt = {"head": "head", "primary": "primary", "branch": "branch", "default": "main"}
        with mock.patch.object(finish_reaper.session_close, "fresh_removable_receipt", return_value=receipt), \
                mock.patch.object(finish_reaper.session_close, "verified_exited", return_value=True), \
                mock.patch.object(finish_reaper.session_close, "other_live_claimant", return_value={"pid": 11}) as claimant, \
                mock.patch.object(finish_reaper.session_close, "git") as git_call, \
                mock.patch.object(finish_reaper.os, "kill") as killer:
            with self.assertRaisesRegex(session_close.Refusal, "another verified"):
                finish_reaper.final_preflight(args)
        claimant.assert_called_once_with(
            self.worktree,
            {"session_id": "ours", "pid": 10, "pid_started_at": 1.0},
        )
        git_call.assert_not_called()
        killer.assert_not_called()

    def test_obligation_removal_requires_both_session_and_worktree(self):
        directory = Path(self.temp.name) / "merge-cleanup/obligations"
        directory.mkdir(parents=True)
        worktree = Path(self.temp.name) / "one"
        other = Path(self.temp.name) / "other"
        records = {
            "matching.json": {"session_id": "ours", "worktree": str(worktree)},
            "same-session.json": {"session_id": "ours", "worktree": str(other)},
            "same-worktree.json": {"session_id": "other", "worktree": str(worktree)},
        }
        for name, value in records.items():
            (directory / name).write_text(json.dumps(value), encoding="utf-8")
        session_close.remove_matching_obligations(worktree, "ours")
        self.assertFalse((directory / "matching.json").exists())
        self.assertTrue((directory / "same-session.json").exists())
        self.assertTrue((directory / "same-worktree.json").exists())


class WindowsWrapperSafetyTests(unittest.TestCase):
    def setUp(self):
        platform = mock.patch.object(session_close, "os", SimpleNamespace(name="nt"))
        platform.start()
        self.addCleanup(platform.stop)

    def test_wrapper_requires_a_shell_command_that_launches_the_verified_host(self):
        host = session_close.register_session.ProcessInfo(10, 20, "codex.exe", 100.0)
        wrapper = session_close.register_session.ProcessInfo(20, 1, "pwsh.exe", 95.0)
        original_table = session_close.register_session._windows_process_table
        session_close.register_session._windows_process_table = lambda: {10: host, 20: wrapper}
        self.addCleanup(
            setattr, session_close.register_session, "_windows_process_table", original_table,
        )
        entry = {
            "session_id": "ours", "cwd": "C:/worktree", "pid": 10,
            "pid_started_at": 100.0, "started_at": 101.0, "host": "codex",
        }
        command = mock.Mock(returncode=0, stdout="pwsh -Command codex", stderr="")
        with mock.patch.object(session_close, "process_info", return_value=host), mock.patch(
                "subprocess.run", return_value=command):
            self.assertEqual(
                {"pid": 20, "started_at": 95.0},
                session_close.qualified_windows_wrapper(entry),
            )
        foreign = mock.Mock(returncode=0, stdout="pwsh -NoProfile", stderr="")
        with mock.patch.object(session_close, "process_info", return_value=host), mock.patch(
                "subprocess.run", return_value=foreign):
            self.assertIsNone(session_close.qualified_windows_wrapper(entry))


    def test_reused_host_identity_cannot_qualify_a_wrapper(self):
        entry = {
            "session_id": "ours", "cwd": "C:/worktree", "pid": 10,
            "pid_started_at": 100.0, "started_at": 101.0, "host": "codex",
        }
        reused = session_close.register_session.ProcessInfo(10, 20, "codex.exe", 200.0)
        with mock.patch.object(session_close, "process_info", return_value=reused), \
                mock.patch.object(session_close.register_session, "_windows_process_table") as table:
            self.assertIsNone(session_close.qualified_windows_wrapper(entry))
            table.assert_not_called()


class WindowsObserverTaskTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="peer cli & xml ")
        self.addCleanup(self.temporary.cleanup)
        self.state = Path(self.temporary.name) / "state & xml"
        self.original_state = os.environ.get("AGENT_STATE_DIRECTORY")
        os.environ["AGENT_STATE_DIRECTORY"] = str(self.state)
        self.addCleanup(self.restore_state)
        self.platform = mock.patch.object(
            session_close, "os", SimpleNamespace(
                name="nt", environ=os.environ, fdopen=os.fdopen, close=os.close,
            ),
        )
        self.platform.start()
        self.addCleanup(self.platform.stop)

    def restore_state(self):
        if self.original_state is None:
            os.environ.pop("AGENT_STATE_DIRECTORY", None)
        else:
            os.environ["AGENT_STATE_DIRECTORY"] = self.original_state

    @staticmethod
    def completed(returncode=0, stdout="", stderr=""):
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)

    @staticmethod
    def windows_arguments(command_line):
        arguments = []
        index = 0
        while index < len(command_line):
            while index < len(command_line) and command_line[index] in " \t":
                index += 1
            if index == len(command_line):
                break
            argument = []
            quoted = False
            while index < len(command_line):
                if command_line[index] in " \t" and not quoted:
                    break
                slashes = 0
                while index < len(command_line) and command_line[index] == "\\":
                    slashes += 1
                    index += 1
                if index < len(command_line) and command_line[index] == '"':
                    argument.append("\\" * (slashes // 2))
                    if slashes % 2:
                        argument.append('"')
                        index += 1
                    elif quoted and index + 1 < len(command_line) and command_line[index + 1] == '"':
                        argument.append('"')
                        index += 2
                    else:
                        quoted = not quoted
                        index += 1
                else:
                    argument.append("\\" * slashes)
                    if index < len(command_line):
                        argument.append(command_line[index])
                        index += 1
            arguments.append("".join(argument))
        return arguments

    def test_long_special_arguments_register_as_a_structured_exec_action(self):
        arguments = [
            "--worktree", "C:\\a space\\<project>&\\quoted\"value",
            "--proof", "x" * 600,
        ]
        calls = []
        task_xml = {}

        def scheduler(arguments, **kwargs):
            calls.append((arguments, kwargs))
            if arguments[0] == "whoami.exe":
                return self.completed(stdout='"EXAMPLE\\A�da","S-1-5-21-123-456-789-1001"\r\n')
            if arguments[1] == "/create":
                task_xml["path"] = Path(arguments[arguments.index("/xml") + 1])
                task_xml["contents"] = task_xml["path"].read_bytes()
            return self.completed()

        with mock.patch.object(session_close.subprocess, "run", side_effect=scheduler):
            self.assertIsNone(session_close.start_observer(arguments))

        namespace = {"task": session_close.TASK_SCHEDULER_NAMESPACE}
        self.assertTrue(task_xml["contents"].startswith(b"\xff\xfe"))
        self.assertIn("encoding='utf-16'", task_xml["contents"].decode("utf-16").splitlines()[0])
        task = session_close.ET.fromstring(task_xml["contents"])
        execute = task.find("task:Actions/task:Exec", namespace)
        self.assertIsNotNone(execute)
        executable = execute.findtext("task:Command", namespaces=namespace)
        encoded_arguments = execute.findtext("task:Arguments", namespaces=namespace)
        working_directory = execute.findtext("task:WorkingDirectory", namespaces=namespace)
        self.assertEqual(sys.executable, executable)
        self.assertGreater(len(encoded_arguments), 262)
        decoded_arguments = self.windows_arguments(encoded_arguments)
        self.assertTrue(decoded_arguments[0].endswith("finish_reaper.py"))
        self.assertEqual(arguments, decoded_arguments[1:])
        self.assertEqual(str(self.state), working_directory)
        self.assertEqual("S-1-5-21-123-456-789-1001", task.findtext("task:Principals/task:Principal/task:UserId", namespaces=namespace))
        self.assertEqual("PT0S", task.findtext("task:Settings/task:ExecutionTimeLimit", namespaces=namespace))
        self.assertEqual(["whoami.exe", "/user", "/fo", "csv", "/nh"], calls[0][0])
        self.assertEqual("InteractiveToken", task.findtext("task:Principals/task:Principal/task:LogonType", namespaces=namespace))
        self.assertFalse(task_xml["path"].exists())
        create = calls[1][0]
        self.assertEqual(["schtasks.exe", "/create", "/tn"], create[:3])
        self.assertIn("/xml", create)
        self.assertNotIn("/tr", [part.casefold() for part in create])
        self.assertEqual(["schtasks.exe", "/run"], calls[2][0][:2])
        self.assertEqual(["schtasks.exe", "/delete"], calls[3][0][:2])

    def test_registration_refusal_reports_scheduler_output_and_removes_task_and_xml(self):
        calls = []
        task_xml = {}

        def scheduler(arguments, **kwargs):
            calls.append(arguments)
            if arguments[0] == "whoami.exe":
                return self.completed(stdout='"EXAMPLE\\A�da","S-1-5-21-123-456-789-1001"\r\n')
            if arguments[1] == "/create":
                task_xml["path"] = Path(arguments[arguments.index("/xml") + 1])
                return self.completed(returncode=5, stderr="ERROR: Access is denied.")
            return self.completed()

        with mock.patch.object(session_close.subprocess, "run", side_effect=scheduler), \
                self.assertRaisesRegex(session_close.Refusal, "create.*exit 5.*Access is denied"):
            session_close.start_observer(["--result", "C:\\result.json"])

        self.assertFalse(task_xml["path"].exists())
        self.assertEqual(["whoami.exe", "schtasks.exe", "schtasks.exe"], [call[0] for call in calls])
        self.assertEqual("/delete", calls[-1][1])


class ObserverHandshakeTests(unittest.TestCase):
    def test_startup_record_requires_spawned_reaper_and_exact_binding(self):
        worktree = str(Path("/tmp/worktree").resolve())
        record = {
            "host_pid": 10,
            "host_start": 5.0,
            "worktree": worktree,
            "session_id": "session",
            "invocation_id": "invocation",
            "started": time.time(),
            "reaper_pid": 20,
            "reaper_started_at": 30.0,
        }
        with mock.patch.object(session_close, "verified_live", return_value=True):
            self.assertTrue(session_close.valid_observer_start(
                record, 20, 10, 5.0, worktree, "session", "invocation",
            ))
            self.assertFalse(session_close.valid_observer_start(
                record, 21, 10, 5.0, worktree, "session", "invocation",
            ))
            self.assertFalse(session_close.valid_observer_start(
                record, 20, 11, 5.0, worktree, "session", "invocation",
            ))

    def test_startup_rejects_final_missing_and_future_bindings(self):
        baseline = {
            "host_pid": 10, "host_start": 5.0, "worktree": "/tmp/worktree",
            "session_id": "session", "invocation_id": "invocation", "started": 100.0,
            "reaper_pid": 20, "reaper_started_at": 30.0,
        }
        invalid = (
            {"status": "failed"},
            {"invocation_id": None},
            {"started": float("nan")},
            {"started": 200.0},
        )
        original_now = session_close.now
        session_close.now = lambda: 100.0
        self.addCleanup(setattr, session_close, "now", original_now)
        with mock.patch.object(session_close, "verified_live", return_value=True):
            for change in invalid:
                with self.subTest(change=change):
                    record = dict(baseline)
                    record.update(change)
                    self.assertFalse(session_close.valid_observer_start(
                        record, 20, 10, 5.0, "/tmp/worktree", "session", "invocation",
                    ))
            self.assertFalse(session_close.valid_observer_start(
                baseline, 20, 10, 5.0, "/tmp/worktree", "session", "invocation",
                minimum_started=103.0,
            ))

    def test_armed_requires_full_acknowledged_identity(self):
        expected = session_close.binding(10, 5.0, "/tmp/worktree", "session", "invocation")
        observer = {
            **expected, "started": 10.0, "reaper_pid": 20,
            "reaper_started_at": 30.0, "observer_pid": 20, "observer_started_at": 30.0,
        }
        accepted = {
            **expected, "accepted": 40.0, "reaper_pid": 20,
            "reaper_started_at": 30.0, "observer_pid": 20, "observer_started_at": 30.0,
        }
        armed = {**accepted, "armed": 50.0}
        original_now = session_close.now
        session_close.now = lambda: 50.0
        self.addCleanup(setattr, session_close, "now", original_now)
        with mock.patch.object(session_close, "verified_live", return_value=True):
            self.assertTrue(session_close.valid_armed(armed, expected, observer, accepted))
            armed["session_id"] = "different"
            self.assertFalse(session_close.valid_armed(armed, expected, observer, accepted))
