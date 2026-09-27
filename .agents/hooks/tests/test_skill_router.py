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
        return env

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
