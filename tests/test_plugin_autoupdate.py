"""Synthetic configuration and command doubles only; no network, CLI or scheduler is touched."""

import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / '.agents/machine/scripts'
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


UPDATE = load('plugin_autoupdate')
SETUP = load('setup_machine')
CORE = 'https://github.com/tj-agents/core.git'
OLD = 'a' * 40
NEW = 'b' * 40


def codex_config():
    return {
        'marketplaces': {
            'base-agents': {'source_type': 'git', 'source': CORE},
            'local-only': {'source_type': 'local', 'source': 'C:/somewhere'},
            'unused': {'source_type': 'git', 'source': 'https://github.com/tj-agents/unused.git'},
        },
        'plugins': {
            'base@base-agents': {'enabled': True},
            'machine@base-agents': {'enabled': True},
            'engineering@base-agents': {'enabled': False},
            'tool@local-only': {'enabled': True},
        },
    }


class CodexTargetTests(unittest.TestCase):
    def test_only_git_marketplaces_with_enabled_plugins_are_refreshed(self):
        targets = UPDATE.codex_targets(codex_config())

        self.assertEqual(['base-agents'], list(targets))
        self.assertEqual(['base@base-agents', 'machine@base-agents'], targets['base-agents']['plugins'])

    def test_an_unchanged_revision_runs_no_cli_command(self):
        run = mock.Mock(return_value=True)
        recorded = {UPDATE.target_key('base-agents', UPDATE.codex_targets(codex_config())['base-agents']): OLD}

        outcomes = UPDATE.refresh_codex('codex', UPDATE.codex_targets(codex_config()), recorded,
                                        revision=lambda source, ref: OLD, run=run)

        self.assertEqual({'base-agents': 'current'}, outcomes)
        run.assert_not_called()

    def test_a_changed_revision_upgrades_then_re_adds_each_enabled_plugin(self):
        run = mock.Mock(return_value=True)
        recorded = {UPDATE.target_key('base-agents', UPDATE.codex_targets(codex_config())['base-agents']): OLD}

        outcomes = UPDATE.refresh_codex('codex', UPDATE.codex_targets(codex_config()), recorded,
                                        revision=lambda source, ref: NEW, run=run)

        self.assertEqual({'base-agents': 'updated'}, outcomes)
        self.assertEqual(NEW, recorded[UPDATE.target_key('base-agents', UPDATE.codex_targets(codex_config())['base-agents'])])
        self.assertEqual([
            mock.call(['codex', 'plugin', 'marketplace', 'upgrade', 'base-agents']),
            mock.call(['codex', 'plugin', 'add', 'base@base-agents']),
            mock.call(['codex', 'plugin', 'add', 'machine@base-agents']),
        ], run.call_args_list)

    def test_a_failed_refresh_keeps_the_old_revision_so_the_next_run_retries(self):
        recorded = {UPDATE.target_key('base-agents', UPDATE.codex_targets(codex_config())['base-agents']): OLD}

        outcomes = UPDATE.refresh_codex('codex', UPDATE.codex_targets(codex_config()), recorded,
                                        revision=lambda source, ref: NEW, run=lambda command: False)

        self.assertEqual({'base-agents': 'failed'}, outcomes)
        self.assertEqual(OLD, recorded[UPDATE.target_key('base-agents', UPDATE.codex_targets(codex_config())['base-agents'])])

    def test_an_unreachable_source_changes_nothing(self):
        run = mock.Mock(return_value=True)

        outcomes = UPDATE.refresh_codex('codex', UPDATE.codex_targets(codex_config()), {},
                                        revision=lambda source, ref: None, run=run)

        self.assertEqual({'base-agents': 'unreachable'}, outcomes)
        run.assert_not_called()


