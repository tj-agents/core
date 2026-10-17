import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / '.agents/machine/utility/close/scripts/close_session.py'
SPEC = importlib.util.spec_from_file_location('completed_session_close', SCRIPT)
close = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(close)


class CloseOperationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.environment = mock.patch.dict(os.environ, {'AGENT_STATE_DIRECTORY': str(self.root)})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.transcript = self.root / 'session.jsonl'
        self.entry = {'host': 'codex', 'session_id': 'own', 'pid': 123, 'pid_started_at': 100,
                      'cwd': str(Path.cwd()), 'started_at': 100}
        self.shared = mock.Mock()
        self.shared.Refusal = RuntimeError
        self.shared.own_host_and_entry.return_value = self.entry
        self.shared.path_key.side_effect = lambda value: str(Path(value).resolve())

    def transcript_with(self, answer, host='codex'):
        if host == 'codex':
            records = [{'type': 'response_item', 'payload': {'role': 'user', 'content': [{'type': 'input_text', 'text': 'Do the work'}]}},
                       {'type': 'response_item', 'payload': {'role': 'assistant', 'channel': 'final',
                        'content': [{'type': 'output_text', 'text': answer}]}}]
        else:
            records = [{'type': 'user', 'message': {'role': 'user', 'content': 'Do the work'}},
                       {'type': 'assistant', 'message': {'role': 'assistant', 'content': [{'type': 'text', 'text': answer}]}}]
        self.transcript.write_text('\n'.join(json.dumps(item) for item in records), encoding='utf-8')
        return {'hook_event_name': 'Stop', 'session_id': 'own', 'transcript_path': str(self.transcript)}

    def test_done_without_skill_is_routed_on_both_hosts_and_any_repo(self):
        for host in ('codex', 'claude'):
            data = self.transcript_with('Done. The requested work is complete.', host)
            data['cwd'] = str(self.root / 'unrelated-consumer')
            result = close.hook(data)
            self.assertEqual('block', result['decision'])
            self.assertIn('machine:close', result['reason'])

    def test_ordinary_answer_or_pending_work_does_not_trigger_close(self):
        for answer in ('The build is still running.', 'Not done yet.', 'What branch should I use?',
                       'The change is ready for your approval.', 'It means the process exited successfully.'):
            with mock.patch.object(close, 'runtime') as runtime:
                self.assertIsNone(close.hook(self.transcript_with(answer)))
                runtime.assert_not_called()

    def test_prior_completion_is_not_current_turn_completion(self):
        data = self.transcript_with('Done.')
        with self.transcript.open('a', encoding='utf-8') as stream:
            stream.write('\n' + json.dumps({'type': 'response_item', 'payload': {'role': 'user', 'content': 'One more thing'}}))
        self.assertIsNone(close.hook(data))

    def test_tool_output_and_analysis_are_not_completion_reports(self):
        data = self.transcript_with('Still investigating.')
        with self.transcript.open('a', encoding='utf-8') as stream:
            for value in ({'role': 'tool', 'content': 'Done.'},
                          {'role': 'assistant', 'channel': 'analysis', 'content': 'Done.'}):
                stream.write('\n' + json.dumps({'type': 'response_item', 'payload': value}))
        self.assertIsNone(close.hook(data))

    def prepare(self, remove=False):
        with mock.patch.object(close, 'runtime', return_value=self.shared):
            result = close.arm(remove)
        self.assertEqual('armed', result['status'])

    def test_arm_only_prepares_and_default_preserves_checkout(self):
        self.prepare()
        self.shared.fresh_removable_receipt.assert_not_called()
        ticket = close.read_ticket('own')
        self.assertFalse(ticket['remove_worktree'])
        self.assertEqual(self.entry, ticket['entry'])

    def test_removal_requires_existing_fresh_cleanup_proof(self):
        self.shared.fresh_removable_receipt.side_effect = RuntimeError('not removable')
        with mock.patch.object(close, 'runtime', return_value=self.shared), self.assertRaises(RuntimeError):
            close.arm(True)
        self.assertIsNone(close.read_ticket('own'))

    def test_new_user_prompt_cancels_prepared_closure(self):
        self.prepare()
        close.hook({'hook_event_name': 'UserPromptSubmit', 'session_id': 'own'})
        self.assertIsNone(close.read_ticket('own'))

    def test_stop_delegates_only_after_report_and_exact_identity_refresh(self):
        self.prepare()
        helper = mock.Mock()
        helper.main.return_value = 0
        with mock.patch.object(close, 'runtime', return_value=self.shared), mock.patch.object(close.importlib, 'import_module', return_value=helper) as load:
            close.hook(self.transcript_with('The requested cleanup is complete.'))
        load.assert_called_once_with('close')
        helper.main.assert_called_once_with([])

    def test_no_report_or_different_session_never_closes(self):
        self.prepare()
        for data in ({'hook_event_name': 'Stop', 'session_id': 'own'},
                     {**self.transcript_with('Done.'), 'session_id': 'other'}):
            with mock.patch.object(close, 'runtime') as runtime:
                close.hook(data)
                runtime.assert_not_called()

    def test_pid_reuse_or_attachment_change_refuses_without_calling_close(self):
        for key, value in (('pid_started_at', 101), ('cwd', str(self.root / 'other'))):
            self.prepare()
            self.shared.own_host_and_entry.return_value = {**self.entry, key: value}
            with mock.patch.object(close, 'runtime', return_value=self.shared), mock.patch.object(close.importlib, 'import_module') as load:
                result = close.hook(self.transcript_with('Done.'))
                self.assertEqual('block', result['decision'])
                load.assert_not_called()
            self.shared.own_host_and_entry.return_value = self.entry

    def test_close_refusal_is_preserved_and_recursive_stop_does_not_loop(self):
        self.prepare()
        helper = mock.Mock()
        helper.main.side_effect = RuntimeError('not awaiting input')
        data = self.transcript_with('Done.')
        with mock.patch.object(close, 'runtime', return_value=self.shared), mock.patch.object(close.importlib, 'import_module', return_value=helper):
            self.assertEqual('block', close.hook(data)['decision'])
            self.assertIn('not awaiting input', close.hook({**data, 'stop_hook_active': True})['systemMessage'])
        helper.main.assert_called_once_with([])

    def test_unknown_host_attachment_never_arms(self):
        self.shared.own_host_and_entry.side_effect = RuntimeError('no verified registration')
        with mock.patch.object(close, 'runtime', return_value=self.shared), self.assertRaises(RuntimeError):
            close.arm()
        self.assertIsNone(close.read_ticket('own'))

    def test_corrective_arm_runs_after_the_initial_stop_block(self):
        data = self.transcript_with('Done.')
        self.assertEqual('block', close.hook(data)['decision'])
        self.prepare()
        helper = mock.Mock()
        helper.main.return_value = 0
        with mock.patch.object(close, 'runtime', return_value=self.shared), mock.patch.object(close.importlib, 'import_module', return_value=helper):
            close.hook({**data, 'stop_hook_active': True})
        helper.main.assert_called_once_with([])

    def test_explicit_keep_open_is_honored_even_with_a_done_report(self):
        self.prepare()
        self.transcript.write_text('\n'.join(json.dumps(record) for record in (
            {'type': 'user', 'message': {'role': 'user', 'content': 'Finish this but keep the CLI open.'}},
            {'type': 'assistant', 'message': {'role': 'assistant', 'content': 'Done.'}},
        )), encoding='utf-8')
        data = {'hook_event_name': 'Stop', 'session_id': 'own', 'transcript_path': str(self.transcript)}
        with mock.patch.object(close, 'runtime') as runtime:
            self.assertIsNone(close.hook(data))
            runtime.assert_not_called()
        self.assertIsNone(close.read_ticket('own'))

    def test_expired_ticket_refuses_once_without_a_stop_loop(self):
        self.prepare()
        ticket = close.read_ticket('own')
        ticket['armed_at'] = 1
        close.save_ticket('own', ticket)
        data = self.transcript_with('Done.')
        self.assertEqual('block', close.hook(data)['decision'])
        self.assertIn('expired', close.hook({**data, 'stop_hook_active': True})['systemMessage'])

    def test_duplicate_stop_cannot_start_another_close(self):
        self.prepare()
        helper = mock.Mock()
        helper.main.return_value = 0
        data = self.transcript_with('Done.')
        with mock.patch.object(close, 'runtime', return_value=self.shared), mock.patch.object(close.importlib, 'import_module', return_value=helper):
            close.hook(data)
            self.assertIn('in progress', close.hook(data)['systemMessage'])
        helper.main.assert_called_once_with([])

    def test_runtime_resolves_from_source_and_both_packaged_entries(self):
        self.assertTrue((close.peer_scripts() / 'close.py').is_file())


if __name__ == '__main__':
    unittest.main()
