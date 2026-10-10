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
            script = arguments[1] if len(arguments) > 1 else ''
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


class SyncCodexStandardsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='codex marketplace sync ')
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        self.lines = []

    def out(self, line):
        self.lines.append(line)

    def test_a_full_sync_refreshes_every_enabled_git_plugin_then_trusts_hooks_in_order(self):
        fake = FakeCodex()
        selected = SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=fake.run)

        self.assertEqual(selected, ['base@base-agents', 'engineering@base-agents'])
        self.assertEqual(fake.calls, [
            'plugin marketplace upgrade --json',
            'plugin list --available --json',
            'plugin add base@base-agents --json',
            'plugin add engineering@base-agents --json',
        ])
        self.assertEqual(len(fake.trust_calls), 1)
        self.assertEqual(self.lines, ['trust tj-agents hooks'])

    def test_the_hook_trust_call_uses_the_current_interpreter_and_the_working_directory(self):
        fake = FakeCodex()
        SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=fake.run)
        (argv, cwd) = fake.trust_calls[0]
        self.assertEqual(argv[0], sys.executable)
        self.assertEqual(argv[1], '-B')
        self.assertEqual(argv[3:], ['--codex', 'Invoke-FakeCodex', '--project', str(self.project.resolve())])
        self.assertEqual(cwd, self.project.resolve())

    def test_the_hook_trust_helpers_stderr_reaches_the_user(self):
        def run(argv, cwd=None, **kwargs):
            if argv[0] == sys.executable:
                return completed(argv, 0, stdout='trust tj-agents hooks\n', stderr='warning: slow disk\n')
            arguments = argv[1:]
            if arguments == ['plugin', 'marketplace', 'upgrade', '--json']:
                return completed(argv, 0, stdout=json.dumps({'errors': []}))
            if arguments == ['plugin', 'list', '--available', '--json']:
                return completed(argv, 0, stdout=json.dumps({
                    'installed': [{'pluginId': 'base@base-agents', 'enabled': True,
                                   'marketplaceSource': {'sourceType': 'git'}}],
                    'available': [],
                }))
            return completed(argv, 0, stdout=json.dumps({'pluginId': arguments[2]}))

        SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=run)
        self.assertIn('warning: slow disk', self.lines)

    def test_the_hook_trust_helper_snapshot_is_a_real_file_distinct_from_the_shipped_copy(self):
        fake = FakeCodex()
        SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=fake.run)
        (argv, _cwd) = fake.trust_calls[0]
        snapshot = Path(argv[2])
        self.assertNotEqual(snapshot, ROOT / '.agents/machine/scripts/codex_hook_trust.py')
        # The snapshot lived in a temporary directory that is cleaned up once the sync returns.
        self.assertFalse(snapshot.exists())

    def test_an_empty_plugin_inventory_never_invokes_hook_trust(self):
        fake = FakeCodex(empty_inventory=True)
        selected = SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=fake.run)

        self.assertEqual(selected, [])
        self.assertEqual(fake.calls, ['plugin marketplace upgrade --json', 'plugin list --available --json'])
        self.assertEqual(fake.trust_calls, [])

    def test_a_failed_marketplace_upgrade_blocks_the_rest_of_the_sync(self):
        fake = FakeCodex(fail_upgrade=True)
        with self.assertRaises(SYNC.SyncError) as raised:
            SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=fake.run)

        self.assertIn('upgrade failed', str(raised.exception))
        self.assertEqual(fake.calls, ['plugin marketplace upgrade --json'])
        self.assertEqual(fake.trust_calls, [])

    def test_a_marketplace_upgrade_that_reports_errors_in_its_json_also_blocks_the_sync(self):
        def run(argv, cwd=None, **kwargs):
            if argv[1:] == ['plugin', 'marketplace', 'upgrade', '--json']:
                return completed(argv, 0, stdout=json.dumps({'errors': ['offline']}))
            raise AssertionError('No call beyond the upgrade should happen')

        with self.assertRaises(SYNC.SyncError) as raised:
            SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=run)
        self.assertIn('upgrade failed', str(raised.exception))

    def test_a_mismatched_plugin_add_response_is_a_sync_error(self):
        def run(argv, cwd=None, **kwargs):
            arguments = argv[1:]
            if arguments == ['plugin', 'marketplace', 'upgrade', '--json']:
                return completed(argv, 0, stdout=json.dumps({'errors': []}))
            if arguments == ['plugin', 'list', '--available', '--json']:
                return completed(argv, 0, stdout=json.dumps({
                    'installed': [{'pluginId': 'base@base-agents', 'enabled': True,
                                   'marketplaceSource': {'sourceType': 'git'}}],
                    'available': [],
                }))
            if arguments[:2] == ['plugin', 'add']:
                return completed(argv, 0, stdout=json.dumps({'pluginId': 'wrong@base-agents'}))
            raise AssertionError(arguments)

        with self.assertRaises(SYNC.SyncError) as raised:
            SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=run)
        self.assertIn('wrong@base-agents', str(raised.exception))
        self.assertIn('base@base-agents', str(raised.exception))

    def test_invalid_json_from_a_sync_command_is_a_sync_error(self):
        def run(argv, cwd=None, **kwargs):
            return completed(argv, 0, stdout='not json')

        with self.assertRaises(SYNC.SyncError) as raised:
            SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=run)
        self.assertIn('invalid JSON', str(raised.exception))

    def test_a_non_object_json_value_from_a_sync_command_is_a_sync_error(self):
        # A future/older Codex build answering with a bare array or scalar must not reach .get() and
        # raise AttributeError; sync_codex_standards only ever calls .get() on this return value.
        def run(argv, cwd=None, **kwargs):
            return completed(argv, 0, stdout='[]')

        with self.assertRaises(SYNC.SyncError) as raised:
            SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=run)
        self.assertIn('non-object JSON', str(raised.exception))

    def test_a_stderr_warning_beside_valid_stdout_json_is_not_a_parse_error(self):
        # Only stdout is parsed as JSON; stderr is for an error message only, never mixed into the parse.
        def run(argv, cwd=None, **kwargs):
            if argv[1:] == ['plugin', 'marketplace', 'upgrade', '--json']:
                return completed(argv, 0, stdout=json.dumps({'errors': []}), stderr='warning: slow network')
            if argv[1:] == ['plugin', 'list', '--available', '--json']:
                return completed(argv, 0, stdout=json.dumps({'installed': [], 'available': []}),
                                  stderr='warning: slow network')
            raise AssertionError(argv)

        selected = SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=run)
        self.assertEqual(selected, [])

    def test_null_and_pluginid_less_entries_are_skipped_not_raised(self):
        def run(argv, cwd=None, **kwargs):
            if argv[0] == sys.executable:
                return completed(argv, 0, stdout='trust tj-agents hooks\n')
            arguments = argv[1:]
            if arguments == ['plugin', 'marketplace', 'upgrade', '--json']:
                return completed(argv, 0, stdout=json.dumps({'errors': []}))
            if arguments == ['plugin', 'list', '--available', '--json']:
                return completed(argv, 0, stdout=json.dumps({
                    'installed': [
                        None,
                        'not a dict',
                        {'enabled': True, 'marketplaceSource': {'sourceType': 'git'}},  # no pluginId
                        {'pluginId': 'base@base-agents', 'enabled': True, 'marketplaceSource': {'sourceType': 'git'}},
                    ],
                    'available': [None, {'pluginId': '', 'enabled': True, 'marketplaceSource': {'sourceType': 'git'}}],
                }))
            if arguments[:2] == ['plugin', 'add']:
                return completed(argv, 0, stdout=json.dumps({'pluginId': arguments[2]}))
            raise AssertionError(arguments)

        selected = SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=run)
        self.assertEqual(selected, ['base@base-agents'])

    def test_marketplace_upgrade_uses_the_180_second_timeout(self):
        seen = {}

        def run(argv, cwd=None, timeout=None, **kwargs):
            if argv[1:] == ['plugin', 'marketplace', 'upgrade', '--json']:
                seen['timeout'] = timeout
                return completed(argv, 0, stdout=json.dumps({'errors': []}))
            return completed(argv, 0, stdout=json.dumps({'installed': [], 'available': []}))

        SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=run)
        self.assertEqual(seen['timeout'], SYNC.MARKETPLACE_TIMEOUT_SECONDS)
        self.assertEqual(SYNC.MARKETPLACE_TIMEOUT_SECONDS, 180)

    def test_other_plugin_calls_use_the_120_second_timeout(self):
        seen = []

        def run(argv, cwd=None, timeout=None, **kwargs):
            if argv[0] == sys.executable:
                return completed(argv, 0, stdout='trust tj-agents hooks\n')
            arguments = argv[1:]
            if arguments == ['plugin', 'marketplace', 'upgrade', '--json']:
                return completed(argv, 0, stdout=json.dumps({'errors': []}))
            seen.append(timeout)
            if arguments == ['plugin', 'list', '--available', '--json']:
                return completed(argv, 0, stdout=json.dumps({
                    'installed': [{'pluginId': 'base@base-agents', 'enabled': True,
                                   'marketplaceSource': {'sourceType': 'git'}}],
                    'available': [],
                }))
            return completed(argv, 0, stdout=json.dumps({'pluginId': 'base@base-agents'}))

        SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=run)
        self.assertEqual(seen, [SYNC.PLUGIN_TIMEOUT_SECONDS, SYNC.PLUGIN_TIMEOUT_SECONDS])
        self.assertEqual(SYNC.PLUGIN_TIMEOUT_SECONDS, 120)

    def test_a_timeout_is_a_sync_error_naming_the_step(self):
        def run(argv, cwd=None, timeout=None, **kwargs):
            raise SYNC.subprocess.TimeoutExpired(argv, timeout)

        with self.assertRaises(SYNC.SyncError) as raised:
            SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=run)
        self.assertIn('timed out', str(raised.exception))
        self.assertIn('plugin marketplace upgrade --json', str(raised.exception))

    def test_a_failure_to_start_a_plugin_call_is_a_sync_error_not_a_raw_traceback(self):
        def run(argv, cwd=None, **kwargs):
            raise FileNotFoundError('no such file or directory')

        with self.assertRaises(SYNC.SyncError) as raised:
            SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=run)
        self.assertIn('plugin marketplace upgrade --json', str(raised.exception))

    def test_a_hook_trust_timeout_is_a_sync_error(self):
        fake = FakeCodex()

        def run(argv, cwd=None, timeout=None, **kwargs):
            if argv[0] == sys.executable:
                raise SYNC.subprocess.TimeoutExpired(argv, timeout)
            return fake.run(argv, cwd=cwd, **kwargs)

        with self.assertRaises(SYNC.SyncError) as raised:
            SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=run)
        self.assertIn('timed out', str(raised.exception))

    def test_a_failure_to_start_hook_trust_is_a_sync_error_not_a_raw_traceback(self):
        fake = FakeCodex()

        def run(argv, cwd=None, **kwargs):
            if argv[0] == sys.executable:
                raise OSError('no such file or directory')
            return fake.run(argv, cwd=cwd, **kwargs)

        with self.assertRaises(SYNC.SyncError):
            SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=run)

    def test_harness_permissions_converge_once_on_a_successful_sync(self):
        fake = FakeCodex()
        SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=fake.run)

        self.assertEqual(len(fake.harness_permission_calls), 1)
        argv, _cwd = fake.harness_permission_calls[0]
        self.assertEqual(argv[0], sys.executable)
        self.assertEqual(argv[1], '-B')
        self.assertTrue(argv[2].endswith('harness_permissions_sync.py'))
        self.assertEqual(argv[3], '--apply')

    def test_harness_permissions_still_converge_after_a_sync_error(self):
        # The ps1 original ran this from a `finally`, so a raised SyncError must not skip it.
        fake = FakeCodex(fail_upgrade=True)
        with self.assertRaises(SYNC.SyncError):
            SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=fake.run)
        self.assertEqual(len(fake.harness_permission_calls), 1)

    def test_a_harness_permissions_failure_never_becomes_a_sync_error(self):
        fake = FakeCodex()

        def failing_run(argv, cwd=None, **kwargs):
            executable, *arguments = argv
            script = arguments[1] if executable == sys.executable and len(arguments) > 1 else ''
            if script.endswith('harness_permissions_sync.py'):
                raise OSError('no python on this machine')
            return fake.run(argv, cwd=cwd, **kwargs)

        selected = SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=failing_run)
        self.assertEqual(selected, ['base@base-agents', 'engineering@base-agents'])

    def test_a_failing_hook_trust_call_is_a_sync_error(self):
        fake = FakeCodex(trust_exit=1)
        with self.assertRaises(SYNC.SyncError) as raised:
            SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=fake.run)
        self.assertIn('could not trust', str(raised.exception))

    def test_a_missing_hook_trust_helper_is_a_sync_error_before_any_codex_call(self):
        fake = FakeCodex()
        with mock.patch.object(SYNC.Path, 'is_file', return_value=False):
            with self.assertRaises(SYNC.SyncError) as raised:
                SYNC.sync_codex_standards('Invoke-FakeCodex', self.project, out=self.out, run=fake.run)
        self.assertIn('helper missing', str(raised.exception))
        self.assertEqual(fake.calls, [])


