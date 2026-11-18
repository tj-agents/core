import json
from pathlib import Path
import tempfile
import unittest

from test_tier_predicates import gate


class SourceOwnership(unittest.TestCase):
    def setUp(self):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.root = Path(holder.name)

    def write(self, name, body=''):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body if isinstance(body, str) else json.dumps(body), encoding='utf-8')
        return path

    def graph(self):
        return gate.discover_projects(self.root)

    def owners(self, graph, path, intended=None):
        return gate.source_owners(graph, path, intended)

    def test_csharp_defaults_and_ordered_explicit_membership(self):
        self.write('App.csproj', '<Project Sdk="Microsoft.NET.Sdk"><ItemGroup><Compile Include="Added.cs"/><Compile Include="Generated.cs"/><Compile Remove="Generated.cs"/><Compile Include="Restored.cs"/><Compile Remove="Restored.cs"/><Compile Include="Restored.cs"/><Compile Include="Kept.cs" Exclude="Kept.cs"/></ItemGroup></Project>')
        for path, expected in [('Default.cs', True), ('Added.cs', True), ('Generated.cs', False), ('Restored.cs', True), ('Kept.cs', True)]:
            with self.subTest(path=path):
                result = self.owners(self.graph(), path)
                self.assertEqual([subject.project_id for subject in result.subjects], ['App.csproj'] if expected else [])
                self.assertFalse(result.diagnostics)

    def test_multitarget_package_condition_and_update_do_not_change_membership(self):
        self.write('App.csproj', '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFrameworks>net8.0;net9.0</TargetFrameworks></PropertyGroup><ItemGroup><PackageReference Include="Example" Condition="$(UseExample)"/><Compile Update="Existing.cs"/></ItemGroup></Project>')
        result = self.owners(self.graph(), 'Existing.cs', 'App.csproj')
        self.assertEqual([item.project_id for item in result.subjects], ['App.csproj'])
        self.assertFalse(result.diagnostics)

    def test_windows_case_and_default_property_order(self):
        self.write('Directory.Build.props', '<Project><PropertyGroup><EnableDefaultItems>false</EnableDefaultItems><EnableDefaultItems>true</EnableDefaultItems></PropertyGroup><ItemGroup><Compile Remove="Kept.cs"/></ItemGroup></Project>')
        self.write('App.csproj', '<Project Sdk="Microsoft.NET.Sdk"><ItemGroup><Compile Remove="kept.cs"/></ItemGroup></Project>')
        self.assertFalse(self.owners(self.graph(), 'Kept.cs', 'App.csproj').subjects)
        self.assertEqual([item.project_id for item in self.owners(self.graph(), 'Other.CS', 'App.csproj').subjects], ['App.csproj'])

    def test_linked_and_shared_files_keep_distinct_project_subjects(self):
        project = '<Project><ItemGroup><Compile Include="../shared/Shared.cs"/></ItemGroup></Project>'
        self.write('a/A.csproj', project)
        self.write('b/B.csproj', project)
        self.write('shared/Shared.cs')
        result = self.owners(self.graph(), 'shared/Shared.cs')
        self.assertEqual({subject.project_id for subject in result.subjects}, {'a/A.csproj', 'b/B.csproj'})
        self.assertEqual({subject.path for subject in result.subjects}, {'shared/Shared.cs'})

    def test_same_directory_projects_and_proposed_paths_require_intent(self):
        self.write('A.csproj', '<Project Sdk="Microsoft.NET.Sdk"/>')
        self.write('B.csproj', '<Project Sdk="Microsoft.NET.Sdk"/>')
        graph = self.graph()
        ambiguous = self.owners(graph, 'New.cs')
        self.assertEqual(ambiguous.subjects, ())
        self.assertEqual(ambiguous.diagnostics[-1]['code'], 'ambiguous-source-owner')
        intended = self.owners(graph, 'New.cs', 'A.csproj')
        self.assertEqual([subject.project_id for subject in intended.subjects], ['A.csproj'])
        self.write('Existing.cs')
        self.assertEqual({subject.project_id for subject in self.owners(graph, 'Existing.cs').subjects}, {'A.csproj', 'B.csproj'})

    def test_excluded_unknown_and_non_csharp_defaults_do_not_claim_proposed_source(self):
        self.write('A.csproj', '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><DefaultItemExcludes>**/Generated.cs</DefaultItemExcludes></PropertyGroup></Project>')
        self.write('F.fsproj', '<Project Sdk="Microsoft.NET.Sdk"/>')
        self.write('Unknown.csproj', '<Project Sdk="$(SdkName)"/>')
        graph = self.graph()
        self.assertFalse(self.owners(graph, 'Generated.cs', 'A.csproj').subjects)
        self.assertTrue(self.owners(graph, 'Generated.cs', 'A.csproj').diagnostics)
        self.assertFalse(self.owners(graph, 'Source.fs', 'F.fsproj').subjects)
        self.assertTrue(self.owners(graph, 'Source.cs', 'Unknown.csproj').diagnostics)

    def test_literal_imports_and_source_affecting_uncertainty(self):
        self.write('parts/compile.props', '<Project><ItemGroup><Compile Include="linked/Linked.cs"/></ItemGroup></Project>')
        self.write('A.csproj', '<Project><Import Project="parts/compile.props"/></Project>')
        self.write('linked/Linked.cs')
        self.assertEqual([subject.project_id for subject in self.owners(self.graph(), 'linked/Linked.cs').subjects], ['A.csproj'])
        self.write('A.csproj', '<Project><ItemGroup Condition="$(Choose)"><Compile Include="Chosen.cs"/></ItemGroup></Project>')
        result = self.owners(self.graph(), 'Chosen.cs')
        self.assertFalse(result.subjects)
        self.assertEqual(result.diagnostics[0]['code'], 'unknown-source-membership')
        self.write('A.csproj', '<Project><Import Project="parts/one.props"/></Project>')
        self.write('parts/one.props', '<Project><Import Project="two.props"/></Project>')
        self.write('parts/two.props', '<Project><Import Project="one.props"/></Project>')
        self.assertTrue(self.owners(self.graph(), 'Other.cs').diagnostics)

    def test_globs_are_anchored_and_import_items_use_consuming_project_base(self):
        self.write('parts/items.props', '<Project><ItemGroup><Compile Include="Linked.cs"/><Compile Include="*.cs"/></ItemGroup></Project>')
        self.write('app/A.csproj', '<Project><Import Project="../parts/items.props"/></Project>')
        graph = self.graph()
        self.assertEqual([item.project_id for item in self.owners(graph, 'app/Linked.cs').subjects], ['app/A.csproj'])
        self.assertFalse(self.owners(graph, 'app/nested/Linked.cs').subjects)
        self.assertFalse(self.owners(graph, 'nested/Other.cs').subjects)

    def test_default_switches_non_csharp_and_unrelated_uncertainty(self):
        self.write('Directory.Build.props', '<Project><PropertyGroup><EnableDefaultItems>false</EnableDefaultItems></PropertyGroup></Project>')
        self.write('app/A.csproj', '<Project Sdk="Microsoft.NET.Sdk"><ItemGroup><Compile Include="Explicit.cs"/><PackageReference Include="Example"/></ItemGroup></Project>')
        self.write('F.fsproj', '<Project Sdk="Microsoft.NET.Sdk"/>')
        self.write('Unknown.csproj', '<Project Sdk="$(Sdk)"/>')
        graph = self.graph()
        self.assertEqual([item.project_id for item in self.owners(graph, 'app/Explicit.cs', 'app/A.csproj').subjects], ['app/A.csproj'])
        self.assertFalse(self.owners(graph, 'app/Default.cs', 'app/A.csproj').subjects)
        self.assertTrue(self.owners(graph, 'Code.fs', 'F.fsproj').diagnostics)
        context = gate.load_standards_context(graph, {'schema_version': 1, 'scopes': [{'root': 'app', 'architecture': ['test']}]})
        result = gate.evaluate_file(graph, 'app/A.csproj', 'app/Explicit.cs', {'context': {'key': 'architecture', 'contains': 'test'}}, context=context)
        self.assertTrue(result.matched)
        self.assertEqual(result.diagnostics, ())

    def test_invalid_nested_npm_manifest_blocks_ancestor_and_directories_escape(self):
        self.write('package.json', {'name': 'parent'})
        self.write('packages/bad/package.json', '{not json')
        graph = self.graph()
        result = self.owners(graph, 'packages/bad/src/index.ts')
        self.assertFalse(result.subjects)
        self.assertTrue(result.diagnostics)
        self.assertEqual(self.owners(graph, 'packages/bad').subjects, ())
        self.assertEqual(self.owners(graph, '../escape.ts').subjects, ())

    def test_npm_nearest_manifest_boundary_never_follows_dependencies(self):
        self.write('package.json', {'dependencies': {'child': 'file:packages/child'}})
        self.write('packages/child/package.json', {'name': 'child'})
        graph = self.graph()
        self.assertEqual([subject.project_id for subject in self.owners(graph, 'packages/child/src/index.ts').subjects], ['packages/child/package.json'])
        self.assertEqual([subject.project_id for subject in self.owners(graph, 'src/index.ts').subjects], ['package.json'])

    def test_file_context_uses_physical_path_and_file_facts_cannot_cross_subjects(self):
        self.write('a/A.csproj', '<Project><ItemGroup><Compile Include="../shared/File.cs"/></ItemGroup></Project>')
        self.write('b/B.csproj', '<Project><ItemGroup><Compile Include="../shared/File.cs"/></ItemGroup></Project>')
        self.write('shared/File.cs')
        graph = self.graph()
        context = gate.load_standards_context(graph, {'schema_version': 1, 'scopes': [
            {'root': 'a', 'house': {'dotnet': 'a'}}, {'root': 'shared', 'house': {'dotnet': 'shared'}}]})
        node = {'context': {'key': 'house.dotnet', 'equals': 'shared'}}
        self.assertTrue(gate.evaluate_file(graph, 'a/A.csproj', 'shared/File.cs', node, context=context).matched)
        source = gate.evaluate_file(graph, 'a/A.csproj', 'shared/File.cs', {'all': [{'context': {'key': 'house.dotnet', 'equals': 'shared'}}]}, context=context)
        foreign = gate.PredicateResult('b/B.csproj', True, subject=next(item for item in self.owners(graph, 'shared/File.cs').subjects if item.project_id == 'b/B.csproj'))
        result = gate.evaluate_file(graph, 'a/A.csproj', 'shared/File.cs', {'fact': 'file.fact'}, facts={'file.fact': foreign})
        self.assertFalse(result.matched)
        self.assertEqual(result.diagnostics[0]['code'], 'unknown-fact')
        other = gate.PredicateResult('a/A.csproj', True, subject=foreign.subject)
        result = gate.evaluate_file(graph, 'a/A.csproj', 'shared/File.cs', {'fact': 'file.fact'}, facts={'file.fact': other})
        self.assertFalse(result.matched)
        self.assertEqual(result.diagnostics[0]['code'], 'unknown-fact')
        self.assertEqual(source.subject.project_id, 'a/A.csproj')

    def test_same_project_file_fact_cannot_cross_paths(self):
        self.write('A.csproj', '<Project Sdk="Microsoft.NET.Sdk"/>')
        graph = self.graph()
        other_subject = gate.evaluate_file(graph, 'A.csproj', 'Other.cs', {'context': {'key': 'architecture', 'contains': 'none'}}).subject
        supplied = gate.PredicateResult('A.csproj', True, subject=other_subject)
        result = gate.evaluate_file(graph, 'A.csproj', 'Current.cs', {'fact': 'file.fact'}, facts={'file.fact': supplied})
        self.assertFalse(result.matched)
        self.assertEqual(result.diagnostics[0]['code'], 'unknown-fact')

    def test_body_import_remove_runs_after_sdk_defaults(self):
        self.write('parts/remove.props', '<Project><ItemGroup><Compile Remove="Default.cs"/></ItemGroup></Project>')
        self.write('App.csproj', '<Project Sdk="Microsoft.NET.Sdk"><Import Project="parts/remove.props"/></Project>')
        result = self.owners(self.graph(), 'Default.cs', 'App.csproj')
        self.assertFalse(result.subjects)
        self.assertEqual(result.diagnostics[-1]['code'], 'invalid-source-owner')

    def test_late_properties_use_final_default_values_and_last_exclusion_assignment(self):
        self.write('App.csproj', '<Project Sdk="Microsoft.NET.Sdk"><ItemGroup><Compile Include="Explicit.cs"/></ItemGroup><PropertyGroup><DefaultItemExcludes>**/Late.cs</DefaultItemExcludes><DefaultItemExcludes>**/Other.cs</DefaultItemExcludes></PropertyGroup></Project>')
        graph = self.graph()
        self.assertEqual([item.project_id for item in self.owners(graph, 'Late.cs', 'App.csproj').subjects], ['App.csproj'])
        self.assertFalse(self.owners(graph, 'Other.cs', 'App.csproj').subjects)
        self.assertEqual([item.project_id for item in self.owners(graph, 'Explicit.cs', 'App.csproj').subjects], ['App.csproj'])

    def test_default_exclusion_aliases_and_windows_patterns_are_platform_neutral(self):
        self.write('App.csproj', '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><DefaultExcludesInProjectFolder>generated\\**</DefaultExcludesInProjectFolder><DefaultItemExcludesInProjectFolder>private\\**</DefaultItemExcludesInProjectFolder></PropertyGroup><ItemGroup><Compile Include="src\\Added.cs"/><Compile Remove="src\\Removed.cs"/></ItemGroup></Project>')
        graph = self.graph()
        self.assertFalse(self.owners(graph, 'generated/File.cs', 'App.csproj').subjects)
        self.assertFalse(self.owners(graph, 'private/File.cs', 'App.csproj').subjects)
        self.assertEqual([item.project_id for item in self.owners(graph, 'src/Added.cs', 'App.csproj').subjects], ['App.csproj'])
        self.assertFalse(self.owners(graph, 'src/Removed.cs', 'App.csproj').subjects)

    def test_source_affecting_knobs_and_generated_nuget_imports_are_unknown(self):
        self.write('App.csproj', '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><PublishDir>publish</PublishDir><DefaultLanguageSourceExtension>.fs</DefaultLanguageSourceExtension></PropertyGroup></Project>')
        result = self.owners(self.graph(), 'Source.cs', 'App.csproj')
        self.assertFalse(result.subjects)
        self.assertTrue(result.diagnostics)
        self.write('App.csproj', '<Project Sdk="Microsoft.NET.Sdk"/>')
        self.write('obj/App.csproj.nuget.g.props', '<Project/>')
        result = self.owners(self.graph(), 'Source.cs', 'App.csproj')
        self.assertFalse(result.subjects)
        self.assertTrue(result.diagnostics)

    def test_external_directory_build_inheritance_is_unknown(self):
        container = tempfile.TemporaryDirectory()
        self.addCleanup(container.cleanup)
        root = Path(container.name) / 'repo'
        root.mkdir()
        (Path(container.name) / 'Directory.Build.props').write_text('<Project/>', encoding='utf-8')
        (root / 'App.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"/>', encoding='utf-8')
        result = gate.source_owners(gate.discover_projects(root), 'Source.cs', 'App.csproj')
        self.assertFalse(result.subjects)
        self.assertTrue(result.diagnostics)

    def test_invalid_oversized_and_escaping_imports_are_unknown(self):
        self.write('App.csproj', '<Project Sdk="Microsoft.NET.Sdk"><Import Project="../outside.props"/></Project>')
        result = self.owners(self.graph(), 'Source.cs', 'App.csproj')
        self.assertFalse(result.subjects)
        self.assertTrue(result.diagnostics)
        self.write('App.csproj', '<Project Sdk="Microsoft.NET.Sdk">')
        result = self.owners(self.graph(), 'Source.cs', 'App.csproj')
        self.assertFalse(result.subjects)
        self.assertTrue(result.diagnostics)
        self.write('App.csproj', '<Project Sdk="Microsoft.NET.Sdk">' + (' ' * (1024 * 1024)) + '</Project>')
        result = self.owners(self.graph(), 'Source.cs', 'App.csproj')
        self.assertFalse(result.subjects)
        self.assertTrue(result.diagnostics)


if __name__ == '__main__':
    unittest.main()
