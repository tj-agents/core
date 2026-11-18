import re
from dataclasses import dataclass
from pathlib import Path
import runpy
import xml.etree.ElementTree as ET
_PROJECTS = runpy.run_path(str(Path(__file__).with_name('project_facts.py')))
repository_path = _PROJECTS['repository_path']
problem = _PROJECTS['problem']
_IMPORT_LIMIT, _XML_BYTES_LIMIT, _XML_ELEMENTS_LIMIT = (128, 1024 * 1024, 10000)
_STANDARD_CSHARP_SDKS = frozenset({'Microsoft.NET.Sdk', 'Microsoft.NET.Sdk.Web', 'Microsoft.NET.Sdk.Razor', 'Microsoft.NET.Sdk.Worker'})

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

def _relative(graph, value):
    try:
        candidate = value.resolve() if isinstance(value, Path) else repository_path(graph.repository, value, strict=True)
        candidate.relative_to(graph.repository)
        return (candidate.relative_to(graph.repository).as_posix(), candidate)
    except (OSError, ValueError):
        return (None, None)

def _tag(element):
    return element.tag.rsplit('}', 1)[-1]

def _unresolved(value):
    return not isinstance(value, str) or any((token in value for token in ('$', '@', '%')))

def _paths(value):
    return [part.strip() for part in value.split(';') if part.strip()]

def _glob(pattern):
    if '[' in pattern or ']' in pattern:
        raise ValueError('Character classes are unsupported')
    pieces, index = ([], 0)
    while index < len(pattern):
        char = pattern[index]
        if char == '*' and index + 1 < len(pattern) and (pattern[index + 1] == '*'):
            index += 2
            if index < len(pattern) and pattern[index] == '/':
                pieces.append('(?:.*/)?')
                index += 1
            else:
                pieces.append('.*')
            continue
        pieces.append('[^/]*' if char == '*' else '[^/]' if char == '?' else re.escape(char))
        index += 1
    return re.compile('^' + ''.join(pieces) + '$', re.IGNORECASE)

