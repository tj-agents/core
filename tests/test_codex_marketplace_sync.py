"""codex_marketplace_sync.py: a faithful Python port of codex_marketplace_sync.ps1's Sync-CodexStandards,
exercised against a fake `codex` runner so no real marketplace, plugin or hook-trust call ever happens."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / '.agents/machine/scripts/codex_marketplace_sync.py'

SPEC = importlib.util.spec_from_file_location('codex_marketplace_sync', SCRIPT)
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)


def completed(argv, returncode=0, stdout='', stderr=''):
    return subprocess.CompletedProcess(argv, returncode, stdout=stdout, stderr=stderr)


class FakeCodex:
    """Records every call made to it and answers the same fixed sequence the PowerShell test's
    Invoke-FakeCodex function did, keyed off the command line rather than call order."""

    def __init__(self, fail_upgrade=False, empty_inventory=False, trust_exit=0):
        self.calls = []
        self.fail_upgrade = fail_upgrade
        self.empty_inventory = empty_inventory
        self.trust_exit = trust_exit
        self.trust_calls = []
        self.harness_permission_calls = []

    def run(self, argv, cwd=None, **kwargs):
        executable, *arguments = argv
        if executable == sys.executable:
            # apply_harness_permissions() also calls through sys.executable, in the sync's own `finally`
            # -- recorded separately so it never gets mistaken for the hook-trust call it runs alongside.
            script = next((argument for argument in arguments if argument.endswith('.py')), '')
            if script.endswith('harness_permissions_sync.py'):
                self.harness_permission_calls.append((argv, cwd))
                return completed(argv, 0, stdout='')
            self.trust_calls.append((argv, cwd))
            if self.trust_exit != 0:
                return completed(argv, self.trust_exit, stdout='', stderr='trust failed')
            return completed(argv, 0, stdout='trust tj-agents hooks\n')

        self.calls.append(' '.join(arguments))
        if arguments == ['plugin', 'marketplace', 'upgrade', '--json']:
            if self.fail_upgrade:
                return completed(argv, 1, stdout='upgrade failed')
            return completed(argv, 0, stdout=json.dumps(
                {'selectedMarketplaces': ['base-agents'], 'upgradedRoots': ['cache'], 'errors': []}
            ))
        if arguments == ['plugin', 'list', '--available', '--json']:
            if self.empty_inventory:
                return completed(argv, 0, stdout=json.dumps({'installed': [], 'available': []}))
            return completed(argv, 0, stdout=json.dumps({
                'installed': [
                    {'pluginId': 'base@base-agents', 'enabled': True, 'marketplaceSource': {'sourceType': 'git'}},
                    {'pluginId': 'local@local', 'enabled': True, 'marketplaceSource': {'sourceType': 'local'}},
                ],
                'available': [
                    {'pluginId': 'engineering@base-agents', 'enabled': True, 'marketplaceSource': {'sourceType': 'git'}},
                    {'pluginId': 'unused@base-agents', 'enabled': False, 'marketplaceSource': {'sourceType': 'git'}},
                ],
            }))
        if len(arguments) == 4 and arguments[0] == 'plugin' and arguments[1] == 'add':
            return completed(argv, 0, stdout=json.dumps({'pluginId': arguments[2]}))
        raise AssertionError(f'Unexpected fake Codex command: {arguments}')






class MainCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='codex marketplace sync cli ')
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        # A real, native-shaped (non-script) file: is_codex_shim() must open it to tell, and an
        # unreadable/nonexistent path is now treated as a shim (re-resolved), so a literal placeholder
        # path no longer stands in for "native executable, use as-is" the way it could before that fix.
        self.native_codex = self.project / 'native-codex'
        self.native_codex.write_bytes(b'\x7fELFnot a script\n')

    def test_a_successful_sync_exits_zero(self):
        import unittest.mock as mock
        with mock.patch.object(SYNC, 'sync_codex_standards', return_value=['base@base-agents']) as synced:
            code = SYNC.main(['--codex', str(self.native_codex), '--project', str(self.project)])
        self.assertEqual(code, 0)
        synced.assert_called_once()
        self.assertEqual(synced.call_args.args[0], str(self.native_codex))

    def test_a_sync_error_is_reported_and_exits_nonzero(self):
        import io
        import contextlib
        import unittest.mock as mock
        with mock.patch.object(SYNC, 'sync_codex_standards', side_effect=SYNC.SyncError('boom')):
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                code = SYNC.main(['--codex', str(self.native_codex), '--project', str(self.project)])
        self.assertEqual(code, 1)
        self.assertIn('boom', err.getvalue())

    def test_omitting_codex_resolves_the_native_executable_via_agent_cli(self):
        fake_agent_cli = mock.Mock()
        fake_agent_cli.resolve_codex_executable.return_value = ('/native/codex', {'text': '0.160.0'})
        fake_agent_cli.LaunchError = SYNC.SyncError  # any distinct exception type works here
        with mock.patch.object(SYNC, '_load_agent_cli', return_value=fake_agent_cli), \
                mock.patch.object(SYNC, 'sync_codex_standards', return_value=[]) as synced:
            code = SYNC.main(['--project', str(self.project)])
        self.assertEqual(code, 0)
        fake_agent_cli.resolve_codex_executable.assert_called_once()
        self.assertEqual(synced.call_args.args[0], '/native/codex')

    def test_a_shim_shaped_codex_value_is_also_resolved_via_agent_cli(self):
        fake_agent_cli = mock.Mock()
        fake_agent_cli.resolve_codex_executable.return_value = ('/native/codex', {'text': '0.160.0'})
        fake_agent_cli.LaunchError = SYNC.SyncError
        with mock.patch.object(SYNC, '_load_agent_cli', return_value=fake_agent_cli), \
                mock.patch.object(SYNC, 'sync_codex_standards', return_value=[]) as synced:
            code = SYNC.main(['--codex', 'C:\\npm\\codex.cmd', '--project', str(self.project)])
        self.assertEqual(code, 0)
        fake_agent_cli.resolve_codex_executable.assert_called_once()
        self.assertEqual(synced.call_args.args[0], '/native/codex')

    def test_a_failure_to_resolve_codex_is_reported_and_exits_nonzero(self):
        class FakeLaunchError(Exception):
            pass

        fake_agent_cli = mock.Mock()
        fake_agent_cli.LaunchError = FakeLaunchError
        fake_agent_cli.resolve_codex_executable.side_effect = FakeLaunchError('no native codex found')
        with mock.patch.object(SYNC, '_load_agent_cli', return_value=fake_agent_cli):
            import io
            import contextlib
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                code = SYNC.main(['--project', str(self.project)])
        self.assertEqual(code, 1)
        self.assertIn('no native codex found', err.getvalue())


class IsCodexShimTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='codex shim detection ')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def test_a_ps1_suffix_is_a_shim(self):
        self.assertTrue(SYNC.is_codex_shim('C:\\tools\\codex.ps1'))

    def test_a_cmd_suffix_is_a_shim(self):
        self.assertTrue(SYNC.is_codex_shim('C:\\tools\\codex.cmd'))

    def test_a_posix_hashbang_script_is_a_shim(self):
        script = self.base / 'codex'
        script.write_text('#!/usr/bin/env node\n')
        self.assertTrue(SYNC.is_codex_shim(str(script)))

    def test_a_native_binary_is_not_a_shim(self):
        binary = self.base / 'codex'
        binary.write_bytes(b'\x7fELFnot a script\n')
        self.assertFalse(SYNC.is_codex_shim(str(binary)))

    def test_an_unreadable_path_is_treated_as_a_shim_so_it_gets_re_resolved(self):
        # Matches agent_cli._is_script's own fail-safe direction (True on OSError): an unreadable path
        # cannot be confirmed native, so main() re-resolves it via agent_cli.resolve_codex_executable()
        # rather than silently trusting it as-is.
        self.assertTrue(SYNC.is_codex_shim(str(self.base / 'missing')))




class EffectiveCodexSelectionTests(unittest.TestCase):
    def test_effective_config_includes_selected_missing_and_explicitly_disabled_plugins(self):
        response = {
            'config': {
                'marketplaces': {'fixture': {'source_type': 'git', 'source': 'https://github.com/tj-agents/core.git'}},
                'plugins': {'missing@fixture': {'enabled': True}, 'disabled@fixture': {'enabled': False}},
            },
        }

        class Server:
            def __init__(self, *_arguments, **_kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *_arguments):
                return None

            def request(self, method, params):
                self.method, self.params = method, params
                return response

        with mock.patch.object(SYNC, 'AppServer', Server):
            selection = SYNC.codex_config_selection('codex', Path.cwd())

        self.assertEqual(selection['selections'], [{
            'identity': 'missing@fixture', 'marketplace': 'fixture',
            'source_url': 'https://github.com/tj-agents/core.git',
        }])
        self.assertEqual(selection['disabled'], ['disabled@fixture'])

    def test_legacy_profile_option_is_rejected_before_reading_native_config(self):
        with self.assertRaisesRegex(SYNC.SyncError, 'profiles are unsupported'):
            SYNC.codex_config_selection('codex', Path.cwd(), ['-p', 'legacy'])

    def test_selected_tj_agents_plugin_without_a_git_marketplace_source_fails_closed(self):
        response = {'config': {'marketplaces': {}, 'plugins': {'base@base-agents': {'enabled': True}}}}

        class Server:
            def __init__(self, *_arguments, **_kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *_arguments):
                return None

            def request(self, method, params):
                return response

        with mock.patch.object(SYNC, 'AppServer', Server), \
                self.assertRaisesRegex(SYNC.SyncError, 'no authenticated Git source'):
            SYNC.codex_config_selection('codex', Path.cwd())

if __name__ == '__main__':
    unittest.main()
