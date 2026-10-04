"""Synthetic Claude profiles and local git remotes only; the normal profile is never read."""
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
SPEC = importlib.util.spec_from_file_location(
    'claude_standards_sync', ROOT / '.agents/machine/scripts/claude_standards_sync.py'
)
SYNC = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SYNC
SPEC.loader.exec_module(SYNC)
FAKE_CLAUDE = ROOT / 'tests/fixtures/fake_claude.py'


def git(cwd, *arguments):
    return subprocess.run(
        ['git', '-c', 'user.name=test', '-c', 'user.email=test@example.invalid', *arguments],
        cwd=cwd, check=True, capture_output=True, text=True,
    ).stdout.strip()


class StandardsSyncHarness(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='claude standards sync ')
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.config = base / 'profile' / '.claude'
        self.plugins = self.config / 'plugins'
        self.state = base / 'state'
        self.project = base / 'project with spaces'
        self.project.mkdir(parents=True)
        self.log = base / 'claude.log'
        self.remote = base / 'remote.git'
        self.author = base / 'author'
        git(base, 'init', '--quiet', '--bare', '--initial-branch=main', str(self.remote))
        git(base, 'clone', '--quiet', str(self.remote), str(self.author))
        self.publish('first')
        self.checkout = self.plugins / 'marketplaces' / 'core'
        git(base, 'clone', '--quiet', str(self.remote), str(self.checkout))
        self.write(self.plugins / 'known_marketplaces.json', {
            'core': {'source': {'source': 'git', 'url': str(self.remote)}, 'installLocation': str(self.checkout)},
        })
        self.write(self.plugins / 'installed_plugins.json', {'version': 2, 'plugins': {}})
        self.enable({'base@core': True})
        self.executable = self.fake_executable(base)
        environment = {
            'CLAUDE_CONFIG_DIR': str(self.config),
            'FAKE_CLAUDE_LOG': str(self.log),
            SYNC.STATE_DIRECTORY_ENV: str(self.state),
        }
        previous = {name: os.environ.get(name) for name in [*environment, 'FAKE_CLAUDE_FAIL']}
        os.environ.update(environment)
        os.environ.pop('FAKE_CLAUDE_FAIL', None)
        self.addCleanup(self.restore, previous)

    @staticmethod
    def restore(previous):
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    @staticmethod
    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2), encoding='utf-8')

    def fake_executable(self, base):
        if os.name == 'nt':
            path = base / 'fake claude.cmd'
            path.write_text(f'@"{sys.executable}" -B "{FAKE_CLAUDE}" %*\r\n', encoding='utf-8')
        else:
            path = base / 'fake claude'
            path.write_text(f'#!/bin/sh\nexec "{sys.executable}" -B "{FAKE_CLAUDE}" "$@"\n', encoding='utf-8')
            path.chmod(0o755)
        return str(path)

    def publish(self, content):
        payload = self.author / 'plugins' / 'base' / 'payload.txt'
        payload.parent.mkdir(parents=True, exist_ok=True)
        payload.write_text(content, encoding='utf-8')
        git(self.author, 'add', '-A')
        git(self.author, 'commit', '--quiet', '-m', content)
        git(self.author, 'push', '--quiet', 'origin', 'HEAD:main')
        return git(self.author, 'rev-parse', 'HEAD')

    def enable(self, values, path=None):
        self.write(path or self.config / 'settings.json', {'enabledPlugins': values})

    def install(self, identity='base@core', scope='user', project=None, version=None):
        if version is None:
            version = git(self.checkout, 'rev-parse', 'HEAD')[:12]
        name, marketplace = identity.split('@')
        path = self.plugins / 'cache' / marketplace / name / version
        path.mkdir(parents=True, exist_ok=True)
        registry = json.loads((self.plugins / 'installed_plugins.json').read_text(encoding='utf-8'))
        record = {'scope': scope, 'installPath': str(path), 'version': version}
        if project is not None:
            record['projectPath'] = str(project)
        registry['plugins'].setdefault(identity, []).append(record)
        self.write(self.plugins / 'installed_plugins.json', registry)
        return path

    def records(self, identity='base@core'):
        return json.loads((self.plugins / 'installed_plugins.json').read_text(encoding='utf-8'))['plugins'][identity]

    def invocations(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding='utf-8').splitlines()]

    def sync(self, check=False, lock_wait=5):
        out = io.StringIO()
        code = SYNC.synchronize(self.config, self.plugins, self.project, self.state, self.executable, check, out, lock_wait)
        return code, out.getvalue()


