import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
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
        for name in ("skill_router.py", "hook_runtime.py"):
            shutil.copy2(HOOKS / name, hooks / name)
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
        sys.path.insert(0, str(HOOKS))
        self.addCleanup(sys.path.remove, str(HOOKS))
        spec = importlib.util.spec_from_file_location(f"router_{uuid.uuid4().hex}", self.router)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def set_inventory(self, harness, value):
        inventory = json.loads(self.inventory.read_text(encoding="utf-8"))
        inventory[harness] = value
        self.inventory.write_text(json.dumps(inventory), encoding="utf-8")

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

    def test_local_alias_resolves_after_cached_native_discovery_failure(self):
        module = self.load_router()
        with patch.dict(os.environ, self.environment()), patch.object(
            module.shutil, "which", return_value=None
        ) as which, patch.object(module, "skill_aliases", return_value={
            "base:feature": "engineering:feature", "base:never-shipped": "engineering:never-shipped"
        }):
            for _ in range(2):
                self.assertIsNotNone(module.resolved_skill("base:feature", "codex"))
            with self.assertRaises(module.NativePluginDiscoveryError) as original:
                module.native_install_roots("codex")
            with self.assertRaises(module.NativePluginDiscoveryError) as missing:
                module.resolved_skill("base:never-shipped", "codex")
            self.assertIs(original.exception, missing.exception)
            which.assert_called_once_with("codex")

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
                        ((), {"tool_name": "apply_patch" if harness == "codex" else "Write",
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

    def test_claude_manifest_dispatch_passes_explicit_host_to_router(self):
        manifest = json.loads((HOOKS.parent / "plugins" / "manifests" / "claude" / "base-hooks.json").read_text(
            encoding="utf-8"
        ))
        group = manifest["hooks"]["PreToolUse"][0]
        self.assertEqual("Write|Edit|MultiEdit|NotebookEdit|Bash|PowerShell|Skill", group["matcher"])
        arguments = group["hooks"][0]["args"]
        self.assertEqual([
            "--hook", "${CLAUDE_PLUGIN_ROOT}/hooks/skill_router.py", "--harness", "claude",
            "--hook", "${CLAUDE_PLUGIN_ROOT}/hooks/tier_gate.py",
        ], arguments[4:])
        local_arguments = [str(self.router) if value.endswith("/skill_router.py") else
                           str(HOOKS / Path(value).name) if value.startswith("${CLAUDE_PLUGIN_ROOT}/hooks/") else value
                           for value in arguments]
        result = subprocess.run(
            [sys.executable, *local_arguments], cwd=self.repo,
            input=json.dumps(self.bash_payload(turn_id=str(uuid.uuid4()))), capture_output=True,
            text=True, encoding="utf-8", env=self.environment(), timeout=30,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        verdict = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual("deny", verdict["permissionDecision"])
        self.assertIn("Invoke the skill(s)", verdict["permissionDecisionReason"])
        self.assertNotIn("READ THIS WHOLE FILE", verdict["permissionDecisionReason"])

    def test_codex_manifest_pins_host_in_unix_and_windows_commands(self):
        manifest = json.loads((HOOKS.parent / "plugins" / "manifests" / "codex" / "base-hooks.json").read_text(
            encoding="utf-8"
        ))
        router = manifest["hooks"]["PreToolUse"][0]["hooks"][0]
        self.assertTrue(router["command"].endswith('"${PLUGIN_ROOT}/hooks/skill_router.py" --harness codex'))
        self.assertTrue(router["commandWindows"].endswith('"${PLUGIN_ROOT}/hooks/skill_router.py" --harness codex'))
        self.assertIn("--timeout 12", router["commandWindows"])

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
        result = self.run_router(payload={
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
        result = self.run_router(payload={
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
        result = self.run_router(payload={
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
        result = self.run_router(payload={
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
            result = self.run_router(payload={
                "hook_event_name": "PreToolUse",
                "tool_use_id": str(uuid.uuid4()),
                "session_id": session,
                "cwd": str(self.repo),
                "tool_name": "Write",
                "tool_input": {"file_path": "src/item.py", "content": "value = 2\n"},
            })
            self.assertEqual(2, result.returncode, result.stderr)
            self.assertIn("readable session transcript", result.stderr)


    def aliases(self, mapping):
        (self.plugin / "hooks" / "compatibility.json").write_text(
            json.dumps({"skills": mapping}), encoding="utf-8"
        )

    def test_a_moved_qualified_name_needs_an_explicit_alias(self):
        self.routes({"routes": [{"path": "^src/", "skills": ["base:feature"]}]})

        result = self.run_router(["--verify-install", "claude"])

        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        write = self.run_router(
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

    def test_the_alias_table_resolves_it_to_the_plugin_that_now_owns_it(self):
        self.routes({"routes": [{"path": "^src/", "skills": ["base:feature"]}]})
        self.aliases({"base:feature": "engineering:feature"})

        result = self.run_router(["--verify-install", "claude"])

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("resolves all 1 routed skill", result.stdout)

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

    def test_an_alias_to_a_skill_that_is_genuinely_absent_still_reports_missing(self):
        self.routes({"routes": [{"path": "^src/", "skills": ["base:feature"]}]})
        self.aliases({"base:feature": "engineering:never-shipped"})

        result = self.run_router(["--verify-install", "claude"])

        self.assertEqual(2, result.returncode)
        self.assertIn("base:feature", result.stdout)

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

    def test_an_alias_chain_is_followed_exactly_one_hop(self):
        self.routes({"routes": [{"path": "^src/", "skills": ["oldest:feature"]}]})
        self.aliases({"oldest:feature": "base:feature", "base:feature": "engineering:feature"})

        result = self.run_router(["--verify-install", "claude"])

        self.assertEqual(2, result.returncode, result.stdout + result.stderr)

    def test_an_unreadable_alias_table_leaves_resolution_where_it_was(self):
        self.routes({"routes": [{"path": "^src/", "skills": ["engineering:feature"]}]})
        (self.plugin / "hooks" / "compatibility.json").write_text("{not json", encoding="utf-8")

        result = self.run_router(["--verify-install", "claude"])

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_the_shipped_table_still_carries_the_rename_that_deadlocked_the_router(self):
        import importlib.util

        sys.path.insert(0, str(HOOKS))
        self.addCleanup(sys.path.remove, str(HOOKS))
        spec = importlib.util.spec_from_file_location("router_under_test", ROUTER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        aliases = module.skill_aliases()

        self.assertEqual("engineering:review-lifecycle", aliases["base:review-lifecycle"])
        self.assertNotIn("base:plan-artifacts", aliases)



if __name__ == "__main__":
    unittest.main()
