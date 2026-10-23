"""Synthetic configuration and command doubles only; no network, CLI or scheduler is touched."""

import ast
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / '.agents/machine/scripts'
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


UPDATE = load('plugin_autoupdate')
import setup_machine as SETUP  # noqa: E402
CORE = 'https://github.com/tj-agents/core.git'
MARKET = 'https://github.com/tj-agents/marketplace.git'
OLD = 'a' * 40
NEW = 'b' * 40
PINNED = 'c' * 40


def user_config(projects=()):
    return {
        'marketplaces': {
            'direct-core': {'source_type': 'git', 'source': CORE},
            'local-only': {'source_type': 'local', 'source': 'C:/somewhere'},
            'unused': {'source_type': 'git', 'source': 'https://github.com/tj-agents/unused.git'},
        },
        'plugins': {
            'base@direct-core': {'enabled': True},
            'machine@direct-core': {'enabled': True},
            'engineering@direct-core': {'enabled': False},
            'tool@local-only': {'enabled': True},
            'kit@tj-agents': {'enabled': True},
        },
        'projects': {str(project): {'trust_level': 'trusted'} for project in projects},
    }


class Machine:
    """A synthetic CODEX_HOME with trusted projects, plugin caches and marketplace clones."""

    def __init__(self, test):
        self.temp = tempfile.TemporaryDirectory(prefix='codex home ')
        test.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / 'codex'
        self.home.mkdir()
        for patcher in (mock.patch.dict(os.environ, {'CODEX_HOME': str(self.home),
                                                     'AGENT_STATE_DIRECTORY': str(self.root / 'state')}),
                        mock.patch.object(UPDATE.tempfile, 'gettempdir', return_value=str(self.root / 'tmp'))):
            patcher.start()
            test.addCleanup(patcher.stop)

    def project(self, name, text):
        directory = self.root / name
        (directory / '.codex').mkdir(parents=True)
        (directory / '.codex' / 'config.toml').write_text(text, encoding='utf-8')
        return directory.resolve()

    def installed(self, marketplace, *plugins):
        for plugin in plugins:
            (self.home / 'plugins' / 'cache' / marketplace / plugin / 'local').mkdir(parents=True)

    def manifest(self, marketplace, entries):
        path = self.home / '.tmp' / 'marketplaces' / marketplace / '.agents' / 'plugins' / 'marketplace.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({'plugins': entries}), encoding='utf-8')


def tj_agents(ref=None, *plugins):
    pinned = f'ref = "{ref}"\n' if ref else ''
    selected = ''.join(f'[plugins."{plugin}@tj-agents"]\nenabled = true\n' for plugin in plugins)
    return f'[marketplaces.tj-agents]\nsource_type = "git"\nsource = "{MARKET}"\n{pinned}{selected}'


