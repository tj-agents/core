import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch, Mock

HOOK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOK_ROOT))

import hook_runtime


@unittest.skipUnless(os.name == "nt", "Windows console window behavior")
class HiddenCommandTests(unittest.TestCase):
    def test_hook_child_process_has_no_console_window(self):
        process = Mock(_handle=1, returncode=0)
        process.communicate.return_value = ("", "")
        kernel = Mock()
        kernel.AssignProcessToJobObject.return_value = True
        job = (kernel, 1, Mock())
        with patch.object(hook_runtime, "_windows_job", return_value=job), patch.object(
            hook_runtime.subprocess, "Popen", return_value=process
        ) as popen, patch.object(hook_runtime, "_resume_windows_process"):
            hook_runtime.run_command(["git", "status"])
        self.assertEqual(
            subprocess.CREATE_NO_WINDOW | hook_runtime.CREATE_SUSPENDED,
            popen.call_args.kwargs["creationflags"],
        )


SKILL_ROUTER = HOOK_ROOT / "skill_router.py"
GIT_AUTH_SCOPE_GATE = HOOK_ROOT / "git_auth_scope_gate.py"


class PayloadRootResolutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.payload_root = self.root / "plugin"
        self.hook = self.payload_root / "hooks" / "skill_router.py"
        self.hook.parent.mkdir(parents=True)
        self.hook.touch()

    def test_each_harness_root_resolves_when_it_owns_the_hook(self):
        for name in hook_runtime.PLUGIN_ROOT_VARIABLES:
            with self.subTest(name=name), patch.dict(
                os.environ, {name: str(self.payload_root)}, clear=True
            ):
                self.assertEqual(
                    self.payload_root, hook_runtime.declared_plugin_root(self.hook)
                )
                self.assertEqual(
                    self.payload_root, hook_runtime.own_payload_root(self.hook)
                )

    def test_each_unrelated_harness_root_falls_back_beside_the_hook(self):
        unrelated = self.root / "unrelated"
        unrelated.mkdir()

        for name in hook_runtime.PLUGIN_ROOT_VARIABLES:
            with self.subTest(name=name), patch.dict(
                os.environ, {name: str(unrelated)}, clear=True
            ):
                self.assertEqual(
                    self.payload_root, hook_runtime.own_payload_root(self.hook)
                )

    def test_workspace_ancestor_is_not_a_declared_plugin_root(self):
        with patch.dict(os.environ, {"PLUGIN_ROOT": str(self.root)}, clear=True):
            self.assertIsNone(hook_runtime.declared_plugin_root(self.hook))
            self.assertEqual(self.payload_root, hook_runtime.own_payload_root(self.hook))

    def test_hook_file_itself_is_not_a_declared_plugin_root(self):
        with patch.dict(os.environ, {"CLAUDE_PLUGIN_ROOT": str(self.hook)}, clear=True):
            self.assertIsNone(hook_runtime.declared_plugin_root(self.hook))
            self.assertEqual(self.payload_root, hook_runtime.own_payload_root(self.hook))

    def test_unrelated_earlier_root_does_not_hide_a_later_valid_root(self):
        unrelated = self.root / "unrelated"
        unrelated.mkdir()

        with patch.dict(
            os.environ,
            {
                "PLUGIN_ROOT": str(unrelated),
                "CLAUDE_PLUGIN_ROOT": str(self.payload_root),
            },
            clear=True,
        ):
            self.assertEqual(self.payload_root, hook_runtime.own_payload_root(self.hook))


class DuplicateRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / ".agents").mkdir()
        self.session = str(uuid.uuid4())

    def run_hook(self, hook, payload, environment=None, arguments=()):
        return subprocess.run(
            [sys.executable, str(hook), *arguments],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            cwd=str(self.root),
            env=environment,
        )

    def test_duplicate_skill_router_registration_blocks_once(self):
        plugin = self.root / "installed-plugin"
        hooks = plugin / "hooks"
        hooks.mkdir(parents=True)
        for source in (SKILL_ROUTER, HOOK_ROOT / "hook_runtime.py", HOOK_ROOT / "tier_gate.py"):
            shutil.copy2(source, hooks / source.name)
        shutil.copytree(HOOK_ROOT.parent / "dependencies/agent/.agents/agent/runtime", plugin / "dependencies/agent/.agents/agent/runtime")
        skill = plugin / "skills" / "branching"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: branching\ndescription: Branch rules.\n---\n", encoding="utf-8"
        )
        (self.root / ".agents" / "skill-routes.json").write_text(
            json.dumps({"routes": [{"path": r"\.cs$", "skills": ["branching"]}]}),
            encoding="utf-8",
        )
        payload = {
            "hook_event_name": "PreToolUse",
            "session_id": self.session,
            "turn_id": "turn-1",
            "tool_use_id": "call-1",
            "tool_name": "Write",
            "cwd": str(self.root),
            "tool_input": {"file_path": str(self.root / "a.cs"), "content": "class A {}"},
        }

        state = self.root / "standards-state"
        proof = state / "currency" / f"{hashlib.sha256(self.session.encode('utf-8')).hexdigest()}.json"
        proof.parent.mkdir(parents=True)
        proof.write_text(
            json.dumps({"status": "current", "checked_at": time.time()}),
            encoding="utf-8",
        )
        environment = os.environ.copy()
        environment["AGENT_STANDARDS_STATE_DIRECTORY"] = str(state)
        environment["PLUGIN_ROOT"] = str(plugin)

        first = self.run_hook(hooks / "skill_router.py", payload, environment,
                              arguments=("--harness", "claude"))
        second = self.run_hook(hooks / "skill_router.py", payload, environment,
                               arguments=("--harness", "claude"))

        self.assertEqual(2, first.returncode, first.stdout + first.stderr)
        self.assertEqual(0, second.returncode, second.stdout + second.stderr)
        self.assertEqual("", second.stderr)

    def test_duplicate_git_auth_scope_gate_registration_blocks_once(self):
        payload = {
            "hook_event_name": "PreToolUse",
            "session_id": self.session,
            "turn_id": "turn-1",
            "tool_use_id": "call-2",
            "tool_name": "Bash",
            "cwd": str(self.root),
            "tool_input": {"command": "gh auth refresh -s admin:org"},
        }

        first = self.run_hook(GIT_AUTH_SCOPE_GATE, payload)
        second = self.run_hook(GIT_AUTH_SCOPE_GATE, payload)

        self.assertEqual(2, first.returncode)
        self.assertEqual(0, second.returncode)
        self.assertEqual("", second.stderr)

    def test_missing_invocation_id_preserves_enforcement(self):
        (self.root / ".agents" / "skill-routes.json").write_text(
            json.dumps(
                {
                    "routes": [
                        {
                            "path": r"\.cs$",
                            "skills": ["branching"],
                            "deny": [{"pattern": "forbidden", "reason": "forbidden test input"}],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        payload = {
            "tool_name": "Write",
            "cwd": str(self.root),
            "tool_input": {"file_path": str(self.root / "a.cs"), "content": "forbidden"},
        }

        first = self.run_hook(SKILL_ROUTER, payload, arguments=("--harness", "claude"))
        second = self.run_hook(SKILL_ROUTER, payload, arguments=("--harness", "claude"))

        self.assertEqual(2, first.returncode)
        self.assertEqual(2, second.returncode)


class ClaimRetentionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.temp_patch = patch.object(
            hook_runtime.tempfile, "gettempdir", return_value=str(self.root)
        )
        self.temp_patch.start()
        self.addCleanup(self.temp_patch.stop)

    def payload(self, tool_use_id):
        return {
            "hook_event_name": "PreToolUse",
            "session_id": "retention-session",
            "tool_use_id": tool_use_id,
        }

    def test_claim_prunes_expired_claims_and_keeps_recent_claims(self):
        stale = self.root / f"{hook_runtime.CLAIM_PREFIX}stale.claim"
        recent = self.root / f"{hook_runtime.CLAIM_PREFIX}recent.claim"
        stale.write_text("stale", encoding="utf-8")
        recent.write_text("recent", encoding="utf-8")
        expired = time.time() - hook_runtime.CLAIM_RETENTION_SECONDS - 1
        os.utime(stale, (expired, expired))

        self.assertTrue(hook_runtime.claim_invocation(self.payload("cleanup"), "router"))

        self.assertFalse(stale.exists())
        self.assertTrue(recent.exists())
        self.assertTrue((self.root / hook_runtime.PRUNE_LOCK_NAME).exists())
        self.assertTrue((self.root / hook_runtime.PRUNE_MARKER_NAME).exists())

    def test_repeated_claims_do_not_lock_or_scan_before_pruning_is_due(self):
        with patch.object(
            hook_runtime,
            "_try_acquire_prune_lock",
            wraps=hook_runtime._try_acquire_prune_lock,
        ) as acquire, patch.object(
            hook_runtime,
            "_remove_expired_claims",
            wraps=hook_runtime._remove_expired_claims,
        ) as scan:
            self.assertTrue(hook_runtime.claim_invocation(self.payload("first"), "router"))
            self.assertTrue(hook_runtime.claim_invocation(self.payload("second"), "router"))

        self.assertEqual(1, acquire.call_count)
        self.assertEqual(1, scan.call_count)

    def test_due_pruning_recovers_after_lock_contention(self):
        stale = self.root / f"{hook_runtime.CLAIM_PREFIX}stale.claim"
        stale.write_text("stale", encoding="utf-8")
        expired = time.time() - hook_runtime.CLAIM_RETENTION_SECONDS - 1
        os.utime(stale, (expired, expired))

        with patch.object(hook_runtime, "_try_acquire_prune_lock", return_value=None):
            self.assertTrue(hook_runtime.claim_invocation(self.payload("contended"), "router"))

        self.assertTrue(stale.exists())
        self.assertFalse((self.root / hook_runtime.PRUNE_MARKER_NAME).exists())
        self.assertTrue(hook_runtime.claim_invocation(self.payload("retry"), "router"))
        self.assertFalse(stale.exists())
        self.assertTrue((self.root / hook_runtime.PRUNE_MARKER_NAME).exists())

    def test_expired_current_claim_remains_suppressive_until_another_invocation_prunes_it(self):
        payload = self.payload("same-call")
        self.assertTrue(hook_runtime.claim_invocation(payload, "router"))
        claim = next(self.root.glob(f"{hook_runtime.CLAIM_PREFIX}*.claim"))
        expired = time.time() - hook_runtime.CLAIM_RETENTION_SECONDS - 1
        os.utime(claim, (expired, expired))
        marker = self.root / hook_runtime.PRUNE_MARKER_NAME
        due = time.time() - hook_runtime.CLAIM_PRUNE_INTERVAL_SECONDS - 1
        os.utime(marker, (due, due))

        self.assertFalse(hook_runtime.claim_invocation(payload, "router"))
        self.assertTrue(claim.exists())
        os.utime(marker, (due, due))
        self.assertTrue(hook_runtime.claim_invocation(self.payload("later-call"), "router"))
        self.assertFalse(claim.exists())

    def test_concurrent_duplicate_claims_have_exactly_one_winner(self):
        payload = self.payload("concurrent-call")
        with ThreadPoolExecutor(max_workers=16) as executor:
            results = list(
                executor.map(
                    lambda _: hook_runtime.claim_invocation(payload, "router"), range(64)
                )
            )

        self.assertEqual(1, results.count(True))
        self.assertEqual(63, results.count(False))


class CommandOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def _tree_command(self, held_directory):
        ready = self.root / "ready.txt"
        child = "\n".join(
            (
                "import os",
                "from pathlib import Path",
                "import sys",
                "import time",
                "os.chdir(sys.argv[2])",
                "Path(sys.argv[1]).write_text(str(os.getpid()), encoding='utf-8')",
                "while True:",
                "    time.sleep(1)",
            )
        )
        parent = "\n".join(
            (
                "import subprocess",
                "import sys",
                "import time",
                "subprocess.Popen([sys.executable, '-c', sys.argv[1], sys.argv[2], sys.argv[3]])",
                "while True:",
                "    time.sleep(1)",
            )
        )
        return [sys.executable, "-c", parent, child, str(ready), str(held_directory)], ready

    def _wait_for_dead_pid(self, pid):
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return True
            time.sleep(0.02)
        return False

    def test_timeout_drains_handshaked_owned_tree_and_releases_working_directory(self):
        held_directory = self.root / "space ü"
        held_directory.mkdir()
        command, ready = self._tree_command(held_directory)

        with self.assertRaises(hook_runtime.CommandTimeout) as timed_out:
            hook_runtime.run_command(
                command,
                timeout=1,
                cwd=str(self.root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        self.assertIn("exceeded 1s", str(timed_out.exception))
        self.assertTrue(ready.exists())
        if os.name != "nt":
            self.assertTrue(self._wait_for_dead_pid(int(ready.read_text(encoding="utf-8"))))
        held_directory.rmdir()

    @unittest.skipUnless(os.name != "nt", "POSIX process-group isolation")
    def test_timeout_leaves_unrelated_process_alive(self):
        unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10)"])
        self.addCleanup(
            lambda: unrelated.poll() is None and unrelated.kill()
        )
        command, _ = self._tree_command(self.root)

        with self.assertRaises(hook_runtime.CommandTimeout):
            hook_runtime.run_command(command, timeout=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.assertIsNone(unrelated.poll())

    def test_success_nonzero_check_input_cwd_env_and_text_output_are_preserved(self):
        working_directory = self.root / "working"
        working_directory.mkdir()
        program = "\n".join(
            (
                "import os",
                "from pathlib import Path",
                "import sys",
                "data = sys.stdin.read()",
                "print(Path.cwd().name + ':' + os.environ['HOOK_RUNTIME_VALUE'] + ':' + data)",
                "sys.exit(3 if '--nonzero' in sys.argv else 0)",
            )
        )
        environment = dict(os.environ, HOOK_RUNTIME_VALUE="ready")

        for _ in range(2):
            completed = hook_runtime.run_command(
                [sys.executable, "-c", program],
                input="payload",
                text=True,
                capture_output=True,
                cwd=str(working_directory),
                env=environment,
                check=True,
            )
            self.assertEqual("working:ready:payload\n", completed.stdout)
        binary = hook_runtime.run_command(
            [sys.executable, "-c", "import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())"],
            input=b"payload",
            capture_output=True,
        )
        self.assertEqual(b"payload", binary.stdout)
        nonzero = hook_runtime.run_command(
            [sys.executable, "-c", program, "--nonzero"],
            capture_output=True,
            text=True,
            cwd=str(working_directory),
            env=environment,
        )
        self.assertEqual(3, nonzero.returncode)
        with self.assertRaises(subprocess.CalledProcessError):
            hook_runtime.run_command(
                [sys.executable, "-c", program, "--nonzero"],
                capture_output=True,
                text=True,
                cwd=str(working_directory),
                env=environment,
                check=True,
            )

    @unittest.skipUnless(os.name == "nt", "Windows Job Object setup")
    def test_assignment_failure_terminates_actual_suspended_child(self):
        marker = self.root / "resumed.txt"
        process = None
        original_job = hook_runtime._windows_job
        original_popen = subprocess.Popen

        def failed_assignment_job():
            kernel, handle, accounting_type = original_job()
            failed_kernel = Mock()
            failed_kernel.AssignProcessToJobObject.return_value = False
            failed_kernel.CloseHandle.side_effect = kernel.CloseHandle
            return failed_kernel, handle, accounting_type

        def capture_popen(*args, **kwargs):
            nonlocal process
            process = original_popen(*args, **kwargs)
            return process

        with patch.object(hook_runtime, "_windows_job", side_effect=failed_assignment_job), patch.object(
            hook_runtime.subprocess, "Popen", side_effect=capture_popen
        ):
            with self.assertRaisesRegex(OSError, "cannot assign owned command to job"):
                hook_runtime.run_command(
                    [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; Path(__import__('sys').argv[1]).touch()",
                        str(marker),
                    ],
                    capture_output=True,
                )

        self.assertIsNotNone(process)
        self.assertIsNotNone(process.poll())
        self.assertFalse(marker.exists())
        self.assertTrue(process.stdout.closed)
        self.assertTrue(process.stderr.closed)

    def test_zero_startup_budget_raises_command_timeout_after_drain(self):
        process = None
        original_popen = subprocess.Popen

        def capture_popen(*args, **kwargs):
            nonlocal process
            process = original_popen(*args, **kwargs)
            return process

        with patch.object(hook_runtime.subprocess, "Popen", side_effect=capture_popen):
            with self.assertRaises(hook_runtime.CommandTimeout) as timed_out:
                hook_runtime.run_command(
                    [sys.executable, "-c", "import time; time.sleep(10)"],
                    timeout=0,
                    capture_output=True,
                )

        self.assertIn("exceeded 0s", str(timed_out.exception))
        self.assertIsNotNone(process)
        self.assertIsNotNone(process.poll())
        self.assertTrue(process.stdout.closed)
        self.assertTrue(process.stderr.closed)

    def test_startup_overrun_raises_command_timeout_after_drain(self):
        process = None
        original_popen = subprocess.Popen

        def capture_popen(*args, **kwargs):
            nonlocal process
            process = original_popen(*args, **kwargs)
            time.sleep(0.15)
            return process

        with patch.object(hook_runtime.subprocess, "Popen", side_effect=capture_popen):
            with self.assertRaises(hook_runtime.CommandTimeout) as timed_out:
                hook_runtime.run_command(
                    [sys.executable, "-c", "import time; time.sleep(10)"],
                    timeout=0.05,
                    capture_output=True,
                )

        self.assertIn("exceeded 0.05s", str(timed_out.exception))
        self.assertIsNotNone(process)
        self.assertIsNotNone(process.poll())
        self.assertTrue(process.stdout.closed)
        self.assertTrue(process.stderr.closed)


if __name__ == "__main__":
    unittest.main()
