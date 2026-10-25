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


class ClientMetadataTests(unittest.TestCase):
    def test_a_new_input_on_the_same_frontend_prevents_signalling_the_old_thread(self):
        entry = {'host': 'codex', 'pid': 123, 'pid_started_at': 10, 'client_identity': 'managed-input',
                 'recording_path': 'events.jsonl', 'client_message_id': 'old-input', 'profile': str(ROOT),
                 'backend': {'pid': 1, 'process_start_time': 'native-start'}}
        def stop(pid, started_at, before_signal):
            before_signal()
            self.fail('A new frontend input must prevent the signal')
        with mock.patch.object(close, 'process_info', return_value=SimpleNamespace(name='codex.exe')), \
                mock.patch.object(close, 'verified_live', return_value=True), \
                mock.patch.object(close, 'client_runtime', return_value=client), \
                mock.patch.object(client, 'process_arguments', return_value=['codex']), \
                mock.patch.object(client, 'process_context', return_value={
                    'profile': str(ROOT), client.RECORD_PATH_ENV: 'events.jsonl'}), \
                mock.patch.object(client, 'daemon_identity', return_value=entry['backend']), \
                mock.patch.object(client, 'latest_input', return_value='new-thread-input'), \
                mock.patch.object(close, 'stop_verified_process', side_effect=stop):
            with self.assertRaisesRegex(close.Refusal, 'binding changed'):
                close.stop_cli_client(entry)

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
                                          return_value=(frontend, {'client_identity': 'managed-input'})):
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
            code = 'import time; print("ready", flush=True); time.sleep(120)'
            process = subprocess.Popen([sys.executable, '-c', code, 'sentinel ü'], env=environment,
                                       stdout=subprocess.PIPE, text=True, encoding='utf-8')
            try:
                self.assertEqual('ready', process.stdout.readline().strip())
                self.assertEqual(Path(profile).resolve(), client.process_profile(process.pid))
                self.assertIn(code, client.process_arguments(process.pid))
                self.assertIn('sentinel ü', client.process_arguments(process.pid))
            finally:
                process.kill()
                process.wait(timeout=5)
                process.stdout.close()



if __name__ == '__main__':
    unittest.main()
