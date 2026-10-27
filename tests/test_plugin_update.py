import importlib.util
from pathlib import Path
import json
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("plugin_update", ROOT / "scripts/update_plugin_digests.py")
updater = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(updater)


class PluginUpdateTests(unittest.TestCase):
    def test_harness_change_converges_without_a_manual_plugin_roster_edit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for name in (".agents", ".codex", ".claude"):
                shutil.copytree(ROOT / name, root / name,
                                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "continuation"))
            path = root / ".agents/plugins/harness/engineering.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["requires"]["permissions"]["claude_allow"].append("Bash(python -B fixture.py)")
            path.write_text(json.dumps(manifest), encoding="utf-8")
            roster_path = root / ".agents/plugins/plugins.json"
            before = roster_path.read_bytes()
            with self.assertRaisesRegex(ValueError, "Stale plugin entries"):
                updater.update(root, check=True)
            self.assertEqual(before, roster_path.read_bytes())
            updater.update(root, check=False)
            updater.update(root, check=True)
            updater.SYNC.build(root)
            roster = json.loads(roster_path.read_text(encoding="utf-8"))
            engineering = next(item for item in roster["packages"] if item["name"] == "engineering")
            self.assertEqual(manifest["requires"], engineering["harness"])


if __name__ == "__main__":
    unittest.main()
