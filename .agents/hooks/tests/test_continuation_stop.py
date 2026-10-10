import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".agents/hooks/continuation_stop.py"
sys.path.insert(0, str(SCRIPT.parent))
spec = importlib.util.spec_from_file_location("continuation_stop", SCRIPT)
continuation_stop = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = continuation_stop
spec.loader.exec_module(continuation_stop)
import workflow_route


class ContinuationStopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/example/repo.git"], cwd=self.root, check=True)
        (self.root / "seed").write_text("seed", encoding="utf-8")
        subprocess.run(["git", "add", "seed"], cwd=self.root, check=True)
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "seed"], cwd=self.root, check=True)
        self.goal = self.root / "GOAL.md"
        self.goal.write_text("# Goal\n", encoding="utf-8")
        self.session = "session"

    def receipt(self, **extra):
        return {
            "worktree": str(self.root.resolve()),
            "execution_obligation": True,
            "execution_obligation_at": 1,
            "routed_at": 1,
            "prompt": "Implement this multi-phase migration through completion.",
            **extra,
        }

    def owner(self, state="waiting", **extra):
        workflows = continuation_stop.workflow_root()
        if str(workflows) not in sys.path:
            sys.path.insert(0, str(workflows))
        runtime = continuation_stop.module("continuation_runtime", workflows)
        return {
            **runtime.identity(self.root),
            "owner_id": "owner",
            "goal": str(self.goal.resolve()),
            "harness": "codex",
            "state": state,
            "reason": "accepted",
            "next_action": "Resume the goal",
            "updated_at": 2,
            "foreground": None,
            "child": None,
            "pr": None,
            **extra,
        }

    def write_owner(self, owner):
        path = self.root / ".agents/continuation/owner.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(owner), encoding="utf-8")

    def payload(self):
        return {"hook_event_name": "Stop", "cwd": str(self.root), "session_id": self.session}

    def call(self, receipt=None):
        with patch.object(continuation_stop, "read_receipt", return_value=receipt or self.receipt()):
            return continuation_stop.outcome(self.payload())

    def test_routed_execution_without_an_owner_blocks_in_independent_repositories(self):
        for name in ("first", "second"):
            with self.subTest(name=name):
                root = self.root.parent / name
                root.mkdir()
                payload = {"hook_event_name": "Stop", "cwd": str(root), "session_id": self.session}
                receipt = {"worktree": str(root.resolve()), "execution_obligation": True,
                           "execution_obligation_at": 1, "routed_at": 1}
                with patch.object(continuation_stop, "read_receipt", return_value=receipt):
                    self.assertIn("Initialize persistent-workflow", continuation_stop.outcome(payload))

    def test_waiting_owner_requires_observed_enabled_scheduler(self):
        self.write_owner(self.owner())
        with patch.object(continuation_stop, "scheduler_ready", return_value=False), \
             patch.object(continuation_stop, "observed_wake", return_value=True):
            self.assertIn("Register and enable", self.call())

    def test_scheduler_receipt_requires_matching_enabled_task_action(self):
        owner = self.owner()
        path = self.root / ".agents/continuation/owner.json"
        path.parent.mkdir(parents=True)
        receipt = {
            "owner_id": owner["owner_id"], "owner_path": str(path), "worktree": str(self.root),
            "task_name": "task", "task_path": "\\", "description": "owner", "execute": "powershell.exe",
            "arguments": "wake", "helper": "helper", "python": "python", "script": "script",
        }
        (path.parent / "scheduler.json").write_text(json.dumps(receipt), encoding="utf-8")
        task = {"TaskName": "task", "TaskPath": "\\", "State": "Ready", "Description": "owner",
                "Actions": [{"Execute": "powershell.exe", "Arguments": "wake", "WorkingDirectory": str(self.root)}],
                "Triggers": [{"Enabled": True}], "Enabled": True}
        with patch.object(continuation_stop, "WINDOWS", True), \
             patch.object(continuation_stop.subprocess, "run", return_value=Mock(returncode=0, stdout=json.dumps(task))):
            self.assertTrue(continuation_stop.scheduler_ready(path, owner, self.root.resolve()))
            for changed in (
                {"State": "Disabled"},
                {"Actions": []},
                {"Actions": [{"Execute": "wrong", "Arguments": "wake", "WorkingDirectory": str(self.root)}]},
                {"Triggers": []},
            ):
                with self.subTest(changed=changed):
                    candidate = dict(task, **changed)
                    continuation_stop.subprocess.run.return_value = Mock(returncode=0, stdout=json.dumps(candidate))
                    self.assertFalse(continuation_stop.scheduler_ready(path, owner, self.root.resolve()))
        receipt["owner_id"] = "foreign"
        (path.parent / "scheduler.json").write_text(json.dumps(receipt), encoding="utf-8")
        self.assertFalse(continuation_stop.scheduler_ready(path, owner, self.root.resolve()))

    def test_observed_wake_requires_this_owner(self):
        owner = self.owner()
        path = self.root / ".agents/continuation/owner.json"
        path.parent.mkdir(parents=True)
        (path.parent / "events.jsonl").write_text(json.dumps({"owner_id": "foreign", "event": "wake"}) + "\n", encoding="utf-8")
        self.assertFalse(continuation_stop.observed_wake(path, owner))
        (path.parent / "events.jsonl").write_text(json.dumps({"owner_id": "owner", "event": "wake"}) + "\n", encoding="utf-8")
        self.assertTrue(continuation_stop.observed_wake(path, owner))

    def test_foreground_and_working_without_a_lease_block(self):
        self.write_owner(self.owner("working", foreground={"pid": 1}))
        self.assertIn("foreground ownership", self.call())
        self.write_owner(self.owner("working"))
        with patch.object(continuation_stop, "scheduler_ready", return_value=True), \
             patch.object(continuation_stop, "observed_wake", return_value=True):
            self.assertIn("working without", self.call())

    def test_complete_uses_canonical_completion_check(self):
        self.goal.write_text(
            "# Goal\n\n```completion\n"
            + json.dumps({"outcome": "done", "acceptance": [{"id": "a", "criterion": "done", "evidence": [{"source": "test", "result": "pass"}], "owner": "", "next_action": ""}], "deliveries": [], "open_tasks": []})
            + "\n```\n",
            encoding="utf-8",
        )
        self.write_owner(self.owner("complete"))
        self.assertIsNone(self.call())
        self.goal.write_text("# Goal\n", encoding="utf-8")
        self.assertIn("completion check", self.call())

    def test_typed_blocker_and_explicit_pause_allow_stop(self):
        self.goal.write_text("## Next Steps\n\nBlocked: external\nBlocked by: approval\nUnblock action: approve\nResume when: approved\n", encoding="utf-8")
        self.write_owner(self.owner("blocked", reason="approval-needed", pr=7))
        self.assertIsNone(self.call())
        self.write_owner(self.owner())
        self.assertIsNone(self.call(self.receipt(prompt="Please pause this work.")))
        self.assertIsNotNone(self.call(self.receipt(prompt="Why did it stop?\n```text\nstop\n```")))

    def test_old_completed_owner_cannot_satisfy_new_execution_obligation(self):
        self.write_owner(self.owner("complete", updated_at=1))
        self.assertIn("no current continuation owner", self.call(self.receipt(execution_obligation_at=2)))

    def test_headless_supervisor_receipt_is_allowed(self):
        result = self.root / "result.json"
        self.write_owner(self.owner("working", launch_nonce="nonce", result_path=str(result)))
        with patch.dict(os.environ, {"CONTINUATION_OWNER_ID": "owner", "CONTINUATION_NONCE": "nonce", "CONTINUATION_RESULT_PATH": str(result)}, clear=False):
            self.assertIsNone(self.call())
        with patch.dict(os.environ, {"CONTINUATION_OWNER_ID": "owner", "CONTINUATION_NONCE": "wrong", "CONTINUATION_RESULT_PATH": str(result)}, clear=False):
            self.assertIn("working without", self.call())

    def test_no_receipt_active_binding_and_repeated_stop_still_block(self):
        binding = self.root / ".agents/persistent-workflow-binding.json"
        binding.parent.mkdir(exist_ok=True)
        binding.write_text("{}", encoding="utf-8")
        with patch.object(continuation_stop, "binding_active", return_value=True):
            self.assertIn("Initialize persistent-workflow", self.call({}))
        self.assertIn("continuation owner", self.call())
        payload = {**self.payload(), "stop_hook_active": True}
        with patch.object(continuation_stop, "read_receipt", return_value=self.receipt()):
            self.assertIn("continuation owner", continuation_stop.outcome(payload))

    def test_stale_binding_blocks_an_active_owner(self):
        self.write_owner(self.owner())
        with patch.object(continuation_stop, "binding_active", side_effect=RuntimeError("binding-head-changed")):
            self.assertIn("binding-head-changed", self.call())

    def test_foreign_owner_file_cannot_satisfy_this_worktree_obligation(self):
        self.write_owner(self.owner(worktree=str(self.root.parent / "other")))
        self.assertIn("owner-worktree-changed", self.call())

    def test_quick_and_planning_only_receipts_do_not_create_an_obligation(self):
        self.assertIsNone(self.call({"worktree": str(self.root.resolve()), "routed_at": 1, "prompt": "Fix a typo."}))
        self.assertIsNone(self.call({"worktree": str(self.root.resolve()), "routed_at": 1, "prompt": "Planning only: revise the plan."}))

    def test_unrelated_read_only_session_does_not_adopt_another_foreground_owner(self):
        self.write_owner(self.owner("working", foreground={"pid": 1}))
        self.assertIsNone(self.call({"worktree": str(self.root.resolve()), "routed_at": 1, "prompt": "Review this diff only."}))

    def test_unrouted_owner_process_still_blocks_and_pid_reuse_does_not(self):
        workflows = continuation_stop.workflow_root()
        runtime = continuation_stop.module("continuation_runtime", workflows)
        receipt = {"worktree": str(self.root.resolve()), "routed_at": 1, "prompt": "Go."}
        self.write_owner(self.owner("working", foreground={"pid": os.getpid(), "identity": runtime.process_identity(os.getpid())}))
        self.assertIn("foreground ownership", self.call(receipt))
        self.write_owner(self.owner("working", foreground={"pid": os.getpid(), "identity": "reused"}))
        self.assertIsNone(self.call(receipt))

    def test_both_host_manifests_ship_the_dedicated_stop_gate(self):
        for host in ("codex", "claude"):
            manifest = json.loads((ROOT / f".agents/plugins/manifests/{host}/engineering-hooks.json").read_text(encoding="utf-8"))
            self.assertIn("continuation_stop.py", json.dumps(manifest["hooks"]["Stop"]))
        sources = json.loads((ROOT / ".agents/plugins/sources.json").read_text(encoding="utf-8"))
        harness = json.loads((ROOT / ".agents/plugins/harness/engineering.json").read_text(encoding="utf-8"))
        self.assertIn(
            {"plugin": "engineering", "source": ".agents/hooks/continuation_stop.py", "destination": "hooks/continuation_stop.py"},
            sources["resources"],
        )
        self.assertIn(
            {"path": "hooks/continuation_stop.py", "hosts": ["claude", "codex"]},
            harness["requires"]["hooks"],
        )

    def test_route_receipt_latches_execution_across_status_and_planning_scope(self):
        scratch = Path(self.temp.name) / "scratch"
        scratch.mkdir()
        with patch.object(workflow_route.tempfile, "gettempdir", return_value=str(scratch)), \
             patch.object(workflow_route.time, "time", side_effect=(1, 2, 3, 4)):
            workflow_route.record_receipt("route", cwd=self.root, execution_obligation=True, prompt="Execute")
            first = workflow_route.read_receipt("route")
            workflow_route.record_receipt("route", cwd=self.root, prompt="Status?")
            status = workflow_route.read_receipt("route")
            workflow_route.record_receipt("route", cwd=self.root, suspend_execution=True, prompt="Planning only")
            planning = workflow_route.read_receipt("route")
            workflow_route.record_receipt("route", cwd=self.root, execution_obligation=True, prompt="Resume execution")
            resumed = workflow_route.read_receipt("route")
        self.assertEqual(1, first["execution_obligation_at"])
        self.assertEqual(1, status["execution_obligation_at"])
        self.assertTrue(planning["execution_suspended"])
        self.assertEqual(4, resumed["execution_obligation_at"])
        self.assertNotIn("execution_suspended", resumed)

    def test_source_and_generated_stop_hooks_block_a_routed_missing_owner(self):
        scratch = Path(self.temp.name) / "receipt"
        receipt = scratch / "agents-workflow-route" / (workflow_route.hashlib.sha256(self.session.encode("utf-8")).hexdigest() + ".json")
        receipt.parent.mkdir(parents=True)
        receipt.write_text(json.dumps(self.receipt()), encoding="utf-8")
        payload = json.dumps(self.payload())
        environment = dict(os.environ, TEMP=str(scratch), TMP=str(scratch), TMPDIR=str(scratch))
        scripts = (SCRIPT, ROOT / "plugins/engineering/hooks/continuation_stop.py")
        for script in scripts:
            with self.subTest(script=script):
                result = subprocess.run([sys.executable, "-B", str(script)], input=payload,
                                        capture_output=True, text=True, cwd=self.root, env=environment, timeout=20)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("block", json.loads(result.stdout)["decision"])


if __name__ == "__main__":
    unittest.main()
