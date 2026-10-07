r"""Answer "does this stack tier apply to the project I am in?" for both hosts.

The corpus is layered: the base, engineering and machine packages are stack-agnostic process and
behavior, so they apply in every project. `dotnet`, `react` and `cpp` are stack tiers, and a tier
whose stack is absent is not merely unhelpful - it is wrong, because its standards describe code the
project does not contain. Nothing in either host expresses that. A plugin manifest has
`defaultEnabled` and `dependencies` but no condition, and the two native gating knobs
(`enabledPlugins`, `skillOverrides`) are settings, at scopes that are either machine-local or written
per consuming repository. Both were ruled out: the rule has to travel inside the corpus so a fresh
machine picks it up by syncing, with nothing hand-placed anywhere.

So each tier ships the condition itself, as `tier.json` at the root of its own plugin payload, and
this script reads whatever declarations are installed. A tier repository added later is gated
the moment it is installed, with no change here and no release of `base`.
Plugin and marketplace identity come from the installed path, never from the declaration, so a
declaration cannot claim to be a plugin it is not.

Three modes, one detection:

- `--session-context` (SessionStart) states which tiers apply in this project. It prints nothing at
  all when no stack tier is installed, because a statement about an empty set is pure noise.
- `--conventions` lists, for every tier that applies here, the conventions its installed payload
  ships - the skills whose front matter declares `kind: convention` or legacy `kind: contract`. This is what a review loads: the
  applicable tiers' rules, resolved from the same installed declarations the gate reads, with nothing
  wired into the reviewed repository.
- No argument (PreToolUse) blocks invoking a skill that belongs to a tier whose stack is absent.
  Claude sends the `Skill` tool and the qualified name; Codex has no such tool, and its contract is a
  successful shell read of the tier's own `SKILL.md`, so a shell command naming a blocked plugin's
  cache path *and* `SKILL.md` is the same event in the other host's shape. Matching only Claude's
  shape would be a gate that looks wired while allowing every Codex read.

A tier's own authoring repository is exempt, even when its source files do not contain the
stack's normal project markers.

Contract: exit 0 allows, exit 2 blocks with stderr fed back to the agent. Anything unexpected exits 0.
A gate that wedges a session is worse than a gate that misses one call.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlsplit


SCHEMA_VERSIONS = (1, 2, 3)
DECLARATION_NAME = "tier.json"
ORPHAN_MARKER = ".orphaned_at"
FRONT_MATTER_KIND = re.compile(r"^kind:[ \t]*([a-z]+)[ \t]*$", re.MULTILINE)
CONVENTION_KINDS = frozenset({"contract", "convention"})
PLUGIN_ROOT_VARIABLES = ("CLAUDE_PLUGIN_ROOT", "PLUGIN_ROOT", "CODEX_PLUGIN_ROOT")
OVERRIDE_VARIABLE = "AGENTS_TIER_OVERRIDE"
SHELL_TOOLS = frozenset({"Bash", "PowerShell", "Shell", "shell", "exec", "local_shell"})
WALK_DEPTH = 4
WALK_SKIP = frozenset({
    ".git", ".hg", ".svn", ".worktrees", "node_modules", "bin", "obj", "dist", "build",
    "target", "vendor", "__pycache__", ".venv", "venv", ".next", ".nuget", "packages",
})
CONTENT_CANDIDATES = 20
CONTENT_BYTES = 256 * 1024
GIT_TIMEOUT = 10
REMOTE_HOST_PATTERN = r"(?=.{1,253}\.?(?![\s\S]))[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*\.?"


class Declaration:
    def __init__(self, plugin, marketplace, data, payload_dir=None, orphaned=False, diagnostics=()):
        self.plugin = plugin
        self.data = data
        self.schema_version = data.get("schema_version")
        self.marketplace = marketplace
        self.tier = _text(data.get("tier")) or plugin
        self.applies = data.get("applies")
        self.stack = _text(data.get("stack")) or self.tier
        owner = data.get("owner_repository")
        owner = [owner] if isinstance(owner, str) else owner if isinstance(owner, list) else []
        self.owner_repositories = [_text(name).lower() for name in owner if _text(name)]
        self.detect = data.get("detect") if isinstance(data.get("detect"), dict) else {}
        self.payload_dir = payload_dir
        self.orphaned = orphaned
        self.diagnostics = tuple(diagnostics)
        self.employer = data.get("employer") if self.schema_version == 3 else None
        self.session_context = _text(data.get("session_context")) if self.schema_version == 3 else ""

    @property
    def id(self):
        return f"{self.plugin}@{self.marketplace}"

    @property
    def gated(self):
        return self.applies == "stack-present"


def _text(value):
    return value if isinstance(value, str) else ""


class PredicateResult:
    def __init__(self, scope, matched=False, evidence=(), prerequisites=(), diagnostics=()):
        self.scope = str(scope)
        self.matched = matched and not diagnostics
        self.evidence = tuple(dict.fromkeys(evidence))
        self.prerequisites = tuple(dict.fromkeys(prerequisites))
        self.diagnostics = tuple(diagnostics)


def diagnostic(code, path, message):
    return {"code": code, "path": path, "message": message}


def predicate_diagnostics(node, path="detect"):
    if not isinstance(node, dict) or len(node) != 1:
        return [diagnostic("malformed-predicate", path, "Expected exactly one positive predicate operator")]
    operator, value = next(iter(node.items()))
    if operator in ("all", "any"):
        if not isinstance(value, list) or not value:
            return [diagnostic("malformed-predicate", path, operator + " requires a non-empty array")]
        return [problem for index, child in enumerate(value)
                for problem in predicate_diagnostics(child, f"{path}.{operator}[{index}]")]
    if operator in ("file", "glob", "remote", "remote_host", "fact"):
        if not isinstance(value, str) or not value:
            return [diagnostic("malformed-predicate", path, operator + " requires a non-empty string")]
        if operator == "remote_host" and not re.fullmatch(REMOTE_HOST_PATTERN, value):
            return [diagnostic("malformed-predicate", path, "Remote host requires an exact hostname")]
        if operator == "remote":
            try:
                re.compile(value)
            except re.error:
                return [diagnostic("malformed-predicate", path, "Remote pattern does not compile")]
        return []
    if operator == "content":
        if not isinstance(value, dict) or set(value) != {"glob", "pattern"} or any(
                not isinstance(value[key], str) or not value[key] for key in ("glob", "pattern")):
            return [diagnostic("malformed-predicate", path, "Content requires glob and pattern strings")]
        try:
            re.compile(value["pattern"])
        except re.error:
            return [diagnostic("malformed-predicate", path, "Content pattern does not compile")]
        return []
    if operator == "context":
        if not isinstance(value, dict) or set(value) not in ({"key", "equals"}, {"key", "contains"}) or any(
                not isinstance(item, str) or not item for item in value.values()):
            return [diagnostic("malformed-predicate", path, "Context requires key and equals or contains strings")]
        return []
    return [diagnostic("unsupported-predicate", path, "Unsupported positive operator: " + str(operator))]


def predicate_uses_fact(node, name):
    if not isinstance(node, dict):
        return False
    if node.get("fact") == name:
        return True
    return any(predicate_uses_fact(child, name) for operator in ("all", "any")
               for child in (node[operator] if isinstance(node.get(operator), list) else []))


def employer_context_path(payload_dir, slug):
    if payload_dir is None or not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        return None
    try:
        payload = Path(payload_dir).resolve()
        skill = (payload / "skills" / slug / "SKILL.md").resolve()
        skill.relative_to(payload)
        text = skill.read_text(encoding="utf-8-sig")
        block = front_matter(text)
        name = re.search(r"^name:[ \t]*([^\r\n]+?)[ \t]*$", block, re.MULTILINE)
        if name is None or name.group(1) != slug or FRONT_MATTER_KIND.search(block) is None:
            return None
        return skill
    except (OSError, UnicodeError, ValueError, RuntimeError):
        return None


def v3_declaration_diagnostics(data, path="tier.json", payload_dir=None):
    problems = []
    unknown = set(data) - {"schema_version", "tier", "applies", "stack", "owner_repository", "detect",
                           "employer", "session_context"}
    if unknown:
        problems.append(diagnostic("malformed-declaration", path, "Unknown declaration fields: " + ", ".join(sorted(unknown))))
    if not isinstance(data.get("tier"), str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", data["tier"]):
        problems.append(diagnostic("malformed-declaration", path, "Tier requires a lowercase tier identifier"))
    if data.get("applies") not in ("always", "stack-present"):
        problems.append(diagnostic("malformed-declaration", path, "Applies requires always or stack-present"))
    if "stack" in data and (not isinstance(data["stack"], str) or not data["stack"]):
        problems.append(diagnostic("malformed-declaration", path, "Stack requires a non-empty string"))
    if "owner_repository" in data:
        owner = data["owner_repository"]
        owners = [owner] if isinstance(owner, str) else owner
        if not isinstance(owners, list) or any(not isinstance(item, str) or not re.fullmatch(r"[^/ ]+/[^/ ]+", item)
                                              for item in owners) or len(set(owners)) != len(owners):
            problems.append(diagnostic("malformed-declaration", path, "Owner requires unique owner/name strings"))
    if data.get("applies") == "stack-present" or "detect" in data:
        problems.extend(predicate_diagnostics(data.get("detect"), path + ".detect"))
    if "session_context" in data:
        context = data["session_context"]
        if not isinstance(context, str) or not context.strip() or any(char in context for char in "\r\n\u0085\u2028\u2029"):
            problems.append(diagnostic("malformed-declaration", path + ".session_context", "Session context requires one non-empty line"))
    if "employer" in data:
        employer = data["employer"]
        if not isinstance(employer, dict) or set(employer) != {"context_skill"} or not isinstance(
                employer.get("context_skill"), str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", employer["context_skill"]):
            problems.append(diagnostic("malformed-employer", path + ".employer", "Employer requires a local context_skill slug"))
        elif payload_dir is not None and employer_context_path(payload_dir, employer["context_skill"]) is None:
            problems.append(diagnostic("missing-employer-context", path + ".employer.context_skill", "Employer context skill must be readable and shipped within this payload"))
        if data.get("applies") != "stack-present":
            problems.append(diagnostic("malformed-employer", path + ".applies", "Employer declarations require stack-present"))
        if predicate_uses_fact(data.get("detect"), "employer"):
            problems.append(diagnostic("employer-self-dependency", path + ".detect", "Employer declarations cannot depend on the employer fact"))
    return problems


def evaluate_predicate(root, node, facts=None, contexts=None, path="detect"):
    return _evaluate_predicate(root, node, facts, contexts, path)


def _evaluate_predicate(root, node, facts=None, contexts=None, path="detect", employer_result=None):
    problems = predicate_diagnostics(node, path)
    if problems:
        return PredicateResult(root, diagnostics=problems)
    operator, value = next(iter(node.items()))
    if operator in ("all", "any"):
        children = [_evaluate_predicate(root, child, facts, contexts, f"{path}.{operator}[{index}]", employer_result)
                    for index, child in enumerate(value)]
        matches = [child.matched for child in children]
        return PredicateResult(root, all(matches) if operator == "all" else any(matches),
                               [item for child in children if child.matched for item in child.evidence],
                               [item for child in children for item in child.prerequisites],
                               [item for child in children for item in child.diagnostics])
    if operator == "fact":
        if value == "employer":
            if employer_result is None:
                return PredicateResult(root, prerequisites=[value], diagnostics=[
                    diagnostic("reserved-fact", path, "Employer evidence is derived from installed employer declarations")])
            return PredicateResult(root, employer_result.matched, employer_result.evidence, [value])
        if facts is None or value not in facts:
            return PredicateResult(root, prerequisites=[value], diagnostics=[
                diagnostic("unknown-fact", path, "Provide scoped evidence for fact: " + value)])
        fact = facts[value]
        if not isinstance(fact, PredicateResult) or fact.scope != str(root) or fact.diagnostics:
            return PredicateResult(root, prerequisites=[value], diagnostics=[
                diagnostic("invalid-fact", path, "Fact requires a valid result in this scope: " + value)])
        return PredicateResult(root, fact.matched, fact.evidence, [value])
    if operator == "context":
        key = value["key"]
        if contexts is None or key not in contexts:
            return PredicateResult(root, prerequisites=["context:" + key], diagnostics=[
                diagnostic("unknown-context", path, "Provide scoped context: " + key)])
        actual = contexts[key]
        comparison = value.get("equals", value.get("contains"))
        if "equals" in value:
            valid = isinstance(actual, str)
            matched = actual == comparison
        else:
            valid = isinstance(actual, list) and all(isinstance(item, str) for item in actual)
            matched = valid and comparison in actual
        if not valid:
            return PredicateResult(root, diagnostics=[diagnostic("invalid-context", path, "Context has incompatible value: " + key)])
        return PredicateResult(root, matched, ["context " + key] if matched else [], ["context:" + key])
    if operator == "remote_host":
        host = repository_host(root)
        matched = host is not None and host == value.rstrip(".").lower()
        return PredicateResult(root, matched, ["origin host " + host] if matched else [])
    legacy = {"file": "files", "glob": "globs", "remote": "remote", "content": "content"}
    matched, evidence = stack_present(root, {legacy[operator]: [value]})
    return PredicateResult(root, matched, [evidence] if evidence else [])


class SelectionResult:
    def __init__(self, scope, ubiquitous=(), applicable=(), blocked=(), diagnostics=(), selections=(), employers=()):
        self.scope = str(scope)
        self.ubiquitous = list(ubiquitous)
        self.applicable = list(applicable)
        self.blocked = list(blocked)
        self.diagnostics = tuple(diagnostics)
        self.selections = tuple(selections)
        self.employers = tuple(employers)

    def __iter__(self):
        return iter((self.ubiquitous, self.applicable, self.blocked))


def cache_roots():
    roots = []

    def add(path):
        try:
            resolved = Path(path).resolve()
        except (OSError, ValueError):
            return
        if resolved.is_dir() and resolved not in roots:
            roots.append(resolved)

    for variable in PLUGIN_ROOT_VARIABLES:
        value = os.environ.get(variable)
        if not value:
            continue
        try:
            plugin_root = Path(value).resolve()
        except (OSError, ValueError):
            continue
        if len(plugin_root.parents) >= 3:
            add(plugin_root.parents[2])

    here = Path(__file__).resolve()
    if len(here.parents) > 4 and here.parents[4].name == "cache":
        add(here.parents[4])

    for variable in ("CLAUDE_CONFIG_DIR", "CODEX_HOME"):
        value = os.environ.get(variable)
        if value:
            add(Path(value) / "plugins" / "cache")

    home = Path.home()
    add(home / ".claude" / "plugins" / "cache")
    add(home / ".codex" / "plugins" / "cache")
    return roots


def _key(path):
    return os.path.normcase(os.path.normpath(str(path)))


def _resolved_key(path):
    try:
        return _key(Path(path).resolve())
    except (OSError, ValueError):
        return _key(path)


def _within(key, ancestor):
    return key == ancestor or key.startswith(ancestor.rstrip("\\/") + os.sep)


def installed_declarations(root, project=None):
    """Each installed `tier.json` the registry beside this cache names, with its scope rank, or None.

    A project-scoped install outranks the user-scope one, the most specific project first; one scoped
    to another project does not count. Reading only installed paths keeps the per-call cost
    proportional to installed plugins, not to the stale versions a cache accumulates.
    """
    registry = Path(root).parent / "installed_plugins.json"
    try:
        plugins = json.loads(registry.read_text(encoding="utf-8-sig")).get("plugins")
    except (OSError, UnicodeError, ValueError, AttributeError):
        return None
    if not isinstance(plugins, dict):
        return None
    cache = _resolved_key(root)
    here = _resolved_key(project) if project is not None else None
    ranked = {}
    for entries in plugins.values():
        for entry in entries if isinstance(entries, list) else ():
            location = entry.get("installPath") if isinstance(entry, dict) else None
            if not _text(location):
                continue
            scoped = _text(entry.get("projectPath"))
            rank = -1
            if scoped:
                scope = _resolved_key(scoped)
                if here is None or not _within(here, scope):
                    continue
                rank = len(scope)
            ancestor = Path(location).parent.parent.parent
            if _key(ancestor) != cache and _resolved_key(ancestor) != cache:
                continue
            path = Path(location) / DECLARATION_NAME
            ranked[path] = max(rank, ranked.get(path, rank))
    return ranked


def declarations(roots=None, project=None, diagnostics=None):
    """One declaration per plugin: the first cache root that has it, at its installed version.

    Roots are in priority order, the running host's cache first. A cache with a host registry beside it
    answers only for its installed versions; one without falls back to every cached version, newest first.
    """
    found = {}
    for root in cache_roots() if roots is None else roots:
        ranked = installed_declarations(root, project)
        if ranked is None:
            try:
                ranked = dict.fromkeys(sorted(Path(root).glob("*/*/*/" + DECLARATION_NAME)), -1)
            except OSError:
                continue
        candidates = {}
        for path, rank in sorted(ranked.items()):
            version_directory = path.parent
            plugin = version_directory.parent.name
            marketplace = version_directory.parent.parent.name
            problems = []
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
            except FileNotFoundError:
                continue
            except (OSError, UnicodeError, ValueError):
                data = {}
                problems.append(diagnostic("unreadable-declaration", str(path), "Read a valid tier.json declaration"))
            if not isinstance(data, dict):
                data = {}
                problems.append(diagnostic("malformed-declaration", str(path), "Declare tier.json as an object"))
            if not problems:
                if data.get("schema_version") not in SCHEMA_VERSIONS:
                    problems.append(diagnostic("unsupported-version", str(path), "Supported tier schema versions: 1, 2, 3"))
                elif data.get("schema_version") == 3:
                    problems.extend(v3_declaration_diagnostics(data, str(path), version_directory))
                elif not _text(data.get("tier")) or data.get("applies") not in ("always", "stack-present"):
                    problems.append(diagnostic("malformed-declaration", str(path), "Declare tier and applies"))
            orphaned = (version_directory / ORPHAN_MARKER).exists()
            declaration = Declaration(plugin, marketplace, data, version_directory, orphaned, problems)
            preference = _preference(declaration, rank)
            current = candidates.get(declaration.id)
            if current is None or preference > current[0]:
                candidates[declaration.id] = (preference, declaration)
        for identity, (_, declaration) in candidates.items():
            current = found.get(identity)
            if current is None or (current.orphaned and not declaration.orphaned):
                found[identity] = declaration
    selected = sorted(found.values(), key=lambda declaration: declaration.tier)
    if diagnostics is not None:
        diagnostics.extend(problem for declaration in selected for problem in declaration.diagnostics)
    return selected


def _preference(declaration, rank):
    """The most specific install scope, then live over orphaned, then the newest directory."""
    try:
        modified = declaration.payload_dir.stat().st_mtime
    except OSError:
        modified = 0.0
    return (rank, not declaration.orphaned, modified)


def project_root(payload):
    for key in ("cwd", "workspace_root", "project_dir", "projectDir"):
        value = _text(payload.get(key))
        if value:
            return Path(value)
    for variable in ("CLAUDE_PROJECT_DIR", "CODEX_PROJECT_DIR"):
        value = os.environ.get(variable)
        if value:
            return Path(value)
    return Path.cwd()


def _git(root, arguments):
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *arguments],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def repository_host(root):
    output = _git(root, ["config", "--get", "remote.origin.url"])
    if output is None:
        return None
    origin = output.removesuffix("\n").removesuffix("\r")
    if not origin or re.search(r"[\s\x00-\x1f\x7f\\]", origin):
        return None
    if "://" in origin:
        try:
            url = urlsplit(origin)
            if url.scheme not in ("https", "http", "ssh", "git") or not url.hostname or "?" in origin or "#" in origin or url.netloc.endswith(":"):
                return None
            if url.port is not None and not 1 <= url.port <= 65535:
                return None
            host, path = url.hostname, url.path.lstrip("/")
        except ValueError:
            return None
    else:
        match = re.fullmatch(r"[^@/:]+@([^/:]+):(.+)", origin)
        if match is None:
            return None
        host, path = match.groups()
        path = path.lstrip("/")
    if not re.fullmatch(REMOTE_HOST_PATTERN, host) or not path or any(part in ("", ".", "..") for part in path.rstrip("/").split("/")):
        return None
    return host.rstrip(".").lower()


def repository_identity(root):
    output = _git(root, ["config", "--get", "remote.origin.url"])
    if output is None:
        return None
    url = output.strip()
    if not url:
        return None
    if url.endswith(".git"):
        url = url[:-4]
    parts = [part for part in re.split(r"[/:]", url) if part]
    if len(parts) < 2:
        return None
    return (parts[-2] + "/" + parts[-1]).lower()


def _tracked_matches(root, patterns):
    output = _git(root, [
        "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *patterns,
    ])
    if output is None:
        return None
    return [entry for entry in output.split("\0") if entry]


def _walked_matches(root, patterns):
    matches = []
    root = Path(root)
    for current, directories, files in os.walk(root):
        relative = Path(current).relative_to(root)
        depth = 0 if str(relative) == "." else len(relative.parts)
        if depth >= WALK_DEPTH:
            directories[:] = []
        else:
            directories[:] = [
                name for name in directories if name not in WALK_SKIP and not name.startswith(".")
            ]
        for name in files:
            if any(fnmatch.fnmatch(name, pattern) for pattern in patterns):
                matches.append((relative / name).as_posix())
                if len(matches) >= CONTENT_CANDIDATES:
                    return matches
    return matches


def matching_paths(root, patterns):
    patterns = [pattern for pattern in patterns if isinstance(pattern, str) and pattern]
    if not patterns:
        return []
    tracked = _tracked_matches(root, patterns)
    if tracked is not None:
        return tracked
    return _walked_matches(root, patterns)


def stack_present(root, detect):
    root = Path(root)
    if not root.is_dir():
        return False, None

    for name in detect.get("files") or []:
        if not isinstance(name, str):
            continue
        try:
            if (root / name).exists():
                return True, name
        except OSError:
            continue

    matches = matching_paths(root, detect.get("globs") or [])
    if matches:
        return True, matches[0]

    remote_patterns = [_text(pattern) for pattern in detect.get("remote") or [] if _text(pattern)]
    if remote_patterns:
        identity = repository_identity(root)
        if identity:
            for pattern in remote_patterns:
                try:
                    expression = re.compile(pattern, re.IGNORECASE)
                except re.error:
                    continue
                if expression.search(identity):
                    return True, "origin " + identity

    for rule in detect.get("content") or []:
        if not isinstance(rule, dict):
            continue
        glob = _text(rule.get("glob"))
        pattern = _text(rule.get("pattern"))
        if not glob or not pattern:
            continue
        try:
            expression = re.compile(pattern)
        except re.error:
            continue
        for candidate in matching_paths(root, [glob])[:CONTENT_CANDIDATES]:
            try:
                text = (root / candidate).read_text(encoding="utf-8-sig", errors="ignore")
            except (OSError, UnicodeError):
                continue
            if expression.search(text[:CONTENT_BYTES]):
                return True, candidate

    return False, None


def overridden():
    raw = os.environ.get(OVERRIDE_VARIABLE) or ""
    return {part.strip().lower() for part in raw.split(",") if part.strip()}


def declaration_diagnostics(declaration):
    if declaration.diagnostics:
        return declaration.diagnostics
    if declaration.schema_version not in SCHEMA_VERSIONS:
        return (diagnostic("unsupported-version", declaration.id, "Supported tier schema versions: 1, 2, 3"),)
    if declaration.schema_version != 3:
        return ()
    path = str(Path(declaration.payload_dir) / DECLARATION_NAME) if declaration.payload_dir else declaration.id
    problems = v3_declaration_diagnostics(declaration.data, path, declaration.payload_dir)
    if declaration.employer is not None:
        if declaration.payload_dir is None:
            problems.append(diagnostic("missing-employer-context", path, "Employer context requires an installed payload"))
        if declaration.orphaned:
            problems.append(diagnostic("orphaned-employer", path, "An orphaned employer payload cannot establish applicability"))
    return tuple(problems)


def assess(root, found=None, facts=None, contexts=None):
    diagnostics = []
    selections = []
    found = list(declarations(project=root) if found is None else found)
    if not found:
        return SelectionResult(root, diagnostics=diagnostics)

    forced = overridden()
    identity = None
    ubiquitous, applicable, blocked = [], [], []
    problems_by_id = {declaration.id: declaration_diagnostics(declaration) for declaration in found}
    employers = []
    employer_predicates = {}
    for declaration in found:
        if declaration.employer is None or problems_by_id[declaration.id]:
            continue
        result = evaluate_predicate(root, declaration.detect, facts, contexts)
        employer_predicates[declaration.id] = result
        if result.matched:
            employers.append((declaration, result))
    employer_result = PredicateResult(root, bool(employers),
                                     [declaration.id + ": " + item for declaration, result in employers
                                      for item in result.evidence])
    for declaration in found:
        problems = problems_by_id[declaration.id]
        if problems:
            diagnostics.extend(problems)
            selections.append({"plugin_id": declaration.id, "scope": str(root),
                               "predicate": declaration.detect, "matched": False,
                               "prerequisites": (), "evidence": (), "diagnostics": problems})
            blocked.append(declaration)
            continue
        if not declaration.gated:
            ubiquitous.append(declaration)
            continue
        if declaration.schema_version == 3:
            result = employer_predicates.get(declaration.id)
            if result is None:
                result = _evaluate_predicate(root, declaration.detect, facts, contexts, employer_result=employer_result)
            selections.append({"plugin_id": declaration.id, "scope": result.scope,
                               "predicate": declaration.detect, "matched": result.matched,
                               "prerequisites": result.prerequisites, "evidence": result.evidence,
                               "diagnostics": result.diagnostics})
            diagnostics.extend(result.diagnostics)
            if result.matched:
                applicable.append((declaration, declaration.stack + " detected"))
            else:
                blocked.append(declaration)
            continue
        if declaration.tier.lower() in forced:
            applicable.append((declaration, "forced by " + OVERRIDE_VARIABLE))
            continue
        if declaration.owner_repositories:
            if identity is None:
                identity = repository_identity(root) or ""
            if identity and identity in declaration.owner_repositories:
                applicable.append((declaration, "this is the tier's own repository"))
                continue
        present, evidence = stack_present(root, declaration.detect)
        if present:
            found_at = " (" + evidence + ")" if evidence else ""
            applicable.append((declaration, declaration.stack + " detected" + found_at))
        else:
            blocked.append(declaration)
    return SelectionResult(root, ubiquitous, applicable, blocked, diagnostics, selections, employers)


def statement(root, found=None):
    result = assess(root, found)
    ubiquitous, applicable, blocked = result
    if not applicable and not blocked and not result.diagnostics and not any(
            declaration.session_context for declaration in ubiquitous):
        return ""

    lines = ["Tier gate - which standards apply in this project"]
    lines.extend("Configuration diagnostic: " + problem["path"] + ": " + problem["message"]
                 for problem in result.diagnostics)
    if ubiquitous:
        names = ", ".join(declaration.tier for declaration in ubiquitous)
        lines.append("Ubiquitous, always applies: " + names + ".")
    for declaration, reason in applicable:
        lines.append("Applies here: `" + declaration.plugin + ":*` - " + reason + ".")
    for declaration, _ in result.employers:
        path = employer_context_path(declaration.payload_dir, declaration.employer["context_skill"])
        lines.append("Employer context: `" + declaration.plugin + ":" + declaration.employer["context_skill"]
                     + "` - " + str(path))
    for declaration in [*ubiquitous, *(item for item, _ in applicable)]:
        if declaration.session_context:
            lines.append(declaration.session_context)
    if blocked:
        names = ", ".join(
            "`" + declaration.plugin + ":*` (no " + declaration.stack + " here)"
            for declaration in blocked
        )
        lines.append(
            "Does not apply here: " + names + ". Those standards describe code this project does "
            "not contain; do not invoke them or apply their rules to this project's code. "
            "For an explicitly requested standards-source audit, read canonical source files as "
            "the subject of the investigation and cite them as evidence. That inspection does not "
            "load them as governing instructions or make their tier applicable. Installed skill "
            "invocations and cached skill loads remain gated."
        )
    return "\n".join(lines)


def front_matter(text):
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[:end] if end != -1 else ""


def contract_skills(payload_dir):
    if payload_dir is None:
        return []
    try:
        entries = sorted((Path(payload_dir) / "skills").iterdir())
    except OSError:
        return []
    skills = []
    for entry in entries:
        skill = entry / "SKILL.md"
        try:
            text = skill.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        match = FRONT_MATTER_KIND.search(front_matter(text))
        if match and match.group(1) in CONVENTION_KINDS:
            skills.append((entry.name, skill))
    return skills


def conventions(root, found=None):
    """The review's rule source: each applicable stack tier's shipped conventions, as one listing."""
    result = assess(root, found)
    _, applicable, _ = result
    lines = ["Tier gate - conventions of every tier that applies to this project." if applicable else
             "Tier gate - no stack tier applies to this project; no tier conventions to load."]
    lines.extend("Configuration diagnostic: " + problem["path"] + ": " + problem["message"]
                 for problem in result.diagnostics)
    for declaration, reason in applicable:
        skills = contract_skills(declaration.payload_dir)
        lines.append("")
        lines.append(declaration.tier + " (" + reason + "): " + str(len(skills)) + " convention(s)")
        for name, path in skills:
            lines.append("  " + name + " - " + str(path))
    return "\n".join(lines)


def requested_skill(payload):
    tool = _text(payload.get("tool_name") or payload.get("toolName"))
    if tool != "Skill":
        return ""
    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    if not isinstance(tool_input, dict):
        return ""
    return _text(tool_input.get("skill") or tool_input.get("name"))


def shell_command(payload):
    tool = _text(payload.get("tool_name") or payload.get("toolName"))
    if tool not in SHELL_TOOLS:
        return ""
    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    if isinstance(command, list):
        command = " ".join(_text(part) for part in command)
    return _text(command)


def refusal(declaration, subject, root, diagnostics=()):
    if diagnostics:
        return "Tier gate blocked " + subject + ".\n" + "\n".join(
            "Configuration diagnostic for " + declaration.id + ": " + problem["path"] + ": " + problem["message"]
            for problem in diagnostics)
    markers = [
        *(declaration.detect.get("files") or []),
        *(declaration.detect.get("globs") or []),
        *(declaration.detect.get("remote") or []),
    ]
    patterns = ", ".join(str(marker) for marker in markers) or "its declared markers"
    owner = declaration.owner_repositories[0] if declaration.owner_repositories else declaration.id
    return (
        "Tier gate blocked " + subject + ".\n"
        "It belongs to the `" + declaration.tier + "` tier, which applies only to projects with "
        + declaration.stack + ". " + str(root) + " has no match for " + patterns + ", so that "
        "standard describes code this project does not contain. Use the ubiquitous core standards "
        "here instead.\n"
        "If this project really is " + declaration.stack + ", the detection is wrong: fix "
        "`tier.json` in " + owner + " rather than working around it."
        + (" To force it for this session only, set " + OVERRIDE_VARIABLE + "=" + declaration.tier + "."
           if declaration.schema_version < 3 else "")
    )


def selection_diagnostics(result, declaration):
    return tuple(problem for selection in result.selections if selection["plugin_id"] == declaration.id
                 for problem in selection["diagnostics"])


def gate(payload, found=None):
    root = project_root(payload)
    result = assess(root, found)
    _, _, blocked = result
    if not blocked:
        return 0

    name = requested_skill(payload)
    plugin, separator, skill = name.partition(":")
    if separator and skill:
        for declaration in blocked:
            if declaration.plugin == plugin:
                print(refusal(declaration, "`" + name + "`", root, selection_diagnostics(result, declaration)), file=sys.stderr)
                return 2

    command = shell_command(payload)
    if command and "SKILL.md" in command:
        haystack = command.replace("\\", "/")
        for declaration in blocked:
            if "/" + declaration.marketplace + "/" + declaration.plugin + "/" in haystack:
                subject = "that read of a `" + declaration.tier + "` standard"
                print(refusal(declaration, subject, root, selection_diagnostics(result, declaration)), file=sys.stderr)
                return 2
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-context", action="store_true")
    parser.add_argument("--instruction-fragment", action="store_true")
    parser.add_argument("--conventions", action="store_true")
    parser.add_argument("--project", default=None)
    arguments = parser.parse_args()

    if sys.version_info < (3, 9):
        print("tier gate: Python 3.9 or newer is required.", file=sys.stderr)
        return 0

    emitting = arguments.session_context or arguments.instruction_fragment or arguments.conventions
    payload = {}
    if not emitting:
        try:
            raw = sys.stdin.read()
        except (OSError, UnicodeError):
            return 0
        try:
            payload = json.loads(raw) if raw.strip() else {}
        except ValueError:
            return 0
        if not isinstance(payload, dict):
            return 0

    if arguments.project:
        payload["cwd"] = arguments.project

    if arguments.conventions:
        print(conventions(project_root(payload)))
        return 0

    if emitting:
        context = statement(project_root(payload))
        if not context:
            return 0
        if arguments.instruction_fragment:
            print("<!-- BEGIN tier-gate -->\n" + context + "\n<!-- END tier-gate -->")
        else:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "SessionStart", "additionalContext": context
            }}, ensure_ascii=True))
        return 0

    return gate(payload)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        raise SystemExit(0)
