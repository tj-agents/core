"""Native submitted-input identity cannot select a parent or peer frontend."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.agents/machine/scripts'))
import cli_client as client
import codex_hook_trust


def events(identity, stamp, *following):
    return [
        {'dir': 'meta', 'kind': 'session_start'},
        {'dir': 'from_tui', 'kind': 'op', 'ts': datetime.fromtimestamp(stamp, timezone.utc).isoformat(),
         'payload': {'UserTurn': {'client_user_message_id': identity}}},
        *following,
    ]


class InputBindingTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.profile = self.root / 'profile'
        self.backend = {'pid': 1, 'process_start_time': 'native-start'}
        self.contexts = {}
        self.infos = {}
        self.commands = {}
        for patch in (
            mock.patch.dict(os.environ, {'AGENT_STATE_DIRECTORY': str(self.root), 'CODEX_HOME': str(self.profile)}),
            mock.patch.object(client.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stderr='')),
            mock.patch.object(client, 'daemon_identity', return_value=self.backend),
            mock.patch.object(client, 'process_context', side_effect=lambda pid: self.contexts.get(pid, {})),
            mock.patch.object(client, 'process_arguments', side_effect=lambda pid: self.commands[pid]),
            mock.patch.object(codex_hook_trust, 'AppServer'),
        ):
            patch.start()
            self.addCleanup(patch.stop)
        self.native_input = mock.patch.object(client, 'current_input', return_value='own-input')
        self.input = self.native_input.start()
        self.addCleanup(self.native_input.stop)
        self.nearest = SimpleNamespace(pid=1, name='codex.exe')
        self.commands[1] = ['codex', 'app-server']

    def bind(self, pid=123, identity='own-input'):
        arguments, environment, ticket = client.prepare(
            'codex', ['resume', 'thread'], self.root,
            {**os.environ, client.RECORD_ENV: '1', client.RECORD_PATH_ENV: 'parent-path'}, executable='codex')
        client.attach(ticket, pid)
        path = client.binding_path(ticket['token'])
        records = events(identity, ticket['created_at'] + 1)
        path.with_name('events.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in records), encoding='utf-8')
        self.infos[pid] = SimpleNamespace(pid=pid, name='codex.exe', started_at=ticket['created_at'])
        self.contexts[pid] = {'profile': str(self.profile.resolve()), client.RECORD_ENV: '1',
                              client.RECORD_PATH_ENV: ticket['recording_path']}
        self.commands[pid] = ['codex', *arguments]
        return ticket, environment, arguments

    def resolve(self, since=0):
        return client.recorded_client('current-thread', self.nearest, self.infos.get, self.infos, since)

    def test_launcher_starts_a_sanitized_daemon_and_keeps_each_frontend_private_record(self):
        ticket, environment, arguments = self.bind()
        daemon_environment = client.subprocess.run.call_args.kwargs['env']
        self.assertNotIn(client.RECORD_ENV, daemon_environment)
        self.assertNotIn(client.RECORD_PATH_ENV, daemon_environment)
        self.assertEqual('1', environment[client.RECORD_ENV])
        self.assertNotEqual('parent-path', environment[client.RECORD_PATH_ENV])
        self.assertEqual(['resume', 'thread'], arguments[4:])
        self.assertIn('shell_environment_policy.set.' + client.RECORD_ENV + '=""', arguments)
        info, record = self.resolve()
        self.assertEqual(123, info.pid)
        self.assertEqual('own-input', record['client_message_id'])
        client.release(ticket)
        self.assertFalse(client.binding_path(ticket['token']).parent.exists())

    def test_foreign_or_inherited_input_never_selects_the_parent(self):
        self.bind(identity='parent-input')
        with mock.patch.dict(os.environ, {client.RECORD_PATH_ENV: self.contexts[123][client.RECORD_PATH_ENV]}):
            with self.assertRaisesRegex(RuntimeError, 'Cannot attribute'):
                self.resolve()

    def test_latest_submitted_input_is_required_and_copied_old_history_is_rejected(self):
        ticket, _, _ = self.bind()
        with self.assertRaisesRegex(RuntimeError, 'Cannot attribute'):
            self.resolve(since=ticket['created_at'] + 2)
        path = Path(ticket['recording_path'])
        with path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(events('new-other-thread-input', ticket['created_at'] + 3)[1]) + '\n')
        with self.assertRaisesRegex(RuntimeError, 'Cannot attribute'):
            self.resolve()

    def test_changed_pid_profile_backend_command_or_recording_state_refuses(self):
        ticket, _, _ = self.bind()
        path = client.binding_path(ticket['token'])
        original = path.read_text(encoding='utf-8')
        for change in ({'profile': 'foreign'}, {'backend': {'pid': 99}}, {'pid': True}, {'created_at': 'invalid'},
                       {'recorded_at': float('nan')}):
            with self.subTest(change=change):
                path.write_text(json.dumps({**json.loads(original), **change}), encoding='utf-8')
                with self.assertRaises(RuntimeError):
                    self.resolve()
        path.write_text(original, encoding='utf-8')
        self.infos[123].started_at -= 100
        with self.assertRaises(RuntimeError):
            self.resolve()
        self.infos[123].started_at = ticket['created_at']
        self.commands[123] = ['codex', 'app-server']
        with self.assertRaises(RuntimeError):
            self.resolve()

    def test_ambiguous_live_writers_and_two_matching_frontends_refuse(self):
        first, _, _ = self.bind()
        self.bind(pid=456)
        with self.assertRaisesRegex(RuntimeError, 'Cannot attribute'):
            self.resolve()
        client.release(first)
        self.contexts[123][client.RECORD_PATH_ENV] = self.contexts[456][client.RECORD_PATH_ENV]
        with self.assertRaisesRegex(RuntimeError, 'Multiple native processes'):
            self.resolve()

    def test_failed_attach_never_deletes_an_existing_record(self):
        _, _, ticket = client.prepare('codex', [], self.root, os.environ, executable='codex')
        path = client.binding_path(ticket['token'])
        path.write_text('existing', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            client.attach(ticket, 123)
        client.release(ticket)
        self.assertEqual('existing', path.read_text(encoding='utf-8'))

    def test_other_hosts_maintenance_and_private_clients_do_not_enable_recording(self):
        for host, arguments in [('claude', []), ('codex', ['--no-daemon']), ('codex', ['review']),
                                ('codex', ['exec']), ('codex', ['app-server']), ('codex', ['--help'])]:
            with self.subTest(host=host, arguments=arguments):
                prepared, environment, ticket = client.prepare(host, arguments, self.root,
                    {client.RECORD_ENV: 'parent', client.RECORD_PATH_ENV: 'parent-path'})
                self.assertEqual(arguments, prepared)
                self.assertNotIn(client.RECORD_ENV, environment)
                self.assertNotIn(client.RECORD_PATH_ENV, environment)
                self.assertIsNone(ticket)


class RecorderTests(unittest.TestCase):
    def test_switch_reset_new_input_partial_write_and_duplicate_header_cancel(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'events.jsonl'
            for following in (
                {'dir': 'to_tui', 'kind': 'clear_ui'}, {'dir': 'to_tui', 'kind': 'new_session'},
                {'dir': 'to_tui', 'kind': 'app_event', 'variant': 'ResetTranscriptForThreadSwitch'},
                {'dir': 'to_tui', 'kind': 'app_event', 'variant': 'SelectAgentThread'},
            ):
                path.write_text(''.join(json.dumps(row) + '\n' for row in events('own', 100, following)), encoding='utf-8')
                self.assertIsNone(client.latest_input(path))
            path.write_text(''.join(json.dumps(row) + '\n' for row in events('own', 100)), encoding='utf-8')
            self.assertEqual('own', client.latest_input(path))
            self.assertIsNone(client.latest_input(path, since=101))
            with path.open('a', encoding='utf-8') as stream:
                stream.write('{')
            with self.assertRaisesRegex(RuntimeError, 'incomplete'):
                client.latest_input(path)
            path.write_text(''.join(json.dumps(row) + '\n' for row in events('own', 100) * 2), encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'unique startup'):
                client.latest_input(path)

    def test_native_history_uses_latest_input_including_steering_not_first_summary(self):
        server = mock.Mock()
        def request(method, params):
            if method == 'thread/read':
                return {'thread': {'source': 'cli'}}
            if method == 'thread/turns/list':
                return {'data': [{'id': 'turn'}]}
            if 'cursor' not in params:
                return {'data': [{'item': {'type': 'commandExecution'}}], 'nextCursor': 'next'}
            return {'data': [{'item': {'type': 'userMessage', 'clientId': 'steering-input'}},
                             {'item': {'type': 'userMessage', 'clientId': 'first-input'}}], 'nextCursor': None}
        server.request.side_effect = request
        self.assertEqual('steering-input', client.current_input(server, 'thread'))
        self.assertEqual('desc', server.request.call_args.args[1]['sortDirection'])


class DaemonSafetyTests(unittest.TestCase):
    def test_inherited_recording_daemon_refuses_even_after_a_second_writer_has_exited(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.dict(os.environ, {'CODEX_HOME': temporary}):
            path = Path(temporary) / 'app-server-daemon/daemon.pid'
            path.parent.mkdir()
            path.write_text(json.dumps({'pid': 77, 'processStartTime': 'native-start'}), encoding='utf-8')
            with mock.patch.object(client, 'process_arguments', return_value=['codex', 'app-server']), \
                    mock.patch.object(client, 'process_context', return_value={
                        'profile': str(Path(temporary).resolve()), client.RECORD_ENV: '1',
                        client.RECORD_PATH_ENV: 'reused-parent-path'}):
                with self.assertRaisesRegex(RuntimeError, 'inherited frontend recording'):
                    client.daemon_identity(expected_pid=77)


if __name__ == '__main__':
    unittest.main()
