import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CodexWindowsHookCommands(unittest.TestCase):
    def test_every_plugin_uses_cmd_environment_syntax(self):
        for name in ("base", "engineering", "machine"):
            with self.subTest(plugin=name):
                manifest = json.loads((ROOT / "plugins" / name / "hooks" / "codex.json").read_text(encoding="utf-8"))
                for groups in manifest["hooks"].values():
                    for group in groups:
                        for hook in group["hooks"]:
                            command = hook["commandWindows"]
                            self.assertIn("%PLUGIN_ROOT%", command)
                            self.assertNotIn("${PLUGIN_ROOT}", command)

    @unittest.skipUnless(os.name == "nt", "Codex runs Windows hook commands through cmd.exe")
    def test_missing_marketplace_blocks_under_native_shell(self):
        with tempfile.TemporaryDirectory(prefix="codex windows hook ") as temporary:
            root = Path(temporary)
            plugin = root / "plugin with spaces"
            repo = root / "repo"
            shutil.copytree(ROOT / "plugins" / "base", plugin)
            (repo / ".agents").mkdir(parents=True)
            (repo / ".agents" / "skill-routes.json").write_text(
                json.dumps({"routes": [{"path": "^src/", "skills": ["missing-marketplace:never-shipped"]}]}),
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
            manifest = json.loads((plugin / "hooks" / "codex.json").read_text(encoding="utf-8"))
            command = manifest["hooks"]["PreToolUse"][0]["hooks"][0]["commandWindows"]
            payload = {
                "cwd": str(repo),
                "tool_name": "apply_patch",
                "tool_input": {"command": "*** Begin Patch\n*** Add File: src/probe.cpp\n+int probe = 1;\n*** End Patch"},
            }
            environment = dict(os.environ, PLUGIN_ROOT=str(plugin))
            result = subprocess.run(
                command, shell=True,
                input=json.dumps(payload), text=True, capture_output=True,
                cwd=repo, env=environment, timeout=20,
            )
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("missing-marketplace:never-shipped", result.stderr)
            self.assertFalse((repo / "src" / "probe.cpp").exists())


if __name__ == "__main__":
    unittest.main()
