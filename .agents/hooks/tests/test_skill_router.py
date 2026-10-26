import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch


HOOKS = Path(__file__).resolve().parents[1]
ROUTER = HOOKS / "skill_router.py"


class SkillRouterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.repo = self.base / "repo"
        (self.repo / ".agents").mkdir(parents=True)
        (self.repo / ".git").mkdir()
        (self.repo / "src").mkdir()
        (self.repo / "src" / "item.py").write_text("value = 1\n", encoding="utf-8")
        self.routes({"routes": [{"path": "^src/", "skills": ["feature"]}]})
        self.plugin = self.base / "engineering"
        hooks = self.plugin / "hooks"
        hooks.mkdir(parents=True)
        for name in ("skill_router.py", "tier_gate.py", "hook_runtime.py"):
            shutil.copy2(HOOKS / name, hooks / name)
        shutil.copy2(HOOKS.parent / "dependencies/agent/.agents/agent/runtime/required_plugins.py", hooks / "required_plugins.py")
        self.router = hooks / "skill_router.py"
        skill = self.plugin / "skills" / "feature"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: feature\ndescription: Implement an explicit feature completely.\n"
            "kind: workflow\ndomain: process\n---\n\n# Feature\n",
            encoding="utf-8",
        )
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.inventory = self.base / "inventory.json"
        self.inventory.write_text(json.dumps({"codex": {"installed": []}, "claude": []}), encoding="utf-8")
        self.inventory_calls = self.base / "inventory-calls.txt"
        inventory_script = self.bin / "inventory.py"
        inventory_script.write_text(
            "import json, pathlib, sys\n"
            f"inventory = json.loads(pathlib.Path({str(self.inventory)!r}).read_text(encoding='utf-8'))\n"
            f"with pathlib.Path({str(self.inventory_calls)!r}).open('a', encoding='utf-8') as calls:\n"
            "    calls.write(sys.argv[1] + '\\n')\n"
            "value = inventory[sys.argv[1]]\n"
            "if isinstance(value, dict) and '_exit' in value:\n"
            "    sys.exit(value['_exit'])\n"
            "print(value['_raw'] if isinstance(value, dict) and '_raw' in value else json.dumps(value))\n",
            encoding="utf-8",
        )
        for harness in ("codex", "claude"):
            if os.name == "nt":
                launcher = self.bin / f"{harness}.cmd"
                launcher.write_text(
                    f'@"{sys.executable}" "{inventory_script}" {harness} %*\n', encoding="utf-8"
                )
            else:
                launcher = self.bin / harness
                launcher.write_text(
                    f'#!{sys.executable}\nimport runpy, sys\nsys.argv.insert(1, {harness!r})\n'
                    f'runpy.run_path({str(inventory_script)!r}, run_name="__main__")\n',
                    encoding="utf-8",
                )
                launcher.chmod(0o755)

    def routes(self, value):
        (self.repo / ".agents" / "skill-routes.json").write_text(
            json.dumps(value), encoding="utf-8"
        )

    def environment(self):
        env = dict(os.environ)
        env["CLAUDE_PLUGIN_ROOT"] = str(self.plugin)
        env["PLUGIN_ROOT"] = str(self.plugin)
        env["HOME"] = str(self.base / "home")
        env["USERPROFILE"] = str(self.base / "home")
        env["CODEX_HOME"] = str(self.base / "home" / ".codex")
        env["CLAUDE_CONFIG_DIR"] = str(self.base / "home" / ".claude")
        env["PATH"] = str(self.bin) + os.pathsep + env.get("PATH", "")
        return env

    def load_router(self):
        sys.path.insert(0, str(self.router.parent))
        self.addCleanup(sys.path.remove, str(self.router.parent))
        spec = importlib.util.spec_from_file_location(f"router_{uuid.uuid4().hex}", self.router)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def set_inventory(self, harness, value):
        inventory = json.loads(self.inventory.read_text(encoding="utf-8"))
        inventory[harness] = value
        self.inventory.write_text(json.dumps(inventory), encoding="utf-8")

    def test_missing_selected_plugin_blocks_writes_even_without_routes(self):
        (self.repo / ".agents/skill-routes.json").unlink()
        (self.repo / ".agents/plugins.json").write_text(json.dumps({
            "schema_version": 1, "plugins": ["missing-stack@publisher"],
        }), encoding="utf-8")
        for harness, tool in (("codex", "apply_patch"), ("claude", "Write")):
            payload = {"cwd": str(self.repo), "tool_name": tool, "tool_input": (
                {"input": "*** Begin Patch\n*** Add File: src/new.py\n+value = 1\n*** End Patch"}
                if harness == "codex" else {"file_path": str(self.repo / "src/new.py"), "content": "value = 1"}
            )}
            result = subprocess.run([sys.executable, str(self.router), "--harness", harness],
                                    input=json.dumps(payload), capture_output=True, text=True,
                                    encoding="utf-8", env=self.environment(), cwd=self.repo)
            self.assertEqual(2, result.returncode, result.stderr)
            self.assertIn("missing-stack@publisher", result.stderr)

    def test_missing_admission_routes_the_agent_to_refresh(self):
        router = self.load_router()
        payload = {"cwd": str(self.repo), "session_id": "native-session", "agent_id": "child",
                   "tool_name": "Write", "tool_input": {"file_path": str(self.repo / "src/new.py"), "content": "value = 1"}}
        error = router.required_plugins.RequiredPluginsError("Invoke agent:refresh-plugins for claude in this project")
        with patch.object(router.required_plugins, "check", side_effect=error) as check, \
                patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), \
                patch.object(sys, "argv", [str(self.router), "--harness", "claude"]), \
                patch.object(sys, "stderr", io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as stopped:
                router.main()
        self.assertEqual(2, stopped.exception.code)
        check.assert_called_once_with(self.repo, "claude")
        self.assertIn("Invoke agent:refresh-plugins", stderr.getvalue())

    def test_stalled_admission_reports_recovery_through_both_host_wrappers(self):
        wrapper = self.base / "stalled router.py"
        wrapper.write_text(
            "import sys,time\n"
            f"sys.path.insert(0, {str(self.router.parent)!r})\n"
            "import skill_router as router\n"
            "router.required_plugins.check = lambda *args: time.sleep(30)\n"
            "router.main()\n", encoding="utf-8")
        payload = {"hook_event_name": "PreToolUse", "cwd": str(self.repo),
                   "session_id": "native-session", "tool_name": "Write",
                   "tool_input": {"file_path": str(self.repo / "src/new.py"), "content": "value = 1"}}
        commands = {
            "claude": [str(HOOKS / "hook_dispatch.py"), "--deadline", "0.5", "--hook", str(wrapper),
                       "--harness", "claude"],
            "codex": [str(HOOKS.parents[1] / ".codex/adapters/pre_tool_use.py"), "--timeout", "0.5",
                      str(wrapper), "--harness", "codex"],
        }
        for host, command in commands.items():
            with self.subTest(host=host):
                started = time.monotonic()
                result = subprocess.run([sys.executable, "-B", *command],
                                        input=json.dumps(payload), capture_output=True, text=True,
                                        encoding="utf-8", env=self.environment(), cwd=self.repo, timeout=5)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertLess(time.monotonic() - started, 4)
                decision = json.loads(result.stdout)["hookSpecificOutput"]
                self.assertEqual("deny", decision["permissionDecision"])
                self.assertIn("This tool call was NOT run", decision["permissionDecisionReason"])
                self.assertIn("agent:refresh-plugins", decision["permissionDecisionReason"])

    def test_skill_proof_keeps_company_and_stack_qualifiers_distinct(self):
        transcript = self.base / "transcript.jsonl"
        transcript.write_text("\n".join(json.dumps(item) for item in (
            {"message": {"content": [{"type": "tool_use", "name": "Skill", "id": "one",
                                      "input": {"skill": "stackx:style"}}]}},
            {"message": {"content": [{"type": "tool_result", "tool_use_id": "one",
                                      "is_error": False}]}},
        )), encoding="utf-8")
        outcomes = self.load_router().transcript_skill_outcomes(transcript)
        self.assertEqual(outcomes["stackx:style"], True)
        self.assertNotIn("acme-stackx:style", outcomes)

    def test_codex_proof_requires_the_company_plugin_path(self):
        transcript = self.base / "codex-transcript.jsonl"
        body = "---\nname: style\ndescription: Company style.\n---\nCompany body."
        def proof(plugin):
            return (
                {"type": "response_item", "payload": {"type": "custom_tool_call", "name": "exec",
                 "call_id": plugin, "input": "Get-Content C:/cache/market/" + plugin
                 + "/1/skills/style/SKILL.md"}},
                {"type": "response_item", "payload": {"type": "custom_tool_call_output",
                 "call_id": plugin, "output": [{"text": "Script completed\n" + body}]}},
            )
        module = self.load_router()
        skill = [("acme-stackx:style", self.base / "style/SKILL.md", body)]
        transcript.write_text("\n".join(json.dumps(item) for item in proof("stackx")), encoding="utf-8")
        self.assertNotIn("acme-stackx:style", module.transcript_skill_outcomes(transcript, skill))
        transcript.write_text("\n".join(json.dumps(item) for item in proof("acme-stackx")), encoding="utf-8")
        self.assertTrue(module.transcript_skill_outcomes(transcript, skill)["acme-stackx:style"])

    def test_codex_proof_requires_the_company_plugin_path(self):
        transcript = self.base / "codex-transcript.jsonl"
        body = "---\nname: style\ndescription: Company style.\n---\nCompany body."
        def proof(plugin):
            return (
                {"type": "response_item", "payload": {"type": "custom_tool_call", "name": "exec",
                 "call_id": plugin, "input": "Get-Content C:/cache/market/" + plugin
                 + "/1/skills/style/SKILL.md"}},
                {"type": "response_item", "payload": {"type": "custom_tool_call_output",
                 "call_id": plugin, "output": [{"text": "Script completed\n" + body}]}},
            )
        module = self.load_router()
        skill = [("acme-stackx:style", self.base / "style/SKILL.md", body)]
        transcript.write_text("\n".join(json.dumps(item) for item in proof("stackx")), encoding="utf-8")
        self.assertNotIn("acme-stackx:style", module.transcript_skill_outcomes(transcript, skill))
        transcript.write_text("\n".join(json.dumps(item) for item in proof("acme-stackx")), encoding="utf-8")
        self.assertTrue(module.transcript_skill_outcomes(transcript, skill)["acme-stackx:style"])

    def test_skill_proof_keeps_company_and_stack_qualifiers_distinct(self):
        transcript = self.base / "transcript.jsonl"
        transcript.write_text("\n".join(json.dumps(item) for item in (
            {"message": {"content": [{"type": "tool_use", "name": "Skill", "id": "one",
                                      "input": {"skill": "stackx:style"}}]}},
            {"message": {"content": [{"type": "tool_result", "tool_use_id": "one",
                                      "is_error": False}]}},
        )), encoding="utf-8")
        outcomes = self.load_router().transcript_skill_outcomes(transcript)
        self.assertEqual(outcomes["stackx:style"], True)
        self.assertNotIn("acme-stackx:style", outcomes)

    def test_codex_native_command_completion_proves_only_successful_matching_read(self):
        transcript = self.base / "native-command.jsonl"
        body = "---\nname: style\ndescription: Company style.\n---\nCompany body."
        skill = [("acme-stackx:style", self.base / "style/SKILL.md", body)]
        for status, code, plugin, output, expected in (
            ("completed", 0, "acme-stackx", body, True),
            ("completed", 1, "acme-stackx", body, False),
            ("failed", 0, "acme-stackx", body, False),
            ("inProgress", None, "acme-stackx", body, False),
            ("completed", 0, "stackx", body, False),
            ("completed", 0, "acme-stackx", "error reading file", False),
        ):
            with self.subTest(status=status, code=code, plugin=plugin, output=output):
                entry = {"type": "event_msg", "payload": {"type": "item_completed", "item": {
                    "type": "CommandExecution", "id": "native-command", "status": status,
                    "exit_code": code, "command": ["pwsh", "-Command", "Get-Content "
                        + f"C:/cache/{plugin}/local/skills/style/SKILL.md"],
                    "aggregated_output": output,
                }}}
                transcript.write_text(json.dumps(entry), encoding="utf-8")
                outcomes = self.load_router().transcript_skill_outcomes(transcript, skill)
                self.assertEqual(expected, outcomes.get("acme-stackx:style", False))

    def test_native_discovery_failures_are_typed_and_cached(self):
        cases = (
            (None, None, "unavailable"),
            ("codex", subprocess.TimeoutExpired("codex", 8), "timed out after 8 seconds"),
            ("codex", OSError("launch failed"), "could not run"),
            ("codex", subprocess.CompletedProcess([], 3, ""), "status 3"),
            ("codex", subprocess.CompletedProcess([], 0, "{"), "invalid JSON"),
            ("codex", subprocess.CompletedProcess([], 0, "{}"), "invalid roster"),
            ("codex", subprocess.CompletedProcess([], 0, "[]"), "invalid roster"),
            ("claude", subprocess.CompletedProcess([], 0, '{"installed": []}'), "invalid roster"),
        )
        for binary, result, expected in cases:
            with self.subTest(expected=expected, binary=binary):
                module = self.load_router()
                harness = binary or "codex"
                with patch.object(module.shutil, "which", return_value=binary) as which, patch.object(
                    module.subprocess, "run",
                    side_effect=result if isinstance(result, Exception) else None,
                    return_value=result,
                ) as run:
                    errors = []
                    for _ in range(2):
                        with self.assertRaises(module.NativePluginDiscoveryError) as raised:
                            module.native_install_roots(harness)
                        self.assertIn(expected, str(raised.exception))
                        errors.append(raised.exception)
                    self.assertIs(errors[0], errors[1])
                    which.assert_called_once_with(harness)
                    self.assertEqual(0 if binary is None else 1, run.call_count)
                    if binary is not None:
                        self.assertEqual(8, run.call_args.kwargs["timeout"])

    def test_successful_native_inventory_is_cached_and_resolves_enabled_plugins(self):
        module = self.load_router()
        other = self.base / "other"
        with patch.object(module.shutil, "which", return_value="claude"), patch.object(
            module.subprocess, "run", return_value=subprocess.CompletedProcess(
                [], 0, json.dumps([{"enabled": True, "installPath": str(other)},
                                   {"enabled": False, "installPath": str(self.base / "disabled")}])
            )
        ) as run:
            self.assertEqual((other,), module.native_install_roots("claude"))
            self.assertEqual((other,), module.native_install_roots("claude"))
            run.assert_called_once()

    def test_own_and_linked_skills_resolve_without_native_discovery(self):
        module = self.load_router()
        linked = self.base / "home" / ".agents" / "skills" / "linked"
        linked.mkdir(parents=True)
        (linked / "SKILL.md").write_text("---\ndescription: Linked skill.\n---\n", encoding="utf-8")
        with patch.dict(os.environ, self.environment()), patch.object(
            module.shutil, "which", side_effect=AssertionError("CLI lookup was unnecessary")
        ):
            self.assertIsNotNone(module.resolved_skill("engineering:feature", "codex"))
            self.assertIsNotNone(module.resolved_skill("linked", "codex"))

    def test_native_enabled_plugin_skills_resolve_for_both_harnesses(self):
        self.routes({"routes": [{"path": "^src/", "skills": ["installed:native"]}]})
        for harness in ("codex", "claude"):
            root = (self.base / "home" / ".codex" / "plugins" / "cache" / "marketplace"
                    / "installed" / "1.0") if harness == "codex" else self.base / "installed"
            skill = root / "skills" / "native"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\ndescription: Native installed skill.\n---\n", encoding="utf-8")
            inventory = {"installed": [{"enabled": True, "marketplaceName": "marketplace",
                                         "name": "installed", "version": "1.0"}]} if harness == "codex" else [
                {"enabled": True, "installPath": str(root)}
            ]
            self.set_inventory(harness, inventory)
            self.inventory_calls.unlink(missing_ok=True)
            result = self.run_router(("--verify-install", harness))
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual([harness], self.inventory_calls.read_text(encoding="utf-8").splitlines())

    def test_discovery_failures_block_hook_and_verify_with_infrastructure_diagnostic(self):
        self.routes({"routes": [{"path": "^src/", "skills": ["missing:one", "missing:two"]}]})
        for harness in ("codex", "claude"):
            for value in ({"_exit": 7}, {"_raw": "{"}, {"installed": "invalid"}):
                with self.subTest(harness=harness, value=value):
                    self.set_inventory(harness, value)
                    for arguments, payload in (
                        (("--verify-install", harness), None),
                        (("--harness", harness), {
                              "tool_name": "apply_patch" if harness == "codex" else "Write",
                              "cwd": str(self.repo), "session_id": str(uuid.uuid4()),
                              "tool_input": {"file_path": "src/item.py", "content": "value = 2\n"}}),
                    ):
                        self.inventory_calls.unlink(missing_ok=True)
                        result = self.run_router(arguments, payload)
                        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
                        self.assertIn("native plugin discovery infrastructure error", result.stderr)
                        self.assertNotIn("unavailable standards", result.stderr)
                        self.assertNotIn("Install or enable", result.stdout + result.stderr)
                        self.assertNotIn("Traceback", result.stderr)
                        self.assertEqual([harness], self.inventory_calls.read_text(encoding="utf-8").splitlines())

    def test_valid_empty_inventory_reports_missing_standards(self):
        self.routes({"routes": [{"path": "^src/", "skills": ["missing:one", "missing:two"]}]})
        for harness in ("codex", "claude"):
            self.inventory_calls.unlink(missing_ok=True)
            result = self.run_router(("--verify-install", harness))
            self.assertEqual(2, result.returncode, result.stdout + result.stderr)
            self.assertIn("missing 2 of 2", result.stdout)
            self.assertNotIn("infrastructure", result.stdout + result.stderr)
            self.assertEqual([harness], self.inventory_calls.read_text(encoding="utf-8").splitlines())

    def bash_payload(self, **extra):
        return {
            "hook_event_name": "PreToolUse", "tool_name": "Bash", "cwd": str(self.repo),
            "tool_use_id": str(uuid.uuid4()), "session_id": str(uuid.uuid4()),
            "tool_input": {"command": "echo value > src/item.py"}, **extra,
        }

    def test_explicit_claude_bash_with_turn_id_uses_claude_skill_proof(self):
        payload = self.bash_payload(turn_id=str(uuid.uuid4()))
        result = self.run_router(("--harness", "claude"), payload)
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn("Invoke the skill(s)", result.stderr)
        self.assertNotIn("READ THIS WHOLE FILE", result.stderr)
        transcript = self.base / "claude-transcript.jsonl"
        transcript.write_text("\n".join(json.dumps(entry) for entry in (
            {"message": {"content": [{"type": "tool_use", "name": "Skill", "id": "loaded",
                                       "input": {"skill": "feature"}}]}},
            {"message": {"content": [{"type": "tool_result", "tool_use_id": "loaded",
                                       "content": "Feature loaded."}]}},
        )), encoding="utf-8")
        payload["transcript_path"] = str(transcript)
        payload["tool_use_id"] = str(uuid.uuid4())
        result = self.run_router(("--harness", "claude"), payload)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_explicit_codex_bash_without_turn_id_requires_file_read_proof(self):
        result = self.run_router(("--harness", "codex"), self.bash_payload())
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn("READ THIS WHOLE FILE", result.stderr)
        self.assertIn("Read each file named above", result.stderr)
        self.assertNotIn("Invoke the skill(s)", result.stderr)

    def test_explicit_harness_does_not_route_nonwrite_tools(self):
        self.routes({"routes": [{"path": "^src/", "skills": ["missing:feature"]}]})
        for harness in ("codex", "claude"):
            result = self.run_router(("--harness", harness), self.bash_payload(tool_name="Read"))
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual("", result.stderr)
        self.assertFalse(self.inventory_calls.exists())

    def test_invalid_or_missing_explicit_harness_fails_closed(self):
        for arguments in (("--harness",), ("--harness", "other")):
            result = self.run_router(arguments, self.bash_payload())
            self.assertEqual(2, result.returncode, result.stdout + result.stderr)
            self.assertIn("--harness requires claude or codex", result.stderr)

    def run_router(self, arguments=(), payload=None):
        return subprocess.run(
            [sys.executable, "-B", str(self.router), *arguments],
            cwd=self.repo,
            input=(json.dumps(payload) if payload is not None else None),
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=self.environment(),
            timeout=20,
        )

    def test_query_returns_the_skill_owned_by_a_changed_path(self):
        result = subprocess.run(
            [sys.executable, "-B", str(self.router), "--skills-for", "--json"],
            cwd=self.repo,
            input="src/item.py\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=self.environment(),
            timeout=20,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual({"feature": ["src/item.py"]}, json.loads(result.stdout)["skills"])

    def test_query_ignores_a_path_outside_the_repository(self):
        result = self.run_router(("--skills-for", "--json", "src/item.py", str(self.base / "outside.py")))
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual({"feature": ["src/item.py"]}, json.loads(result.stdout)["skills"])

    def test_malformed_opt_in_table_fails_closed(self):
        (self.repo / ".agents" / "skill-routes.json").write_text("{", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-B", str(self.router), "--skills-for", "--json"],
            cwd=self.repo,
            input="src/item.py\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=self.environment(),
            timeout=20,
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("table exists", result.stdout)

    def test_write_outside_repo_does_not_consult_its_broken_routes(self):
        (self.repo / ".agents" / "skill-routes.json").write_text("{", encoding="utf-8")
        result = self.run_router(
            ("--harness", "claude"),
            payload={
                "hook_event_name": "PreToolUse",
                "tool_use_id": str(uuid.uuid4()),
                "session_id": str(uuid.uuid4()),
                "cwd": str(self.repo),
                "tool_name": "Write",
                "tool_input": {"file_path": str(self.base / "outside.py"), "content": "value = 2\n"},
            }
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("", result.stderr)

    def test_first_routed_write_blocks_with_the_owning_skill(self):
        result = self.run_router(
            ("--harness", "claude"),
            payload={
                "hook_event_name": "PreToolUse",
                "tool_use_id": str(uuid.uuid4()),
                "session_id": str(uuid.uuid4()),
                "cwd": str(self.repo),
                "tool_name": "Write",
                "tool_input": {"file_path": "src/item.py", "content": "value = 2\n"},
            }
        )
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("feature", result.stderr)
        self.assertIn("Implement an explicit feature completely", result.stderr)

    def test_shell_read_of_a_routed_path_is_not_treated_as_a_write(self):
        result = self.run_router(
            ("--harness", "claude"),
            payload={
                "hook_event_name": "PreToolUse",
                "tool_use_id": str(uuid.uuid4()),
                "session_id": str(uuid.uuid4()),
                "cwd": str(self.repo),
                "tool_name": "Bash",
                "tool_input": {"command": "cat src/item.py"},
            }
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)

    def test_quoted_arrow_in_inline_python_is_not_a_redirect(self):
        result = self.run_router(
            ("--harness", "claude"),
            payload={
                "hook_event_name": "PreToolUse",
                "tool_use_id": str(uuid.uuid4()),
                "session_id": str(uuid.uuid4()),
                "cwd": str(self.repo),
                "tool_name": "Bash",
                "tool_input": {"command": "python -c \"print('value -> src/item.py')\""},
            }
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)

    def test_redirect_in_inline_shell_still_routes_the_write(self):
        result = self.run_router(
            ("--harness", "claude"),
            payload={
                "hook_event_name": "PreToolUse",
                "tool_use_id": str(uuid.uuid4()),
                "session_id": str(uuid.uuid4()),
                "cwd": str(self.repo),
                "tool_name": "Bash",
                "tool_input": {"command": "bash -c 'echo value > src/item.py'"},
            }
        )
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("feature", result.stderr)

    def test_repository_without_a_route_table_is_silent(self):
        (self.repo / ".agents" / "skill-routes.json").unlink()
        result = self.run_router(
            ("--harness", "claude"),
            payload={
                "hook_event_name": "PreToolUse",
                "tool_use_id": str(uuid.uuid4()),
                "session_id": str(uuid.uuid4()),
                "cwd": str(self.repo),
                "tool_name": "Write",
                "tool_input": {"file_path": "src/item.py", "content": "value = 2\n"},
            }
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_missing_marketplace_blocks_unrouted_claude_write(self):
        self.routes({"routes": [{"path": "^src/", "skills": ["missing-marketplace:never-shipped"]}]})
        result = self.run_router(("--harness", "claude"), payload={
            "hook_event_name": "PreToolUse",
            "tool_use_id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "cwd": str(self.repo),
            "tool_name": "Write",
            "tool_input": {"file_path": "notes.txt", "content": "new\n"},
        })
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("missing-marketplace:never-shipped", result.stderr)

    def test_missing_marketplace_blocks_nested_codex_edit(self):
        self.routes({"routes": [{"path": "^src/", "skills": ["missing-marketplace:never-shipped"]}]})
        result = self.run_router(("--harness", "codex"), payload={
            "hook_event_name": "PreToolUse",
            "tool_use_id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "cwd": str(self.repo),
            "tool_name": "apply_patch",
            "tool_input": {"patch": "*** Begin Patch\n*** Update File: src/item.py\n+value = 2\n*** End Patch"},
        })
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("missing-marketplace:never-shipped", result.stderr)

    def test_nested_codex_shell_write_needs_skill_proof(self):
        result = self.run_router(("--harness", "codex"), payload={
            "hook_event_name": "PreToolUse",
            "tool_use_id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "cwd": str(self.repo),
            "tool_name": "exec_command",
            "tool_input": {"cmd": "echo value > src/item.py"},
        })
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("readable session transcript", result.stderr)

    def test_codex_canonical_bash_uses_codex_registry(self):
        self.routes({"routes": [{"path": "^src/", "skills": ["missing-marketplace:never-shipped"]}]})
        result = self.run_router(("--harness", "codex"), payload={
            "hook_event_name": "PreToolUse",
            "tool_use_id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "turn_id": str(uuid.uuid4()),
            "cwd": str(self.repo),
            "tool_name": "Bash",
            "tool_input": {"command": "echo value > src/item.py"},
        })
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("for codex", result.stderr)

    def test_missing_transcript_never_trusts_a_repeated_routed_write(self):
        session = str(uuid.uuid4())
        for _ in range(2):
            result = self.run_router(("--harness", "claude"), payload={
                "hook_event_name": "PreToolUse",
                "tool_use_id": str(uuid.uuid4()),
                "session_id": session,
                "cwd": str(self.repo),
                "tool_name": "Write",
                "tool_input": {"file_path": "src/item.py", "content": "value = 2\n"},
            })
            self.assertEqual(2, result.returncode, result.stderr)
            self.assertIn("readable session transcript", result.stderr)


    def test_a_moved_qualified_name_stays_unresolved(self):
        self.routes({"routes": [{"path": "^src/", "skills": ["base:feature"]}]})

        result = self.run_router(["--verify-install", "claude"])

        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        write = self.run_router(
            ("--harness", "claude"),
            payload={
                "hook_event_name": "PreToolUse",
                "tool_use_id": str(uuid.uuid4()),
                "session_id": str(uuid.uuid4()),
                "cwd": str(self.repo),
                "tool_name": "Write",
                "tool_input": {"file_path": "src/item.py", "content": "value = 2\n"},
            }
        )
        self.assertEqual(2, write.returncode, write.stderr)
        self.assertIn("base:feature", write.stderr)

    def test_a_qualified_name_with_two_other_providers_stays_unresolved(self):
        import importlib.util

        sys.path.insert(0, str(HOOKS))
        self.addCleanup(sys.path.remove, str(HOOKS))
        spec = importlib.util.spec_from_file_location("router_with_two_providers", ROUTER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        roots = []
        for plugin in ("first", "second"):
            root = self.base / "cache" / "marketplace" / plugin / "1.0" / "skills"
            skill = root / "feature"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: feature\ndescription: Feature work.\n---\n", encoding="utf-8"
            )
            roots.append(root)
        with patch.object(module, "skill_search_dirs", return_value=roots):
            self.assertIsNone(module.resolved_skill("missing:feature", "claude"))

    def test_stale_codex_cache_does_not_count_as_an_enabled_plugin(self):
        self.routes({"routes": [{"path": "^src/", "skills": ["disabled:feature"]}]})
        skill = self.base / "home/.codex/plugins/cache/disabled/feature/1.0/skills/feature"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: feature\n---\n", encoding="utf-8")

        result = self.run_router(["--verify-install", "codex"])

        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn("disabled:feature", result.stdout)

    def test_stale_claude_manifest_does_not_count_as_an_enabled_plugin(self):
        self.routes({"routes": [{"path": "^src/", "skills": ["disabled:feature"]}]})
        plugin = self.base / "home/.claude/plugins/cache/disabled/feature/1.0"
        skill = plugin / "skills/feature"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: feature\n---\n", encoding="utf-8")
        manifest = self.base / "home/.claude/plugins/installed_plugins.json"
        manifest.write_text(json.dumps({"plugins": {"feature@disabled": [
            {"installPath": str(plugin)}
        ]}}), encoding="utf-8")

        result = self.run_router(["--verify-install", "claude"])

        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn("disabled:feature", result.stdout)

    def install_stack_tier(self):
        (self.repo / ".agents" / "skill-routes.json").unlink()
        payload = self.base / "home" / ".claude" / "plugins" / "cache" / "market" / "stackx" / "1"
        skill = payload / "skills" / "style"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: style\ndescription: Stack style for every source file.\nkind: contract\n---\n",
            encoding="utf-8",
        )
        self.declare_stack_tier([{"path": r"\.sx$", "skills": ["stackx:style"]}])
        return skill / "SKILL.md"

    def declare_stack_tier(self, routes=None):
        tier = {
            "schema_version": 1, "tier": "stackx", "stack": "StackX", "applies": "stack-present",
            "detect": {"files": ["stack.marker"]},
        }
        if routes is not None:
            tier["routes"] = routes
        (self.base / "home" / ".claude" / "plugins" / "cache" / "market" / "stackx" / "1" / "tier.json").write_text(
            json.dumps(tier), encoding="utf-8")

    def write_payload(self, session, transcript=None, **extra):
        payload = {
            "hook_event_name": "PreToolUse", "tool_use_id": str(uuid.uuid4()), "session_id": session,
            "cwd": str(self.repo), "tool_name": "Write",
            "tool_input": {"file_path": "src/item.sx", "content": "value\n"}, **extra,
        }
        if transcript is not None:
            payload["transcript_path"] = str(transcript)
        return payload

    def transcript(self, path, *blocks):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps({"message": {"content": [block]}}) for block in blocks),
                        encoding="utf-8")
        return path

    def test_applicable_tier_routes_gate_a_repository_without_its_own_table(self):
        self.install_stack_tier()
        session = str(uuid.uuid4())
        transcript = self.base / "sessions" / f"{session}.jsonl"
        self.transcript(transcript, {"type": "text", "text": "no skills"})

        result = self.run_router(("--harness", "claude"), self.write_payload(session, transcript))
        self.assertEqual(0, result.returncode, result.stderr)

        (self.repo / "stack.marker").write_text("", encoding="utf-8")
        result = self.run_router(("--harness", "claude"), self.write_payload(session, transcript))
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("stackx:style", result.stderr)
        self.assertIn("Stack style for every source file", result.stderr)

        self.transcript(
            transcript,
            {"type": "tool_use", "name": "Skill", "id": "load", "input": {"skill": "stackx:style"}},
            {"type": "tool_result", "tool_use_id": "load", "content": "loaded"},
        )
        result = self.run_router(("--harness", "claude"), self.write_payload(session, transcript))
        self.assertEqual(0, result.returncode, result.stderr)

    def test_subagent_proves_its_own_load_and_a_whole_file_read_counts(self):
        skill_file = self.install_stack_tier()
        (self.repo / "stack.marker").write_text("", encoding="utf-8")
        session = str(uuid.uuid4())
        parent = self.transcript(
            self.base / "sessions" / f"{session}.jsonl",
            {"type": "tool_use", "name": "Skill", "id": "load", "input": {"skill": "stackx:style"}},
            {"type": "tool_result", "tool_use_id": "load", "content": "loaded"},
        )
        result = self.run_router(("--harness", "claude"), self.write_payload(session, parent))
        self.assertEqual(0, result.returncode, result.stderr)

        agent = "a0123456789abcdef"
        subagent = self.write_payload(session, parent, agent_id=agent, agent_type="engineering:lane-l4")
        result = self.run_router(("--harness", "claude"), dict(subagent, tool_use_id=str(uuid.uuid4())))
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("READ THIS WHOLE FILE", result.stderr)
        self.assertIn("parent loaded", result.stderr)

        own = self.base / "sessions" / session / "subagents" / f"agent-{agent}.jsonl"
        self.transcript(
            own,
            {"type": "tool_use", "name": "Read", "id": "part",
             "input": {"file_path": str(skill_file), "offset": 20, "limit": 5}},
            {"type": "tool_result", "tool_use_id": "part", "content": "partial"},
        )
        result = self.run_router(("--harness", "claude"), dict(subagent, tool_use_id=str(uuid.uuid4())))
        self.assertEqual(2, result.returncode, result.stderr)

        self.transcript(
            own,
            {"type": "tool_use", "name": "Read", "id": "whole", "input": {"file_path": str(skill_file)}},
            {"type": "tool_result", "tool_use_id": "whole", "content": "body"},
        )
        result = self.run_router(("--harness", "claude"), dict(subagent, tool_use_id=str(uuid.uuid4())))
        self.assertEqual(0, result.returncode, result.stderr)

    def test_absolute_write_into_a_sibling_worktree_is_gated_by_that_worktree(self):
        self.install_stack_tier()
        sibling = self.base / "repo.worktrees" / "feature"
        (sibling / "src").mkdir(parents=True)
        (sibling / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
        (sibling / "stack.marker").write_text("", encoding="utf-8")
        payload = self.write_payload(str(uuid.uuid4()))
        payload["tool_input"]["file_path"] = str(sibling / "src" / "item.sx")
        result = self.run_router(("--harness", "claude"), payload)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("stackx:style", result.stderr)

    def test_malformed_routes_on_a_v3_tier_still_fail_closed(self):
        self.install_stack_tier()
        (self.repo / "stack.marker").write_text("", encoding="utf-8")
        (self.base / "home" / ".claude" / "plugins" / "cache" / "market" / "stackx" / "1" / "tier.json").write_text(
            json.dumps({"schema_version": 3, "tier": "stackx", "applies": "stack-present",
                        "detect": {"file": "stack.marker"},
                        "routes": [{"path": r"\.sx$", "skills": ["stackx:style"], "content_requires": ["x"]}]}),
            encoding="utf-8")
        result = self.run_router(("--harness", "claude"), self.write_payload(str(uuid.uuid4())))
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("tier.json routes are unusable", result.stderr)

    def test_a_repo_table_adds_to_tier_routes_instead_of_replacing_them(self):
        self.install_stack_tier()
        (self.repo / "stack.marker").write_text("", encoding="utf-8")
        self.routes({"routes": [{"path": "^docs/", "skills": ["feature"]}]})
        result = self.run_router(("--harness", "claude"), self.write_payload(str(uuid.uuid4())))
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("stackx:style", result.stderr)

    def test_an_always_applicable_tier_enforces_its_routes(self):
        self.install_stack_tier()
        (self.base / "home" / ".claude" / "plugins" / "cache" / "market" / "stackx" / "1" / "tier.json").write_text(
            json.dumps({"schema_version": 1, "tier": "stackx", "applies": "always",
                        "routes": [{"path": r"\.sx$", "skills": ["stackx:style"]}]}),
            encoding="utf-8")
        result = self.run_router(("--harness", "claude"), self.write_payload(str(uuid.uuid4())))
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("stackx:style", result.stderr)

    def test_one_write_into_two_routed_repositories_must_be_split(self):
        self.install_stack_tier()
        (self.repo / "stack.marker").write_text("", encoding="utf-8")
        sibling = self.base / "repo.worktrees" / "feature"
        (sibling / "src").mkdir(parents=True)
        (sibling / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
        (sibling / "stack.marker").write_text("", encoding="utf-8")
        payload = self.write_payload(str(uuid.uuid4()), tool_name="Bash", tool_input={
            "command": f"echo a > {(self.repo / 'src' / 'a.sx').as_posix()} && echo b > {(sibling / 'src' / 'b.sx').as_posix()}"})
        result = self.run_router(("--harness", "claude"), payload)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("more than one routed repository", result.stderr)

    def sibling_repository(self):
        sibling = self.base / "repo.worktrees" / "feature"
        (sibling / "src").mkdir(parents=True)
        (sibling / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
        (sibling / "stack.marker").write_text("", encoding="utf-8")
        return sibling

    def test_a_relative_write_into_a_routed_sibling_is_resolved_from_the_session_directory(self):
        self.install_stack_tier()
        self.sibling_repository()
        session_directory = self.repo / "src"
        payload = self.write_payload(str(uuid.uuid4()), tool_name="Bash", cwd=str(session_directory),
                                     tool_input={"command": "echo b > ../../repo.worktrees/feature/src/b.sx"})
        result = self.run_router(("--harness", "claude"), payload)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("src/b.sx", result.stderr)

    def test_an_unrouted_relative_target_is_not_checked_against_a_routed_sibling(self):
        self.install_stack_tier()
        sibling = self.sibling_repository()
        payload = self.write_payload(str(uuid.uuid4()), tool_name="Bash", tool_input={
            "command": f"echo a > src/a.sx && echo b > {(sibling / 'src' / 'b.sx').as_posix()}"})
        result = self.run_router(("--harness", "claude"), payload)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("src/b.sx", result.stderr)
        self.assertNotIn("src/a.sx", result.stderr)

    def test_git_bash_drive_paths_resolve_to_windows_paths_only_on_windows(self):
        module = self.load_router()
        with patch.object(module.os, "name", "nt"):
            self.assertEqual("C:/Users/me/repo/a.cs", module.native_path("/c/Users/me/repo/a.cs"))
            self.assertEqual("src/a.cs", module.native_path("src/a.cs"))
        with patch.object(module.os, "name", "posix"):
            self.assertEqual("/c/Users/me/repo/a.cs", module.native_path("/c/Users/me/repo/a.cs"))

    def test_route_validation_rejects_rows_that_would_crash_at_match_time(self):
        module = self.load_router()
        validate = module.tier_gate.route_diagnostics
        self.assertEqual([], validate([{"path": r"\.cs$", "skills": ["dotnet:style"], "content_requires": "//"}]))
        for row in ({"path": r"\.cs$", "skills": ["dotnet:style"], "content_requires": ["//"]},
                    {"path": r"\.cs$", "skills": ["style"]},
                    {"path": r"\.cs$", "skills": ["dotnet:style"], "deny": ["x"]},
                    {"path": "(", "skills": ["dotnet:style"]}):
            with self.subTest(row=row):
                self.assertEqual(1, len(validate([row])))

    def test_main_session_read_of_a_skill_file_is_not_an_invocation(self):
        skill_file = self.install_stack_tier()
        (self.repo / "stack.marker").write_text("", encoding="utf-8")
        session = str(uuid.uuid4())
        transcript = self.transcript(
            self.base / "sessions" / f"{session}.jsonl",
            {"type": "tool_use", "name": "Read", "id": "whole", "input": {"file_path": str(skill_file)}},
            {"type": "tool_result", "tool_use_id": "whole", "content": "body"},
        )
        result = self.run_router(("--harness", "claude"), self.write_payload(session, transcript))
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("Invoke the skill(s)", result.stderr)

    def test_malformed_tier_routes_fail_closed(self):
        self.install_stack_tier()
        (self.repo / "stack.marker").write_text("", encoding="utf-8")
        self.declare_stack_tier([{"path": "(", "skills": ["stackx:style"]}])
        result = self.run_router(("--harness", "claude"), self.write_payload(str(uuid.uuid4())))
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("tier.json routes are unusable", result.stderr)

    def test_tier_statement_names_the_write_gate_only_for_a_routed_tier(self):
        self.install_stack_tier()
        (self.repo / "stack.marker").write_text("", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-B", str(self.plugin / "hooks" / "tier_gate.py"), "--session-context"],
            cwd=self.repo, capture_output=True, text=True, encoding="utf-8", env=self.environment(), timeout=20,
        )
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("`stackx:*` - StackX detected (stack.marker). Load its skills before writing", context)
        self.declare_stack_tier()
        result = subprocess.run(
            [sys.executable, "-B", str(self.plugin / "hooks" / "tier_gate.py"), "--session-context"],
            cwd=self.repo, capture_output=True, text=True, encoding="utf-8", env=self.environment(), timeout=20,
        )
        self.assertNotIn("write gate", json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"])

    def test_claude_manifest_dispatches_router_for_every_write_tool_and_blocks_on_failure(self):
        manifest = json.loads((HOOKS.parent / "plugins" / "manifests" / "claude" / "base-hooks.json").read_text(
            encoding="utf-8"
        ))
        group = manifest["hooks"]["PreToolUse"][0]
        self.assertEqual("Write|Edit|MultiEdit|NotebookEdit|Bash|PowerShell", group["matcher"])
        hook = group["hooks"][0]
        self.assertEqual("block", hook["onFailure"])
        arguments = hook["args"]
        self.assertEqual(["--hook", "${CLAUDE_PLUGIN_ROOT}/hooks/skill_router.py",
                          "--harness", "claude"], arguments[4:])
        local_arguments = [str(self.router) if value.endswith("/skill_router.py") else
                           str(HOOKS / Path(value).name) if value.startswith("${CLAUDE_PLUGIN_ROOT}/hooks/") else value
                           for value in arguments]
        result = subprocess.run(
            [sys.executable, *local_arguments], cwd=self.repo,
            input=json.dumps(self.bash_payload()), capture_output=True,
            text=True, encoding="utf-8", env=self.environment(), timeout=30,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        verdict = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual("deny", verdict["permissionDecision"])
        self.assertIn("Invoke the skill(s)", verdict["permissionDecisionReason"])

    def test_codex_manifest_pins_host_in_unix_and_windows_commands(self):
        manifest = json.loads((HOOKS.parent / "plugins" / "manifests" / "codex" / "base-hooks.json").read_text(
            encoding="utf-8"
        ))
        group = manifest["hooks"]["PreToolUse"][0]
        self.assertIn("apply_patch", group["matcher"].split("|"))
        router = group["hooks"][0]
        self.assertTrue(router["command"].endswith('"${PLUGIN_ROOT}/hooks/skill_router.py" --harness codex'))
        self.assertTrue(router["commandWindows"].endswith('"${PLUGIN_ROOT}/hooks/skill_router.py" --harness codex'))



if __name__ == "__main__":
    unittest.main()
