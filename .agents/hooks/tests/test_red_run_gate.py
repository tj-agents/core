import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch
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

    def result(self, command, output, event="PostToolUseFailure", exit_code=None):
        key = "tool_error" if event == "PostToolUseFailure" else "tool_response"
        response = {"stdout": output, "stderr": "", "interrupted": False}
        if exit_code is not None:
            response["exit_code"] = exit_code
        return self.run_gate(
            {
                "hook_event_name": event,
                "tool_name": "Bash",
                "tool_input": {"command": command},
                key: response,
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

    def test_ci_log_read_with_echoed_failure_script_and_passing_summary_is_silent(self):
        command = 'gh run view 42 --log | grep -iE "##\\[error\\]|error:|failed|Error " | head -30'
        output = (
            'echo "::error file=example.cs::failed build step"\n'
            'echo "Error: The following required dependencies are missing..."\n'
            "Passed! - Failed: 0, Passed: 12, Skipped: 0, Total: 12\n"
        )
        result = self.result(command, output, event="PostToolUse")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        stop = self.run_gate({"hook_event_name": "Stop", "stop_hook_active": False})
        self.assertEqual("", stop.stdout)

    def test_quoted_test_runner_and_log_search_are_silent(self):
        for command in (
            'echo "dotnet test Example.IntegrationTests"',
            "grep -i 'dotnet test' workflow.log",
            'echo "example; dotnet test Example.IntegrationTests"',
            "grep 'example | pytest' workflow.log",
            'printf "example\npytest"',
        ):
            with self.subTest(command=command):
                result = self.result(command, FAILED)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("", result.stderr)

    def test_failing_suite_is_detected_after_a_passing_suite(self):
        result = self.result("dotnet test Example.IntegrationTests", PASSED + FAILED)
        self.assertEqual(2, result.returncode, result.stderr)

    def test_e2e_runner_still_selects_its_tier(self):
        for command in ("./scripts/e2e.ps1 ui",
                        "pwsh -NoProfile -File scripts/e2e.ps1 ui",
                        "& 'C:\\Project Space\\scripts\\e2e.ps1' ui"):
            with self.subTest(command=command):
                result = self.result(command, FAILED)
                self.assertEqual(2, result.returncode, result.stderr)
                self.assertIn("e2e-ui-debug", result.stderr)

    def test_compound_command_exit_alone_is_not_a_test_verdict(self):
        result = self.result("pytest | grep missing", "", exit_code=1)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)

    def test_stop_discards_legacy_ci_read_obligation(self):
        sys.path.insert(0, str(HOOKS))
        self.addCleanup(sys.path.remove, str(HOOKS))
        import red_run_gate

        red_run_gate.save_state(self.session, {
            "command": "gh run view 42 --log", "skills": ["engineering:failing-tests"],
            "answered": False,
        })
        self.addCleanup(red_run_gate.clear_state, self.session)
        stop = self.run_gate({"hook_event_name": "Stop", "stop_hook_active": False})
        self.assertEqual("", stop.stdout + stop.stderr)

    def test_structured_failing_exit_requires_an_executed_test_runner(self):
        failed = self.result("pytest", "", event="PostToolUse", exit_code=1)
        self.assertEqual(2, failed.returncode, failed.stderr)
        for output, exit_code in (("", 0), (PASSED, 1)):
            with self.subTest(output=output, exit_code=exit_code):
                result = self.result("pytest", output, event="PostToolUse", exit_code=exit_code)
                self.assertEqual(0, result.returncode, result.stderr)

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

    def test_fallback_skill_is_named_by_its_installed_plugin(self):
        sys.path.insert(0, str(HOOKS))
        self.addCleanup(sys.path.remove, str(HOOKS))
        import red_run_gate

        path = self.base / "cache" / "marketplace" / "replacement" / "1.0" / "skills" / "failing-tests" / "SKILL.md"
        with patch.object(red_run_gate.skill_router, "plugin_of", return_value="replacement"):
            lines = red_run_gate.skill_lines(
                ["engineering:failing-tests"],
                {"engineering:failing-tests": ("Repair failed tests.", path)},
                "claude",
            )
        self.assertIn("  * replacement:failing-tests", lines)


if __name__ == "__main__":
    unittest.main()
