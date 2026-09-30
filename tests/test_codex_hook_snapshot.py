import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "codex_hook_snapshot", ROOT / ".agents" / "hooks" / "codex_hook_snapshot.py"
)
SNAPSHOT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SNAPSHOT)


class CodexHookSnapshotTests(unittest.TestCase):
    def test_each_generated_command_binds_to_its_package_bytes(self):
        for plugin in ("base", "engineering", "machine"):
            with self.subTest(plugin=plugin):
                root = ROOT / "plugins" / plugin
                expected = SNAPSHOT.digest_tree(root, plugin)
                manifest = json.loads((root / "hooks" / "codex.json").read_text(encoding="utf-8"))
                for groups in manifest["hooks"].values():
                    for group in groups:
                        for hook in group["hooks"]:
                            for field in ("command", "commandWindows"):
                                command = hook[field]
                                self.assertEqual(
                                    re.search(r"sha256:[0-9a-f]{64}", command).group(), expected
                                )

    def test_hook_survives_deleted_cache_path_and_rejects_modified_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            payload = temporary / "cache" / "base-agents" / "base" / "2.1.16"
            shutil.copytree(ROOT / "plugins" / "base", payload)
            data = temporary / "data"
            manifest = json.loads((payload / "hooks" / "codex.json").read_text(encoding="utf-8"))
            command = manifest["hooks"]["SessionStart"][0]["hooks"][0]["commandWindows"]
            command = command.replace("${PLUGIN_ROOT}", str(payload))
            environment = dict(os.environ, PLUGIN_DATA=str(data))

            first = subprocess.run(
                command, shell=True, cwd=ROOT, env=environment,
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            key = hashlib.sha256(str(payload).encode("utf-8")).hexdigest()
            snapshot = data / "hook-snapshots" / key
            self.assertTrue((snapshot / "hooks" / "codex_hook_snapshot.py").is_file())

            shutil.rmtree(payload)
            recovered = subprocess.run(
                command, shell=True, cwd=ROOT, env=environment,
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            first_context = json.loads(first.stdout)["hookSpecificOutput"]["additionalContext"]
            recovered_context = json.loads(recovered.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Maintained plan artifacts", first_context)
            self.assertIn("Maintained plan artifacts", recovered_context)

            pre_tool = manifest["hooks"]["PreToolUse"][0]["hooks"][0]["commandWindows"]
            pre_tool = pre_tool.replace("${PLUGIN_ROOT}", str(payload))
            routed = subprocess.run(
                pre_tool, shell=True, cwd=ROOT, env=environment,
                input=json.dumps({
                    "tool_name": "exec_command", "cwd": str(ROOT),
                    "tool_input": {"cmd": "echo read only"},
                }),
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(routed.returncode, 0, routed.stderr)

            (snapshot / "hooks" / "hook_runtime.py").write_text("changed", encoding="utf-8")
            rejected = subprocess.run(
                command, shell=True, cwd=ROOT, env=environment,
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(rejected.returncode, 2, rejected.stderr)
            self.assertIn("integrity check failed", rejected.stderr)


if __name__ == "__main__":
    unittest.main()
