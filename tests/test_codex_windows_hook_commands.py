import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CodexWindowsHookCommands(unittest.TestCase):
    def test_every_plugin_uses_host_expanded_plugin_root(self):
        sources = json.loads((ROOT / ".agents/plugins/sources.json").read_text(encoding="utf-8"))
        declared = [
            name
            for name, hosts in sources["host_hook_sources"].items()
            if "codex" in hosts
        ]
        self.assertTrue(declared)
        for name in declared:
            with self.subTest(plugin=name):
                manifest = json.loads((ROOT / "plugins" / name / "hooks" / "codex.json").read_text(encoding="utf-8"))
                for groups in manifest["hooks"].values():
                    for group in groups:
                        for hook in group["hooks"]:
                            for platform in ("command", "commandWindows"):
                                command = hook[platform]
                                self.assertIn("${PLUGIN_ROOT}", command)
                                self.assertNotIn("%PLUGIN_ROOT%", command)


if __name__ == "__main__":
    unittest.main()
