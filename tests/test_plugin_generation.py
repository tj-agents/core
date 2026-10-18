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

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / '.agents/machine/scripts'
SPEC = importlib.util.spec_from_file_location('plugin_generation', SCRIPTS / 'plugin_generation.py')
GENERATION = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GENERATION
SPEC.loader.exec_module(GENERATION)
ROLLING = sys.modules['rolling_plugins']

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
        self.environ = {
            'CLAUDE_CONFIG_DIR': str(self.claude),
            'CODEX_HOME': str(self.codex),
            'AGENT_STATE_DIRECTORY': str(base / 'state'),
        }

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')
        return path

    def install(self, host, *revisions, now=1000.0):
        plugins = self.claude / 'plugins' if host == 'claude' else self.codex / 'plugins'
        for offset, revision in enumerate(revisions):
            ROLLING.record_generations(
                plugins, host, [ROLLING.VerifiedRoot('machine@tj-agents', Path('unused'), revision, CORE)], now + offset)

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

    def receipt(self, *roots, tamper=False):
        encoded = (json.dumps({'schema_version': 1, 'roots': [str(root) for root in roots]}) + '\n').encode('utf-8')
        path = self.codex / 'plugins/cache/.tj-agents-rolling/codex/sessions/nonce/runtime-receipt.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encoded)
        digest = hashlib.sha256(encoded + (b'x' if tamper else b'')).hexdigest()
        return {GENERATION.RECEIPT_ENV: str(path), GENERATION.RECEIPT_SHA256_ENV: digest}

    def prompt(self, host, environ, session=SESSION):
        stream = io.StringIO()
        GENERATION.main(['prompt', '--host', host], dict(self.environ, **environ),
                        io.StringIO(json.dumps({'session_id': session, 'cwd': self.temp.name})), stream)
        return json.loads(stream.getvalue()) if stream.getvalue().strip() else None

    def context(self, output):
        return output['hookSpecificOutput']['additionalContext']


class CodexGenerationTests(GenerationHarness):
    def test_a_newer_install_is_reported_at_the_next_prompt_and_not_before(self):
        alias = self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A)
        environ = self.receipt(alias)
        self.install('codex', A)

        self.assertIsNone(self.prompt('codex', environ))

        self.install('codex', B, now=2000.0)
        first = self.prompt('codex', environ)
        second = self.prompt('codex', environ)

        self.assertIn(f'runs {A[:12]}, superseded by {B[:12]}', self.context(first))
        self.assertIn(f'codex resume {SESSION}', self.context(first))
        self.assertIn('task and ownership are unchanged', self.context(first))
        self.assertIn('systemMessage', first)
        self.assertIn(f'superseded by {B[:12]}', self.context(second))
        self.assertNotIn('systemMessage', second)

    def test_a_newer_install_by_the_other_host_also_supersedes(self):
        alias = self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A)
        self.install('codex', A)
        self.install('claude', B, now=3000.0)

        output = self.prompt('codex', self.receipt(alias))

        self.assertIn('for new claude sessions', self.context(output))

    def test_duplicate_aliases_at_two_revisions_are_reported_as_mixed(self):
        base = self.codex_root(f'tj-run-{SESSION}-base-agents', 'base', A)
        tj = self.codex_root(f'tj-run-{SESSION}-tj-agents', 'base', B)
        self.install('codex', A, B)

        output = self.prompt('codex', self.receipt(base, tj))

        self.assertIn('several generations at once', self.context(output))
        self.assertIn(f'base@tj-run-{SESSION}-base-agents {A[:12]}', self.context(output))

    def test_duplicate_aliases_at_the_newest_revision_are_silent(self):
        base = self.codex_root(f'tj-run-{SESSION}-base-agents', 'base', B)
        tj = self.codex_root(f'tj-run-{SESSION}-tj-agents', 'base', B)
        self.install('codex', A, B)

        self.assertIsNone(self.prompt('codex', self.receipt(base, tj)))

    def test_a_tampered_receipt_is_unverifiable_rather_than_current(self):
        alias = self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', B)
        self.install('codex', B)

        output = self.prompt('codex', self.receipt(alias, tamper=True))

        self.assertIn('failed its integrity check', self.context(output))

    def test_an_unmanaged_shared_root_is_unverifiable_rather_than_current(self):
        shared = self.codex_root('tj-agents', 'machine', B)
        self.install('codex', B)

        output = self.prompt('codex', {'PLUGIN_ROOT': str(shared)})

        self.assertIn('not launched through the tj-agents launcher', self.context(output))

    def test_an_unrecorded_revision_is_never_called_current(self):
        alias = self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', 'c' * 40)
        self.install('codex', B)

        output = self.prompt('codex', self.receipt(alias))

        self.assertIn('which no verified install recorded', self.context(output))

    def test_a_failed_refresh_records_nothing_so_the_session_is_not_told_of_it(self):
        alias = self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A)
        self.install('codex', A)
        record = ROLLING.generations_path(self.codex / 'plugins', 'codex')
        before = record.read_bytes()

        self.assertIsNone(self.prompt('codex', self.receipt(alias)))
        self.assertEqual(before, record.read_bytes())

    def test_malformed_records_cannot_become_the_newest_generation(self):
        alias = self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A)
        self.install('codex', A)
        record = ROLLING.generations_path(self.codex / 'plugins', 'codex')
        document = json.loads(record.read_text(encoding='utf-8'))
        document['installed'].append({'repository': CORE, 'revision': 'not-a-sha', 'installed_at': 9999})
        document['installed'].append({'repository': CORE, 'revision': B})
        record.write_text(json.dumps(document), encoding='utf-8')

        self.assertIsNone(self.prompt('codex', self.receipt(alias)))


