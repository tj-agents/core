import copy
import json
import os
import shutil
import stat
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.agents/machine/utility/bootstrap-capabilities/scripts'))
import bootstrap_capabilities as bootstrap
import compose_catalog as composer
import repo_config


class CatalogCompositionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.checkout = Path(self.temporary.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.test')
        self.git('remote', 'add', 'origin', 'https://github.com/example/capabilities.git')
        self.write_json('.claude-plugin/marketplace.json', {'name': 'example', 'plugins': [
            {'name': name, 'source': f'./plugins/{name}'} for name in ('base', 'extra')]})
        self.write_json('.agents/plugins/marketplace.json', {'name': 'example', 'plugins': [
            {'name': name, 'source': {'source': 'local', 'path': f'./plugins/{name}'}} for name in ('base', 'extra')]})
        for name, version, dependencies in (('base', '1.2.3', []), ('extra', '4.5.6', ['example/base'])):
            root = f'plugins/{name}/'
            native = {'name': name, 'version': version, 'description': f'{name} capabilities', 'skills': './skills/'}
            for host in ('codex', 'claude'):
                self.write_json(root + f'.{host}-plugin/plugin.json', native)
            self.write_json(root + 'harness.json', {'schema_version': 1, 'plugin': f'example/{name}', 'requires': {
                'marketplaces': [{'id': 'example', 'repository': 'example/capabilities'}],
                'plugins': [f'example/{name}', *dependencies],
                'hooks': [{'path': 'hooks/entry.py', 'hosts': ['codex', 'claude']}],
                'permissions': {'claude_allow': [], 'codex_prefix_rules': []}}})
            self.write_json(root + 'selection.json', {'plugin': name, 'prerequisites': [value.split('/')[1] for value in dependencies],
                                                       'skills': [{'name': 'sample', 'requires': ['library-not-a-plugin']}]})
            self.write(root + 'hooks/entry.py', b'raise RuntimeError("must never execute")\n')
            self.write(root + 'skills/sample/SKILL.md', b'---\nname: sample\n---\nfixture\n')
            self.write(root + 'binary.dat', bytes(range(256)))
        self.commit()

    def git(self, *arguments, data=None):
        result = subprocess.run(['git', '-C', str(self.checkout), *arguments], input=data,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return result.stdout.decode('utf-8').strip()

    def write(self, relative, data):
        path = self.checkout / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def write_json(self, relative, value):
        self.write(relative, json.dumps(value).encode('utf-8'))

    def change_json(self, relative, mutate):
        path = self.checkout / relative
        value = json.loads(path.read_text(encoding='utf-8'))
        mutate(value)
        self.write_json(relative, value)

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'Fixture snapshot')
        self.revision = self.git('rev-parse', 'HEAD')

    def document(self):
        return {'schema_version': 1, 'sources': [{'repository': 'example/capabilities', 'checkout': str(self.checkout),
                                                'commit': self.revision, 'plugins': ['extra', 'base'], 'version_plugin': 'base'}]}

    def compose(self):
        return composer.compose_catalog(self.document(), 'linux')

    def test_versions_anchor_digest_and_dirty_worktree_independence(self):
        catalog = self.compose()
        release = catalog['releases'][0]
        self.assertEqual((release['id'], release['revision']), ('example@1.2.3', self.revision))
        self.assertEqual([plugin['version'] for plugin in release['plugins']], ['1.2.3', '4.5.6'])
        for plugin in release['plugins']:
            self.assertEqual(plugin['digest'], bootstrap.tree_digest(self.checkout / plugin['package_path'], []))
            self.assertEqual(plugin['skills'], ['sample'])
            self.assertNotIn('_release', plugin)
        self.write('plugins/base/binary.dat', b'dirty')
        self.write('plugins/extra/skills/rogue/SKILL.md', b'untracked')
        (self.checkout / 'plugins/base/harness.json').unlink()
        self.assertEqual(self.compose(), catalog)

    def test_rejects_noncommit_objects_and_abbreviations(self):
        self.git('tag', '-a', 'fixture-tag', '-m', 'Annotated')
        for revision in (self.git('rev-parse', 'HEAD^{tree}'), self.git('rev-parse', 'refs/tags/fixture-tag'), self.revision[:8], self.revision.upper()):
            with self.subTest(revision=revision):
                document = self.document()
                document['sources'][0]['commit'] = revision
                with self.assertRaises(bootstrap.BootstrapError):
                    composer.compose_catalog(document, 'linux')

    def test_rejects_wrong_origin_without_leaking_credentials(self):
        self.git('remote', 'set-url', 'origin', 'https://secret:password@github.com/wrong/repo.git')
        with self.assertRaises(bootstrap.BootstrapError) as caught:
            self.compose()
        self.assertNotIn('secret', str(caught.exception))
        self.assertNotIn('password', str(caught.exception))

    def test_missing_and_contradictory_contracts_fail(self):
        cases = [
            ('plugins/base/harness.json', None),
            ('plugins/base/.codex-plugin/plugin.json', lambda value: value.update(name='wrong')),
            ('plugins/base/.claude-plugin/plugin.json', lambda value: value.update(version='9.9.9')),
            ('plugins/base/harness.json', lambda value: value.update(plugin='wrong/base')),
            ('.agents/plugins/marketplace.json', lambda value: value.update(name='wrong')),
            ('.claude-plugin/marketplace.json', lambda value: value['plugins'][0].update(source='../elsewhere')),
            ('plugins/base/harness.json', lambda value: value['requires']['hooks'][0].update(path='../outside')),
            ('plugins/base/harness.json', lambda value: value['requires']['marketplaces'][0].update(repository='wrong/repo')),
            ('plugins/extra/selection.json', lambda value: value.update(prerequisites=[])),
        ]
        original = self.revision
        for path, mutate in cases:
            with self.subTest(path=path, mutate=mutate):
                self.git('reset', '--hard', original)
                if mutate is None:
                    (self.checkout / path).unlink()
                else:
                    self.change_json(path, mutate)
                self.commit()
                with self.assertRaises(bootstrap.BootstrapError):
                    self.compose()

    def test_unknown_dependencies_and_cycles_fail(self):
        original = self.revision
        for target in ('example/missing', 'example/extra'):
            with self.subTest(target=target):
                self.git('reset', '--hard', original)
                self.change_json('plugins/base/harness.json', lambda value: value['requires'].update(plugins=['example/base', target]))
                self.change_json('plugins/base/selection.json', lambda value: value.update(prerequisites=[target.split('/')[1]]))
                self.commit()
                with self.assertRaisesRegex(bootstrap.BootstrapError, 'unknown dependency|cycle'):
                    self.compose()

    def test_git_symlink_payload_is_rejected(self):
        oid = self.git('hash-object', '-w', '--stdin', data=b'../../../outside')
        self.git('update-index', '--add', '--cacheinfo', f'120000,{oid},plugins/base/escape')
        self.git('commit', '-qm', 'Linked fixture')
        self.revision = self.git('rev-parse', 'HEAD')
        with self.assertRaisesRegex(bootstrap.BootstrapError, 'linked'):
            self.compose()

    def test_cli_prints_catalog_and_failure_emits_no_catalog(self):
        request = self.checkout / 'sources.json'
        request.write_text(json.dumps(self.document()), encoding='utf-8')
        script = ROOT / '.agents/machine/utility/bootstrap-capabilities/scripts/compose_catalog.py'
        command = [sys.executable, '-B', str(script), '--input', str(request), '--platform', 'linux']
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), self.compose())
        document = self.document()
        document['sources'][0]['commit'] = self.revision[:8]
        request.write_text(json.dumps(document), encoding='utf-8')
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, '')

    def test_gitlink_payload_is_rejected(self):
        self.git('update-index', '--add', '--cacheinfo', f'160000,{self.revision},plugins/base/nested')
        self.git('commit', '-qm', 'Gitlink fixture')
        self.revision = self.git('rev-parse', 'HEAD')
        with self.assertRaisesRegex(bootstrap.BootstrapError, 'linked'):
            self.compose()

    def test_catalog_v1_rejects_prerelease_and_build_versions(self):
        original = self.revision
        for version in ('1.2.3-rc.1', '1.2.3+build.4'):
            with self.subTest(version=version):
                self.git('reset', '--hard', original)
                for host in ('codex', 'claude'):
                    self.change_json(f'plugins/base/.{host}-plugin/plugin.json', lambda value: value.update(version=version))
                self.commit()
                with self.assertRaisesRegex(bootstrap.BootstrapError, 'catalog v1 N.N.N'):
                    self.compose()

    def test_local_harness_names_are_consumable_by_repository_declarations(self):
        names = ('base', 'engineering', 'machine')
        for name in names[1:]:
            shutil.copytree(self.checkout / 'plugins/extra', self.checkout / f'plugins/{name}')
        for host in ('claude', 'codex'):
            entries = [{'name': name, 'source': f'./plugins/{name}' if host == 'claude' else
                        {'source': 'local', 'path': f'./plugins/{name}'}} for name in names]
            path = '.claude-plugin/marketplace.json' if host == 'claude' else '.agents/plugins/marketplace.json'
            self.write_json(path, {'name': 'base-agents', 'plugins': entries})
        for name in names:
            for host in ('codex', 'claude'):
                self.change_json(f'plugins/{name}/.{host}-plugin/plugin.json', lambda value: value.update(name=name))
            self.change_json(f'plugins/{name}/selection.json', lambda value: value.update(plugin=name))
            self.change_json(f'plugins/{name}/harness.json', lambda value: value.update(
                plugin=f'base-agents/{name}', requires={**value['requires'],
                    'marketplaces': [{'id': 'base-agents', 'repository': 'example/capabilities'}],
                    'plugins': [name] if name == 'base' else [name, 'base']}))
        self.commit()
        document = self.document()
        document['sources'][0]['plugins'] = list(names)
        original_harness = (self.checkout / 'plugins/engineering/harness.json').read_bytes()
        catalog = composer.compose_catalog(document, 'linux')
        release = catalog['releases'][0]
        engineering = next(plugin for plugin in release['plugins'] if plugin['name'] == 'engineering')
        self.assertEqual(engineering['harness']['plugins'], ['base-agents/base', 'base-agents/engineering'])
        self.assertEqual(engineering['dependencies']['required'], ['base-agents/base'])
        self.assertEqual((self.checkout / 'plugins/engineering/harness.json').read_bytes(), original_harness)
        lock = {'schema_version': 1, 'plugins': [
            {'id': plugin['id'], 'release': release['id'], 'commit': self.revision,
             'required_skills': [], 'path_scopes': [], 'exceptions': []} for plugin in release['plugins']]}
        self.write_json('composed.json', catalog)
        self.write_json('capabilities.lock.json', lock)
        sources, identities, allow, rules = repo_config.declarations(self.checkout / 'capabilities.lock.json', self.checkout / 'composed.json')
        self.assertEqual(set(sources), {'base-agents'})
        self.assertEqual(identities, {f'{name}@base-agents': True for name in names})
        self.assertEqual((allow, rules), ([], []))

    def test_missing_promisor_blob_fails_without_fetch_or_object_writes(self):
        provider_temporary = tempfile.TemporaryDirectory()
        self.addCleanup(provider_temporary.cleanup)
        provider = Path(provider_temporary.name) / 'provider.git'
        subprocess.run(['git', 'clone', '--bare', '--no-hardlinks', str(self.checkout), str(provider)],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        oid = self.git('rev-parse', f'{self.revision}:plugins/base/binary.dat')
        subprocess.run(['git', '-C', str(provider), 'cat-file', '-e', oid],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        self.git('remote', 'add', 'provider', str(provider))
        self.git('config', 'remote.provider.promisor', 'true')
        self.git('config', 'remote.provider.partialclonefilter', 'blob:none')
        self.git('config', 'extensions.partialClone', 'provider')
        objects = self.checkout / '.git/objects'
        missing_blob = objects / oid[:2] / oid[2:]
        missing_blob.chmod(stat.S_IREAD | stat.S_IWRITE)
        missing_blob.unlink()
        before = {path.relative_to(objects).as_posix(): path.read_bytes() for path in objects.rglob('*') if path.is_file()}
        trace = self.checkout / 'git-inspection.trace'
        with mock.patch.dict(os.environ, {'GIT_TRACE': str(trace), 'GIT_NO_LAZY_FETCH': '0'}):
            with self.assertRaisesRegex(bootstrap.BootstrapError, 'locally available blob|snapshot inspection failed'):
                self.compose()
        after = {path.relative_to(objects).as_posix(): path.read_bytes() for path in objects.rglob('*') if path.is_file()}
        self.assertEqual(after, before)
        self.assertNotIn('fetch', trace.read_text(encoding='utf-8').lower())
        self.assertFalse((objects / oid[:2] / oid[2:]).exists())

    def test_source_catalog_policy_and_exclusions_are_preserved(self):
        policy = copy.deepcopy(self.compose())
        base = policy['releases'][0]['plugins'][0]
        base.update(platforms=['linux', 'macos'], status='deprecated', digest_excludes=['binary.dat'],
                    external_prerequisites={'required': ['exe:compiler'], 'optional': ['exe:formatter']})
        self.write_json('.agents/catalog/catalog.json', policy)
        self.commit()
        actual = self.compose()['releases'][0]['plugins'][0]
        for field in ('platforms', 'status', 'digest_excludes', 'external_prerequisites'):
            self.assertEqual(actual[field], base[field])
        self.assertEqual(actual['digest'], bootstrap.tree_digest(self.checkout / 'plugins/base', ['binary.dat']))


if __name__ == '__main__':
    unittest.main()
