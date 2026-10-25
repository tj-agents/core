"""Native completion closes a frozen frontend even when Stop hooks are stale."""

import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.agents/machine/scripts'))
sys.path.insert(0, str(ROOT / '.agents/machine/utility/peer-cli/scripts'))
import cli_client
import session_close

SCRIPT = ROOT / '.agents/cli/utility/close/scripts/close_watcher.py'
SPEC = importlib.util.spec_from_file_location('native_close_watcher', SCRIPT)
watcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(watcher)


class NativeCompletionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='native close é ')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        environment = mock.patch.dict(os.environ, {'AGENT_STATE_DIRECTORY': str(self.root / 'state')})
        environment.start()
        self.addCleanup(environment.stop)
        self.rollout = self.root / 'sessions/rollout.jsonl'
        self.rollout.parent.mkdir()
        self.recording = self.root / 'events.jsonl'
        self.recording.write_text(json.dumps({'dir': 'meta', 'kind': 'session_start'}) + '\n' + json.dumps({
            'dir': 'from_tui', 'kind': 'op', 'payload': {'UserTurn': {'client_user_message_id': 'input'}}}) + '\n',
            encoding='utf-8')
        self.entry = {'host': 'codex', 'session_id': 'thread', 'pid': 123, 'pid_started_at': 50.0,
                      'client_identity': 'managed-input', 'client_message_id': 'input', 'native_turn_id': 'turn',
                      'native_rollout': str(self.rollout), 'profile': str(self.root),
                      'recording_path': str(self.recording)}
        self.append({'type': 'session_meta', 'payload': {'id': 'thread', 'source': 'cli'}})
        self.event('task_started')
        self.event('item_completed', item={'type': 'UserMessage', 'client_id': 'input'})
        self.args = watcher.arguments(['--host', 'codex', '--session-id', 'thread', '--pid', '123',
                                       '--pid-started-at', '50', '--armed-at', '100', '--timeout', '20'])
        self.now = 100.0

    def append(self, row):
        with self.rollout.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row) + '\n')

    def event(self, kind, turn='turn', **extra):
        self.append({'type': 'event_msg', 'payload': {'type': kind, 'turn_id': turn, **extra}})

    def arm(self):
        guard = cli_client.NativeCompletion(self.entry)
        guard.poll()
        session_close.write_json(watcher.armed_path('thread'), {
            'armed_at': 100.0, 'entry': self.entry, 'rollout': guard.pin()})

    def clock(self):
        return self.now

    def wait(self, on_sleep=None):
        def sleep(seconds):
            self.now += seconds
            if on_sleep:
                on_sleep()
        with mock.patch.object(session_close, 'verified_live', return_value=True), \
                mock.patch.object(session_close, 'client_runtime', return_value=cli_client), \
                mock.patch.object(watcher, 'session_row', side_effect=AssertionError('stale hook store read')):
            return watcher.wait_for_idle(self.args, clock=self.clock, sleep=sleep)

    def test_actual_native_completion_drives_wait_and_signal_without_stop_store(self):
        self.arm()
        def completion():
            if self.now == 101.0:
                self.event('task_complete')
        guard = self.wait(completion)
        self.assertIsNotNone(guard)
        self.assertGreaterEqual(self.now, 104.0)
        with mock.patch.object(watcher, 'registered_entry', return_value=self.entry), \
                mock.patch.object(session_close, 'awaiting_input_activity', side_effect=AssertionError('hook state')), \
                mock.patch.object(watcher.close, 'close_host', side_effect=lambda entry, check: check()), \
                mock.patch.object(session_close, 'verified_exited', return_value=True), \
                mock.patch.object(session_close, '_record_own_end') as ended:
            watcher.close_session(self.args, guard)
            ended.assert_called_once_with(self.entry, 'closed')

    def test_completion_before_watcher_start_is_not_lost(self):
        self.arm()
        self.event('task_complete')
        self.assertIsNotNone(self.wait())
        self.assertEqual(103.0, self.now)

    def test_managed_remote_tui_native_source_is_supported(self):
        self.rollout.write_bytes(self.rollout.read_bytes().replace(b'"cli"', b'"vscode"'))
        self.arm()
        self.event('task_complete')
        self.assertIsNotNone(self.wait())

    def test_new_native_turn_inside_retained_signal_callback_refuses(self):
        self.arm()
        self.event('task_complete')
        guard = self.wait()
        def stop(entry, before_signal):
            self.event('task_started', turn='next')
            before_signal()
            self.fail('New input must prevent the retained handle from being signalled')
        with mock.patch.object(watcher, 'registered_entry', return_value=self.entry), \
                mock.patch.object(watcher.close, 'close_host', side_effect=stop):
            with self.assertRaisesRegex(RuntimeError, 'new native turn'):
                watcher.close_session(self.args, guard)

    def test_no_completion_never_closes(self):
        self.arm()
        self.assertIsNone(self.wait())

    def test_new_turn_and_peer_steering_cancel_even_before_watcher_start(self):
        for kind, extra in (('task_started', {'turn': 'new'}), ('turn_aborted', {}),
                            ('item_completed', {'item': {'type': 'UserMessage', 'client_id': 'peer'}})):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                saved = self.rollout.read_bytes()
                self.arm()
                self.event('task_complete')
                self.event(kind, **extra)
                with self.assertRaises(RuntimeError):
                    self.wait()
                self.rollout.write_bytes(saved)

    def test_new_input_at_signal_boundary_refuses(self):
        self.arm()
        self.event('task_complete')
        guard = self.wait()
        with self.recording.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'dir': 'to_tui', 'variant': 'OpenResumePicker'}) + '\n')
        with mock.patch.object(watcher, 'registered_entry', return_value=self.entry), \
                mock.patch.object(watcher.close, 'close_host') as signal:
            with self.assertRaisesRegex(RuntimeError, 'input changed'):
                watcher.close_session(self.args, guard)
            signal.assert_not_called()

    def test_changed_registration_at_signal_boundary_refuses(self):
        self.arm()
        self.event('task_complete')
        guard = self.wait()
        with mock.patch.object(watcher, 'registered_entry', return_value={**self.entry, 'client_message_id': 'new'}):
            with self.assertRaisesRegex(RuntimeError, 'binding changed'):
                watcher.close_session(self.args, guard)

    def test_replaced_truncated_foreign_or_unattributed_rollout_refuses(self):
        self.arm()
        original = self.rollout.read_bytes()
        self.rollout.unlink()
        self.rollout.write_bytes(original)
        with self.assertRaisesRegex(RuntimeError, 'replaced or truncated'):
            self.wait()
        self.arm()
        self.rollout.write_text('', encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError, 'replaced or truncated'):
            self.wait()
        for change in ('foreign', 'unattributed'):
            self.rollout.write_bytes(original.replace(b'"thread"', b'"other"') if change == 'foreign'
                                     else original.replace(b'"client_id": "input"', b'"client_id": null'))
            with self.assertRaises(RuntimeError):
                self.arm()

    def test_partial_appended_record_defers_closure_until_complete(self):
        self.arm()
        self.event('task_complete')
        with self.rollout.open('ab') as stream:
            stream.write(b'{')
        self.assertIsNone(self.wait())

    def test_missing_arm_binding_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, 'binding is missing'):
            self.wait()


if __name__ == '__main__':
    unittest.main()