class StandardsSyncTests(StandardsSyncHarness):
    def test_current_install_makes_no_host_call(self):
        self.install()
        code, output = self.sync()
        self.assertEqual((code, output), (0, ''))
        self.assertEqual(self.invocations(), [])

    def test_remote_push_updates_before_launch_and_keeps_loaded_directory(self):
        loaded = self.install()
        pushed = self.publish('second')
        code, output = self.sync()
        self.assertEqual(code, 0, output)
        self.assertEqual(
            [entry['argv'] for entry in self.invocations()],
            [['plugin', 'marketplace', 'update', 'core'], ['plugin', 'update', 'base@core', '--scope', 'user', '--json']],
        )
        self.assertEqual(self.records()[0]['version'], pushed[:12])
        self.assertIn(f'core at {pushed[:12]}: base {pushed[:12]}', output)
        self.assertTrue((loaded / '.orphaned_at').is_file())
        self.assertEqual(self.sync(), (0, ''))
        self.assertEqual(len(self.invocations()), 2)

    def test_stale_install_behind_current_marketplace_is_updated(self):
        self.install()
        pushed = self.publish('second')
        git(self.checkout, 'pull', '--quiet', '--ff-only')
        code, output = self.sync()
        self.assertEqual(code, 0, output)
        self.assertEqual([entry['argv'][:2] for entry in self.invocations()], [['plugin', 'update']])
        self.assertEqual(self.records()[0]['version'], pushed[:12])

    def test_unreachable_remote_warns_and_leaves_installed_version(self):
        self.install()
        git(self.checkout, 'remote', 'set-url', 'origin', str(Path(self.temp.name) / 'missing.git'))
        code, output = self.sync()
        self.assertEqual(code, 1)
        self.assertIn('could not check core', output)
        self.assertIn('this session loads base', output)
        self.assertEqual(self.invocations(), [])

    def test_disabled_plugin_is_not_refreshed(self):
        self.install()
        self.publish('second')
        self.enable({'base@core': True})
        self.enable({'base@core': False}, self.project / '.claude' / 'settings.local.json')
        self.assertEqual(self.sync(), (0, ''))
        self.assertEqual(self.invocations(), [])

    def test_project_install_updates_only_in_its_own_project(self):
        other = Path(self.temp.name) / 'other project'
        other.mkdir()
        self.install(scope='project', project=other)
        self.install(scope='project', project=self.project)
        pushed = self.publish('second')
        code, output = self.sync()
        self.assertEqual(code, 0, output)
        updates = [entry for entry in self.invocations() if entry['argv'][:2] == ['plugin', 'update']]
        self.assertEqual(len(updates), 1)
        self.assertEqual(os.path.normcase(updates[0]['cwd']), os.path.normcase(str(self.project)))
        self.assertIn(f'core at {pushed[:12]}: base {pushed[:12]} (project)', output)
        versions = {record['projectPath']: record['version'] for record in self.records()}
        self.assertEqual(versions[str(self.project)], pushed[:12])
        self.assertNotEqual(versions[str(other)], pushed[:12])

    def test_failed_update_is_reported_and_retried_next_launch(self):
        self.install()
        self.publish('second')
        os.environ['FAKE_CLAUDE_FAIL'] = 'base@core'
        code, output = self.sync()
        self.assertEqual(code, 1)
        self.assertIn('base@core (user) was not updated (command needs acceptance)', output)
        os.environ.pop('FAKE_CLAUDE_FAIL')
        code, output = self.sync()
        self.assertEqual(code, 0, output)
        self.assertEqual(self.invocations()[-1]['argv'][:3], ['plugin', 'update', 'base@core'])

    def test_failed_marketplace_refresh_skips_plugin_updates(self):
        self.install()
        self.publish('second')
        os.environ['FAKE_CLAUDE_FAIL'] = 'core'
        code, output = self.sync()
        self.assertEqual(code, 1)
        self.assertIn('core was not refreshed (Failed to refresh marketplace)', output)
        self.assertEqual([entry['argv'][:2] for entry in self.invocations()], [['plugin', 'marketplace']])

    def test_check_reports_without_changing_anything(self):
        self.install()
        pushed = self.publish('second')
        code, output = self.sync(check=True)
        self.assertEqual(code, 1)
        self.assertIn(f'core needs a refresh to {pushed[:12]}', output)
        self.assertEqual(self.invocations(), [])

    def test_pinned_tag_tracks_the_tag_not_the_branch(self):
        self.install()
        git(self.author, 'tag', 'v1')
        git(self.author, 'push', '--quiet', 'origin', 'v1')
        self.write(self.plugins / 'known_marketplaces.json', {
            'core': {'source': {'source': 'git', 'url': str(self.remote), 'ref': 'v1'}, 'installLocation': str(self.checkout)},
        })
        self.publish('second')
        self.assertEqual(self.sync(), (0, ''))
        self.assertEqual(self.invocations(), [])

    def test_unregistered_or_directory_marketplace_is_left_to_the_host(self):
        self.install()
        self.publish('second')
        self.write(self.plugins / 'known_marketplaces.json', {
            'core': {'source': {'source': 'directory', 'path': str(self.author)}, 'installLocation': str(self.author)},
        })
        self.assertEqual(self.sync(), (0, ''))
        self.write(self.plugins / 'known_marketplaces.json', {})
        self.assertEqual(self.sync(), (0, ''))
        self.assertEqual(self.invocations(), [])

    def test_downloaded_marketplace_inside_a_git_managed_profile_is_left_to_the_host(self):
        self.install('tool@official')
        self.enable({'tool@official': True})
        git(self.config, 'init', '--quiet')
        git(self.config, 'commit', '--quiet', '--allow-empty', '-m', 'profile')
        downloaded = self.plugins / 'marketplaces' / 'official'
        downloaded.mkdir(parents=True)
        (downloaded / '.gcs-sha').write_text('0' * 40, encoding='utf-8')
        self.write(self.plugins / 'known_marketplaces.json', {
            'official': {'source': {'source': 'github', 'repo': 'example/official'}, 'installLocation': str(downloaded)},
        })
        self.assertEqual(self.sync(), (0, ''))
        self.assertEqual(self.invocations(), [])

    def test_concurrent_launch_waits_for_the_update_lock(self):
        self.install()
        self.publish('second')
        self.state.mkdir(parents=True)
        (self.state / SYNC.LOCK_FILE).write_text('1', encoding='utf-8')
        code, output = self.sync(lock_wait=0)
        self.assertEqual(code, 1)
        self.assertIn('another launch is still updating plugins', output)
        self.assertEqual(self.invocations(), [])
        stale = time.time() - SYNC.STALE_LOCK_SECONDS - 60
        os.utime(self.state / SYNC.LOCK_FILE, (stale, stale))
        code, output = self.sync(lock_wait=0)
        self.assertEqual(code, 0, output)
        self.assertFalse((self.state / SYNC.LOCK_FILE).exists())

    def test_lock_is_renewed_before_every_host_call(self):
        self.install()
        self.publish('second')
        os.environ['FAKE_CLAUDE_AGE_LOCK'] = str(self.state / SYNC.LOCK_FILE)
        self.addCleanup(os.environ.pop, 'FAKE_CLAUDE_AGE_LOCK', None)
        code, output = self.sync()
        self.assertEqual(code, 0, output)
        ages = [entry['lock_age'] for entry in self.invocations()]
        self.assertEqual(len(ages), 2)
        self.assertTrue(all(age < SYNC.STALE_LOCK_SECONDS for age in ages), ages)

    def test_command_line_runs_against_the_configured_profile(self):
        self.install()
        pushed = self.publish('second')
        completed = subprocess.run(
            [sys.executable, '-B', str(ROOT / '.agents/machine/scripts/claude_standards_sync.py'),
             '--project', str(self.project), '--claude', self.executable],
            capture_output=True, text=True, env=os.environ.copy(),
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(self.records()[0]['version'], pushed[:12])


class ExternalPluginSourceTests(StandardsSyncHarness):
    """The marketplace's git-subdir plugins can source a different repository than the marketplace
    itself; the sync must track that source, not the marketplace's own remote."""

    def setUp(self):
        super().setUp()
        base = Path(self.temp.name)
        self.plugin_remote = base / 'plugin-source.git'
        self.plugin_author = base / 'plugin author'
        git(base, 'init', '--quiet', '--bare', '--initial-branch=main', str(self.plugin_remote))
        git(base, 'clone', '--quiet', str(self.plugin_remote), str(self.plugin_author))
        self.plugin_head = self.publish_plugin('first')
        self.declare_sources({'ext': str(self.plugin_remote)})
        self.enable({'ext@core': True})

    def declare_sources(self, plugins):
        self.write(self.checkout / '.claude-plugin' / 'marketplace.json', {
            'name': 'core',
            'plugins': [
                {'name': name, 'source': {'source': 'git-subdir', 'url': url, 'path': f'./plugins/{name}', 'ref': 'main'}}
                for name, url in plugins.items()
            ],
        })

    def publish_plugin(self, content, author=None):
        author = author or self.plugin_author
        payload = author / 'payload.txt'
        payload.write_text(content, encoding='utf-8')
        git(author, 'add', '-A')
        git(author, 'commit', '--quiet', '-m', content)
        git(author, 'push', '--quiet', 'origin', 'HEAD:main')
        return git(author, 'rev-parse', 'HEAD')

    def test_plugin_source_outside_the_marketplace_repository_is_tracked_independently(self):
        self.install('ext@core', version=self.plugin_head[:12])
        pushed = self.publish_plugin('second')
        code, output = self.sync()
        self.assertEqual(code, 0, output)
        self.assertEqual(
            [entry['argv'] for entry in self.invocations()],
            [['plugin', 'update', 'ext@core', '--scope', 'user', '--json']],
        )
        self.assertEqual(self.records('ext@core')[0]['version'], pushed[:12])
        self.assertIn(f'at {pushed[:12]}: ext {pushed[:12]}', output)

    def test_plugin_source_shaped_differently_but_same_repository_is_tracked_as_native(self):
        differently_shaped = str(self.remote)[:-4] + '/'
        self.declare_sources({'base': differently_shaped, 'ext': str(self.plugin_remote)})
        self.enable({'base@core': True, 'ext@core': True})
        self.install('base@core')
        pushed = self.publish('second')
        code, output = self.sync()
        self.assertEqual(code, 0, output)
        self.assertEqual(
            [entry['argv'] for entry in self.invocations()],
            [['plugin', 'marketplace', 'update', 'core'], ['plugin', 'update', 'base@core', '--scope', 'user', '--json']],
        )
        self.assertEqual(self.records('base@core')[0]['version'], pushed[:12])

    def test_unchanged_plugin_source_outside_the_marketplace_is_silent(self):
        self.install('ext@core', version=self.plugin_head[:12])
        code, output = self.sync()
        self.assertEqual((code, output), (0, ''))
        self.assertEqual(self.invocations(), [])

    def test_unreachable_plugin_source_warns_and_continues(self):
        self.install('ext@core', version=self.plugin_head[:12])
        self.declare_sources({'ext': str(Path(self.temp.name) / 'missing-plugin.git')})
        code, output = self.sync()
        self.assertEqual(code, 1)
        self.assertIn('could not check', output)
        self.assertIn('this session loads ext', output)
        self.assertEqual(self.invocations(), [])

    def test_shared_external_source_is_probed_once_for_all_its_plugins(self):
        self.declare_sources({'ext': str(self.plugin_remote), 'ext2': str(self.plugin_remote)})
        self.enable({'ext@core': True, 'ext2@core': True})
        self.install('ext@core', version=self.plugin_head[:12])
        self.install('ext2@core', version=self.plugin_head[:12])
        pushed = self.publish_plugin('second')
        probes = []
        original = SYNC.run
        def counting(command, cwd=None, timeout=SYNC.REMOTE_TIMEOUT_SECONDS):
            if len(command) > 1 and command[1] == 'ls-remote' and str(self.plugin_remote) in command:
                probes.append(command)
            return original(command, cwd=cwd, timeout=timeout)
        SYNC.run = counting
        try:
            code, output = self.sync()
        finally:
            SYNC.run = original
        self.assertEqual(code, 0, output)
        self.assertEqual(len(probes), 1, probes)
        self.assertEqual(
            sorted(entry['argv'] for entry in self.invocations()),
            [
                ['plugin', 'update', 'ext2@core', '--scope', 'user', '--json'],
                ['plugin', 'update', 'ext@core', '--scope', 'user', '--json'],
            ],
        )
        self.assertEqual(self.records('ext@core')[0]['version'], pushed[:12])
        self.assertEqual(self.records('ext2@core')[0]['version'], pushed[:12])

if __name__ == '__main__':
    unittest.main()
