from pathlib import Path
import json
import runpy


_PATHS = runpy.run_path(str(Path(__file__).with_name('project_facts.py')))
repository_path = _PATHS['repository_path']
problem = _PATHS['problem']


class StandardsContext:
    def __init__(self, graph):
        self.graph = graph
        self.claims = []
        self.supplements = []
        self.diagnostics = []
        self.issues = []

    def report(self, item, root=None, project=None):
        self.diagnostics.append(item)
        self.issues.append((item, root, project))

    def diagnostics_for(self, identity):
        root = self.graph.projects[identity].root
        return [item for item, affected_root, project in self.issues
                if item["code"] != "invalid-dependency-evidence" and (project is None or project == identity)
                and (affected_root is None or root.is_relative_to(affected_root))]

    def load(self, data=None, additional_claims=()):
        path = self.graph.repository / '.agents' / 'standards-context.json'
        if data is None:
            try:
                data = json.loads(path.read_text(encoding='utf-8-sig'))
            except FileNotFoundError:
                data = {'schema_version': 1, 'scopes': []}
            except (OSError, UnicodeError, ValueError) as error:
                self.report(problem('invalid-context', path, str(error)))
                return self
        if not isinstance(data, dict) or set(data) - {'schema_version', 'scopes', 'dependency_evidence'} or type(data.get('schema_version')) is not int or data['schema_version'] != 1 or not isinstance(data.get('scopes'), list):
            self.report(problem('invalid-context', path, 'Expected version 1 with positive scopes and optional dependency_evidence'))
            return self
        for index, claim in enumerate(list(data['scopes']) + list(additional_claims)):
            location = str(path) + f':scopes[{index}]'
            if not isinstance(claim, dict) or set(claim) - {'root', 'house', 'architecture', 'adopted_suites'} or 'root' not in claim:
                self.report(problem('invalid-context', location, 'Scope requires root and only positive context facets'))
                continue
            root = None
            try:
                root = repository_path(self.graph.repository, claim['root'], strict=True)
                if not root.is_dir():
                    raise ValueError('Scope root must be an existing directory')
                values = {}
                house = claim.get('house', {})
                if not isinstance(house, dict) or any(not isinstance(key, str) or not key.strip() or not isinstance(value, str) or not value.strip() for key, value in house.items()):
                    raise ValueError('House requires non-empty identity strings')
                values.update(('house.' + key, value) for key, value in house.items())
                for facet in ('architecture', 'adopted_suites'):
                    items = claim.get(facet, [])
                    if not isinstance(items, list) or any(not isinstance(item, str) or not item.strip() for item in items) or len(set(items)) != len(items):
                        raise ValueError(facet + ' requires unique positive identity strings')
                    values[facet] = items
                self.claims.append({'root': root, 'values': values, 'path': location})
            except ValueError as error:
                self.report(problem('invalid-context', location, str(error)), root=root)
        for index, left in enumerate(self.claims):
            for right in self.claims[index + 1:]:
                if not (left['root'].is_relative_to(right['root']) or right['root'].is_relative_to(left['root'])):
                    continue
                for key in set(left['values']) & set(right['values']):
                    if key.startswith('house.') and left['values'][key] != right['values'][key]:
                        self.report(problem('conflicting-context', right['path'], key + ': incompatible overlapping house claims at ' + left['path']),
                                    root=left['root'] if left['root'].is_relative_to(right['root']) else right['root'])
        evidence = data.get('dependency_evidence', [])
        if not isinstance(evidence, list):
            self.report(problem('invalid-dependency-evidence', path, 'dependency_evidence requires an array'))
        else:
            for index, entry in enumerate(evidence):
                self._supplement(entry, str(path) + f':dependency_evidence[{index}]')
        return self

    def _supplement(self, entry, path):
        try:
            if not isinstance(entry, dict) or set(entry) != {'project', 'dependency', 'evidence'}:
                raise ValueError('Evidence requires project, exact dependency and evidence records')
            identity = entry['project']
            if not isinstance(identity, str) or identity not in self.graph.projects:
                raise ValueError('Project must name an existing discovered manifest')
            dependency = entry['dependency']
            if not isinstance(dependency, dict) or set(dependency) != {'kind', 'id'} or dependency['kind'] not in _PATHS['KINDS'] or not isinstance(dependency['id'], str) or not dependency['id'].strip():
                raise ValueError('Dependency requires kind and an exact non-empty id')
            status = self.graph.dependency(identity, dependency)
            if status['matched']:
                raise ValueError('Already-proven dependency evidence is redundant')
            if not status['diagnostics']:
                raise ValueError('Evidence cannot replace proven absence')
            evidence = entry['evidence']
            if not isinstance(evidence, list) or not evidence:
                raise ValueError('Evidence requires non-empty path/reason records')
            unresolved = {item['path'] for item in status['diagnostics']}
            for item in evidence:
                if not isinstance(item, dict) or set(item) != {'path', 'reason'} or not isinstance(item['reason'], str) or not item['reason'].strip():
                    raise ValueError('Evidence requires path and a non-empty reason')
                candidate = repository_path(self.graph.repository, item['path'], strict=True)
                relative = candidate.relative_to(self.graph.repository).as_posix()
                if not candidate.is_file() or relative not in unresolved:
                    raise ValueError('Evidence must exist and identify this dependency\'s unresolved manifest or import')
            self.supplements.append(entry)
        except (ValueError, TypeError) as error:
            self.report(problem('invalid-dependency-evidence', path, str(error)))

    def for_project(self, identity):
        project = self.graph.projects[identity]
        values = {'architecture': [], 'adopted_suites': []}
        evidence = []
        for claim in self.claims:
            if project.root.is_relative_to(claim['root']):
                evidence.append(claim['path'])
                for key, value in claim['values'].items():
                    if isinstance(value, list):
                        values[key] = sorted(set(values.get(key, [])) | set(value))
                    elif key not in values:
                        values[key] = value
        return values, evidence