class DeclaredTargetTests(unittest.TestCase):
    def test_user_and_project_declarations_form_one_union_without_starting_codex(self):
        machine = Machine(self)
        docs = machine.project('docs', tj_agents(None, 'base'))
        cpp = machine.project('cpp', '[plugins."base@direct-core"]\nenabled = true\n'
                                     '[plugins."machine@direct-core"]\nenabled = false\n')
        with mock.patch.object(UPDATE.subprocess, 'Popen') as popen, \
                mock.patch.object(UPDATE.subprocess, 'run') as run:
            targets, ignored = UPDATE.declared_targets(user_config([docs, cpp]))

        popen.assert_not_called()
        run.assert_not_called()
        self.assertEqual([], ignored)
        self.assertEqual(['direct-core', 'tj-agents'], sorted(targets))
        self.assertEqual(['base@direct-core', 'machine@direct-core'], targets['direct-core']['plugins'])
        self.assertEqual(Path.home(), targets['direct-core']['project'])
        self.assertEqual(['base@tj-agents'], targets['tj-agents']['plugins'])
        self.assertEqual(docs, targets['tj-agents']['project'])

    def test_one_declaration_wins_per_marketplace_and_stale_pins_are_reported(self):
        machine = Machine(self)
        stale = machine.project('stale', tj_agents(PINNED, 'base', 'kit'))
        current = machine.project('current', tj_agents(None, 'base', 'python'))
        sandbox = machine.project('sandbox', '[marketplaces.direct-core]\nsource_type = "git"\n'
                                             f'source = "{CORE}"\nref = "{PINNED}"\n'
                                             '[plugins."base@direct-core"]\nenabled = true\n')

        targets, ignored = UPDATE.declared_targets(user_config([stale, current, sandbox]))

        self.assertIsNone(targets['tj-agents']['ref'])
        self.assertEqual(['base@tj-agents', 'python@tj-agents'], targets['tj-agents']['plugins'])
        self.assertIsNone(targets['direct-core']['ref'])
        self.assertEqual(Path.home(), targets['direct-core']['project'])
        self.assertEqual(2, len(ignored))
        self.assertTrue(any(str(stale) in line and PINNED in line for line in ignored))
        self.assertTrue(any(str(sandbox) in line for line in ignored))

    def test_the_user_configuration_listed_as_a_project_is_read_once(self):
        machine = Machine(self)
        config = user_config([machine.home.parent])
        (machine.home.parent / '.codex').mkdir()
        (machine.home.parent / '.codex' / 'config.toml').write_text('', encoding='utf-8')
        with mock.patch.dict(os.environ, {'CODEX_HOME': str(machine.home.parent / '.codex')}):
            self.assertEqual(1, len(UPDATE.declarations(config)))

    def test_projects_inside_the_temporary_directory_are_ignored(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ('kept', 'scratch'):
                (root / name / '.codex').mkdir(parents=True)
                (root / name / '.codex' / 'config.toml').write_text('', encoding='utf-8')
            config = {'projects': {str(root / 'kept'): {'trust_level': 'trusted'},
                                   str(root / 'scratch'): {'trust_level': 'trusted'}}}

            found = UPDATE.project_directories(config, temporary=root / 'scratch')

        self.assertEqual([(root / 'kept').resolve()], found)

    def test_project_discovery_requires_exact_saved_trust_and_project_configuration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ('trusted', 'untrusted', 'parent/nested'):
                (root / name / '.codex').mkdir(parents=True)
                (root / name / '.codex/config.toml').write_text('', encoding='utf-8')
            config = {'projects': {str(root / 'trusted'): {'trust_level': 'trusted'},
                                   str(root / 'untrusted'): {'trust_level': 'untrusted'},
                                   str(root / 'parent'): {'trust_level': 'trusted'}}}
            self.assertEqual([(root / 'trusted').resolve()],
                             UPDATE.project_directories(config, temporary=Path('/nonexistent-temp')))

    def test_installation_state_comes_from_the_cache_and_the_marketplace_clone(self):
        machine = Machine(self)
        machine.installed('tj-agents', 'base')
        machine.manifest('tj-agents', [
            {'name': 'base', 'source': {'source': 'git-subdir', 'url': CORE, 'ref': 'main'}},
            {'name': 'python', 'source': {'source': 'git-subdir', 'url': 'https://x/python.git', 'sha': OLD}},
            {'name': 'unselected', 'source': {'source': 'git-subdir', 'url': 'https://x/other.git'}},
        ])
        target = {'plugins': ['base@tj-agents', 'python@tj-agents']}

        UPDATE.inspect_installation('tj-agents', target)

        self.assertEqual(['python@tj-agents'], target['missing'])
        self.assertEqual([{'source': CORE, 'ref': 'main'}, {'source': 'https://x/python.git', 'ref': OLD}],
                         target['publishers'])


def target(**extra):
    return {'direct-core': {'source': CORE, 'ref': None, 'project': ROOT,
                            'plugins': ['base@direct-core', 'machine@direct-core'], **extra}}


def idle():
    return False


class RefreshTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='codex home ')
        self.addCleanup(temp.cleanup)
        patcher = mock.patch.dict(os.environ, {'CODEX_HOME': temp.name,
                                               'AGENT_STATE_DIRECTORY': str(Path(temp.name) / 'state')})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_an_unchanged_revision_runs_no_cli_command(self):
        run = mock.Mock(return_value=True)

        outcomes = UPDATE.refresh_codex('codex', target(), {'codex:direct-core': OLD},
                                        revision=lambda *_: OLD, run=run, busy=idle)

        self.assertEqual({'direct-core': 'current'}, outcomes)
        run.assert_not_called()

    def test_a_changed_revision_upgrades_then_re_adds_from_the_declaring_project(self):
        run = mock.Mock(return_value=True)
        recorded = {'codex:direct-core': OLD}

        outcomes = UPDATE.refresh_codex('codex', target(), recorded, revision=lambda *_: NEW, run=run, busy=idle)

        self.assertEqual({'direct-core': 'updated'}, outcomes)
        self.assertEqual(NEW, recorded['codex:direct-core'])
        self.assertEqual([
            mock.call(['codex', 'plugin', 'marketplace', 'upgrade', 'direct-core'], cwd=ROOT),
            mock.call(['codex', 'plugin', 'add', 'base@direct-core'], cwd=ROOT),
            mock.call(['codex', 'plugin', 'add', 'machine@direct-core'], cwd=ROOT),
        ], run.call_args_list)

    def test_only_plugins_whose_publisher_moved_are_re_added(self):
        machine_source = 'https://github.com/tj-agents/machine-source.git'
        run = mock.Mock(return_value=True)
        recorded = {'codex:direct-core': OLD, 'codex-plugin:base@direct-core': OLD}
        publishers = lambda name: {'base': (CORE, 'main', 'plugins/base'),
                                   'machine': (machine_source, 'main', 'plugins/machine')}
        targets = target(publishers=[{'source': CORE, 'ref': 'main'}, {'source': machine_source, 'ref': 'main'}])

        outcomes = UPDATE.refresh_codex('codex', targets, recorded, revision=lambda source, ref: OLD if source == CORE else NEW,
                                        run=run, busy=idle, publishers=publishers)

        self.assertEqual({'direct-core': 'updated'}, outcomes)
        self.assertEqual([
            mock.call(['codex', 'plugin', 'marketplace', 'upgrade', 'direct-core'], cwd=ROOT),
            mock.call(['codex', 'plugin', 'add', 'machine@direct-core'], cwd=ROOT),
        ], run.call_args_list)
        self.assertEqual(NEW, recorded['codex-plugin:machine@direct-core'])

    def test_a_plugin_whose_files_did_not_change_at_the_new_head_is_not_re_added(self):
        run = mock.Mock(return_value=True)
        recorded = {'codex:direct-core': OLD, 'codex-plugin:base@direct-core': OLD,
                    'codex-plugin:machine@direct-core': OLD}
        UPDATE.record_contents({}, {f'tj-agents/core@{OLD}:plugins/base': PINNED,
                                    f'tj-agents/core@{NEW}:plugins/base': PINNED}, {OLD, NEW})
        publishers = lambda name: {'base': (CORE, 'main', 'plugins/base'), 'machine': (CORE, 'main', 'plugins/machine')}

        UPDATE.refresh_codex('codex', target(publishers=[{'source': CORE, 'ref': 'main'}]), recorded,
                             revision=lambda *_: NEW, run=run, busy=idle, publishers=publishers)

        self.assertEqual([
            mock.call(['codex', 'plugin', 'marketplace', 'upgrade', 'direct-core'], cwd=ROOT),
            mock.call(['codex', 'plugin', 'add', 'machine@direct-core'], cwd=ROOT),
        ], run.call_args_list)
        self.assertEqual(NEW, recorded['codex-plugin:base@direct-core'])

    def test_a_running_codex_session_never_defers_an_upgrade(self):
        run = mock.Mock(return_value=True)
        preserve = mock.Mock()
        recorded = {'codex:direct-core': OLD}

        outcomes = UPDATE.refresh_codex('codex', target(), recorded, revision=lambda *_: NEW, run=run,
                                        busy=lambda: True, packages=lambda name: [{'snapshot_first': False}],
                                        preserve=preserve)

        self.assertTrue(outcomes['direct-core'].startswith('updated'))
        self.assertIn('restart Codex sessions', outcomes['direct-core'])
        self.assertEqual(NEW, recorded['codex:direct-core'])
        self.assertTrue(run.called)
        preserve.assert_called_once()

    def test_snapshot_first_hooks_are_preserved_then_upgraded_while_a_codex_session_runs(self):
        order = []
        hooks = [{'plugin': 'base', 'snapshot_first': True}]
        busy = mock.Mock(return_value=True)

        def run(command, cwd):
            order.append(command[2])
            return True

        outcomes = UPDATE.refresh_codex('codex', target(), {'codex:direct-core': OLD}, revision=lambda *_: NEW,
                                        run=run, busy=busy, packages=lambda name: hooks,
                                        preserve=lambda name, packages: order.append(('preserve', name, packages)))

        self.assertEqual('updated', outcomes['direct-core'])
        self.assertEqual([('preserve', 'direct-core', hooks), 'marketplace', 'add', 'add'], order)
        busy.assert_not_called()

    def test_a_running_session_keeps_its_hooks_after_the_cache_is_replaced(self):
        cache = Path(os.environ['CODEX_HOME']) / 'plugins' / 'cache' / 'tj-agents' / 'base' / 'local'
        shutil.copytree(ROOT / 'plugins' / 'base', cache)
        field = 'commandWindows' if os.name == 'nt' else 'command'
        manifest = json.loads((cache / 'hooks' / 'codex.json').read_text(encoding='utf-8'))
        command = manifest['hooks']['SessionStart'][0]['hooks'][0][field].replace('${PLUGIN_ROOT}', str(cache))
        packages = UPDATE.hook_packages('tj-agents')
        self.assertEqual([('base', cache, True)], [(p['plugin'], p['root'], p['snapshot_first']) for p in packages])

        UPDATE.preserve_hook_snapshots('tj-agents', packages)
        (cache / 'hooks' / 'codex_hook_snapshot.py').write_text("raise SystemExit('new loader')\n", encoding='utf-8')
        (cache / 'hooks' / 'hook_runtime.py').write_text("raise SystemExit('new hooks')\n", encoding='utf-8')
        data = Path(os.environ['CODEX_HOME']) / 'plugins' / 'data' / 'base-tj-agents'
        result = subprocess.run(command, shell=True, cwd=ROOT, env=dict(os.environ, PLUGIN_DATA=str(data)),
                                stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('base:idea-initialization', result.stdout)

    def test_an_unchanged_marketplace_never_asks_whether_sessions_are_running(self):
        busy = mock.Mock(return_value=True)
        UPDATE.refresh_codex('codex', target(), {'codex:direct-core': OLD}, revision=lambda *_: OLD,
                             run=mock.Mock(), busy=busy)
        busy.assert_not_called()

    def test_a_failed_refresh_keeps_the_old_revision_and_waits_a_day(self):
        recorded = {'codex:direct-core': OLD}
        failing = mock.Mock(return_value=False)

        self.assertEqual('failed', UPDATE.refresh_codex(
            'codex', target(), recorded, revision=lambda *_: NEW, run=failing, now=1000.0, busy=idle)['direct-core'])
        retry = mock.Mock(return_value=True)
        soon = UPDATE.refresh_codex('codex', target(), recorded, revision=lambda *_: NEW, run=retry, now=2000.0,
                                    busy=idle)
        self.assertEqual(OLD, recorded['codex:direct-core'])
        later = UPDATE.refresh_codex('codex', target(), recorded, revision=lambda *_: NEW, run=retry,
                                     now=1000.0 + UPDATE.FAILURE_BACKOFF_SECONDS + 1, busy=idle)

        self.assertIn('retried after 24 hours', soon['direct-core'])
        self.assertEqual('updated', later['direct-core'])
        self.assertNotIn('failed:codex:direct-core', recorded)

    def test_an_unreachable_source_changes_nothing(self):
        run = mock.Mock(return_value=True)

        outcomes = UPDATE.refresh_codex('codex', target(), {}, revision=lambda *_: None, run=run, busy=idle)

        self.assertEqual({'direct-core': 'unreachable'}, outcomes)
        run.assert_not_called()

    def test_a_retired_plugin_is_skipped_once_and_never_forces_another_refresh(self):
        targets = target(plugins=['base@direct-core', 'kit@direct-core'], missing=['kit@direct-core'])
        recorded = {}

        def run(command, cwd):
            return UPDATE.RETIRED if command[-1] == 'kit@direct-core' else True

        first = UPDATE.refresh_codex('codex', targets, recorded, revision=lambda *_: NEW, run=run, busy=idle)
        again = mock.Mock(return_value=True)
        second = UPDATE.refresh_codex('codex', targets, recorded, revision=lambda *_: NEW, run=again, busy=idle)

        self.assertTrue(first['direct-core'].startswith('updated'))
        self.assertIn('kit@direct-core', first['direct-core'])
        self.assertEqual({'direct-core': 'current'}, second)
        again.assert_not_called()

    def test_a_missing_installation_is_added_at_an_unchanged_revision(self):
        run = mock.Mock(return_value=True)
        self.assertEqual({'direct-core': 'updated'}, UPDATE.refresh_codex(
            'codex', target(missing=['base@direct-core']), {'codex:direct-core': OLD},
            revision=lambda *_: OLD, run=run, busy=idle))
        self.assertTrue(run.called)

    def test_publisher_changes_refresh_an_unchanged_umbrella_marketplace(self):
        publisher = 'https://github.com/tj-agents/python.git'
        targets = target(publishers=[{'source': publisher, 'ref': 'main'}])
        recorded = {}
        run = mock.Mock(return_value=True)
        UPDATE.refresh_codex('codex', targets, recorded, revision=lambda *_: OLD, run=run, busy=idle)
        run.reset_mock()

        self.assertEqual({'direct-core': 'current'}, UPDATE.refresh_codex(
            'codex', targets, recorded, revision=lambda *_: OLD, run=run, busy=idle))
        run.assert_not_called()
        self.assertEqual({'direct-core': 'updated'}, UPDATE.refresh_codex(
            'codex', targets, recorded, revision=lambda source, ref: NEW if source == publisher else OLD,
            run=run, busy=idle))

    def test_an_unreachable_publisher_does_not_block_the_marketplace_refresh(self):
        retired = 'https://github.com/tj-agents/retired.git'
        recorded = {}
        run = mock.Mock(return_value=True)

        self.assertEqual({'direct-core': 'updated'}, UPDATE.refresh_codex(
            'codex', target(publishers=[{'source': retired, 'ref': 'removed'}]), recorded,
            revision=lambda source, ref: None if source == retired else NEW, run=run, busy=idle))
        self.assertEqual({}, recorded)

    def test_a_pinned_reference_needs_no_network(self):
        with mock.patch.object(UPDATE.subprocess, 'run') as run:
            self.assertEqual(PINNED, UPDATE.remote_revision(CORE, PINNED.upper()))
        run.assert_not_called()


class DeclaredRefreshTests(unittest.TestCase):
    def test_a_no_change_run_over_many_projects_checks_each_source_once_and_runs_no_cli(self):
        machine = Machine(self)
        projects = [machine.project(f'repo-{index:02}', tj_agents(None, 'base')) for index in range(40)]
        machine.installed('direct-core', 'base', 'machine')
        machine.installed('tj-agents', 'base')
        revision = mock.Mock(return_value=OLD)
        recorded = {'codex:direct-core': OLD, 'codex:tj-agents': OLD,
                    'targets:C:/old': {}, 'codex:tj-agents:' + 'f' * 64: OLD}
        run = mock.Mock(return_value=True)

        with mock.patch.object(UPDATE, 'remote_revision', revision), \
                mock.patch.object(UPDATE.subprocess, 'Popen') as popen:
            started = UPDATE.time.monotonic()
            outcomes = UPDATE.refresh_declared('codex', user_config(projects), recorded, run=run, busy=idle,
                                               revision=revision)
            elapsed = UPDATE.time.monotonic() - started

        self.assertEqual({'direct-core': 'current', 'tj-agents': 'current'}, outcomes['marketplaces'])
        self.assertEqual(2, revision.call_count)
        run.assert_not_called()
        popen.assert_not_called()
        self.assertLess(elapsed, 5)
        self.assertEqual({'codex:direct-core', 'codex:tj-agents'}, set(recorded))

    def test_cleanup_keeps_per_plugin_hashes_for_still_declared_plugins(self):
        machine = Machine(self)
        docs = machine.project('docs', tj_agents(None, 'base'))
        machine.installed('direct-core', 'base', 'machine')
        machine.installed('tj-agents', 'base')
        recorded = {'codex-plugin:base@direct-core': OLD, 'codex-plugin:retired@direct-core': OLD}
        run = mock.Mock(return_value=True)

        UPDATE.refresh_declared('codex', user_config([docs]), recorded, run=run, busy=idle, revision=lambda *_: OLD)

        self.assertIn('codex-plugin:base@direct-core', recorded)
        self.assertNotIn('codex-plugin:retired@direct-core', recorded)

    def test_a_repository_filter_refreshes_only_marketplaces_that_list_or_publish_it(self):
        machine = Machine(self)
        project = machine.project('kit-user', tj_agents(None, 'kit'))
        machine.installed('direct-core', 'base', 'machine')
        machine.installed('tj-agents', 'kit')
        machine.manifest('tj-agents', [{'name': 'kit', 'source': {
            'source': 'git-subdir', 'url': 'https://github.com/tj-agents/kit.git', 'path': 'plugins/kit'}}])
        run = mock.Mock(return_value=True)
        recorded = {'codex:direct-core': OLD, 'codex:tj-agents': OLD}

        for repositories, refreshed in (({'tj-agents/kit'}, {'tj-agents'}), ({'tj-agents/core'}, {'direct-core'}),
                                        ({'tj-agents/elsewhere'}, set())):
            with self.subTest(repositories=repositories):
                outcomes = UPDATE.refresh_declared('codex', user_config([project]), dict(recorded), run=run, busy=idle,
                                                   revision=lambda *_: OLD, repositories=repositories)
                self.assertEqual(refreshed, set(outcomes['marketplaces']))

    def test_codex_writing_its_own_configuration_does_not_trigger_another_refresh(self):
        machine = Machine(self)
        docs = machine.project('docs', tj_agents(None, 'base'))
        machine.installed('tj-agents', 'base')
        machine.installed('direct-core', 'base', 'machine')
        user = machine.home / 'config.toml'
        recorded = {}

        def run(command, cwd):
            user.write_text(f'# rewritten by codex {command[-1]}\n', encoding='utf-8')
            return True

        first = UPDATE.refresh_declared('codex', user_config([docs]), recorded, run=run, busy=idle,
                                        revision=lambda *_: NEW)
        again = mock.Mock(return_value=True)
        second = UPDATE.refresh_declared('codex', user_config([docs]), recorded, run=again, busy=idle,
                                         revision=lambda *_: NEW)

        self.assertEqual({'updated'}, set(first['marketplaces'].values()))
        self.assertEqual({'current'}, set(second['marketplaces'].values()))
        again.assert_not_called()

    def test_a_plugin_declared_only_by_projects_is_removed_from_user_scope_after_codex_enables_it(self):
        machine = Machine(self)
        work = machine.project('work', tj_agents(None, 'infonetica'))
        machine.installed('tj-agents', 'infonetica')
        machine.installed('direct-core', 'base', 'machine')
        user = machine.home / 'config.toml'
        user.write_text('[plugins."base@direct-core"]\nenabled = true\n', encoding='utf-8')

        def run(command, cwd):
            if command[2] == 'add':
                user.write_text(user.read_text(encoding='utf-8') + f'\n[plugins."{command[-1]}"]\nenabled = true\n',
                                encoding='utf-8')
            return True

        first = UPDATE.refresh_declared('codex', user_config([work]), {}, run=run, busy=idle, revision=lambda *_: NEW)
        leaked = user_config([work])
        leaked['plugins']['infonetica@tj-agents'] = {'enabled': True}
        second = UPDATE.refresh_declared('codex', leaked, {}, first['project_only'], run=run, busy=idle,
                                         revision=lambda *_: NEW)

        text = user.read_text(encoding='utf-8')
        self.assertEqual(['infonetica@tj-agents'], first['project_only'])
        self.assertEqual(['infonetica@tj-agents'], second['project_only'])
        self.assertNotIn('infonetica@tj-agents', text)
        self.assertIn('[plugins."base@direct-core"]\nenabled = true', text)


class SessionDetectionTests(unittest.TestCase):
    def sessions(self, machine, rows):
        database = machine.root / 'state' / 'sessions.db'
        database.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(database)
        connection.execute('CREATE TABLE sessions (profile TEXT, pid INTEGER, ended_at REAL)')
        connection.executemany('INSERT INTO sessions VALUES (?, ?, ?)', rows)
        connection.commit()
        connection.close()

    def test_only_a_live_unended_session_of_this_codex_home_counts(self):
        machine = Machine(self)
        codex = str(machine.home)
        claude = str(machine.root / 'claude')
        self.sessions(machine, [(codex, 10, 5.0), (claude, 11, None), (codex.upper() if os.name == 'nt' else codex, 12, None)])

        self.assertTrue(UPDATE.codex_session_running(alive=lambda pid: pid == 12))
        self.assertFalse(UPDATE.codex_session_running(alive=lambda pid: pid in (10, 11)))

    def test_no_registry_means_no_running_session(self):
        Machine(self)
        self.assertFalse(UPDATE.codex_session_running(alive=lambda pid: True))

    def test_an_unreadable_registry_is_treated_as_busy(self):
        machine = Machine(self)
        database = machine.root / 'state' / 'sessions.db'
        database.parent.mkdir(parents=True)
        database.write_bytes(b'not a database')
        self.assertTrue(UPDATE.codex_session_running(alive=lambda pid: False))

    def test_the_current_process_is_alive_and_a_bogus_pid_is_not(self):
        self.assertTrue(UPDATE.process_alive(os.getpid()))
        self.assertFalse(UPDATE.process_alive(0))
        self.assertFalse(UPDATE.process_alive(True))


class ConsoleTests(unittest.TestCase):
    def test_every_child_process_starts_without_a_console_window(self):
        tree = ast.parse((SCRIPTS / 'plugin_autoupdate.py').read_text(encoding='utf-8'))
        launches = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute) and node.func.attr in ('run', 'Popen')
                    and isinstance(node.func.value, ast.Name) and node.func.value.id == 'subprocess']

        self.assertTrue(launches)
        for call in launches:
            with self.subTest(line=call.lineno):
                self.assertTrue(any(keyword.arg == 'creationflags' for keyword in call.keywords))


