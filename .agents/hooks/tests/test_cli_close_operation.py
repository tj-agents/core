import importlib.util
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / '.agents/cli/utility/close/scripts/close_session.py'
SPEC = importlib.util.spec_from_file_location('completed_session_close', SCRIPT)
close = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(close)
sys.path.insert(0, str(close.peer_scripts()))
WATCHER_SPEC = importlib.util.spec_from_file_location('close_watcher', SCRIPT.with_name('close_watcher.py'))
watcher = importlib.util.module_from_spec(WATCHER_SPEC)
WATCHER_SPEC.loader.exec_module(watcher)
sys.path.insert(0, str(SCRIPT.parent))
CLOSEOUT = ROOT / '.agents/cli/workflow/closeout/scripts'
sys.path.insert(0, str(CLOSEOUT))
import closeout
closeout.close_session = close
LANDED_SPEC = importlib.util.spec_from_file_location('close_landed', CLOSEOUT / 'close_landed.py')
landed = importlib.util.module_from_spec(LANDED_SPEC)
LANDED_SPEC.loader.exec_module(landed)


class ArmTests(unittest.TestCase):
    def setUp(self):
        self.entry = {'host': 'codex', 'session_id': 'own', 'pid': 123, 'pid_started_at': 100.5,
                      'cwd': str(Path.cwd()), 'started_at': 100}
        self.shared = mock.Mock()
        self.shared.Refusal = RuntimeError
        self.shared.state_directory.return_value = Path('state')
        self.shared.own_host_and_entry.return_value = self.entry
        self.shared.entries.return_value = [('own.json', self.entry)]
        self.shared.git.return_value = (1, '', '')
        self.store = self.shared.register_session._load_session_store.return_value
        self.store.get_session.return_value = {'ended_at': None, 'turn_state': 'working', 'last_activity_at': 100,
                                               'pid': 123, 'pid_started_at': 100.5}
        self.shared.client_runtime_path.return_value = ROOT / '.agents/machine/scripts/cli_client.py'

    def arm(self):
        with mock.patch.object(close, 'runtime', return_value=self.shared):
            return close.arm()

    def test_arm_starts_one_detached_watcher_bound_to_this_exact_host(self):
        self.assertEqual('armed', self.arm()['status'])
        self.shared.start_detached.assert_called_once()
        script, arguments, extra = self.shared.start_detached.call_args.args
        self.assertEqual('close_watcher.py', script.name)
        self.assertEqual(['codex', 'own', '123', '100.5'], [arguments[i] for i in (1, 3, 5, 7)])
        self.assertEqual({'close.py', 'cli_client.py'}, {path.name for path in extra})
        self.assertTrue(all(path.is_file() for path in extra))

    def test_arm_has_no_terminal_or_checkout_cleanup_dependency(self):
        self.shared.git.return_value = (0, str(ROOT / '.git'), '')
        self.arm()
        arguments = self.shared.start_detached.call_args.args[1]
        self.assertNotIn('--repo', arguments)
        self.assertNotIn('--sweep', arguments)
        self.shared.git.assert_not_called()

    def test_only_closeout_supplies_optional_checkout_cleanup(self):
        self.shared.git.return_value = (0, str(ROOT / '.git'), '')
        with mock.patch.object(close, 'runtime', return_value=self.shared), \
                mock.patch.object(closeout, 'sweep_script', return_value=Path('sweep.py')):
            closeout.arm()
        arguments = self.shared.start_detached.call_args.args[1]
        self.assertEqual(str(ROOT), arguments[arguments.index('--repo') + 1])
        self.assertEqual('sweep.py', arguments[arguments.index('--sweep') + 1])

    def test_claude_arm_passes_its_transcript_and_the_size_at_arming(self):
        self.entry['host'] = 'claude'
        with tempfile.TemporaryDirectory() as home:
            transcript = Path(home) / 'projects' / 'C--repo' / 'own.jsonl'
            transcript.parent.mkdir(parents=True)
            transcript.write_bytes(b'{}\n')
            with mock.patch.dict(os.environ, {'CLAUDE_CONFIG_DIR': home}):
                self.arm()
        arguments = self.shared.start_detached.call_args.args[1]
        self.assertEqual(str(transcript), arguments[arguments.index('--transcript') + 1])
        self.assertEqual('3', arguments[arguments.index('--transcript-offset') + 1])

    def test_arm_refuses_without_an_active_turn(self):
        for row in (None, {'ended_at': 5, 'turn_state': 'working'},
                    {**self.store.get_session.return_value, 'turn_state': 'awaiting_input'}):
            self.store.get_session.return_value = row
            with self.assertRaisesRegex(RuntimeError, 'no active turn'):
                self.arm()
        self.shared.start_detached.assert_not_called()

    def arm_after_stop(self, landed_at=2000.0):
        with mock.patch.object(close, 'runtime', return_value=self.shared), \
                mock.patch.object(closeout, 'sweep_script', return_value=None):
            return closeout.arm_after_stop(landed_at)

    def test_arm_after_stop_binds_the_watcher_to_the_recorded_stop(self):
        self.shared.finite_positive = watcher.session_close.finite_positive
        self.store.get_session.return_value = {**self.store.get_session.return_value, 'turn_state': 'awaiting_input',
                                               'last_activity_at': 1005.0, 'started_at': 100.0}
        self.assertEqual('armed', self.arm_after_stop()['status'])
        arguments = self.shared.start_detached.call_args.args[1]
        armed_at = float(arguments[arguments.index('--armed-at') + 1])
        self.assertEqual(math.nextafter(1005.0, 0.0), armed_at)
        self.assertEqual({'armed_at': armed_at}, self.shared.write_json.call_args.args[1])

    def test_arm_after_stop_refuses_mid_turn_or_a_delivery_that_landed_before_the_session(self):
        self.shared.finite_positive = watcher.session_close.finite_positive
        for row, reason in (({'turn_state': 'working', 'last_activity_at': 1005.0, 'started_at': 100.0}, 'no recorded stop'),
                            ({'turn_state': 'awaiting_input', 'last_activity_at': 1005.0, 'started_at': 2500.0}, 'before this session')):
            self.store.get_session.return_value = {**self.store.get_session.return_value, **row}
            with self.assertRaisesRegex(RuntimeError, reason):
                self.arm_after_stop()
        self.shared.start_detached.assert_not_called()

    def test_sibling_registration_does_not_prevent_attributed_client_arming(self):
        self.shared.entries.return_value.append(('peer.json', {**self.entry, 'session_id': 'peer'}))
        self.assertEqual('armed', self.arm()['status'])
        self.shared.start_detached.assert_called_once()

    def test_store_must_match_the_frontend_attachment(self):
        self.store.get_session.return_value['pid'] = 999
        with self.assertRaisesRegex(RuntimeError, 'attachment is not recorded'):
            self.arm()
        self.shared.start_detached.assert_not_called()

    def test_runtime_resolves_from_source_and_both_packaged_entries(self):
        self.assertTrue((close.peer_scripts() / 'close.py').is_file())
        for directory in ('skills', 'codex-skills'):
            entry = ROOT / 'plugins/cli' / directory / 'close/scripts/close_session.py'
            with mock.patch.object(close, '__file__', str(entry)):
                self.assertEqual(entry.parents[3] / '.agents/machine/utility/peer-cli/scripts', close.peer_scripts())

    def test_missing_packaged_dependency_cannot_fall_back_to_the_author_checkout(self):
        missing = ROOT / 'plugins/missing-package/codex-skills/close/scripts/close_session.py'
        with mock.patch.object(close, '__file__', str(missing)), self.assertRaisesRegex(RuntimeError, 'shipped peer-cli runtime'):
            close.peer_scripts()


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class WatcherTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        environment = mock.patch.dict(os.environ, {'AGENT_STATE_DIRECTORY': directory.name})
        environment.start()
        self.addCleanup(environment.stop)
        self.args = watcher.arguments(['--host', 'claude', '--session-id', 'own', '--pid', '123',
                                       '--pid-started-at', '100.5', '--armed-at', '1000', '--timeout', '60'])
        self.clock = Clock()
        self.rows = []
        live = mock.patch.object(watcher.session_close, 'verified_live', return_value=True)
        live.start()
        self.addCleanup(live.stop)

    def row(self, state, activity):
        return {'turn_state': state, 'last_activity_at': activity, 'ended_at': None, 'pid': 123}

    def wait(self, timeline):
        def current(_args):
            for until, row in timeline:
                if self.clock.now < until:
                    return row
            return timeline[-1][1]
        with mock.patch.object(watcher, 'session_row', side_effect=current):
            return watcher.wait_for_idle(self.args, clock=self.clock, sleep=self.clock.sleep)

    def test_closes_only_after_the_turn_ends_and_stays_idle(self):
        timeline = [(1005, self.row('working', 990)), (1e9, self.row('awaiting_input', 1005))]
        self.assertEqual(1005, self.wait(timeline))
        self.assertGreaterEqual(self.clock.now, 1005 + self.args.idle)

    def test_a_new_prompt_after_the_reply_cancels(self):
        timeline = [(1002, self.row('working', 990)), (1003, self.row('awaiting_input', 1002)),
                    (1e9, self.row('working', 1003))]
        self.assertIsNone(self.wait(timeline))
        self.assertLess(self.clock.now, 1010)

    def test_a_stop_from_before_arming_is_not_the_final_reply(self):
        self.assertIsNone(self.wait([(1e9, self.row('awaiting_input', 999))]))

    def test_an_arm_after_the_stop_closes_on_that_stop(self):
        self.args.armed_at = math.nextafter(1005.0, 0.0)
        self.assertEqual(1005, self.wait([(1e9, self.row('awaiting_input', 1005.0))]))

    def test_a_newer_arm_supersedes_this_watcher_without_recording_an_outcome(self):
        watcher.session_close.write_json(watcher.armed_path('own'), {'armed_at': 2000.0})
        self.assertIsNone(self.wait([(1e9, self.row('awaiting_input', 1005))]))
        with mock.patch.object(watcher, 'wait_for_idle', return_value=None):
            self.assertEqual(0, watcher.main(['--host', 'claude', '--session-id', 'own', '--pid', '123',
                                              '--pid-started-at', '100.5', '--armed-at', '1000']))
        self.assertFalse(watcher.outcome_path('own').exists())

    def test_ended_session_or_exited_host_cancels(self):
        self.assertIsNone(self.wait([(1e9, {**self.row('awaiting_input', 1005), 'ended_at': 1006})]))
        with mock.patch.object(watcher.session_close, 'verified_live', return_value=False):
            self.assertIsNone(self.wait([(1e9, self.row('awaiting_input', 1005))]))

    def test_a_prompt_after_an_interrupted_turn_cancels(self):
        timeline = [(1004, self.row('working', 990)), (1e9, self.row('working', 1004))]
        self.assertIsNone(self.wait(timeline))
        self.assertLess(self.clock.now, 1005)

    def test_a_prompt_and_its_stop_inside_one_poll_cancel(self):
        timeline = [(1002, self.row('awaiting_input', 1001)), (1e9, self.row('awaiting_input', 1002))]
        self.assertIsNone(self.wait(timeline))

    def transcript(self, *records):
        path = Path(os.environ['AGENT_STATE_DIRECTORY']) / 'transcript.jsonl'
        path.write_text(''.join(json.dumps(record) + '\n' for record in records), encoding='utf-8')
        self.args.transcript, self.args.transcript_offset = str(path), 0
        return path

    def test_a_blocked_stop_hook_cancels(self):
        self.transcript({'type': 'assistant', 'message': {'content': 'done'}},
                        {'type': 'attachment', 'attachment': {'type': 'hook_blocking_error', 'hookEvent': 'Stop'}},
                        {'type': 'system', 'subtype': 'stop_hook_summary'})
        self.assertIsNone(self.wait([(1e9, self.row('awaiting_input', 1005))]))

    def test_idle_counts_only_after_every_stop_hook_finished(self):
        path = self.transcript({'type': 'assistant', 'message': {'content': 'done'}})
        sleep = self.clock.sleep

        def finish_hooks_at_1010(seconds):
            sleep(seconds)
            if self.clock.now >= 1010 and 'stop_hook_summary' not in path.read_text(encoding='utf-8'):
                with path.open('a', encoding='utf-8') as stream:
                    stream.write(json.dumps({'type': 'system', 'subtype': 'stop_hook_summary'}) + '\n')
        self.clock.sleep = finish_hooks_at_1010
        self.assertEqual(1005, self.wait([(1e9, self.row('awaiting_input', 1005))]))
        self.assertGreaterEqual(self.clock.now, 1010 + self.args.idle)

    def test_transcript_written_before_arming_is_ignored(self):
        path = self.transcript({'type': 'attachment', 'attachment': {'type': 'hook_blocking_error', 'hookEvent': 'Stop'}})
        self.args.transcript_offset = path.stat().st_size
        with path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'type': 'system', 'subtype': 'stop_hook_summary'}) + '\n')
        self.assertEqual('finished', watcher.transcript_verdict(self.args))

    def test_compaction_after_arming_does_not_cancel_a_claude_close(self):
        self.transcript({'type': 'user', 'isCompactSummary': True, 'message': {'content': 'summary'}},
                        {'type': 'assistant', 'message': {'content': 'done'}},
                        {'type': 'system', 'subtype': 'stop_hook_summary'})
        timeline = [(1004, self.row('working', 1002)), (1e9, self.row('awaiting_input', 1004))]
        self.assertEqual(1004, self.wait(timeline))

    def test_a_registry_blip_after_the_final_stop_only_restarts_the_claude_idle_wait(self):
        self.transcript({'type': 'assistant', 'message': {'content': 'done'}},
                        {'type': 'system', 'subtype': 'stop_hook_summary'})
        timeline = [(1002, self.row('awaiting_input', 1001)), (1003, self.row('working', 1002)),
                    (1e9, self.row('awaiting_input', 1003))]
        self.assertEqual(1003, self.wait(timeline))
        self.assertGreaterEqual(self.clock.now, 1003 + self.args.idle)

    def test_a_claude_prompt_after_arming_cancels_even_without_a_stop(self):
        self.transcript({'type': 'user', 'message': {'content': '[Request interrupted by user]'}},
                        {'type': 'user', 'message': {'content': [{'type': 'text', 'text': 'wait, also do X'}]}})
        self.assertIsNone(self.wait([(1e9, self.row('working', 1004))]))

    def test_a_turn_injected_after_the_final_stop_cancels(self):
        self.transcript({'type': 'assistant', 'message': {'content': 'done'}},
                        {'type': 'system', 'subtype': 'stop_hook_summary'},
                        {'type': 'user', 'isMeta': True, 'message': {'content': '<task-notification>'}})
        self.assertIsNone(self.wait([(1e9, self.row('awaiting_input', 1005))]))

    def test_tool_results_after_arming_are_not_prompts(self):
        self.transcript({'type': 'user', 'message': {'content': [{'type': 'tool_result', 'content': 'armed'}]}},
                        {'type': 'assistant', 'message': {'content': 'done'}},
                        {'type': 'system', 'subtype': 'stop_hook_summary'})
        self.assertEqual('finished', watcher.transcript_verdict(self.args))

    def test_the_session_store_is_read_without_taking_a_write_lock(self):
        store = watcher.session_close.register_session._load_session_store()
        connection = store.connect()
        store.start_session(connection, 'claude', 'own', str(Path.cwd()), pid=123, pid_started_at=100.5)
        connection.execute('BEGIN IMMEDIATE')
        try:
            self.assertEqual('working', watcher.session_row(self.args)['turn_state'])
        finally:
            connection.rollback()
            connection.close()

    def close_main(self):
        return watcher.main(['--host', 'claude', '--session-id', 'own', '--pid', '123',
                             '--pid-started-at', '100.5', '--armed-at', '1000'])

    def test_refused_close_is_recorded_without_ending_the_session(self):
        with mock.patch.object(watcher, 'wait_for_idle', return_value=1005), \
                mock.patch.object(watcher, 'registered_entry', return_value=None), \
                mock.patch.object(watcher.session_close, '_record_own_end') as ended:
            self.assertEqual(2, self.close_main())
        ended.assert_not_called()
        self.assertIn('no longer registered', watcher.session_close.read_json(watcher.outcome_path('own'))['status'])

    def test_close_confirms_client_exit_before_recording_the_end(self):
        entry = {'host': 'claude', 'session_id': 'own', 'pid': 123, 'pid_started_at': 100.5}
        calls = []
        def stop(selected, before_signal):
            self.assertIs(entry, selected)
            before_signal()
            calls.append('close')
        with mock.patch.object(watcher, 'wait_for_idle', return_value=1005), \
                mock.patch.object(watcher, 'registered_entry', return_value=entry), \
                mock.patch.object(watcher.session_close, 'awaiting_input_activity') as idle, \
                mock.patch.object(watcher.session_close, '_record_own_end', side_effect=lambda *a: calls.append('end')), \
                mock.patch.object(watcher.close, 'close_host', side_effect=stop), \
                mock.patch.object(watcher.session_close, 'verified_exited', return_value=True):
            self.assertEqual(0, self.close_main())
        self.assertEqual([mock.call(entry, 1005)] * 2, idle.call_args_list)
        self.assertEqual(['close', 'end'], calls)

    def test_failed_or_unconfirmed_exit_never_marks_the_session_ended(self):
        entry = {'host': 'claude', 'session_id': 'own', 'pid': 123, 'pid_started_at': 100.5}
        for failure, message in ((RuntimeError('identity changed'), 'identity changed'),
                                 (None, 'CLI client exit was not confirmed')):
            with self.subTest(message=message), \
                    mock.patch.object(watcher, 'wait_for_idle', return_value=1005), \
                    mock.patch.object(watcher, 'registered_entry', return_value=entry), \
                    mock.patch.object(watcher.session_close, 'awaiting_input_activity'), \
                    mock.patch.object(watcher.session_close, '_record_own_end') as ended, \
                    mock.patch.object(watcher.close, 'close_host', side_effect=failure), \
                    mock.patch.object(watcher.session_close, 'verified_exited', return_value=False), \
                    mock.patch.object(watcher, 'EXIT_WAIT_SECONDS', 0):
                self.assertEqual(2, self.close_main())
            ended.assert_not_called()
            self.assertIn(message, watcher.session_close.read_json(watcher.outcome_path('own'))['status'])

    def test_activity_is_rechecked_at_the_signal_boundary(self):
        entry = {'host': 'claude', 'session_id': 'own', 'pid': 123, 'pid_started_at': 100.5}
        def stop(selected, before_signal):
            before_signal()
            self.fail('a new prompt must prevent signalling')
        with mock.patch.object(watcher, 'wait_for_idle', return_value=1005), \
                mock.patch.object(watcher, 'registered_entry', return_value=entry), \
                mock.patch.object(watcher.session_close, 'awaiting_input_activity',
                                  side_effect=[1005, RuntimeError('activity changed')]), \
                mock.patch.object(watcher.session_close, '_record_own_end') as ended, \
                mock.patch.object(watcher.close, 'close_host', side_effect=stop):
            self.assertEqual(2, self.close_main())
        ended.assert_not_called()
        self.assertEqual('refused: activity changed',
                         watcher.session_close.read_json(watcher.outcome_path('own'))['status'])


