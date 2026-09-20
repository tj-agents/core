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


if __name__ == "__main__":
    unittest.main()