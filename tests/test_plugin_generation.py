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
import time
import unittest

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
        self.state = base / 'state'
        self.environ = {
            'CLAUDE_CONFIG_DIR': str(self.claude),
            'CODEX_HOME': str(self.codex),
            'AGENT_STATE_DIRECTORY': str(self.state),
        }

    def write(self, path, value, encoding='utf-8'):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding=encoding)
        return path

    def install(self, host, *revisions, now=1000.0):
        plugins = self.claude / 'plugins' if host == 'claude' else self.codex / 'plugins'
        for offset, revision in enumerate(revisions):
            self.verify(RECORD.generations_path(plugins, host), [(CORE, revision)], now + offset)

    def verify(self, record, revisions, now):
        self.write(record, RECORD.merged_generations(RECORD.read_generations(record), revisions, now))

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
        GENERATION.main(['prompt', '--host', host], dict(self.environ, **environ),
                        io.StringIO(json.dumps({'session_id': session, 'cwd': self.temp.name})), stream)
        return json.loads(stream.getvalue()) if stream.getvalue().strip() else None

    def context(self, output):
        return output['hookSpecificOutput']['additionalContext']


class CodexGenerationTests(GenerationHarness):
    def test_a_newer_verified_generation_is_reported_at_the_next_prompt_and_not_before(self):
        environ = self.receipt(self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A))
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

    def test_a_newer_verification_by_the_other_host_also_supersedes(self):
        environ = self.receipt(self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A))
        self.install('codex', A)
        self.install('claude', B, now=3000.0)

        self.assertIn(f'superseded by {B[:12]}', self.context(self.prompt('codex', environ)))

    def test_the_most_recent_verification_decides_the_newest_generation(self):
        environ = self.receipt(self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', B))
        self.install('codex', A, B)
        self.install('claude', A, now=5000.0)

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
        record = RECORD.generations_path(self.codex / 'plugins', 'codex')
        document = json.loads(record.read_text(encoding='utf-8'))
        document['verified'].append({'repository': CORE, 'revision': 'not-a-sha', 'verified_at': 9999})
        document['verified'].append({'repository': CORE, 'revision': B})
        record.write_text(json.dumps(document), encoding='utf-8')

        self.assertIsNone(self.prompt('codex', environ))


class ClaudeGenerationTests(GenerationHarness):
    def registry(self, *roots, updated='2026-10-19T00:00:00Z', stale=(), encoding='utf-8'):
        plugins = {f'{root.parent.name}@tj-agents': [{'scope': 'user', 'installPath': str(root), 'lastUpdated': updated}]
                   for root in roots}
        plugins.update({f'{root.parent.name}@tj-agents': [{'scope': 'user', 'installPath': str(root),
                                                           'lastUpdated': '2026-01-01T00:00:00Z'}]
                        for root in stale})
        self.write(self.claude / 'plugins/installed_plugins.json', {'version': 2, 'plugins': plugins}, encoding)

    def start(self, environ, source='startup'):
        GENERATION.main(['session-start', '--host', 'claude'], dict(self.environ, **environ),
                        io.StringIO(json.dumps({'session_id': SESSION, 'cwd': self.temp.name, 'source': source})),
                        io.StringIO())

    def test_a_resumed_process_takes_a_fresh_snapshot_but_a_compaction_keeps_it(self):
        other = 'https://github.com/tj-agents/dotnet.git'
        machine_a = self.claude_root('machine', A)
        self.registry(machine_a, self.claude_root('dotnet', A, other))
        self.install('claude', A)
        self.verify(RECORD.generations_path(self.claude / 'plugins', 'claude'), [(other, A)], 1000.0)
        environ = {'CLAUDE_PLUGIN_ROOT': str(machine_a)}
        self.start(environ)
        self.registry(machine_a, self.claude_root('dotnet', B, other), updated='later')
        self.verify(RECORD.generations_path(self.claude / 'plugins', 'claude'), [(other, B)], 2000.0)

        self.start(environ, source='compact')
        self.assertIn(f'runs {A[:12]}, superseded by {B[:12]}', self.context(self.prompt('claude', environ)))

        self.start(environ, source='resume')
        self.assertIsNone(self.prompt('claude', environ))

    def test_an_install_record_without_a_launch_time_says_so(self):
        machine_a = self.claude_root('machine', A)
        self.write(self.claude / 'plugins/installed_plugins.json', {'version': 2, 'plugins': {
            'machine@tj-agents': [{'scope': 'user', 'installPath': str(machine_a)}],
            'engineering@tj-agents': [{'scope': 'user', 'installPath': str(self.claude_root('engineering', A))}]}})
        self.install('claude', A)

        output = self.prompt('claude', {'CLAUDE_PLUGIN_ROOT': str(machine_a)})

        self.assertIn('no launch time', self.context(output))

    def test_a_failing_snapshot_never_stops_a_session_starting(self):
        original = GENERATION.claude_records

        def broken(*_arguments):
            raise OSError('registry on an unavailable drive')

        GENERATION.claude_records = broken
        try:
            self.start({'CLAUDE_PLUGIN_ROOT': str(self.claude_root('machine', A))})
        finally:
            GENERATION.claude_records = original

    def test_every_package_of_the_binding_launch_is_checked_after_a_newer_verification(self):
        machine_a, engineering_a = self.claude_root('machine', A), self.claude_root('engineering', A)
        self.registry(machine_a, engineering_a, encoding='utf-8-sig')
        self.install('claude', A)
        environ = {'CLAUDE_PLUGIN_ROOT': str(machine_a)}
        self.start(environ)
        self.assertIsNone(self.prompt('claude', environ))

        self.registry(self.claude_root('machine', B), self.claude_root('engineering', B), updated='later')
        self.install('claude', B, now=2000.0)
        output = self.prompt('claude', environ)

        self.assertIn(f'runs {A[:12]}, superseded by {B[:12]}', self.context(output))
        self.assertIn('/reload-plugins', self.context(output))
        self.assertIn(f'claude --resume {SESSION}', self.context(output))

    def test_a_package_left_behind_by_an_earlier_launch_is_not_counted_as_loaded(self):
        machine_b = self.claude_root('machine', B)
        self.registry(machine_b, stale=(self.claude_root('engineering', A),))
        self.install('claude', A, B)
        environ = {'CLAUDE_PLUGIN_ROOT': str(machine_b)}

        self.start(environ)

        self.assertIsNone(self.prompt('claude', environ))

    def test_the_loaded_root_outranks_a_registry_that_moved_before_session_start(self):
        machine_a = self.claude_root('machine', A)
        self.registry(self.claude_root('machine', B))
        self.install('claude', A, B)
        environ = {'CLAUDE_PLUGIN_ROOT': str(machine_a)}

        self.start(environ)
        output = self.prompt('claude', environ)

        self.assertIn(f'runs {A[:12]}, superseded by {B[:12]}', self.context(output))
        self.assertNotIn('several generations', self.context(output))

    def test_a_repeated_session_start_keeps_the_packages_it_bound(self):
        machine_a, engineering_a = self.claude_root('machine', A), self.claude_root('engineering', A)
        self.registry(machine_a, engineering_a)
        self.install('claude', A)
        environ = {'CLAUDE_PLUGIN_ROOT': str(machine_a)}
        self.start(environ)

        self.registry(self.claude_root('machine', B), self.claude_root('engineering', B), updated='later')
        self.install('claude', B, now=2000.0)
        self.start(environ, source='compact')
        output = self.prompt('claude', environ)

        stored = json.loads((self.state / 'plugin-generation' / f'claude-{SESSION}.json').read_text(encoding='utf-8'))
        self.assertEqual(sorted([str(machine_a), str(engineering_a)]), stored['roots'])
        self.assertNotIn('other tj-agents packages are unknown', self.context(output))
        self.assertIn(f'runs {A[:12]}, superseded by {B[:12]}', self.context(output))

    def test_a_session_whose_install_left_the_registry_reports_its_unknown_packages(self):
        machine_a = self.claude_root('machine', A)
        self.registry(self.claude_root('machine', B), self.claude_root('engineering', B))
        self.install('claude', A, B)

        output = self.prompt('claude', {'CLAUDE_PLUGIN_ROOT': str(machine_a)})

        self.assertIn('other tj-agents packages are unknown', self.context(output))

    def test_a_reload_that_rebinds_the_session_silences_the_report(self):
        machine_a, engineering_a = self.claude_root('machine', A), self.claude_root('engineering', A)
        self.registry(machine_a, engineering_a)
        self.install('claude', A)
        self.start({'CLAUDE_PLUGIN_ROOT': str(machine_a)})
        machine_b, engineering_b = self.claude_root('machine', B), self.claude_root('engineering', B)
        self.registry(machine_b, engineering_b, updated='later')
        self.install('claude', B, now=2000.0)
        self.assertIsNotNone(self.prompt('claude', {'CLAUDE_PLUGIN_ROOT': str(machine_a)}))

        self.assertIsNone(self.prompt('claude', {'CLAUDE_PLUGIN_ROOT': str(machine_b)}))

    def test_a_superseded_non_rolling_install_is_still_reported(self):
        loaded = self.claude / 'plugins/cache/market/machine/1.0.0'
        installed = self.claude / 'plugins/cache/market/machine/1.1.0'
        loaded.mkdir(parents=True)
        installed.mkdir(parents=True)
        self.write(self.claude / 'plugins/installed_plugins.json', {'version': 2, 'plugins': {
            'machine@market': [{'scope': 'user', 'installPath': str(installed)}]}})

        output = self.prompt('claude', {'CLAUDE_PLUGIN_ROOT': str(loaded)})

        self.assertIn('this process loaded 1.0.0, but 1.1.0 is installed', self.context(output))

    def test_a_current_non_rolling_install_is_ignored(self):
        root = self.claude / 'plugins/cache/other/plugin/1.0.0'
        root.mkdir(parents=True)
        self.write(self.claude / 'plugins/installed_plugins.json', {'version': 2, 'plugins': {
            'plugin@other': [{'scope': 'user', 'installPath': str(root)}]}})
        self.install('claude', A, B)

        self.assertIsNone(self.prompt('claude', {'CLAUDE_PLUGIN_ROOT': str(root)}))


class GateContractTests(GenerationHarness):
    def test_an_invalid_session_identity_produces_nothing(self):
        environ = self.receipt(self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A))
        self.install('codex', A, B)

        self.assertIsNone(self.prompt('codex', environ, session='../escape'))

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
        record = RECORD.generations_path(self.codex / 'plugins', 'codex')
        for index in range(RECORD.GENERATION_HISTORY + 5):
            self.verify(record, [(CORE, f'{index:040x}')], index)

        entries = RECORD.read_generations(record)

        self.assertEqual(RECORD.GENERATION_HISTORY, len(entries))
        self.assertEqual(f'{RECORD.GENERATION_HISTORY + 4:040x}', entries[-1]['revision'])

    def test_reverifying_the_newest_revision_does_not_repeat_the_user_notice(self):
        environ = self.receipt(self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A))
        self.install('codex', A, B)
        self.assertIn('systemMessage', self.prompt('codex', environ))

        self.install('claude', B, now=9000.0)
        self.install('codex', B, now=9500.0)
        output = self.prompt('codex', environ)

        self.assertIn(f'superseded by {B[:12]}', self.context(output))
        self.assertNotIn('systemMessage', output)

    def test_a_supersession_that_returns_after_a_rollback_is_announced_again(self):
        environ = self.receipt(self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A))
        self.install('codex', A, B)
        self.assertIn('systemMessage', self.prompt('codex', environ))
        self.install('codex', A, now=3000.0)
        self.assertIsNone(self.prompt('codex', environ))

        self.install('codex', B, now=4000.0)

        self.assertIn('systemMessage', self.prompt('codex', environ))

    def test_a_vanished_unmanaged_root_does_not_invalidate_the_receipt(self):
        alias = self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A)
        self.install('codex', A, B)

        output = self.prompt('codex', self.receipt(alias, unmanaged=(self.codex / 'plugins/cache/other/gone/1.0',)))

        self.assertIn(f'superseded by {B[:12]}', self.context(output))
        self.assertNotIn('receipt', self.context(output).split('. Codex cannot')[0])

    def test_an_unchanged_live_session_keeps_its_state_alive(self):
        environ = self.receipt(self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A))
        self.install('codex', A, B)
        self.prompt('codex', environ)
        state = self.state / 'plugin-generation' / f'codex-{SESSION}.json'
        old = time.time() - GENERATION.STATE_RETENTION_SECONDS - 60
        os.utime(state, (old, old))

        self.prompt('codex', environ)

        self.assertLess(time.time() - state.stat().st_mtime, 60)

    def test_session_state_expires_after_its_retention(self):
        stale = self.state / 'plugin-generation' / 'codex-stale.json'
        self.write(stale, {'notified': 'old'})
        old = time.time() - GENERATION.STATE_RETENTION_SECONDS - 60
        os.utime(stale, (old, old))
        environ = self.receipt(self.codex_root(f'tj-run-{SESSION}-tj-agents', 'machine', A))
        self.install('codex', A, B)

        self.prompt('codex', environ)

        self.assertFalse(stale.exists())
        self.assertTrue((self.state / 'plugin-generation' / f'codex-{SESSION}.json').exists())

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
        claude = json.loads((ROOT / '.agents/plugins/manifests/claude/machine-hooks.json').read_text(encoding='utf-8'))
        codex = json.loads((ROOT / '.agents/plugins/manifests/codex/machine-hooks.json').read_text(encoding='utf-8'))

        for event, mode in (('SessionStart', 'session-start'), ('UserPromptSubmit', 'prompt')):
            arguments = [argument for group in claude['hooks'][event] for hook in group['hooks']
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
