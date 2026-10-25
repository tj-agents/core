import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / '.agents/machine/utility/close/scripts/close_session.py'
SPEC = importlib.util.spec_from_file_location('machine_close_bridge', SCRIPT)
close = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(close)


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
        cli = mock.Mock()
        cli.own_session.side_effect = RuntimeError('exact frontend binding required')
        with mock.patch.object(close, 'runtime', return_value=self.shared), \
                mock.patch.object(close, 'cli_runtime', return_value=cli):
            with self.assertRaisesRegex(RuntimeError, 'exact frontend binding required'):
                close.arm()
        cli.start_watcher.assert_not_called()
        cli.own_session.assert_called_once_with(self.shared, None)

    def test_arm_delegates_to_the_shared_cli_watcher_with_closeout_cleanup(self):
        cli = mock.Mock()
        cli.own_session.return_value = (self.entry, {'turn_state': 'working'})
        cli.start_watcher.return_value = {'status': 'armed'}
        with mock.patch.object(close, 'runtime', return_value=self.shared), \
                mock.patch.object(close, 'cli_runtime', return_value=cli), \
                mock.patch.object(close, 'primary_checkout', return_value=Path('repo')), \
                mock.patch.object(close, 'sweep_script', return_value=Path('sweep.py')):
            self.assertEqual({'status': 'armed'}, close.arm())
        self.assertEqual((Path('repo'), Path('sweep.py')),
                         cli.start_watcher.call_args.args[3])
        cli.own_session.assert_called_once_with(self.shared, None)

    def test_source_and_machine_package_find_the_canonical_cli_runtime(self):
        self.assertTrue(close.cli_runtime().start_watcher)
        for tree in ('skills', 'codex-skills'):
            packaged = ROOT / f'plugins/machine/{tree}/close/scripts/close_session.py'
            with mock.patch.object(close, '__file__', str(packaged)):
                self.assertTrue(close.cli_runtime().start_watcher)


if __name__ == '__main__':
    unittest.main()
