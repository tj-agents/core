"""Exercise selected engineering hooks from a relocated, self-contained package."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]


class PackagedEngineeringHooks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='engineering package with spaces ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.package = self.root / 'relocated plugin'
        shutil.copytree(ROOT / 'plugins/engineering', self.package)
        self.cwd = self.root / 'unrelated caller'
        self.cwd.mkdir()
        self.environment = dict(os.environ, PLUGIN_ROOT=str(self.package),
                                CLAUDE_PLUGIN_ROOT=str(self.package), PYTHONIOENCODING='utf-8')

    def run_hook(self, path, data=None):
        payload = dict(cwd=str(self.cwd), session_id=str(uuid.uuid4()),
                       hook_event_name='PreToolUse', tool_use_id=str(uuid.uuid4()))
        payload.update(data or {})
        return subprocess.run([sys.executable, '-B', str(self.package / path)],
                              input=json.dumps(payload), capture_output=True, text=True,
                              encoding='utf-8', cwd=self.cwd, env=self.environment, timeout=20)

    def test_each_host_context_uses_its_packaged_contract_without_mutating_the_caller(self):
        script = ".agents/engineering/contract/session-guidance/scripts/session-context.py"
        contract = self.package / ".agents/engineering/contract/session-guidance/SKILL.md"
        bodies = []
        for host, variable in (("claude", "CLAUDE_PLUGIN_ROOT"), ("codex", "PLUGIN_ROOT")):
            with self.subTest(host=host):
                manifest = json.loads(
                    (self.package / f".{host}-plugin/plugin.json").read_text(encoding="utf-8")
                )
                hooks = json.loads((self.package / manifest["hooks"]).read_text(encoding="utf-8"))
                command = hooks["hooks"]["SessionStart"][0]["hooks"][0]["command"]
                self.assertIn(chr(36) + "{" + variable + "}/" + script, command)
                result = self.run_hook(script)
                self.assertEqual(0, result.returncode, result.stderr)
                context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
                self.assertIn("engineering:plan-execution", context)
                self.assertIn(str(contract), context)
                self.assertIn("source SHA-256", context)
                bodies.append(context)
        self.assertEqual(1, len(set(bodies)))
        self.assertEqual([], list(self.cwd.iterdir()))

    def test_missing_context_contract_is_an_actionable_error(self):
        contract = self.package / ".agents/engineering/contract/session-guidance/SKILL.md"
        contract.unlink()
        result = self.run_hook(
            ".agents/engineering/contract/session-guidance/scripts/session-context.py"
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("cannot read contract", result.stderr)
        self.assertEqual("", result.stdout)

    def test_each_host_routes_an_active_goal_to_the_packaged_plan_execution_contract(self):
        (self.cwd / "GOAL.md").write_text(
            "# Goal\n\nStatus: in progress\n\nComplete every phase.\n", encoding="utf-8"
        )
        canonical = (
            self.package / ".agents/engineering/workflow/plan-execution/SKILL.md"
        ).read_text(encoding="utf-8").strip()
        for host, variable in (("claude", "CLAUDE_PLUGIN_ROOT"), ("codex", "PLUGIN_ROOT")):
            with self.subTest(host=host):
                manifest = json.loads(
                    (self.package / f".{host}-plugin/plugin.json").read_text(encoding="utf-8")
                )
                hooks = json.loads((self.package / manifest["hooks"]).read_text(encoding="utf-8"))
                command = hooks["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
                self.assertIn(
                    chr(36) + "{" + variable + "}/hooks/workflow_route.py", command
                )
                result = self.run_hook("hooks/workflow_route.py", {
                    "hook_event_name": "UserPromptSubmit",
                    "prompt": "Continue and complete the active goal.",
                })
                self.assertEqual(0, result.returncode, result.stderr)
                context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
                self.assertEqual(canonical, context.split("\n\n", 1)[1])
                self.assertIn(str(
                    self.package / ".agents/engineering/workflow/plan-execution/SKILL.md"
                ), context)
    def test_policy_gates_are_silent_without_repository_opt_in(self):
        commands = {'forge_poll_gate': 'gh pr checks 42',
                    'compact_output_gate': 'python -m unittest',
                    'persistent_workflow_merge_gate': 'gh pr merge 42 --auto',
                    'delivery_binding_gate': 'gh pr create --title Example',
                    'worktree_cleanup_gate': ''}
        for name, command in commands.items():
            with self.subTest(name=name):
                result = self.run_hook(f'hooks/{name}.py', dict(
                    tool_name='Bash', tool_input={'command': command},
                    tool_response='https://github.com/example/repository/pull/42',
                    hook_event_name='SessionStart' if name == 'worktree_cleanup_gate' else 'PreToolUse'))
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual('', result.stdout + result.stderr)

    def test_credential_guard_blocks_widening_but_allows_read_only_status(self):
        for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
            for command, expected in (('gh auth refresh -s admin:org', 2), ('gh auth status', 0)):
                with self.subTest(tool=tool, command=command):
                    result = self.run_hook('hooks/git_auth_scope_gate.py', dict(
                        tool_name=tool, tool_input={field: command}))
                    self.assertEqual(expected, result.returncode, result.stderr)
                    if expected:
                        self.assertIn('GIT-AUTH GATE', result.stderr)


if __name__ == '__main__':
    unittest.main()
