import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / '.agents/machine/utility/close/scripts/close_session.py'
SPEC = importlib.util.spec_from_file_location('machine_close_bridge', SCRIPT)
close = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(close)
LANDED_SPEC = importlib.util.spec_from_file_location('machine_close_landed', SCRIPT.with_name('close_landed.py'))
landed = importlib.util.module_from_spec(LANDED_SPEC)
with mock.patch.dict(sys.modules, {'close_session': close}):
    LANDED_SPEC.loader.exec_module(landed)


class MachineCloseBridgeTests(unittest.TestCase):
    def setUp(self):
        self.entry = {'host': 'codex', 'session_id': 'own', 'pid': 123, 'pid_started_at': 100.5,
                      'cwd': str(Path.cwd()), 'started_at': 100}
        self.shared = mock.Mock()
        self.shared.Refusal = RuntimeError
        self.shared.own_host_and_entry.return_value = self.entry
        self.store = self.shared.register_session._load_session_store.return_value
        self.store.get_session.return_value = {'ended_at': None, 'turn_state': 'working'}

    def test_arm_requires_the_exact_frontend_before_starting_a_watcher(self):
        self.shared.close_target.side_effect = RuntimeError('exact frontend binding required')
        with mock.patch.object(close, 'runtime', return_value=self.shared), \
                mock.patch.object(close, 'cli_runtime') as cli:
            with self.assertRaisesRegex(RuntimeError, 'exact frontend binding required'):
                close.arm()
        cli.assert_not_called()
        self.shared.own_host_and_entry.assert_called_once_with(session_id=None)

    def test_arm_delegates_to_the_shared_cli_watcher_with_closeout_cleanup(self):
        cli = mock.Mock()
        cli.start_watcher.return_value = {'status': 'armed'}
        with mock.patch.object(close, 'runtime', return_value=self.shared), \
                mock.patch.object(close, 'cli_runtime', return_value=cli), \
                mock.patch.object(close, 'primary_checkout', return_value=Path('repo')), \
                mock.patch.object(close, 'sweep_script', return_value=Path('sweep.py')):
            self.assertEqual({'status': 'armed'}, close.arm())
        self.assertEqual((Path('repo'), Path('sweep.py')),
                         cli.start_watcher.call_args.args[3])
        self.shared.close_target.assert_called_once_with(self.entry)

    def test_landed_hook_binds_the_payload_session_id(self):
        payload = json.dumps({'cwd': str(ROOT), 'session_id': 'own'})
        with mock.patch.object(landed, 'merged_at', return_value=200.0), \
                mock.patch.object(landed.close_session, 'arm_after_stop') as arm, \
                mock.patch.object(sys, 'stdin', io.StringIO(payload)):
            self.assertEqual(0, landed.main())
        arm.assert_called_once_with(200.0, 'own')

    def test_source_and_machine_package_find_the_canonical_cli_runtime(self):
        self.assertTrue(close.cli_runtime().start_watcher)
        for tree in ('skills', 'codex-skills'):
            packaged = ROOT / f'plugins/machine/{tree}/close/scripts/close_session.py'
            with mock.patch.object(close, '__file__', str(packaged)):
                self.assertTrue(close.cli_runtime().start_watcher)


if __name__ == '__main__':
    unittest.main()
