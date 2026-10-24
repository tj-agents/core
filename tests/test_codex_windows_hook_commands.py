import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CodexWindowsHookCommands(unittest.TestCase):
    def test_authored_pretool_budgets_leave_time_for_host_response(self):
        names = []
        manifest = json.loads(
            (ROOT / ".agents" / "plugins" / "manifests" / "codex" / "engineering-hooks.json")
            .read_text(encoding="utf-8")
        )
        for group in manifest["hooks"]["PreToolUse"]:
            for hook in group["hooks"]:
                command = hook["commandWindows"]
                budget = float(re.search(r"--timeout (\d+)", command)[1])
                script = command.rsplit("/", 1)[-1].split('"', 1)[0]
                names.append(script)
                self.assertEqual(budget, 12)
                self.assertEqual(hook["timeout"] - budget, 3)
        self.assertCountEqual(names, ["git_auth_scope_gate.py", "delivery_binding_gate.py"])

    def test_every_plugin_uses_host_expanded_plugin_root_and_pretool_adapter(self):
        for name in ("base", "engineering", "machine"):
            with self.subTest(plugin=name):
                manifest = json.loads((ROOT / "plugins" / name / "hooks" / "codex.json").read_text(encoding="utf-8"))
                for event, groups in manifest["hooks"].items():
                    for group in groups:
                        for hook in group["hooks"]:
                            for platform in ("command", "commandWindows"):
                                command = hook[platform]
                                self.assertIn("${PLUGIN_ROOT}", command)
                                self.assertNotIn("%PLUGIN_ROOT%", command)
                                if event == "PreToolUse":
                                    self.assertIn("/hooks/pre_tool_use_adapter.py", command)
                                    self.assertTrue((ROOT / "plugins" / name / "hooks" / "pre_tool_use_adapter.py").is_file())


if __name__ == "__main__":
    unittest.main()