class ClaudeGenerationTests(GenerationHarness):
    def registry(self, *roots):
        plugins = {f'{root.parent.name}@tj-agents': [{'scope': 'user', 'installPath': str(root)}] for root in roots}
        self.write(self.claude / 'plugins/installed_plugins.json', {'version': 2, 'plugins': plugins})

    def start(self, environ):
        GENERATION.main(['session-start', '--host', 'claude'], dict(self.environ, **environ),
                        io.StringIO(json.dumps({'session_id': SESSION, 'cwd': self.temp.name})), io.StringIO())

    def test_every_loaded_package_is_checked_after_the_registry_moves_on(self):
        machine_a, engineering_a = self.claude_root('machine', A), self.claude_root('engineering', A)
        self.registry(machine_a, engineering_a)
        self.install('claude', A)
        environ = {'CLAUDE_PLUGIN_ROOT': str(machine_a)}
        self.start(environ)
        self.assertIsNone(self.prompt('claude', environ))

        self.registry(self.claude_root('machine', B), self.claude_root('engineering', B))
        self.install('claude', B, now=2000.0)
        output = self.prompt('claude', environ)

        self.assertIn(f'runs {A[:12]}, superseded by {B[:12]}', self.context(output))
        self.assertIn('/reload-plugins', self.context(output))
        self.assertIn(f'claude --resume {SESSION}', self.context(output))

    def test_the_loaded_root_outranks_a_registry_that_moved_before_session_start(self):
        machine_a = self.claude_root('machine', A)
        self.registry(self.claude_root('machine', B))
        self.install('claude', A, B)
        environ = {'CLAUDE_PLUGIN_ROOT': str(machine_a)}

        self.start(environ)
        output = self.prompt('claude', environ)

        self.assertIn(f'runs {A[:12]}, superseded by {B[:12]}', self.context(output))
        self.assertNotIn('several generations', self.context(output))

    def test_a_reload_that_rebinds_every_package_silences_the_report(self):
        machine_a, engineering_a = self.claude_root('machine', A), self.claude_root('engineering', A)
        self.registry(machine_a, engineering_a)
        self.install('claude', A)
        self.start({'CLAUDE_PLUGIN_ROOT': str(machine_a)})
        machine_b, engineering_b = self.claude_root('machine', B), self.claude_root('engineering', B)
        self.registry(machine_b, engineering_b)
        self.install('claude', B, now=2000.0)
        self.assertIsNotNone(self.prompt('claude', {'CLAUDE_PLUGIN_ROOT': str(machine_a)}))

        self.assertIsNone(self.prompt('claude', {'CLAUDE_PLUGIN_ROOT': str(machine_b)}))

    def test_a_non_rolling_install_is_ignored(self):
        root = self.claude / 'plugins/cache/other/plugin/1.0.0'
        root.mkdir(parents=True)
        self.install('claude', A, B)

        self.assertIsNone(self.prompt('claude', {'CLAUDE_PLUGIN_ROOT': str(root)}))


