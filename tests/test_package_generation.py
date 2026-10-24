import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package_generation", ROOT / "scripts/sync_plugin_packages.py")
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)


class PackageGenerationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="generated packages é ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for name in (".agents", ".codex", ".claude"):
            shutil.copytree(
                ROOT / name, self.root / name,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "continuation"),
            )

    def edit(self, relative, transform):
        path = self.root / relative
        value = json.loads(path.read_text(encoding="utf-8"))
        transform(value)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def records(self, output):
        return {package["name"]: package for package in json.loads(output["plugins/packages.json"])["packages"]}

    def test_generation_repairs_stale_records_and_is_deterministic(self):
        SYNC.generate(self.root)
        first = (self.root / "plugins/packages.json").read_bytes()
        (self.root / "plugins/packages.json").write_bytes(b"stale records")
        (self.root / "plugins/machine/packages.json").write_bytes(b"stale embedded records")
        with self.assertRaisesRegex(ValueError, "Stale generated files"):
            SYNC.generate(self.root, check=True)
        SYNC.generate(self.root)
        SYNC.generate(self.root, check=True)
        self.assertEqual(first, (self.root / "plugins/packages.json").read_bytes())
        self.assertEqual(first, (self.root / "plugins/machine/packages.json").read_bytes())

    def test_authored_metadata_and_permissions_generate_updated_records(self):
        before = SYNC.build(self.root)[1]
        before_records = self.records(before)
        self.edit(
            ".agents/plugins/harness/engineering.json",
            lambda value: value["requires"]["permissions"]["claude_allow"].append("Bash(python -B fixture.py)"),
        )
        for host in ("codex", "claude"):
            self.edit(
                f".agents/plugins/manifests/{host}/engineering.json",
                lambda value: value.update(description="Generated description"),
            )
        self.edit(
            ".agents/plugins/sources.json",
            lambda value: (
                value["platforms"].update(engineering=["windows", "linux"]),
                value["runtime_prerequisites"]["engineering"]["required"].append("exe:fixture"),
            ),
        )
        output = SYNC.build(self.root)[1]
        engineering = self.records(output)["engineering"]
        self.assertEqual("Generated description", engineering["description"])
        self.assertEqual(["windows", "linux"], engineering["platforms"])
        self.assertIn("exe:fixture", engineering["external_prerequisites"]["required"])
        self.assertIn("Bash(python -B fixture.py)", engineering["harness"]["permissions"]["claude_allow"])
        self.assertNotEqual(before_records["engineering"]["digest"], engineering["digest"])
        self.assertNotEqual(before["plugins/publication.json"], output["plugins/publication.json"])

    def test_record_metadata_changes_the_publication_without_a_digest_cycle(self):
        before = SYNC.build(self.root)[1]
        self.edit(
            ".agents/plugins/sources.json",
            lambda value: value["platforms"].update(base=["windows", "linux"]),
        )
        after = SYNC.build(self.root)[1]
        self.assertNotEqual(before["plugins/publication.json"], after["plugins/publication.json"])
        records = json.loads(after["plugins/packages.json"])
        for package in records["packages"]:
            package["digest"] = "sha256:" + "0" * 64
        after["plugins/packages.json"] = json.dumps(records).encode("utf-8")
        after["plugins/machine/packages.json"] = after["plugins/packages.json"]
        self.assertEqual(
            json.loads(after["plugins/publication.json"])["source_fingerprint"],
            SYNC.publication_fingerprint(after),
        )

    def test_discovered_skills_generate_the_roster_without_record_edits(self):
        canonical = ".agents/base/utility/fixture/SKILL.md"
        header = "---\nname: fixture\ndescription: Fixture capability.\nkind: utility\ndomain: behavior\n---\n"
        path = self.root / canonical
        path.parent.mkdir(parents=True)
        path.write_text(header + "\n# Fixture\n\nFixture body.\n", encoding="utf-8")
        for host in ("codex", "claude"):
            path = self.root / f".{host}/skills/base/fixture/SKILL.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                header + "\n# Fixture\n\n"
                + f"Read and follow the [canonical shared definition](../../../../{canonical}) in full.\n"
                + f"This entry point supplies only {host.capitalize()} discovery metadata; "
                + "the shared procedure is authored once under `.agents/`.\n",
                encoding="utf-8",
            )
        output = SYNC.build(self.root)[1]
        self.assertIn("fixture", self.records(output)["base"]["skills"])
        self.assertIn("plugins/base/skills/fixture/SKILL.md", output)
        self.assertIn("plugins/base/codex-skills/fixture/SKILL.md", output)

    def test_dependencies_generate_from_the_source_map(self):
        dependency = {"id": "docs-agents/docs", "marketplace": "docs-agents", "repository": "tj-agents/docs"}
        self.edit(
            ".agents/plugins/sources.json",
            lambda value: (
                value["prerequisites"]["base"].append("agent-store"),
                value["external_prerequisites"]["base"].append(dependency),
            ),
        )
        self.edit(
            ".agents/plugins/harness/base.json",
            lambda value: value["requires"].update(
                plugins=["docs-agents/docs", "tj-agents/agent-store", "tj-agents/base"],
                marketplaces=[
                    {"id": "docs-agents", "repository": "tj-agents/docs"},
                    {"id": "tj-agents", "repository": "tj-agents/marketplace"},
                ],
            ),
        )
        base = self.records(SYNC.build(self.root)[1])["base"]
        self.assertEqual(["tj-agents/agent-store", "docs-agents/docs"], base["dependencies"]["required"])
        self.assertEqual([dependency], base["external_dependencies"]["required"])

    def test_harness_drift_still_fails_without_generated_input(self):
        self.edit(
            ".agents/plugins/harness/base.json",
            lambda value: value["requires"].update(plugins=[]),
        )
        with self.assertRaisesRegex(ValueError, "required plugins"):
            SYNC.build(self.root)


if __name__ == "__main__":
    unittest.main()
