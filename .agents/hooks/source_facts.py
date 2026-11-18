import re
from dataclasses import dataclass
from pathlib import Path
import runpy
import xml.etree.ElementTree as ET


_PROJECTS = runpy.run_path(str(Path(__file__).with_name('project_facts.py')))
repository_path = _PROJECTS['repository_path']
problem = _PROJECTS['problem']
_IMPORT_LIMIT = 128
_XML_BYTES_LIMIT = 1024 * 1024
_XML_ELEMENTS_LIMIT = 10000
_SDK = frozenset({'Microsoft.NET.Sdk', 'Microsoft.NET.Sdk.Razor', 'Microsoft.NET.Sdk.Web', 'Microsoft.NET.Sdk.Worker'})
_EXCLUDES = frozenset({'DefaultItemExcludes', 'DefaultExcludesInProjectFolder', 'DefaultItemExcludesInProjectFolder'})
_KNOBS = frozenset({'BaseIntermediateOutputPath', 'BaseOutputPath', 'DefaultLanguageSourceExtension', 'DefaultLanguageSourceItems', 'EnableDefaultContentItems', 'EnableDefaultEmbeddedResourceItems', 'EnableDefaultNoneItems', 'ImportDirectoryBuildProps', 'ImportDirectoryBuildTargets', 'MSBuildProjectExtensionsPath', 'PublishDir'})


@dataclass(frozen=True)
class SourceSubject:
    project_id: str
    path: str

    @property
    def scope(self):
        return self.project_id + ':' + self.path


@dataclass
class SourceOwners:
    subjects: tuple = ()
    evidence: tuple = ()
    diagnostics: tuple = ()


def _tag(element):
    return element.tag.rsplit('}', 1)[-1]


def _unresolved(value):
    return not isinstance(value, str) or any(token in value for token in ('$', '@', '%'))


def _paths(value):
    return [part.strip().replace('\\', '/') for part in value.split(';') if part.strip()]


def _glob(pattern):
    pattern = pattern.replace('\\', '/')
    if '[' in pattern or ']' in pattern:
        raise ValueError('Character classes are unsupported')
    pieces, index = [], 0
    while index < len(pattern):
        character = pattern[index]
        if character == '*' and index + 1 < len(pattern) and pattern[index + 1] == '*':
            index += 2
            if index < len(pattern) and pattern[index] == '/':
                pieces.append('(?:.*/)?')
                index += 1
            else:
                pieces.append('.*')
            continue
        pieces.append('[^/]*' if character == '*' else '[^/]' if character == '?' else re.escape(character))
        index += 1
    return re.compile('^' + ''.join(pieces) + '$', re.IGNORECASE)


def _relative(graph, value):
    try:
        candidate = value.resolve() if isinstance(value, Path) else repository_path(graph.repository, value, strict=True)
        candidate.relative_to(graph.repository)
        return candidate.relative_to(graph.repository).as_posix(), candidate
    except (OSError, ValueError):
        return None, None