class ProjectUpdateTests(unittest.TestCase):
    def test_native_project_inventory_drives_initial_installation_without_user_selection(self):
        listing = {"installed": [], "available": [
            {"pluginId": "base@tj-agents", "enabled": True,
             "marketplaceSource": {"sourceType": "git", "source": CORE}},
            {"pluginId": "disabled@tj-agents", "enabled": False,
             "marketplaceSource": {"sourceType": "git", "source": CORE}},
        ]}
        config = {"marketplaces": {"tj-agents": {"source_type": "git", "source": CORE}},
                  "plugins": {"base@tj-agents": {"enabled": True}, "disabled@tj-agents": {"enabled": False}}}
        with mock.patch.object(UPDATE, "effective_config", return_value=config), \
                mock.patch.object(UPDATE.subprocess, "run", return_value=mock.Mock(stdout=json.dumps(listing))) as run:
            targets = UPDATE.project_targets("codex", ROOT)
        self.assertEqual(["base@tj-agents"], targets["tj-agents"]["plugins"])
        self.assertEqual(ROOT, run.call_args.kwargs["cwd"])
        self.assertIn("--available", run.call_args.args[0])

    def test_absent_native_marketplace_snapshots_are_bootstrapped_before_discovery(self):
        import subprocess

        missing = subprocess.CalledProcessError(1, "codex", stderr="no snapshot")
        with mock.patch.object(UPDATE, "effective_config", return_value={}), \
                mock.patch.object(UPDATE.subprocess, "run", side_effect=[missing, mock.Mock(stdout='{"installed": [], "available": []}')]) as run, \
                mock.patch.object(UPDATE, "run_cli", return_value=True) as bootstrap:
            self.assertEqual({}, UPDATE.project_targets("codex", ROOT))
        bootstrap.assert_called_once_with(["codex", "plugin", "marketplace", "upgrade"], cwd=ROOT)
        self.assertEqual(2, run.call_count)

    def test_selected_plugin_absent_from_snapshot_still_refreshes_its_marketplace(self):
        config = {"marketplaces": {"tj-agents": {"source_type": "git", "source": CORE}},
                  "plugins": {"new@tj-agents": {"enabled": True}}}
        with mock.patch.object(UPDATE, "effective_config", return_value=config), \
                mock.patch.object(UPDATE.subprocess, "run", return_value=mock.Mock(stdout='{"installed": [], "available": []}')):
            targets = UPDATE.project_targets("codex", ROOT)
        run = mock.Mock(return_value=True)
        self.assertEqual(["new@tj-agents"], targets["tj-agents"]["missing"])
        self.assertEqual({"tj-agents": "updated"}, UPDATE.refresh_codex(
            "codex", targets, {}, revision=lambda *_: NEW, run=run, project=ROOT))
        self.assertIn(mock.call(["codex", "plugin", "add", "new@tj-agents"], cwd=ROOT), run.call_args_list)

    def test_retired_publisher_does_not_block_reachable_marketplace_refresh(self):
        targets = UPDATE.codex_targets(codex_config())
        retired = "https://github.com/tj-agents/retired.git"
        targets["base-agents"]["publishers"] = [{"source": retired, "ref": "removed"}]
        recorded = {}
        run = mock.Mock(return_value=True)
        self.assertEqual({"base-agents": "updated"}, UPDATE.refresh_codex(
            "codex", targets, recorded,
            revision=lambda source, ref: None if source == retired else NEW, run=run))
        self.assertEqual(["codex", "plugin", "marketplace", "upgrade", "base-agents"], run.call_args_list[0].args[0])
        self.assertEqual({}, recorded)

    def test_project_discovery_requires_exact_saved_trust_and_project_configuration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("trusted", "untrusted", "parent/nested"):
                (root / name / ".codex").mkdir(parents=True)
                (root / name / ".codex/config.toml").write_text("", encoding="utf-8")
            config = {"projects": {str(root / "trusted"): {"trust_level": "trusted"},
                                   str(root / "untrusted"): {"trust_level": "untrusted"},
                                   str(root / "parent"): {"trust_level": "trusted"}}}
            self.assertEqual([(root / "trusted").resolve()], UPDATE.project_directories(config))

    def test_project_runs_use_the_native_cwd_and_share_remote_revision_checks(self):
        target = UPDATE.codex_targets(codex_config())
        recorded = {}
        run = mock.Mock(return_value=True)
        with mock.patch.object(UPDATE, "project_directories", return_value=[ROOT, ROOT.parent]), \
                mock.patch.object(UPDATE, "project_targets", return_value=target), \
                mock.patch.object(UPDATE, "remote_revision", return_value=NEW) as revision, \
                mock.patch.object(UPDATE, "refresh_codex", wraps=UPDATE.refresh_codex) as refresh:
            outcomes = UPDATE.refresh_projects("codex", {}, recorded, run=run)
        revision.assert_called_once_with(CORE, "HEAD")
        self.assertEqual("updated", outcomes[str(ROOT)]["base-agents"])
        self.assertEqual("current", outcomes[str(ROOT.parent)]["base-agents"])
        self.assertTrue(all(call.kwargs.get("cwd") == ROOT for call in run.call_args_list))

    def test_a_new_selection_at_the_same_source_revision_is_installed(self):
        targets = UPDATE.codex_targets(codex_config())
        recorded = {UPDATE.target_key("base-agents", targets["base-agents"]): OLD}
        targets["base-agents"]["plugins"].append("engineering@base-agents")
        run = mock.Mock(return_value=True)
        self.assertEqual({"base-agents": "updated"}, UPDATE.refresh_codex(
            "codex", targets, recorded, revision=lambda *_: OLD, run=run))
        self.assertIn(mock.call(["codex", "plugin", "add", "engineering@base-agents"]), run.call_args_list)

    def test_missing_native_installation_is_retried_at_an_unchanged_revision(self):
        targets = UPDATE.codex_targets(codex_config())
        recorded = {UPDATE.target_key("base-agents", targets["base-agents"]): OLD}
        targets["base-agents"]["missing"] = ["base@base-agents"]
        run = mock.Mock(return_value=True)
        self.assertEqual({"base-agents": "updated"}, UPDATE.refresh_codex(
            "codex", targets, recorded, revision=lambda *_: OLD, run=run))
        self.assertTrue(run.called)

    def test_publisher_changes_refresh_an_unchanged_umbrella_marketplace(self):
        targets = UPDATE.codex_targets(codex_config())
        publisher = "https://github.com/tj-agents/python.git"
        targets["base-agents"]["publishers"] = [{"source": publisher, "ref": "main"}]
        recorded = {}
        run = mock.Mock(return_value=True)
        revision = lambda source, ref: OLD
        UPDATE.refresh_codex("codex", targets, recorded, revision=revision, run=run)
        run.reset_mock()
        self.assertEqual({"base-agents": "current"}, UPDATE.refresh_codex(
            "codex", targets, recorded, revision=revision, run=run))
        run.assert_not_called()
        revision = lambda source, ref: NEW if source == publisher else OLD
        self.assertEqual({"base-agents": "updated"}, UPDATE.refresh_codex(
            "codex", targets, recorded, revision=revision, run=run))
        self.assertTrue(run.called)

    def test_a_broken_project_does_not_prevent_another_project_from_updating(self):
        with mock.patch.object(UPDATE, "project_directories", return_value=[ROOT, ROOT.parent]), \
                mock.patch.object(UPDATE, "project_targets", side_effect=[ValueError("bad native output"), {}]), \
                mock.patch.object(UPDATE, "refresh_codex", return_value={}) as refresh:
            outcomes = UPDATE.refresh_projects("codex", {}, {})
        self.assertIn("error", outcomes[str(ROOT)])
        self.assertEqual({}, outcomes[str(ROOT.parent)])
        self.assertEqual(1, refresh.call_count)


