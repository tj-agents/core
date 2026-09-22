"""Synthetic profiles only; no normal-profile plugin cache is read or removed."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'prune_plugin_cache', ROOT / '.agents/machine/scripts/prune_plugin_cache.py'
)
PRUNE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PRUNE)


class PluginCacheReconcileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic plugin cache ')
        self.addCleanup(self.temp.cleanup)
        self.config = Path(self.temp.name) / '.claude'
        self.cache = self.config / 'plugins' / 'cache'

    def version(self, marketplace, plugin, version):
        path = self.cache / marketplace / plugin / version
        path.mkdir(parents=True, exist_ok=True)
        (path / 'payload.txt').write_text('x' * 16, encoding='utf-8')
        return path

    def registry(self, *install_paths, raw=None):
        path = self.config / 'plugins' / 'installed_plugins.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        if raw is not None:
            path.write_text(raw, encoding='utf-8')
            return path
        plugins = {
            f'plugin{index}@market': [{'scope': 'user', 'installPath': str(entry)}]
            for index, entry in enumerate(install_paths)
        }
        path.write_text(json.dumps({'version': 2, 'plugins': plugins}), encoding='utf-8')
        return path

    def run_cli(self, *arguments):
        stream = io.StringIO()
        code = PRUNE.run_reconcile(
            self.config,
            keep_previous=0,
            apply_mode='--apply' in arguments,
            stream=stream,
        )
        return code, stream.getvalue()

    def test_report_is_the_default_and_removes_nothing(self):
        live = self.version('market', 'kept', 'aaaa')
        stale = self.version('market', 'kept', 'bbbb')
        orphan = self.version('gone', 'renamed', 'cccc')
        self.registry(live)

        code, output = self.run_cli()

        self.assertEqual(PRUNE.EXIT_OK, code)
        self.assertTrue(live.is_dir())
        self.assertTrue(stale.is_dir())
        self.assertTrue(orphan.is_dir())
        self.assertIn('would remove 2 directories', output)
        self.assertIn(str(stale), output)
        self.assertIn(str(orphan), output)

    def test_apply_removes_only_what_the_registry_does_not_name(self):
        live = self.version('market', 'kept', 'aaaa')
        stale = self.version('market', 'kept', 'bbbb')
        orphan = self.version('gone', 'renamed', 'cccc')
        self.registry(live)

        code, output = self.run_cli('--apply')

        self.assertEqual(PRUNE.EXIT_OK, code)
        self.assertTrue(live.is_dir())
        self.assertFalse(stale.exists())
        self.assertFalse(orphan.exists())
        self.assertIn('removed 2 directories', output)

    def test_apply_is_idempotent(self):
        live = self.version('market', 'kept', 'aaaa')
        self.version('market', 'kept', 'bbbb')
        self.registry(live)

        first, _ = self.run_cli('--apply')
        second, output = self.run_cli('--apply')

        self.assertEqual(PRUNE.EXIT_OK, first)
        self.assertEqual(PRUNE.EXIT_OK, second)
        self.assertIn('nothing to prune', output)
        self.assertTrue(live.is_dir())

    def test_a_clean_cache_succeeds_with_nothing_to_do(self):
        live = self.version('market', 'kept', 'aaaa')
        self.registry(live)

        code, output = self.run_cli('--apply')

        self.assertEqual(PRUNE.EXIT_OK, code)
        self.assertIn('nothing to prune', output)

    def test_an_unreadable_registry_removes_nothing(self):
        orphan = self.version('gone', 'renamed', 'cccc')

        code, output = self.run_cli('--apply')

        self.assertEqual(PRUNE.EXIT_REGISTRY, code)
        self.assertTrue(orphan.is_dir())
        self.assertEqual('', output)

    def test_a_malformed_registry_removes_nothing(self):
        orphan = self.version('gone', 'renamed', 'cccc')
        self.registry(raw='{ not json')

        code, _ = self.run_cli('--apply')

        self.assertEqual(PRUNE.EXIT_REGISTRY, code)
        self.assertTrue(orphan.is_dir())

    def test_a_registry_naming_no_install_paths_removes_nothing(self):
        orphan = self.version('gone', 'renamed', 'cccc')
        self.registry(raw=json.dumps({'version': 2, 'plugins': {}}))

        code, _ = self.run_cli('--apply')

        self.assertEqual(PRUNE.EXIT_REGISTRY, code)
        self.assertTrue(orphan.is_dir())

    def test_a_registry_entry_for_a_missing_directory_is_a_warning(self):
        live = self.version('market', 'kept', 'aaaa')
        self.registry(live, self.cache / 'market' / 'kept' / 'never-fetched')

        code, output = self.run_cli()

        self.assertEqual(PRUNE.EXIT_OK, code)
        self.assertIn('missing install path', output)
        self.assertIn('nothing to prune', output)

    def test_every_version_of_an_unregistered_plugin_is_an_orphan(self):
        live = self.version('market', 'kept', 'aaaa')
        first = self.version('gone', 'renamed', 'bbbb')
        second = self.version('gone', 'renamed', 'cccc')
        self.registry(live)

        states = dict(
            PRUNE.classify(PRUNE.cached_versions(self.cache), {PRUNE.normalize(live)})
        )

        self.assertEqual(PRUNE.LIVE, states[live])
        self.assertEqual(PRUNE.ORPHAN, states[first])
        self.assertEqual(PRUNE.ORPHAN, states[second])

    def test_retention_applies_only_to_a_still_installed_plugin(self):
        live = self.version('market', 'kept', 'aaaa')
        stale = self.version('market', 'kept', 'bbbb')
        orphan = self.version('gone', 'renamed', 'cccc')

        states = dict(
            PRUNE.classify(
                PRUNE.cached_versions(self.cache), {PRUNE.normalize(live)}, keep_previous=1
            )
        )

        self.assertEqual(PRUNE.LIVE, states[live])
        self.assertEqual(PRUNE.RETAINED, states[stale])
        self.assertEqual(PRUNE.ORPHAN, states[orphan])

    def test_a_removal_target_must_be_a_cached_version_directory(self):
        PRUNE.assert_within(self.cache, self.cache / 'market' / 'plugin' / 'version')
        with self.assertRaises(ValueError):
            PRUNE.assert_within(self.cache, self.cache / 'market' / 'plugin')
        with self.assertRaises(ValueError):
            PRUNE.assert_within(self.cache, self.cache.parent / 'installed_plugins.json')

    def test_the_notice_is_throttled_and_never_removes(self):
        live = self.version('market', 'kept', 'aaaa')
        stale = self.version('market', 'kept', 'bbbb')
        self.registry(live)
        state = Path(self.temp.name) / 'state'
        environ = {PRUNE.STATE_DIRECTORY_ENV: str(state)}

        first = io.StringIO()
        PRUNE.run_notice(self.config, 0, 1000.0, environ=environ, stream=first)
        second = io.StringIO()
        PRUNE.run_notice(self.config, 0, 1001.0, environ=environ, stream=second)

        self.assertIn('1 version directories', first.getvalue())
        self.assertEqual('', second.getvalue())
        self.assertTrue(stale.is_dir())

    def test_the_notice_stays_silent_on_an_unusable_registry(self):
        self.version('gone', 'renamed', 'cccc')
        stream = io.StringIO()

        code = PRUNE.run_notice(
            self.config,
            0,
            1000.0,
            environ={PRUNE.STATE_DIRECTORY_ENV: str(Path(self.temp.name) / 'state')},
            stream=stream,
        )

        self.assertEqual(PRUNE.EXIT_OK, code)
        self.assertEqual('', stream.getvalue())


if __name__ == '__main__':
    unittest.main()
