"""The stack-tier gate decides applicability from shipped declarations, never from local settings."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import unittest.mock


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / ".agents" / "hooks" / "tier_gate.py"
SCHEMA = ROOT / ".agents" / "schemas" / "tier.schema.json"
DECLARED = ROOT / ".agents" / "tiers"


def load_module():
    specification = importlib.util.spec_from_file_location("tier_gate", SCRIPT)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


gate = load_module()


DOTNET = {
    "schema_version": 1,
    "tier": "dotnet",
    "stack": ".NET",
    "applies": "stack-present",
    "owner_repository": "tomjseery/dotagents",
    "detect": {"globs": ["*.sln", "*.csproj"], "files": ["global.json"]},
}
REACT = {
    "schema_version": 1,
    "tier": "react",
    "stack": "TypeScript/React",
    "applies": "stack-present",
    "owner_repository": "tomjseery/react-agents",
    "detect": {"content": [{"glob": "package.json", "pattern": r"\"react\"\s*:"}]},
}
BASE = {"schema_version": 1, "tier": "base", "stack": "any project", "applies": "always"}
INFONETICA = {
    "schema_version": 2,
    "tier": "infonetica",
    "stack": "Infonetica work",
    "applies": "stack-present",
    "detect": {"remote": [r"^infonetica/"]},
}


def declaration(plugin, marketplace, data):
    return gate.Declaration(plugin, marketplace, data)


class DeclarationDiscovery(unittest.TestCase):
    def test_identity_comes_from_the_installed_path_not_the_declaration(self):
        with tempfile.TemporaryDirectory() as cache:
            payload = Path(cache) / "dotagents" / "dotnet" / "1.1.0"
            payload.mkdir(parents=True)
            claim = dict(DOTNET, tier="dotnet")
            (payload / "tier.json").write_text(json.dumps(claim), encoding="utf-8")

            found = gate.declarations([cache])

        self.assertEqual([item.id for item in found], ["dotnet@dotagents"])
        self.assertEqual(found[0].plugin, "dotnet")
        self.assertEqual(found[0].marketplace, "dotagents")

    def test_an_unreadable_or_unversioned_declaration_is_ignored(self):
        with tempfile.TemporaryDirectory() as cache:
            for name, body in (
                ("broken", "{not json"),
                ("future", json.dumps({"schema_version": 99, "tier": "x", "applies": "always"})),
                ("nameless", json.dumps({"schema_version": 1, "applies": "always"})),
            ):
                payload = Path(cache) / name / name / "1.0.0"
                payload.mkdir(parents=True)
                (payload / "tier.json").write_text(body, encoding="utf-8")

            self.assertEqual(gate.declarations([cache]), [])

    def test_schema_version_two_is_accepted(self):
        with tempfile.TemporaryDirectory() as cache:
            payload = Path(cache) / "infonetica" / "infonetica" / "1.0.0"
            payload.mkdir(parents=True)
            (payload / "tier.json").write_text(json.dumps(INFONETICA), encoding="utf-8")

            found = gate.declarations([cache])

        self.assertEqual([item.tier for item in found], ["infonetica"])

    def test_an_orphaned_version_never_shadows_a_live_one(self):
        with tempfile.TemporaryDirectory() as cache:
            live = Path(cache) / "dotagents" / "dotnet" / "aaa-old"
            orphaned = Path(cache) / "dotagents" / "dotnet" / "zzz-new"
            for payload in (live, orphaned):
                payload.mkdir(parents=True)
                (payload / "tier.json").write_text(json.dumps(DOTNET), encoding="utf-8")
            (orphaned / ".orphaned_at").write_text("", encoding="utf-8")

            found = gate.declarations([cache])

        self.assertEqual([item.payload_dir for item in found], [live])

    def test_the_registry_installed_version_beats_every_other_cached_version(self):
        with tempfile.TemporaryDirectory() as config:
            cache = Path(config) / "plugins" / "cache"
            installed = cache / "dotagents" / "dotnet" / "aaa-installed"
            for name in ("aaa-installed", "zzz-stale"):
                payload = cache / "dotagents" / "dotnet" / name
                payload.mkdir(parents=True)
                (payload / "tier.json").write_text(json.dumps(DOTNET), encoding="utf-8")
            os.utime(installed, (1, 1))
            registry = {"plugins": {"dotnet@dotagents": [{"installPath": str(installed)}]}}
            (cache.parent / "installed_plugins.json").write_text(json.dumps(registry), encoding="utf-8")

            found = gate.declarations([cache])

        self.assertEqual([item.payload_dir for item in found], [installed])

    def test_a_project_scoped_install_answers_only_inside_its_project(self):
        with tempfile.TemporaryDirectory() as config:
            cache = Path(config) / "plugins" / "cache"
            user = cache / "dotagents" / "dotnet" / "user-version"
            scoped = cache / "dotagents" / "dotnet" / "project-version"
            for payload in (user, scoped):
                payload.mkdir(parents=True)
                (payload / "tier.json").write_text(json.dumps(DOTNET), encoding="utf-8")
            project = Path(config) / "project-x"
            (project / "src").mkdir(parents=True)
            registry = {"plugins": {"dotnet@dotagents": [
                {"scope": "user", "installPath": str(user)},
                {"scope": "project", "projectPath": str(project), "installPath": str(scoped)},
            ]}}
            (cache.parent / "installed_plugins.json").write_text(json.dumps(registry), encoding="utf-8")
            os.utime(scoped, (1, 1))

            inside = gate.declarations([cache], project=project / "src")
            elsewhere = gate.declarations([cache], project=Path(config) / "project-y")

        self.assertEqual([item.payload_dir.name for item in inside], ["project-version"])
        self.assertEqual([item.payload_dir.name for item in elsewhere], ["user-version"])

    def test_a_project_install_without_a_declaration_leaves_the_user_install_answering(self):
        with tempfile.TemporaryDirectory() as config:
            cache = Path(config) / "plugins" / "cache"
            user = cache / "dotagents" / "dotnet" / "user-version"
            user.mkdir(parents=True)
            (user / "tier.json").write_text(json.dumps(DOTNET), encoding="utf-8")
            legacy = cache / "dotagents" / "dotnet" / "pre-tier"
            legacy.mkdir(parents=True)
            project = Path(config) / "project"
            project.mkdir()
            registry = {"plugins": {"dotnet@dotagents": [
                {"scope": "user", "installPath": str(user)},
                {"scope": "project", "projectPath": str(project), "installPath": str(legacy)},
            ]}}
            (cache.parent / "installed_plugins.json").write_text(json.dumps(registry), encoding="utf-8")

            found = gate.declarations([cache], project=project)

        self.assertEqual([item.payload_dir.name for item in found], ["user-version"])

    def test_the_most_specific_project_install_wins(self):
        with tempfile.TemporaryDirectory() as config:
            cache = Path(config) / "plugins" / "cache"
            outer, inner = cache / "dotagents" / "dotnet" / "outer", cache / "dotagents" / "dotnet" / "inner"
            for payload in (outer, inner):
                payload.mkdir(parents=True)
                (payload / "tier.json").write_text(json.dumps(DOTNET), encoding="utf-8")
            os.utime(inner, (1, 1))
            repos = Path(config) / "repos"
            (repos / "app" / "src").mkdir(parents=True)
            registry = {"plugins": {"dotnet@dotagents": [
                {"scope": "project", "projectPath": str(repos), "installPath": str(outer)},
                {"scope": "project", "projectPath": str(repos / "app"), "installPath": str(inner)},
            ]}}
            (cache.parent / "installed_plugins.json").write_text(json.dumps(registry), encoding="utf-8")

            found = gate.declarations([cache], project=repos / "app" / "src")

        self.assertEqual([item.payload_dir.name for item in found], ["inner"])

    def test_the_gates_own_install_cache_precedes_the_home_caches(self):
        with tempfile.TemporaryDirectory() as home:
            own = Path(home) / ".codex" / "plugins" / "cache"
            script = own / "base-agents" / "engineering" / "1.0.0" / "hooks" / "tier_gate.py"
            script.parent.mkdir(parents=True)
            (Path(home) / ".claude" / "plugins" / "cache").mkdir(parents=True)
            cleared = {name: "" for name in (*gate.PLUGIN_ROOT_VARIABLES, "CLAUDE_CONFIG_DIR", "CODEX_HOME")}
            with unittest.mock.patch.dict(os.environ, cleared), \
                    unittest.mock.patch.object(gate, "__file__", str(script)), \
                    unittest.mock.patch.object(gate.Path, "home", return_value=Path(home)):
                roots = gate.cache_roots()

        self.assertEqual(own.resolve(), roots[0])

    def test_the_first_cache_root_answers_for_a_plugin_both_hosts_cache(self):
        with tempfile.TemporaryDirectory() as claude, tempfile.TemporaryDirectory() as codex:
            payloads = []
            for cache, name in ((claude, "b693fe48ccd8"), (codex, "1.1.2")):
                payload = Path(cache) / "dotagents" / "dotnet" / name
                payload.mkdir(parents=True)
                (payload / "tier.json").write_text(json.dumps(DOTNET), encoding="utf-8")
                payloads.append(payload)

            found = gate.declarations([claude, codex])

        self.assertEqual([item.payload_dir for item in found], [payloads[0]])


class TemporaryProject(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.project = Path(directory.name)
        patched = unittest.mock.patch.dict(os.environ, {gate.OVERRIDE_VARIABLE: ""})
        patched.start()
        self.addCleanup(patched.stop)


class Detection(TemporaryProject):
    def populated(self, stack, names):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        directory = Path(holder.name)
        for name in names:
            path = directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(stack, encoding="utf-8")
        return directory

    def test_a_marker_at_any_depth_proves_the_stack(self):
        project = self.populated("", ["src/api/Service.csproj"])
        present, evidence = gate.stack_present(project, DOTNET["detect"])
        self.assertTrue(present)
        self.assertIn("Service.csproj", evidence)

    def test_an_unrelated_project_does_not_match(self):
        project = self.populated("", ["README.md", "app/main.py"])
        present, _ = gate.stack_present(project, DOTNET["detect"])
        self.assertFalse(present)

    def test_content_matching_reads_the_file_not_its_name(self):
        project = self.populated(json.dumps({"dependencies": {"react": "18.3.1"}}), ["package.json"])
        present, evidence = gate.stack_present(project, REACT["detect"])
        self.assertTrue(present)
        self.assertEqual(evidence, "package.json")

        other = self.populated(json.dumps({"dependencies": {"vue": "3"}}), ["package.json"])
        present, _ = gate.stack_present(other, REACT["detect"])
        self.assertFalse(present)

    def test_a_remote_matcher_reads_the_origin_identity_not_the_tree(self):
        project = self.populated("", ["README.md"])
        subprocess.run(["git", "init", "-q"], cwd=project, check=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/Infonetica/cris-preaward-app.git"],
            cwd=project,
            check=True,
        )
        present, evidence = gate.stack_present(project, INFONETICA["detect"])
        self.assertTrue(present)
        self.assertEqual(evidence, "origin infonetica/cris-preaward-app")

        unrelated = self.populated("", ["README.md"])
        subprocess.run(["git", "init", "-q"], cwd=unrelated, check=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/tj-agents/core.git"],
            cwd=unrelated,
            check=True,
        )
        present, _ = gate.stack_present(unrelated, INFONETICA["detect"])
        self.assertFalse(present)


class Applicability(TemporaryProject):
    def setUp(self):
        super().setUp()
        self.found = [
            declaration("base", "base-agents", BASE),
            declaration("dotnet", "dotagents", DOTNET),
        ]

    def test_a_ubiquitous_package_is_never_gated(self):
        ubiquitous, _, blocked = gate.assess(self.project, self.found)
        self.assertEqual([item.tier for item in ubiquitous], ["base"])
        self.assertNotIn("base", [item.tier for item in blocked])

    def test_a_stack_tier_without_its_stack_is_blocked(self):
        _, applicable, blocked = gate.assess(self.project, self.found)
        self.assertEqual(applicable, [])
        self.assertEqual([item.tier for item in blocked], ["dotnet"])

    def test_a_stack_tier_with_its_stack_applies(self):
        (self.project / "Solution.sln").write_text("", encoding="utf-8")
        _, applicable, blocked = gate.assess(self.project, self.found)
        self.assertEqual([item.tier for item, _ in applicable], ["dotnet"])
        self.assertEqual(blocked, [])

    def test_the_override_forces_one_session_without_configuring_the_project(self):
        with unittest.mock.patch.dict(os.environ, {gate.OVERRIDE_VARIABLE: "dotnet"}):
            _, applicable, blocked = gate.assess(self.project, self.found)
        self.assertEqual([item.tier for item, _ in applicable], ["dotnet"])
        self.assertEqual(blocked, [])

    def test_a_tier_is_readable_inside_its_own_authoring_repository(self):
        subprocess.run(["git", "init", "-q"], cwd=self.project, check=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/tomjseery/dotagents.git"],
            cwd=self.project,
            check=True,
        )
        _, applicable, blocked = gate.assess(self.project, self.found)
        self.assertEqual([item.tier for item, _ in applicable], ["dotnet"])
        self.assertEqual(blocked, [])


class SessionStatement(TemporaryProject):
    def test_nothing_is_said_when_no_stack_tier_is_installed(self):
        found = [declaration("base", "base-agents", BASE)]
        self.assertEqual(gate.statement(self.project, found), "")

    def test_the_statement_names_what_applies_and_what_does_not(self):
        found = [
            declaration("base", "base-agents", BASE),
            declaration("dotnet", "dotagents", DOTNET),
            declaration("react", "react-agents", REACT),
        ]
        (self.project / "Api.csproj").write_text("", encoding="utf-8")
        text = gate.statement(self.project, found)

        self.assertIn("Ubiquitous, always applies: base", text)
        self.assertIn("Applies here: `dotnet:*`", text)
        self.assertIn("Does not apply here: `react:*`", text)
        self.assertNotIn("Does not apply here: `dotnet", text)

    def test_an_audit_can_inspect_source_without_adopting_inapplicable_rules(self):
        found = [declaration("dotnet", "dotagents", DOTNET)]
        text = gate.statement(self.project, found)
        self.assertIn("standards-source audit", text)
        self.assertIn("canonical source files", text)
        self.assertIn("does not load them as governing instructions", text)
        self.assertNotIn("do not read, invoke or cite", text)
        self.assertIn("no stack tier applies", gate.conventions(self.project, found))


class Conventions(TemporaryProject):
    def installed(self, skills):
        cache = tempfile.TemporaryDirectory()
        self.addCleanup(cache.cleanup)
        payload = Path(cache.name) / "dotagents" / "dotnet" / "1.0.0"
        for name, kind in skills:
            skill = payload / "skills" / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: rule\nkind: {kind}\n---\n\n# {name}\n",
                encoding="utf-8",
            )
        (payload / "tier.json").write_text(json.dumps(DOTNET), encoding="utf-8")
        return gate.declarations([cache.name])

    def test_legacy_new_and_mixed_payloads_discover_the_same_conventions(self):
        (self.project / "Api.csproj").write_text("", encoding="utf-8")
        excluded = [(kind, kind) for kind in ("operation", "policy", "utility", "workflow", "knowledge", "custom")]
        for kinds in (("contract", "contract"), ("convention", "convention"), ("contract", "convention")):
            with self.subTest(kinds=kinds):
                found = self.installed(list(zip(("persistence", "style"), kinds)) + excluded)
                payload = found[0].payload_dir
                self.assertEqual([name for name, _ in gate.contract_skills(payload)], ["persistence", "style"])
                text = gate.conventions(self.project, found)
                self.assertIn("dotnet (.NET detected (Api.csproj)): 2 convention(s)", text)
                self.assertIn("persistence", text)
                self.assertIn("style", text)
                for name, _ in excluded:
                    self.assertNotIn("  " + name + " -", text)

    def test_no_applicable_tier_is_said_explicitly(self):
        for kind in ("contract", "convention"):
            with self.subTest(kind=kind):
                found = self.installed([("persistence", kind)])
                text = gate.conventions(self.project, found)
                self.assertIn("no stack tier applies", text)
                self.assertNotIn("persistence", text)


class Gate(TemporaryProject):
    def setUp(self):
        super().setUp()
        self.found = [
            declaration("base", "base-agents", BASE),
            declaration("dotnet", "dotagents", DOTNET),
        ]

    def call(self, payload):
        return gate.gate(dict(payload, cwd=str(self.project)), self.found)

    def test_a_blocked_tier_skill_is_refused(self):
        payload = {"tool_name": "Skill", "tool_input": {"skill": "dotnet:persistence"}}
        self.assertEqual(self.call(payload), 2)

    def test_a_ubiquitous_skill_is_allowed(self):
        payload = {"tool_name": "Skill", "tool_input": {"skill": "engineering:review"}}
        self.assertEqual(self.call(payload), 0)

    def test_the_same_skill_is_allowed_where_the_stack_exists(self):
        (self.project / "Api.csproj").write_text("", encoding="utf-8")
        payload = {"tool_name": "Skill", "tool_input": {"skill": "dotnet:persistence"}}
        self.assertEqual(self.call(payload), 0)

    def test_a_codex_shell_read_of_the_standard_is_the_same_event(self):
        command = 'cat ~/.codex/plugins/cache/dotagents/dotnet/1.1.0/skills/persistence/SKILL.md'
        payload = {"tool_name": "shell", "tool_input": {"command": command}}
        self.assertEqual(self.call(payload), 2)

    def test_naming_the_plugin_without_reading_a_standard_is_not_a_block(self):
        payload = {"tool_name": "Bash", "tool_input": {"command": "git log dotagents/dotnet"}}
        self.assertEqual(self.call(payload), 0)

    def test_source_inspection_does_not_enable_skill_invocation(self):
        command = 'cat ../standards/.agents/dotnet/contract/style/SKILL.md'
        self.assertEqual(self.call({"tool_name": "shell", "tool_input": {"command": command}}), 0)
        self.assertEqual(self.call({"tool_name": "Skill", "tool_input": {"skill": "dotnet:style"}}), 2)
        _, applicable, blocked = gate.assess(self.project, self.found)
        self.assertEqual(applicable, [])
        self.assertEqual([item.tier for item in blocked], ["dotnet"])

    def test_an_unrecognized_payload_allows(self):
        self.assertEqual(self.call({"tool_name": "Read", "tool_input": {"file_path": "x"}}), 0)


class ShippedDeclarations(unittest.TestCase):
    def test_every_base_agents_package_declares_itself_ubiquitous(self):
        names = sorted(path.stem for path in DECLARED.glob("*.json"))
        self.assertEqual(names, ["base", "engineering", "machine"])
        for path in DECLARED.glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["schema_version"], 1)
            self.assertEqual(data["applies"], "always")
            self.assertEqual(data["tier"], path.stem)

    def test_each_package_ships_its_declaration_at_its_payload_root(self):
        for plugin in ("base", "engineering", "machine"):
            payload = ROOT / "plugins" / plugin / "tier.json"
            self.assertTrue(payload.is_file(), f"{plugin} ships no tier.json")
            self.assertEqual(json.loads(payload.read_text(encoding="utf-8"))["tier"], plugin)

    def test_the_schema_describes_the_declarations_it_governs(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(set(schema["required"]), {"schema_version", "tier", "applies"})
        self.assertEqual(set(schema["properties"]["applies"]["enum"]), {"always", "stack-present"})
        self.assertFalse(schema["additionalProperties"])


class Runtime(unittest.TestCase):
    def test_the_session_hook_prints_valid_hook_output_or_nothing(self):
        with tempfile.TemporaryDirectory() as project:
            completed = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), "--session-context", "--project", project],
                capture_output=True,
                text=True,
                timeout=120,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        if completed.stdout.strip():
            emitted = json.loads(completed.stdout)
            self.assertEqual(
                emitted["hookSpecificOutput"]["hookEventName"], "SessionStart"
            )

    def test_a_malformed_payload_never_wedges_a_session(self):
        completed = subprocess.run(
            [sys.executable, "-B", str(SCRIPT)],
            input="not json",
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
