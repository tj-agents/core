"""Validate the canonical-source, host-adapter, and generated-package boundary."""

import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "package_sync", ROOT / "scripts/sync_plugin_packages.py"
)
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)


class SourceLayoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="agent source layout ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        for name in (".agents", ".codex", ".claude"):
            shutil.copytree(
                ROOT / name,
                self.root / name,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )

    def config(self, edit):
        path = self.root / ".agents/plugins/sources.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        edit(value)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def test_each_host_adapter_resolves_one_canonical_definition(self):
        _, output, skills, _ = SYNC.build(self.root)
        self.assertEqual(61, len(skills))
        self.assertEqual(set(skills), {
            path.parent.name for path in (self.root / ".codex/skills").glob("*/SKILL.md")
        })
        self.assertEqual(set(skills), {
            path.parent.name for path in (self.root / ".claude/skills").glob("*/SKILL.md")
        })
        for name, skill in skills.items():
            for host in ("codex", "claude"):
                adapter = (self.root / f".{host}/skills/{name}/SKILL.md").read_text(
                    encoding="utf-8"
                )
                self.assertEqual(
                    1,
                    adapter.count(f"](../../../{skill['relative']})"),
                    f"{host}:{name}",
                )
        self.assertFalse((self.root / "base").exists())
        self.assertFalse((self.root / "engineering").exists())
        self.assertFalse((self.root / "machine").exists())
        self.assertIn(
            "plugins/base/.agents/base/plan-artifacts/SKILL.md",
            output,
        )

    def test_authored_host_manifests_have_one_canonical_owner(self):
        for host in ("codex", "claude"):
            manifest_root = self.root / f".agents/plugins/manifests/{host}"
            self.assertTrue((manifest_root / "engineering.json").is_file())
            self.assertTrue((manifest_root / "engineering-hooks.json").is_file())
            self.assertFalse((self.root / f".{host}/plugins").exists())
            self.assertFalse((self.root / f".{host}/hooks").exists())

    def test_generated_payloads_are_self_contained(self):
        _, output, _, _ = SYNC.build(self.root)
        for relative in (
            "plugins/base/skills/plan-artifacts/scripts/session-context.py",
            "plugins/base/codex-skills/plan-artifacts/templates/PLAN.md",
            "plugins/machine/skills/handoff-codex/scripts/launch-codex.ps1",
            "plugins/machine/codex-skills/handoff-claude/scripts/launch-claude.ps1",
            "plugins/machine/resources/machine/utility/scripts/history.py",
        ):
            self.assertIn(relative, output)
        self.assertEqual(
            output["plugins/machine/skills/handoff-codex/scripts/launch-codex.ps1"],
            (self.root / ".agents/machine/utility/handoff-codex/scripts/launch-codex.ps1").read_bytes(),
        )

    def test_fresh_default_selection_has_handoff_closure_for_both_hosts(self):
        config, output, skills, compatibility = SYNC.build(self.root)
        marketplace = json.loads(
            output[".agents/plugins/marketplace.json"].decode("utf-8")
        )
        default_plugins = [
            plugin["name"]
            for plugin in marketplace["plugins"]
            if plugin["policy"]["installation"] == "INSTALLED_BY_DEFAULT"
        ]
        fresh_plugins = [
            entry.removesuffix(f"@{marketplace['name']}")
            for entry in compatibility["fresh_selection"]
        ]

        self.assertEqual(["base", "engineering", "machine"], fresh_plugins)
        self.assertEqual(fresh_plugins, default_plugins)
        for plugin in fresh_plugins:
            self.assertLessEqual(
                set(config["prerequisites"][plugin]), set(fresh_plugins)
            )

        required = set(compatibility["fresh_required_skills"])
        owners = {name: skill["plugin"] for name, skill in skills.items()}
        self.assertEqual({"cd", "handoff", "handoff-codex"}, required)
        self.assertLessEqual(required, set(owners))
        for tree in ("skills", "codex-skills"):
            for name in required:
                self.assertIn(
                    f"plugins/{owners[name]}/{tree}/{name}/SKILL.md",
                    output,
                )

    def test_cd_routes_to_automatic_handoff_before_manual_fallback(self):
        _, output, _, _ = SYNC.build(self.root)
        bodies = [
            (self.root / ".agents/base/cd/SKILL.md").read_text(encoding="utf-8"),
            output["plugins/base/.agents/base/cd/SKILL.md"].decode("utf-8"),
        ]
        for body in bodies:
            automatic = body.index("resolve and invoke the unqualified `handoff` workflow")
            manual = body.index("Only after the automatic `handoff` capability")
            self.assertLess(automatic, manual)
            self.assertIn("starts exactly one successor", body)
            self.assertIn("never make\nmanual `/cd` the normal transfer path", body)

    def test_fresh_selection_must_match_marketplace_policy(self):
        path = self.root / ".agents/plugins/manifests/codex/marketplace.json"
        marketplace = json.loads(path.read_text(encoding="utf-8"))
        marketplace["plugins"][-1]["policy"]["installation"] = "AVAILABLE"
        path.write_text(json.dumps(marketplace, indent=2) + "\n", encoding="utf-8")

        with self.assertRaisesRegex(
            ValueError, "fresh_selection must exactly match"
        ):
            SYNC.build(self.root)

    def test_fresh_selection_must_contain_its_required_skills(self):
        path = self.root / ".agents/plugins/compatibility.json"
        compatibility = json.loads(path.read_text(encoding="utf-8"))
        compatibility["fresh_required_skills"].append("missing-skill")
        path.write_text(
            json.dumps(compatibility, indent=2) + "\n", encoding="utf-8"
        )

        with self.assertRaisesRegex(ValueError, "missing required skills"):
            SYNC.build(self.root)

    def test_generation_is_deterministic_and_prunes_only_declared_output(self):
        SYNC.generate(self.root)
        SYNC.generate(self.root, check=True)
        unrelated = self.root / "user-owned.txt"
        unrelated.write_text("preserve", encoding="utf-8")
        stale = self.root / "plugins/base/obsolete.txt"
        stale.write_text("generated orphan", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "orphans: 1"):
            SYNC.generate(self.root, check=True)
        self.assertTrue(stale.exists())
        SYNC.generate(self.root)
        self.assertFalse(stale.exists())
        self.assertEqual("preserve", unrelated.read_text(encoding="utf-8"))

    def test_adapter_roster_and_body_are_enforced(self):
        (self.root / ".codex/skills/commit/SKILL.md").unlink()
        with self.assertRaisesRegex(ValueError, "adapter roster mismatch"):
            SYNC.build(self.root)

        shutil.copy2(
            ROOT / ".codex/skills/commit/SKILL.md",
            self.root / ".codex/skills/commit/SKILL.md",
        )
        path = self.root / ".codex/skills/commit/SKILL.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nDuplicated rule.\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "thin canonical reference"):
            SYNC.build(self.root)

    def test_scope_metadata_and_public_names_are_enforced(self):
        path = self.root / ".agents/machine/utility/clip/SKILL.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("kind: utility", "kind: workflow"),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "kind .* does not match kind folder"):
            SYNC.build(self.root)

        path.write_text(
            path.read_text(encoding="utf-8").replace("kind: workflow", "kind: utility"),
            encoding="utf-8",
        )
        duplicate = self.root / ".agents/engineering/utility/clip"
        shutil.copytree(path.parent, duplicate)
        duplicate_skill = duplicate / "SKILL.md"
        duplicate_skill.write_text(
            duplicate_skill.read_text(encoding="utf-8").replace(
                "domain: machine", "domain: process"
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "Duplicate public skill name"):
            SYNC.build(self.root)

    def test_resources_and_generated_roots_cannot_escape_ownership(self):
        self.config(
            lambda value: value["resources"].append(
                {
                    "plugin": "machine",
                    "source": ".agents/machine/utility/scripts",
                    "destination": "../base/escaped",
                }
            )
        )
        with self.assertRaisesRegex(ValueError, "Invalid resource destination"):
            SYNC.build(self.root)

        self.config(
            lambda value: value.update(
                resources=value["resources"][:-1],
                generated_roots=value["generated_roots"] + [".agents/engineering"],
            )
        )
        with self.assertRaisesRegex(ValueError, "overlaps authored source"):
            SYNC.build(self.root)

    def test_prerequisite_cycles_and_missing_owners_fail(self):
        self.config(lambda value: value["prerequisites"]["base"].append("engineering"))
        with self.assertRaisesRegex(ValueError, "Prerequisite cycle"):
            SYNC.build(self.root)

        self.config(lambda value: value["prerequisites"].update(base=["absent"]))
        with self.assertRaisesRegex(ValueError, "Unknown prerequisite"):
            SYNC.build(self.root)


if __name__ == "__main__":
    unittest.main()
