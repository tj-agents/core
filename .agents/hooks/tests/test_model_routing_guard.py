import json
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path


HOOKS = Path(__file__).resolve().parents[1]
GUARD = HOOKS / "model_routing_guard.py"
sys.path.insert(0, str(HOOKS))
import model_routing_guard as guard


class ModelRoutingGuardTests(unittest.TestCase):
    def run_hook(self, payload):
        return subprocess.run(
            [sys.executable, str(GUARD)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
        )

    def payload(self, tool_name, tool_input):
        return {
            "hook_event_name": "PreToolUse",
            "session_id": uuid.uuid4().hex,
            "tool_use_id": uuid.uuid4().hex,
            "tool_name": tool_name,
            "cwd": str(Path.cwd()),
            "tool_input": tool_input,
        }

    def test_resolved_variables_are_allowed(self):
        text = "launch.ps1 -Model $route.codex_model -ReasoningEffort $route.codex_effort"
        self.assertEqual([], guard.violations(text))

    def test_literal_launch_arguments_are_rejected(self):
        text = "launch.ps1 -Model frontier-choice -ReasoningEffort max"
        reasons = [reason for _, reason in guard.violations(text)]
        self.assertEqual(["literal routing argument", "literal routing argument"], reasons)

    def test_literal_vendor_slug_is_rejected_without_a_roster(self):
        slug = "g" + "pt-example-tier"
        self.assertEqual("literal model slug", guard.violations(slug)[0][1])

    def test_agent_calls_must_name_routed_fields(self):
        self.assertEqual(
            ["delegation omits model"],
            [reason for _, reason in guard.delegation_call_violations("Agent({ prompt: task })")],
        )
        self.assertEqual(
            ["delegation omits reasoning_effort"],
            [
                reason
                for _, reason in guard.delegation_call_violations(
                    "spawn_agent({ model: route.codex_model, message: task })"
                )
            ],
        )
        self.assertEqual(
            ["delegation omits effort"],
            [
                reason
                for _, reason in guard.delegation_call_violations(
                    "agent(prompt, { model: args.model })"
                )
            ],
        )

    def test_complete_agent_calls_are_allowed(self):
        text = "\n".join(
            [
                "Agent({ model: route.model, prompt: task })",
                "spawn_agent({ model: route.codex_model, reasoning_effort: route.codex_effort })",
                "agent(prompt, { model: args.model, effort: args.effort })",
            ]
        )
        self.assertEqual([], guard.delegation_call_violations(text))

    def test_delegating_skill_requires_route_declaration(self):
        missing = "---\nname: sample\ndomain: process\n---\n\nDispatch a review lens."
        declared = "---\nname: sample\ndomain: process\nroute: tags=review\n---\n\nDispatch a review lens."
        self.assertEqual(
            "delegating skill omits route declaration",
            guard.skill_route_violations(missing)[0][1],
        )
        self.assertEqual([], guard.skill_route_violations(declared))

    def test_skill_write_with_literal_is_blocked(self):
        result = self.run_hook(
            self.payload(
                "Write",
                {"file_path": ".agents/skills/example/SKILL.md", "content": "run -Model fixed"},
            )
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("MODEL ROUTING GUARD", result.stderr)

    def test_partial_skill_edit_does_not_require_front_matter_in_the_fragment(self):
        result = self.run_hook(
            self.payload(
                "Edit",
                {
                    "file_path": ".agents/skills/example/SKILL.md",
                    "old_string": "Dispatch one lens.",
                    "new_string": "Dispatch two independent lenses.",
                },
            )
        )
        self.assertEqual(0, result.returncode)

    def test_unrelated_write_is_ignored(self):
        result = self.run_hook(
            self.payload("Write", {"file_path": "src/example.py", "content": "run -Model fixed"})
        )
        self.assertEqual(0, result.returncode)

    def test_literal_shell_launch_is_blocked(self):
        result = self.run_hook(self.payload("exec_command", {"cmd": "launch.ps1 --model fixed"}))
        self.assertEqual(2, result.returncode)

    def test_agent_tool_without_model_is_blocked(self):
        result = self.run_hook(self.payload("Agent", {"prompt": "Review the change."}))
        self.assertEqual(2, result.returncode)
        self.assertIn("unrouted", result.stderr)

    def test_spawn_agent_without_effort_is_blocked(self):
        result = self.run_hook(
            self.payload("spawn_agent", {"model": "resolved-value", "message": "Inspect code."})
        )
        self.assertEqual(2, result.returncode)

    def test_routed_agent_tool_is_allowed(self):
        result = self.run_hook(
            self.payload(
                "spawn_agent",
                {
                    "model": "resolved-value",
                    "reasoning_effort": "resolved-effort",
                    "message": "Inspect code.",
                },
            )
        )
        self.assertEqual(0, result.returncode)

    def test_repository_scan_reports_guarded_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            target = root / ".agents" / "skills" / "example" / "SKILL.md"
            target.parent.mkdir(parents=True)
            target.write_text("launch -Model fixed\n", encoding="utf-8")
            self.assertEqual(
                [(".agents/skills/example/SKILL.md", 1, "literal routing argument")],
                guard.scan_repository(root),
            )


if __name__ == "__main__":
    unittest.main()
