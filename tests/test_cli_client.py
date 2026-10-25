"""Individual frontend identity and kernel-bound closure regressions."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.agents/machine/scripts'))
sys.path.insert(0, str(ROOT / '.agents/machine/utility/peer-cli/scripts'))
import cli_client as client
import session_close as close


class BindingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        environment = mock.patch.dict(os.environ, {
            'AGENT_STATE_DIRECTORY': str(self.root), 'CODEX_HOME': str(self.root / 'profile'),
        })
        environment.start()
        self.addCleanup(environment.stop)

    def bind(self, arguments=None):
        arguments, environment, ticket = client.prepare(
            'codex', arguments or ['resume', 'thread-a'], self.root,
            {**os.environ, client.TOKEN_ENV: 'inherited-parent'},
        )
        self.assertNotIn(client.TOKEN_ENV, environment)
        client.attach(ticket, 123)
        return arguments, ticket

    def test_managed_identity_is_per_launch_and_native_arguments_are_preserved(self):
        original = ['-m', 'model', 'resume', 'thread-a', 'two words']
        arguments, ticket = self.bind(original)
        self.assertEqual(original, arguments[2:])
        self.assertEqual('--config', arguments[0])
        self.assertEqual(client.TOKEN_KEY + '="' + ticket['token'] + '"', arguments[1])
        other, _, another = client.prepare('codex', [], self.root, os.environ)
        self.assertNotEqual(ticket['token'], another['token'])
        info = SimpleNamespace(pid=123, name='codex.exe', started_at=ticket['created_at'])
        found, record = client.resolve(ticket['token'], lambda pid: info, lambda pid: ['codex', *arguments])
        self.assertIs(info, found)
        self.assertEqual(str(self.root.resolve()), record['launch_cwd'])
        client.release(ticket)
        self.assertFalse(client.binding_path(ticket['token']).exists())

    def test_maintenance_and_other_hosts_do_not_receive_a_binding(self):
        for host, arguments in [('claude', []), ('codex', ['app-server']), ('codex', ['agents', 'list']),
                                ('codex', ['--config', 'x=1', 'plugin', 'list']), ('codex', ['--version'])]:
            with self.subTest(host=host, arguments=arguments):
                prepared, environment, ticket = client.prepare(host, arguments, self.root,
                                                                {client.TOKEN_ENV: 'parent'})
                self.assertEqual(arguments, prepared)
                self.assertNotIn(client.TOKEN_ENV, environment)
                self.assertIsNone(ticket)

    def test_resume_parser_ignores_option_values_and_respects_literal_separator(self):
        self.assertEqual('thread-a', client.resumed_session(
            ['codex', '--model', 'resume', '-cfoo="resume"', 'resume', '--cd', 'somewhere', 'thread-a']))
        self.assertIsNone(client.resumed_session(['codex', '--', 'resume', 'thread-a']))
        self.assertIsNone(client.resumed_session(['codex', 'resume', '--last']))
        self.assertTrue(client.is_session(['--', '--help']))

    def test_invalid_missing_and_foreign_bindings_fail_closed(self):
        arguments, ticket = self.bind()
        path = client.binding_path(ticket['token'])
        original = json.loads(path.read_text(encoding='utf-8'))
        info = SimpleNamespace(pid=123, name='codex.exe', started_at=ticket['created_at'])
        for changes in ({'profile': str(self.root / 'other')}, {'pid': True}, {'pid': -1},
                        {'created_at': 'invalid'}, {'recorded_at': float('nan')},
                        {'recorded_at': original['created_at'] - 1}):
            with self.subTest(changes=changes):
                path.write_text(json.dumps({**original, **changes}), encoding='utf-8')
                with self.assertRaises(RuntimeError):
                    client.resolve(ticket['token'], lambda pid: info, lambda pid: ['codex', *arguments])
        path.write_text('[]', encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError, 'invalid'):
            client.resolve(ticket['token'], lambda pid: info, lambda pid: [])
        for token in ('../other', '', 'g' * 64):
            with self.assertRaises(RuntimeError):
                client.binding_path(token)

    def test_backend_reused_pid_and_missing_native_nonce_are_rejected(self):
        arguments, ticket = self.bind()
        for name, started, argv in (
            ('codex.exe', ticket['created_at'], ['codex', *arguments[:2], 'app-server']),
            ('codex.exe', ticket['created_at'] + 100, ['codex', *arguments]),
            ('codex.exe', ticket['created_at'], ['codex', 'resume', 'thread-a']),
            ('python.exe', ticket['created_at'], ['codex', *arguments]),
        ):
            with self.subTest(name=name, started=started, argv=argv):
                info = SimpleNamespace(pid=123, name=name, started_at=started)
                with self.assertRaises(RuntimeError):
                    client.resolve(ticket['token'], lambda pid: info, lambda pid: argv)

    def test_failed_exclusive_attach_does_not_delete_someone_elses_record(self):
        _, _, ticket = client.prepare('codex', [], self.root, os.environ)
        path = client.binding_path(ticket['token'])
        path.parent.mkdir(parents=True)
        path.write_text('existing', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            client.attach(ticket, 123)
        client.release(ticket)
        self.assertEqual('existing', path.read_text(encoding='utf-8'))


class ClientResolutionTests(unittest.TestCase):
    def test_client_helper_resolves_only_shipped_resources_in_every_layout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative, resource in (
                ('source/.agents/machine/utility/peer-cli/scripts', 'source/.agents/machine/scripts'),
                ('package/.agents/machine/utility/peer-cli/scripts', 'package/resources/machine/scripts'),
                ('package/codex-skills/peer-cli/scripts', 'package/resources/machine/scripts'),
                ('package/skills/peer-cli/scripts', 'package/resources/machine/scripts'),
                ('staged', 'staged'),
            ):
                script = root / relative / 'session_close.py'
                helper = root / resource / 'cli_client.py'
                helper.parent.mkdir(parents=True, exist_ok=True)
                helper.touch()
                with self.subTest(layout=relative), mock.patch.object(close, '__file__', str(script)):
                    self.assertEqual(helper.resolve(), close.client_runtime_path())

    def test_native_thread_reattachment_preserves_its_stop_and_shared_backend_peer(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.dict(os.environ, {'AGENT_STATE_DIRECTORY': directory, 'CODEX_THREAD_ID': 'own'}):
            root = Path(directory)
            store = close.register_session._load_session_store()
            connection = store.connect()
            try:
                own = store.start_session(connection, 'codex', 'own', root, pid=100, pid_started_at=10.0)
                peer = store.start_session(connection, 'codex', 'peer', root, pid=100, pid_started_at=10.0)
                store.record_stop(connection, own, root)
                before = store.get_session(connection, own)
                sibling = store.get_session(connection, peer)
                backend = close.register_session.ProcessInfo(100, 1, 'codex.exe', 10.0)
                frontend = close.register_session.ProcessInfo(200, 1, 'codex.exe', 20.0)
                with mock.patch.object(close.os, 'getppid', return_value=100), \
                        mock.patch.object(close, 'process_info', return_value=backend), \
                        mock.patch.object(close.register_session, 'read_host_names', return_value={'codex'}), \
                        mock.patch.object(close, 'current_codex_client',
                                          return_value=(frontend, {'client_identity': 'native-resume'})):
                    entry = close.own_host_and_entry(root)
                self.assertEqual('own', entry['session_id'])
                self.assertEqual(200, entry['pid'])
                after = store.get_session(connection, own)
                self.assertEqual(200, after['pid'])
                self.assertEqual(before['last_activity_at'], after['last_activity_at'])
                self.assertEqual(before['started_at'], after['started_at'])
                self.assertEqual('awaiting_input', after['turn_state'])
                self.assertEqual(sibling, store.get_session(connection, peer))
            finally:
                connection.close()

    @unittest.skipIf(os.name == 'nt', 'POSIX npm launcher')
    def test_npm_symlink_launches_the_native_frontend_for_an_attributable_pid(self):
        import terminal_command

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / 'codex.js'
            script.touch()
            target = root / 'codex'
            target.symlink_to(script)
            with mock.patch.object(terminal_command.agent_cli, 'resolve_codex_executable',
                                   return_value=('/native/codex', '0.164.0')):
                self.assertEqual(['/native/codex', 'resume', 'own'],
                                 terminal_command.command_for_target(str(target), ['resume', 'own']))
                with mock.patch.object(terminal_command.shutil, 'which', return_value=str(target)):
                    self.assertEqual(['/native/codex', 'resume', 'own'],
                                     terminal_command.command_for_target('codex', ['resume', 'own']))

    def test_same_backend_and_checkout_resolve_only_the_current_native_thread(self):
        backend = SimpleNamespace(pid=1, name='codex.exe', started_at=10)
        own = SimpleNamespace(pid=2, name='codex.exe', started_at=20)
        peer = SimpleNamespace(pid=3, name='codex.exe', started_at=30)
        commands = {1: ['codex', 'app-server'], 2: ['codex', 'resume', 'own'], 3: ['codex', 'resume', 'peer']}
        with mock.patch.object(close, 'client_runtime', return_value=client), \
                mock.patch.dict(os.environ, {client.TOKEN_ENV: ''}), \
                mock.patch.object(client, 'process_arguments', side_effect=lambda pid: commands[pid]), \
                mock.patch.object(client, 'process_profile', return_value=client.profile_directory()), \
                mock.patch.object(close.register_session, 'process_table', return_value={1: backend, 2: own, 3: peer}):
            self.assertIs(own, close.current_codex_client('own', backend)[0])
            commands[3] = ['codex', 'resume', 'own']
            with self.assertRaisesRegex(close.Refusal, 'one Codex frontend'):
                close.current_codex_client('own', backend)

    def test_private_native_child_precedes_inherited_parent_binding(self):
        child = SimpleNamespace(pid=2, name='codex.exe', started_at=20)
        with mock.patch.object(close, 'client_runtime', return_value=client), \
                mock.patch.dict(os.environ, {client.TOKEN_ENV: 'parent'}), \
                mock.patch.object(client, 'process_arguments', return_value=['codex', 'exec', 'review']), \
                mock.patch.object(client, 'resolve') as resolve:
            self.assertIs(child, close.current_codex_client('child-thread', child)[0])
        resolve.assert_not_called()

    def test_managed_shared_backend_uses_verified_client_ticket(self):
        backend = SimpleNamespace(pid=1, name='codex.exe')
        own = SimpleNamespace(pid=2, name='codex.exe')
        record = {'launch_cwd': str(ROOT), 'terminal_environment': {}}
        with mock.patch.object(close, 'client_runtime', return_value=client), \
                mock.patch.dict(os.environ, {client.TOKEN_ENV: 'own-token'}), \
                mock.patch.object(client, 'process_arguments', return_value=['codex', 'app-server']), \
                mock.patch.object(client, 'resolve', return_value=(own, record)) as resolve:
            self.assertIs(own, close.current_codex_client('own-thread', backend)[0])
        self.assertEqual('own-token', resolve.call_args.args[0])

    def test_backend_is_never_a_close_target(self):
        entry = {'host': 'codex', 'pid': 1, 'pid_started_at': 10}
        with mock.patch.object(close, 'process_info', return_value=SimpleNamespace(name='codex.exe')), \
                mock.patch.object(close, 'verified_live', return_value=True), \
                mock.patch.object(close, 'client_runtime', return_value=client), \
                mock.patch.object(client, 'process_arguments', return_value=['codex', 'app-server']), \
                mock.patch.object(close, 'stop_verified_process') as stop:
            with self.assertRaisesRegex(close.Refusal, 'backend or maintenance'):
                close.stop_cli_client(entry)
        stop.assert_not_called()


@unittest.skipUnless(os.name == 'nt' or sys.platform == 'linux', 'Supported process identity backend')
class KernelCloseTests(unittest.TestCase):
    def test_only_the_selected_child_exits_and_checkout_survives(self):
        with tempfile.TemporaryDirectory() as directory:
            sentinel = Path(directory) / 'worktree.txt'
            sentinel.write_text('preserve', encoding='utf-8')
            children = [subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)']) for _ in range(3)]
            try:
                selected = children[1]
                info = close.process_info(selected.pid)
                self.assertIsNotNone(info)
                with self.assertRaisesRegex(close.Refusal, 'identity changed'):
                    close.stop_verified_process(selected.pid, info.started_at - 100)
                self.assertTrue(all(process.poll() is None for process in children))
                def cancelled():
                    raise close.Refusal('new prompt')
                with self.assertRaisesRegex(close.Refusal, 'new prompt'):
                    close.stop_verified_process(selected.pid, info.started_at, cancelled)
                self.assertIsNone(selected.poll())
                close.stop_verified_process(selected.pid, info.started_at)
                selected.wait(timeout=5)
                self.assertIsNone(children[0].poll(), 'shared backend must remain alive')
                self.assertIsNone(children[2].poll(), 'peer frontend must remain alive')
                self.assertEqual('preserve', sentinel.read_text(encoding='utf-8'))
            finally:
                for process in children:
                    if process.poll() is None:
                        process.kill()
                    process.wait(timeout=5)

    def test_native_metadata_reader_sees_the_exact_child_profile(self):
        with tempfile.TemporaryDirectory() as profile:
            environment = {key: value for key, value in os.environ.items() if key.casefold() != 'codex_home'}
            environment['Codex_Home' if os.name == 'nt' else 'CODEX_HOME'] = profile
            process = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'],
                                       env=environment)
            try:
                self.assertEqual(Path(profile).resolve(), client.process_profile(process.pid))
                self.assertIn('import time; time.sleep(120)', client.process_arguments(process.pid))
            finally:
                process.kill()
                process.wait(timeout=5)


if __name__ == '__main__':
    unittest.main()
