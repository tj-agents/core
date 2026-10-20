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
        recorded = {'codex:base-agents': OLD}

        outcomes = UPDATE.refresh_codex('codex', UPDATE.codex_targets(codex_config()), recorded,
                                        revision=lambda source, ref: OLD, run=run)

        self.assertEqual({'base-agents': 'current'}, outcomes)
        run.assert_not_called()

    def test_a_changed_revision_upgrades_then_re_adds_each_enabled_plugin(self):
        run = mock.Mock(return_value=True)
        recorded = {'codex:base-agents': OLD}

        outcomes = UPDATE.refresh_codex('codex', UPDATE.codex_targets(codex_config()), recorded,
                                        revision=lambda source, ref: NEW, run=run)

        self.assertEqual({'base-agents': 'updated'}, outcomes)
        self.assertEqual(NEW, recorded['codex:base-agents'])
        self.assertEqual([
            mock.call(['codex', 'plugin', 'marketplace', 'upgrade', 'base-agents']),
            mock.call(['codex', 'plugin', 'add', 'base@base-agents']),
            mock.call(['codex', 'plugin', 'add', 'machine@base-agents']),
        ], run.call_args_list)

    def test_a_failed_refresh_keeps_the_old_revision_so_the_next_run_retries(self):
        recorded = {'codex:base-agents': OLD}

        outcomes = UPDATE.refresh_codex('codex', UPDATE.codex_targets(codex_config()), recorded,
                                        revision=lambda source, ref: NEW, run=lambda command: False)

        self.assertEqual({'base-agents': 'failed'}, outcomes)
        self.assertEqual(OLD, recorded['codex:base-agents'])

    def test_an_unreachable_source_changes_nothing(self):
        run = mock.Mock(return_value=True)

        outcomes = UPDATE.refresh_codex('codex', UPDATE.codex_targets(codex_config()), {},
                                        revision=lambda source, ref: None, run=run)

        self.assertEqual({'base-agents': 'unreachable'}, outcomes)
        run.assert_not_called()


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


    def test_every_child_process_starts_without_a_console_window(self):
        source = (SCRIPTS / 'plugin_autoupdate.py').read_text(encoding='utf-8')
        launches = source.count('subprocess.run(') + source.count('subprocess.Popen(')

        self.assertEqual(launches, source.count('creationflags=NO_WINDOW'))
        if os.name == 'nt':
            self.assertEqual(UPDATE.subprocess.CREATE_NO_WINDOW, UPDATE.NO_WINDOW)

    def test_the_sweep_runs_under_a_console_interpreter_when_scheduled_windowless(self):
        with tempfile.TemporaryDirectory(prefix='python dir ') as temp:
            pythonw = Path(temp) / 'pythonw.exe'
            console = Path(temp) / 'python.exe'
            pythonw.write_text('', encoding='utf-8')
            console.write_text('', encoding='utf-8')

            with mock.patch.object(UPDATE.sys, 'executable', str(pythonw)):
                self.assertEqual(str(console), UPDATE.console_python())


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
