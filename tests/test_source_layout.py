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

    def test_kind_accepts_only_current_responsibilities(self):
        for kind in (
            "policy", "standard", "operation", "workflow", "learning", "reference"
        ):
            with self.subTest(kind=kind):
                self.assertEqual(SYNC.metadata(self.body(kind), Path("fixture/SKILL.md"))["kind"], kind)

    def test_kind_rejects_retired_custom_and_invalid_values(self):
        for kind in (
            "contract", "convention", "utility", "knowledge", "custom",
            "Convention", "", "two words", "café"
        ):
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):
                    SYNC.metadata(self.body(kind), Path("fixture/SKILL.md"))


class SubjectDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="subject source é ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.config = {
            "scopes": [
                {
                    "name": "base",
                    "plugin": "base",
                    "root": ".agents/base/skills",
                    "layout": "subject",
                    "domain": "behavior",
                }
            ]
        }
        (self.root / ".agents/base/skills").mkdir(parents=True)

    def skill(self, subject, name, kind="operation"):
        path = self.root / ".agents/base/skills" / subject / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"---\nname: {name}\ndescription: fixture\nkind: {kind}\n"
            "domain: behavior\n---\n# Fixture\n",
            encoding="utf-8",
        )
        return path

    def test_recursive_subjects_flatten_into_public_names(self):
        path = self.skill("state/client", "state-client")
        shared = SYNC.discover(self.root, self.config)["base:state-client"]
        self.assertEqual(path, shared["path"])
        self.assertEqual(
            ".agents/base/skills/state/client/SKILL.md", shared["relative"]
        )

    def test_path_and_metadata_names_must_agree(self):
        self.skill("state/client", "client")
        with self.assertRaisesRegex(
            ValueError, "does not match subject path state-client"
        ):
            SYNC.discover(self.root, self.config)

    def test_flattened_subject_collision_fails(self):
        self.skill("state/client", "state-client")
        self.skill("state-client", "state-client")
        with self.assertRaisesRegex(
            ValueError, "Duplicate public skill name: base:state-client"
        ):
            SYNC.discover(self.root, self.config)

    def test_invalid_subject_segments_fail(self):
        self.skill("Bad/client", "bad-client")
        with self.assertRaisesRegex(ValueError, "invalid subject path"):
            SYNC.discover(self.root, self.config)

    def test_retired_layouts_and_parallel_old_trees_fail(self):
        self.skill("example", "example")
        for layout in ("flat", "kind"):
            with self.subTest(layout=layout):
                self.config["scopes"][0]["layout"] = layout
                with self.assertRaisesRegex(ValueError, "Unsupported source layout"):
                    SYNC.discover(self.root, self.config)
        self.config["scopes"][0]["layout"] = "subject"
        old = self.root / ".agents/base/utility/old/SKILL.md"
        old.parent.mkdir(parents=True)
        old.write_text("old", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "outside subject layout"):
            SYNC.discover(self.root, self.config)

    def test_native_metadata_does_not_read_unrelated_nested_fields(self):
        body = (
            "---\nname: fixture\ndescription: fixture\nmetadata:\n"
            "    tj-agents-kind: standard\n    tj-agents-domain: behavior\n"
            "    example:\n      model: unrelated\n      kind: utility\n---\n"
        )
        values = SYNC.metadata(body, Path("fixture/SKILL.md"))
        self.assertEqual("standard", values["kind"])
        self.assertNotIn("model", values)
        for required in ("name", "description"):
            with self.subTest(required=required):
                projected = body.replace(f"{required}: fixture\n", "").replace(
                    "metadata:\n", f"metadata:\n    tj-agents-{required}: fixture\n"
                )
                with self.assertRaisesRegex(ValueError, f"missing {required}"):
                    SYNC.metadata(projected, Path("fixture/SKILL.md"))
        for declaration in ("kind: standard\n", "kind: operation\n"):
            with (
                self.subTest(declaration=declaration),
                self.assertRaisesRegex(
                    ValueError, "ambiguous frontmatter field kind"
                ),
            ):
                SYNC.metadata(
                    body.replace("metadata:\n", declaration + "metadata:\n"),
                    Path("fixture/SKILL.md"),
                )

    def test_native_projection_preserves_host_fields_and_existing_metadata_indent(self):
        body = (
            "---\nname: fixture\ndescription : fixture\nkind: standard\n"
            "domain: behavior\nmodel: sonnet\nallowed-tools: Read\n"
            "context: fork\nmetadata:\n    example:\n"
            "      model: unrelated\n---\nBody\n"
        )
        claude = SYNC.native_payload(body, Path("fixture/SKILL.md"), "claude")
        codex = SYNC.native_payload(body, Path("fixture/SKILL.md"), "codex")
        self.assertIn("\nmodel: sonnet\n", claude)
        self.assertIn("\ncontext: fork\n", claude)
        self.assertNotIn("\nmodel: sonnet\n", codex)
        self.assertIn("\n    tj-agents-model: sonnet\n", codex)
        for rendered in (claude, codex):
            self.assertIn("\ndescription: fixture\n", rendered)
            self.assertIn("\nallowed-tools: Read\n", rendered)
            self.assertIn("\n    tj-agents-kind: standard\n", rendered)
            values = SYNC.metadata(rendered, Path("fixture/SKILL.md"))
            self.assertEqual("sonnet", values["model"])
            self.assertEqual("standard", values["kind"])


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
        roster_path = self.root / ".agents/plugins/plugins.json"
        roster = json.loads(roster_path.read_text(encoding="utf-8"))
        roster["packages"].append({"name": "agent", "owner_repository": "tj-agents/core"})
        roster_path.write_text(json.dumps(roster), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Core may author only packages .*: agent"):
            SYNC.validate_configuration(self.root, config)

    def test_an_unpublished_package_requires_a_local_core_owner(self) -> None:
        snapshot_path = self.root / SYNC.MARKETPLACE_SNAPSHOT
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        snapshot["marketplace"]["plugins"] = [
            entry for entry in snapshot["marketplace"]["plugins"] if entry["name"] != "docs"
        ]
        snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
        config = json.loads((self.root / ".agents/plugins/sources.json").read_text(encoding="utf-8"))
        self.assertIn("docs", SYNC.validate_configuration(self.root, config))
        roster_path = self.root / ".agents/plugins/plugins.json"
        roster = json.loads(roster_path.read_text(encoding="utf-8"))
        for package in roster["packages"]:
            if package["name"] == "docs":
                package["owner_repository"] = "tj-agents/other"
        roster_path.write_text(json.dumps(roster), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Core may author only packages .*: docs"):
            SYNC.validate_configuration(self.root, config)

    def test_each_host_adapter_resolves_one_canonical_definition(self):
        _, output, skills, _ = SYNC.build(self.root)
        self.assertEqual(57, len(skills))
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
            "plugins/workflow/.agents/workflow/skills/plan-artifacts/SKILL.md",
            output,
        )
        self.assertIn("plugins/base/.agents/base/skills/agent-files/SKILL.md", output)
        self.assertIn("plugins/base/.agents/base/skills/task-routing/SKILL.md", output)
        self.assertIn("plugins/base/.agents/base/skills/project-setup/SKILL.md", output)
        self.assertIn(
            "plugins/base/.agents/base/skills/solution-assessment/SKILL.md", output
        )

    def test_problem_record_consumers_and_shared_contract_ship_for_both_hosts(self):
        _, output, skills, _ = SYNC.build(self.root)
        canonical = {
            "address-bug": "skills/address-bug",
            "address-mistake": "skills/address-mistake",
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
        roster = json.loads((self.root / ".agents/plugins/plugins.json").read_text(encoding="utf-8"))
        engineering = next(package for package in roster["packages"] if package["id"] == "tj-agents/engineering")
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
        roster = json.loads((self.root / ".agents/plugins/plugins.json").read_text(encoding="utf-8"))
        packages = {package["id"]: package for package in roster["packages"]}
        external = "personal-agents/personal"
        engineering = packages["tj-agents/engineering"]
        engineering["dependencies"]["required"].append(external)
        engineering["external_dependencies"]["required"].append({
            "id": external, "marketplace": "personal-agents", "repository": "tj-agents/personal"})

        borrowed = json.loads(json.dumps(roster))
        next(package for package in borrowed["packages"] if package["id"] == "tj-agents/base")[
            "dependencies"]["required"].append(external)
        with self.assertRaisesRegex(ValueError, "tj-agents/base names unknown dependency"):
            SYNC.roster_index(borrowed)

        for mutation in (
            lambda dependency: dependency.update(marketplace="Personal_Items", id="Personal_Items/personal"),
            lambda dependency: dependency.update(repository="not a repository"),
        ):
            invalid = json.loads(json.dumps(roster))
            engineering = next(package for package in invalid["packages"] if package["id"] == "tj-agents/engineering")
            mutation(engineering["external_dependencies"]["required"][0])
            with self.subTest(dependency=engineering["external_dependencies"]["required"][0]):
                with self.assertRaisesRegex(ValueError, "Invalid external dependency for tj-agents/engineering"):
                    SYNC.roster_index(invalid)

        duplicate = json.loads(json.dumps(roster))
        engineering = next(package for package in duplicate["packages"] if package["id"] == "tj-agents/engineering")
        engineering["external_dependencies"]["required"].append(dict(engineering["external_dependencies"]["required"][0]))
        with self.assertRaisesRegex(ValueError, "Invalid external dependency for tj-agents/engineering"):
            SYNC.roster_index(duplicate)

        conflicting = json.loads(json.dumps(roster))
        base = next(package for package in conflicting["packages"] if package["id"] == "tj-agents/base")
        base["dependencies"]["optional"].append(external)
        base["external_dependencies"] = {"required": base.get("external_dependencies", {}).get("required", []), "optional": [
            {"id": external, "marketplace": "personal-agents", "repository": "someone/else"}]}
        with self.assertRaisesRegex(ValueError, "inconsistent ownership: personal-agents"):
            SYNC.roster_index(conflicting)

        self.assertEqual(
            {"owner_repository": "tj-agents/personal", "source": "https://github.com/tj-agents/personal.git"},
            SYNC.roster_marketplaces(SYNC.roster_index(roster))["personal-agents"],
        )
        self.assertEqual(set(packages), set(SYNC.roster_index(roster)))

    def test_authored_host_manifests_have_one_canonical_owner(self):
        for host in ("codex", "claude"):
            manifest_root = self.root / f".agents/plugins/manifests/{host}"
            self.assertTrue((manifest_root / "engineering.json").is_file())
            self.assertTrue((manifest_root / "workflow.json").is_file())
            self.assertTrue((manifest_root / "base-hooks.json").is_file())
            self.assertFalse((manifest_root / "engineering-hooks.json").exists())
            self.assertFalse((manifest_root / "workflow-hooks.json").exists())
            self.assertFalse((self.root / f".{host}/plugins").exists())

    def test_generated_payloads_are_self_contained(self):
        _, output, _, _ = SYNC.build(self.root)
        for relative in (
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

    def test_nested_subjects_ship_their_own_siblings_once(self):
        roster_path = self.root / ".agents/plugins/plugins.json"
        roster = json.loads(roster_path.read_text(encoding="utf-8"))
        engineering = next(
            package
            for package in roster["packages"]
            if package["id"] == "tj-agents/engineering"
        )
        engineering["skills"] = sorted([*engineering["skills"], "recents-child"])
        roster_path.write_text(json.dumps(roster, indent=2) + "\n", encoding="utf-8")
        child = self.root / ".agents/engineering/skills/recents/child/SKILL.md"
        child.parent.mkdir()
        header = (
            "---\nname: recents-child\ndescription: fixture\n"
            "kind: reference\ndomain: process\n---\n"
        )
        child.write_text(header + "# Child\n", encoding="utf-8")
        sibling = child.parent / "reference.txt"
        sibling.write_text("child resource", encoding="utf-8")
        shared = {
            "body": child.read_text(encoding="utf-8"),
            "metadata": {"name": "recents-child"},
            "relative": child.relative_to(self.root).as_posix(),
        }
        for host in ("codex", "claude"):
            adapter = self.root / f".{host}/skills/engineering/recents-child/SKILL.md"
            adapter.parent.mkdir()
            adapter.write_text(
                header + SYNC.expected_adapter_body(shared, host), encoding="utf-8"
            )

        _, output, _, _ = SYNC.build(self.root, validate_plugin_digests=False)

        self.assertEqual(
            b"child resource",
            output[
                "plugins/engineering/.agents/engineering/skills/recents/child/reference.txt"
            ],
        )
        for tree in ("skills", "codex-skills"):
            self.assertEqual(
                b"child resource",
                output[f"plugins/engineering/{tree}/recents-child/reference.txt"],
            )
            self.assertNotIn(
                f"plugins/engineering/{tree}/recents/child/SKILL.md", output
            )
            self.assertNotIn(
                f"plugins/engineering/{tree}/recents/child/reference.txt", output
            )

    def test_generated_text_bytes_are_stable_across_checkout_line_endings(self):
        source = self.root / ".agents/workflow/skills/plan-artifacts/templates/PLAN.md"
        lf = source.read_bytes().replace(b"\r\n", b"\n")
        source.write_bytes(lf.replace(b"\n", b"\r\n"))

        _, output, _, _ = SYNC.build(self.root)

        generated = output[
            "plugins/workflow/.agents/workflow/skills/plan-artifacts/templates/PLAN.md"
        ]
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

        self.assertEqual(["base", "workflow", "engineering", "docs"], fresh_plugins)
        self.assertEqual(fresh_plugins, default_plugins)
        self.assertEqual(
            fresh_plugins,
            [plugin["name"] for plugin in claude_marketplace["plugins"]],
        )

        selection_skills = set()
        for plugin in fresh_plugins:
            expected_source = f"./plugins/{plugin}"
            claude_entry = next(
                entry
                for entry in claude_marketplace["plugins"]
                if entry["name"] == plugin
            )
            self.assertEqual(expected_source, claude_entry["source"])
            selection = json.loads(
                output[f"plugins/{plugin}/selection.json"].decode("utf-8")
            )
            self.assertLessEqual(
                set(selection["prerequisites"]), set(fresh_plugins)
            )
            selection_skills.update(selection["skills"])

        workflow_selection = json.loads(output["plugins/workflow/selection.json"].decode("utf-8"))
        self.assertEqual(["base"], workflow_selection["prerequisites"])
        self.assertNotIn("engineering", workflow_selection["prerequisites"])
        engineering_selection = json.loads(output["plugins/engineering/selection.json"].decode("utf-8"))
        self.assertIn("workflow", engineering_selection["prerequisites"])

        required = set(compatibility["fresh_required_skills"])
        owners = {skill["name"]: skill["plugin"] for skill in skills.values()}
        self.assertEqual({"cd", "handoff"}, required)
        self.assertLessEqual(required, selection_skills)
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
        shared = self.root / ".agents/engineering/skills/review/SKILL.md"
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

    def test_changing_kind_preserves_subject_path_and_public_identity(self):
        path = self.root / ".agents/engineering/skills/recents/SKILL.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "kind: operation", "kind: workflow"
            ),
            encoding="utf-8",
        )
        config = SYNC.load(self.root / ".agents/plugins/sources.json")
        discovered = SYNC.discover(self.root, config)
        self.assertEqual(
            "workflow", discovered["engineering:recents"]["metadata"]["kind"]
        )
        self.assertEqual(path, discovered["engineering:recents"]["path"])

    def test_duplicate_public_names_fail_generation(self):
        path = self.root / ".agents/engineering/skills/recents/SKILL.md"
        shutil.copytree(path.parent, path.parent.with_name("recents-copy"))
        with self.assertRaisesRegex(
            ValueError, "Duplicate public skill name: engineering:recents"
        ):
            SYNC.build(self.root)

    def test_public_names_equal_without_hyphens_fail_generation(self):
        source = self.root / ".agents/engineering/skills/address-debt"
        near_miss = self.root / ".agents/engineering/skills/addressdebt"
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