class _Membership:

    def __init__(self, graph, project):
        self.graph, self.project = (graph, project)
        self.operations = []
        self.default_items = True
        self.default_compile_items = True
        self.default_excludes = tuple((_glob(item) for item in ('bin/**', 'obj/**', '**/.*/**')))
        self.unknown, self.seen, self.count = ([], set(), 0)

    def uncertain(self, path, message):
        detail = problem('unknown-source-membership', path, message)
        detail['project'] = self.project.id
        self.unknown.append(detail)

    def records(self, value, evidence):
        answer = []
        for part in _paths(value):
            try:
                candidate = (self.project.root / part).resolve()
                answer.append((_glob(candidate.relative_to(self.graph.repository).as_posix()), evidence))
            except (OSError, ValueError) as error:
                self.uncertain(evidence, 'Compile item path is unsupported: ' + str(error))
        return tuple(answer)

    def read(self, manifest, implicit=False):
        if self.count >= _IMPORT_LIMIT:
            self.uncertain(self.project.id, 'Source membership import limit reached')
            return
        try:
            resolved = Path(manifest).resolve()
            resolved.relative_to(self.graph.repository)
            if resolved.stat().st_size > _XML_BYTES_LIMIT:
                raise ValueError('Source membership XML exceeds the byte limit')
        except (OSError, ValueError) as error:
            self.uncertain(str(manifest), str(error))
            return
        if resolved in self.seen:
            self.uncertain(resolved.relative_to(self.graph.repository).as_posix(), 'Source membership import cycle')
            return
        self.seen.add(resolved)
        self.count += 1
        relative = resolved.relative_to(self.graph.repository).as_posix()
        try:
            root = ET.parse(resolved).getroot()
            if sum((1 for _ in root.iter())) > _XML_ELEMENTS_LIMIT:
                raise ValueError('Source membership XML exceeds the element limit')
        except (OSError, ET.ParseError, ValueError) as error:
            self.uncertain(relative, str(error))
            return
        default_pending = False
        for element in root.iter():
            tag = _tag(element)
            if element is root:
                sdk = element.get('Sdk')
                if sdk is not None:
                    if _unresolved(sdk) or sdk not in _STANDARD_CSHARP_SDKS:
                        self.uncertain(relative, 'SDK default Compile membership is unsupported')
                    elif not implicit:
                        default_pending = True
                if any((_tag(child) == 'Sdk' for child in element)):
                    self.uncertain(relative, 'SDK child imports are unsupported')
            affects = tag in ('Compile', 'EnableDefaultItems', 'EnableDefaultCompileItems', 'DefaultItemExcludes', 'DefaultExcludesInProjectFolder', 'Import') or any((_tag(child) in ('Compile', 'EnableDefaultItems', 'EnableDefaultCompileItems', 'DefaultItemExcludes', 'DefaultExcludesInProjectFolder', 'Import') for child in element.iter()))
            if element.get('Condition') or tag in ('Choose', 'When', 'Otherwise', 'Target'):
                if affects:
                    self.uncertain(relative, 'Conditional or target-time source membership is unresolved')
                continue
            if tag in ('ImportDirectoryBuildProps', 'ImportDirectoryBuildTargets', 'DirectoryBuildPropsPath', 'DirectoryBuildTargetsPath', 'BaseOutputPath', 'BaseIntermediateOutputPath'):
                self.uncertain(relative, tag + ' can change source membership')
            elif tag in ('EnableDefaultItems', 'EnableDefaultCompileItems'):
                value = (element.text or '').strip().lower()
                if value not in ('true', 'false'):
                    self.uncertain(relative, tag + ' is unresolved')
                elif tag == 'EnableDefaultItems':
                    self.default_items = value == 'true'
                else:
                    self.default_compile_items = value == 'true'
            elif tag in ('DefaultItemExcludes', 'DefaultExcludesInProjectFolder'):
                value = (element.text or '').strip()
                if _unresolved(value):
                    self.uncertain(relative, tag + ' is unresolved')
                else:
                    try:
                        patterns = tuple((_glob(item) for item in _paths(value)))
                    except ValueError as error:
                        self.uncertain(relative, str(error))
                        continue
                    self.default_excludes += patterns
            elif tag == 'Compile':
                if default_pending:
                    self.operations.append(('default', (), tuple(self.default_excludes)))
                    default_pending = False
                values = {name: element.get(name) for name in ('Include', 'Exclude', 'Remove', 'Update') if element.get(name) is not None}
                if not values or any((_unresolved(value) for value in values.values())):
                    self.uncertain(relative, 'Compile item operation is unresolved')
                    continue
                if set(values) - {'Include', 'Exclude'} and len(values) != 1:
                    self.uncertain(relative, 'Compile item operation is unsupported')
                    continue
                if 'Include' in values:
                    self.operations.append(('include', self.records(values['Include'], relative), self.records(values.get('Exclude', ''), relative)))
                elif 'Remove' in values:
                    self.operations.append(('remove', self.records(values['Remove'], relative), ()))
                elif 'Update' in values:
                    self.operations.append(('update', self.records(values['Update'], relative), ()))
                else:
                    self.uncertain(relative, 'Compile Exclude without Include is unresolved')
            elif tag == 'Import':
                value = element.get('Project')
                if value is None or element.get('Sdk') is not None or _unresolved(value):
                    self.uncertain(relative, 'Import mechanism is unsupported')
                    continue
                try:
                    imported = repository_path(self.graph.repository, value, resolved.parent)
                    if not imported.is_file():
                        raise ValueError('Imported project file is missing')
                    self.read(imported)
                except ValueError as error:
                    self.uncertain(relative, str(error))
        if default_pending:
            self.operations.append(('default', (), tuple(self.default_excludes)))

    def evaluate(self, path):
        physical = path.relative_to(self.graph.repository).as_posix()
        relative = path.relative_to(self.project.root).as_posix() if path.is_relative_to(self.project.root) else None
        if self.project.id.lower().endswith(('.fsproj', '.vbproj')):
            self.uncertain(self.project.id, 'F# and Visual Basic default Compile membership is unsupported')

        def directory_build(name):
            directory = self.project.root
            while directory.is_relative_to(self.graph.repository):
                candidate = directory / name
                if candidate.is_file():
                    return candidate
                if directory == self.graph.repository:
                    external = directory.parent / name
                    return False if external.exists() else None
                directory = directory.parent
        manifest = self.graph.repository / self.project.id
        try:
            sdk = ET.parse(manifest).getroot().get('Sdk')
            implicit_build_imports = sdk in _STANDARD_CSHARP_SDKS
        except (OSError, ET.ParseError):
            implicit_build_imports = False
        if implicit_build_imports:
            props = directory_build('Directory.Build.props')
            if props is False:
                self.uncertain(self.project.id, 'Directory.Build.props may be inherited outside the repository')
            elif props:
                self.read(props, True)
        self.read(manifest)
        if implicit_build_imports:
            targets = directory_build('Directory.Build.targets')
            if targets is False:
                self.uncertain(self.project.id, 'Directory.Build.targets may be inherited outside the repository')
            elif targets:
                self.read(targets, True)
        if self.unknown:
            return (None, (), tuple(self.unknown))
        included = False
        evidence = ()
        for operation, patterns, excluded in self.operations:
            matches = [source for pattern, source in patterns if pattern.fullmatch(physical)]
            if operation == 'default' and self.default_items and self.default_compile_items and (relative is not None) and (path.suffix.lower() == '.cs') and (not any((pattern.fullmatch(relative) for pattern in excluded))):
                included, evidence = (True, (self.project.id,))
            elif operation == 'include' and matches and (not any((pattern.fullmatch(physical) for pattern, _ in excluded))):
                included, evidence = (True, tuple(matches))
            elif operation == 'remove' and matches:
                included, evidence = (False, ())
        return (included, evidence, ())

