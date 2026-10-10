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
        for prompt in ("Please pause this work.", "Cancel it.", "Cancel this."):
            self.assertIsNone(self.call(self.receipt(prompt=prompt)))
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

    def test_read_only_questions_do_not_create_or_resume_an_execution_obligation(self):
        scratch = Path(self.temp.name) / "receipt-questions"
        scratch.mkdir()
        prompts = (
            "How does plan-execution work?",
            "Why didn't you finish the plan?",
            "Explain how to implement the plan.",
        )
        with patch.object(workflow_route.tempfile, "gettempdir", return_value=str(scratch)):
            for prompt in prompts:
                with self.subTest(prompt=prompt):
                    payload = json.dumps({"hook_event_name": "UserPromptSubmit", "cwd": str(self.root),
                                          "session_id": self.session, "prompt": prompt})
                    with patch.object(sys, "stdin", io.StringIO(payload)), patch.object(sys, "stdout", io.StringIO()):
                        self.assertEqual(0, workflow_route.main())
                    receipt = workflow_route.read_receipt(self.session)
                    self.assertIsNot(receipt.get("execution_obligation"), True)
                    self.assertIsNone(continuation_stop.outcome(self.payload()))
            workflow_route.record_receipt(self.session, cwd=self.root, execution_obligation=True)
            workflow_route.record_receipt(self.session, cwd=self.root, suspend_execution=True, prompt="Pause.")
            for prompt in prompts:
                payload = json.dumps({"hook_event_name": "UserPromptSubmit", "cwd": str(self.root),
                                      "session_id": self.session, "prompt": prompt})
                with patch.object(sys, "stdin", io.StringIO(payload)), patch.object(sys, "stdout", io.StringIO()):
                    self.assertEqual(0, workflow_route.main())
                receipt = workflow_route.read_receipt(self.session)
                self.assertTrue(receipt["execution_suspended"])
                self.assertIsNone(continuation_stop.outcome(self.payload()))

    def test_both_host_manifests_ship_the_shared_stop_gate(self):
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

    def test_pause_persists_across_prompts_until_explicit_resume(self):
        scratch = Path(self.temp.name) / "controls"
        scratch.mkdir()
        with patch.object(workflow_route.tempfile, "gettempdir", return_value=str(scratch)):
            for previous_obligation in (False, True):
                session = f"controls-{previous_obligation}"
                workflow_route.record_receipt(session, cwd=self.root, execution_obligation=previous_obligation)
                for prompt in ("Cancel it.", "Cancel this.", "Please pause this work."):
                    control = workflow_route.direct_control(prompt)
                    self.assertIn(control, {"pause", "cancel"})
                    workflow_route.record_receipt(session, cwd=self.root, suspend_execution=True, prompt=prompt)
                    workflow_route.record_receipt(session, cwd=self.root, prompt="Status?")
                    receipt = workflow_route.read_receipt(session)
                    self.assertTrue(receipt["execution_suspended"])
                    with patch.object(continuation_stop, "read_receipt", return_value=receipt):
                        self.assertIsNone(continuation_stop.outcome({**self.payload(), "session_id": session}))
                    workflow_route.record_receipt(session, cwd=self.root, prompt="Continue.", resume_execution=True)
                    self.assertFalse(workflow_route.read_receipt(session)["execution_suspended"])

    def test_prompt_hook_persists_cancel_and_resumes_the_existing_obligation(self):
        scratch = Path(self.temp.name) / "prompt-controls"
        scratch.mkdir()
        with patch.object(workflow_route.tempfile, "gettempdir", return_value=str(scratch)):
            workflow_route.record_receipt(self.session, cwd=self.root, execution_obligation=True)
            for prompt in ("Cancel it.", "Status?", "Continue."):
                payload = json.dumps({"hook_event_name": "UserPromptSubmit", "cwd": str(self.root), "session_id": self.session, "prompt": prompt})
                with patch.object(sys, "stdin", io.StringIO(payload)), patch.object(sys, "stdout", io.StringIO()):
                    self.assertEqual(0, workflow_route.main())
                receipt = workflow_route.read_receipt(self.session)
                with patch.object(continuation_stop, "read_receipt", return_value=receipt):
                    result = continuation_stop.outcome(self.payload())
                if prompt == "Continue.":
                    self.assertIsNotNone(result)
                else:
                    self.assertTrue(receipt["execution_suspended"])
                    self.assertIsNone(result)

    def test_control_commands_do_not_adopt_quoted_text_or_other_worktrees(self):
        for prompt in ('"Cancel it."', "Why did it stop?", "Continue? What does that mean?", "```text\nstop\n```", "The log says cancel this."):
            self.assertIsNone(workflow_route.direct_control(prompt))
        scratch = Path(self.temp.name) / "isolation"
        scratch.mkdir()
        with patch.object(workflow_route.tempfile, "gettempdir", return_value=str(scratch)):
            workflow_route.record_receipt("isolated", cwd=self.root, suspend_execution=True, prompt="Pause.")
            workflow_route.record_receipt("isolated", cwd=self.root.parent, prompt="Status?")
            self.assertNotIn("execution_suspended", workflow_route.read_receipt("isolated"))

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
        package = ROOT / "plugins/engineering"
        manifest = json.loads((package / "hooks/claude.json").read_text(encoding="utf-8"))
        hooks = [hook for group in manifest["hooks"]["Stop"] for hook in group["hooks"]]
        self.assertEqual(1, len(hooks))
        args = [value.replace("${CLAUDE_PLUGIN_ROOT}", str(package)) for value in hooks[0]["args"]]
        result = subprocess.run([sys.executable, *args], input=payload, capture_output=True, text=True,
                                cwd=self.root, env=environment, timeout=hooks[0]["timeout"])
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("block", json.loads(result.stdout)["decision"])
        self.assertIn("persistent-workflow", json.loads(result.stdout)["reason"])



if __name__ == "__main__":
    unittest.main()
