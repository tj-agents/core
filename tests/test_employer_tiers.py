import contextlib
import importlib.util
import io
import json
import re
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / '.agents/hooks' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load('tier_gate')
checker = load('check_tier_payload')
WORK = {'schema_version': 3, 'tier': 'work', 'applies': 'stack-present',
        'detect': {'fact': 'employer'}, 'session_context': 'Load work:ask-person before drafting and clip the draft.'}
EMPLOYER = {'schema_version': 3, 'tier': 'employer-a', 'applies': 'stack-present',
            'owner_repository': 'publisher/employer-a', 'detect': {'remote': '^employer-a/'},
            'employer': {'context_skill': 'communication-context'}}


class EmployerScope(unittest.TestCase):
    def setUp(self):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.root = Path(holder.name)
        self.project = self.root / 'project'
        self.project.mkdir()
        self.cache = self.root / 'profile/plugins/cache'
        self.work = self.install('work', WORK)

    def install(self, plugin, data, context=True):
        payload = self.cache / 'test-market' / plugin / '1'
        skill = payload / 'skills/communication-context'
        skill.mkdir(parents=True, exist_ok=True)
        if context:
            (skill / 'SKILL.md').write_text('---\nname: communication-context\nkind: knowledge\n---\nEmployer contacts.\n', encoding='utf-8')
        if data is not None:
            (payload / 'tier.json').write_text(data if isinstance(data, str) else json.dumps(data), encoding='utf-8')
        registry_path = self.cache.parent / 'installed_plugins.json'
        registry = json.loads(registry_path.read_text(encoding='utf-8')) if registry_path.exists() else {'plugins': {}}
        registry['plugins'][plugin + '@test-market'] = [{'installPath': str(payload)}]
        registry_path.write_text(json.dumps(registry), encoding='utf-8')
        return payload

    def found(self):
        return gate.declarations([self.cache], project=self.project)

    def remote(self, identity):
        subprocess.run(['git', 'init', '--quiet', str(self.project)], check=True, capture_output=True)
        subprocess.run(['git', '-C', str(self.project), 'config', 'remote.origin.url', 'git@example.test:' + identity + '.git'],
                       check=True, capture_output=True)

    def hooks(self):
        return ({'cwd': str(self.project), 'tool_name': 'Skill', 'tool_input': {'skill': 'work:ask-person'}},
                {'cwd': str(self.project), 'tool_name': 'PowerShell',
                 'tool_input': {'command': "Get-Content '" + str(self.work / 'skills/ask-person/SKILL.md') + "'"}})

    def test_actual_work_remote_allows_both_hosts_and_reports_exact_context(self):
        employer = self.install('employer-a', EMPLOYER)
        self.remote('employer-a/service')
        result = gate.assess(self.project, self.found())
        self.assertEqual({item.plugin for item, _ in result.applicable}, {'work', 'employer-a'})
        self.assertEqual(result.diagnostics, ())
        work = next(item for item in result.selections if item['plugin_id'] == 'work@test-market')
        self.assertEqual(work['prerequisites'], ('employer',))
        self.assertEqual(work['evidence'], ('employer-a@test-market: origin employer-a/service',))
        context = gate.statement(self.project, self.found())
        self.assertIn(str((employer / 'skills/communication-context/SKILL.md').resolve()), context)
        self.assertIn('employer-a:communication-context', context)
        self.assertEqual(context.count(WORK['session_context']), 1)
        for hook in self.hooks():
            self.assertEqual(gate.gate(hook, self.found()), 0)

    def test_session_start_output_carries_context_only_for_the_matching_project(self):
        self.install('employer-a', EMPLOYER)
        for identity, applies in (('employer-a/service', True), ('personal/project', False)):
            self.remote(identity)
            output = io.StringIO()
            with patch.object(gate, 'cache_roots', return_value=[self.cache]), \
                    patch.object(gate.sys, 'argv', ['tier_gate.py', '--session-context', '--project', str(self.project)]), \
                    contextlib.redirect_stdout(output):
                self.assertEqual(gate.main(), 0)
            context = json.loads(output.getvalue())['hookSpecificOutput']
            self.assertEqual(context['hookEventName'], 'SessionStart')
            self.assertEqual(WORK['session_context'] in context['additionalContext'], applies)
            self.assertEqual('Employer context:' in context['additionalContext'], applies)

    def test_personal_remote_blocks_both_hosts_and_omits_conditional_context(self):
        employer = self.install('employer-a', EMPLOYER)
        self.remote('personal/project')
        context = gate.statement(self.project, self.found())
        self.assertNotIn(WORK['session_context'], context)
        self.assertNotIn('Employer context:', context)
        self.assertNotIn(str(employer / 'skills/communication-context/SKILL.md'), context)
        for hook in self.hooks():
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(gate.gate(hook, self.found()), 2)
            self.assertIn('work', stderr.getvalue())

    def test_missing_malformed_and_orphaned_employers_never_establish_the_fact(self):
        self.remote('employer-a/service')
        cases = (None, '{', [], dict(EMPLOYER, employer=None),
                 dict(EMPLOYER, employer={'context_skill': '../outside'}),
                 dict(EMPLOYER, employer={'context_skill': 'communication-context', 'extra': True}),
                 dict(EMPLOYER, detect={'any': []}), dict(EMPLOYER, applies='always'))
        for data in cases:
            with self.subTest(data=data):
                self.install('employer-a', data)
                path = self.cache / 'test-market/employer-a/1/tier.json'
                if data is None:
                    path.unlink(missing_ok=True)
                result = gate.assess(self.project, self.found())
                self.assertFalse(any(item.plugin == 'work' for item, _ in result.applicable))
                self.assertEqual(result.employers, ())
                self.assertNotIn(WORK['session_context'], gate.statement(self.project, self.found()))
        employer = self.install('employer-a', EMPLOYER)
        (employer / gate.ORPHAN_MARKER).touch()
        result = gate.assess(self.project, self.found())
        self.assertEqual(result.applicable, [])
        self.assertTrue(any(item['code'] == 'orphaned-employer' for item in result.diagnostics))

    def test_missing_and_unreadable_context_skills_fail_runtime_and_payload_validation(self):
        self.remote('employer-a/service')
        employer = self.install('employer-a', EMPLOYER, context=False)
        skill = employer / 'skills/communication-context/SKILL.md'
        for body in (None, b'\xff', b'Not a skill'):
            if body is not None:
                skill.write_bytes(body)
            result = gate.assess(self.project, self.found())
            self.assertEqual(result.applicable, [])
            self.assertTrue(any(item['code'] == 'missing-employer-context' for item in result.diagnostics))
            problems = []
            checker.check_tier_declaration(employer, problems)
            self.assertTrue(any('shipped within this payload' in item for item in problems), problems)

    def test_context_path_cannot_follow_a_symlink_outside_the_payload(self):
        employer = self.install('employer-a', EMPLOYER)
        skill = employer / 'skills/communication-context/SKILL.md'
        target = self.root / 'outside.md'
        target.write_text('External context', encoding='utf-8')
        skill.unlink()
        try:
            skill.symlink_to(target)
        except OSError as error:
            self.skipTest('Symlinks unavailable: ' + str(error))
        self.remote('employer-a/service')
        self.assertEqual(gate.assess(self.project, self.found()).applicable, [])
        self.assertIsNone(gate.employer_context_path(employer, 'communication-context'))

    def test_resolved_context_path_must_stay_inside_its_payload(self):
        employer = self.install('employer-a', EMPLOYER)
        skill = employer / 'skills/communication-context/SKILL.md'
        target = self.root / 'outside.md'
        resolve = Path.resolve
        skill = skill.resolve()
        with patch.object(Path, 'resolve', lambda path: target if path == skill else resolve(path)):
            self.assertIsNone(gate.employer_context_path(employer, 'communication-context'))
            self.assertTrue(any(item['code'] == 'missing-employer-context'
                                for item in gate.v3_declaration_diagnostics(EMPLOYER, payload_dir=employer)))

    def test_unresolvable_context_path_does_not_turn_into_a_hook_exception(self):
        employer = self.install('employer-a', EMPLOYER)
        with patch.object(Path, 'resolve', side_effect=RuntimeError('Symlink loop')):
            self.assertIsNone(gate.employer_context_path(employer, 'communication-context'))

    def test_reserved_fact_cannot_be_spoofed_even_in_nested_composition(self):
        spoof = {'employer': gate.PredicateResult(self.project, True, ['fake employer'])}
        for node in ({'fact': 'employer'}, {'all': [{'fact': 'employer'}, {'file': 'marker'}]}):
            (self.project / 'marker').touch()
            direct = gate.evaluate_predicate(self.project, node, spoof)
            self.assertFalse(direct.matched)
            self.assertTrue(any(item['code'] == 'reserved-fact' for item in direct.diagnostics))
            declaration = gate.Declaration('work', 'test-market', dict(WORK, detect=node), self.work)
            result = gate.assess(self.project, [declaration], facts=spoof)
            self.assertEqual(result.applicable, [])
            self.assertEqual(result.diagnostics, ())
        self.install('employer-a', EMPLOYER)
        self.remote('employer-a/service')
        false_spoof = {'employer': gate.PredicateResult(self.project, False)}
        result = gate.assess(self.project, self.found(), facts=false_spoof)
        self.assertTrue(any(item.plugin == 'work' for item, _ in result.applicable))

    def test_owner_identity_and_overrides_do_not_establish_employer(self):
        self.install('employer-a', EMPLOYER)
        self.remote('publisher/employer-a')
        with patch.dict(gate.os.environ, {gate.OVERRIDE_VARIABLE: 'employer-a,work'}):
            result = gate.assess(self.project, self.found())
        self.assertEqual(result.applicable, [])
        self.assertEqual(result.employers, ())

    def test_employer_cannot_depend_on_itself_directly_or_in_a_matching_alternative(self):
        (self.project / 'marker').touch()
        for node in ({'fact': 'employer'}, {'any': [{'file': 'marker'}, {'fact': 'employer'}]},
                     {'all': [{'file': 'marker'}, {'any': [{'fact': 'employer'}, {'file': 'marker'}]}]}):
            with self.subTest(node=node):
                employer = self.install('employer-a', dict(EMPLOYER, detect=node))
                result = gate.assess(self.project, self.found(), facts={'employer': gate.PredicateResult(self.project, True)})
                self.assertEqual(result.applicable, [])
                self.assertTrue(any(item['code'] == 'employer-self-dependency' for item in result.diagnostics))
                problems = []
                checker.check_tier_declaration(employer, problems)
                self.assertTrue(any('cannot depend' in item for item in problems))

    def test_multiple_matching_employers_are_all_reported(self):
        (self.project / 'marker').touch()
        payloads = [self.install(name, dict(EMPLOYER, tier=name, detect={'file': 'marker'}))
                    for name in ('employer-a', 'employer-b')]
        result = gate.assess(self.project, self.found())
        self.assertEqual([item.plugin for item, _ in result.employers], ['employer-a', 'employer-b'])
        context = gate.statement(self.project, self.found())
        self.assertEqual(context.count('Employer context:'), 2)
        for payload in payloads:
            self.assertIn(str((payload / 'skills/communication-context/SKILL.md').resolve()), context)
        self.assertEqual(context.count(WORK['session_context']), 1)

    def test_legacy_metadata_cannot_supply_employer_evidence(self):
        self.remote('employer-a/service')
        for version in (1, 2):
            employer = self.install('employer-a', dict(EMPLOYER, schema_version=version, detect={'files': ['marker']}))
            (self.project / 'marker').touch()
            result = gate.assess(self.project, self.found())
            self.assertEqual(result.employers, ())
            self.assertFalse(any(item.plugin == 'work' for item, _ in result.applicable))
            problems = []
            checker.check_tier_declaration(employer, problems)
            self.assertTrue(any('employer requires schema_version 3' in item for item in problems))

    def test_only_valid_applicable_tiers_emit_one_line_session_context(self):
        declaration = gate.Declaration('base', 'test-market', {'schema_version': 3, 'tier': 'base',
                                      'applies': 'always', 'session_context': 'Always load this context.'})
        self.assertIn('Always load this context.', gate.statement(self.project, [declaration]))
        for text in ('', '  ', 'first\nsecond', 'first\rsecond', 'first\u2028second'):
            invalid = gate.Declaration('base', 'test-market', dict(declaration.data, session_context=text))
            result = gate.assess(self.project, [invalid])
            self.assertEqual(result.ubiquitous, [])
            self.assertTrue(result.diagnostics)
        legacy = gate.Declaration('base', 'test-market', dict(declaration.data, schema_version=2))
        self.assertEqual(gate.statement(self.project, [legacy]), '')

    def test_employer_context_shipping_is_required_for_in_memory_declarations_too(self):
        (self.project / 'marker').touch()
        provider = gate.Declaration('employer-a', 'test-market', dict(EMPLOYER, detect={'file': 'marker'}))
        result = gate.assess(self.project, [provider, gate.Declaration('work', 'test-market', WORK)])
        self.assertEqual(result.applicable, [])
        self.assertTrue(any(item['code'] == 'missing-employer-context' for item in result.diagnostics))

    def test_schema_shapes_and_runtime_agree_on_new_field_constraints(self):
        schema = json.loads((ROOT / '.agents/schemas/tier.schema.json').read_text(encoding='utf-8'))
        slug = schema['properties']['employer']['properties']['context_skill']['pattern']
        context = schema['properties']['session_context']['pattern']
        self.assertIsNotNone(re.search(slug, 'communication-context'))
        for value in ('../outside', 'work:context', 'Context', 'context\n', ''):
            self.assertIsNone(re.search(slug, value))
            data = dict(EMPLOYER, employer={'context_skill': value})
            self.assertTrue(gate.v3_declaration_diagnostics(data))
        self.assertIsNotNone(re.search(context, 'Load this context.'))
        for value in ('', '  ', 'first\nsecond', 'first\r', 'first\u2028second', 'first\n'):
            self.assertIsNone(re.search(context, value))
            self.assertTrue(gate.v3_declaration_diagnostics(dict(WORK, session_context=value)))
        self.assertFalse(schema['allOf'][0]['else']['properties']['employer'])
        self.assertFalse(schema['allOf'][0]['else']['properties']['session_context'])
        employer = schema['allOf'][-1]
        self.assertEqual(employer['if'], {'required': ['employer']})
        self.assertEqual(employer['then']['properties']['applies'], {'const': 'stack-present'})
        recursive = schema['$defs']['nonEmployerPredicate']
        self.assertEqual(recursive['allOf'][1]['not']['properties']['fact'], {'const': 'employer'})
        for operator in ('all', 'any'):
            self.assertEqual(recursive['properties'][operator]['items'], {'$ref': '#/$defs/nonEmployerPredicate'})

    def test_shipped_base_harness_and_resources_cover_the_shared_gate_contract(self):
        manifest = json.loads((ROOT / '.agents/plugins/harness/base.json').read_text(encoding='utf-8'))
        self.assertIn({'path': 'hooks/tier_gate.py', 'hosts': ['claude', 'codex']}, manifest['requires']['hooks'])
        resources = json.loads((ROOT / '.agents/plugins/sources.json').read_text(encoding='utf-8'))['resources']
        for source, destination in (('.agents/hooks/tier_gate.py', 'hooks/tier_gate.py'),
                                    ('.agents/hooks/check_tier_payload.py', 'hooks/check_tier_payload.py'),
                                    ('.agents/schemas/tier.schema.json', 'schemas/tier.schema.json')):
            self.assertIn({'plugin': 'base', 'source': source, 'destination': destination}, resources)
            self.assertEqual((ROOT / source).read_text(encoding='utf-8'),
                             (ROOT / 'plugins/base' / destination).read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()