import importlib.util
import io
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
import continuation_receipts


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
        with patch.object(continuation_stop, "read_receipt", return_value=receipt if receipt is not None else self.receipt()):
            return continuation_stop.outcome(self.payload())

    def assert_unreadable_artifact_blocks(self, path):
        original_read = Path.read_text

        def unreadable(candidate, *args, **kwargs):
            if candidate.resolve() == path.resolve():
                raise PermissionError("unreadable")
            return original_read(candidate, *args, **kwargs)

        with patch.object(Path, "read_text", side_effect=unreadable, autospec=True):
            self.assertIn("unreadable", self.call({}))

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
            for _ in range(2):
                self.assertIn("Continue authorized unblocked work", self.call())
                self.assertIn("Close the CLI when the goal is verified complete", self.call())

    def test_scheduler_receipt_uses_shared_read_only_verifier(self):
        owner = self.owner()
        path = self.root / ".agents/continuation/owner.json"
        path.parent.mkdir(parents=True)
        receipt = {
            "owner_id": owner["owner_id"], "owner_path": str(path), "worktree": str(self.root),
            "task_name": "task", "task_path": "\\", "description": "owner", "execute": "powershell.exe",
            "arguments": "wake", "helper": "helper", "python": "python", "script": "script",
        }
        (path.parent / "scheduler.json").write_text(json.dumps(receipt), encoding="utf-8")
        verifier = Mock()
        verifier.verify_receipt.return_value = True
        with patch.object(continuation_stop, "module", return_value=verifier):
            self.assertTrue(continuation_stop.scheduler_ready(path, owner, self.root.resolve()))
        verifier.verify_receipt.return_value = False
        with patch.object(continuation_stop, "module", return_value=verifier):
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

    def test_complete_allows_pending_cleanup_for_both_hosts(self):
        self.goal.write_text(
            "# Goal\n\n```completion\n"
            + json.dumps({"outcome": "done", "acceptance": [{"id": "a", "criterion": "done", "evidence": [{"source": "test", "result": "pass"}], "owner": "", "next_action": ""}], "deliveries": [], "open_tasks": []})
            + "\n```\n",
            encoding="utf-8",
        )
        state = tempfile.TemporaryDirectory()
        self.addCleanup(state.cleanup)
        obligations = Path(state.name) / "merge-cleanup" / "obligations"
        obligations.mkdir(parents=True)
        obligations.joinpath("own.json").write_text(json.dumps({
            "worktree": str(self.root),
            "session_exit_required": True,
            "checkout_retained": True,
            "disposition": {"status": "pending", "reason": "keep-open"},
        }), encoding="utf-8")
        with patch.dict(os.environ, {"AGENT_STATE_DIRECTORY": state.name}):
            for host in ("codex", "claude"):
                with self.subTest(host=host):
                    self.write_owner(self.owner("complete", harness=host))
                    self.assertIsNone(self.call())

    def test_complete_requires_fresh_report_readiness_despite_owner_snapshot(self):
        workflows = continuation_stop.workflow_root()
        completion = continuation_stop.module("completion", workflows)
        self.write_owner(self.owner("complete", completion_snapshot={
            "report_ready": True,
            "ready": True,
            "cleanup_status": "verified",
            "pending_cleanup": [],
        }))
        for report_ready in (False, None):
            with self.subTest(report_ready=report_ready), \
                 patch.object(completion, "completion_check", return_value={"report_ready": report_ready,
                                                                              "ready": True, "blockers": []}):
                self.assertIn("Completion is not verified", self.call())

    def test_typed_blocker_and_explicit_pause_allow_stop(self):
        self.write_owner(self.owner("blocked", reason="approval-needed", pr=7))
        self.assertIsNone(self.call())
        self.write_owner(self.owner())
        for prompt in ("Please pause this work.", "Cancel it.", "Cancel this."):
            self.assertIsNone(self.call(self.receipt(prompt=prompt)))
        self.assertIsNotNone(self.call(self.receipt(prompt="Why did it stop?\n```text\nstop\n```")))

    def test_documented_blocker_needs_only_a_reason_and_next_action(self):
        self.goal.write_text("# Goal\n", encoding="utf-8")
        self.assertTrue(continuation_stop.documented_blocker(self.owner("blocked")))
        for key in ("reason", "next_action"):
            for value in ("", "  ", None):
                with self.subTest(key=key, value=value):
                    self.assertFalse(continuation_stop.documented_blocker(self.owner("blocked", **{key: value})))

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

    def isolated_state(self):
        state = tempfile.TemporaryDirectory()
        self.addCleanup(state.cleanup)
        patcher = patch.dict(os.environ, {"AGENT_STATE_DIRECTORY": state.name})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_a_stop_is_blocked_once_and_its_own_retry_is_released_even_with_new_wording(self):
        self.isolated_state()
        first = {"session_id": "once"}
        for flag in ("stop_hook_active", "stopHookActive"):
            with self.subTest(flag=flag):
                self.assertEqual("reason", continuation_stop.once_per_stop(first, "reason"))
                self.assertIsNone(continuation_stop.once_per_stop({**first, flag: True}, "reworded: error 2"))
                self.assertEqual("reason", continuation_stop.once_per_stop(first, "reason"))
                continuation_stop.once_per_stop(first, None)

    def test_another_gates_block_does_not_release_this_gate(self):
        self.isolated_state()
        retry = {"session_id": "other", "stop_hook_active": True}

        self.assertEqual("reason", continuation_stop.once_per_stop(retry, "reason"))
        for _ in range(3):
            self.assertIsNone(continuation_stop.once_per_stop(retry, "reason"))

    def test_expired_block_records_are_pruned(self):
        self.isolated_state()
        stale = continuation_stop.block_record("stale")
        stale.parent.mkdir(parents=True)
        stale.write_text("{}", encoding="utf-8")
        old = continuation_stop.time.time() - continuation_stop.BLOCK_RETENTION_SECONDS - 60
        os.utime(stale, (old, old))

        continuation_stop.once_per_stop({"session_id": "fresh"}, "reason")

        self.assertFalse(stale.exists())
        self.assertTrue(continuation_stop.block_record("fresh").exists())

    def test_an_unwritable_block_record_never_loops(self):
        self.isolated_state()
        session = {"session_id": "unwritable"}
        with patch.object(Path, "write_text", side_effect=PermissionError("shared tmp")):
            self.assertEqual("reason", continuation_stop.once_per_stop(session, "reason"))
            self.assertIsNone(continuation_stop.once_per_stop({**session, "stop_hook_active": True}, "reason"))

    def test_invalid_owner_artifacts_block_unrouted_stop(self):
        path = self.root / ".agents/continuation/owner.json"
        path.parent.mkdir(parents=True)
        for payload in (b"{", b"\xff", b"[]"):
            with self.subTest(payload=payload):
                path.write_bytes(payload)
                self.assertIn("cannot read JSON artifact", self.call({}))
        self.assert_unreadable_artifact_blocks(path)

    def test_invalid_binding_artifacts_block_unrouted_stop(self):
        path = self.root / ".agents/persistent-workflow-binding.json"
        path.parent.mkdir(exist_ok=True)
        for payload in (b"{", b"\xff", b"[]"):
            with self.subTest(payload=payload):
                path.write_bytes(payload)
                self.assertIn("cannot read JSON artifact", self.call({}))
        self.assert_unreadable_artifact_blocks(path)

    def test_pause_precedes_invalid_continuation_artifacts(self):
        path = self.root / ".agents/continuation/owner.json"
        path.parent.mkdir(parents=True)
        path.write_text("{", encoding="utf-8")
        self.assertIsNone(self.call(self.receipt(prompt="Pause.")))

    def test_stale_binding_blocks_an_active_owner(self):
        self.write_owner(self.owner())
        with patch.object(continuation_stop, "binding_active", side_effect=RuntimeError("binding-head-changed")):
            self.assertIn("binding-head-changed", self.call())

    def test_binding_active_compares_the_normalized_repository_key(self):
        runtime = Mock()
        runtime.binding_from_artifact.return_value = {
            "repository": "tj-agents/core",
            "worktree": str(self.root.resolve()),
            "branch": "Fix/Example",
            "remote_head_sha": "a" * 40,
        }
        runtime.identity.return_value = {
            "repo": "tj-agents/core",
            "worktree": str(self.root.resolve()),
            "branch": "Fix/Example",
            "head": "a" * 40,
        }
        self.assertTrue(continuation_stop.binding_active(runtime, self.root, {}))

    def test_binding_active_rejects_a_different_bound_head(self):
        runtime = Mock()
        runtime.binding_from_artifact.return_value = {
            "repository": "tj-agents/core",
            "worktree": str(self.root.resolve()),
            "branch": "Fix/Example",
            "remote_head_sha": "a" * 40,
        }
        runtime.identity.return_value = {
            "repo": "tj-agents/core",
            "worktree": str(self.root.resolve()),
            "branch": "Fix/Example",
            "head": "b" * 40,
        }
        with self.assertRaisesRegex(RuntimeError, "binding-head-changed"):
            continuation_stop.binding_active(runtime, self.root, {})

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

    def test_foreground_association_requires_the_nearest_cli_owner(self):
        lease = {"pid": 111, "identity": "identity"}
        owner = {"foreground": lease}
        runtime = Mock(process_identity=Mock(return_value="identity"))
        with patch.object(continuation_stop, "WINDOWS", True), \
             patch.object(continuation_stop.subprocess, "run", return_value=Mock(returncode=0)) as run:
            self.assertTrue(continuation_stop.foreground_owns_current_process(owner, runtime))
            self.assertIn("ExecutablePath", run.call_args.args[0][-1])
        with patch.object(continuation_stop, "WINDOWS", True), \
             patch.object(continuation_stop.subprocess, "run", return_value=Mock(returncode=1)):
            self.assertFalse(continuation_stop.foreground_owns_current_process(owner, runtime))
        with patch.object(continuation_stop, "WINDOWS", False), \
             patch.object(continuation_stop.os, "getpid", return_value=333), \
             patch.object(continuation_stop.os, "readlink", side_effect=lambda path: {
                 "/proc/111/exe": "codex", "/proc/333/exe": "hook",
             }[path]), \
             patch.object(Path, "read_text", return_value="x) S 111 0"):
            self.assertTrue(continuation_stop.foreground_owns_current_process(owner, runtime))
        with patch.object(continuation_stop, "WINDOWS", False), \
             patch.object(continuation_stop.os, "getpid", return_value=333), \
             patch.object(continuation_stop.os, "readlink", side_effect=lambda path: {
                 "/proc/111/exe": "codex", "/proc/333/exe": "hook", "/proc/222/exe": "codex",
             }[path]), \
             patch.object(Path, "read_text", side_effect=("x) S 222 0", "x) S 111 0")):
            self.assertFalse(continuation_stop.foreground_owns_current_process(owner, runtime))
        with patch.object(continuation_stop, "WINDOWS", False), \
             patch.object(continuation_stop.os, "readlink", side_effect=OSError("missing")):
            self.assertFalse(continuation_stop.foreground_owns_current_process(owner, runtime))
        runtime.process_identity.return_value = "foreign"
        self.assertFalse(continuation_stop.foreground_owns_current_process(owner, runtime))

    def test_binding_active_reads_the_head_through_real_artifact_normalization(self):
        workflows = continuation_stop.workflow_root()
        if str(workflows) not in sys.path:
            sys.path.insert(0, str(workflows))
        runtime = continuation_stop.module("continuation_runtime", workflows)
        root = self.root.resolve()
        current = runtime.identity(root)
        artifact = {
            "repo": current["repo"], "pr": 42, "pr_url": f"https://github.com/{current['repo']}/pull/42",
            "branch": current["branch"], "worktree": current["worktree"], "head": current["head"],
            "pending_evidence": [], "review": {"work_order": "review", "work_order_order": ["review"], "reviewed_sha": None},
            "merge_authorization": {"mode": "absent", "instruction": None}, "completion_condition": "Boundary recorded",
        }
        path = root / runtime.BINDING_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(artifact), encoding="utf-8")
        self.assertTrue(continuation_stop.binding_active(runtime, root))
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-q",
                        "--allow-empty", "-m", "advance"], cwd=root, check=True)
        with self.assertRaisesRegex(RuntimeError, "binding-head-changed"):
            continuation_stop.binding_active(runtime, root)



