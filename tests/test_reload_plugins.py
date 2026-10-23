from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/machine/scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("reload_plugins", SCRIPTS / "reload_plugins.py")
REFRESH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REFRESH)
SESSION_VARIABLES = ("CLAUDE_CODE_SESSION_ID", "CLAUDE_PID", "CLAUDE_CODE_CHILD_SESSION")
ISOLATION = []


def setUpModule():
    home = tempfile.TemporaryDirectory(prefix="sync plugins home ")
    ISOLATION.append(home)
    environment = {key: value for key, value in os.environ.items() if key not in SESSION_VARIABLES}
    environment.update(CLAUDE_CONFIG_DIR=str(Path(home.name) / "claude"), CODEX_HOME=str(Path(home.name) / "codex"),
                       AGENT_STATE_DIRECTORY=str(Path(home.name) / "state"))
    patcher = mock.patch.dict(os.environ, environment, clear=True)
    patcher.start()
    ISOLATION.append(patcher)


def tearDownModule():
    for item in reversed(ISOLATION):
        (item.stop if hasattr(item, "stop") else item.cleanup)()


def updated(version="v2", outcome="updated", **extra):
    return json.dumps({"command": "update", "outcome": "ok", "updateOutcome": outcome, "newVersion": version, **extra})


class FakeClaude:
    """A claude CLI double whose update writes the reported version into its own installation records."""

    def __init__(self, installations, persist=True, version="v2", errors=None):
        self.installations = installations
        self.persist = persist
        self.version = version
        self.errors = errors or {}
        self.commands = []

    def __call__(self, command, cwd):
        self.commands.append((command, Path(cwd)))
        if command[1:3] == ["plugin", "list"]:
            return json.dumps([{**entry, "errors": self.errors.get(entry["id"], [])} for entry in self.installations])
        if command[1:3] == ["plugin", "update"]:
            identity, scope = command[3], command[5]
            for entry in self.installations:
                if (self.persist and entry["id"] == identity and entry["scope"] == scope
                        and (scope == "user" or REFRESH.path_key(entry["projectPath"]) == REFRESH.path_key(cwd))):
                    entry["version"] = self.version
            return "Checking for updates\n" + updated(self.version)
        return ""


