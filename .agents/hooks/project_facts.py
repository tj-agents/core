import json
import os
from pathlib import Path, PureWindowsPath
import xml.etree.ElementTree as ET


KINDS = ('nuget', 'npm', 'sdk', 'framework')
SKIP = frozenset({'.git', '.worktrees', 'node_modules', 'bin', 'obj', 'dist', 'build', 'vendor', '.venv', '__pycache__'})


def problem(code, path, message):
    return {'code': code, 'path': str(path), 'message': message}


def repository_path(repository, value, base=None, strict=False):
    if not isinstance(value, str) or not value or PureWindowsPath(value).is_absolute() or ':' in value or value.startswith(('/', '\\')):
        raise ValueError('Expected a repository-relative path')
    value = value.replace('\\', '/')
    if strict and '..' in value.split('/'):
        raise ValueError('Parent traversal is forbidden')
    candidate = ((base or repository) / value).resolve()
    candidate.relative_to(repository.resolve())
    return candidate


class Project:
    def __init__(self, repository, manifest, kind):
        self.repository = repository
        self.id = manifest.relative_to(repository).as_posix()
        self.root = manifest.parent
        self.kind = kind
        self.dependencies = []
        self.unknown = []
        self.references = []
        self.name = None
        self.version = None
        self.workspace_patterns = []

    def dependency(self, kind, identity, path, uncertain=False):
        record = {'kind': kind, 'id': identity, 'path': path}
        (self.unknown if uncertain else self.dependencies).append(record)


