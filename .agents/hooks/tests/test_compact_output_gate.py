import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path


HOOKS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOKS))


def load_gate():
    spec = importlib.util.spec_from_file_location("compact_output_gate", HOOKS / "compact_output_gate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load_gate()


class ClassificationTests(unittest.TestCase):
    def test_validation_commands_require_capture(self):
        for command in (
            "dotnet test src/Test.csproj",
            "npm run build",
            "python -m unittest discover",
            "pwsh .agents/sync-generated.ps1 -Check",
            "gh run view 42 --log",
        ):
            with self.subTest(command=command):
                self.assertTrue(gate.requires_capture(command, gate.DEFAULT_PATTERNS))

    def test_shared_wrapper_is_allowed(self):
        command = "python .agents/workflows/workflow_ops.py --workflow-run-id x run --label tests -- dotnet test"
        self.assertFalse(gate.requires_capture(command, gate.DEFAULT_PATTERNS))

    def test_mentioning_the_wrapper_does_not_bypass_capture(self):
        for command in (
            "echo workflow_ops.py run -- dotnet test",
            "python .agents/workflows/workflow_ops.py --workflow-run-id x run --label tests -- dotnet test; pytest",
            "python C:\\untrusted\\workflow_ops.py --workflow-run-id x run --label tests -- dotnet test",
            "python .agents/workflows/workflow_ops.py --workflow-run-id x run --label tests -- true <(dotnet test)",
        ):
            with self.subTest(command=command):
                self.assertTrue(gate.requires_capture(command, gate.DEFAULT_PATTERNS))

    def test_inspection_is_not_captured(self):
        self.assertFalse(gate.requires_capture("git status --short", gate.DEFAULT_PATTERNS))


class EndToEndTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / ".agents").mkdir()
        (self.root / ".agents" / "forge-poll-gate.json").write_text("{}\n", encoding="utf-8")

    def invoke(self, command, codex=False):
        payload = {
            "session_id": uuid.uuid4().hex,
            "hook_event_name": "PreToolUse",
            "tool_use_id": uuid.uuid4().hex,
            "tool_name": "exec_command" if codex else "Bash",
            "cwd": str(self.root),
            "tool_input": {"cmd": command} if codex else {"command": command},
        }
        if codex:
            payload["turn_id"] = uuid.uuid4().hex
        return subprocess.run(
            [sys.executable, str(HOOKS / "compact_output_gate.py")],
            cwd=str(self.root),
            input=json.dumps(payload),
            capture_output=True,
            text=True,
        )

    def test_claude_and_codex_block_uncaptured_validation(self):
        for codex in (False, True):
            completed = self.invoke("dotnet test tests.csproj", codex)
            self.assertEqual(2, completed.returncode)
            self.assertIn("workflow_ops.py", completed.stderr)

    def test_wrapped_validation_passes(self):
        command = "python .agents/workflows/workflow_ops.py --workflow-run-id x run --label tests -- dotnet test"
        self.assertEqual(0, self.invoke(command).returncode)


if __name__ == "__main__":
    unittest.main()
