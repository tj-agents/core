"""The stack-tier gate decides applicability from shipped declarations the running host enables."""

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


HOST_VARIABLES = ("PLUGIN_ROOT", "CODEX_PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT", "CODEX_THREAD_ID",
                  "CLAUDE_CODE_SESSION_ID", "CLAUDE_CONFIG_DIR", "CODEX_HOME")
SKILL = {"schema_version": 1, "tier": "skill", "applies": "always"}
TEMPLATE = {"schema_version": 1, "tier": "template", "applies": "always"}
PERSONAL = {"schema_version": 1, "tier": "personal", "applies": "always"}
PYTHON = {"schema_version": 1, "tier": "python", "stack": "Python", "applies": "stack-present",
          "detect": {"files": ["pyproject.toml"]}}


def declaration(plugin, marketplace, data):
    return gate.Declaration(plugin, marketplace, data)


class DeclarationDiscovery(unittest.TestCase):
    def test_only_the_running_hosts_cache_is_read(self):
        with tempfile.TemporaryDirectory() as home:
            codex = Path(home) / ".codex" / "plugins" / "cache"
            claude = Path(home) / ".claude" / "plugins" / "cache"
            codex.mkdir(parents=True)
            claude.mkdir(parents=True)
            script = codex / "tj-agents" / "engineering" / "1.0.0" / "hooks" / "tier_gate.py"
            cleared = {name: "" for name in HOST_VARIABLES}
            with unittest.mock.patch.dict(os.environ, cleared), \
                    unittest.mock.patch.object(gate.Path, "home", return_value=Path(home)):
                with unittest.mock.patch.object(gate, "__file__", str(script)):
                    self.assertEqual([codex.resolve()], gate.cache_roots())
                with unittest.mock.patch.dict(os.environ, {"CLAUDE_PLUGIN_ROOT": home}):
                    self.assertEqual([claude.resolve()], gate.cache_roots())
                self.assertEqual([], gate.cache_roots())

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

    def test_an_invalid_declaration_retains_its_installed_identity(self):
        with tempfile.TemporaryDirectory() as cache:
            for name, body in (
                ("broken", "{not json"),
                ("future", json.dumps({"schema_version": 99, "tier": "x", "applies": "always"})),
                ("nameless", json.dumps({"schema_version": 1, "applies": "always"})),
            ):
                payload = Path(cache) / name / name / "1.0.0"
                payload.mkdir(parents=True)
                (payload / "tier.json").write_text(body, encoding="utf-8")

            found = gate.declarations([cache])
            self.assertEqual([item.plugin for item in found], ["broken", "nameless", "future"])
            self.assertTrue(all(item.diagnostics for item in found))

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