class LockAndSelfUpdateTests(unittest.TestCase):
    def test_a_second_run_cannot_take_a_held_lock(self):
        with tempfile.TemporaryDirectory(prefix='autoupdate lock ') as temp:
            lock = Path(temp) / 'plugin-autoupdate.lock'

            self.assertTrue(UPDATE.acquire_lock(lock))
            self.assertFalse(UPDATE.acquire_lock(lock))

    def test_a_stale_lock_is_reclaimed(self):
        with tempfile.TemporaryDirectory(prefix='autoupdate lock ') as temp:
            lock = Path(temp) / 'plugin-autoupdate.lock'
            lock.write_text('', encoding='utf-8')
            old = lock.stat().st_mtime - UPDATE.LOCK_STALE_SECONDS - 60
            os.utime(lock, (old, old))

            self.assertTrue(UPDATE.acquire_lock(lock))

    def test_the_stable_copy_adopts_the_newest_packaged_script(self):
        with tempfile.TemporaryDirectory(prefix='autoupdate self ') as temp:
            stable = Path(temp) / 'bin' / UPDATE.SCRIPT_NAME
            stable.parent.mkdir()
            stable.write_text('old', encoding='utf-8')
            packaged = Path(temp) / 'package' / UPDATE.SCRIPT_NAME
            packaged.parent.mkdir()
            packaged.write_text('new', encoding='utf-8')

            with mock.patch.object(UPDATE, 'packaged_copies', return_value=[packaged]):
                self.assertTrue(UPDATE.self_update(stable, {}))
                self.assertFalse(UPDATE.self_update(stable, {}))

            self.assertEqual('new', stable.read_text(encoding='utf-8'))


    def test_only_enabled_installed_machine_packages_are_self_update_sources(self):
        with tempfile.TemporaryDirectory(prefix='plugin homes ') as temp:
            claude = Path(temp) / 'claude'
            (claude / 'plugins').mkdir(parents=True)
            current = Path(temp) / 'claude-cache' / 'tj-agents' / 'machine' / 'new'
            legacy = Path(temp) / 'claude-cache' / 'base-agents' / 'machine' / 'old'
            (claude / 'settings.json').write_text(json.dumps({'enabledPlugins': {
                'machine@tj-agents': True, 'machine@base-agents': False}}), encoding='utf-8')
            (claude / 'plugins' / 'installed_plugins.json').write_text(json.dumps({'plugins': {
                'machine@tj-agents': [{'installPath': str(current)}],
                'machine@base-agents': [{'installPath': str(legacy)}]}}), encoding='utf-8')
            codex = Path(temp) / 'codex'
            config = {'plugins': {'machine@base-agents': {'enabled': True},
                                  'machine@retired': {'enabled': False}}}

            with mock.patch.dict(os.environ, {'CODEX_HOME': str(codex)}):
                roots = UPDATE.installed_plugin_roots('machine', claude, config)

            self.assertEqual([current, codex / 'plugins' / 'cache' / 'base-agents' / 'machine' / 'local'], roots)


    def test_the_sweep_is_skipped_when_no_engineering_package_is_installed(self):
        with tempfile.TemporaryDirectory(prefix='plugin homes ') as temp:
            with mock.patch.dict(os.environ, {'CLAUDE_CONFIG_DIR': temp, 'CODEX_HOME': temp}):
                self.assertEqual('engineering package not installed', UPDATE.sweep_worktrees({}))


