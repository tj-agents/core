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
