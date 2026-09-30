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
        with patch.object(hook_runtime.subprocess, "run", return_value=Mock(returncode=0)) as run:
            hook_runtime.run_command(["git", "status"])
        self.assertEqual(subprocess.CREATE_NO_WINDOW, run.call_args.kwargs["creationflags"])


SKILL_ROUTER = HOOK_ROOT / "skill_router.py"
MERGE_GATE = HOOK_ROOT / "merge_review_gate.py"
STOP_LAUNCHER = HOOK_ROOT / "plan_handoff_stop_launcher.py"
M = "gh pr " + "merge"


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

    def run_hook(self, hook, payload, environment=None):
        return subprocess.run(
            [sys.executable, str(hook)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            cwd=str(self.root),
            env=environment,
        )

    def run_stop_hook(self, payload):
        environment = os.environ.copy()
        for name in hook_runtime.PLUGIN_ROOT_VARIABLES:
            environment.pop(name, None)
        environment["PLUGIN_ROOT"] = str(HOOK_ROOT.parent)
        return self.run_hook(STOP_LAUNCHER, payload, environment)

    def stop_payload(self, message):
        plan_directory = self.root / "plans" / "runtime"
        plan_directory.mkdir(parents=True)
        (plan_directory / "RUNTIME_PLAN.md").write_text("# Runtime plan\n", encoding="utf-8")
        (plan_directory / "RUNTIME_ROADMAP.md").write_text(
            "# Runtime roadmap\n\n- [ ] **Runtime** `runtime/handoff`\n",
            encoding="utf-8",
        )
        (plan_directory / "RUNTIME_PROGRESS.md").write_text(
            "\n".join(
                [
                    "# Runtime progress",
                    "",
                    "- Plan: `plans/runtime/RUNTIME_PLAN.md`",
                    "- Roadmap: `plans/runtime/RUNTIME_ROADMAP.md`",
                    "- Roadmap item: `runtime/handoff`",
                    f"- Worktree: `{self.root}`",
                    "",
                    "## Next Steps",
                    "",
                    "Finish the runtime verification.",
                    "Scope: current slice only; full plan remains incomplete.",
                    "Current slice: finish the runtime verification.",
                    "Remaining scope: delivery and closeout remain.",
                    "Done when: this fixture step is green; the full plan remains open.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        transcript = self.root / "transcript.jsonl"
        transcript.write_text("", encoding="utf-8")
        return {
            "hook_event_name": "Stop",
            "session_id": self.session,
            "cwd": str(self.root),
            "transcript_path": str(transcript),
            "last_assistant_message": message,
            "stop_hook_active": False,
        }

    def test_duplicate_skill_router_registration_blocks_once(self):
        plugin = self.root / "installed-plugin"
        hooks = plugin / "hooks"
        hooks.mkdir(parents=True)
        for source in (SKILL_ROUTER, HOOK_ROOT / "hook_runtime.py"):
            shutil.copy2(source, hooks / source.name)
        skill = plugin / "skills" / "git-branching"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: git-branching\ndescription: Branch rules.\n---\n", encoding="utf-8"
        )
        (self.root / ".agents" / "skill-routes.json").write_text(
            json.dumps({"routes": [{"path": r"\.cs$", "skills": ["git-branching"]}]}),
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

        first = self.run_hook(hooks / "skill_router.py", payload, environment)
        second = self.run_hook(hooks / "skill_router.py", payload, environment)

        self.assertEqual(2, first.returncode, first.stdout + first.stderr)
        self.assertEqual(0, second.returncode, second.stdout + second.stderr)
        self.assertEqual("", second.stderr)

    def test_duplicate_merge_gate_registration_blocks_once(self):
        (self.root / ".agents" / "merge-gate.json").write_text(
            json.dumps({"security_paths": []}), encoding="utf-8"
        )
        payload = {
            "hook_event_name": "PreToolUse",
            "session_id": self.session,
            "turn_id": "turn-1",
            "tool_use_id": "call-2",
            "tool_name": "Bash",
            "cwd": str(self.root),
            "tool_input": {"command": M + " 1 --auto"},
        }

        first = self.run_hook(MERGE_GATE, payload)
        second = self.run_hook(MERGE_GATE, payload)

        self.assertEqual(2, first.returncode)
        self.assertEqual(0, second.returncode)
        self.assertEqual("", second.stderr)

    def test_duplicate_stop_registration_evaluates_once(self):
        payload = self.stop_payload("Continue this work in a fresh context.")

        first = self.run_stop_hook(payload)
        second = self.run_stop_hook(payload)

        self.assertEqual(0, first.returncode)
        self.assertEqual("block", json.loads(first.stdout)["decision"])
        self.assertEqual(0, second.returncode)
        self.assertEqual("", second.stdout)

    def test_duplicate_stop_registration_allows_same_context_continuation(self):
        payload = self.stop_payload("Continue this work in the current context.")

        first = self.run_stop_hook(payload)
        second = self.run_stop_hook(payload)

        self.assertEqual(0, first.returncode)
        self.assertEqual({}, json.loads(first.stdout))
        self.assertEqual(0, second.returncode)
        self.assertEqual("", second.stdout)

    def test_missing_invocation_id_preserves_enforcement(self):
        (self.root / ".agents" / "skill-routes.json").write_text(
            json.dumps(
                {
                    "routes": [
                        {
                            "path": r"\.cs$",
                            "skills": ["git-branching"],
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

        first = self.run_hook(SKILL_ROUTER, payload)
        second = self.run_hook(SKILL_ROUTER, payload)

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


if __name__ == "__main__":
    unittest.main()
