import importlib.util
import json
import os
from pathlib import Path
import shutil
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
    return subprocess.run(['git', '-c', 'user.name=test', '-c', 'user.email=test@example.invalid', '-C', str(path), *arguments], check=True, capture_output=True,
                          text=True, encoding='utf-8').stdout.strip()


class ProcessCleanupTests(unittest.TestCase):
    def test_failed_windows_tree_cleanup_still_terminates_the_native_child(self):
        failures = (
            subprocess.TimeoutExpired("taskkill", 1),
            OSError("taskkill unavailable"),
            subprocess.CompletedProcess(["taskkill"], 1),
            subprocess.CompletedProcess(["taskkill"], 0),
        )
        for failure in failures:
            with self.subTest(failure=str(failure)):
                process = subprocess.Popen([sys.executable, "-I", "-c", "import time; time.sleep(60)"])
                try:
                    result = {"side_effect": failure} if isinstance(failure, Exception) else {"return_value": failure}
                    with mock.patch.object(ROLLING.os, "name", "nt"), \
                            mock.patch.object(ROLLING.subprocess, "run", **result):
                        ROLLING.terminate_process_tree(process, timeout=0.1)
                    self.assertIsNotNone(process.poll())
                finally:
                    if process.poll() is None:
                        process.kill()
                    process.wait(timeout=5)

    def test_forceful_cleanup_keeps_its_final_wait_bounded(self):
        process = mock.Mock()
        process.poll.return_value = None
        process.wait.side_effect = subprocess.TimeoutExpired("native", 0.1)
        with mock.patch.object(ROLLING.os, "name", "nt"), \
                mock.patch.object(ROLLING.subprocess, "run", side_effect=OSError("unavailable")):
            with self.assertRaises(subprocess.TimeoutExpired):
                ROLLING.terminate_process_tree(process, timeout=0.1)
        self.assertTrue(all(call.kwargs == {"timeout": 0.1} for call in process.wait.call_args_list))


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
        os.utime(payload, (1000, 1000))
        stamp = payload.stat().st_mtime_ns
        ROLLING._projection('codex', [package], self.root / 'cache')
        self.assertEqual(payload.stat().st_mtime_ns, stamp)
        obsolete = payload.with_name('obsolete.txt')
        obsolete.write_bytes(b'removed')
        payload.write_bytes(b'changed')
        ROLLING._projection('codex', [package], self.root / 'cache')
        self.assertEqual(payload.read_bytes(), b'one')
        self.assertFalse(obsolete.exists())

    def test_verified_tree_reuse_repairs_missing_extra_and_changed_files(self):
        root = self.root / 'verified'
        files = {'payload.txt': (b'current', False), 'nested/other.txt': (b'other', False)}
        ROLLING._write_tree(root, files)
        payload = root / 'payload.txt'
        os.utime(payload, (1000, 1000))
        stamp = payload.stat().st_mtime_ns
        ROLLING._write_tree(root, files)
        self.assertEqual(payload.stat().st_mtime_ns, stamp)
        (root / 'nested/other.txt').unlink()
        (root / 'obsolete.txt').write_bytes(b'old')
        payload.write_bytes(b'changed')
        ROLLING._write_tree(root, files)
        self.assertEqual(ROLLING._tree_bytes(root), files)
        if os.name != 'nt':
            payload.chmod(payload.stat().st_mode | 0o111)
            ROLLING._write_tree(root, files)
            self.assertEqual(ROLLING._tree_bytes(root), files)

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

    def claude_dependency_preflight(self):
        config = self.root / 'claude'
        project = self.root / 'project'
        project.mkdir()
        self.write(config / 'settings.json', {'enabledPlugins': {'engineering@umbrella': True}})
        self.write(config / 'plugins/known_marketplaces.json', {
            'umbrella': {'source': {'source': 'github', 'repo': 'tj-agents/core'}},
        })
        return config, project, ROLLING.preflight('claude', config, project, {'cache_root': config / 'plugins/cache/r'})

    def test_claude_materializes_declared_dependency_without_saved_marketplace(self):
        config, project, preflight = self.claude_dependency_preflight()
        self.write(config / 'settings.json', {'enabledPlugins': {
            'engineering@umbrella': True, 'base@umbrella': True,
        }})
        installs = []
        saved = {path: path.read_bytes() for path in
                 (config / 'settings.json', config / 'plugins/known_marketplaces.json')}
        with preflight as active:
            expected = {root.identity: root for root in active.prepared.selected_roots}
            settings = json.loads(active.prepared.launch_args[1])
            source = settings['extraKnownMarketplaces']['core']['source']
            self.assertEqual(source, {'source': 'directory', 'path': str(active.prepared.catalog_root / 'core')})

            def native(command, _project, environment, _deadline, json_output=False):
                if command[1:3] == ['plugin', 'install']:
                    identity = command[3]
                    installs.append(identity)
                    plugins = Path(environment['CLAUDE_CODE_PLUGIN_CACHE_DIR'])
                    destination = plugins / 'cache' / identity / 'unknown'
                    shutil.copytree(expected[identity].root, destination)
                    registry_path = plugins / 'installed_plugins.json'
                    document = json.loads(registry_path.read_text()) if registry_path.exists() else {'version': 2, 'plugins': {}}
                    document['plugins'][identity] = [{'scope': 'user', 'installPath': str(destination)}]
                    self.write(registry_path, document)
                    return None
                self.assertEqual(command[-3:], ['plugin', 'list', '--json'])
                document = json.loads((config / 'plugins/installed_plugins.json').read_text())
                return [{'id': identity, 'enabled': True, 'installPath': records[0]['installPath'],
                         'version': records[0].get('version', 'unknown')}
                        for identity, records in document['plugins'].items()]

            with mock.patch.object(ROLLING, '_native', side_effect=native), \
                    mock.patch.object(ROLLING, '_pin_claude_cache'), \
                    mock.patch.object(ROLLING, '_claude_pinned_paths', return_value=set()):
                prepared = active.materialize_native('claude')
            self.assertEqual({root.identity for root in prepared.selected_roots}, {
                'base@core', 'base@umbrella', 'engineering@umbrella',
            })
            self.assertEqual(installs, ['base@core', 'engineering@umbrella'])
            self.assertTrue(all((root.root / 'payload.txt').read_text() == 'one' for root in prepared.selected_roots))
            active.acknowledge_binding()
        self.assertEqual(saved, {path: path.read_bytes() for path in saved})

    def test_claude_still_refuses_removed_explicit_marketplace_before_native_install(self):
        config, project, preflight = self.claude_dependency_preflight()
        with preflight as active:
            self.write(config / 'plugins/known_marketplaces.json', {})
            with mock.patch.object(ROLLING, '_native') as native:
                with self.assertRaisesRegex(ROLLING.RollingPluginError, 'no longer registered: umbrella'):
                    active.materialize_native('claude')
            native.assert_not_called()

    def test_claude_alias_reuse_remains_bound_to_publisher_bytes_and_inventory(self):
        for variation in ('repository', 'revision', 'payload', 'inventory'):
            with self.subTest(variation=variation):
                directory = self.root / variation
                config = directory / 'config'
                registry_path = config / 'plugins/installed_plugins.json'
                before = {'version': 2, 'plugins': {}}
                self.write(registry_path, before)
                self.write(config / 'plugins/known_marketplaces.json', {})
                roots = []
                for marketplace in ('one', 'two'):
                    root = directory / marketplace
                    self.write(root / '.claude-plugin/plugin.json', {'name': 'base'})
                    payload = 'changed' if variation == 'payload' and marketplace == 'two' else 'verified'
                    (root / 'payload.txt').write_text(payload, encoding='utf-8')
                    repository = 'https://github.com/tj-agents/core.git'
                    revision = 'a' * 40
                    if marketplace == 'two' and variation == 'repository':
                        repository = 'https://github.com/tj-agents/other.git'
                    if marketplace == 'two' and variation == 'revision':
                        revision = 'b' * 40
                    roots.append(ROLLING.VerifiedRoot(f'base@{marketplace}', root, revision, repository))
                expected = {root.identity: root for root in roots}
                prepared = ROLLING.Prepared('claude', (), tuple(roots), directory / 'catalog', {},
                                            plugins_root=config / 'plugins')
                installs = []

                def native(command, _project, environment, _deadline, json_output=False):
                    if command[1:3] == ['plugin', 'install']:
                        identity = command[3]
                        installs.append(identity)
                        plugins = Path(environment['CLAUDE_CODE_PLUGIN_CACHE_DIR'])
                        destination = plugins / 'cache' / identity / 'unknown'
                        shutil.copytree(expected[identity].root, destination)
                        path = plugins / 'installed_plugins.json'
                        value = json.loads(path.read_text()) if path.exists() else {'plugins': {}}
                        value['plugins'][identity] = [{'scope': 'user', 'installPath': str(destination)}]
                        self.write(path, value)
                        return None
                    value = json.loads(registry_path.read_text())
                    return [{'id': identity, 'enabled': True, 'installPath': records[0]['installPath'],
                             'version': records[0].get('version', 'unknown')}
                            for identity, records in value['plugins'].items()
                            if variation != 'inventory' or identity != 'base@two']

                with mock.patch.object(ROLLING, '_native', side_effect=native), \
                        mock.patch.object(ROLLING, '_pin_claude_cache'), \
                        mock.patch.object(ROLLING, '_claude_pinned_paths', return_value=set()):
                    if variation in {'payload', 'inventory'}:
                        message = 'differs from verified Git package' if variation == 'payload' else 'native inventory did not select'
                        with self.assertRaisesRegex(ROLLING.RollingPluginError, message):
                            ROLLING.materialize_native(prepared, 'claude', config, directory, 'claude')
                        self.assertEqual(installs, ['base@one'])
                        self.assertEqual(json.loads(registry_path.read_text()), before)
                    else:
                        result = ROLLING.materialize_native(prepared, 'claude', config, directory, 'claude')
                        self.assertEqual(installs, ['base@one', 'base@two'])
                        self.assertEqual({root.identity for root in result.selected_roots}, set(expected))
                        registry = json.loads(registry_path.read_text())['plugins']
                        for root in result.selected_roots:
                            record = registry[root.identity][0]
                            self.assertEqual(record['installPath'], str(root.root))
                            self.assertEqual(record['version'], root.root.name)
                            self.assertEqual(record['gitCommitSha'], root.revision)
                        installs.clear()
                        ROLLING.materialize_native(prepared, 'claude', config, directory, 'claude')
                        self.assertEqual(installs, [])
                        (roots[0].root / 'payload.txt').write_text('new main content', encoding='utf-8')
                        ROLLING.materialize_native(prepared, 'claude', config, directory, 'claude')
                        self.assertEqual(installs, ['base@one'])
                        self.assertEqual((result.selected_roots[0].root / 'payload.txt').read_text(), 'new main content')

    def test_cached_claude_source_requires_matching_unlinked_ownership(self):
        source = self.root / 'verified'
        source.mkdir()
        (source / 'payload.txt').write_bytes(b'current')
        expected = ROLLING.VerifiedRoot('base@core', source, 'a' * 40, 'https://github.com/tj-agents/core.git')
        cache = self.root / 'cache'
        destination = cache / 'core/base' / expected.revision
        ROLLING._promote(source, destination, source, cache, expected)
        self.assertEqual(ROLLING._cached_claude_source(expected, cache), destination)
        marker = destination.parent / '.tj-agents-rolling.json'
        marker.unlink()
        self.assertIsNone(ROLLING._cached_claude_source(expected, cache))
        self.write(marker, {'identity': expected.identity, 'repository': 'https://github.com/tj-agents/other.git',
                            'revision': expected.revision})
        self.assertIsNone(ROLLING._cached_claude_source(expected, cache))
        marker.unlink()
        outside = self.root / 'outside'
        outside.mkdir()
        RollingBoundaryTests.linked_directory(self, marker, outside)
        with self.assertRaisesRegex(ROLLING.RollingPluginError, 'linked or reparse ancestor'):
            ROLLING._cached_claude_source(expected, cache)

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

    def add_generators(self, exit_code=0):
        digests = "import sys\nsys.exit(0)\n"
        sync = (
            "import argparse, pathlib, sys\n"
            "parser = argparse.ArgumentParser(); parser.add_argument('--root'); parser.add_argument('--check', action='store_true')\n"
            "arguments = parser.parse_args(); built = pathlib.Path(arguments.root) / 'plugins/base/generated.txt'\n"
            f"if {exit_code}: sys.exit({exit_code})\n"
            "if arguments.check: sys.exit(0 if built.read_text() == 'built' else 1)\n"
            "built.write_text('built')\n"
        )
        (self.author / 'scripts').mkdir(exist_ok=True)
        (self.author / 'scripts/update_catalog_digests.py').write_text(digests, encoding='utf-8')
        (self.author / 'scripts/sync_plugin_packages.py').write_text(sync, encoding='utf-8')
        git(self.author, 'add', '-A')
        git(self.author, 'commit', '-m', 'merged source awaiting regeneration')
        git(self.author, 'push', 'origin', 'HEAD:main')

    def test_unpublished_core_main_is_generated_locally_for_startup(self):
        self.add_generators()
        cache = self.root / 'cache'
        clone, tip = ROLLING._fetch_main(str(self.remote), cache)
        core = 'https://github.com/tj-agents/core.git'
        catalog_cache, published = {}, set()
        with mock.patch.object(ROLLING, 'canonical_source', return_value=core),                 mock.patch.object(ROLLING, '_fetch_main', return_value=(clone, tip)),                 mock.patch.object(ROLLING, '_publication_gate', side_effect=ROLLING.RollingPluginError('Catalog digest drift')):
            source, generated, revision, catalog = ROLLING._state(core, cache, catalog_cache, published, ROLLING.Deadline(60))
        self.assertEqual((core, tip), (source, revision))
        self.assertEqual(cache / 'generated' / tip, generated)
        self.assertEqual(['base', 'engineering'], [entry['name'] for entry in catalog['plugins']])
        files = ROLLING._tree_files(generated, tip, 'plugins/base')
        self.assertEqual(b'built', files['generated.txt'][0])
        self.assertEqual(b'one', files['payload.txt'][0])
        self.assertNotIn(ROLLING.GENERATED_MARKER, files)
        with mock.patch.object(ROLLING, '_extract_repository', side_effect=AssertionError('rebuilt')):
            self.assertEqual(generated, ROLLING._generated_publication(clone, tip, cache, ROLLING.Deadline(60)))

    def test_a_core_main_that_cannot_be_generated_still_fails_startup_with_both_causes(self):
        self.add_generators(exit_code=3)
        cache = self.root / 'cache'
        clone, tip = ROLLING._fetch_main(str(self.remote), cache)
        core = 'https://github.com/tj-agents/core.git'
        with mock.patch.object(ROLLING, 'canonical_source', return_value=core), \
                mock.patch.object(ROLLING, '_fetch_main', return_value=(clone, tip)), \
                mock.patch.object(ROLLING, '_publication_gate', side_effect=ROLLING.RollingPluginError('Catalog digest drift')), \
                self.assertRaisesRegex(ROLLING.RollingPluginError, 'could not be generated for startup.*Catalog digest drift'):
            ROLLING._state(core, cache, {}, set(), ROLLING.Deadline(60))
        self.assertFalse((cache / 'generated' / tip).exists())
        self.assertEqual([], list((cache / 'generated').iterdir()))

    def test_a_newer_generated_main_replaces_older_builds_and_write_failures_are_refresh_errors(self):
        self.add_generators()
        cache = self.root / 'cache'
        stale = cache / 'generated' / ('0' * 40)
        stale.mkdir(parents=True)
        (stale / ROLLING.GENERATED_MARKER).write_text('old', encoding='utf-8')
        clone, tip = ROLLING._fetch_main(str(self.remote), cache)
        locked = cache / 'generated' / ('1' * 40)
        locked.mkdir()
        real_remove = ROLLING._remove_cache_tree

        def remove(path, root):
            if path == locked:
                raise PermissionError('in use')
            return real_remove(path, root)

        with mock.patch.object(ROLLING, '_remove_cache_tree', side_effect=remove):
            generated = ROLLING._generated_publication(clone, tip, cache, ROLLING.Deadline(60))
        self.assertEqual(sorted([generated, locked]), sorted((cache / 'generated').iterdir()))
        shutil.rmtree(locked)
        shutil.rmtree(generated)
        with mock.patch.object(ROLLING.os, 'replace', side_effect=PermissionError('in use')), \
                self.assertRaisesRegex(ROLLING.RollingPluginError, 'generated tree could not be written'):
            ROLLING._generated_publication(clone, tip, cache, ROLLING.Deadline(60))
        self.assertEqual([], list((cache / 'generated').iterdir()))

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
        self.assertNotIn('unrelated', settings)
        self.assertEqual(json.loads((config / 'settings.json').read_text(encoding='utf-8'))['unrelated'], {'retained': True})
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

    def test_only_a_final_verification_still_on_main_records_its_generation(self):
        core = 'https://github.com/tj-agents/core.git'
        plugins = self.root / 'plugins'
        root = ROLLING.VerifiedRoot('base@core', self.root / 'root', 'a' * 40, core)
        prepared = ROLLING.Prepared('claude', (), (root,), self.root / 'catalog', {},
                                    source_revisions=((core, 'a' * 40),), plugins_root=plugins)
        record = ROLLING.generation_record.generations_path(plugins, 'claude')

        def verify(main, linked=False):
            refuse = ROLLING.RollingPluginError('linked') if linked else None
            with mock.patch.object(ROLLING, '_selection_state', return_value=([], set())), \
                    mock.patch.object(ROLLING, '_cache_root', return_value=self.root / 'cache'), \
                    mock.patch.object(ROLLING, '_fetch_main', return_value=(self.root, main)), \
                    mock.patch.object(ROLLING, '_unlinked_ancestors', side_effect=refuse):
                ROLLING.verify_final(prepared, 'claude', self.root, self.root, {})

        with self.assertRaisesRegex(ROLLING.RollingPluginError, 'main advanced'):
            verify('b' * 40)
        verify('a' * 40, linked=True)
        self.assertFalse(record.exists())

        verify('a' * 40)

        self.assertEqual([(core, 'a' * 40)], [(entry['repository'], entry['revision'])
                                              for entry in ROLLING.generation_record.read_generations(record)])

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


class RollingBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='rolling boundaries ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_claude_selection_maps_merge_by_identity_in_native_precedence_order(self):
        config = self.root / 'config'
        project = self.root / 'project'
        RollingPluginsTests.write(config / 'settings.json', {
            'enabledPlugins': {'base@core': True, 'machine@core': False},
            'extraKnownMarketplaces': {'core': {'autoUpdate': True}},
        })
        RollingPluginsTests.write(project / '.claude/settings.json', {
            'enabledPlugins': {'engineering@core': True},
            'extraKnownMarketplaces': {'stack': {'autoUpdate': True}},
        })
        RollingPluginsTests.write(project / '.claude/settings.local.json', {
            'enabledPlugins': {'base@core': False},
        })
        effective, supplied = ROLLING.claude_settings(config, project, (
            '--setting-sources', 'local,project,user',
            '--settings', '{"enabledPlugins":{"other@core":true},"cli":"retained"}',
        ))
        self.assertEqual(effective['enabledPlugins'], {
            'base@core': False, 'machine@core': False, 'engineering@core': True, 'other@core': True,
        })
        self.assertEqual(set(effective['extraKnownMarketplaces']), {'core', 'stack'})
        self.assertEqual(supplied, {'enabledPlugins': {'other@core': True}, 'cli': 'retained'})


    def linked_directory(self, link, target):
        link.parent.mkdir(parents=True, exist_ok=True)
        if os.name == 'nt':
            subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(link), str(target)],
                           check=True, capture_output=True)
            self.addCleanup(link.rmdir)
        else:
            link.symlink_to(target, target_is_directory=True)
            self.addCleanup(link.unlink)

    def test_redirected_cache_ancestor_cannot_write_or_delete_outside_files(self):
        outside = self.root / 'outside'
        (outside / 'package').mkdir(parents=True)
        (outside / 'package/keep.txt').write_bytes(b'preserved')
        staging = outside / f'.package.{os.getpid()}.tmp'
        staging.mkdir()
        (staging / 'keep.txt').write_bytes(b'staged sentinel')
        cache = self.root / 'cache'
        link = cache / 'packages'
        self.linked_directory(link, outside)
        destination = link / 'package'
        before = {p.relative_to(outside): p.read_bytes() for p in outside.rglob('*') if p.is_file()}
        with self.assertRaisesRegex(ROLLING.RollingPluginError, 'linked or reparse ancestor'):
            ROLLING._write_tree(destination, {'new.txt': (b'new', False)})
        with self.assertRaisesRegex(ROLLING.RollingPluginError, 'linked or reparse ancestor'):
            ROLLING._remove_cache_tree(destination, destination.parent)
        self.assertEqual(before, {p.relative_to(outside): p.read_bytes() for p in outside.rglob('*') if p.is_file()})

    def test_redirected_cache_lock_and_git_checkout_fail_before_mutation(self):
        outside = self.root / 'outside'
        outside.mkdir()
        cache = self.root / 'cache'
        self.linked_directory(cache, outside)
        with self.assertRaisesRegex(ROLLING.RollingPluginError, 'linked or reparse ancestor'):
            with ROLLING.exclusive(cache):
                self.fail('redirected lock acquired')
        with mock.patch.object(ROLLING, '_run') as run:
            with self.assertRaisesRegex(ROLLING.RollingPluginError, 'linked or reparse ancestor'):
                ROLLING._fetch_main('https://github.com/tj-agents/core.git', cache)
            run.assert_not_called()
        self.assertEqual([], list(outside.iterdir()))

    def test_selection_cache_components_reject_traversal_and_identity_mismatch(self):
        for identity, marketplace in (
            ('../base@core', 'core'), ('base@../core', '../core'), ('base@core', 'other'),
            ('base@core.', 'core.'), ('base@core/other', 'core/other'), ('CON@core', 'core'),
        ):
            with self.subTest(identity=identity), self.assertRaises(ROLLING.RollingPluginError):
                ROLLING.Selection(identity, 'https://github.com/tj-agents/core.git', marketplace)
        for source in ('https://github.com/tj-agents/%2e%2e.git', 'https://github.com/tj-agents/core?x.git'):
            with self.subTest(source=source):
                self.assertIsNone(ROLLING.canonical_source(source))


    def test_approved_concertable_marketplace_is_selected_by_both_hosts(self):
        config = self.root / 'config'
        project = self.root / 'project'
        identity = 'concertable@agents'
        RollingPluginsTests.write(config / 'settings.json', {'enabledPlugins': {identity: True}})
        RollingPluginsTests.write(config / 'plugins/known_marketplaces.json', {
            'agents': {'source': {'source': 'github', 'repo': 'Concertable/agents'}},
        })
        claude = ROLLING.selected_claude(config, config / 'plugins', project)
        codex = ROLLING.selected_codex({'installed': [{
            'pluginId': identity, 'enabled': True,
            'marketplaceSource': {'sourceType': 'git', 'source': 'https://github.com/Concertable/agents.git'},
        }]})
        self.assertEqual(claude, codex)
        self.assertEqual([ROLLING.Selection(identity, 'https://github.com/concertable/agents.git', 'agents')], claude)
        with mock.patch.object(ROLLING, '_run', side_effect=['', claude[0].source_url, '', 'a' * 40]) as run:
            _clone, revision = ROLLING._fetch_main(claude[0].source_url, self.root / 'cache')
        self.assertEqual('a' * 40, revision)
        self.assertIn('refs/heads/main:refs/remotes/origin/main', run.call_args_list[2].args[0])

    def test_expired_deadline_cannot_spawn_a_child(self):
        deadline = mock.Mock()
        deadline.remaining.side_effect = ROLLING.RollingPluginError('expired')
        with mock.patch.object(ROLLING.subprocess, 'Popen') as start:
            with self.assertRaisesRegex(ROLLING.RollingPluginError, 'expired'):
                ROLLING._completed(['git', 'fetch'], None, {}, deadline)
            start.assert_not_called()

    def test_deadline_expiring_during_spawn_terminates_the_child(self):
        deadline = mock.Mock()
        deadline.remaining.side_effect = [1, ROLLING.RollingPluginError('expired')]
        with mock.patch.object(ROLLING.subprocess, 'Popen') as start, \
                mock.patch.object(ROLLING, 'terminate_process_tree') as terminate:
            with self.assertRaisesRegex(ROLLING.RollingPluginError, 'expired'):
                ROLLING._completed(['git', 'fetch'], None, {}, deadline)
            terminate.assert_called_once_with(start.return_value)
            start.return_value.communicate.assert_not_called()


if __name__ == '__main__':
    unittest.main()