class EnabledPlugins(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.claude, self.codex, self.project = root / "claude", root / "codex", root / "project"
        self.project.mkdir()
        payloads = {plugin: self.install(self.claude, plugin, data) for plugin, data in (
            ("base", BASE), ("skill", SKILL), ("template", TEMPLATE), ("python", PYTHON), ("personal", PERSONAL))}
        registry = {"plugins": {plugin + "@tj-agents": [{"scope": "user", "installPath": str(payload)}]
                                for plugin, payload in payloads.items()}}
        (self.claude / "plugins" / "installed_plugins.json").write_text(json.dumps(registry), encoding="utf-8")
        self.write(self.claude / "settings.json", {"base@tj-agents": True})
        for plugin in ("kit", "machine"):
            self.install(self.codex, plugin, {"schema_version": 1, "tier": plugin, "applies": "always"})
        (self.codex / "config.toml").write_text('[plugins."kit@tj-agents"]\nenabled = true\n', encoding="utf-8")
        self.environment = dict({name: "" for name in HOST_VARIABLES}, CLAUDE_CONFIG_DIR=str(self.claude),
                                CODEX_HOME=str(self.codex), CLAUDE_PLUGIN_ROOT=str(payloads["base"]))
        environment = unittest.mock.patch.dict(os.environ, dict(self.environment, **{gate.OVERRIDE_VARIABLE: ""}))
        environment.start()
        self.addCleanup(environment.stop)
        gate._settings.cache_clear()
        self.addCleanup(gate._settings.cache_clear)

    def install(self, profile, plugin, data):
        payload = profile / "plugins" / "cache" / "tj-agents" / plugin / "1"
        payload.mkdir(parents=True)
        (payload / "tier.json").write_text(json.dumps(data), encoding="utf-8")
        return payload

    def write(self, path, enabled):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"enabledPlugins": enabled}), encoding="utf-8")
        gate._settings.cache_clear()

    def test_only_enabled_ubiquitous_packages_apply_and_the_rest_fail_loudly(self):
        result = gate.assess(self.project)
        text = gate.statement(self.project)

        self.assertEqual([item.tier for item in result.ubiquitous], ["base"])
        self.assertEqual([item.tier for item in result.disabled], ["skill", "template"])
        self.assertEqual([line for line in text.splitlines() if line.startswith("Ubiquitous")], [
            "Ubiquitous, always applies: base.",
            "Ubiquitous but not enabled: skill, template. Run agent:refresh-plugins, then start a fresh session.",
        ])
        self.assertNotIn("`python:*`", text)
        self.assertNotIn("`personal:*`", text)

    def test_project_settings_enable_a_package_for_that_project_only(self):
        self.write(self.project / ".claude" / "settings.json", {"skill@tj-agents": True, "python@tj-agents": True})
        (self.project / "pyproject.toml").write_text("", encoding="utf-8")
        other = self.project.parent / "other"
        other.mkdir()

        here = gate.assess(self.project)
        elsewhere = gate.assess(other)

        self.assertEqual([item.tier for item in here.ubiquitous], ["base", "skill"])
        self.assertEqual([item.tier for item, _ in here.applicable], ["python"])
        self.assertEqual([item.tier for item in here.disabled], ["template"])
        self.assertEqual([item.tier for item in elsewhere.ubiquitous], ["base"])

    def test_a_later_settings_scope_overrides_an_earlier_one(self):
        self.write(self.project / ".claude" / "settings.json", {"skill@tj-agents": True})
        self.write(self.project / ".claude" / "settings.local.json", {"skill@tj-agents": False})

        result = gate.assess(self.project)

        self.assertEqual([item.tier for item in result.ubiquitous], ["base"])
        self.assertEqual([item.tier for item in result.disabled], ["skill", "template"])

    def test_a_codex_session_reads_only_codex_enablement(self):
        with unittest.mock.patch.dict(os.environ, {"CLAUDE_PLUGIN_ROOT": "", "PLUGIN_ROOT": str(self.codex)}):
            result = gate.assess(self.project)
            text = gate.statement(self.project)

        self.assertEqual([item.tier for item in result.ubiquitous], ["kit"])
        self.assertEqual(result.disabled, [])
        self.assertEqual(text, "")

    def codex_context(self):
        target = str(self.project / "module.py")
        with unittest.mock.patch.dict(os.environ, {"CLAUDE_PLUGIN_ROOT": "", "PLUGIN_ROOT": str(self.codex)}):
            return gate.statement(self.project), gate.tool_context({"tool_name": "apply_patch", "tool_input": {
                "command": "*** Begin Patch\n*** Add File: " + target + "\n+x\n*** End Patch"}})

    def test_codex_enablement_without_tomllib_is_reported_not_silently_empty(self):
        with unittest.mock.patch.dict(sys.modules, {"tomllib": None}):
            texts = self.codex_context()

        for text in texts:
            self.assertIn("Tier gate could not read Codex plugin enablement: Python 3.11+ is required.", text)

    def test_malformed_codex_enablement_is_reported(self):
        (self.codex / "config.toml").write_text("[plugins\n", encoding="utf-8")

        for text in self.codex_context():
            self.assertIn("Tier gate could not read Codex plugin enablement: "
                          + str(self.codex / "config.toml") + " is unreadable or malformed.", text)

    def test_an_undetermined_host_is_reported_not_silently_empty(self):
        target = str(self.project / "module.py")
        with unittest.mock.patch.dict(os.environ, {"CLAUDE_PLUGIN_ROOT": ""}):
            texts = (gate.statement(self.project),
                     gate.tool_context({"tool_name": "Read", "tool_input": {"file_path": target}}))

        for text in texts:
            self.assertIn("Tier gate could not determine the running host; plugin standards are unknown.", text)

    def test_personal_follows_adoption_and_never_reports_as_not_enabled(self):
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)
        self.assertNotIn("personal", gate.statement(self.project).split("Ubiquitous but not enabled:")[1].splitlines()[0])

        self.write(self.project / ".claude" / "settings.json", {"personal@tj-agents": True})
        self.assertEqual([item.tier for item, _ in gate.assess(self.project).applicable], [])

        (self.project / ".agents").mkdir()
        (self.project / ".agents" / "plugins.json").write_text(json.dumps({
            "schema_version": 1, "plugins": ["personal@tj-agents"],
            "marketplaces": {"tj-agents": {"repository": "tj-agents/marketplace"}}}), encoding="utf-8")
        self.assertIn("Applies here: `personal:*` - explicit repository adoption.", gate.statement(self.project))

    def test_path_and_tool_context_apply_the_target_repositorys_enablement(self):
        (self.project / "pyproject.toml").write_text("", encoding="utf-8")
        target = str(self.project / "module.py")
        self.assertEqual(gate.path_selection(target)["applicable"], [])

        self.write(self.project / ".claude" / "settings.json", {"python@tj-agents": True})
        self.assertEqual(gate.path_selection(target)["applicable"], ["python@tj-agents"])
        context = gate.tool_context({"tool_name": "Read", "tool_input": {"file_path": target}})
        self.assertIn("Applies here: `python:*`", context)

    def test_the_session_hook_reports_packages_this_host_has_not_enabled(self):
        completed = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--session-context", "--project", str(self.project)],
            capture_output=True, text=True, timeout=120, env=dict(os.environ, **self.environment),
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        context = json.loads(completed.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Ubiquitous, always applies: base.", context)
        self.assertIn("Ubiquitous but not enabled: skill, template.", context)


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

    def test_an_untracked_marker_in_a_repository_proves_the_stack(self):
        project = self.populated("", ["src/api/Service.csproj"])
        subprocess.run(["git", "init", "-q"], cwd=project, check=True)
        present, evidence = gate.stack_present(project, DOTNET["detect"])
        self.assertTrue(present)
        self.assertEqual(evidence, "src/api/Service.csproj")

    def test_an_ignored_marker_never_proves_the_stack(self):
        project = self.populated("", ["generated/App.csproj", "README.md"])
        (project / ".gitignore").write_text("generated/\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=project, check=True)
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
            declaration("base", "tj-agents", BASE),
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

    def test_a_mostly_untracked_repository_is_walked_once_and_never_scanned_unbounded(self):
        subprocess.run(["git", "init", "-q"], cwd=self.project, check=True)
        cache = self.project / "plugins" / "cache" / "market" / "dotnet" / "version" / "templates"
        cache.mkdir(parents=True)
        (cache / "Template.csproj").write_text("", encoding="utf-8")
        for index in range(50):
            (self.project / "projects" / f"session-{index}").mkdir(parents=True)
            (self.project / "projects" / f"session-{index}" / "transcript.jsonl").write_text("{}\n", encoding="utf-8")
        found = [*self.found, *(declaration(f"stack{index}", "tj-agents", {**DOTNET, "tier": f"stack{index}",
                                                                              "detect": {"globs": [f"*.ext{index}"]}})
                                for index in range(8))]
        commands, walks = [], []
        real_git, real_walk = gate._run_git, gate.os.walk

        def git(root, arguments):
            commands.append(arguments)
            return real_git(root, arguments)

        def walk(top, *arguments, **options):
            walks.append(top)
            return real_walk(top, *arguments, **options)

        with unittest.mock.patch.object(gate, "_run_git", side_effect=git), \
                unittest.mock.patch.object(gate.os, "walk", side_effect=walk):
            _, applicable, _ = gate.assess(self.project, found)
        self.assertEqual(applicable, [])
        self.assertFalse([command for command in commands if "--others" in command])
        self.assertEqual(1, len(walks))

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
        found = [declaration("base", "tj-agents", BASE)]
        self.assertEqual(gate.statement(self.project, found), "")

    def test_the_statement_names_what_applies_and_what_does_not(self):
        found = [
            declaration("base", "tj-agents", BASE),
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


class ShippedDeclarations(unittest.TestCase):
    def test_every_core_package_declares_itself_ubiquitous(self):
        names = sorted(path.stem for path in DECLARED.glob("*.json"))
        self.assertEqual(names, ["base", "docs", "engineering", "workflow"])
        for path in DECLARED.glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["schema_version"], 1)
            self.assertEqual(data["applies"], "always")
            self.assertEqual(data["tier"], path.stem)

    def test_each_package_ships_its_declaration_at_its_payload_root(self):
        for plugin in ("base", "engineering", "workflow"):
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
