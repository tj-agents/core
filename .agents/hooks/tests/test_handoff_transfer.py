import json
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "engineering/workflow/handoff/scripts/transfer.py"


class HandoffTransferTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.goal = self.root / "GOAL.md"
        self.receipt = self.root / "receipt.json"
        self.write_goal()
        self.git("init")
        self.git("config", "user.email", "test@example.test")
        self.git("config", "user.name", "Test")
        self.git("add", "GOAL.md")
        self.git("commit", "-m", "initial")

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True, check=True)

    def write_goal(self, receipt=None):
        receipt = receipt or self.receipt
        self.goal.write_text(
            "# Goal\n\n## Execution readiness\n\nVerdict: ready\n"
            "Execution authorization: implementation\nTransfer: required\n"
            f"Receipt: {receipt}\n\n## Next Steps\n\nImplement it.\n",
            encoding="utf-8",
        )

    def invoke(self, command, *args, cwd=None, ok=True):
        result = subprocess.run([sys.executable, str(SCRIPT), command, *args], cwd=cwd, capture_output=True, text=True)
        if ok:
            self.assertEqual(0, result.returncode, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(0, result.returncode)
        return result

    def prepare(self, receipt=None, mode="transfer", owner=None):
        receipt = receipt or self.receipt
        args = ("--receipt", str(receipt), "--goal", str(self.goal), "--worktree", str(self.root),
                "--predecessor", "planner", "--harness", "codex", "--mode", mode)
        if owner:
            args += ("--owner-reference", owner)
        return self.invoke("prepare", *args, cwd=self.root)

    def begin(self, data):
        return self.invoke("begin", "--receipt", str(self.receipt), "--attempt", data["attempt"], "--predecessor", "planner", cwd=self.root)

    def submit(self, data, content="submitted"):
        evidence = self.root / "submission.txt"
        evidence.write_text(content, encoding="utf-8")
        return self.invoke("submitted", "--receipt", str(self.receipt), "--attempt", data["attempt"], "--evidence-file", str(evidence))

    def acknowledge(self, data, successor="executor", harness="codex", cwd=None, ok=True):
        return self.invoke("acknowledge", "--receipt", str(self.receipt), "--attempt", data["attempt"],
                        "--successor", successor, "--harness", harness, cwd=cwd or self.root, ok=ok)

    def progress(self, data, successor="executor", harness="codex", ok=True):
        evidence = self.root / "progress.txt"
        evidence.write_text("first action", encoding="utf-8")
        return self.invoke("progress", "--receipt", str(self.receipt), "--attempt", data["attempt"],
                        "--successor", successor, "--harness", harness, "--evidence-file", str(evidence), cwd=self.root, ok=ok)

    def status(self):
        return self.invoke("status", "--receipt", str(self.receipt))

    def test_happy_chain_records_evidence(self):
        data = self.prepare()
        self.assertEqual("launching", self.begin(data)["state"])
        self.assertEqual("submitted", self.submit(data)["state"])
        self.assertEqual("acknowledged", self.acknowledge(data)["state"])
        self.assertEqual("active", self.progress(data)["state"])
        result = self.status()
        self.assertTrue(result["checkpoint_immutable"])
        self.assertEqual({"progress": True, "submission": True}, result["evidence_validity"])

    def test_receipt_accepts_equivalent_forward_slash_path(self):
        self.write_goal(str(self.receipt).replace("\\", "/"))
        self.assertEqual("prepared", self.prepare()["state"])

    def test_acknowledgement_can_precede_submission_without_downgrade(self):
        data = self.prepare()
        self.begin(data)
        self.acknowledge(data)
        self.assertEqual("acknowledged", self.submit(data)["state"])

    def test_prepare_and_claim_are_atomic(self):
        def attempt_prepare():
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "prepare", "--receipt", str(self.receipt), "--goal", str(self.goal),
                 "--worktree", str(self.root), "--predecessor", "planner", "--harness", "codex"],
                cwd=self.root, capture_output=True, text=True)
            return json.loads(result.stdout) if result.returncode == 0 else result
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: attempt_prepare(), range(2)))
        successes = [item for item in results if isinstance(item, dict)]
        self.assertEqual(1, len(successes))
        data = successes[0]
        self.begin(data)
        def claim(name):
            return subprocess.run(
                [sys.executable, str(SCRIPT), "acknowledge", "--receipt", str(self.receipt), "--attempt", data["attempt"],
                 "--successor", name, "--harness", "codex"], cwd=self.root, capture_output=True, text=True)
        with ThreadPoolExecutor(max_workers=2) as pool:
            claims = list(pool.map(claim, ("one", "two")))
        self.assertEqual(1, sum(item.returncode == 0 for item in claims))

    def test_missing_acknowledgement_is_submitted_or_uncertain(self):
        data = self.prepare()
        self.begin(data)
        self.submit(data)
        self.assertEqual("submitted", self.status()["state"])
        self.invoke("fail", "--receipt", str(self.receipt), "--attempt", data["attempt"], "--reason", "lost", "--outcome", "uncertain")
        self.assertEqual("uncertain", self.status()["state"])

    def test_repeated_begin_cannot_duplicate_a_launch(self):
        data = self.prepare()
        self.begin(data)
        self.invoke("begin", "--receipt", str(self.receipt), "--attempt", data["attempt"], "--predecessor", "planner", cwd=self.root, ok=False)
        self.assertEqual("launching", self.status()["state"])

    def test_pickup_rejects_wrong_attempt_goal_checkpoint_and_cwd(self):
        self.invoke("prepare", "--receipt", str(self.receipt), "--goal", str(self.goal), "--worktree", str(self.root),
                    "--predecessor", "planner", "--harness", "codex", cwd=self.root.parent, ok=False)
        data = self.prepare()
        self.goal.write_text(self.goal.read_text(encoding="utf-8") + "\nChanged.\n", encoding="utf-8")
        self.invoke("begin", "--receipt", str(self.receipt), "--attempt", data["attempt"], "--predecessor", "planner", cwd=self.root, ok=False)
        self.write_goal()
        self.invoke("acknowledge", "--receipt", str(self.receipt), "--attempt", data["attempt"], "--successor", "executor", "--harness", "codex", cwd=self.root, ok=False)
        self.begin(data)
        self.acknowledge({"attempt": "wrong"}, ok=False)
        self.acknowledge(data, cwd=self.root.parent, ok=False)
        self.goal.write_text(self.goal.read_text(encoding="utf-8") + "\nChanged.\n", encoding="utf-8")
        self.acknowledge(data, ok=False)

    def test_pickup_rejects_branch_and_head_changes(self):
        data = self.prepare()
        self.begin(data)
        self.git("checkout", "-b", "other")
        self.acknowledge(data, ok=False)
        self.git("checkout", "-")
        (self.root / "checkpoint.txt").write_text("head changed", encoding="utf-8")
        self.git("add", "checkpoint.txt")
        self.git("commit", "-m", "checkpoint")
        self.acknowledge(data, ok=False)

    def test_modes_do_not_reserve_and_owner_reference_is_preserved(self):
        for mode in ("planning-only", "prompt-only", "inline"):
            receipt = self.root / f"{mode}.json"
            self.invoke(
                "prepare", "--receipt", str(receipt), "--goal", str(self.goal), "--worktree", str(self.root),
                "--predecessor", "planner", "--harness", "codex", "--mode", mode, cwd=self.root, ok=False)
            self.assertFalse(receipt.exists())
        self.goal.write_text(
            self.goal.read_text(encoding="utf-8").replace(
                "Execution authorization: implementation\nTransfer",
                "Execution authorization: implementation\nExecution authorization: planning-only\nTransfer"),
            encoding="utf-8")
        self.invoke("prepare", "--receipt", str(self.receipt), "--goal", str(self.goal), "--worktree", str(self.root),
                    "--predecessor", "planner", "--harness", "codex", cwd=self.root, ok=False)
        self.assertFalse(self.receipt.exists())
        self.write_goal()
        data = self.prepare(owner="continuation://owner")
        self.assertEqual("continuation://owner", data["owner_reference"])

    def test_claimant_evidence_and_failure_are_monotonic(self):
        data = self.prepare()
        self.begin(data)
        self.acknowledge(data)
        self.progress(data, successor="other", ok=False)
        self.progress(data)
        self.invoke("fail", "--receipt", str(self.receipt), "--attempt", data["attempt"], "--reason", "late", "--outcome", "uncertain", ok=False)
        fresh = self.root / "fresh.json"
        self.receipt = fresh
        self.write_goal()
        self.git("add", "GOAL.md")
        self.git("commit", "-m", "fresh receipt")
        prepared = self.prepare()
        self.invoke("fail", "--receipt", str(fresh), "--attempt", prepared["attempt"], "--reason", "no launch", "--outcome", "failed")
        self.invoke("begin", "--receipt", str(fresh), "--attempt", prepared["attempt"], "--predecessor", "planner", cwd=self.root, ok=False)

    def test_harness_mismatch_preserves_pickup_state(self):
        data = self.prepare()
        self.begin(data)
        self.acknowledge(data, harness="claude", ok=False)
        self.assertEqual("launching", self.status()["state"])
        self.acknowledge(data)
        self.progress(data, harness="claude", ok=False)
        self.assertEqual("acknowledged", self.status()["state"])


if __name__ == "__main__":
    unittest.main()
