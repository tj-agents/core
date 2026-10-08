import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / ".agents/workflows/continuation_runtime.py"
WORKFLOWS = RUNTIME.parent
FIXTURE = Path(__file__).parent / "fixtures/continuation_fixture.py"
RUNTIME_FIXTURE = Path(__file__).parent / "fixtures/continuation_runtime_fixture.py"
sys.path.insert(0, str(RUNTIME.parent))
spec = importlib.util.spec_from_file_location("continuation_runtime", RUNTIME)
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        for args in (["init", "-b", "feature"], ["config", "user.name", "Fixture"],
                     ["config", "user.email", "fixture@example.invalid"],
                     ["remote", "add", "origin", "https://github.com/example/test.git"]):
            self.git(*args)
        self.write_completion_goal()
        self.git("add", "goal.md")
        self.git("commit", "-m", "Initial")
        self.owner = self.root / ".agents/continuation/owner.json"
        self.fixture("complete")
        self.init()
        self.processes = []

    def tearDown(self):
        for process in self.processes:
            if process.poll() is None:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
                else:
                    process.kill()
                process.wait()
            for stream in (process.stdout, process.stderr):
                if stream:
                    stream.close()
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, text=True, stderr=subprocess.DEVNULL).strip()

    def init(self, *extra):
        return self.cli("init", "--root", str(self.root), "--goal", "goal.md",
                        "--completion", "CI repaired and boundary recorded", "--authority", "Isolated test",
                        "--harness", "codex", "--actions", "edit", "test", *extra)

    def write_completion_goal(self, deliveries=None, evidence=None):
        document = {
            "outcome": "The fixture records a verified completion boundary.",
            "acceptance": [{
                "id": "fixture",
                "criterion": "The focused continuation fixture completed.",
                "evidence": [{"source": "fixture", "result": "passed"}] if evidence is None else evidence,
                "owner": "fixture owner",
                "next_action": "None.",
            }],
            "deliveries": deliveries or [],
            "open_tasks": [],
        }
        (self.root / "goal.md").write_text("```completion\n" + json.dumps(document) + "\n```\n")

    def cli(self, *args, code=0, env=None):
        result = subprocess.run([sys.executable, str(RUNTIME_FIXTURE), *args], capture_output=True,
                                text=True, timeout=30, env=env)
        self.assertEqual(result.returncode, code, result.stderr + result.stdout)
        return json.loads(result.stdout)

    def state(self):
        return json.loads(self.owner.read_text())

    def fixture(self, mode, **extra):
        (self.root / "scenario.json").write_text(json.dumps({"mode": mode, **extra}))

    def wake_args(self):
        return ["wake", "--owner", str(self.owner), "--observer-command", sys.executable,
                str(FIXTURE), "observer", "--host-command", sys.executable, str(FIXTURE), "host"]

    def wake(self, env=None):
        return self.cli(*self.wake_args(), env=env)

    def binding(self, status="IN_PROGRESS", conclusion=None):
        state = self.state()
        binding = {key: state[key] for key in ("repo", "worktree", "branch", "head")}
        binding.update(pr=42, pr_url="https://github.com/example/test/pull/42",
                       pending_evidence=[], review={"work_order": "review", "work_order_order": ["review"], "reviewed_sha": None},
                       merge_authorization={"mode": "absent", "instruction": None}, completion_condition="Boundary recorded")
        (self.root / ".agents/persistent-workflow-binding.json").write_text(json.dumps(binding))
        self.write_completion_goal([{"repository": state["repo"], "pr": 42, "head": state["head"]}])
        self.observation(status, conclusion)

    def observation(self, status, conclusion=None):
        binding = json.loads((self.root / ".agents/persistent-workflow-binding.json").read_text())
        value = {"number": 42, "headRefName": "feature", "headRefOid": binding["head"],
                 "url": "https://github.com/example/test/pull/42", "state": "OPEN",
                 "statusCheckRollup": [{"name": "CI", "status": status, "conclusion": conclusion}]}
        (self.root / "observation.json").write_text(json.dumps(value))

    def start(self, *args):
        process = subprocess.Popen([sys.executable, str(RUNTIME_FIXTURE), *args], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
        self.processes.append(process)
        return process

    def wait_for(self, predicate):
        until = time.monotonic() + 10
        while time.monotonic() < until:
            if predicate():
                return
            time.sleep(0.05)
        self.fail("fixture did not reach expected subprocess boundary")

    def test_unverified_complete_receipt_preserves_active_owner(self):
        state = self.state()
        state.update(launch_nonce="fixture", state="working", reason="headless-launch", next_action="Verify outcome")
        receipt = {"nonce": "fixture", "owner_id": state["owner_id"], "state": "complete", "reason": "Done"}
        before = dict(state)
        binding = {"repository": state["repo"], "pr": 42, "head": state["head"]}
        with mock.patch.object(runtime, "identity", return_value={key: state[key] for key in ("repo", "worktree", "branch", "head")}), \
             mock.patch.object(runtime, "check_identity", return_value=binding), \
             mock.patch.object(runtime, "completion_check", return_value={"ready": False, "blockers": ["missing observation"]}):
            with self.assertRaisesRegex(runtime.Gate, "completion-unverified"):
                runtime.apply_receipt(state, receipt)
        self.assertEqual(before, state)

    def test_released_receipt_cannot_substitute_another_delivery(self):
        state = self.state()
        state.update(pr=42, launch_nonce="fixture")
        delivery = {"repository": state["repo"], "pr": 43, "head": state["head"]}
        self.write_completion_goal([delivery])
        receipt = {"owner_id": state["owner_id"], "nonce": "fixture", "state": "complete",
                   "reason": "Done", "released_binding": delivery}
        with mock.patch.object(runtime, "identity", return_value={key: state[key] for key in ("repo", "worktree", "branch", "head")}), \
             mock.patch.object(runtime, "check_identity", return_value=None), \
             mock.patch("completion.forge_state", return_value={"number": 43, "headRefOid": state["head"], "state": "MERGED", "body": ""}):
            with self.assertRaisesRegex(runtime.Gate, "bound delivery is absent"):
                runtime.apply_receipt(state, receipt)

    def test_child_complete_receipt_keeps_owner_when_bound_delivery_is_omitted(self):
        self.binding("COMPLETED", "SUCCESS")
        self.write_completion_goal()
        before = self.state()
        self.cli(*self.wake_args())
        after = self.state()
        self.assertEqual(before["owner_id"], after["owner_id"])
        self.assertEqual("blocked", after["state"])
        self.assertIn("completion-unverified: bound delivery is absent", after["reason"])

    def test_foreground_complete_checkpoint_preserves_claim_on_missing_evidence(self):
        self.write_completion_goal(evidence=[])
        claimed = self.cli("claim", "--owner", str(self.owner), "--pid", str(os.getpid()))
        token = claimed["foreground"]["token"]
        result = self.cli("checkpoint", "--owner", str(self.owner), "--token", token,
                          "--state", "complete", "--reason", "Fixture completion", code=2)
        after = self.state()
        self.assertEqual("working", after["state"])
        self.assertEqual(token, after["foreground"]["token"])
        self.assertEqual(claimed["reason"], after["reason"])
        self.assertIn("completion-unverified: acceptance fixture lacks evidence", result["reason"])

    def test_parent_exit_delayed_failure_repair_success_complete(self):
        self.binding()
        parent = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        self.processes.append(parent)
        claimed = self.cli("claim", "--owner", str(self.owner), "--pid", str(parent.pid))
        self.assertEqual(self.wake()["launches"], 0)
        parent.kill()
        parent.wait()
        self.assertEqual(self.wake()["launches"], 0)
        self.fixture("repair")
        self.observation("COMPLETED", "FAILURE")
        old_head = self.state()["head"]
        repaired = self.wake()
        self.assertEqual(repaired["state"], "waiting")
        self.assertNotEqual(old_head, repaired["head"])
        self.assertEqual(repaired["launches"], 1)
        self.assertEqual(self.wake()["launches"], 1)
        self.fixture("complete")
        self.observation("COMPLETED", "SUCCESS")
        final = self.wake()
        self.assertEqual(final["state"], "complete")
        self.assertEqual(final["launches"], 2)
        self.assertTrue(Path(final["last_result"]).exists())
        self.assertEqual(self.wake()["launches"], 2)

    def test_real_child_supervisor_boundary_suppresses_bytecode_without_ambient_env(self):
        pycache = WORKFLOWS / "__pycache__"
        if pycache.exists():
            shutil.rmtree(pycache)
        env = {key: value for key, value in os.environ.items()
               if key not in {"PYTHONDONTWRITEBYTECODE", "PYTHONPYCACHEPREFIX"}}
        try:
            result = self.wake(env=env)
            self.assertEqual(result["state"], "complete")
            self.assertEqual([], list(WORKFLOWS.rglob("*.pyc")))
        finally:
            if pycache.exists():
                shutil.rmtree(pycache)

    def test_duplicate_wakes_kernel_lock_and_child(self):
        self.fixture("complete", sleep=6)
        first = self.start(*self.wake_args())
        self.wait_for(lambda: (self.root / "host-started").exists())
        duplicate = self.wake()
        self.assertEqual(duplicate["reason"], "owner-lock-busy")
        stdout, stderr = first.communicate(timeout=10)
        self.assertEqual(first.returncode, 0, stderr)
        self.assertEqual(json.loads(stdout)["launches"], 1)

    def test_fresh_and_stale_foreground(self):
        claimed = self.cli("claim", "--owner", str(self.owner), "--pid", str(os.getpid()))
        token = claimed["foreground"]["token"]
        self.assertEqual(self.wake()["launches"], 0)
        self.cli("heartbeat", "--owner", str(self.owner), "--token", token)
        state = self.state()
        state["foreground"]["activity"] = time.time() - 1000
        runtime.atomic_json(self.owner, state)
        blocked = self.wake()
        self.assertEqual(blocked["reason"], "stale-live-foreground-reconciliation")
        self.assertEqual(blocked["state"], "blocked")
        self.cli("checkpoint", "--owner", str(self.owner), "--token", token,
                 "--state", "waiting", "--reason", "foreground confirmed", "--next-action", "resume")
        self.assertEqual(self.wake()["state"], "complete")

    def test_orphan_writer_gate_after_supervisor_exit(self):
        self.fixture("complete", sleep=3)
        supervisor = self.start(*self.wake_args())
        self.wait_for(lambda: (self.root / "host-started").exists())
        recorded = self.state()
        supervisor.kill()
        supervisor.wait()
        self.assertEqual(self.wake()["reason"], "interrupted-writer-still-alive")
        self.wait_for(lambda: not runtime.alive(recorded["child"]))
        self.assertEqual(self.wake()["state"], "blocked")
        self.assertEqual(self.state()["launches"], 1)

    def test_genuine_gate_and_nonce_validation(self):
        self.fixture("gate")
        final = self.wake()
        self.assertEqual(final["state"], "blocked")
        self.assertEqual(final["next_action"], "Ask for product approval")
        self.assertEqual(self.wake()["launches"], 1)

    def test_claim_requires_an_explicit_positive_pid(self):
        result = subprocess.run([sys.executable, str(RUNTIME_FIXTURE), "claim", "--owner", str(self.owner)],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(2, result.returncode)
        self.assertIn("--pid", result.stderr)
        before = self.state()
        for pid in (0, -1, None):
            with self.subTest(pid=pid), mock.patch.object(runtime, "process_identity") as process_identity:
                args = SimpleNamespace(operation="claim", pid=pid)
                with self.assertRaisesRegex(runtime.Gate, "foreground-pid-required"):
                    runtime.operate(self.owner, dict(before), args)
                process_identity.assert_not_called()
        self.assertEqual(before, self.state())

    def test_claim_pins_a_valid_host_executable_after_foreground_validation(self):
        executable = self.root / "codex.exe"
        executable.touch()
        state = self.state()
        args = SimpleNamespace(operation="claim", pid=os.getpid(), host_executable=str(executable))
        runtime.operate(self.owner, state, args)
        self.assertEqual(str(executable), state["host_executable"])
        self.assertEqual(os.getpid(), state["foreground"]["pid"])

    def test_claim_rejects_invalid_host_executable_without_mutating_owner(self):
        state = self.state()
        before = dict(state)
        args = SimpleNamespace(operation="claim", pid=os.getpid(), host_executable=str(self.root / "codex.cmd"))
        with self.assertRaisesRegex(runtime.Gate, "foreground-host-executable-invalid"):
            runtime.operate(self.owner, state, args)
        self.assertEqual(before, state)
        self.assertEqual(before, self.state())

    def test_pinned_native_host_overrides_a_path_wrapper(self):
        state = self.state()
        state["host_executable"] = str(self.root / "codex.exe")
        with mock.patch.object(runtime.shutil, "which", return_value=str(self.root / "codex.cmd")):
            command = runtime.lane_command(state, "resume")
        self.assertEqual(str(self.root / "codex.exe"), command[0])

    def test_unexplained_exit_is_bounded(self):
        self.fixture("missing")
        for attempt in range(3):
            state = self.wake()
            self.assertEqual(state["launches"], attempt + 1)
        self.assertEqual(state["state"], "blocked")
        self.assertEqual(state["reason"], "host-checkpoint-missing")

    def test_bad_nonce_is_gate(self):
        self.fixture("badnonce")
        self.assertEqual(self.wake()["reason"], "checkpoint-identity-invalid")

    def test_init_preserves_progress_limits_and_does_not_schedule(self):
        state = self.state()
        state.update(launches=2, max_launches=3, deadline=time.time() + 10)
        runtime.atomic_json(self.owner, state)
        again = self.init()
        self.assertEqual(again["launches"], 2)
        self.assertEqual(again["max_launches"], 3)
        self.assertEqual(again["deadline"], state["deadline"])
        self.assertFalse((self.owner.parent / "scheduler.json").exists())
        tightened = self.init("--max-launches", "2")
        self.assertEqual(tightened["max_launches"], 2)
        self.assertEqual(tightened["launches"], 2)
        self.assertEqual(self.init()["max_launches"], 2)

    def test_external_head_and_forge_identity_gate(self):
        self.binding("COMPLETED", "SUCCESS")
        observation = json.loads((self.root / "observation.json").read_text())
        observation["headRefOid"] = "b" * 40
        (self.root / "observation.json").write_text(json.dumps(observation))
        self.assertEqual(self.wake()["reason"], "forge-identity-changed")

    def test_unsupported_host_and_l4_no_bypass(self):
        state = self.state()
        state["harness"] = "other"
        runtime.atomic_json(self.owner, state)
        self.assertEqual(self.wake()["reason"], "unsupported-host")
        state["harness"] = "codex"
        args = runtime.lane_command(state, "test", ["fixture"])
        lane = json.loads((ROOT / ".agents/lanes/codex.json").read_text())["lanes"]["L4"]
        self.assertIn(lane["model"], args)
        self.assertIn(f'model_reasoning_effort="{lane["reasoning_effort"]}"', args)
        self.assertFalse(any("bypass" in arg for arg in args))

    def test_timeout_kills_writer_before_next_wake(self):
        state = self.state()
        state["timeout_seconds"] = 0.5
        runtime.atomic_json(self.owner, state)
        self.fixture("complete", sleep=10)
        result = self.wake()
        self.assertEqual(result["state"], "waiting")
        host_pid = int((self.root / "host-started").read_text())
        self.assertIsNone(runtime.process_identity(host_pid))

    def test_wrapper_exit_kills_host_job(self):
        self.fixture("complete", sleep=10)
        supervisor = self.start(*self.wake_args())
        self.wait_for(lambda: (self.root / "host-started").exists())
        wrapper = self.state()["child"]
        os.kill(wrapper["pid"], 9 if os.name != "nt" else 15)
        stdout, stderr = supervisor.communicate(timeout=10)
        self.assertEqual(supervisor.returncode, 0, stderr)
        self.assertEqual(json.loads(stdout)["state"], "waiting")
        host_pid = int((self.root / "host-started").read_text())
        self.wait_for(lambda: runtime.process_identity(host_pid) is None)
        self.fixture("complete")
        self.assertEqual(self.wake()["state"], "complete")

    def test_unsupported_model_is_one_capability_gate(self):
        self.fixture("unsupported")
        state = self.wake()
        self.assertEqual(state["reason"], "host-capability-or-permission-unavailable")
        self.assertEqual(state["state"], "blocked")
        self.assertEqual(self.wake()["launches"], 1)

    def test_foreground_rebind_before_pr_and_external_change_gate(self):
        claimed = self.cli("claim", "--owner", str(self.owner), "--pid", str(os.getpid()))
        old = {key: claimed[key] for key in ("repo", "worktree", "branch", "head")}
        (self.root / "foreground.txt").write_text("authorized work")
        self.git("add", "foreground.txt")
        self.git("commit", "-m", "Foreground work")
        new = dict(old, head=self.git("rev-parse", "HEAD"))
        rebind = self.root / "rebind.json"
        rebind.write_text(json.dumps({"old": old, "new": new}))
        result = self.cli("checkpoint", "--owner", str(self.owner), "--token", claimed["foreground"]["token"],
                          "--state", "waiting", "--reason", "foreground repair", "--next-action", "resume",
                          "--rebind", str(rebind))
        self.assertEqual(result["head"], new["head"])
        self.git("commit", "--allow-empty", "-m", "External replacement")
        self.assertEqual(self.wake()["reason"], "owner-head-changed")

    def test_deadline_is_terminal_and_canonical_goal_required(self):
        state = self.state()
        state["deadline"] = time.time() - 1
        runtime.atomic_json(self.owner, state)
        self.assertEqual(self.wake()["reason"], "continuation-budget-exhausted")
        result = self.cli("init", "--root", str(self.root), "--goal", "missing.md", "--completion", "done",
                          "--authority", "test", "--harness", "codex", "--actions", "test", code=2)
        self.assertTrue(result["reason"].startswith("canonical-goal-file-required:"))

    def test_absolute_external_goal_survives_claim_yield_repair_and_wake(self):
        with tempfile.TemporaryDirectory() as external:
            goal = Path(external).resolve() / "canonical goal.md"
            goal.write_text("Merge the approved PR after exact-head review and checks")
            self.owner.unlink()
            initialized = self.init("--goal", str(goal))
            self.assertEqual(initialized["goal"], str(goal))
            self.binding()
            goal.write_text((self.root / "goal.md").read_text())
            binding_path = self.root / ".agents/persistent-workflow-binding.json"
            binding = json.loads(binding_path.read_text())
            binding["merge_authorization"] = {"mode": "merge", "instruction": "Merge this PR when reviewed and green"}
            binding_path.write_text(json.dumps(binding))
            claimed = self.cli("claim", "--owner", str(self.owner), "--pid", str(os.getpid()))
            self.assertEqual(self.wake()["launches"], 0)
            self.cli("yield", "--owner", str(self.owner), "--token", claimed["foreground"]["token"])
            self.assertEqual(self.wake()["launches"], 0)
            self.fixture("repair")
            self.observation("COMPLETED", "FAILURE")
            repaired = self.wake()
            self.assertEqual(repaired["state"], "waiting")
            self.assertEqual(repaired["goal"], str(goal))
            self.assertEqual(json.loads(binding_path.read_text())["merge_authorization"], binding["merge_authorization"])
            self.assertEqual(self.wake()["launches"], 1)
            self.fixture("complete")
            self.observation("COMPLETED", "SUCCESS")
            final = self.wake()
            self.assertEqual(final["state"], "complete")
            self.assertEqual(final["goal"], str(goal))
            for payload_path in self.owner.parent.glob("launch-*.json"):
                prompt = json.loads(payload_path.read_text())["command"][-1]
                self.assertIn(f"Read {goal}.", prompt)
                self.assertIn(binding["merge_authorization"]["instruction"], prompt)
            goal.unlink()
            with self.assertRaisesRegex(runtime.Gate, "canonical-goal-unavailable"):
                runtime.check_identity(final)

    def test_relative_escape_and_directory_goal_are_rejected(self):
        with tempfile.TemporaryDirectory() as external:
            goal = Path(external).resolve() / "goal.md"
            goal.write_text("External goal")
            escaped = os.path.relpath(goal, self.root)
            result = self.cli(
                "init", "--root", str(self.root), "--goal", escaped, "--completion", "done",
                "--authority", "test", "--harness", "codex", "--actions", "test", code=2)
            self.assertTrue(result["reason"].startswith("relative-goal-escape:"))
            result = self.cli("init", "--root", str(self.root), "--goal", external, "--completion", "done",
                              "--authority", "test", "--harness", "codex", "--actions", "test", code=2)
            self.assertTrue(result["reason"].startswith("canonical-goal-file-required:"))

    def test_alias_owner_and_nested_root_are_rejected(self):
        alias = self.root / "alternate-owner.json"
        alias.write_text(self.owner.read_text())
        denied = self.cli("wake", "--owner", str(alias), code=2)
        self.assertTrue(denied["reason"].startswith("canonical-owner-path-required:"))
        self.assertIn("omit --owner", denied["reason"])
        nested = self.root / "nested"
        nested.mkdir()
        (nested / "goal.md").write_text("same checkout")
        denied = self.cli("init", "--root", str(nested), "--goal", "goal.md", "--completion", "done",
                          "--authority", "test", "--harness", "codex", "--actions", "test", code=2)
        self.assertEqual(denied["reason"], "canonical-worktree-root-required")
        self.assertFalse((nested / ".agents/continuation/owner.json").exists())

    def recover_completed_child(self, expired=False):
        state = self.state()
        state["max_launches"] = 1
        runtime.atomic_json(self.owner, state)
        self.fixture("complete", after_receipt_sleep=1)
        supervisor = self.start(*self.wake_args())
        self.wait_for(lambda: bool(self.state().get("result_path"))
                      and Path(self.state()["result_path"]).exists())
        supervisor.kill()
        supervisor.wait()
        recorded = self.state()
        self.wait_for(lambda: not runtime.alive(recorded["child"]))
        if expired:
            recorded["deadline"] = time.time() - 1
            runtime.atomic_json(self.owner, recorded)
        complete = self.wake()
        self.assertEqual(complete["state"], "complete")
        self.assertEqual(complete["launches"], 1)
        self.assertEqual(complete["last_result"], recorded["result_path"])
        self.assertEqual(self.wake()["launches"], 1)

    def test_recover_final_launch_receipt_before_budget_gate(self):
        self.recover_completed_child()

    def test_recover_completed_receipt_after_deadline(self):
        self.recover_completed_child(expired=True)

    @unittest.skipUnless(os.name == "nt", "Windows job assignment")
    def test_unassigned_suspended_host_is_killed_and_waited(self):
        state = self.state()
        state["child"] = {"pid": os.getpid()}
        runtime.atomic_json(self.owner, state)
        payload = self.root / "assignment-payload.json"
        payload.write_text(json.dumps({"command": ["fixture"], "environment": {},
                                       "child_path": str(self.root / "host.json")}))
        kernel = mock.Mock()
        kernel.AssignProcessToJobObject.return_value = False
        process = mock.Mock(pid=12345, _handle=123)
        process.poll.return_value = None
        args = SimpleNamespace(owner=str(self.owner), payload=str(payload))
        with mock.patch.object(runtime, "windows_job", return_value=(kernel, 456)), \
                mock.patch.object(runtime.subprocess, "Popen", return_value=process), \
                mock.patch.object(runtime, "atomic_json") as write:
            with self.assertRaisesRegex(OSError, "cannot assign"):
                runtime.child(args)
        process.kill.assert_called_once_with()
        process.wait.assert_called_once_with(timeout=15)
        kernel.TerminateJobObject.assert_not_called()
        kernel.CloseHandle.assert_called_once_with(456)
        write.assert_not_called()

    def released_child(self, status):
        self.binding("COMPLETED", "SUCCESS")
        self.fixture("gate" if status == "blocked" else "complete",
                     release_binding=True, release_state=status)
        result = self.wake()
        self.assertFalse((self.root / ".agents/persistent-workflow-binding.json").exists())
        self.assertEqual(result["launches"], 1)
        return result

    def test_owned_binding_release_can_complete(self):
        result = self.released_child("complete")
        self.assertEqual(result["state"], "complete")
        self.assertEqual(result["reason"], "fixture verified boundary")

    def test_owned_binding_release_can_checkpoint_human_gate(self):
        result = self.released_child("blocked")
        self.assertEqual(result["state"], "blocked")
        self.assertEqual(result["reason"], "human approval required")

    def test_nonterminal_binding_release_gates(self):
        result = self.released_child("waiting")
        self.assertEqual(result["state"], "blocked")
        self.assertEqual(result["reason"], "binding-removed")

    def test_expired_owner_stops_even_when_evidence_pending(self):
        self.binding()
        state = self.state()
        state["deadline"] = time.time() - 1
        runtime.atomic_json(self.owner, state)
        result = self.wake()
        self.assertEqual(result["state"], "blocked")
        self.assertEqual(result["reason"], "continuation-budget-exhausted")
        self.assertEqual(result["launches"], 0)
        self.assertFalse((self.root / "host-started").exists())

    def repaired_release(self, status, **extra):
        self.binding("COMPLETED", "FAILURE")
        self.fixture("repair", release_binding=True, release_state=status, **extra)
        return self.wake()

    def test_repaired_terminal_release_completes(self):
        old_head = self.state()["head"]
        result = self.repaired_release("complete")
        self.assertEqual(result["state"], "complete")
        self.assertNotEqual(result["head"], old_head)
        self.assertEqual(result["head"], self.git("rev-parse", "HEAD"))
        self.assertFalse((self.root / ".agents/persistent-workflow-binding.json").exists())

    def test_repaired_terminal_release_preserves_human_gate(self):
        result = self.repaired_release("blocked", receipt={"reason": "Approve repaired release",
                                                          "next_action": "Obtain product approval"})
        self.assertEqual(result["state"], "blocked")
        self.assertEqual(result["reason"], "Approve repaired release")
        self.assertEqual(result["next_action"], "Obtain product approval")
        self.assertEqual(result["head"], self.git("rev-parse", "HEAD"))

    def test_repaired_release_rejects_missing_or_mismatched_snapshot(self):
        self.binding()
        state = self.state()
        runtime.check_identity(state)
        state["launch_nonce"] = "fixture-receipt"
        old = {key: state[key] for key in ("repo", "worktree", "branch", "head")}
        self.git("commit", "--allow-empty", "-m", "Repaired head")
        new = dict(old, head=self.git("rev-parse", "HEAD"))
        binding_path = self.root / ".agents/persistent-workflow-binding.json"
        snapshot = dict(json.loads(binding_path.read_text()), head=new["head"])
        binding_path.unlink()
        receipt = {"nonce": state["launch_nonce"], "owner_id": state["owner_id"], "state": "complete",
                   "reason": "Repaired boundary", "rebind": {"old": old, "new": new}}
        invalid = [None, dict(snapshot, pr=None), dict(snapshot, pr=99), dict(snapshot, head=old["head"])]
        for candidate in invalid:
            with self.subTest(snapshot=candidate):
                current_receipt = dict(receipt, released_binding=candidate)
                with self.assertRaisesRegex(runtime.Gate, "released-binding-(required|invalid)"):
                    runtime.apply_receipt(dict(state), current_receipt)
        waiting = dict(receipt, state="waiting", next_action="resume", released_binding=snapshot)
        with self.assertRaisesRegex(runtime.Gate, "binding-removed"):
            runtime.apply_receipt(dict(state), waiting)

    def test_repaired_release_cannot_override_existing_stale_binding(self):
        result = self.repaired_release("complete", retain_stale_binding=True)
        self.assertEqual(result["state"], "blocked")
        self.assertEqual(result["reason"], "repair-binding-not-refreshed")


if __name__ == "__main__":
    unittest.main()
