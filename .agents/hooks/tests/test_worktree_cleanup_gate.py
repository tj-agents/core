import json
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HOOK = ROOT / ".agents" / "hooks" / "worktree_cleanup_gate.py"


class WorktreeCleanupGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"
        (self.repo / ".agents").mkdir(parents=True)

    def configure(self, output, exit_code=0):
        audit = self.repo / "audit.py"
        audit.write_text(
            f"import sys\nsys.stdout.write({output!r})\nsys.exit({exit_code})\n",
            encoding="utf-8",
        )
        (self.repo / ".agents" / "worktree-cleanup-gate.json").write_text(
            json.dumps({"audit_command": [sys.executable, str(audit)]}), encoding="utf-8"
        )

    def invoke(self, event="Stop"):
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(
                {
                    "hook_event_name": event,
                    "session_id": f"worktree-cleanup-{uuid.uuid4().hex}",
                    "turn_id": "turn-1",
                    "cwd": str(self.repo),
                }
            ),
            capture_output=True,
            text=True,
            cwd=self.repo,
            check=False,
        )

    def test_blocks_only_the_audit_states_that_need_human_cleanup(self):
        self.configure("OPEN_PR active\nMERGED_NOT_IN_MAIN stale\nORPHAN_FOLDER old-folder\n")

        result = self.invoke()

        self.assertEqual(0, result.returncode, result.stderr)
        response = json.loads(result.stdout)
        self.assertEqual("block", response["decision"])
        self.assertIn("MERGED_NOT_IN_MAIN stale", response["reason"])
        self.assertIn("ORPHAN_FOLDER old-folder", response["reason"])
        self.assertIn("never deletes automatically", response["reason"])

    def test_allows_a_clean_audit_and_unrelated_states(self):
        self.configure("OPEN_PR active\nCLOSED_UNMERGED retained\n")

        result = self.invoke("SessionStart")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def test_configured_audit_failure_surfaces_loudly(self):
        self.configure("audit unavailable", exit_code=1)

        result = self.invoke()

        self.assertEqual(0, result.returncode, result.stderr)
        response = json.loads(result.stdout)
        self.assertEqual("block", response["decision"])
        self.assertIn("cannot run the configured audit", response["reason"])

    def test_no_config_is_not_this_gates_business(self):
        result = self.invoke()

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)


if __name__ == "__main__":
    unittest.main()