class GateContractTests(GenerationHarness):
    def test_an_invalid_session_identity_produces_nothing(self):
        alias = self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A)
        self.install('codex', A, B)

        self.assertIsNone(self.prompt('codex', self.receipt(alias), session='../escape'))

    def test_an_internal_failure_reports_an_unverified_generation(self):
        original = GENERATION.check

        def broken(*_arguments):
            raise RuntimeError('synthetic failure')

        GENERATION.check = broken
        try:
            output = self.prompt('codex', {})
        finally:
            GENERATION.check = original

        self.assertIn('could not be checked (synthetic failure)', self.context(output))

    def test_the_record_keeps_a_bounded_history_per_repository(self):
        plugins = self.codex / 'plugins'
        for index in range(ROLLING.GENERATION_HISTORY + 5):
            ROLLING.record_generations(
                plugins, 'codex', [ROLLING.VerifiedRoot('machine@tj-agents', Path('unused'), f'{index:040x}', CORE)], index)
        ROLLING.record_generations(
            plugins, 'codex', [ROLLING.VerifiedRoot('machine@tj-agents', Path('unused'), f'{10:040x}', CORE)], 9999)

        entries = ROLLING.read_generations(ROLLING.generations_path(plugins, 'codex'))

        self.assertEqual(ROLLING.GENERATION_HISTORY, len(entries))
        self.assertEqual(f'{ROLLING.GENERATION_HISTORY + 4:040x}', entries[-1]['revision'])

    def test_both_hosts_dispatch_the_gate_through_their_prompt_chain(self):
        alias = self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A)
        self.install('codex', A, B)
        environment = dict(os.environ, **self.environ, **self.receipt(alias))
        completed = subprocess.run(
            [sys.executable, '-B', str(ROOT / '.agents/hooks/hook_dispatch.py'), '--deadline', '12',
             '--hook', str(SCRIPTS / 'plugin_generation.py'), 'prompt', '--host', 'codex'],
            input=json.dumps({'hook_event_name': 'UserPromptSubmit', 'session_id': SESSION}),
            capture_output=True, text=True, encoding='utf-8', env=environment, timeout=60, check=True)

        merged = json.loads(completed.stdout)

        self.assertEqual('UserPromptSubmit', merged['hookSpecificOutput']['hookEventName'])
        self.assertIn(f'superseded by {B[:12]}', merged['hookSpecificOutput']['additionalContext'])
        self.assertIn(f'superseded by {B[:12]}', merged['systemMessage'])

    def test_both_host_manifests_wire_the_gate(self):
        claude = (ROOT / '.agents/plugins/manifests/claude/machine-hooks.json').read_text(encoding='utf-8')
        codex = json.loads((ROOT / '.agents/plugins/manifests/codex/machine-hooks.json').read_text(encoding='utf-8'))
        claude_hooks = json.loads(claude)['hooks']

        for event, mode in (('SessionStart', 'session-start'), ('UserPromptSubmit', 'prompt')):
            arguments = [argument for group in claude_hooks[event] for hook in group['hooks']
                         for argument in hook.get('args', [])]
            index = arguments.index('${CLAUDE_PLUGIN_ROOT}/resources/machine/scripts/plugin_generation.py')
            self.assertEqual([mode, '--host', 'claude'], arguments[index + 1:index + 4])
        for field in ('command', 'commandWindows'):
            commands = [hook[field] for group in codex['hooks']['UserPromptSubmit'] for hook in group['hooks']]
            self.assertTrue(any('resources/machine/scripts/plugin_generation.py\\" prompt --host codex' in command
                                or 'resources/machine/scripts/plugin_generation.py" prompt --host codex' in command
                                for command in commands))


if __name__ == '__main__':
    unittest.main()