def git(cwd, *arguments):
    subprocess.run(['git', '-C', str(cwd), *arguments], check=True, capture_output=True)


class LandedTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.primary = Path(directory.name) / 'primary'
        self.linked = Path(directory.name) / 'linked'
        git(directory.name, 'init', '-q', '-b', 'main', str(self.primary))
        git(self.primary, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'base')
        git(self.primary, 'worktree', 'add', '-q', '-b', 'Fix/Thing', str(self.linked))
        self.head = subprocess.run(['git', '-C', str(self.linked), 'rev-parse', 'HEAD'], capture_output=True,
                                   text=True, check=True).stdout.strip()

    def merged_at(self, cwd, pulls):
        with mock.patch.object(landed, 'merged_pulls', return_value=pulls) as lookup:
            return landed.merged_at(cwd, watcher.session_close.git), lookup

    def test_a_clean_linked_worktree_merged_at_head_reports_the_merge_time(self):
        pulls = [{'headRefOid': 'other', 'mergedAt': '2026-10-24T13:00:00Z'},
                 {'headRefOid': self.head, 'mergedAt': '2026-10-24T12:00:00Z'}]
        when, lookup = self.merged_at(self.linked, pulls)
        self.assertEqual(1792843200.0, when)
        lookup.assert_called_once_with(self.linked, 'Fix/Thing')

    def test_unmerged_head_dirty_tree_or_primary_checkout_never_lands(self):
        self.assertIsNone(self.merged_at(self.linked, [{'headRefOid': 'older', 'mergedAt': '2026-10-24T12:00:00Z'}])[0])
        merged = [{'headRefOid': self.head, 'mergedAt': '2026-10-24T12:00:00Z'}]
        self.assertIsNone(self.merged_at(self.primary, merged)[0])
        (self.linked / 'work.txt').write_text('unsaved', encoding='utf-8')
        when, lookup = self.merged_at(self.linked, merged)
        self.assertIsNone(when)
        lookup.assert_not_called()

    def test_hook_arms_only_a_landed_delivery_and_never_raises(self):
        payload = json.dumps({'hook_event_name': 'Stop', 'session_id': 'own', 'cwd': str(self.linked)})
        for landed_at, failure in ((None, None), (1792843200.0, None), (1792843200.0, RuntimeError('refused'))):
            with mock.patch.object(landed, 'merged_at', return_value=landed_at), \
                    mock.patch.object(landed.closeout, 'arm_after_stop', side_effect=failure) as arm, \
                    mock.patch.object(sys, 'stdin', io.StringIO(payload)):
                self.assertEqual(0, landed.main())
            self.assertEqual(landed_at is not None, arm.called)


if __name__ == '__main__':
    unittest.main()
