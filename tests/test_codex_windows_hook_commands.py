import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CodexWindowsHookCommands(unittest.TestCase):
    def test_every_plugin_uses_host_expanded_plugin_root(self):
        for name in ("base", "engineering", "workflow"):
            with self.subTest(plugin=name):
                payload = ROOT / "plugins" / name
                plugin = json.loads((payload / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
                if "hooks" not in plugin:
                    self.assertFalse((payload / "hooks" / "codex.json").exists())
                    continue
                manifest = json.loads((payload / plugin["hooks"]).read_text(encoding="utf-8"))
                for groups in manifest["hooks"].values():
                    for group in groups:
                        for hook in group["hooks"]:
                            for platform in ("command", "commandWindows"):
                                command = hook[platform]
                                self.assertIn("${PLUGIN_ROOT}", command)
                                self.assertNotIn("%PLUGIN_ROOT%", command)


if __name__ == "__main__":
    unittest.main()
