"""Exercise selected engineering hooks from a relocated, self-contained package."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def command_line(hook):
    return " ".join([hook["command"], *hook.get("args", [])])


class PackagedEngineeringHooks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='engineering package with spaces ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.package = self.root / 'relocated plugin'
        shutil.copytree(ROOT / 'plugins/engineering', self.package)
        self.cwd = self.root / 'unrelated caller'
        self.cwd.mkdir()
        review_cache = self.root / 'review cache'
        review_cache.mkdir()
        self.environment = dict(os.environ, PLUGIN_ROOT=str(self.package),
                                CLAUDE_PLUGIN_ROOT=str(self.package), PYTHONIOENCODING='utf-8',
                                TMP=str(review_cache), TEMP=str(review_cache))

    def run_hook(self, path, data=None):
        payload = dict(cwd=str(self.cwd), session_id=str(uuid.uuid4()),
                       hook_event_name='PreToolUse', tool_use_id=str(uuid.uuid4()))
        payload.update(data or {})
        return subprocess.run([sys.executable, '-B', str(self.package / path)],
                              input=json.dumps(payload), capture_output=True, text=True,
                              encoding='utf-8', cwd=self.cwd, env=self.environment, timeout=20)

    def test_each_host_context_uses_its_packaged_contract_without_mutating_the_caller(self):
        script = ".agents/engineering/policy/session-guidance/scripts/session-context.py"
        contract = self.package / ".agents/engineering/policy/session-guidance/SKILL.md"
        bodies = []
        for host, variable in (("claude", "CLAUDE_PLUGIN_ROOT"), ("codex", "PLUGIN_ROOT")):
            with self.subTest(host=host):
                manifest = json.loads(
                    (self.package / f".{host}-plugin/plugin.json").read_text(encoding="utf-8")
                )
                hooks = json.loads((self.package / manifest["hooks"]).read_text(encoding="utf-8"))
                command = command_line(hooks["hooks"]["SessionStart"][0]["hooks"][0])
                self.assertIn(chr(36) + "{" + variable + "}/" + script, command)
                result = self.run_hook(script)
                self.assertEqual(0, result.returncode, result.stderr)
                context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
                self.assertIn("engineering:plan-execution", context)
                self.assertRegex(context, r"load `engineering:lanes`.*?select the next phase")
                self.assertIn(str(contract), context)
                self.assertIn("source SHA-256", context)
                bodies.append(context)
        self.assertEqual(1, len(set(bodies)))
        self.assertEqual([], list(self.cwd.iterdir()))

    def test_missing_context_contract_is_an_actionable_error(self):
        contract = self.package / ".agents/engineering/policy/session-guidance/SKILL.md"
        contract.unlink()
        result = self.run_hook(
            ".agents/engineering/policy/session-guidance/scripts/session-context.py"
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
                command = command_line(hooks["hooks"]["UserPromptSubmit"][0]["hooks"][0])
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
                entry, standalone = context.split("## Standalone or runtime-unavailable execution", 1)
                standalone, repository = standalone.split("## Repository runtime execution", 1)
                self.assertRegex(entry, r"load `engineering:lanes`")
                self.assertRegex(entry, r"(?s)Repeat selection.*?phase changes.*?design approval.*?fallback")
                self.assertRegex(entry, r"(?s)Apply the selected lane.*?before implementing")
                self.assertNotRegex(entry.split("---", 2)[1], r"(?m)^lane:")
                self.assertIn("The rest of this document does not apply in this mode", standalone)
                fallback = repository.split("## Dispatch and fallback", 1)[1].split("## Transfer", 1)[0]
                self.assertRegex(fallback, r"(?s)reselect the phase lane.*?`engineering:lanes`")
                self.assertRegex(fallback, r"(?s)Parent fallback must.*?same lane and capability-limit rules")
                self.assertIn(str(
                    self.package / ".agents/engineering/workflow/plan-execution/SKILL.md"
                ), context)

    def test_planning_then_approval_selects_the_corresponding_packaged_workflow(self):
        (self.cwd / "GOAL.md").write_text(
            "# Goal\n\nStatus: awaiting approval\n\nFinish the taxonomy proposal.\n", encoding="utf-8"
        )
        for prompt, name in (
            ("Planning only: finish the taxonomy proposal, but do not implement it.", "plan-authoring"),
            ("I approve the plan. Implement it through completion.", "plan-execution"),
        ):
            with self.subTest(workflow=name):
                result = self.run_hook("hooks/workflow_route.py", {
                    "hook_event_name": "UserPromptSubmit", "prompt": prompt,
                })
                self.assertEqual(0, result.returncode, result.stderr)
                context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
                canonical = (
                    self.package / f".agents/engineering/workflow/{name}/SKILL.md"
                ).read_text(encoding="utf-8").strip()
                self.assertIn(f"engineering:{name} automatically selected", context)
                self.assertEqual(canonical, context.split("\n\n", 1)[1])

    def test_packaged_planning_intent_distinguishes_execution_and_authoring(self):
        (self.cwd / "GOAL.md").write_text("# Goal\n\nStatus: in progress\n", encoding="utf-8")
        for prompt, name in (
            ("Implement phase 2 of the plan only, not phase 3", "plan-execution"),
            ("Don’t only plan it, implement it", "plan-execution"),
            ("Draft the plan without implementing it", "plan-authoring"),
            ("Please revise the current plan only", "plan-authoring"),
            ("I want to continue planning the migration", "plan-authoring"),
            ("I want you to only plan the migration", "plan-authoring"),
            ("Please continue with planning only", "plan-authoring"),
            ("I don't want to continue planning the migration", None),
            ("Continue with the plan only", "plan-execution"),
            ("Do not implement any changes yet", None),
            ("Review the plan branch without implementing it", None),
        ):
            with self.subTest(prompt=prompt):
                result = self.run_hook("hooks/workflow_route.py", {
                    "hook_event_name": "UserPromptSubmit", "prompt": prompt,
                })
                self.assertEqual(0, result.returncode, result.stderr)
                if name is None:
                    self.assertEqual("", result.stdout)
                else:
                    context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
                    self.assertTrue(context.startswith(f"engineering:{name} automatically selected"))
                    canonical = (
                        self.package / f".agents/engineering/workflow/{name}/SKILL.md"
                    ).read_text(encoding="utf-8").strip()
                    self.assertEqual(canonical, context.split("\n\n", 1)[1])

    def test_host_manifests_register_supported_router_and_red_run_events(self):
        codex = json.loads((self.package / "hooks/codex.json").read_text(encoding="utf-8"))
        claude = json.loads((self.package / "hooks/claude.json").read_text(encoding="utf-8"))
        base_codex = json.loads((ROOT / "plugins/base/hooks/codex.json").read_text(encoding="utf-8"))
        base_claude = json.loads((ROOT / "plugins/base/hooks/claude.json").read_text(encoding="utf-8"))

        def commands(manifest, event):
            return [
                command_line(hook)
                for registration in manifest["hooks"].get(event, [])
                for hook in registration.get("hooks", [])
            ]

        self.assertTrue(any("skill_router.py" in command for command in commands(base_codex, "PreToolUse")))
        codex_router = next(
            registration for registration in base_codex["hooks"]["PreToolUse"]
            if any("skill_router.py" in command_line(hook) for hook in registration["hooks"])
        )
        self.assertIn("Bash", codex_router["matcher"])
        self.assertIn("apply_patch", codex_router["matcher"])
        self.assertNotIn("functions", codex_router["matcher"])
        self.assertFalse(any("skill_router.py" in command for command in commands(codex, "PreToolUse")))
        self.assertFalse(any("red_run_gate.py" in command for event in codex["hooks"] for command in commands(codex, event)))
        self.assertTrue(any("skill_router.py" in command for command in commands(base_claude, "PreToolUse")))
        self.assertFalse(any("skill_router.py" in command for command in commands(claude, "PreToolUse")))
        for event in ("PostToolUse", "PostToolUseFailure", "Stop"):
            self.assertTrue(
                any("red_run_gate.py" in command for command in commands(claude, event)), event
            )

    def test_packaged_review_runtime_resolves_consumer_routes(self):
        consumer = self.root / "routed consumer"
        subprocess.run(["git", "init", "-q", "-b", "main", str(consumer)], check=True)

        def git(*arguments):
            return subprocess.run(
                ["git", *arguments], cwd=consumer, capture_output=True, text=True, check=True
            ).stdout.strip()

        git("config", "user.email", "package@example.test")
        git("config", "user.name", "Package Fixture")
        git("remote", "add", "origin", "https://github.com/example/routed-consumer.git")
        (consumer / ".agents" / "skills" / "feature").mkdir(parents=True)
        (consumer / ".agents" / "skills" / "feature" / "SKILL.md").write_text(
            "---\nname: feature\n---\n\n# Feature\n", encoding="utf-8"
        )
        (consumer / ".agents" / "skill-routes.json").write_text(
            json.dumps({"routes": [{"path": "^src/", "skills": ["feature"]}]}),
            encoding="utf-8",
        )
        (consumer / "src").mkdir()
        (consumer / "src" / "item.py").write_text("value = 1\n", encoding="utf-8")
        git("add", ".")
        git("commit", "-q", "-m", "baseline")
        base = git("rev-parse", "HEAD")
        git("update-ref", "refs/remotes/origin/main", base)
        git("switch", "-q", "-c", "Feature/Routed-review")
        (consumer / "src" / "item.py").write_text("value = 2\n", encoding="utf-8")
        git("add", "src/item.py")
        git("commit", "-q", "-m", "candidate")

        runtime = self.package / "workflows" / "workflow_ops.py"
        spec = importlib.util.spec_from_file_location("packaged_workflow_ops", runtime)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with mock.patch.object(module.tempfile, "gettempdir", return_value=str(self.root / "review cache")):
            result = module.review_prepare(consumer, "packaged-route", "origin/main", "HEAD", False)

        self.assertEqual(["feature"], [rule["name"] for rule in result["rules"]])
        self.assertEqual(".agents/skills/feature/SKILL.md", result["rules"][0]["path"])

    def test_policy_gates_are_silent_without_repository_opt_in(self):
        commands = {'forge_poll_gate': 'gh pr checks 42',
                    'compact_output_gate': 'python -m unittest',
                    'persistent_workflow_merge_gate': 'gh pr merge 42 --auto',
                    'worktree_cleanup_gate': ''}
        for name, command in commands.items():
            with self.subTest(name=name):
                result = self.run_hook(f'hooks/{name}.py', dict(
                    tool_name='Bash', tool_input={'command': command},
                    tool_response='https://github.com/example/repository/pull/42',
                    hook_event_name='SessionStart' if name == 'worktree_cleanup_gate' else 'PreToolUse'))
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual('', result.stdout + result.stderr)

    def test_both_hosts_register_body_validation_before_shell_writes(self):
        for host in ('claude', 'codex'):
            data = json.loads((self.package / f'hooks/{host}.json').read_text(encoding='utf-8'))
            commands = [command_line(hook) for group in data['hooks']['PreToolUse']
                        for hook in group['hooks']]
            body = [command for command in commands if 'delivery_binding_gate.py' in command]
            self.assertEqual(1, len(body))
            if host == 'codex':
                self.assertIn('--validate-body', body[0])
                windows = [hook['commandWindows'] for group in data['hooks']['PreToolUse']
                           for hook in group['hooks'] if 'delivery_binding_gate.py' in hook['command']]
                self.assertIn('pre_tool_use_adapter.py', windows[0])
                self.assertIn('--validate-body', windows[0])
            else:
                self.assertIn('hook_dispatch.py', body[0])
                self.assertIn('delivery_binding_gate.py@Bash|PowerShell', body[0])

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
