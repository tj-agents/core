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


class BaseRouterTests(unittest.TestCase):
    def test_base_package_blocks_missing_marketplace_without_engineering(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plugin = root / "base"
            repo = root / "repo"
            shutil.copytree(ROOT / "plugins/base", plugin)
            (repo / ".agents").mkdir(parents=True)
            (repo / ".git").mkdir()
            (repo / ".agents/skill-routes.json").write_text(json.dumps({
                "routes": [{"path": "^src/", "skills": ["missing-marketplace:never-shipped"]}]
            }), encoding="utf-8")
            environment = dict(os.environ, PLUGIN_ROOT=str(plugin), CLAUDE_PLUGIN_ROOT=str(plugin),
                               HOME=str(root / "home"), USERPROFILE=str(root / "home"))
            for host, tool, tool_input in (
                ("codex", "apply_patch", {"patch": "*** Begin Patch\n*** Add File: src/item.cpp\n+int x;\n*** End Patch"}),
                ("claude", "Write", {"file_path": "src/item.cpp", "content": "int x;"}),
            ):
                with self.subTest(host=host):
                    payload = {
                        "hook_event_name": "PreToolUse",
                        "tool_use_id": str(uuid.uuid4()),
                        "session_id": str(uuid.uuid4()),
                        "cwd": str(repo),
                        "tool_name": tool,
                        "tool_input": tool_input,
                    }
                    result = subprocess.run(
                        [sys.executable, "-B", str(plugin / "hooks/skill_router.py")],
                        cwd=repo, env=environment, input=json.dumps(payload),
                        capture_output=True, text=True, encoding="utf-8", timeout=20,
                    )
                    self.assertEqual(2, result.returncode, result.stderr)
                    self.assertIn("missing-marketplace:never-shipped", result.stderr)


if __name__ == "__main__":
    unittest.main()