class LockAndSelfUpdateTests(unittest.TestCase):
    def test_a_second_run_cannot_take_a_held_lock_even_after_an_hour(self):
        with tempfile.TemporaryDirectory(prefix='autoupdate lock ') as temp:
            path = Path(temp) / 'plugin-autoupdate.lock'
            held = UPDATE.acquire_lock(path)
            self.assertIsNotNone(held)
            try:
                old = path.stat().st_mtime - 7200
                os.utime(path, (old, old))
                self.assertIsNone(UPDATE.acquire_lock(path))
            finally:
                held.close()

    def test_an_orphan_lockfile_from_the_retired_task_does_not_block_refresh(self):
        with tempfile.TemporaryDirectory(prefix='autoupdate lock ') as temp:
            path = Path(temp) / 'plugin-autoupdate.lock'
            path.write_text('', encoding='utf-8')
            held = UPDATE.acquire_lock(path)
            self.assertIsNotNone(held)
            held.close()

    def test_an_old_cache_without_the_listener_cannot_replace_the_installed_runtime(self):
        with tempfile.TemporaryDirectory(prefix='autoupdate cutover ') as temp:
            stable = Path(temp) / 'bin' / UPDATE.SCRIPT_NAME
            stable.parent.mkdir()
            stable.write_text('current updater', encoding='utf-8')
            stable.with_name('machine_events.py').write_text('current listener', encoding='utf-8')
            old = Path(temp) / 'old-package' / UPDATE.SCRIPT_NAME
            old.parent.mkdir()
            old.write_text('old updater', encoding='utf-8')
            old.with_name('machine_events.py').write_text('old listener', encoding='utf-8')
            with mock.patch.object(UPDATE, 'packaged_copies', return_value=[old]):
                self.assertFalse(UPDATE.self_update(stable, {}))
            self.assertEqual('current updater', stable.read_text(encoding='utf-8'))
            self.assertEqual('current listener', stable.with_name('machine_events.py').read_text(encoding='utf-8'))

    def test_the_stable_copy_adopts_the_newest_packaged_script(self):
        with tempfile.TemporaryDirectory(prefix='autoupdate self ') as temp:
            stable = Path(temp) / 'bin' / UPDATE.SCRIPT_NAME
            stable.parent.mkdir()
            stable.write_text('old', encoding='utf-8')
            packaged = Path(temp) / 'package' / UPDATE.SCRIPT_NAME
            packaged.parent.mkdir()
            for name in UPDATE.RUNTIME:
                packaged.with_name(name).write_text('new ' + name, encoding='utf-8')
            packaged.write_text('new', encoding='utf-8')
            stable.with_name('machine_events.py').write_text('old listener', encoding='utf-8')

            with mock.patch.object(UPDATE, 'packaged_copies', return_value=[packaged]):
                self.assertTrue(UPDATE.self_update(stable, {}))
                self.assertFalse(UPDATE.self_update(stable, {}))

            self.assertEqual('new', stable.read_text(encoding='utf-8'))
            for name in UPDATE.RUNTIME[1:]:
                self.assertEqual('new ' + name, stable.with_name(name).read_text(encoding='utf-8'))


    def test_only_enabled_installed_machine_packages_are_self_update_sources(self):
        with tempfile.TemporaryDirectory(prefix='plugin homes ') as temp:
            claude = Path(temp) / 'claude'
            (claude / 'plugins').mkdir(parents=True)
            current = Path(temp) / 'claude-cache' / 'tj-agents' / 'machine' / 'new'
            legacy = Path(temp) / 'claude-cache' / 'direct-core' / 'machine' / 'old'
            (claude / 'settings.json').write_text(json.dumps({'enabledPlugins': {
                'machine@tj-agents': True, 'machine@direct-core': False}}), encoding='utf-8')
            (claude / 'plugins' / 'installed_plugins.json').write_text(json.dumps({'plugins': {
                'machine@tj-agents': [{'installPath': str(current)}],
                'machine@direct-core': [{'installPath': str(legacy)}]}}), encoding='utf-8')
            codex = Path(temp) / 'codex'
            config = {'plugins': {'machine@direct-core': {'enabled': True},
                                  'machine@retired': {'enabled': False}}}

            with mock.patch.dict(os.environ, {'CODEX_HOME': str(codex)}):
                roots = UPDATE.installed_plugin_roots('machine', claude, config)

            self.assertEqual([current, codex / 'plugins' / 'cache' / 'direct-core' / 'machine' / 'local'], roots)


    def test_the_sweep_is_skipped_when_no_engineering_package_is_installed(self):
        with tempfile.TemporaryDirectory(prefix='plugin homes ') as temp:
            with mock.patch.dict(os.environ, {'CLAUDE_CONFIG_DIR': temp, 'CODEX_HOME': temp}):
                self.assertEqual('engineering package not installed', UPDATE.sweep_worktrees({}))


    def test_every_child_process_starts_without_a_console_window(self):
        source = (SCRIPTS / 'plugin_autoupdate.py').read_text(encoding='utf-8')
        launches = source.count('subprocess.run(') + source.count('subprocess.Popen(')

        self.assertEqual(launches, source.count('creationflags=NO_WINDOW'))
        if os.name == 'nt':
            self.assertEqual(UPDATE.subprocess.CREATE_NO_WINDOW, UPDATE.NO_WINDOW)

    def test_the_sweep_runs_under_a_console_interpreter_when_scheduled_windowless(self):
        with tempfile.TemporaryDirectory(prefix='python dir ') as temp:
            pythonw = Path(temp) / 'pythonw.exe'
            console = Path(temp) / 'python.exe'
            pythonw.write_text('', encoding='utf-8')
            console.write_text('', encoding='utf-8')

            with mock.patch.object(UPDATE.sys, 'executable', str(pythonw)):
                self.assertEqual(str(console), UPDATE.console_python())


