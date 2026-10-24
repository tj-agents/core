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


class PackagedEngineeringHooks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='engineering package with spaces ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.package = self.root / 'cache' / 'tj-agents' / 'engineering' / '2.1.16'
        shutil.copytree(ROOT / 'plugins/engineering', self.package)
        self.cwd = self.root / 'unrelated caller'
        self.cwd.mkdir()
        review_cache = self.root / 'review cache'
        review_cache.mkdir()
        plugin_data = self.root / 'plugin data'
        self.environment = dict(os.environ, PLUGIN_ROOT=str(self.package),
                                CLAUDE_PLUGIN_ROOT=str(self.package), PYTHONIOENCODING='utf-8',
                                TMP=str(review_cache), TEMP=str(review_cache),
                                PLUGIN_DATA=str(plugin_data))

    def run_hook(self, path, data=None, arguments=()):
        payload = dict(cwd=str(self.cwd), session_id=str(uuid.uuid4()),
                       hook_event_name='PreToolUse', tool_use_id=str(uuid.uuid4()))
        payload.update(data or {})
        return subprocess.run([sys.executable, '-B', str(self.package / path), *arguments],
                              input=json.dumps(payload), capture_output=True, text=True,
                              encoding='utf-8', cwd=self.cwd, env=self.environment, timeout=20)

    def run_without_stdin(self, path, arguments=()):
        return subprocess.run(
            [sys.executable, '-B', str(self.package / path), *arguments],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding='utf-8',
            cwd=self.cwd, env=self.environment, timeout=20,
        )

    def additional_context(self, result):
        return json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]

    def test_context_uses_its_packaged_contract_without_mutating_the_caller(self):
        script = ".agents/engineering/policy/session/scripts/session-context.py"
        contract = self.package / ".agents/engineering/policy/session/SKILL.md"
        result = self.run_hook(script)
        self.assertEqual(0, result.returncode, result.stderr)
        context = self.additional_context(result)
        self.assertIn("engineering:session (source SHA-256", context)
        self.assertNotIn("engineering:session-guidance", context)
        self.assertIn("workflow:run", context)
        self.assertIn(str(contract), context)
        self.assertIn("source SHA-256", context)
        body = contract.read_text(encoding="utf-8").split("\n---\n", 1)[1].strip()
        self.assertTrue(context.split("\n\n", 1)[1].startswith(body))
        self.assertIn("auto_approve_design=false", context)
        self.assertEqual([], list(self.cwd.iterdir()))

    def test_session_start_context_carries_the_callout_lifecycle_and_finish_sections(self):
        script = ".agents/engineering/policy/session/scripts/session-context.py"
        contract = self.package / ".agents/engineering/policy/session/SKILL.md"
        result = self.run_hook(
            script, {"hook_event_name": "SessionStart"}, arguments=("--session-start-context",)
        )
        self.assertEqual(0, result.returncode, result.stderr)
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual("SessionStart", output["hookEventName"])
        context = output["additionalContext"]
        self.assertIn(str(contract), context)
        self.assertIn("machine:close", context)
        self.assertIn("Before returning a completed outcome", context)
        self.assertIn("before any host product feedback", context)
        self.assertIn("A bounded behavior change selects `engineering:feature`", context)
        self.assertNotIn("## ", context)
        self.assertNotIn("Repository routine-decision delegation", context)
        self.assertLess(len(context), 4000)
        self.assertEqual([], list(self.cwd.iterdir()))

    def test_manifest_dispatches_session_start_context_to_codex(self):
        manifest = json.loads(
            (ROOT / ".agents/plugins/manifests/codex/engineering-hooks.json").read_text(encoding="utf-8")
        )
        hook = manifest["hooks"]["SessionStart"][0]["hooks"][0]
        for field in ("command", "commandWindows"):
            self.assertIn(
                '--hook "${PLUGIN_ROOT}/.agents/engineering/policy/session/scripts/session-context.py" '
                "--session-start-context",
                hook[field],
            )

    def test_manifest_dispatches_session_start_context_to_claude(self):
        manifest = json.loads(
            (ROOT / ".agents/plugins/manifests/claude/engineering-hooks.json").read_text(encoding="utf-8")
        )
        registrations = manifest["hooks"]["SessionStart"]
        self.assertEqual(1, len(registrations))
        self.assertEqual(1, len(registrations[0]["hooks"]))
        hook = registrations[0]["hooks"][0]
        self.assertEqual(
            ["-B", "${CLAUDE_PLUGIN_ROOT}/hooks/hook_dispatch.py", "--deadline", "10", "--hook",
             "${CLAUDE_PLUGIN_ROOT}/.agents/engineering/policy/session/scripts/session-context.py",
             "--session-start-context"],
            hook["args"],
        )

    def test_missing_context_contract_is_an_actionable_error(self):
        contract = self.package / ".agents/engineering/policy/session/SKILL.md"
        contract.unlink()
        result = self.run_hook(
            ".agents/engineering/policy/session/scripts/session-context.py"
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("cannot read contract", result.stderr)
        self.assertEqual("", result.stdout)

    def test_uses_the_payload_checkout_for_routine_design_delegation(self):
        script = ".agents/engineering/policy/session/scripts/session-context.py"
        project = self.root / "configured repository"
        agents = project / ".agents"
        agents.mkdir(parents=True)
        settings = agents / "settings.json"

        def prompt_submit():
            return self.run_hook(script, {"cwd": str(project)}, arguments=("--prompt-context",))

        settings.unlink(missing_ok=True)
        with self.subTest(setting="absent"):
            start = self.run_hook(script, {"cwd": str(project)})
            self.assertEqual(0, start.returncode, start.stderr)
            start_context = self.additional_context(start)
            self.assertIn("auto_approve_design=false", start_context)
            self.assertIn(str(settings), start_context)

            prompt = prompt_submit()
            self.assertEqual(0, prompt.returncode, prompt.stderr)
            self.assertIn("auto_approve_design=false", self.additional_context(prompt))

        with self.subTest(setting="nested-all-enabled"):
            settings.write_text(
                json.dumps({"configuration": {"core": {"auto_approve": {"all": True}}}}),
                encoding="utf-8",
            )
            prompt = prompt_submit()
            self.assertEqual(0, prompt.returncode, prompt.stderr)
            prompt_context = self.additional_context(prompt)
            self.assertIn("auto_approve_design=true", prompt_context)
            self.assertIn(str(settings), prompt_context)
            self.assertIn("configuration.core.auto_approve.all", prompt_context)

        with self.subTest(setting="nested-design-disabled-next-prompt"):
            settings.write_text(
                json.dumps({"configuration": {
                    "core": {"auto_approve": {"all": True, "design": False}}
                }}),
                encoding="utf-8",
            )
            prompt = prompt_submit()
            self.assertEqual(0, prompt.returncode, prompt.stderr)
            prompt_context = self.additional_context(prompt)
            self.assertIn("auto_approve_design=false", prompt_context)
            self.assertIn("configuration.core.auto_approve.design", prompt_context)

        with self.subTest(setting="legacy-enabled"):
            settings.write_text(
                json.dumps({"configuration": {"core": {"auto_approve_design": True}}}),
                encoding="utf-8",
            )
            prompt = prompt_submit()
            self.assertEqual(0, prompt.returncode, prompt.stderr)
            self.assertIn("auto_approve_design=true", self.additional_context(prompt))

        with self.subTest(setting="invalid"):
            settings.write_text(
                json.dumps({"configuration": {"core": {"auto_approve_design": "true"}}}),
                encoding="utf-8",
            )
            prompt = prompt_submit()
            self.assertEqual(0, prompt.returncode, prompt.stderr)
            prompt_context = self.additional_context(prompt)
            self.assertIn("auto_approve_design=false", prompt_context)
            self.assertIn("cannot resolve repository routine delegation", prompt_context)

        invalid_root = self.run_hook(script, {"cwd": "not-an-absolute-root"})
        self.assertEqual(0, invalid_root.returncode, invalid_root.stderr)
        invalid_context = self.additional_context(invalid_root)
        self.assertIn("auto_approve_design=false", invalid_context)
        self.assertIn("existing absolute directory", invalid_context)

        self.assertEqual([], list(self.cwd.iterdir()))

    def test_context_fails_when_the_packaged_settings_reader_is_missing(self):
        script = ".agents/engineering/policy/session/scripts/session-context.py"
        project = self.root / "configured repository"
        (project / ".agents").mkdir(parents=True)
        reader = self.package / "workflows" / "repository_configuration.py"
        reader.unlink()
        result = self.run_hook(script, {"cwd": str(project)})
        self.assertEqual(0, result.returncode, result.stderr)
        context = self.additional_context(result)
        self.assertIn("auto_approve_design=false", context)
        self.assertIn("repository settings reader is unavailable", context)

    def test_instruction_fragment_stays_static_without_stdin(self):
        script = ".agents/engineering/policy/session/scripts/session-context.py"
        result = self.run_without_stdin(script, ("--instruction-fragment",))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("auto_approve_design=", result.stdout)

    def test_user_prompt_context_includes_routine_delegation_guidance(self):
        script = ".agents/engineering/policy/session/scripts/session-context.py"
        contract = self.package / ".agents/engineering/policy/session/SKILL.md"
        headings = (
            "## When the user calls out a mistake",
            "## A task has an owning lifecycle — load it before the first edit",
            "## Repository routine-decision delegation",
        )
        body = contract.read_text(encoding="utf-8").split("\n---\n", 1)[1]
        expected = "\n\n".join(
            body.split(heading, 1)[1].split("\n## ", 1)[0].strip()
            for heading in headings
        )

        for prompt in (
            "What should I work on?",
            "Move these global plans to a shared docs repo like Concertable docs.",
        ):
            with self.subTest(prompt=prompt):
                result = self.run_hook(script, {"prompt": prompt}, arguments=("--prompt-context",))
                self.assertEqual(0, result.returncode, result.stderr)
                output = json.loads(result.stdout)["hookSpecificOutput"]
                self.assertEqual("UserPromptSubmit", output["hookEventName"])
                context = output["additionalContext"]
                source = context.split("\n\n", 1)[0].split("Source: ", 1)[1]
                self.assertTrue(source.endswith(str(
                    Path(".agents") / "engineering" / "policy" / "session" / "SKILL.md"
                )))
                self.assertIn("source SHA-256", context)
                self.assertIn(expected, context)
                self.assertTrue(context.split("\n\n", 1)[1].startswith(expected))
                self.assertIn("auto_approve_design=false", context)
                self.assertNotIn("## A link to another skill is a stage pointer", context)
                self.assertNotIn("## Keep large changes reviewable", context)
                self.assertLess(len(context), 4000)

        before = json.loads(self.run_hook(script, arguments=("--prompt-context",)).stdout)["hookSpecificOutput"]["additionalContext"]
        contract.write_text(contract.read_text(encoding="utf-8").replace(
            "Established standards defects follow",
            "Canonical source changed. Established standards defects follow",
        ), encoding="utf-8")
        after = json.loads(self.run_hook(script, arguments=("--prompt-context",)).stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertNotEqual(before, after)
        self.assertNotEqual(before.splitlines()[0], after.splitlines()[0])
        self.assertIn("Canonical source changed.", after)
        self.assertEqual([], list(self.cwd.iterdir()))

    def test_prompt_context_reports_missing_and_empty_sections(self):
        script = ".agents/engineering/policy/session/scripts/session-context.py"
        contract = self.package / ".agents/engineering/policy/session/SKILL.md"
        headings = (
            "## When the user calls out a mistake",
            "## A task has an owning lifecycle — load it before the first edit",
        )
        original = contract.read_text(encoding="utf-8")

        for heading in headings:
            with self.subTest(section=heading, defect="missing"):
                contract.write_text(
                    original.replace(heading, "## Replaced heading", 1), encoding="utf-8"
                )
                missing = self.run_hook(script, arguments=("--prompt-context",))
                self.assertNotEqual(0, missing.returncode)
                self.assertIn("missing prompt context section", missing.stderr)
                self.assertIn(heading, missing.stderr)
                self.assertEqual("", missing.stdout)

            with self.subTest(section=heading, defect="empty"):
                before, remainder = original.split(heading, 1)
                _, after = remainder.split("\n## ", 1)
                contract.write_text(
                    before + heading + "\n\n## " + after, encoding="utf-8"
                )
                empty = self.run_hook(script, arguments=("--prompt-context",))
                self.assertNotEqual(0, empty.returncode)
                self.assertIn("is empty", empty.stderr)
                self.assertIn(heading, empty.stderr)
                self.assertEqual("", empty.stdout)

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
