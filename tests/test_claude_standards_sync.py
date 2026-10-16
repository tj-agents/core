"""Synthetic Claude profiles and local git remotes only; the normal profile is never read."""
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'claude_standards_sync', ROOT / '.agents/machine/scripts/claude_standards_sync.py'
)
SYNC = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SYNC
SPEC.loader.exec_module(SYNC)
FAKE_CLAUDE = ROOT / 'tests/fixtures/fake_claude.py'


class NormalizeUrlTests(unittest.TestCase):
    def test_folds_scheme_host_case_and_git_suffix_but_not_path_case(self):
        self.assertEqual(SYNC.normalize_url('HTTPS://GitHub.com/tj-agents/Cpp.git'), 'github.com/tj-agents/Cpp')
        self.assertEqual(SYNC.normalize_url('https://github.com/tj-agents/cpp.git/'), SYNC.normalize_url('https://github.com/tj-agents/cpp'))
        self.assertNotEqual(
            SYNC.normalize_url('https://git.example.com/Org/RepoA.git'),
            SYNC.normalize_url('https://git.example.com/Org/repoa.git'),
        )

    def test_folds_scp_style_ssh_remotes_to_the_same_form_as_https(self):
        self.assertEqual(SYNC.normalize_url('git@github.com:tj-agents/cpp.git'), SYNC.normalize_url('https://github.com/tj-agents/cpp.git'))
        self.assertEqual(SYNC.normalize_url('ssh://git@github.com/tj-agents/cpp.git'), SYNC.normalize_url('https://github.com/tj-agents/cpp.git'))

    def test_repository_authentication_rejects_a_lookalike_host(self):
        self.assertFalse(SYNC.source_matches_repository(
            {'source': 'git', 'url': 'https://evil.example/tj-agents/core.git'}, 'tj-agents/core'
        ))



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
        recorded_commit = None
        if version is None:
            version = git(self.checkout, 'rev-parse', 'HEAD')[:12]
            recorded_commit = git(self.checkout, 'rev-parse', 'HEAD')
        name, marketplace = identity.split('@')
        path = self.plugins / 'cache' / marketplace / name / version
        (path / '.claude-plugin').mkdir(parents=True, exist_ok=True)
        (path / 'skills' / 'fixture').mkdir(parents=True, exist_ok=True)
        (path / 'hooks').mkdir(parents=True, exist_ok=True)
        (path / '.claude-plugin' / 'plugin.json').write_text(
            json.dumps({'name': name, 'skills': './skills', 'hooks': './hooks/claude.json'}), encoding='utf-8'
        )
        (path / 'skills' / 'fixture' / 'SKILL.md').write_text('fixture\n', encoding='utf-8')
        (path / 'hooks' / 'claude.json').write_text(json.dumps({'hooks': {}}), encoding='utf-8')
        (path / 'harness.json').write_text(json.dumps({'requires': {'hooks': []}}), encoding='utf-8')
        registry = json.loads((self.plugins / 'installed_plugins.json').read_text(encoding='utf-8'))
        record = {
            'scope': scope,
            'installPath': str(path),
            'version': version,
        }
        if recorded_commit:
            record['gitCommitSha'] = recorded_commit
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





if __name__ == '__main__':
    unittest.main()
