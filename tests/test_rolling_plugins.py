import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / '.agents/machine/scripts/rolling_plugins.py'
SPEC = importlib.util.spec_from_file_location('rolling_plugins', SCRIPT)
ROLLING = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ROLLING
SPEC.loader.exec_module(ROLLING)


def git(path, *arguments):
    return subprocess.run(['git', '-C', str(path), *arguments], check=True, capture_output=True,
                          text=True, encoding='utf-8').stdout.strip()


class RollingPluginsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='rolling plugins ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.remote = self.root / 'publisher.git'
        self.author = self.root / 'author'
        subprocess.run(['git', 'init', '--bare', '--initial-branch=main', str(self.remote)], check=True,
                       capture_output=True)
        subprocess.run(['git', 'clone', str(self.remote), str(self.author)], check=True, capture_output=True)
        self.original_canonical = ROLLING.canonical_source
        ROLLING.canonical_source = lambda value: str(self.remote) if value.endswith('tj-agents/core.git') else value
        self.addCleanup(setattr, ROLLING, 'canonical_source', self.original_canonical)
        self.publish('one')

    def publish(self, text, include_extra=False):
        catalog = {
            'name': 'core',
            'plugins': [
                {'name': 'base', 'source': './plugins/base'},
                {'name': 'engineering', 'source': './plugins/engineering'},
            ],
        }
        self.write(self.author / '.claude-plugin/marketplace.json', catalog)
        self.write(self.author / 'plugins/base/.claude-plugin/plugin.json', {'name': 'base'})
        (self.author / 'plugins/base/payload.txt').write_text(text, encoding='utf-8')
        self.write(self.author / 'plugins/base/harness.json', {'requires': {
            'marketplaces': [{'id': 'core', 'repository': 'tj-agents/core'}], 'plugins': ['core/base'],
        }})
        self.write(self.author / 'plugins/engineering/.claude-plugin/plugin.json', {'name': 'engineering'})
        (self.author / 'plugins/engineering/payload.txt').write_text(text, encoding='utf-8')
        self.write(self.author / 'plugins/engineering/harness.json', {'requires': {
            'marketplaces': [{'id': 'core', 'repository': 'tj-agents/core'}], 'plugins': ['core/base'],
        }})
        if include_extra:
            (self.author / 'plugins/base/extra.txt').write_text('new', encoding='utf-8')
        git(self.author, 'add', '-A')
        git(self.author, 'commit', '-m', text)
        git(self.author, 'push', 'origin', 'HEAD:main')
        return git(self.author, 'rev-parse', 'HEAD')

    @staticmethod
    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')

    def test_resolve_fetches_main_and_closes_harness_dependencies_without_unselected_roster(self):
        packages = ROLLING.resolve([ROLLING.Selection('engineering@core', str(self.remote), 'core')], self.root / 'cache')
        self.assertEqual([package.identity for package in packages], ['base@core', 'engineering@core'])
        self.assertEqual((packages[0].root / 'payload.txt').read_text(encoding='utf-8'), 'one')

    def test_resolve_replaces_same_named_package_with_new_main_tree(self):
        cache = self.root / 'cache'
        ROLLING.resolve([ROLLING.Selection('base@core', str(self.remote), 'core')], cache)
        self.publish('two', include_extra=True)
        package = ROLLING.resolve([ROLLING.Selection('base@core', str(self.remote), 'core')], cache)[0]
        self.assertEqual((package.root / 'payload.txt').read_text(encoding='utf-8'), 'two')
        self.assertTrue((package.root / 'extra.txt').is_file())
        (self.author / 'plugins/base/extra.txt').unlink()
        self.publish('three')
        package = ROLLING.resolve([ROLLING.Selection('base@core', str(self.remote), 'core')], cache)[0]
        self.assertEqual((package.root / 'payload.txt').read_text(encoding='utf-8'), 'three')
        self.assertFalse((package.root / 'extra.txt').exists())

    def test_missing_selected_package_fails_instead_of_selecting_a_substitute(self):
        with self.assertRaisesRegex(ROLLING.RollingPluginError, 'missing from the current publisher catalog'):
            ROLLING.resolve([ROLLING.Selection('removed@core', str(self.remote), 'core')], self.root / 'cache')

    def test_unrelated_sources_are_not_a_tj_agents_selection(self):
        self.assertIsNone(self.original_canonical('https://github.com/other/plugins.git'))

    def test_codex_clean_profile_accepts_empty_installed_inventory_before_add(self):
        self.assertEqual(ROLLING._codex_inventory_entries({'installed': []}), [])

    def test_projection_preserves_payload_bytes_and_codex_arguments(self):
        package = ROLLING.resolve([ROLLING.Selection('base@core', str(self.remote), 'core')], self.root / 'cache')[0]
        catalog, roots = ROLLING._projection('codex', [package], self.root / 'cache')
        self.assertEqual(roots, (package.root,))
        payload = catalog / 'core/plugins/base/payload.txt'
        self.assertEqual(payload.read_bytes(), b'one')
        manifest = json.loads((catalog / 'core/.agents/plugins/marketplace.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['owner']['name'], 'core')
        self.assertEqual(manifest['plugins'][0]['name'], 'base')

    def test_preflight_holds_its_lock_until_binding_is_acknowledged(self):
        target = self.root / 'profile'
        project = self.root / 'project'
        project.mkdir()
        selection = ROLLING.Selection('base@core', str(self.remote), 'core')
        prepared = ROLLING.Prepared('claude', (), (), target, {}, (selection,))
        with mock.patch.object(ROLLING, '_prepare', return_value=prepared):
            with ROLLING.preflight('claude', target, project) as active:
                self.assertIsNotNone(active.prepared)
                lock = self.root / 'profile/plugins/cache/.tj-agents-rolling/claude/rolling-plugins.lock'
                self.assertTrue(lock.is_file())
                prepared = active.acknowledge_binding()
                with ROLLING.exclusive(lock.parent, wait=0):
                    pass
        self.assertEqual(prepared.selected_roots, ())

    def test_external_git_subdir_uses_the_external_publisher_current_catalog_once(self):
        external = self.root / 'external.git'
        author = self.root / 'external-author'
        subprocess.run(['git', 'init', '--bare', '--initial-branch=main', str(external)], check=True, capture_output=True)
        subprocess.run(['git', 'clone', str(external), str(author)], check=True, capture_output=True)
        self.write(author / '.claude-plugin/marketplace.json', {'name': 'external', 'plugins': [
            {'name': 'base', 'source': './packages/base'},
        ]})
        self.write(author / 'packages/base/.claude-plugin/plugin.json', {'name': 'base'})
        (author / 'packages/base/payload.txt').write_text('external', encoding='utf-8')
        git(author, 'add', '-A')
        git(author, 'commit', '-m', 'external')
        git(author, 'push', 'origin', 'HEAD:main')
        self.write(self.author / '.claude-plugin/marketplace.json', {'name': 'core', 'plugins': [
            {'name': 'base', 'source': {'source': 'git-subdir', 'url': str(external), 'path': './obsolete'}},
        ]})
        git(self.author, 'add', '-A')
        git(self.author, 'commit', '-m', 'external source')
        git(self.author, 'push', 'origin', 'HEAD:main')
        original = ROLLING.canonical_source
        ROLLING.canonical_source = lambda value: str(self.remote) if value.endswith('tj-agents/core.git') else value
        self.addCleanup(setattr, ROLLING, 'canonical_source', original)
        revisions = {}
        package = ROLLING.resolve([ROLLING.Selection('base@core', str(self.remote), 'core')], self.root / 'cache', source_revisions=revisions)[0]
        self.assertEqual((package.root / 'payload.txt').read_text(encoding='utf-8'), 'external')
        self.assertEqual(len(revisions), 2)

    def test_explicitly_disabled_required_dependency_fails(self):
        with self.assertRaisesRegex(ROLLING.RollingPluginError, 'explicitly disabled'):
            ROLLING.resolve([ROLLING.Selection('engineering@core', str(self.remote), 'core')], self.root / 'cache', {'base@core'})

    def test_published_executable_bit_is_preserved_in_the_verified_tree(self):
        if os.name == 'nt':
            self.skipTest('Windows does not expose POSIX executable bits')
        payload = self.author / 'plugins/base/payload.txt'
        git(self.author, 'add', '-A')
        git(self.author, 'update-index', '--chmod=+x', 'plugins/base/payload.txt')
        git(self.author, 'commit', '-m', 'executable payload')
        git(self.author, 'push', 'origin', 'HEAD:main')
        package = ROLLING.resolve([ROLLING.Selection('base@core', str(self.remote), 'core')], self.root / 'cache')[0]
        self.assertTrue(package.root.joinpath('payload.txt').stat().st_mode & 0o111)

    def test_publication_gate_runs_the_fetched_generator_in_a_bounded_subprocess(self):
        clone = self.root / 'clone'
        clone.mkdir()
        revision = 'a' * 40
        calls = []

        def extract(_clone, _revision, destination, _deadline):
            (destination / 'scripts').mkdir(parents=True)
            (destination / 'scripts/sync_plugin_packages.py').write_text('', encoding='utf-8')

        def completed(command, cwd, environment, deadline, timeout=ROLLING.GIT_TIMEOUT_SECONDS):
            calls.append((command, cwd, deadline.remaining(timeout)))
            return subprocess.CompletedProcess(command, 0, b'', b'')

        with mock.patch.object(ROLLING, '_git_text', return_value=b'{"source_fingerprint":"fingerprint"}'), \
                mock.patch.object(ROLLING, '_extract_repository', side_effect=extract), \
                mock.patch.object(ROLLING, '_completed', side_effect=completed):
            ROLLING._publication_gate(clone, revision, ROLLING.Deadline(5))

        self.assertEqual(calls[0][0][0], sys.executable)
        self.assertIn('--check', calls[0][0])
        self.assertGreater(calls[0][2], 0)

    def test_claude_cli_settings_last_value_selects_and_preserves_unrelated_settings(self):
        config = self.root / 'profile'
        plugins = config / 'plugins'
        project = self.root / 'project'
        project.mkdir()
        self.write(config / 'settings.json', {
            'enabledPlugins': {'engineering@core': True}, 'unrelated': {'retained': True},
            'extraKnownMarketplaces': {'core': {'source': {'source': 'github', 'repo': 'tj-agents/core'}, 'autoUpdate': True}},
        })
        self.write(plugins / 'known_marketplaces.json', {
            'core': {'source': {'source': 'github', 'repo': 'tj-agents/core'}},
        })
        arguments = {
            'plugins_root': plugins,
            'argv': ('--settings', '{"enabledPlugins":{"base@core":true}}',
                     '--settings', '{"enabledPlugins":{"engineering@core":true},"cli":"kept"}'),
        }
        prepared = ROLLING._prepare('claude', config, project, arguments, self.root / 'cache', ROLLING.Deadline(20))
        settings = json.loads(prepared.launch_args[1])
        self.assertEqual(settings['unrelated'], {'retained': True})
        self.assertEqual(settings['cli'], 'kept')
        self.assertEqual(settings['enabledPlugins'], {'engineering@core': True, 'base@core': True})
        self.assertFalse(settings['extraKnownMarketplaces']['core']['autoUpdate'])
        self.assertEqual(settings['extraKnownMarketplaces']['core']['source']['repo'], 'tj-agents/core')

    def test_claude_final_explicit_disablement_blocks_the_launch(self):
        config = self.root / 'profile'
        plugins = config / 'plugins'
        project = self.root / 'project'
        project.mkdir()
        self.write(config / 'settings.json', {'enabledPlugins': {'engineering@core': True}})
        self.write(plugins / 'known_marketplaces.json', {
            'core': {'source': {'source': 'github', 'repo': 'tj-agents/core'}},
        })
        arguments = {'plugins_root': plugins}
        prepared = ROLLING._prepare('claude', config, project, arguments, self.root / 'cache', ROLLING.Deadline(20))
        self.write(config / 'settings.json', {'enabledPlugins': {'engineering@core': True, 'base@core': False}})
        with self.assertRaisesRegex(ROLLING.RollingPluginError, 'disablement changed'):
            ROLLING.verify_final(prepared, 'claude', config, project, arguments)

    def test_claude_setting_sources_excludes_unselected_layers(self):
        config = self.root / 'profile'
        project = self.root / 'project'
        project.mkdir()
        self.write(config / 'settings.json', {'enabledPlugins': {'base@core': True}})
        self.write(project / '.claude/settings.json', {'enabledPlugins': {'engineering@core': True}})
        self.assertEqual(
            ROLLING.claude_enabled(config, project, ('--setting-sources', 'project')),
            {'engineering@core': True},
        )

    def test_malformed_ownership_marker_cannot_authorize_replacing_a_native_root(self):
        source = self.root / 'source'
        expected = self.root / 'expected'
        destination = self.root / 'cache/core/base/revision'
        for root in (source, expected, destination):
            (root / '.claude-plugin').mkdir(parents=True)
            (root / '.claude-plugin/plugin.json').write_text('{"name":"base"}', encoding='utf-8')
        marker = destination.parent / '.tj-agents-rolling.json'
        marker.write_text('{', encoding='utf-8')
        root = ROLLING.VerifiedRoot('base@core', expected, 'revision', 'https://github.com/tj-agents/core.git')
        with self.assertRaisesRegex(ROLLING.RollingPluginError, 'cannot read JSON'):
            ROLLING._promote(source, destination, expected, self.root / 'cache', root, allow_adopt=True)
        self.assertTrue(destination.is_dir())

    def test_pinned_and_unrelated_native_cache_roots_are_not_pruned(self):
        cache = self.root / 'cache'
        pinned = cache / 'core/base/old'
        active = cache / 'core/base/new'
        unrelated = cache / 'other/side/old'
        for root, name in ((pinned, 'base'), (active, 'base'), (unrelated, 'side')):
            (root / '.claude-plugin').mkdir(parents=True)
            (root / '.claude-plugin/plugin.json').write_text(json.dumps({'name': name}), encoding='utf-8')
        self.write(pinned.parent / '.tj-agents-rolling.json', {
            'identity': 'base@core', 'repository': 'https://github.com/tj-agents/core.git', 'revision': 'new',
        })
        self.write(unrelated.parent / '.tj-agents-rolling.json', {
            'identity': 'side@other', 'repository': 'https://github.com/tj-agents/other.git', 'revision': 'old',
        })
        root = ROLLING.VerifiedRoot('base@core', active, 'new', 'https://github.com/tj-agents/core.git')
        ROLLING._prune_native_cache(cache, [pinned], [root])
        self.assertTrue(pinned.is_dir())
        self.assertTrue(unrelated.is_dir())

if __name__ == '__main__':
    unittest.main()