class _Membership:
    def __init__(self, graph, project):
        self.graph, self.project = graph, project
        self.operations = []
        self.properties = {'EnableDefaultItems': True, 'EnableDefaultCompileItems': True}
        self.exclusions = {}
        self.unknown, self.seen, self.count = [], set(), 0

    def uncertain(self, path, message):
        item = problem('unknown-source-membership', path, message)
        item['project'] = self.project.id
        self.unknown.append(item)

    def load(self, manifest):
        try:
            resolved = Path(manifest).resolve()
            resolved.relative_to(self.graph.repository)
            content = resolved.read_bytes()
            if len(content) > _XML_BYTES_LIMIT:
                raise ValueError('Source membership XML exceeds the byte limit')
            root = ET.fromstring(content)
            if sum(1 for _ in root.iter()) > _XML_ELEMENTS_LIMIT:
                raise ValueError('Source membership XML exceeds the element limit')
            return resolved, root
        except (OSError, ET.ParseError, ValueError) as error:
            self.uncertain(str(manifest), str(error))
            return None, None

    def records(self, value, evidence):
        records = []
        for part in _paths(value):
            try:
                candidate = (self.project.root / Path(part)).resolve()
                records.append((_glob(candidate.relative_to(self.graph.repository).as_posix()), evidence))
            except (OSError, ValueError) as error:
                self.uncertain(evidence, 'Compile item path is unsupported: ' + str(error))
        return tuple(records)

    def property(self, element, evidence):
        name, value = _tag(element), (element.text or '').strip()
        if name in self.properties:
            if value.lower() in ('true', 'false'):
                self.properties[name] = value.lower() == 'true'
            else:
                self.uncertain(evidence, name + ' is unresolved')
        elif name in _EXCLUDES:
            if _unresolved(value):
                self.uncertain(evidence, name + ' is unresolved')
            else:
                try:
                    self.exclusions[name] = tuple(_glob(part) for part in _paths(value))
                except ValueError as error:
                    self.uncertain(evidence, str(error))
        elif name in _KNOBS or name.startswith(('CustomBeforeMicrosoftCommon', 'CustomAfterMicrosoftCommon')):
            self.uncertain(evidence, name + ' can change source membership')

    def compile(self, element, evidence):
        values = {name: element.get(name) for name in ('Include', 'Exclude', 'Remove', 'Update') if element.get(name) is not None}
        if not values or any(_unresolved(value) for value in values.values()):
            self.uncertain(evidence, 'Compile item operation is unresolved')
        elif set(values) - {'Include', 'Exclude'} and len(values) != 1:
            self.uncertain(evidence, 'Compile item operation is unsupported')
        elif 'Include' in values:
            self.operations.append(('include', self.records(values['Include'], evidence), self.records(values.get('Exclude', ''), evidence)))
        elif 'Remove' in values:
            self.operations.append(('remove', self.records(values['Remove'], evidence), ()))
        elif 'Update' in values:
            self.operations.append(('update', self.records(values['Update'], evidence), ()))
        else:
            self.uncertain(evidence, 'Compile Exclude without Include is unresolved')

    def read(self, manifest):
        if self.count >= _IMPORT_LIMIT:
            self.uncertain(self.project.id, 'Source membership import limit reached')
            return
        resolved, root = self.load(manifest)
        if root is None:
            return
        relative = resolved.relative_to(self.graph.repository).as_posix()
        if resolved in self.seen:
            self.uncertain(relative, 'Source membership import cycle')
            return
        self.seen.add(resolved)
        self.count += 1

        def visit(element, conditional=False):
            tag = _tag(element)
            affects = any(_tag(item) in ('Compile', 'Import', 'EnableDefaultItems', 'EnableDefaultCompileItems') or _tag(item) in _EXCLUDES or _tag(item) in _KNOBS for item in element.iter())
            conditional = conditional or bool(element.get('Condition')) or tag in ('Choose', 'When', 'Otherwise', 'Target')
            if conditional:
                if affects:
                    self.uncertain(relative, 'Conditional or target-time source membership is unresolved')
                return
            if tag == 'PropertyGroup':
                for child in element:
                    self.property(child, relative)
            elif tag == 'Import':
                value = element.get('Project')
                if value is None or element.get('Sdk') is not None or _unresolved(value):
                    self.uncertain(relative, 'Import mechanism is unsupported')
                else:
                    try:
                        imported = repository_path(self.graph.repository, value.replace('\\', '/'), resolved.parent)
                        if not imported.is_file():
                            raise ValueError('Imported project file is missing')
                        if imported.name.endswith(('.nuget.g.props', '.nuget.g.targets')):
                            self.uncertain(relative, 'Generated NuGet imports are unsupported')
                        else:
                            self.read(imported)
                    except ValueError as error:
                        self.uncertain(relative, str(error))
            elif tag == 'Compile':
                self.compile(element, relative)
            elif tag == 'Sdk':
                self.uncertain(relative, 'SDK child imports are unsupported')
            else:
                for child in element:
                    visit(child, conditional)

        for child in root:
            visit(child)

    def main_sdk(self):
        manifest = self.graph.repository / self.project.id
        resolved, root = self.load(manifest)
        if root is None:
            return False
        sdk = root.get('Sdk')
        if sdk is None:
            return False
        if _unresolved(sdk) or sdk not in _SDK:
            self.uncertain(resolved.relative_to(self.graph.repository).as_posix(), 'SDK default Compile membership is unsupported')
            return False
        return True

    def directory_build(self, name):
        directory = self.project.root
        while True:
            candidate = directory / name
            if candidate.is_file():
                try:
                    candidate.relative_to(self.graph.repository)
                    return candidate
                except ValueError:
                    return False
            if directory.parent == directory:
                return None
            directory = directory.parent

    def defaults(self, path):
        if not self.properties['EnableDefaultItems'] or not self.properties['EnableDefaultCompileItems']:
            return False
        if path.suffix.lower() != '.cs' or not path.is_relative_to(self.project.root):
            return False
        patterns = [_glob(value) for value in ('bin/**', 'obj/**', '**/.*/**')]
        for name in _EXCLUDES:
            patterns.extend(self.exclusions.get(name, ()))
        relative = path.relative_to(self.project.root).as_posix()
        return not any(pattern.fullmatch(relative) for pattern in patterns)

    def evaluate(self, path):
        if self.project.id.lower().endswith(('.fsproj', '.vbproj')):
            self.uncertain(self.project.id, 'F# and Visual Basic default Compile membership is unsupported')
        sdk = self.main_sdk()
        manifest = self.graph.repository / self.project.id
        if sdk:
            props = self.directory_build('Directory.Build.props')
            if props is False:
                self.uncertain(self.project.id, 'Directory.Build.props may be inherited outside the repository')
            elif props:
                self.read(props)
            self.operations.append(('default', (), ()))
        self.read(manifest)
        if sdk:
            targets = self.directory_build('Directory.Build.targets')
            if targets is False:
                self.uncertain(self.project.id, 'Directory.Build.targets may be inherited outside the repository')
            elif targets:
                self.read(targets)
            stem = Path(self.project.id).name
            for suffix in ('.nuget.g.props', '.nuget.g.targets'):
                generated = self.project.root / 'obj' / (stem + suffix)
                if generated.is_file():
                    self.uncertain(generated.relative_to(self.graph.repository).as_posix(), 'Generated NuGet import coverage is unknown')
        if self.unknown:
            return None, (), tuple(self.unknown)
        physical, included, evidence = path.relative_to(self.graph.repository).as_posix(), False, ()
        for operation, patterns, excluded in self.operations:
            matches = [source for pattern, source in patterns if pattern.fullmatch(physical)]
            if operation == 'default' and self.defaults(path):
                included, evidence = True, (self.project.id,)
            elif operation == 'include' and matches and not any(pattern.fullmatch(physical) for pattern, _ in excluded):
                included, evidence = True, tuple(matches)
            elif operation == 'remove' and matches:
                included, evidence = False, ()
        return included, evidence, ()


