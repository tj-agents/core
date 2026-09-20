import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path


HOOKS = Path(__file__).resolve().parents[1]
GATE = HOOKS / "red_run_gate.py"
FAILED = "[FAIL] ExampleTests.works\nFailed! - Failed: 1, Passed: 2, Skipped: 0, Total: 3\n"
BUILD_FAILED = "Example.cs(1,1): error CS1002: ; expected\nBuild FAILED.\nTESTS FAILED\n"
PASSED = "Passed! - Failed: 0, Passed: 3, Skipped: 0, Total: 3\n"


class RedRunGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.repo = self.base / "repo"
        (self.repo / ".agents").mkdir(parents=True)
        (self.repo / ".git").mkdir()
        (self.repo / ".agents" / "skill-routes.json").write_text(
            '{"routes": []}', encoding="utf-8"
        )
        self.plugin = self.base / "engineering"
        hooks = self.plugin / "hooks"
        hooks.mkdir(parents=True)
        for name in ("red_run_gate.py", "skill_router.py", "hook_runtime.py"):
            shutil.copy2(HOOKS / name, hooks / name)
        self.gate = hooks / "red_run_gate.py"
        for name in ("failing-tests", "merging", "integration-debug", "e2e-ui-debug"):
            skill = self.plugin / "skills" / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: {name} repair procedure.\n"
                "kind: workflow\ndomain: process\n---\n\n# Procedure\n",
                encoding="utf-8",
            )
        self.session = str(uuid.uuid4())

    def environment(self):
        env = dict(os.environ)
        env["CLAUDE_PLUGIN_ROOT"] = str(self.plugin)
        env["HOME"] = str(self.base / "home")
        env["USERPROFILE"] = str(self.base / "home")
        return env

    def run_gate(self, payload):
        payload.setdefault("session_id", self.session)
        payload.setdefault("cwd", str(self.repo))
        payload.setdefault("tool_use_id", str(uuid.uuid4()))
        return subprocess.run(
            [sys.executable, "-B", str(self.gate)],
            cwd=self.repo,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=self.environment(),
            timeout=20,
        )

    def result(self, command, output, event="PostToolUseFailure"):
        key = "tool_error" if event == "PostToolUseFailure" else "tool_response"
        return self.run_gate(
            {
                "hook_event_name": event,
                "tool_name": "Bash",
                "tool_input": {"command": command},
                key: {"stdout": output, "stderr": "", "interrupted": False},
            }
        )

    def test_failed_test_run_demands_the_repair_loop(self):
        result = self.result("dotnet test Example.IntegrationTests", FAILED)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("RED RUN", result.stderr)
        self.assertIn("engineering:failing-tests", result.stderr)
        self.assertIn("integration-debug", result.stderr)

    def test_build_failure_and_passing_run_are_silent(self):
        for output in (BUILD_FAILED, PASSED):
            with self.subTest(output=output):
                result = self.result("dotnet test Example.IntegrationTests", output)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("", result.stderr)

    def test_successful_ci_read_reporting_queue_failure_is_detected(self):
        output = "X merge queue run\nTriggered via merge_group\nX e2e-ui in 2m (ID 42)\n"
        result = self.result("gh run view 42", output, event="PostToolUse")
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("e2e-ui-debug", result.stderr)
        self.assertIn("engineering:merging", result.stderr)

    def test_stop_blocks_once_while_the_owner_is_unproven(self):
        first = self.result("pytest", "1 failed in 0.1s")
        self.assertEqual(2, first.returncode, first.stderr)
        stop = self.run_gate({"hook_event_name": "Stop", "stop_hook_active": False})
        self.assertEqual(0, stop.returncode, stop.stderr)
        envelope = json.loads(stop.stdout)
        self.assertEqual("block", envelope["decision"])
        self.assertIn("engineering:failing-tests", envelope["reason"])
        second = self.run_gate({"hook_event_name": "Stop", "stop_hook_active": False})
        self.assertEqual("", second.stdout)

    def test_repository_without_routing_opt_in_is_silent(self):
        (self.repo / ".agents" / "skill-routes.json").unlink()
        result = self.result("pytest", "1 failed in 0.1s")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)


if __name__ == "__main__":
    unittest.main()