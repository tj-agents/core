import importlib.util
from pathlib import Path
import json
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("catalog_update", ROOT / "scripts/update_catalog_digests.py")
updater = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(updater)


class CatalogUpdateTests(unittest.TestCase):
    def test_harness_change_converges_without_a_manual_catalog_edit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for name in (".agents", ".codex", ".claude"):
                shutil.copytree(ROOT / name, root / name,
                                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "continuation"))
            path = root / ".agents/plugins/harness/engineering.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["requires"]["permissions"]["claude_allow"].append("Bash(python -B fixture.py)")
            path.write_text(json.dumps(manifest), encoding="utf-8")
            catalog_path = root / ".agents/catalog/catalog.json"
            before = catalog_path.read_bytes()
            with self.assertRaisesRegex(ValueError, "Stale catalog packages"):
                updater.update(root, check=True)
            self.assertEqual(before, catalog_path.read_bytes())
            updater.update(root, check=False)
            updater.update(root, check=True)
            updater.SYNC.build(root)
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            engineering = next(item for item in catalog["packages"] if item["name"] == "engineering")
            self.assertEqual(manifest["requires"], engineering["harness"])


if __name__ == "__main__":
    unittest.main()
