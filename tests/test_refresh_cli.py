from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents" / "machine" / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("refresh_cli", SCRIPTS / "refresh_cli.py")
REFRESH = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = REFRESH
SPEC.loader.exec_module(REFRESH)

MAIN = "b" * 40
OLD = "a" * 40


class RefreshCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="refresh cli ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.environ = {"CLAUDE_CONFIG_DIR": str(self.root / "claude"), "CODEX_HOME": str(self.root / "codex")}
        self.project = self.root / "project"
        self.project.mkdir()

    def write(self, path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def install(self, host: str, identity: str, revision: str, directory: str) -> Path:
        name, marketplace = identity.rsplit("@", 1)
        package = self.root / host / "plugins" / "cache" / marketplace / name
        (package / directory).mkdir(parents=True)
        self.write(package / REFRESH.MARKER, {
            "schema_version": 1, "identity": identity, "repository": "https://github.com/tj-agents/core.git",
            "revision": revision,
        })
        return package / directory

    def test_repository_names_cover_github_sources(self):
        cases = {
            "https://github.com/tj-agents/core.git": "tj-agents/core",
            "git@github.com:tj-agents/marketplace.git": "tj-agents/marketplace",
            "https://github.com/Concertable/agents": "Concertable/agents",
            "C:\\local\\catalog": None,
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(REFRESH.repository_name(source), expected)
        self.assertEqual(REFRESH.repository_name({"source": "github", "repo": "tj-agents/marketplace"}),
                         "tj-agents/marketplace")

    def test_only_tj_agents_marketplaces_are_updated(self):
        self.write(self.root / "claude/plugins/known_marketplaces.json", {
            "tj-agents": {"source": {"source": "github", "repo": "tj-agents/marketplace"}},
            "agents": {"source": {"source": "github", "repo": "Concertable/agents"}},
            "local": {"source": {"source": "directory", "path": "C:/x"}},
        })
        self.assertEqual(REFRESH.claude_marketplaces(self.environ), ["tj-agents"])
        selection = {"effective_marketplace_configuration": {
            "base-agents": {"source_type": "git", "source": "https://github.com/tj-agents/core.git"},
            "openai-bundled": {"source_type": "local", "source": "C:/bundled"},
            "agents": {"source_type": "git", "source": "https://github.com/Concertable/agents.git"},
        }}
        self.assertEqual(REFRESH.codex_marketplaces(selection), ["base-agents"])

    def test_claude_registry_version_must_name_the_refreshed_install(self):
        current = self.install("claude", "machine@tj-agents", MAIN, MAIN)
        self.write(self.root / "claude/plugins/installed_plugins.json", {"version": 2, "plugins": {
            "machine@tj-agents": [{"scope": "user", "installPath": str(current), "version": "61b5b1ee19f7-aee5d9df"}],
        }})
        report = REFRESH.verify("claude", {"machine@tj-agents"}, lambda _repository: MAIN, self.environ)
        self.assertEqual(len(report["problems"]), 1)
        self.assertIn("so Claude loads another copy", report["problems"][0])

        self.write(self.root / "claude/plugins/installed_plugins.json", {"version": 2, "plugins": {
            "machine@tj-agents": [{"scope": "user", "installPath": str(current), "version": MAIN}],
        }})
        report = REFRESH.verify("claude", {"machine@tj-agents"}, lambda _repository: MAIN, self.environ)
        self.assertEqual(report["problems"], [])
        self.assertTrue(report["packages"][0]["current"])

    def test_stale_enabled_packages_are_reported_and_disabled_ones_ignored(self):
        self.install("codex", "machine@base-agents", OLD, "local")
        self.install("codex", "engineering@base-agents", OLD, "local")
        report = REFRESH.verify("codex", {"machine@base-agents"}, lambda _repository: MAIN, self.environ)
        self.assertEqual([package["identity"] for package in report["packages"]], ["machine@base-agents"])
        self.assertEqual(report["problems"], [f"machine@base-agents is at {OLD}, main is {MAIN}"])

    def test_codex_reports_stale_cache_outside_machine_as_unused(self):
        self.install("codex", "machine@base-agents", MAIN, "local")
        self.install("codex", "cpp@cpp-agents", OLD, "local")
        report = REFRESH.verify("codex", {"machine@base-agents", "cpp@cpp-agents"}, lambda _repository: MAIN,
                                self.environ)
        self.assertEqual(report["problems"], [])
        self.assertEqual(report["unused_stale_cache"], ["cpp@cpp-agents"])

    def test_no_enabled_package_is_a_problem(self):
        report = REFRESH.verify("codex", set(), lambda _repository: MAIN, self.environ)
        self.assertEqual(report["problems"], ["no rolling tj-agents package is installed for codex"])

    def test_refresh_updates_marketplaces_then_runs_the_bound_refresh(self):
        self.write(self.root / "claude/plugins/known_marketplaces.json", {
            "tj-agents": {"source": {"source": "github", "repo": "tj-agents/marketplace"}},
        })
        self.write(self.root / "claude/settings.json", {"enabledPlugins": {"machine@tj-agents": True, "x@y": False}})
        calls = []
        launch = mock.Mock(return_value=0)
        with mock.patch.object(REFRESH.agent_cli, "resolve_claude_executable", return_value="claude.exe"), \
                mock.patch.object(REFRESH, "run", side_effect=lambda command, *_args: calls.append(command)):
            enabled = REFRESH.refresh("claude", self.project, environ=self.environ, launch=launch)
        self.assertEqual(calls, [["claude.exe", "plugin", "marketplace", "update", "tj-agents"]])
        launch.assert_called_once_with("claude", "claude.exe", self.project, ["--version"])
        self.assertEqual(enabled, {"machine@tj-agents"})

    def test_verify_only_changes_nothing(self):
        self.write(self.root / "claude/plugins/known_marketplaces.json", {})
        launch = mock.Mock()
        with mock.patch.object(REFRESH.agent_cli, "resolve_claude_executable", return_value="claude.exe"), \
                mock.patch.object(REFRESH, "run") as run:
            REFRESH.refresh("claude", self.project, verify_only=True, environ=self.environ, launch=launch)
        run.assert_not_called()
        launch.assert_not_called()

    def test_failed_bound_refresh_is_reported(self):
        self.write(self.root / "claude/plugins/known_marketplaces.json", {})
        for launch in (mock.Mock(return_value=1),
                       mock.Mock(side_effect=REFRESH.StartupBindingError("preflight failed"))):
            with self.subTest(launch=launch), \
                    mock.patch.object(REFRESH.agent_cli, "resolve_claude_executable", return_value="claude.exe"):
                with self.assertRaises(REFRESH.RefreshError):
                    REFRESH.refresh("claude", self.project, environ=self.environ, launch=launch)


if __name__ == "__main__":
    unittest.main()
