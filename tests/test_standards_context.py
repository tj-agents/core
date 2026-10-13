import json
import os
import subprocess
from pathlib import Path
import tempfile
import unittest
from test_tier_predicates import gate


class StandardsContexts(unittest.TestCase):
    def setUp(self):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.root = Path(holder.name)
        self.write('a/A.csproj', '<Project Sdk="Microsoft.NET.Sdk"/>')
        self.write('b/B.csproj', '<Project Sdk="Microsoft.NET.Sdk"/>')

    def write(self, name, body):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding='utf-8')
        return path

    def context(self, scopes=(), evidence=(), additional=()):
        graph = gate.discover_projects(self.root)
        context = gate.load_standards_context(graph, {'schema_version': 1, 'scopes': list(scopes), 'dependency_evidence': list(evidence)}, additional)
        return graph, context

    def test_absence_never_selects_house_rules(self):
        graph = gate.discover_projects(self.root)
        context = gate.load_standards_context(graph)
        self.assertEqual(context.diagnostics, [])
        predicate = {'context': {'key': 'house.dotnet', 'equals': 'tommy'}}
        self.assertFalse(gate.evaluate_project(graph, 'a/A.csproj', predicate, context=context).matched)

    def test_context_facets_combine_without_replacing_scopes(self):
        graph, context = self.context([{'root': '.', 'architecture': ['first']},
                                       {'root': 'a', 'house': {'dotnet': 'tommy'}, 'architecture': ['second'], 'adopted_suites': ['integration']}])
        values, evidence = context.for_project('a/A.csproj')
        self.assertEqual(values['architecture'], ['first', 'second'])
        self.assertEqual(len(evidence), 2)
        self.assertTrue(gate.evaluate_project(graph, 'a/A.csproj', {'context': {'key': 'house.dotnet', 'equals': 'tommy'}}, context=context).matched)
        self.assertNotIn('house.dotnet', context.for_project('b/B.csproj')[0])

    def test_generic_external_house_claims_conflict_without_organization_rosters(self):
        graph, context = self.context([{'root': '.', 'house': {'dotnet': 'first'}}], additional=[{'root': 'a', 'house': {'dotnet': 'second'}}])
        self.assertEqual(context.diagnostics[0]['code'], 'conflicting-context')
        result = gate.evaluate_project(graph, 'a/A.csproj', {'context': {'key': 'house.dotnet', 'equals': 'first'}}, context=context)
        self.assertFalse(result.matched)
        self.assertTrue(result.diagnostics)
        unrelated = gate.evaluate_project(graph, 'b/B.csproj', {'context': {'key': 'house.dotnet', 'equals': 'first'}}, context=context)
        self.assertTrue(unrelated.matched)
        self.assertFalse(unrelated.diagnostics)
        _, separate = self.context([{'root': 'a', 'house': {'dotnet': 'first'}}, {'root': 'b', 'house': {'dotnet': 'second'}}])
        self.assertEqual(separate.diagnostics, [])

    def test_invalid_context_fields_versions_and_paths_are_diagnosed(self):
        for scopes in ([{'root': '../escape'}], [{'root': str(self.root)}], [{'root': 'a', 'exclude': ['rule']}],
                       [{'root': 'a', 'house': {'dotnet': None}}], [{'root': 'a', 'architecture': ['x', 'x']}]):
            with self.subTest(scopes=scopes):
                self.assertTrue(self.context(scopes)[1].diagnostics)
        for data in ({'schema_version': 2, 'scopes': []}, {'schema_version': True, 'scopes': []}, {'schema_version': 1, 'scopes': [], 'override': []}):
            self.assertTrue(gate.load_standards_context(gate.discover_projects(self.root), data).diagnostics)

    def test_escaping_symlink_scope_is_rejected(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        try:
            (self.root / 'escape').symlink_to(outside.name, target_is_directory=True)
        except OSError as error:
            self.skipTest(str(error))
        self.assertTrue(self.context([{'root': 'escape'}])[1].diagnostics)

    @unittest.skipUnless(os.name == 'nt', 'NTFS junction regression requires Windows')
    def test_junction_escape_cannot_supply_context_or_manifest_facts(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        (Path(outside.name) / 'Outside.csproj').write_text('<Project/>', encoding='utf-8')
        link = self.root / 'junction'
        command = "New-Item -ItemType Junction -Path '" + str(link).replace("'", "''") + "' -Target '" + outside.name.replace("'", "''") + "' -ErrorAction Stop | Out-Null"
        result = subprocess.run(['pwsh', '-NoProfile', '-Command', command], capture_output=True, text=True)
        if result.returncode:
            self.skipTest('Host cannot create a test junction: ' + result.stderr.strip())
        self.addCleanup(link.rmdir)
        graph = gate.discover_projects(self.root)
        self.assertEqual(set(graph.projects), {'a/A.csproj', 'b/B.csproj'})
        context = gate.load_standards_context(graph, {'schema_version': 1, 'scopes': [{'root': 'junction'}]})
        self.assertTrue(context.diagnostics)

    def assertion(self, project='a/A.csproj', identity='Example', evidence='a/A.csproj'):
        return {'project': project, 'dependency': {'kind': 'nuget', 'id': identity},
                'evidence': [{'path': evidence, 'reason': 'The unresolved conditional reference is selected for this project'}]}

    def test_positive_evidence_supplements_only_corresponding_unknowns(self):
        self.write('a/A.csproj', '<Project><ItemGroup Condition="$(UseIt)"><PackageReference Include="Example"/><PackageReference Include="Other"/></ItemGroup></Project>')
        self.write('b/B.csproj', '<Project><ItemGroup Condition="$(UseIt)"><PackageReference Include="Example"/></ItemGroup></Project>')
        graph, context = self.context(evidence=[self.assertion()])
        self.assertEqual(context.diagnostics, [])
        example = {'dependency': {'kind': 'nuget', 'id': 'Example'}}
        self.assertTrue(gate.evaluate_project(graph, 'a/A.csproj', example, context=context).matched)
        self.assertTrue(gate.evaluate_project(graph, 'b/B.csproj', example, context=context).diagnostics)
        self.assertTrue(gate.evaluate_project(graph, 'a/A.csproj', {'dependency': {'kind': 'nuget', 'id': 'Other'}}, context=context).diagnostics)

    def test_evidence_cannot_inject_absent_redundant_or_unrelated_dependencies(self):
        self.write('a/A.csproj', '<Project><ItemGroup><PackageReference Include="Known"/><PackageReference Include="Unknown" Condition="$(UseIt)"/></ItemGroup></Project>')
        for entry in (self.assertion(identity='Absent'), self.assertion(identity='Known'),
                      self.assertion(identity='Unknown', evidence='b/B.csproj'),
                      self.assertion(identity='Unknown', project='missing.csproj'),
                      self.assertion(identity='Unknown', evidence='../escape')):
            with self.subTest(entry=entry):
                _, context = self.context(evidence=[entry])
                self.assertEqual(context.supplements, [])
                self.assertTrue(context.diagnostics)

    def test_import_evidence_and_invalid_evidence_shapes(self):
        self.write('a/A.csproj', '<Project><Import Project="custom.props"/></Project>')
        self.write('a/custom.props', '<Project/>')
        graph, context = self.context(evidence=[self.assertion(evidence='a/custom.props')])
        self.assertEqual(context.diagnostics, [])
        self.assertTrue(gate.evaluate_project(graph, 'a/A.csproj', {'dependency': {'kind': 'nuget', 'id': 'Example'}}, context=context).matched)
        for entry in ({'project': 'a/A.csproj', 'dependency': {'kind': 'nuget', 'prefix': 'Ex'}, 'evidence': []},
                      dict(self.assertion(), evidence=[{'path': 'a/A.csproj', 'reason': ''}]),
                      dict(self.assertion(), evidence=[{'path': 'a/missing.props', 'reason': 'selected'}])):
            self.assertTrue(self.context(evidence=[entry])[1].diagnostics)

    def test_runtime_dependencies_and_schema_ship_with_both_gate_copies(self):
        root = Path(__file__).resolve().parent.parent
        sources = json.loads((root / '.agents/plugins/sources.json').read_text(encoding='utf-8'))
        for plugin in ('base', 'engineering'):
            paths = {item['destination'] for item in sources['resources'] if item['plugin'] == plugin}
            self.assertTrue({'hooks/project_facts.py', 'hooks/standards_context.py', 'schemas/standards-context.schema.json'} <= paths)
            import runpy
            runtime = runpy.run_path(str(root / 'plugins' / plugin / 'hooks' / 'tier_gate.py'))
            graph = runtime['discover_projects'](self.root)
            context = runtime['load_standards_context'](graph)
            self.assertEqual(set(graph.projects), {'a/A.csproj', 'b/B.csproj'})
            self.assertEqual(context.diagnostics, [])


if __name__ == '__main__':
    unittest.main()