class ProjectGraph:
    def __init__(self, repository):
        self.repository = Path(repository).resolve()
        self.projects = {}
        self.diagnostics = []

    def discover(self):
        visited = set()
        for current, directories, files in os.walk(self.repository, followlinks=False):
            resolved = Path(current).resolve()
            if not resolved.is_relative_to(self.repository) or resolved in visited:
                directories[:] = []
                continue
            visited.add(resolved)
            directories[:] = sorted(name for name in directories if name not in SKIP
                                     and not (Path(current) / name).is_symlink()
                                     and (Path(current) / name).resolve().is_relative_to(self.repository))
            for name in sorted(files):
                if name == 'package.json' or Path(name).suffix.lower() in ('.csproj', '.fsproj', '.vbproj'):
                    manifest = Path(current) / name
                    if manifest.is_symlink() or not manifest.resolve().is_relative_to(self.repository):
                        self.diagnostics.append(problem('escaping-manifest', manifest, 'Manifest symlinks are not project identities'))
                        continue
                    project = Project(self.repository, manifest, 'npm' if name == 'package.json' else 'dotnet')
                    self.projects[project.id] = project
                    if project.kind == 'npm':
                        self._npm(project, manifest)
                    else:
                        self._dotnet(project, manifest)
        self._workspace_edges()
        return self

    def _dotnet(self, project, manifest):
        try:
            tree = ET.parse(manifest).getroot()
        except (OSError, ET.ParseError) as error:
            project.unknown.append({'kind': None, 'id': None, 'path': project.id})
            self.diagnostics.append(problem('unreadable-project', project.id, str(error)))
            return
        for sdk in (tree.get('Sdk') or '').split(';'):
            if sdk:
                project.dependency('sdk', None if '$(' in sdk else sdk.split('/')[0], project.id, '$(' in sdk)
        def unresolved(value):
            return any(token in value for token in ('*', '?', '$(', '@(', '%('))
        def target_identity(value):
            if unresolved(value):
                return None
            try:
                return repository_path(self.repository, value, manifest.parent).relative_to(self.repository).as_posix()
            except ValueError:
                return None
        def visit(element, conditional=False):
            tag = element.tag.rsplit('}', 1)[-1]
            conditional = conditional or bool(element.get('Condition')) or tag in ('Choose', 'When', 'Otherwise')
            if tag in ('PackageReference', 'FrameworkReference', 'Sdk', 'ProjectReference'):
                reference = tag == 'ProjectReference'
                kind = {'PackageReference': 'nuget', 'FrameworkReference': 'framework', 'Sdk': 'sdk'}.get(tag)
                def key(value):
                    return target_identity(value) if reference else value.lower() if kind == 'nuget' else value
                def unknown(value=None):
                    if reference:
                        project.references.append({'target': key(value) if value else None, 'path': project.id, 'unknown': True})
                    else:
                        project.dependency(kind, value, project.id, True)
                for removed in (element.get('Remove') or '').split(';'):
                    removed = removed.strip()
                    if not removed:
                        continue
                    if conditional or unresolved(removed) or (reference and key(removed) is None):
                        unknown(None if unresolved(removed) else removed)
                    elif reference:
                        project.references[:] = [edge for edge in project.references if edge['target'] != key(removed)]
                    else:
                        project.dependencies[:] = [item for item in project.dependencies
                                                   if item['kind'] != kind or key(item['id']) != key(removed)]
                exclusions = [value.strip() for value in (element.get('Exclude') or '').split(';') if value.strip()]
                uncertain_exclusion = any(unresolved(value) or (reference and key(value) is None) for value in exclusions)
                excluded = {key(value) for value in exclusions if not unresolved(value)}
                identity = element.get('Include') or element.get('Name')
                for item in (identity or '').split(';'):
                    item = item.strip()
                    if not item:
                        continue
                    if not unresolved(item) and key(item) in excluded:
                        continue
                    uncertain = conditional or unresolved(item) or uncertain_exclusion
                    if reference:
                        target = key(item)
                        project.references.append({'target': target, 'path': project.id,
                                                   'unknown': uncertain or target is None})
                    else:
                        project.dependency(kind, None if unresolved(item) else item, project.id, uncertain)
                    if uncertain_exclusion:
                        unknown()
            elif tag == 'Import':
                evidence = project.id
                try:
                    imported = repository_path(self.repository, element.get('Project'), manifest.parent)
                    if imported.is_file():
                        evidence = imported.relative_to(self.repository).as_posix()
                except ValueError:
                    pass
                project.unknown.append({'kind': None, 'id': None, 'path': evidence})
                project.references.append({'target': None, 'path': evidence, 'unknown': True})
            for child in element:
                visit(child, conditional)
        visit(tree)
        for name in ('Directory.Build.props', 'Directory.Build.targets'):
            directory = manifest.parent
            while directory.is_relative_to(self.repository):
                candidate = directory / name
                if candidate.is_file():
                    evidence = candidate.relative_to(self.repository).as_posix()
                    project.unknown.append({'kind': None, 'id': None, 'path': evidence})
                    project.references.append({'target': None, 'path': evidence, 'unknown': True})
                    break
                if directory == self.repository:
                    break
                directory = directory.parent

    def _npm(self, project, manifest):
        try:
            data = json.loads(manifest.read_text(encoding='utf-8-sig'))
            if not isinstance(data, dict):
                raise ValueError('Package manifest must be an object')
            project.name = data.get('name')
            project.version = data.get('version')
            workspaces = data.get('workspaces', [])
            if isinstance(workspaces, dict):
                workspaces = workspaces.get('packages', [])
            if not isinstance(workspaces, list) or any(not isinstance(item, str) for item in workspaces):
                raise ValueError('Workspace patterns must be strings')
            project.workspace_patterns = workspaces
            dependency_fields = {}
            for field in ('dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies'):
                dependencies = data.get(field, {})
                if not isinstance(dependencies, dict):
                    raise ValueError(field + ' must be an object')
                dependency_fields[field] = dependencies
            dependency_fields['dependencies'] = dict(dependency_fields['dependencies'], **dependency_fields.pop('optionalDependencies'))
            for dependencies in dependency_fields.values():
                for identity, version in dependencies.items():
                    project.dependency('npm', identity, project.id, not isinstance(version, str) or not version)
                    if isinstance(version, str) and version.startswith(('file:', 'link:')):
                        try:
                            target = repository_path(self.repository, version.split(':', 1)[1], manifest.parent)
                            target_id = (target / 'package.json').relative_to(self.repository).as_posix()
                        except ValueError:
                            target_id = None
                        project.references.append({'target': target_id, 'path': project.id, 'unknown': target_id is None})
                    elif isinstance(version, str):
                        project.references.append({'name': identity, 'version': version, 'target': None,
                                                   'path': project.id, 'unknown': False})
        except (OSError, UnicodeError, ValueError) as error:
            project.dependencies.clear()
            project.references.clear()
            project.workspace_patterns.clear()
            project.unknown.append({'kind': 'npm', 'id': None, 'path': project.id})
            self.diagnostics.append(problem('unreadable-project', project.id, str(error)))

    def _workspace_edges(self):
        for workspace in self.projects.values():
            if not workspace.workspace_patterns:
                continue
            members = []
            for pattern in workspace.workspace_patterns:
                try:
                    repository_path(self.repository, pattern, workspace.root, strict=True)
                    members.extend((path / 'package.json').relative_to(self.repository).as_posix()
                                   for path in workspace.root.glob(pattern) if path.is_dir() and not path.is_symlink())
                except (ValueError, OSError):
                    self.diagnostics.append(problem('invalid-workspace', workspace.id, 'Workspace path must remain in the repository'))
            named = {}
            for identity in sorted(set(members)):
                member = self.projects.get(identity)
                if member and isinstance(member.name, str):
                    named.setdefault(member.name, []).append(member.id)
            for identity in sorted(set(members)) + [workspace.id]:
                member = self.projects.get(identity)
                if member:
                    for edge in member.references:
                        if 'name' in edge:
                            targets = named.get(edge['name'], [])
                            version = edge['version']
                            if not targets and not version.startswith('workspace:'):
                                continue
                            edge['target'] = targets[0] if len(targets) == 1 else None
                            expected = version.removeprefix('workspace:')
                            edge['unknown'] = len(targets) != 1 or expected not in ('*', self.projects[targets[0]].version if targets else None)
        for project in self.projects.values():
            project.references[:] = [edge for edge in project.references if 'name' not in edge or edge['target'] or edge['version'].startswith('workspace:') or edge['unknown']]

    def dependency(self, identity, rule, supplements=()):
        project = self.projects[identity]
        kind = rule['kind']
        def matches(item):
            if item['kind'] not in (None, kind):
                return False
            if item['id'] is None:
                return True
            actual = item['id'].lower() if kind == 'nuget' else item['id']
            expected = rule.get('id', rule.get('prefix'))
            expected = expected.lower() if kind == 'nuget' else expected
            return actual == expected if 'id' in rule else actual.startswith(expected)
        proven = [item for item in project.dependencies if matches(item)]
        supplemented = [item for item in supplements if item['project'] == identity and matches(item['dependency'])]
        evidence = [identity + ': ' + item['path'] for item in proven]
        evidence.extend(identity + ': ' + item['path'] + ' (' + item['reason'] + ')'
                        for entry in supplemented for item in entry['evidence'])
        unresolved = [item for item in project.unknown if matches(item)]
        diagnostics = []
        if not supplemented and unresolved:
            diagnostics = [problem('unknown-dependency', item['path'], identity + ': resolve static ' + kind + ' dependency evidence')
                           for item in unresolved]
        return {'matched': bool(proven or supplemented) and not diagnostics, 'evidence': evidence, 'diagnostics': diagnostics}

    def reachable(self, identity, transitive):
        queue = [(identity, ())]
        visited = {identity}
        reachable = []
        diagnostics = []
        while queue:
            current, chain = queue.pop(0)
            for edge in self.projects[current].references:
                target = edge['target']
                if edge['unknown'] or target not in self.projects:
                    diagnostics.append(problem('unknown-project-reference', edge['path'], current + ': resolve local project reference'))
                    continue
                if target in visited:
                    continue
                visited.add(target)
                next_chain = chain + (current + ' -> ' + target,)
                reachable.append((target, next_chain))
                if transitive:
                    queue.append((target, next_chain))
        return reachable, diagnostics
