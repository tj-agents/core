from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/machine/scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("refresh_cli", SCRIPTS / "refresh_cli.py")
REFRESH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REFRESH)


class RefreshCliTests(unittest.TestCase):
    def test_default_uses_native_commands_without_verification_or_bound_launch(self):
        with mock.patch.object(REFRESH.agent_cli, "resolve_claude_executable", return_value="claude"), \
                mock.patch.object(REFRESH, "selection", return_value=({"tj-agents": "tj-agents/marketplace"}, ["machine@tj-agents"])), \
                mock.patch.object(REFRESH, "run") as run, mock.patch.object(REFRESH, "verify") as verify, \
                mock.patch.object(REFRESH, "read_json", return_value={"tj-agents": {}}), \
                mock.patch("sys.stdout"), mock.patch("sys.stderr"):
            self.assertEqual(0, REFRESH.main(["--host", "claude"]))
        self.assertEqual([call.args[0] for call in run.call_args_list], [
            ["claude", "plugin", "marketplace", "update", "tj-agents"],
            ["claude", "plugin", "install", "machine@tj-agents", "--scope", "project"],
            ["claude", "plugin", "update", "machine@tj-agents", "--scope", "project"],
        ])
        verify.assert_not_called()

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
        for relative in ("skills/refresh-cli", "codex-skills/refresh-cli",
                         ".agents/machine/utility/refresh-cli"):
            with self.subTest(surface=relative):
                result = subprocess.run([sys.executable, "-I", "-B", str(package / relative / "scripts/refresh_cli.py"),
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