def _npm_owner(graph, project, path):
    try:
        path.relative_to(project.root)
    except ValueError:
        return False, (), ()
    if any(item.get('code') == 'unreadable-project' and str(item.get('path')) == project.id for item in graph.diagnostics):
        detail = problem('unknown-source-membership', project.id, 'Package manifest is unreadable')
        detail['project'] = project.id
        return None, (), (detail,)
    return True, (project.id,), ()


def source_owners(graph, path, intended_project=None):
    relative, candidate = _relative(graph, path)
    if relative is None or candidate.is_dir():
        return SourceOwners(diagnostics=(problem('invalid-source-path', str(path), 'Source path must be a repository-contained file path'),))
    dotnet, npm, evidence, diagnostics = [], [], [], []
    for identity, project in sorted(graph.projects.items()):
        member, detail, problems = _npm_owner(graph, project, candidate) if project.kind == 'npm' else _Membership(graph, project).evaluate(candidate)
        diagnostics.extend(problems)
        subject = SourceSubject(identity, relative)
        if project.kind == 'npm':
            try:
                candidate.relative_to(project.root)
                npm.append((len(project.root.parts), subject, detail, member))
            except ValueError:
                pass
        elif member:
                dotnet.append(subject)
                evidence.extend(identity + ': ' + item for item in detail)
    owners = dotnet
    if npm:
        deepest = max(depth for depth, _, _, _ in npm)
        for depth, subject, detail, member in npm:
            if depth == deepest and member:
                owners.append(subject)
                evidence.extend(subject.project_id + ': ' + item for item in detail)
    intended = [subject for subject in owners if subject.project_id == intended_project]
    if intended_project is not None:
        if intended_project not in graph.projects:
            diagnostics.append(problem('unknown-project', intended_project, 'Intended source project must be discovered'))
        elif not intended:
            diagnostics.append(problem('invalid-source-owner', relative, 'Intended project does not own this source path'))
        elif not candidate.exists():
            owners = intended
    if not candidate.exists() and len(owners) > 1 and intended_project is None:
        diagnostics.append(problem('ambiguous-source-owner', relative, 'Proposed source path belongs to multiple projects; provide intended_project'))
        owners = []
    return SourceOwners(tuple(owners), tuple(dict.fromkeys(evidence)), tuple(diagnostics))