class SetupTests(unittest.TestCase):
    def test_claude_auto_update_is_enabled_only_for_marketplaces_of_enabled_plugins(self):
        with tempfile.TemporaryDirectory(prefix='claude config ') as temp:
            config = Path(temp)
            (config / 'plugins').mkdir()
            (config / 'settings.json').write_text(json.dumps({'enabledPlugins': {
                'base@tj-agents': True, 'old@legacy': False}}), encoding='utf-8')
            known = config / 'plugins' / 'known_marketplaces.json'
            known.write_text(json.dumps({
                'tj-agents': {'autoUpdate': False}, 'legacy': {'autoUpdate': False}}), encoding='utf-8')

            self.assertEqual(['tj-agents'], SETUP.enable_claude_autoupdate(config))
            self.assertEqual([], SETUP.enable_claude_autoupdate(config))

            saved = json.loads(known.read_text(encoding='utf-8'))
            self.assertTrue(saved['tj-agents']['autoUpdate'])
            self.assertFalse(saved['legacy']['autoUpdate'])

    def test_launchers_replace_retired_blocks_keep_other_lines_and_are_idempotent(self):
        with tempfile.TemporaryDirectory(prefix='profile ü ') as temp:
            profile = Path(temp) / 'Microsoft.PowerShell_profile.ps1'
            original = (b'\xef\xbb\xbf' + (
                "$env:Path = 'x'\r\n"
                "# >>> base-agents claude launcher >>>\r\nfunction global:claude {}\r\n"
                "# <<< base-agents claude launcher <<<\r\n"
                "# >>> base-agents codex launcher >>>\r\nfunction global:codex {}\r\n"
                "# <<< base-agents codex launcher <<<\r\n"
                ". 'accounts.ps1'\r\n").encode('utf-8'))
            profile.write_bytes(original)
            script = Path(temp) / "it's bin" / 'launch_check.py'

            self.assertEqual([profile], SETUP.install_shell_profiles([profile], 'C:/Python/python.exe', script))
            installed = profile.read_bytes()
            self.assertEqual([], SETUP.install_shell_profiles([profile], 'C:/Python/python.exe', script))
            self.assertEqual(installed, profile.read_bytes())

            self.assertTrue(installed.startswith(b'\xef\xbb\xbf'))
            text = installed[3:].decode('utf-8')
            self.assertTrue(text.startswith("$env:Path = 'x'\r\n. 'accounts.ps1'\r\n\r\n" + SETUP.PROFILE_START + '\r\n'))
            self.assertTrue(text.endswith(SETUP.PROFILE_END + '\r\n'))
            self.assertNotIn('base-agents', text)
            self.assertNotIn('\n', text.replace('\r\n', ''))
            self.assertIn("it''s bin", text)
            self.assertEqual(original, profile.with_name(profile.name + '.pre-tj-agents.bak').read_bytes())

            self.assertEqual([profile], SETUP.install_shell_profiles([profile], 'C:/Python314/python.exe', script))
            moved = profile.read_bytes()[3:].decode('utf-8')
            self.assertEqual(1, moved.count(SETUP.PROFILE_START))
            self.assertIn('Python314', moved)
            self.assertNotIn("'C:/Python/python.exe'", moved)

    def test_only_existing_profiles_change_and_the_first_is_created_when_none_exist(self):
        with tempfile.TemporaryDirectory(prefix='profile ') as temp:
            bashrc, zshrc = Path(temp) / '.bashrc', Path(temp) / '.zshrc'
            self.assertEqual([bashrc], SETUP.install_shell_profiles([bashrc, zshrc], '/usr/bin/python3', Path('/s.py')))
            self.assertFalse(zshrc.exists())
            zshrc.write_text('export A=1', encoding='utf-8')
            self.assertEqual([zshrc], SETUP.install_shell_profiles([bashrc, zshrc], '/usr/bin/python3', Path('/s.py')))
            self.assertEqual('export A=1\n\n' + SETUP.posix_block('/usr/bin/python3', Path('/s.py')) + '\n',
                             zshrc.read_text(encoding='utf-8'))
            self.assertFalse(bashrc.with_name('.bashrc.pre-tj-agents.bak').exists())



if __name__ == '__main__':
    unittest.main()