class ApplyHarnessPermissionsTests(unittest.TestCase):
    """apply_harness_permissions() in isolation: the fire-and-forget contract shared with
    claude_standards_sync.py's own version of this function."""

    def test_does_nothing_when_the_shared_script_is_missing(self):
        calls = []
        with mock.patch.object(SYNC.Path, 'is_file', return_value=False):
            SYNC.apply_harness_permissions(run=lambda *a, **k: calls.append((a, k)))
        self.assertEqual(calls, [])

    def test_runs_the_real_shared_script_path_with_apply(self):
        calls = []
        SYNC.apply_harness_permissions(run=lambda *a, **k: calls.append((a, k)))
        self.assertEqual(len(calls), 1)
        (argv,), kwargs = calls[0]
        self.assertEqual(argv[0], sys.executable)
        self.assertEqual(argv[1], '-B')
        self.assertTrue(argv[2].endswith('harness_permissions_sync.py'))
        self.assertEqual(argv[3], '--apply')
        self.assertEqual(kwargs.get('stdin'), SYNC.subprocess.DEVNULL)
        self.assertEqual(kwargs.get('timeout'), 30)

    def test_an_exception_from_run_is_swallowed(self):
        def failing_run(*_args, **_kwargs):
            raise OSError('no python on this machine')

        SYNC.apply_harness_permissions(run=failing_run)  # must not raise


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


if __name__ == '__main__':
    unittest.main()