class SetupTests(unittest.TestCase):
    def test_claude_auto_update_is_enabled_only_for_marketplaces_of_enabled_plugins(self):
        with tempfile.TemporaryDirectory(prefix='claude config ') as temp:
            config = Path(temp)
            (config / 'plugins').mkdir()
            (config / 'settings.json').write_text(json.dumps({'enabledPlugins': {
                'base@tj-agents': True, 'old@legacy': False}}), encoding='utf-8')
            known = config / 'plugins' / 'known_marketplaces.json'
            known.write_text(json.dumps({
                'tj-agents': {'autoUpdate': False}, 'legacy': {'autoUpdate': False}}), encoding='utf-8')

            self.assertEqual(['tj-agents'], SETUP.enable_claude_autoupdate(config))
            self.assertEqual([], SETUP.enable_claude_autoupdate(config))

            saved = json.loads(known.read_text(encoding='utf-8'))
            self.assertTrue(saved['tj-agents']['autoUpdate'])
            self.assertFalse(saved['legacy']['autoUpdate'])

    def test_retired_launcher_blocks_are_removed_and_other_profile_lines_kept(self):
        with tempfile.TemporaryDirectory(prefix='profile ü ') as temp:
            profile = Path(temp) / 'Microsoft.PowerShell_profile.ps1'
            profile.write_bytes(b'\xef\xbb\xbf' + (
                "$env:Path = 'x'\r\n"
                "# >>> base-agents claude launcher >>>\r\nfunction global:claude {}\r\n"
                "# <<< base-agents claude launcher <<<\r\n"
                "# >>> base-agents codex launcher >>>\r\nfunction global:codex {}\r\n"
                "# <<< base-agents codex launcher <<<\r\n"
                ". 'accounts.ps1'\r\n").encode('utf-8'))

            self.assertEqual([profile], SETUP.remove_retired_launchers([profile]))
            self.assertEqual([], SETUP.remove_retired_launchers([profile]))

            raw = profile.read_bytes()
            self.assertTrue(raw.startswith(b'\xef\xbb\xbf'))
            self.assertEqual("$env:Path = 'x'\r\n. 'accounts.ps1'\r\n", raw[3:].decode('utf-8'))
            self.assertTrue(profile.with_name(profile.name + '.pre-autoupdate.bak').is_file())

    def test_a_missing_profile_is_skipped(self):
        with tempfile.TemporaryDirectory(prefix='profile ') as temp:
            self.assertEqual([], SETUP.remove_retired_launchers([Path(temp) / 'absent.ps1']))

    def test_cron_entries_replace_earlier_ones_and_keep_other_jobs(self):
        calls = []

        def run(command, **kwargs):
            calls.append((command, kwargs.get('input')))
            existing = f'0 5 * * * backup\n@reboot old {SETUP.CRON_MARKER}\n'
            return mock.Mock(returncode=0, stdout=existing)

        SETUP.schedule_cron(Path('/home/t/.agents-state/bin/plugin_autoupdate.py'), run=run)

        written = calls[-1][1].splitlines()
        self.assertEqual(['crontab', '-'], calls[-1][0])
        self.assertEqual('0 5 * * * backup', written[0])
        self.assertEqual(2, sum(SETUP.CRON_MARKER in line for line in written))
        self.assertTrue(any(line.startswith('@reboot ') and 'plugin_autoupdate.py' in line for line in written))
        self.assertTrue(any(line.startswith('17 * * * * ') for line in written))

    def test_windows_task_runs_hidden_at_logon_and_hourly(self):
        script = Path('C:/state dir/a.py')
        xml = SETUP.windows_task_xml('PC\\Tommy & Co', 'C:/Python/pythonw.exe', script)

        self.assertIn('<LogonTrigger>', xml)
        self.assertIn('<Interval>PT1H</Interval>', xml)
        self.assertIn('<Hidden>true</Hidden>', xml)
        self.assertIn('PC\\Tommy &amp; Co', xml)
        self.assertIn(f'-B "{script}"', xml)


if __name__ == '__main__':
    unittest.main()
