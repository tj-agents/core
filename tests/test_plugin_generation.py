"""Synthetic host profiles only; no real Claude or Codex configuration is read."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / '.agents/machine/scripts'
SPEC = importlib.util.spec_from_file_location('plugin_generation_under_test', SCRIPTS / 'plugin_generation.py')
GENERATION = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GENERATION
SPEC.loader.exec_module(GENERATION)
RECORD = sys.modules['generation_record']

CORE = 'https://github.com/tj-agents/core.git'
A = 'a' * 40
B = 'b' * 40
SESSION = 'd0affffee0995d0898222ed71d806c73'


class GenerationHarness(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic plugin generation ')
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.claude = base / '.claude'
        self.codex = base / '.codex'
        self.environ = {'CLAUDE_CONFIG_DIR': str(self.claude), 'CODEX_HOME': str(self.codex)}

    def write(self, path, value, encoding='utf-8'):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding=encoding)
        return path

    def record(self, host):
        return RECORD.generations_path((self.claude if host == 'claude' else self.codex) / 'plugins', host)

    def install(self, host, *revisions, now=1000.0):
        record = self.record(host)
        for offset, revision in enumerate(revisions):
            self.write(record, RECORD.merged_generations(RECORD.read_generations(record) or [], [(CORE, revision)],
                                                         now + offset))

    def codex_root(self, marketplace, plugin, revision, repository=CORE):
        root = self.codex / 'plugins/cache' / marketplace / plugin / 'local'
        root.mkdir(parents=True, exist_ok=True)
        self.write(root.parent / '.tj-agents-rolling.json', {
            'schema_version': 1, 'identity': f'{plugin}@{marketplace}', 'repository': repository,
            'revision': revision})
        return root

    def claude_root(self, plugin, revision, repository=CORE):
        root = self.claude / 'plugins/cache/tj-agents' / plugin / revision
        root.mkdir(parents=True, exist_ok=True)
        self.write(root.parent / '.tj-agents-rolling.json', {
            'schema_version': 1, 'identity': f'{plugin}@tj-agents', 'repository': repository, 'revision': revision})
        return root

    def receipt(self, *roots, tamper=False, home=None, unmanaged=(), catalog=None):
        session = self.codex / 'plugins/cache/.tj-agents-rolling/codex/sessions/nonce'
        (session / 'catalog').mkdir(parents=True, exist_ok=True)
        payload = {'schema_version': 1, 'codex_home': str(home or self.codex),
                   'catalog': str(catalog or session / 'catalog'), 'roots': [str(root) for root in roots],
                   'unmanaged_roots': [str(root) for root in unmanaged]}
        encoded = (json.dumps(payload) + '\n').encode('utf-8')
        path = session / 'runtime-receipt.json'
        path.write_bytes(encoded)
        digest = hashlib.sha256(encoded + (b'x' if tamper else b'')).hexdigest()
        return {GENERATION.RECEIPT_ENV: str(path), GENERATION.RECEIPT_SHA256_ENV: digest}

    def prompt(self, host, environ, session=SESSION):
        stream = io.StringIO()
        GENERATION.main(['--host', host], dict(self.environ, **environ),
                        io.StringIO(json.dumps({'session_id': session})), stream)
        return json.loads(stream.getvalue()) if stream.getvalue().strip() else None

    def context(self, output):
        return output['hookSpecificOutput']['additionalContext']


class CodexGenerationTests(GenerationHarness):
    def test_a_newer_verified_generation_is_stated_at_every_prompt_after_it_lands(self):
        environ = self.receipt(self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A))
        self.install('codex', A)

        self.assertIsNone(self.prompt('codex', environ))

        self.install('codex', B, now=2000.0)
        for _ in range(2):
            output = self.prompt('codex', environ)
            self.assertIn(f'runs {A[:12]}, superseded by {B[:12]}', self.context(output))
            self.assertIn(f'superseded by {B[:12]}', output['systemMessage'])
        self.assertIn(f'codex resume {SESSION}', self.context(output))
        self.assertIn('task and ownership are unchanged', self.context(output))

    def test_only_this_hosts_verified_installs_supersede_its_sessions(self):
        environ = self.receipt(self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A))
        self.install('codex', A)
        self.install('claude', B, now=3000.0)

        self.assertIsNone(self.prompt('codex', environ))

    def test_the_other_hosts_bad_record_does_not_disable_this_hosts_gate(self):
        environ = self.receipt(self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A))
        self.install('codex', A, B)
        self.write(self.record('claude'), '{')

        self.assertIn(f'superseded by {B[:12]}', self.context(self.prompt('codex', environ)))

    def test_the_most_recent_verification_decides_the_newest_generation(self):
        environ = self.receipt(self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', B))
        self.install('codex', A, B)
        self.install('codex', A, now=5000.0)

        self.assertIn(f'runs {B[:12]}, superseded by {A[:12]}', self.context(self.prompt('codex', environ)))

    def test_duplicate_aliases_at_two_revisions_are_reported_as_mixed(self):
        environ = self.receipt(self.codex_root(f'tj-run-{SESSION}-base-agents', 'base', A),
                               self.codex_root(f'tj-run-{SESSION}-tj-agents', 'base', B))
        self.install('codex', A, B)

        output = self.prompt('codex', environ)

        self.assertIn('several generations at once', self.context(output))
        self.assertIn(f'base@tj-run-{SESSION}-base-agents {A[:12]}', self.context(output))

    def test_duplicate_aliases_at_the_newest_revision_are_silent(self):
        environ = self.receipt(self.codex_root(f'tj-run-{SESSION}-base-agents', 'base', B),
                               self.codex_root(f'tj-run-{SESSION}-tj-agents', 'base', B))
        self.install('codex', A, B)

        self.assertIsNone(self.prompt('codex', environ))

    def test_an_invalid_receipt_is_unverifiable_rather_than_current(self):
        alias = self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', B)
        shared = self.codex_root('tj-agents', 'machine', B)
        self.install('codex', B)
        cases = {
            'failed its integrity check': lambda: self.receipt(alias, tamper=True),
            'names another Codex home': lambda: self.receipt(alias, home=Path(self.temp.name) / 'elsewhere'),
            'outside the runtime cache layout': lambda: self.receipt(shared),
            'names another catalog': lambda: self.receipt(alias, catalog=self.codex),
        }
        for message, receipt in cases.items():
            with self.subTest(message=message):
                self.assertIn(message, self.context(self.prompt('codex', receipt())))

    def test_an_unmanaged_tj_agents_root_in_the_receipt_is_unverifiable(self):
        alias = self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', B)
        shared = self.codex_root('tj-agents', 'dotnet', B)
        self.install('codex', B)

        output = self.prompt('codex', self.receipt(alias, unmanaged=(shared,)))

        self.assertIn('dotnet@tj-agents has no verifiable generation', self.context(output))

    def test_a_vanished_unmanaged_root_does_not_invalidate_the_receipt(self):
        alias = self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A)
        self.install('codex', A, B)

        output = self.prompt('codex', self.receipt(alias, unmanaged=(self.codex / 'plugins/cache/other/gone/1.0',)))

        self.assertIn(f'superseded by {B[:12]}', self.context(output))
        self.assertNotIn('receipt', self.context(output).split('. Codex cannot')[0])

    def test_a_session_without_the_launcher_is_unverifiable_rather_than_current(self):
        shared = self.codex_root('tj-agents', 'machine', B)
        self.install('codex', B)

        for variable in GENERATION.CODEX_ROOT_VARIABLES:
            with self.subTest(variable=variable):
                output = self.prompt('codex', {variable: str(shared)})
                self.assertIn('not launched through the tj-agents launcher', self.context(output))
        self.assertIn('neither a Codex runtime receipt nor a plugin root', self.context(self.prompt('codex', {})))

    def test_an_unrecorded_revision_is_never_called_current(self):
        environ = self.receipt(self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', 'c' * 40))
        self.install('codex', B)

        self.assertIn('which no verified install recorded', self.context(self.prompt('codex', environ)))

    def test_malformed_records_cannot_become_the_newest_generation(self):
        environ = self.receipt(self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A))
        self.install('codex', A)
        document = json.loads(self.record('codex').read_text(encoding='utf-8'))
        document['verified'].append({'repository': CORE, 'revision': 'not-a-sha', 'verified_at': 9999})
        document['verified'].append({'repository': CORE, 'revision': B})
        self.write(self.record('codex'), document)

        self.assertIsNone(self.prompt('codex', environ))

    def test_a_busy_or_corrupt_record_skips_history_but_still_reports_binding_problems(self):
        shared = self.codex_root('tj-agents', 'machine', A)
        alias = self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A)
        self.install('codex', A, B)
        cases = {
            'busy': lambda: mock.patch.object(GENERATION, 'read_generations', return_value=None),
            'corrupt': lambda: mock.patch.object(GENERATION, 'read_generations',
                                                 side_effect=lambda path: RECORD.read_generations(
                                                     self.write(path, '{'))),
        }
        for name, disturbance in cases.items():
            with self.subTest(record=name), disturbance():
                self.assertIsNone(self.prompt('codex', self.receipt(alias)))
                problem = self.prompt('codex', {'PLUGIN_ROOT': str(shared)})
                self.assertIn('not launched through the tj-agents launcher', self.context(problem))
                self.assertIn('not launched through the tj-agents launcher', problem['systemMessage'])


class ClaudeGenerationTests(GenerationHarness):
    def registry(self, *records):
        plugins = {}
        for root, scope in records:
            plugins.setdefault(f'{root.parent.name}@{root.parent.parent.name}', []).append(
                {'scope': scope, 'installPath': str(root)})
        self.write(self.claude / 'plugins/installed_plugins.json', {'version': 2, 'plugins': plugins},
                   encoding='utf-8-sig')

    def test_the_loaded_root_is_reported_once_a_newer_generation_is_verified(self):
        machine_a = self.claude_root('machine', A)
        self.install('claude', A)
        environ = {'CLAUDE_PLUGIN_ROOT': str(machine_a)}
        self.assertIsNone(self.prompt('claude', environ))

        self.registry((self.claude_root('machine', B), 'user'))
        self.install('claude', B, now=2000.0)
        output = self.prompt('claude', environ)

        self.assertIn(f'runs {A[:12]}, superseded by {B[:12]}', self.context(output))
        self.assertIn('/reload-plugins', self.context(output))
        self.assertIn(f'claude --resume {SESSION}', self.context(output))

    def test_a_reload_onto_the_newest_root_silences_the_report(self):
        machine_a = self.claude_root('machine', A)
        self.install('claude', A, B)
        self.assertIsNotNone(self.prompt('claude', {'CLAUDE_PLUGIN_ROOT': str(machine_a)}))

        self.assertIsNone(self.prompt('claude', {'CLAUDE_PLUGIN_ROOT': str(self.claude_root('machine', B))}))

    def test_an_install_directory_without_a_revision_is_unverifiable(self):
        root = self.claude / 'plugins/cache/tj-agents/machine/unknown'
        root.mkdir(parents=True)
        self.write(root.parent / '.tj-agents-rolling.json', {
            'schema_version': 1, 'identity': 'machine@tj-agents', 'repository': CORE, 'revision': B})
        self.install('claude', B)

        output = self.prompt('claude', {'CLAUDE_PLUGIN_ROOT': str(root)})

        self.assertIn('does not name a verified revision', self.context(output))

    def test_a_superseded_non_rolling_install_is_still_reported(self):
        loaded = self.claude / 'plugins/cache/market/machine/1.0.0'
        loaded.mkdir(parents=True)
        installed = self.claude / 'plugins/cache/market/machine/1.1.0'
        installed.mkdir(parents=True)
        self.registry((installed, 'user'))

        output = self.prompt('claude', {'CLAUDE_PLUGIN_ROOT': str(loaded)})

        self.assertIn('this process loaded 1.0.0, but 1.1.0 is installed', self.context(output))

    def test_a_non_rolling_root_still_named_by_any_registry_record_is_current(self):
        loaded = self.claude / 'plugins/cache/market/machine/1.0.0'
        loaded.mkdir(parents=True)
        newer = self.claude / 'plugins/cache/market/machine/1.1.0'
        newer.mkdir(parents=True)
        for scope in ('project', 'local', 'managed'):
            with self.subTest(scope=scope):
                self.registry((newer, 'user'), (loaded, scope))
                self.assertIsNone(self.prompt('claude', {'CLAUDE_PLUGIN_ROOT': str(loaded)}))

    def test_a_current_non_rolling_install_is_ignored(self):
        root = self.claude / 'plugins/cache/other/plugin/1.0.0'
        root.mkdir(parents=True)
        self.registry((root, 'user'))
        self.install('claude', A, B)

        self.assertIsNone(self.prompt('claude', {'CLAUDE_PLUGIN_ROOT': str(root)}))


class GateContractTests(GenerationHarness):
    def test_an_invalid_session_identity_produces_nothing(self):
        environ = self.receipt(self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A))
        self.install('codex', A, B)

        self.assertIsNone(self.prompt('codex', environ, session='../escape'))

    def test_an_internal_failure_reports_an_unverified_generation(self):
        with mock.patch.object(GENERATION, 'check', side_effect=RuntimeError('synthetic failure')):
            output = self.prompt('codex', {})

        self.assertIn('could not be checked (synthetic failure)', self.context(output))

    def test_the_record_keeps_a_bounded_history_per_repository(self):
        entries = []
        for index in range(RECORD.GENERATION_HISTORY + 5):
            entries = RECORD.merged_generations(entries, [(CORE, f'{index:040x}')], index)['verified']

        self.assertEqual(RECORD.GENERATION_HISTORY, len(entries))
        self.assertEqual(f'{RECORD.GENERATION_HISTORY + 4:040x}', entries[-1]['revision'])

    def test_a_record_reads_missing_and_corrupt_as_empty_and_unreadable_as_unknown(self):
        record = self.record('codex')
        self.assertEqual([], RECORD.read_generations(record))
        self.write(record, '{')
        self.assertEqual([], RECORD.read_generations(record))
        with mock.patch.object(Path, 'read_text', side_effect=PermissionError('in use')):
            self.assertIsNone(RECORD.read_generations(record))

    def test_both_hosts_dispatch_the_gate_through_their_prompt_chain(self):
        alias = self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A)
        self.install('codex', A, B)
        environment = dict(os.environ, **self.environ, **self.receipt(alias))
        completed = subprocess.run(
            [sys.executable, '-B', str(ROOT / '.agents/hooks/hook_dispatch.py'), '--deadline', '12',
             '--hook', str(SCRIPTS / 'plugin_generation.py'), '--host', 'codex'],
            input=json.dumps({'hook_event_name': 'UserPromptSubmit', 'session_id': SESSION}),
            capture_output=True, text=True, encoding='utf-8', env=environment, timeout=60, check=True)

        merged = json.loads(completed.stdout)

        self.assertEqual('UserPromptSubmit', merged['hookSpecificOutput']['hookEventName'])
        self.assertIn(f'superseded by {B[:12]}', merged['hookSpecificOutput']['additionalContext'])
        self.assertIn(f'superseded by {B[:12]}', merged['systemMessage'])

    def test_both_host_manifests_wire_the_gate(self):
        claude = json.loads((ROOT / '.agents/plugins/manifests/claude/machine-hooks.json').read_text(encoding='utf-8'))
        codex = json.loads((ROOT / '.agents/plugins/manifests/codex/machine-hooks.json').read_text(encoding='utf-8'))

        arguments = [argument for group in claude['hooks']['UserPromptSubmit'] for hook in group['hooks']
                     for argument in hook.get('args', [])]
        index = arguments.index('${CLAUDE_PLUGIN_ROOT}/resources/machine/scripts/plugin_generation.py')
        self.assertEqual(['--host', 'claude'], arguments[index + 1:index + 3])
        for field in ('command', 'commandWindows'):
            commands = [hook[field] for group in codex['hooks']['UserPromptSubmit'] for hook in group['hooks']]
            self.assertTrue(any('resources/machine/scripts/plugin_generation.py" --host codex' in command
                                for command in commands))


if __name__ == '__main__':
    unittest.main()