class RefreshCliTests(unittest.TestCase):
    def test_default_uses_native_commands_without_verification_or_bound_launch(self):
        with mock.patch.object(REFRESH.agent_cli, "resolve_claude_executable", return_value="claude"), \
                mock.patch.object(REFRESH, "selection", return_value=({"tj-agents": "tj-agents/marketplace"}, ["machine@tj-agents"])), \
                mock.patch.object(REFRESH, "verify") as verify, \
                mock.patch.object(REFRESH, "read_json", return_value={"tj-agents": {}}), \
                mock.patch("sys.stdout"), mock.patch("sys.stderr"):
            fake = FakeClaude([{"id": "machine@tj-agents", "scope": "user", "enabled": True, "version": "v1"}])
            with mock.patch.object(REFRESH, "run", side_effect=fake):
                self.assertEqual(0, REFRESH.main(["--host", "claude", "--all"]))
        self.assertEqual([command for command, _ in fake.commands], [
            ["claude", "plugin", "marketplace", "update", "tj-agents"],
            ["claude", "plugin", "list", "--json"],
            ["claude", "plugin", "update", "machine@tj-agents", "--scope", "user", "--json"],
            ["claude", "plugin", "list", "--json"],
        ])
        verify.assert_not_called()

    def test_default_applies_published_events_and_falls_back_to_a_full_refresh_when_unconfigured(self):
        for result, code in (("current", 0), ("updated", 0), ("failed", 1), ("offline", 1)):
            with self.subTest(result=result), mock.patch.object(REFRESH.launch_check, "check", return_value=result), \
                    mock.patch.object(REFRESH, "refresh") as refresh, mock.patch("sys.stdout"), mock.patch("sys.stderr"):
                self.assertEqual(code, REFRESH.main([]))
                refresh.assert_not_called()
        with mock.patch.object(REFRESH.launch_check, "check", return_value="unconfigured"), \
                mock.patch.object(REFRESH.agent_cli, "resolve_claude_executable", return_value="claude"), \
                mock.patch.object(REFRESH, "selection", return_value=({}, [])), \
                mock.patch.object(REFRESH, "refresh") as refresh, mock.patch("sys.stdout"), mock.patch("sys.stderr"):
            self.assertEqual(0, REFRESH.main(["--host", "claude"]))
        refresh.assert_called_once()

    def test_a_published_repository_refreshes_only_the_claude_marketplaces_that_list_or_publish_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, plugins in (("tj-agents", [{"name": "base", "source": {
                    "source": "git-subdir", "url": "https://github.com/tj-agents/core.git", "path": "plugins/base"}}]),
                                  ("other", [{"name": "kit", "source": "./plugins/kit"}])):
                catalog = root / name / ".claude-plugin/marketplace.json"
                catalog.parent.mkdir(parents=True)
                catalog.write_text(json.dumps({"plugins": plugins}), encoding="utf-8")
            (root / "plugins").mkdir()
            (root / "plugins/known_marketplaces.json").write_text(json.dumps({
                "tj-agents": {"source": {"source": "github", "repo": "tj-agents/marketplace"},
                              "installLocation": str(root / "tj-agents")},
                "other": {"source": {"source": "github", "repo": "tj-agents/other"},
                          "installLocation": str(root / "other")}}), encoding="utf-8")
            (root / "settings.json").write_text(json.dumps({"enabledPlugins": {
                "base@tj-agents": True, "kit@other": True}}), encoding="utf-8")
            for repositories, chosen in (({"tj-agents/core"}, {"tj-agents"}), ({"tj-agents/marketplace"}, {"tj-agents"}),
                                         ({"tj-agents/other"}, {"other"}), ({"tj-agents/none"}, None),
                                         (None, {"tj-agents", "other"})):
                with self.subTest(repositories=repositories), \
                        mock.patch.object(REFRESH, "configuration_root", return_value=root), \
                        mock.patch.object(REFRESH.agent_cli, "resolve_claude_executable", return_value="claude"), \
                        mock.patch.object(REFRESH, "refresh") as refresh:
                    self.assertTrue(REFRESH.refresh_repositories(root / "project", repositories))
                    if chosen is None:
                        refresh.assert_not_called()
                    else:
                        self.assertEqual(chosen, set(refresh.call_args.args[3]))
                        self.assertEqual([identity for identity in ("base@tj-agents", "kit@other")
                                          if identity.rsplit("@", 1)[1] in chosen], refresh.call_args.args[4])

    def test_refresh_updates_applicable_claude_local_installations(self):
        fake = FakeClaude([
            {"id": "machine@tj-agents", "scope": "local", "projectPath": str(ROOT), "enabled": True, "version": "v1"},
            {"id": "machine@tj-agents", "scope": "local", "projectPath": str(ROOT / "other"), "enabled": True,
             "version": "v1"},
            {"id": "machine@tj-agents", "scope": "user", "enabled": True, "version": "v1"}])
        with mock.patch.object(REFRESH, "read_json", return_value={}), mock.patch.object(REFRESH, "run", side_effect=fake):
            self.assertEqual(["machine@tj-agents"], REFRESH.refresh("claude", "claude", ROOT, {}, ["machine@tj-agents"]))
        self.assertEqual(fake.commands, [
            (["claude", "plugin", "list", "--json"], ROOT),
            (["claude", "plugin", "update", "machine@tj-agents", "--scope", "local", "--json"], ROOT),
            (["claude", "plugin", "update", "machine@tj-agents", "--scope", "user", "--json"], ROOT),
            (["claude", "plugin", "list", "--json"], ROOT),
        ])
        self.assertEqual("v1", fake.installations[1]["version"])

    def test_recorded_revisions_skip_update_calls_for_unchanged_plugins(self):
        fake = FakeClaude([
            {"id": "base@tj-agents", "scope": "user", "enabled": True, "version": "v1"},
            {"id": "machine@tj-agents", "scope": "user", "enabled": True, "version": "v1"}])
        recorded = {"base@tj-agents": "same"}
        revisions = {"base@tj-agents": "same", "machine@tj-agents": "changed"}
        with mock.patch.object(REFRESH, "read_json", return_value={}), mock.patch.object(REFRESH, "run", side_effect=fake), \
                mock.patch.object(REFRESH, "plugin_revision", side_effect=lambda identity: revisions[identity]):
            updated = REFRESH.refresh("claude", "claude", ROOT, {}, ["base@tj-agents", "machine@tj-agents"], recorded)
        self.assertEqual(["machine@tj-agents"], updated)
        self.assertEqual([command for command, _ in fake.commands], [
            ["claude", "plugin", "list", "--json"],
            ["claude", "plugin", "update", "machine@tj-agents", "--scope", "user", "--json"],
            ["claude", "plugin", "list", "--json"],
        ])
        self.assertEqual("changed", recorded["machine@tj-agents"])

    def test_claude_installs_only_at_the_scope_the_repository_declares(self):
        for declared, scope in (("settings.local.json", "local"), ("settings.json", "project")):
            def settings(path, declared=declared):
                return {"enabledPlugins": {"infonetica@tj-agents": True}} if path.name == declared else {}
            fake = FakeClaude([])

            def install(command, cwd, fake=fake, scope=scope):
                if command[2] == "install":
                    fake.installations.append({"id": command[3], "scope": scope, "projectPath": str(cwd),
                                               "enabled": True, "version": "v1"})
                return fake(command, cwd)
            with self.subTest(declared=declared), mock.patch.object(REFRESH, "read_json", side_effect=settings), \
                    mock.patch.object(REFRESH, "run", side_effect=install):
                REFRESH.refresh("claude", "claude", ROOT, {}, ["infonetica@tj-agents"])
            self.assertEqual([command for command, _ in fake.commands], [
                ["claude", "plugin", "list", "--json"],
                ["claude", "plugin", "install", "infonetica@tj-agents", "--scope", scope],
                ["claude", "plugin", "update", "infonetica@tj-agents", "--scope", scope, "--json"],
                ["claude", "plugin", "list", "--json"],
            ])

    def test_a_project_declaration_still_updates_the_user_installation_every_other_directory_uses(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / ".claude").mkdir()
            (project / ".claude/settings.local.json").write_text(json.dumps({"enabledPlugins": {
                "machine@tj-agents": True}}), encoding="utf-8")
            fake = FakeClaude([
                {"id": "machine@tj-agents", "scope": "user", "enabled": True, "version": "v1"},
                {"id": "machine@tj-agents", "scope": "local", "projectPath": str(project), "enabled": True,
                 "version": "v1"}])
            with mock.patch.object(REFRESH, "run", side_effect=fake):
                REFRESH.refresh("claude", "claude", project, {}, ["machine@tj-agents"])
        self.assertIn(["claude", "plugin", "update", "machine@tj-agents", "--scope", "user", "--json"],
                      [command for command, _ in fake.commands])
        self.assertEqual(["v2", "v2"], [entry["version"] for entry in fake.installations])

    def test_an_update_that_reports_success_but_does_not_persist_fails(self):
        fake = FakeClaude([{"id": "machine@tj-agents", "scope": "user", "enabled": True, "version": "v1"}], persist=False)
        with mock.patch.object(REFRESH, "read_json", return_value={}), mock.patch.object(REFRESH, "run", side_effect=fake), \
                self.assertRaisesRegex(REFRESH.RefreshError, r"machine@tj-agents \(user\) update did not persist.*v1.*v2"):
            REFRESH.refresh("claude", "claude", ROOT, {}, ["machine@tj-agents"])

    def test_a_skipped_or_stale_catalog_update_is_a_failure_even_with_exit_code_zero(self):
        for output in (updated(outcome="skipped", message="Skipped - pinned"),
                       updated(outcome="up_to_date", refreshFailed=True), "Updated.\n"):
            def run(command, cwd, output=output):
                return output if command[2] == "update" else json.dumps(
                    [{"id": "machine@tj-agents", "scope": "user", "enabled": True, "version": "v1"}])
            with self.subTest(output=output), mock.patch.object(REFRESH, "read_json", return_value={}), \
                    mock.patch.object(REFRESH, "run", side_effect=run), self.assertRaises(REFRESH.RefreshError):
                REFRESH.refresh("claude", "claude", ROOT, {}, ["machine@tj-agents"])

    def test_listed_plugin_errors_fail_the_refresh_loudly(self):
        dependency = 'Dependency "work@work-agents" is not installed'
        fake = FakeClaude([
            {"id": "infonetica@tj-agents", "scope": "user", "enabled": True, "version": "v1"},
            {"id": "infonetica@tj-agents", "scope": "local", "projectPath": str(ROOT / "elsewhere"), "enabled": True,
             "version": "v1"}], errors={"infonetica@tj-agents": [dependency]})
        with mock.patch.object(REFRESH, "read_json", return_value={}), mock.patch.object(REFRESH, "run", side_effect=fake), \
                self.assertRaises(REFRESH.RefreshError) as raised:
            REFRESH.refresh("claude", "claude", ROOT, {}, ["infonetica@tj-agents"])
        self.assertEqual(f"infonetica@tj-agents (user): {dependency}", str(raised.exception))

    def test_main_reports_refresh_problems_on_stderr_and_fails(self):
        with mock.patch.object(REFRESH.agent_cli, "resolve_claude_executable", return_value="claude"), \
                mock.patch.object(REFRESH, "selection", return_value=({}, ["machine@tj-agents"])), \
                mock.patch.object(REFRESH, "refresh", side_effect=REFRESH.RefreshError("machine@tj-agents (user): broken")), \
                mock.patch("sys.stdout"), mock.patch("sys.stderr") as stderr:
            self.assertEqual(1, REFRESH.main(["--host", "claude", "--all"]))
        self.assertIn("plugins: claude: machine@tj-agents (user): broken",
                      "".join(call.args[0] for call in stderr.write.call_args_list))

    def test_codex_refresh_removes_project_only_plugins_from_user_scope(self):
        with tempfile.TemporaryDirectory() as home:
            config = Path(home) / "config.toml"
            config.write_text('[plugins."base@tj-agents"]\nenabled = true\n', encoding="utf-8")

            def add(command, project):
                identity = command[-1]
                if command[2] == "add":
                    config.write_text(config.read_text(encoding="utf-8")
                                      + f'\n[plugins."{identity}"]\nenabled = true\n', encoding="utf-8")
                return ""
            with mock.patch.dict("os.environ", {"CODEX_HOME": home}), mock.patch.object(REFRESH, "run", side_effect=add):
                REFRESH.refresh("codex", "codex", ROOT, {}, ["base@tj-agents", "infonetica@tj-agents"])
            text = config.read_text(encoding="utf-8")
        self.assertIn('[plugins."base@tj-agents"]\nenabled = true', text)
        self.assertNotIn('infonetica@tj-agents', text)

    def test_missing_claude_marketplace_is_registered_before_refresh(self):
        with mock.patch.object(REFRESH, "read_json", return_value={}), \
                mock.patch.object(REFRESH, "run") as run:
            REFRESH.refresh("claude", "claude", ROOT, {"tj-agents": "tj-agents/marketplace"}, [])
        self.assertEqual([call.args[0] for call in run.call_args_list], [
            ["claude", "plugin", "marketplace", "add", "tj-agents/marketplace"],
            ["claude", "plugin", "marketplace", "update", "tj-agents"],
        ])

    def test_packaged_entry_point_resolves_from_each_skill_surface(self):
        package = ROOT / "plugins/machine"
        for relative in ("skills/sync-plugins", "codex-skills/sync-plugins",
                         ".agents/machine/utility/sync-plugins"):
            with self.subTest(surface=relative):
                result = subprocess.run([sys.executable, "-I", "-B", str(package / relative / "scripts/sync_plugins.py"),
                                         "--help"], cwd=ROOT.parent, capture_output=True, text=True,
                                        encoding="utf-8", timeout=20)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertIn("--verify-only", result.stdout)

    def test_project_selection_overrides_user_and_foreign_sources_are_untouched(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            for path in (root / "settings.json", project / ".claude/settings.json"):
                path.parent.mkdir(parents=True, exist_ok=True)
            (root / "settings.json").write_text(json.dumps({"enabledPlugins": {"base@tj-agents": True}}))
            (project / ".claude/settings.json").write_text(json.dumps({
                "enabledPlugins": {"base@tj-agents": False, "machine@tj-agents": True, "other@foreign": True},
                "extraKnownMarketplaces": {
                    "tj-agents": {"source": {"source": "github", "repo": "tj-agents/marketplace"}},
                    "foreign": {"source": {"source": "github", "repo": "elsewhere/plugin"}},
                }}))
            with mock.patch.object(REFRESH, "configuration_root", return_value=root):
                sources, enabled = REFRESH.selection("claude", "unused", project)
            self.assertEqual({"tj-agents": "tj-agents/marketplace"}, sources)
            self.assertEqual(["machine@tj-agents"], enabled)

    def test_verification_detects_stale_package_bytes_at_a_current_marketplace_revision(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            market = root / "market"
            source = market / "plugins/base"
            install = root / "cache/base"
            for path in (market / ".claude-plugin", source, install, root / "plugins"):
                path.mkdir(parents=True, exist_ok=True)
            (source / "payload").write_bytes(b"current")
            (install / "payload").write_bytes(b"old")
            (market / ".claude-plugin/marketplace.json").write_text(json.dumps({
                "plugins": [{"name": "base", "source": "./plugins/base"}]}), encoding="utf-8")
            (root / "plugins/known_marketplaces.json").write_text(json.dumps({
                "tj-agents": {"installLocation": str(market)}}), encoding="utf-8")
            inventory = [{"id": "base@tj-agents", "enabled": True, "scope": "user", "installPath": str(install)}]
            with mock.patch.object(REFRESH, "configuration_root", return_value=root), \
                    mock.patch.object(REFRESH, "run", side_effect=[json.dumps(inventory), "a" * 40 + " refs/heads/main", "a" * 40]), \
                    mock.patch("sys.stderr"):
                report = REFRESH.verify("claude", "claude", root, {"tj-agents": "tj-agents/marketplace"}, ["base@tj-agents"])
            self.assertEqual(1, len(report["problems"]))
            self.assertIn("Native installed bytes differ", report["problems"][0])

    def test_verification_ignores_claude_in_use_markers_and_reports_listed_errors(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            market = root / "market"
            source = market / "plugins/base"
            install = root / "cache/base"
            for path in (market / ".claude-plugin", source, install / ".in_use", root / "plugins"):
                path.mkdir(parents=True, exist_ok=True)
            (source / "payload").write_bytes(b"current")
            (install / "payload").write_bytes(b"current")
            (install / ".in_use" / "4242").write_text('{"pid":4242}', encoding="utf-8")
            (market / ".claude-plugin/marketplace.json").write_text(json.dumps({
                "plugins": [{"name": "base", "source": "./plugins/base"}]}), encoding="utf-8")
            (root / "plugins/known_marketplaces.json").write_text(json.dumps({
                "tj-agents": {"installLocation": str(market)}}), encoding="utf-8")
            for errors, expected in (([], []), (["broken hook"], ["base@tj-agents (user): broken hook"])):
                inventory = [{"id": "base@tj-agents", "enabled": True, "scope": "user", "installPath": str(install),
                              "errors": errors}]
                with self.subTest(errors=errors), mock.patch.object(REFRESH, "configuration_root", return_value=root), \
                        mock.patch.object(REFRESH, "run", side_effect=[json.dumps(inventory), "a" * 40 + " refs/heads/main",
                                                                       "a" * 40]), \
                        mock.patch("sys.stderr"):
                    report = REFRESH.verify("claude", "claude", root, {"tj-agents": "tj-agents/marketplace"},
                                            ["base@tj-agents"])
                self.assertEqual(expected, report["problems"])

    def test_supported_github_sources_are_normalized_before_selection(self):
        for source in ("ssh://git@github.com/TJ-Agents/core.git", "git@github.com:tj-agents/core.git",
                       "https://github.com/TJ-AGENTS/Core.git", "tj-agents/core"):
            with self.subTest(source=source):
                self.assertEqual("tj-agents/core", REFRESH.repository(source))
                config = {"marketplaces": {"core": {"source_type": "git", "source": source}},
                          "plugins": {"base@core": {"enabled": True}}}
                with mock.patch.object(REFRESH, "AppServer") as server:
                    server.return_value.__enter__.return_value.request.return_value = {"config": config}
                    self.assertEqual(({"core": "tj-agents/core"}, ["base@core"]),
                                     REFRESH.selection("codex", "codex", ROOT))

    def test_external_publisher_packages_are_verified_at_the_declared_revision(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            publisher = root / "publisher"
            publisher.mkdir()
            subprocess.run(["git", "init", str(publisher)], check=True, capture_output=True)
            package = publisher / "plugins/base"
            package.mkdir(parents=True)
            (package / "payload").write_bytes(b"published")
            subprocess.run(["git", "-C", str(publisher), "add", "."], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(publisher), "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                            "commit", "-m", "package"], check=True, capture_output=True)
            revision = subprocess.check_output(["git", "-C", str(publisher), "rev-parse", "HEAD"], text=True).strip()
            run_native = REFRESH.run

            def run(command, project):
                arguments = [str(publisher) if value == "https://github.com/tj-agents/core.git" else value for value in command]
                return run_native(arguments, project)

            clones = {}
            source = {"source": "git-subdir", "url": "ssh://git@github.com/TJ-Agents/core.git",
                      "path": "plugins/base", "sha": revision}
            with mock.patch.object(REFRESH, "run", side_effect=run) as commands, mock.patch("sys.stderr"):
                expected = REFRESH.source_tree(source, root, root, root / "scratch", clones)
                self.assertEqual({"payload": b"published"}, expected)
                self.assertEqual(expected, REFRESH.source_tree(source, root, root, root / "scratch", clones))
                self.assertEqual(1, sum("fetch" in call.args[0] for call in commands.call_args_list))
                source["path"] = "./../../escape"
                with self.assertRaisesRegex(REFRESH.RefreshError, "escapes"):
                    REFRESH.source_tree(source, root, root, root / "scratch", clones)

    def test_another_projects_installation_does_not_satisfy_verification(self):
        inventory = [{"id": "base@tj-agents", "enabled": True, "scope": "project", "projectPath": str(ROOT / "elsewhere")}]
        with mock.patch.object(REFRESH, "run", return_value=json.dumps(inventory)), mock.patch("sys.stderr"):
            report = REFRESH.verify("claude", "claude", ROOT, {}, ["base@tj-agents"])
        self.assertEqual(["Missing enabled native installation: base@tj-agents"], report["problems"])

    def test_verify_only_does_not_modify_installations(self):
        with mock.patch.object(REFRESH.agent_cli, "resolve_codex_executable", return_value=("codex", "version")), \
                mock.patch.object(REFRESH, "selection", return_value=({}, [])), \
                mock.patch.object(REFRESH, "refresh") as refresh, \
                mock.patch.object(REFRESH, "verify", return_value={"problems": []}) as verify, \
                mock.patch("sys.stdout"), mock.patch("sys.stderr"):
            self.assertEqual(0, REFRESH.main(["--host", "codex", "--verify-only"]))
        refresh.assert_not_called()
        verify.assert_called_once()

    def test_native_failure_is_reported_and_other_host_is_still_attempted(self):
        with mock.patch.object(REFRESH.agent_cli, "resolve_claude_executable", return_value="claude"), \
                mock.patch.object(REFRESH.agent_cli, "resolve_codex_executable", return_value=("codex", "version")), \
                mock.patch.object(REFRESH, "selection", side_effect=[REFRESH.RefreshError("failed"), ({}, [])]), \
                mock.patch.object(REFRESH, "refresh") as refresh, mock.patch("sys.stdout"), mock.patch("sys.stderr"):
            self.assertEqual(1, REFRESH.main([]))
        refresh.assert_called_once_with("codex", "codex", Path.cwd().resolve(), {}, [])


if __name__ == "__main__":
    unittest.main()
