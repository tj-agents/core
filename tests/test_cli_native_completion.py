"""Native completion closes a frozen frontend even when Stop hooks are stale."""

import importlib.util
import json
import os
from pathlib import Path, PureWindowsPath
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

    def test_mutating_an_exported_pin_cannot_change_the_bound_file_identity(self):
        guard = cli_client.NativeCompletion(self.entry)
        pin = guard.pin()
        pin['identity'][1] += 1
        self.event('task_complete')
        self.assertTrue(guard.poll())
        with self.assertRaisesRegex(RuntimeError, 'replaced or truncated'):
            cli_client.NativeCompletion(self.entry, pin)

    def test_truncation_between_path_check_and_open_cannot_reuse_completion(self):
        guard = cli_client.NativeCompletion(self.entry)
        self.event('task_complete')
        self.assertTrue(guard.poll())
        original_open = Path.open

        def truncate_before_open(path, *args, **kwargs):
            if path == self.rollout and args and args[0] == 'rb':
                with original_open(path, 'wb'):
                    pass
            return original_open(path, *args, **kwargs)

        with mock.patch.object(Path, 'open', new=truncate_before_open):
            with self.assertRaisesRegex(RuntimeError, 'replaced or truncated'):
                guard.poll()

    @unittest.skipUnless(os.name == 'nt', 'Win32 extended paths require Windows')
    def test_equivalent_extended_profile_and_rollout_paths_keep_the_exact_binding(self):
        self.event('task_complete')
        original = dict(self.entry)
        for profile_extended, rollout_extended in ((False, True), (True, False), (True, True)):
            with self.subTest(profile_extended=profile_extended, rollout_extended=rollout_extended):
                self.entry = dict(original)
                for key, extended in (('profile', profile_extended), ('native_rollout', rollout_extended)):
                    if extended:
                        self.entry[key] = '\\\\?\\' + self.entry[key]
                frozen = dict(self.entry)
                self.assertTrue(os.path.samefile(self.entry['native_rollout'], self.rollout))
                self.arm()
                self.assertIsNotNone(self.wait())
                self.assertEqual(frozen, self.entry)

    def test_valid_transcript_outside_the_profile_cannot_authorize_closure(self):
        with tempfile.TemporaryDirectory() as outside:
            foreign = Path(outside).resolve() / 'rollout.jsonl'
            foreign.write_bytes(self.rollout.read_bytes())
            variants = [str(foreign)]
            if os.name == 'nt':
                variants.append('\\\\?\\' + str(foreign))
            for path in variants:
                with self.subTest(path=path), self.assertRaisesRegex(RuntimeError, 'outside the verified profile'):
                    cli_client.NativeCompletion({**self.entry, 'native_rollout': path})

    def test_symlink_cannot_make_an_outside_rollout_look_contained(self):
        with tempfile.TemporaryDirectory() as outside:
            foreign = Path(outside).resolve() / 'rollout.jsonl'
            foreign.write_bytes(self.rollout.read_bytes())
            link = self.rollout.with_name('linked.jsonl')
            try:
                link.symlink_to(foreign)
            except OSError as error:
                if os.name == 'nt' and getattr(error, 'winerror', None) == 1314:
                    self.skipTest('This Windows account cannot create symbolic links; Linux exercises this guard')
                raise
            variants = [str(link)]
            if os.name == 'nt':
                variants.append('\\\\?\\' + str(link))
            for path in variants:
                with self.subTest(path=path), self.assertRaisesRegex(RuntimeError, 'outside the verified profile'):
                    cli_client.NativeCompletion({**self.entry, 'native_rollout': path})

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
        replacement = self.rollout.with_name('replacement.jsonl')
        replacement.write_bytes(original)
        self.assertNotEqual(self.rollout.stat().st_ino, replacement.stat().st_ino)
        os.replace(replacement, self.rollout)
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


class WindowsPathComparisonTests(unittest.TestCase):
    def test_native_drive_and_unc_prefixes_preserve_profile_containment(self):
        for profile, rollout in (
                ('C:/profile', '//?/C:/profile/sessions/rollout.jsonl'),
                ('//?/C:/profile', 'C:/profile/sessions/rollout.jsonl'),
                ('//server/share/profile', '//?/UNC/server/share/profile/sessions/rollout.jsonl'),
                ('//?/UNC/server/share/profile', '//server/share/profile/sessions/rollout.jsonl')):
            with self.subTest(profile=profile, rollout=rollout):
                sessions = cli_client._comparable_path(PureWindowsPath(profile) / 'sessions')
                self.assertIn(sessions, cli_client._comparable_path(PureWindowsPath(rollout)).parents)

    def test_unrelated_drive_share_profile_and_device_namespace_remain_outside(self):
        for profile, rollout in (
                ('C:/profile', '//?/D:/profile/sessions/rollout.jsonl'),
                ('C:/profile', '//?/C:/profile-other/sessions/rollout.jsonl'),
                ('//server/share/profile', '//?/UNC/server/other/profile/sessions/rollout.jsonl'),
                ('C:/profile', '//?/GLOBALROOT/Device/profile/sessions/rollout.jsonl'),
                ('C:/profile', '//./C:/profile/sessions/rollout.jsonl')):
            with self.subTest(profile=profile, rollout=rollout):
                sessions = cli_client._comparable_path(PureWindowsPath(profile) / 'sessions')
                self.assertNotIn(sessions, cli_client._comparable_path(PureWindowsPath(rollout)).parents)

    @unittest.skipIf(os.name == 'nt', 'POSIX path spelling')
    def test_posix_paths_are_not_reinterpreted_as_win32_namespaces(self):
        path = Path('/tmp') / '\\\\?\\C:\\profile'
        self.assertIs(path, cli_client._comparable_path(path))


if __name__ == '__main__':
    unittest.main()