if __name__ == "__main__":
    unittest.main()


class ContinuationReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def test_direct_controls_and_read_only_receipts(self):
        with patch.object(continuation_receipts.tempfile, "gettempdir", return_value=self.temp.name):
            for prompt, expected in (("Pause this work.", "pause"), ("Cancel it.", "cancel"), ("stop", "stop"), ("Continue.", "continue"), ("quoted stop", None)):
                with self.subTest(prompt=prompt):
                    self.assertEqual(expected, continuation_receipts.direct_control(prompt))
            path = continuation_receipts.receipt_path("session")
            path.parent.mkdir()
            path.write_text(json.dumps({"worktree": "/work", "execution_suspended": True}), encoding="utf-8")
            self.assertEqual({"worktree": "/work", "execution_suspended": True}, continuation_receipts.read_receipt("session"))
            path.write_text("[]", encoding="utf-8")
            self.assertEqual({}, continuation_receipts.read_receipt("session"))
            path.unlink()
            self.assertEqual({}, continuation_receipts.read_receipt("session"))

    def test_receipt_paths_are_exact_session_isolated(self):
        with patch.object(continuation_receipts.tempfile, "gettempdir", return_value=self.temp.name):
            first = continuation_receipts.receipt_path("first")
            second = continuation_receipts.receipt_path("second")
            self.assertNotEqual(first, second)
            self.assertEqual(first.parent, second.parent)
