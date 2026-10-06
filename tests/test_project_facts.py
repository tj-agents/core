import json
from pathlib import Path
import tempfile
import unittest
from test_tier_predicates import gate, checker


class ProjectFacts(unittest.TestCase):
    def setUp(self):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.root = Path(holder.name)

    def write(self, name, body):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body if isinstance(body, str) else json.dumps(body), encoding='utf-8')
        return path

    def graph(self):
        return gate.discover_projects(self.root)

    def dependency(self, kind, identity):
        return {'dependency': {'kind': kind, 'id': identity}}

    def test_direct_dependencies_preserve_manifest_identity_and_case_rules(self):
        self.write('A.csproj', '<Project Sdk="Microsoft.NET.Sdk.Web"><ItemGroup><PackageReference Include="Example"/><FrameworkReference Include="Microsoft.AspNetCore.App"/></ItemGroup></Project>')
        self.write('B.csproj', '<Project Sdk="Microsoft.NET.Sdk"/>')
        graph = self.graph()
        self.assertEqual(set(graph.projects), {'A.csproj', 'B.csproj'})
        for kind, identity in [('nuget', 'example'), ('sdk', 'Microsoft.NET.Sdk.Web'), ('framework', 'Microsoft.AspNetCore.App')]:
            result = gate.evaluate_project(graph, 'A.csproj', self.dependency(kind, identity))
            self.assertTrue(result.matched)
            self.assertEqual(result.scope, 'A.csproj')
            self.assertIn('A.csproj: A.csproj', result.evidence)
        self.assertFalse(gate.evaluate_project(graph, 'B.csproj', self.dependency('nuget', 'Example')).matched)

    def test_central_versions_and_arbitrary_json_do_not_create_consumption(self):
        self.write('Directory.Packages.props', '<Project><ItemGroup><PackageVersion Include="Example" Version="1"/></ItemGroup></Project>')
        self.write('A.csproj', '<Project Sdk="Microsoft.NET.Sdk"/>')
        self.write('app/package.json', {'description': 'react', 'resolutions': {'react': '1'}, 'dependencies': {'axios': '1'}})
        graph = self.graph()
        self.assertFalse(gate.evaluate_project(graph, 'A.csproj', self.dependency('nuget', 'Example')).matched)
        self.assertFalse(gate.evaluate_project(graph, 'app/package.json', self.dependency('npm', 'react')).matched)
        self.assertTrue(gate.evaluate_project(graph, 'app/package.json', self.dependency('npm', 'axios')).matched)
        self.assertFalse(gate.evaluate_project(graph, 'app/package.json', self.dependency('npm', 'Axios')).matched)

    def test_condition_and_import_are_unknown_without_execution(self):
        self.write('A.csproj', '<Project><ItemGroup Condition="$(UseIt)"><PackageReference Include="Example"/></ItemGroup><Import Project="custom.props"/></Project>')
        self.write('custom.props', '<Project/>')
        graph = self.graph()
        result = gate.evaluate_project(graph, 'A.csproj', self.dependency('nuget', 'Example'))
        self.assertFalse(result.matched)
        self.assertEqual({item['path'] for item in result.diagnostics}, {'A.csproj', 'custom.props'})
        self.assertEqual({item['code'] for item in result.diagnostics}, {'unknown-dependency'})

    def test_literal_prefix_has_no_wildcard_or_regex_matching(self):
        self.write('A.csproj', '<Project><ItemGroup><PackageReference Include="Example.Extension"/></ItemGroup></Project>')
        graph = self.graph()
        for prefix, expected in [('example.', True), ('Example.*', False), ('Example\\..*', False)]:
            self.assertEqual(gate.evaluate_project(graph, 'A.csproj', {'dependency': {'kind': 'nuget', 'prefix': prefix}}).matched, expected)

    def test_project_edges_do_not_pool_sibling_facts(self):
        self.write('A.csproj', '<Project><ItemGroup><ProjectReference Include="B.csproj"/><ProjectReference Include="C.csproj"/></ItemGroup></Project>')
        self.write('B.csproj', '<Project><ItemGroup><PackageReference Include="Left"/></ItemGroup></Project>')
        self.write('C.csproj', '<Project><ItemGroup><PackageReference Include="Right"/></ItemGroup></Project>')
        graph = self.graph()
        combined = {'all': [self.dependency('nuget', 'Left'), self.dependency('nuget', 'Right')]}
        self.assertFalse(gate.evaluate_project(graph, 'A.csproj', combined).matched)
        self.assertFalse(gate.evaluate_project(graph, 'A.csproj', {'project_dependency': {'transitive': True, 'where': combined}}).matched)
        result = gate.evaluate_project(graph, 'A.csproj', {'project_dependency': {'transitive': False, 'where': self.dependency('nuget', 'Left')}})
        self.assertTrue(result.matched)
        self.assertIn('A.csproj -> B.csproj', result.evidence)
        self.assertIn('B.csproj: B.csproj', result.evidence)

    def test_transitive_edges_and_cycles_are_bounded(self):
        self.write('A.csproj', '<Project><ItemGroup><ProjectReference Include="B.csproj"/></ItemGroup></Project>')
        self.write('B.csproj', '<Project><ItemGroup><ProjectReference Include="A.csproj"/><ProjectReference Include="C.csproj"/></ItemGroup></Project>')
        self.write('C.csproj', '<Project><ItemGroup><PackageReference Include="Example"/></ItemGroup></Project>')
        graph = self.graph()
        where = self.dependency('nuget', 'Example')
        self.assertFalse(gate.evaluate_project(graph, 'A.csproj', {'project_dependency': {'transitive': False, 'where': where}}).matched)
        result = gate.evaluate_project(graph, 'A.csproj', {'project_dependency': {'transitive': True, 'where': where}})
        self.assertTrue(result.matched)
        self.assertIn('B.csproj -> C.csproj', result.evidence)

    def test_missing_and_conditional_targets_remain_unknown(self):
        self.write('A.csproj', '<Project><ItemGroup><ProjectReference Include="Missing.csproj"/><ProjectReference Include="B.csproj" Condition="$(UseIt)"/></ItemGroup></Project>')
        self.write('B.csproj', '<Project><ItemGroup><PackageReference Include="Example"/></ItemGroup></Project>')
        result = gate.evaluate_project(self.graph(), 'A.csproj', {'project_dependency': {'transitive': True, 'where': self.dependency('nuget', 'Example')}})
        self.assertFalse(result.matched)
        self.assertEqual(len(result.diagnostics), 2)

    def test_explicit_workspace_and_file_edges_do_not_include_unreferenced_packages(self):
        self.write('package.json', {'workspaces': ['packages/*']})
        self.write('packages/a/package.json', {'name': 'a', 'dependencies': {'b': 'workspace:*'}})
        self.write('packages/b/package.json', {'name': 'b', 'peerDependencies': {'react': '18'}})
        self.write('packages/c/package.json', {'name': 'c', 'dependencies': {'other': '1'}})
        self.write('packages/d/package.json', {'name': 'd', 'dependencies': {'b': 'file:../b'}})
        graph = self.graph()
        for identity in ('packages/a/package.json', 'packages/d/package.json'):
            self.assertTrue(gate.evaluate_project(graph, identity, {'project_dependency': {'transitive': True, 'where': self.dependency('npm', 'react')}}).matched)
            self.assertFalse(gate.evaluate_project(graph, identity, {'project_dependency': {'transitive': True, 'where': self.dependency('npm', 'other')}}).matched)
        self.assertFalse(gate.evaluate_project(graph, 'package.json', self.dependency('npm', 'react')).matched)

    def test_fact_definitions_validate_references_cycles_and_conflicts(self):
        self.write('A.csproj', '<Project><ItemGroup><PackageReference Include="Example"/></ItemGroup></Project>')
        definitions = {'technology.example': self.dependency('nuget', 'Example')}
        result = gate.evaluate_project(self.graph(), 'A.csproj', {'fact': 'technology.example'}, definitions)
        self.assertTrue(result.matched)
        for invalid in ({'a': {'fact': 'b'}, 'b': {'fact': 'a'}}, {'a': {'all': []}}):
            self.assertTrue(gate.fact_definition_diagnostics(invalid))
        data = {'schema_version': 3, 'tier': 'example', 'applies': 'stack-present', 'detect': {'fact': 'technology.example'}, 'fact_definitions': definitions}
        first = gate.Declaration('first', 'test', data)
        second = gate.Declaration('second', 'test', dict(data, fact_definitions={'technology.example': self.dependency('nuget', 'Other')}))
        self.assertEqual(gate.compose_fact_definitions([first])[1], [])
        self.assertEqual(gate.compose_fact_definitions([first, second])[1][0]['code'], 'conflicting-fact-definition')
        payload = self.root / 'payload'
        payload.mkdir()
        (payload / 'tier.json').write_text(json.dumps(data), encoding='utf-8')
        problems = []
        checker.check_tier_declaration(payload, problems)
        self.assertEqual(problems, [])

    def test_removes_imports_and_macros_do_not_leave_definite_positives(self):
        for suffix in ('<PackageReference Remove="Example" Condition="$(RemoveIt)"/>', '<Import Project="missing.props"/>'):
            self.write('A.csproj', '<Project><ItemGroup><PackageReference Include="Example"/>' + suffix + '</ItemGroup></Project>')
            result = gate.evaluate_project(self.graph(), 'A.csproj', self.dependency('nuget', 'Example'))
            self.assertFalse(result.matched)
            self.assertTrue(result.diagnostics)
        self.write('A.csproj', '<Project><ItemGroup><PackageReference Include="Left;Right"/><PackageReference Include="$(Packages)"/></ItemGroup></Project>')
        result = gate.evaluate_project(self.graph(), 'A.csproj', self.dependency('nuget', 'Left'))
        self.assertFalse(result.matched)
        self.assertTrue(result.diagnostics)
        self.write('A.csproj', '<Project><ItemGroup><PackageReference Include="Left;Right"/></ItemGroup></Project>')
        graph = self.graph()
        self.assertTrue(gate.evaluate_project(graph, 'A.csproj', self.dependency('nuget', 'Left')).matched)
        self.assertTrue(gate.evaluate_project(graph, 'A.csproj', self.dependency('nuget', 'Right')).matched)

    def test_malformed_npm_fields_discard_partial_dependency_results(self):
        self.write('package.json', {'dependencies': {'react': '18'}, 'peerDependencies': 'invalid'})
        result = gate.evaluate_project(self.graph(), 'package.json', self.dependency('npm', 'react'))
        self.assertFalse(result.matched)
        self.assertTrue(result.diagnostics)

    def test_normal_workspace_versions_are_explicit_edges_or_unknown(self):
        self.write('package.json', {'workspaces': ['packages/*']})
        self.write('packages/a/package.json', {'name': 'a', 'dependencies': {'b': '1.0.0'}})
        self.write('packages/b/package.json', {'name': 'b', 'version': '1.0.0', 'dependencies': {'react': '18'}})
        graph = self.graph()
        node = {'project_dependency': {'transitive': True, 'where': self.dependency('npm', 'react')}}
        self.assertTrue(gate.evaluate_project(graph, 'packages/a/package.json', node).matched)
        self.write('packages/a/package.json', {'name': 'a', 'dependencies': {'b': '^1.0.0'}})
        result = gate.evaluate_project(self.graph(), 'packages/a/package.json', node)
        self.assertFalse(result.matched)
        self.assertEqual(result.diagnostics[0]['code'], 'unknown-project-reference')

    def test_malformed_fact_definitions_stay_blocked_through_discovery(self):
        cache = self.root / 'cache'
        payload = cache / 'test' / 'example' / '1'
        payload.mkdir(parents=True)
        data = {'schema_version': 3, 'tier': 'example', 'applies': 'stack-present', 'detect': {'fact': 'a'}, 'fact_definitions': {'a': {'all': None}}}
        (payload / 'tier.json').write_text(json.dumps(data), encoding='utf-8')
        found = gate.declarations([cache])
        self.assertEqual(found[0].diagnostics[0]['code'], 'malformed-predicate')
        self.assertEqual(gate.assess(self.root, found).blocked, found)

    def test_fact_composition_allows_foreign_references_and_detects_global_failures(self):
        self.write('A.csproj', '<Project><ItemGroup><PackageReference Include="Example"/></ItemGroup></Project>')
        def declaration(name, definitions, detect):
            return gate.Declaration(name, 'test', {'schema_version': 3, 'tier': name, 'applies': 'stack-present',
                                                  'detect': detect, 'fact_definitions': definitions})
        first = declaration('first', {'first.fact': {'fact': 'second.fact'}}, {'fact': 'first.fact'})
        second = declaration('second', {'second.fact': self.dependency('nuget', 'Example')}, {'fact': 'second.fact'})
        self.assertEqual(gate.v3_declaration_diagnostics({'schema_version': 3, 'tier': 'first', 'applies': 'stack-present',
                                                        'detect': first.detect, 'fact_definitions': first.fact_definitions}), [])
        definitions, problems = gate.compose_fact_definitions([first, second])
        self.assertEqual(problems, [])
        self.assertTrue(gate.evaluate_project(self.graph(), 'A.csproj', first.detect, definitions).matched)
        self.assertEqual(gate.compose_fact_definitions([first])[1][0]['code'], 'unknown-fact-definition')
        cyclic = declaration('second', {'second.fact': {'fact': 'first.fact'}}, {'fact': 'second.fact'})
        self.assertTrue(any(item['code'] == 'cyclic-fact-definition' for item in gate.compose_fact_definitions([first, cyclic])[1]))
        supplied = {'second.fact': gate.PredicateResult('A.csproj', True, ['A.csproj'])}
        definitions, problems = gate.compose_fact_definitions([first], supplied)
        self.assertEqual(problems, [])
        self.assertTrue(gate.evaluate_project(self.graph(), 'A.csproj', first.detect, definitions, facts=supplied).matched)
        self.assertFalse(gate.evaluate_project(self.graph(), 'A.csproj', first.detect, definitions,
                                              facts={'second.fact': gate.PredicateResult('Other.csproj', True)}).matched)

    def test_new_primitives_require_project_identity_and_validate_shape(self):
        dependency = self.dependency('nuget', 'Example')
        self.assertEqual(gate.evaluate_predicate(self.root, dependency).diagnostics[0]['code'], 'project-scope-required')
        for invalid in ({'dependency': {'kind': 'nuget', 'id': 'Example', 'prefix': 'Example'}},
                        {'dependency': {'kind': 'unknown', 'id': 'Example'}},
                        {'project_dependency': {'where': dependency}},
                        {'project_dependency': {'transitive': 'true', 'where': dependency}}):
            self.assertTrue(gate.predicate_diagnostics(invalid))


if __name__ == '__main__':
    unittest.main()
