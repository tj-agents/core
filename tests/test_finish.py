import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
REAPER = ROOT / ".agents/machine/utility/peer-cli/scripts/finish_reaper.py"
sys.path.insert(0, str(REAPER.parent))
import session_close
import finish


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], text=True, capture_output=True, check=True).stdout.strip()


@unittest.skipUnless(sys.platform == "linux", "Linux integration")
class FinishReaperLinuxTests(unittest.TestCase):
    def test_armed_observer_removes_worktree_then_waits_to_clear_obligation(self):
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
            raw = (Path("/proc") / str(host.pid) / "stat").read_text(encoding="utf-8").split(); boot = next(float(line.split()[1]) for line in Path("/proc/stat").read_text(encoding="utf-8").splitlines() if line.startswith("btime ")); started = boot + int(raw[21]) / os.sysconf("SC_CLK_TCK")
            result = state / "merge-cleanup/results/result.json"; env = dict(os.environ, AGENT_STATE_DIRECTORY=str(state), AGENT_FINISH_REAPER_TIMEOUT_SECONDS="10")
            observer = subprocess.Popen([sys.executable, str(REAPER), "--host-pid", str(host.pid), "--host-start", str(started), "--worktree", str(worktree), "--result", str(result), "--session-id", "ours", "--head", head, "--primary", str(primary), "--branch", "feature", "--default", "main"], env=env)
            try:
                for _ in range(200):
                    if result.exists(): break
                    time.sleep(.05)
                record = json.loads(result.read_text(encoding="utf-8")); (Path(str(result) + ".accepted")).write_text(json.dumps({"reaper_pid": record["reaper_pid"], "reaper_started_at": record["reaper_started_at"]}), encoding="utf-8")
                for _ in range(200):
                    if not worktree.exists(): break
                    time.sleep(.05)
                self.assertFalse(worktree.exists()); self.assertTrue(obligation.exists())
                host.terminate(); host.wait(5); observer.wait(10)
                self.assertFalse(obligation.exists()); self.assertEqual(1, subprocess.run(["git", "-C", str(primary), "show-ref", "--verify", "--quiet", "refs/heads/feature"]).returncode)
                self.assertEqual("succeeded", json.loads(result.read_text(encoding="utf-8"))["status"])
            finally:
                if host.poll() is None: host.kill()
                if observer.poll() is None: observer.kill()


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
        session_close.git = lambda _cwd, *args: (0, "head" if args[-1] == "HEAD" else "branch", "")
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
        session_close.git = lambda _cwd, *args: (0, "moved" if args[-1] == "HEAD" else "branch", "")
        with self.assertRaises(session_close.Refusal): session_close.fresh_removable_receipt(self.worktree)
        session_close.git = lambda _cwd, *args: (0, "head" if args[-1] == "HEAD" else "branch", "")
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
