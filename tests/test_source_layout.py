"""Validate the canonical-source, host-adapter, and generated-package boundary."""

import importlib.util
import json
from pathlib import Path
import posixpath
import shutil
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "package_sync", ROOT / "scripts/sync_plugin_packages.py"
)
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)


class KindMetadataTests(unittest.TestCase):
    def body(self, kind):
        return f"---\nname: custom-skill\ndescription: fixture\nkind: {kind}\ndomain: process\n---\n"

    def test_kind_accepts_open_lowercase_words(self):
        for kind in ("contract", "convention", "policy", "utility", "workflow", "knowledge", "custom"):
            with self.subTest(kind=kind):
                self.assertEqual(SYNC.metadata(self.body(kind), Path("fixture/SKILL.md"))["kind"], kind)

    def test_kind_rejects_nonword_syntax(self):
        for kind in ("convention2", "con-vention", "Convention", "", "two words", "café"):
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):
                    SYNC.metadata(self.body(kind), Path("fixture/SKILL.md"))


class SourceLayoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="agent source layout ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        for name in (".agents", ".codex", ".claude"):
            patterns = ["__pycache__", "*.pyc"]
            if name == ".agents":
                patterns.append("continuation")
            shutil.copytree(
                ROOT / name,
                self.root / name,
                ignore=shutil.ignore_patterns(*patterns),
            )

    def config(self, edit):
        path = self.root / ".agents/plugins/sources.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        edit(value)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def test_a_package_the_marketplace_publishes_elsewhere_cannot_be_authored(self):
        config = json.loads((self.root / ".agents/plugins/sources.json").read_text(encoding="utf-8"))
        config["scopes"].append({"name": "agent", "root": ".agents/agent", "layout": "kind", "plugin": "agent",
                                 "domain": "agent"})
        with self.assertRaisesRegex(ValueError, "Core may author only packages .*: agent"):
            SYNC.validate_configuration(self.root, config)

    def test_each_host_adapter_resolves_one_canonical_definition(self):
        _, output, skills, _ = SYNC.build(self.root)
        self.assertEqual(62, len(skills))
        self.assertEqual("workflow", skills["workflow:session"]["plugin"])
        self.assertNotIn("agent:background-listener", skills)
        for tree in ("skills", "codex-skills"):
            self.assertIn(f"plugins/workflow/{tree}/session/SKILL.md", output)
            self.assertNotIn(f"plugins/workflow/{tree}/background-listener/SKILL.md", output)
        self.assertEqual("session", skills["workflow:session"]["name"])
        self.assertEqual("session", skills["engineering:session"]["name"])
        for host in ("codex", "claude"):
            self.assertEqual(set(skills), {
                f"{path.parent.parent.name}:{path.parent.name}"
                for path in (self.root / f".{host}/skills").glob("*/*/SKILL.md")
            })
        for name, skill in skills.items():
            for host in ("codex", "claude"):
                adapter = (self.root / f".{host}/skills/{skill['plugin']}/{skill['name']}/SKILL.md").read_text(
                    encoding="utf-8"
                )
                self.assertEqual(
                    1,
                    adapter.count(f"](../../../../{skill['relative']})"),
                    f"{host}:{name}",
                )
        for plugin in ("workflow", "engineering"):
            self.assertIn(f"plugins/{plugin}/skills/session/SKILL.md", output)
        self.assertFalse((self.root / "base").exists())
        self.assertFalse((self.root / "engineering").exists())
        self.assertFalse((self.root / "workflow").exists())
        self.assertIn(
            "plugins/workflow/.agents/workflow/contract/plan-artifacts/SKILL.md",
            output,
        )
        self.assertIn("plugins/base/.agents/base/policy/agent-files/SKILL.md", output)
        self.assertIn("plugins/base/.agents/base/policy/task-routing/SKILL.md", output)
        self.assertIn("plugins/base/.agents/base/policy/project-setup/SKILL.md", output)
        self.assertIn("plugins/base/.agents/base/policy/solution-assessment/SKILL.md", output)

    def test_problem_record_consumers_and_shared_contract_ship_for_both_hosts(self):
        _, output, skills, _ = SYNC.build(self.root)
        canonical = {
            "address-bug": "workflow/address-bug",
            "address-mistake": "workflow/address-mistake",
        }
        resource = "plugins/engineering/.agents/workflow/resources/problem-records.md"
        workflow_resource = "plugins/workflow/.agents/workflow/resources/problem-records.md"
        self.assertIn(resource, output)
        self.assertIn(workflow_resource, output)
        for name, relative in canonical.items():
            with self.subTest(skill=name):
                self.assertEqual("engineering", skills[f"engineering:{name}"]["plugin"])
                for tree in ("skills", "codex-skills"):
                    adapter = output[f"plugins/engineering/{tree}/{name}/SKILL.md"].decode("utf-8")
                    self.assertIn(f"](../../.agents/engineering/{relative}/SKILL.md)", adapter)
                canonical_path = f"plugins/engineering/.agents/engineering/{relative}/SKILL.md"
                canonical_body = output[canonical_path].decode("utf-8")
                link = "../../../workflow/resources/problem-records.md"
                self.assertIn(f"]({link})", canonical_body)
                resolved = posixpath.normpath(f"{posixpath.dirname(canonical_path)}/{link}")
                self.assertEqual(resource, resolved)

    def test_engineering_declares_external_runtime_publishers(self):
        _, output, _, _ = SYNC.build(self.root)
        catalog = json.loads((self.root / ".agents/catalog/catalog.json").read_text(encoding="utf-8"))
        engineering = next(package for package in catalog["packages"] if package["id"] == "tj-agents/engineering")
        self.assertEqual(
            ["tj-agents/base", "tj-agents/workflow",
             "tj-agents/agent-store", "tj-agents/agent", "tj-agents/cli"],
            engineering["dependencies"]["required"],
        )
        self.assertEqual(
            ["tj-agents/agent-store", "tj-agents/agent", "tj-agents/cli"],
            [entry["id"] for entry in engineering["external_dependencies"]["required"]],
        )
        harness = json.loads(output["plugins/engineering/harness.json"].decode("utf-8"))
        self.assertEqual([{"id": "tj-agents", "repository": "tj-agents/marketplace"}], harness["requires"]["marketplaces"])
        self.assertEqual(["tj-agents/agent", "tj-agents/agent-store", "tj-agents/base", "tj-agents/cli", "tj-agents/engineering", "tj-agents/workflow"], harness["requires"]["plugins"])
        selection = json.loads(output["plugins/engineering/selection.json"].decode("utf-8"))
        self.assertEqual(engineering["external_dependencies"]["required"], selection["external_prerequisites"])

    def test_external_dependencies_are_validated_per_owner(self):
        catalog = json.loads((self.root / ".agents/catalog/catalog.json").read_text(encoding="utf-8"))
        packages = {package["id"]: package for package in catalog["packages"]}
        external = "personal-agents/personal"
        engineering = packages["tj-agents/engineering"]
        engineering["dependencies"]["required"].append(external)
        engineering["external_dependencies"]["required"].append({
            "id": external, "marketplace": "personal-agents", "repository": "tj-agents/personal"})

        borrowed = json.loads(json.dumps(catalog))
        next(package for package in borrowed["packages"] if package["id"] == "tj-agents/base")[
            "dependencies"]["required"].append(external)
        with self.assertRaisesRegex(ValueError, "tj-agents/base names unknown dependency"):
            SYNC.catalog_index(borrowed)

        for mutation in (
            lambda dependency: dependency.update(marketplace="Personal_Items", id="Personal_Items/personal"),
            lambda dependency: dependency.update(repository="not a repository"),
        ):
            invalid = json.loads(json.dumps(catalog))
            engineering = next(package for package in invalid["packages"] if package["id"] == "tj-agents/engineering")
            mutation(engineering["external_dependencies"]["required"][0])
            with self.subTest(dependency=engineering["external_dependencies"]["required"][0]):
                with self.assertRaisesRegex(ValueError, "Invalid external dependency for tj-agents/engineering"):
                    SYNC.catalog_index(invalid)

        duplicate = json.loads(json.dumps(catalog))
        engineering = next(package for package in duplicate["packages"] if package["id"] == "tj-agents/engineering")
        engineering["external_dependencies"]["required"].append(dict(engineering["external_dependencies"]["required"][0]))
        with self.assertRaisesRegex(ValueError, "Invalid external dependency for tj-agents/engineering"):
            SYNC.catalog_index(duplicate)

        conflicting = json.loads(json.dumps(catalog))
        base = next(package for package in conflicting["packages"] if package["id"] == "tj-agents/base")
        base["dependencies"]["optional"].append(external)
        base["external_dependencies"] = {"required": base.get("external_dependencies", {}).get("required", []), "optional": [
            {"id": external, "marketplace": "personal-agents", "repository": "someone/else"}]}
        with self.assertRaisesRegex(ValueError, "inconsistent ownership: personal-agents"):
            SYNC.catalog_index(conflicting)

        self.assertEqual(
            {"owner_repository": "tj-agents/personal", "source": "https://github.com/tj-agents/personal.git"},
            SYNC.catalog_marketplaces(SYNC.catalog_index(catalog))["personal-agents"],
        )
        self.assertEqual(set(packages), set(SYNC.catalog_index(catalog)))

    def test_authored_host_manifests_have_one_canonical_owner(self):
        for host in ("codex", "claude"):
            manifest_root = self.root / f".agents/plugins/manifests/{host}"
            self.assertTrue((manifest_root / "engineering.json").is_file())
            self.assertTrue((manifest_root / "workflow.json").is_file())
            self.assertTrue((manifest_root / "engineering-hooks.json").is_file())
            self.assertFalse((self.root / f".{host}/plugins").exists())

    def test_generated_payloads_are_self_contained(self):
        _, output, _, _ = SYNC.build(self.root)
        for relative in (
            "plugins/base/skills/agent-files/scripts/session-context.py",
            "plugins/base/skills/project-setup/scripts/session-context.py",
            "plugins/base/skills/solution-assessment/scripts/session-context.py",
            "plugins/base/skills/task-routing/scripts/session-context.py",
            "plugins/workflow/codex-skills/plan-artifacts/templates/PLAN.md",
            "plugins/workflow/skills/status/scripts/status.py",
            "plugins/workflow/codex-skills/status/scripts/status.py",
            "CAPABILITIES.md",
        ):
            self.assertIn(relative, output)

    def test_agent_store_runtime_is_embedded_in_each_core_consumer(self):
        _, output, _, _ = SYNC.build(self.root)
        runtime = ".agents/agent-store/runtime"
        staged = self.root / ".agents/dependencies/agent/.agents/agent-store/runtime"
        for plugin in ("workflow", "engineering"):
            for name in ("session_store.py", "repository_identity.py", "reader.py"):
                self.assertEqual(
                    SYNC.canonical_output_bytes((staged / name).read_bytes()),
                    output[f"plugins/{plugin}/{runtime}/{name}"],
                )
        isolated = self.root / "isolated package \u00e9"
        for relative, body in output.items():
            if relative.startswith("plugins/workflow/"):
                destination = isolated / relative.removeprefix("plugins/workflow/")
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(body)
        spec = importlib.util.spec_from_file_location(
            "isolated_agent_store", isolated / runtime / "session_store.py"
        )
        store = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(store)
        database = self.root / "fixture state \u00e9" / "sessions.db"
        connection = store.connect(database)
        try:
            store.upsert_work_item(
                connection, "github.com/example/repo:fixture/task", "github.com/example/repo",
                "fixture", "task", status="active", title="Fixture execution",
            )
            connection.commit()
        finally:
            connection.close()
        before = database.read_bytes()
        reader_spec = importlib.util.spec_from_file_location(
            "isolated_reader", isolated / runtime / "reader.py"
        )
        reader = importlib.util.module_from_spec(reader_spec)
        reader_spec.loader.exec_module(reader)
        payload = reader.ReadOnlyWorkItemStore(database).inspect("github.com/example/repo:fixture/task")
        self.assertEqual("Fixture execution", payload["work_items"][0]["title"])
        self.assertEqual(before, database.read_bytes())

    def test_generated_text_bytes_are_stable_across_checkout_line_endings(self):
        source = self.root / ".agents/workflow/contract/plan-artifacts/templates/PLAN.md"
        lf = source.read_bytes().replace(b"\r\n", b"\n")
        source.write_bytes(lf.replace(b"\n", b"\r\n"))

        _, output, _, _ = SYNC.build(self.root)

        generated = output["plugins/workflow/.agents/workflow/contract/plan-artifacts/templates/PLAN.md"]
        self.assertEqual(lf, generated)
        self.assertNotIn(b"\r\n", generated)

    def test_fresh_default_selection_has_handoff_closure_for_both_hosts(self):
        config, output, skills, compatibility = SYNC.build(self.root)
        marketplace = json.loads(
            output[".agents/plugins/marketplace.json"].decode("utf-8")
        )
        claude_marketplace = json.loads(
            output[".claude-plugin/marketplace.json"].decode("utf-8")
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

        self.assertEqual(["base", "workflow", "engineering"], fresh_plugins)
        self.assertEqual(fresh_plugins, default_plugins)
        self.assertEqual(
            fresh_plugins,
            [plugin["name"] for plugin in claude_marketplace["plugins"]],
        )

        catalog_skills = set()
        for plugin in fresh_plugins:
            expected_source = f"./plugins/{plugin}"
            claude_entry = next(
                entry
                for entry in claude_marketplace["plugins"]
                if entry["name"] == plugin
            )
            self.assertEqual(expected_source, claude_entry["source"])
            catalog = json.loads(
                output[f"plugins/{plugin}/selection.json"].decode("utf-8")
            )
            self.assertLessEqual(
                set(catalog["prerequisites"]), set(fresh_plugins)
            )
            catalog_skills.update(catalog["skills"])

        workflow_selection = json.loads(output["plugins/workflow/selection.json"].decode("utf-8"))
        self.assertEqual(["base"], workflow_selection["prerequisites"])
        self.assertNotIn("engineering", workflow_selection["prerequisites"])
        engineering_selection = json.loads(output["plugins/engineering/selection.json"].decode("utf-8"))
        self.assertIn("workflow", engineering_selection["prerequisites"])

        required = set(compatibility["fresh_required_skills"])
        owners = {skill["name"]: skill["plugin"] for skill in skills.values()}
        self.assertEqual({"cd", "handoff"}, required)
        self.assertLessEqual(required, catalog_skills)
        for tree in ("skills", "codex-skills"):
            for name in required:
                self.assertIn(
                    f"plugins/{owners[name]}/{tree}/{name}/SKILL.md",
                    output,
                )

    def test_fresh_selection_must_match_marketplace_policy(self):
        path = self.root / ".agents/plugins/manifests/codex/marketplace.json"
        marketplace = json.loads(path.read_text(encoding="utf-8"))
        marketplace["plugins"][-1]["policy"]["installation"] = "AVAILABLE"
        path.write_text(json.dumps(marketplace, indent=2) + "\n", encoding="utf-8")

        with self.assertRaisesRegex(
            ValueError, "fresh_selection must exactly match"
        ):
            SYNC.build(self.root)

    def test_claude_marketplace_must_match_fresh_selection(self):
        path = self.root / ".agents/plugins/manifests/claude/marketplace.json"
        marketplace = json.loads(path.read_text(encoding="utf-8"))
        marketplace["plugins"].pop()
        path.write_text(json.dumps(marketplace, indent=2) + "\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "Claude marketplace roster"):
            SYNC.build(self.root)

    def test_claude_marketplace_sources_must_resolve_selected_plugins(self):
        path = self.root / ".agents/plugins/manifests/claude/marketplace.json"
        marketplace = json.loads(path.read_text(encoding="utf-8"))
        marketplace["plugins"][-1]["source"] = "./plugins/absent"
        path.write_text(json.dumps(marketplace, indent=2) + "\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "Claude marketplace source"):
            SYNC.build(self.root)

    def test_required_handoff_skills_cannot_be_removed_or_weakened(self):
        path = self.root / ".agents/plugins/compatibility.json"
        original = json.loads(path.read_text(encoding="utf-8"))
        cases = {
            "missing": None,
            "empty": [],
            "wrong-type": "cd",
            "incomplete": ["cd"],
            "expanded": ["cd", "handoff", "handoff-codex"],
        }
        for name, required in cases.items():
            with self.subTest(name=name):
                compatibility = dict(original)
                if required is None:
                    compatibility.pop("fresh_required_skills")
                else:
                    compatibility["fresh_required_skills"] = required
                path.write_text(
                    json.dumps(compatibility, indent=2) + "\n", encoding="utf-8"
                )

                with self.assertRaisesRegex(
                    ValueError, "fresh_required_skills must exactly declare"
                ):
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
        (self.root / ".codex/skills/engineering/commit/SKILL.md").unlink()
        with self.assertRaisesRegex(ValueError, "adapter roster mismatch"):
            SYNC.build(self.root)

        shutil.copy2(
            ROOT / ".codex/skills/engineering/commit/SKILL.md",
            self.root / ".codex/skills/engineering/commit/SKILL.md",
        )
        path = self.root / ".codex/skills/engineering/commit/SKILL.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nDuplicated rule.\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "thin canonical reference"):
            SYNC.build(self.root)

    def test_a_host_only_term_in_a_shared_definition_fails_generation(self):
        shared = self.root / ".agents/engineering/utility/review/SKILL.md"
        original = shared.read_text(encoding="utf-8")
        for host, term in (
            ("claude", "`code-review`"),
            ("claude", "`/code-review`"),
            ("claude", "askuserquestion"),
            ("claude", "the Skill tool"),
            ("claude", "the `Skill` tool"),
            ("claude", "**/code-review**"),
            ("codex", "codex  review"),
        ):
            with self.subTest(host=host, term=term):
                shared.write_text(original + f"\nRun {term} here.\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, rf"{host}-only term .* belongs in \.{host}/skills/engineering/review"):
                    SYNC.build(self.root)
        shared.write_text(
            original + "\nThe `code-review-lens` path engineering/code-review/ runs in the Codex review lane"
            " as a scheduled task through the host's skill tool.\n",
            encoding="utf-8",
        )
        config = SYNC.load(self.root / ".agents/plugins/sources.json")
        SYNC.validate_host_neutral(config, SYNC.discover(self.root, config))
        shared.write_text(original, encoding="utf-8")

        reference = shared.parent / "reference.md"
        reference.write_text("Invoke `/security-review` next.\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, r"reference\.md: claude-only term"):
            SYNC.build(self.root)
        reference.unlink()
        SYNC.build(self.root)

    def test_scope_metadata_and_public_names_are_enforced(self):
        kinded = self.root / ".agents/engineering/utility/recents/SKILL.md"
        kinded.write_text(
            kinded.read_text(encoding="utf-8").replace("kind: utility", "kind: workflow"),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "kind .* does not match kind folder"):
            SYNC.build(self.root)

        kinded.write_text(
            kinded.read_text(encoding="utf-8").replace("kind: workflow", "kind: utility"),
            encoding="utf-8",
        )
        path = self.root / ".agents/engineering/utility/recents/SKILL.md"
        shutil.copytree(path.parent, self.root / ".agents/engineering/utility/recents-copy")
        with self.assertRaisesRegex(ValueError, "Duplicate public skill name: engineering:recents"):
            SYNC.build(self.root)

    def test_public_names_equal_without_hyphens_fail_generation(self):
        source = self.root / ".agents/engineering/workflow/address-debt"
        near_miss = self.root / ".agents/engineering/workflow/addressdebt"
        shutil.copytree(source, near_miss)
        skill = near_miss / "SKILL.md"
        skill.write_text(
            skill.read_text(encoding="utf-8").replace("name: address-debt", "name: addressdebt"),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "differ only by hyphens: engineering:address-debt, engineering:addressdebt"):
            SYNC.build(self.root)

    def test_resources_and_generated_roots_cannot_escape_ownership(self):
        self.config(
            lambda value: value["resources"].append(
                {
                    "plugin": "engineering",
                    "source": ".agents/hooks",
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
