import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".agents" / "hooks"))
SOURCE = ROOT / ".codex" / "hooks" / "marketplace_refresh.py"
SPEC = importlib.util.spec_from_file_location("marketplace_refresh", SOURCE)
marketplace_refresh = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(marketplace_refresh)


class MarketplaceRefreshTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / "state"
        self.codex_home = self.root / "codex-home"
        self.environment = patch.dict(
            os.environ,
            {
                marketplace_refresh.STATE_DIRECTORY_ENV: str(self.state),
                "CODEX_HOME": str(self.codex_home),
            },
            clear=False,
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_profile_managed_repo_is_refreshed(self):
        repo = self.root / "repo"
        (repo / ".agents").mkdir(parents=True)
        (repo / ".agents" / "profile.json").write_text("{}", encoding="utf-8")
        payload = json.dumps({"cwd": str(repo), "session_id": "profile-session"})
        with (
            patch("sys.stdin.read", return_value=payload),
            patch.object(marketplace_refresh, "start_refresh_if_due", return_value=True) as start,
        ):
            self.assertEqual(0, marketplace_refresh.run_session_start())
        start.assert_called_once_with()

    def test_bundled_codex_is_used_when_codex_is_absent_from_path(self):
        bundled = self.codex_home / "plugins" / ".plugin-appserver" / "codex.exe"
        bundled.parent.mkdir(parents=True)
        bundled.touch()
        with patch.object(marketplace_refresh.shutil, "which", return_value=None):
            self.assertEqual(str(bundled), marketplace_refresh._codex_executable())

    def test_codex_home_is_supplied_to_every_codex_command(self):
        completed = subprocess.CompletedProcess([], 0, stdout="{}")
        with patch.object(subprocess, "run", return_value=completed) as run:
            marketplace_refresh._run("codex", ["plugin", "list", "--json"], True)
        self.assertEqual(str(self.codex_home), run.call_args.kwargs["env"]["CODEX_HOME"])

    def test_refresh_updates_only_enabled_default_git_plugins(self):
        listed = [
            {
                "pluginId": "concertable@agent-standards",
                "marketplaceName": "agent-standards",
                "installed": True,
                "enabled": True,
                "installPolicy": "INSTALLED_BY_DEFAULT",
                "marketplaceSource": {"sourceType": "git"},
            },
            {
                "pluginId": "optional@elsewhere",
                "marketplaceName": "elsewhere",
                "installed": True,
                "enabled": True,
                "installPolicy": "AVAILABLE",
                "marketplaceSource": {"sourceType": "git"},
            },
        ]
        completed = subprocess.CompletedProcess([], 0)
        with (
            patch.object(marketplace_refresh, "_codex_executable", return_value="codex"),
            patch.object(marketplace_refresh, "_installed_plugins", return_value=listed),
            patch.object(marketplace_refresh, "_run", return_value=completed) as run,
        ):
            self.assertTrue(marketplace_refresh.refresh_plugins())
        self.assertEqual(
            [
                ("codex", ["plugin", "marketplace", "upgrade", "agent-standards"]),
                ("codex", ["plugin", "add", "concertable@agent-standards"]),
            ],
            [call.args for call in run.call_args_list],
        )

    def test_failure_gets_a_short_retry_window_and_does_not_mark_success(self):
        self.state.mkdir(parents=True)
        with (
            patch.object(marketplace_refresh, "refresh_plugins", return_value=False),
            patch.object(marketplace_refresh, "_release_lock"),
            patch.object(marketplace_refresh.time, "time", return_value=1000),
        ):
            self.assertEqual(1, marketplace_refresh.run_worker())
        state = json.loads(marketplace_refresh._state_path().read_text(encoding="utf-8"))
        self.assertEqual(1000, state["last_failure"])
        self.assertNotIn("last_success", state)
        self.assertFalse(marketplace_refresh._due(1000 + marketplace_refresh.FAILURE_RETRY_SECONDS - 1))
        self.assertTrue(marketplace_refresh._due(1000 + marketplace_refresh.FAILURE_RETRY_SECONDS))

    def test_success_uses_the_full_refresh_interval(self):
        self.state.mkdir(parents=True)
        marketplace_refresh._state_path().write_text(
            json.dumps({"last_success": time.time()}), encoding="utf-8"
        )
        self.assertFalse(marketplace_refresh._due())


if __name__ == "__main__":
    unittest.main()
