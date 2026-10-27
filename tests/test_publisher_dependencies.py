import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("publisher_packages", ROOT / "scripts/sync_plugin_packages.py")
PACKAGES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGES)


class PublisherDependenciesTests(unittest.TestCase):
    def roster(self):
        return json.loads((ROOT / ".agents/plugins/plugins.json").read_text(encoding="utf-8"))

    def test_shared_marketplace_accepts_external_publisher(self):
        roster = self.roster()
        package = next(item for item in roster["packages"] if item["name"] == "engineering")
        package["dependencies"]["required"].append("tj-agents/codex")
        package["external_dependencies"]["required"].append({
            "id": "tj-agents/codex", "marketplace": "tj-agents", "repository": "tj-agents/agent"})
        marketplaces = PACKAGES.roster_marketplaces(PACKAGES.roster_index(roster))
        self.assertEqual({"owner_repository": "tj-agents/marketplace",
                          "source": "https://github.com/tj-agents/marketplace.git"}, marketplaces["tj-agents"])

    def test_external_package_still_needs_its_declared_dependency(self):
        roster = self.roster()
        package = next(item for item in roster["packages"] if item["name"] == "engineering")
        package["external_dependencies"]["required"].append({
            "id": "tj-agents/codex", "marketplace": "tj-agents", "repository": "tj-agents/agent"})
        with self.assertRaisesRegex(ValueError, "Invalid external dependency"):
            PACKAGES.roster_index(roster)


if __name__ == "__main__":
    unittest.main()
