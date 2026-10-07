import copy
import importlib.util
import itertools
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / '.agents/machine/utility/bootstrap-capabilities/scripts/selection_profiles.py'
SPEC = importlib.util.spec_from_file_location('selection_profiles', SCRIPT)
profiles = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(profiles)
FIXTURE = json.loads((ROOT / 'tests/fixtures/selection-profile.json').read_text())
OWNER = FIXTURE['owner_package']
CANDIDATES = [OWNER, 'cpp-agents/gpp', 'cpp-agents/msvc', 'cpp-agents/win32']


class SelectionProfilesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.metadata = copy.deepcopy(FIXTURE)

    def evaluate(self, document=None, filenames=()):
        if document is not None:
            target = self.root / self.metadata['document']
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(document), encoding='utf-8')
        return profiles.evaluate(self.metadata, OWNER, CANDIDATES, self.root, filenames)

    def assert_selection(self, document, names):
        result = self.evaluate(document)
        self.assertEqual(result['selected_ids'], sorted('cpp-agents/' + n for n in names))
        self.assertEqual(result['diagnostics'], [])
        return result

    def test_modern_matrix_and_defaults(self):
        for toolchain, apis in itertools.product((None, 'gpp', 'msvc'), ([], ['win32'])):
            with self.subTest(toolchain=toolchain, apis=apis):
                expected = ['cpp'] + ([toolchain] if toolchain else []) + apis
                self.assert_selection({'profile': {'toolchain': toolchain, 'apis': apis}}, expected)
        self.assert_selection({'profile': {}}, ['cpp'])
        self.assert_selection({'profile': {'extra': 'ignored', 'apis': ['win32', 'win32']}}, ['cpp', 'win32'])

    def test_legacy_table_and_independent_first_match_groups(self):
        cases = [({'kind': 'generic'}, ['cpp']), ({'kind': 'portable'}, ['cpp']),
                 ({'kind': 'gcc'}, ['cpp', 'gpp']), ({'kind': 'gpp'}, ['cpp', 'gpp']),
                 ({'kind': 'windows'}, ['cpp', 'msvc', 'win32']),
                 ({'layers': []}, ['cpp']), ({'layers': ['base', 'cpp']}, ['cpp']),
                 ({'layers': ['msvc']}, ['cpp', 'msvc']),
                 ({'layers': ['gcc', 'windows', 'msvc', 'win32']}, ['cpp', 'gpp', 'win32']),
                 ({'layers': ['win32', 'win32']}, ['cpp', 'win32'])]
        for document, expected in cases:
            with self.subTest(document=document):
                self.assert_selection(document, expected)
        result = self.assert_selection({'layers': ['gcc', 'windows']}, ['cpp', 'gpp', 'win32'])
        self.assertEqual(result['matched_rules'], [[0, 0], [1, 0]])

    def test_terminal_precedence_and_fallback(self):
        self.assert_selection({'profile': {}, 'kind': 'windows', 'layers': ['gpp']}, ['cpp'])
        self.assert_selection({'profile': False, 'kind': 'unknown', 'layers': ['gpp']}, ['cpp', 'gpp'])
        self.assert_selection({'kind': 'portable', 'layers': ['windows']}, ['cpp'])
        for field in [{'toolchain': 'unknown'}, {'apis': [{}]}, {'apis': [['win32']]},
                      {'apis': None}, {'toolchain': True}]:
            result = self.evaluate({'profile': field, 'kind': 'windows'}, ['src/UNIT.CPP'])
            self.assertEqual(result['selected_ids'], [OWNER])
            self.assertEqual(result['selected_form'], 'profile')
            self.assertEqual(len(result['diagnostics']), 1)
            self.assertIn('form profile:', result['diagnostics'][0])
        result = self.evaluate({'layers': ['unknown']})
        self.assertEqual(result['selected_ids'], [])
        self.assertIn('layers', result['diagnostics'][0])

    def test_missing_document_and_exact_marker_semantics(self):
        self.assertEqual(self.evaluate(filenames=['a.txt'])['selected_ids'], [])
        result = self.evaluate(filenames=['b/CMakeLists.txt', 'a/X.CPP', 'a/X.CPP', 'cmakelists.txt'])
        self.assertEqual(result['selected_ids'], [OWNER])
        self.assertEqual(result['marker_matches'], ['a/X.CPP', 'b/CMakeLists.txt'])

    def test_typed_scalar_and_array_equality(self):
        field = self.metadata['forms'][0]['fields']['toolchain']
        field['values'] = [None, True, 1, 1.0]
        rules = self.metadata['forms'][0]['selection_groups'][0]['rules']
        rules[:] = [{'field': 'toolchain', 'equals': True, 'plugins': ['gpp']},
                    {'field': 'toolchain', 'equals': 1, 'plugins': ['msvc']},
                    {'field': 'toolchain', 'equals': 1.0, 'plugins': ['win32']}]
        for value, selected in [(True, 'gpp'), (1, 'msvc'), (1.0, 'msvc')]:
            self.assert_selection({'profile': {'toolchain': value}}, ['cpp', selected])
        field = self.metadata['forms'][0]['fields']['apis']
        field['members'] = [True, 1]
        rule = self.metadata['forms'][0]['selection_groups'][1]['rules'][0]
        rule['intersects'] = [True]
        self.assert_selection({'profile': {'apis': [1]}}, ['cpp'])
        self.assert_selection({'profile': {'apis': [True]}}, ['cpp', 'win32'])
        rule['intersects'] = [1]
        self.assert_selection({'profile': {'apis': [1.0]}}, ['cpp', 'win32'])
        self.assert_selection({'profile': {'apis': [True]}}, ['cpp'])

    def test_metadata_rejects_unknown_keys_invalid_domains_paths_and_outputs(self):
        mutations = [lambda m: m.update(extra=True), lambda m: m.update(schema_version=True),
                     lambda m: m.update(document='../routes.json'),
                     lambda m: m.update(document='C:/routes.json'),
                     lambda m: m.update(document='a//b'),
                     lambda m: m['markers']['suffixes'].append('cpp'),
                     lambda m: m['markers']['basenames'].append('a/b'),
                     lambda m: m['forms'].append(copy.deepcopy(m['forms'][0])),
                     lambda m: m['forms'][0]['select'].update(extra=1),
                     lambda m: m['forms'][0]['select'].update(type='execute'),
                     lambda m: m['forms'][0]['fields']['apis'].update(default=[{}]),
                     lambda m: m['forms'][0]['fields']['toolchain'].update(values=[{}]),
                     lambda m: m['forms'][0]['fields']['toolchain'].update(path=[0]),
                     lambda m: m['forms'][0]['selection_groups'][0]['rules'][0].update(field='missing'),
                     lambda m: m['forms'][0]['selection_groups'][0]['rules'][0].update(plugins=[]),
                     lambda m: m['valid_profile_plugins'].append('other/cpp'),
                     lambda m: m['valid_profile_plugins'].append('cpp-compat')]
        for mutate in mutations:
            metadata = copy.deepcopy(FIXTURE)
            mutate(metadata)
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                profiles.validate_metadata(metadata, OWNER, CANDIDATES)
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            profiles.validate_metadata(FIXTURE, 'other/cpp', ['other/cpp'])
        with self.assertRaisesRegex(ValueError, 'candidate'):
            profiles.validate_metadata(FIXTURE, OWNER, [OWNER])

    def test_unreadable_invalid_oversized_and_nonfile_documents_retain_markers(self):
        target = self.root / self.metadata['document']
        target.parent.mkdir(parents=True)
        for content in [b'{', b'[]', b'\xff', b'{"value":NaN}', b'[' * 2000,
                        b' ' * (profiles.MAX_DOCUMENT_BYTES + 1)]:
            target.write_bytes(content)
            result = self.evaluate(filenames=['x.cpp'])
            self.assertEqual(result['selected_ids'], [OWNER])
            self.assertEqual(len(result['diagnostics']), 1)
        target.unlink()
        target.mkdir()
        self.assertIn('file', self.evaluate(filenames=['x.cpp'])['diagnostics'][0])

    def test_escaping_real_directory_link_is_rejected_even_when_missing(self):
        with tempfile.TemporaryDirectory() as outside:
            link = self.root / '.agents'
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError:
                if os.name != 'nt':
                    raise
                subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), outside],
                               check=True, capture_output=True)
            try:
                result = self.evaluate(filenames=['x.cpp'])
                self.assertEqual(result['selected_ids'], [OWNER])
                self.assertIn('escapes', result['diagnostics'][0])
                (Path(outside) / 'skill-routes.json').write_text('{"profile":{}}')
                self.assertIn('escapes', self.evaluate()['diagnostics'][0])
            finally:
                if link.is_symlink():
                    link.unlink()
                else:
                    link.rmdir()

    def test_supplied_filename_paths_are_strict(self):
        for filename in ['.', '../x.cpp', '/x.cpp', 'C:/x.cpp', 'a\\x.cpp', './x.cpp']:
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                self.evaluate(filenames=[filename])

    def test_invalid_scope_roots_raise_instead_of_returning_marker_selections(self):
        file_root = self.root / 'file-root'
        file_root.write_text('not a directory')
        for root in [self.root / 'missing-root', file_root]:
            for filenames in [[], ['x.cpp']]:
                with self.subTest(root=root, filenames=filenames), self.assertRaisesRegex(ValueError, 'scope root'):
                    profiles.evaluate(self.metadata, OWNER, CANDIDATES, root, filenames)

    def test_nul_paths_are_rejected_before_marker_selection_or_document_reading(self):
        with self.assertRaises(ValueError):
            self.evaluate(filenames=['x\0.cpp'])
        self.metadata['document'] = '.agents/skill\0-routes.json'
        with self.assertRaises(ValueError):
            profiles.validate_metadata(self.metadata, OWNER, CANDIDATES)
        with self.assertRaises(ValueError):
            self.evaluate(filenames=['x.cpp'])


if __name__ == '__main__':
    unittest.main()