def _npm_owner(graph, project, path):
    try:
        path.relative_to(project.root)
    except ValueError:
        return (False, (), ())
    if any((item.get('code') == 'unreadable-project' and str(item.get('path')) == project.id for item in graph.diagnostics)):
        detail = problem('unknown-source-membership', project.id, 'Package manifest is unreadable')
        detail['project'] = project.id
        return (None, (), (detail,))
    return (True, (project.id,), ())

def source_owners(graph, path, intended_project=None):
    relative, candidate = _relative(graph, path)
    if relative is None or candidate.is_dir():
        return SourceOwners(diagnostics=(problem('invalid-source-path', str(path), 'Source path must be a repository-contained file path'),))
    dotnet, npm, npm_depths, evidence, diagnostics = ([], [], [], [], [])
    for identity, project in sorted(graph.projects.items()):
        if project.kind == 'npm':
            try:
                candidate.relative_to(project.root)
                npm_depths.append(len(project.root.parts))
            except ValueError:
                pass
        member, detail, problems = _npm_owner(graph, project, candidate) if project.kind == 'npm' else _Membership(graph, project).evaluate(candidate)
        diagnostics.extend(problems)
        if member is True:
            subject = SourceSubject(identity, relative)
            if project.kind == 'npm':
                npm.append((len(project.root.parts), subject, detail))
            else:
                dotnet.append(subject)
                evidence.extend((identity + ': ' + item for item in detail))
    owners = dotnet
    if npm:
        deepest = max(npm_depths)
        for depth, subject, detail in npm:
            if depth == deepest:
                owners.append(subject)
                evidence.extend((subject.project_id + ': ' + item for item in detail))
    intended = [subject for subject in owners if subject.project_id == intended_project]
    if intended_project is not None:
        if intended_project not in graph.projects:
            diagnostics.append(problem('unknown-project', intended_project, 'Intended source project must be discovered'))
        elif not intended:
            diagnostics.append(problem('invalid-source-owner', relative, 'Intended project does not own this source path'))
        elif not candidate.exists():
            owners = intended
    if not candidate.exists() and len(owners) > 1 and (intended_project is None):
        diagnostics.append(problem('ambiguous-source-owner', relative, 'Proposed source path belongs to multiple projects; provide intended_project'))
        owners = []
    return SourceOwners(tuple(owners), tuple(dict.fromkeys(evidence)), tuple(diagnostics))
