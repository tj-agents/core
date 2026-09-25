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
this script reads whatever declarations are installed. A tier repository added later - `cpp` is not
even cloned yet - is gated the moment it is installed, with no change here and no release of `base`.
Plugin and marketplace identity come from the installed path, never from the declaration, so a
declaration cannot claim to be a plugin it is not.

Two modes, one detection:

- `--session-context` (SessionStart) states which tiers apply in this project. It prints nothing at
  all when no stack tier is installed, because a statement about an empty set is pure noise.
- No argument (PreToolUse) blocks invoking a skill that belongs to a tier whose stack is absent.
  Claude sends the `Skill` tool and the qualified name; Codex has no such tool, and its contract is a
  successful shell read of the tier's own `SKILL.md`, so a shell command naming a blocked plugin's
  cache path *and* `SKILL.md` is the same event in the other host's shape. Matching only Claude's
  shape would be a gate that looks wired while allowing every Codex read.

A tier's own authoring repository is exempt. `dotagents` contains no .NET, so without that exemption
the gate would refuse to read the very standards being edited there.

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


SCHEMA_VERSION = 1
DECLARATION_NAME = "tier.json"
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


class Declaration:
    def __init__(self, plugin, marketplace, data):
        self.plugin = plugin
        self.marketplace = marketplace
        self.tier = data["tier"]
        self.applies = data["applies"]
        self.stack = data.get("stack") or data["tier"]
        owner = data.get("owner_repository")
        owner = [owner] if isinstance(owner, str) else list(owner or [])
        self.owner_repositories = [_text(name).lower() for name in owner if _text(name)]
        self.detect = data.get("detect") or {}

    @property
    def id(self):
        return f"{self.plugin}@{self.marketplace}"

    @property
    def gated(self):
        return self.applies == "stack-present"


def _text(value):
    return value if isinstance(value, str) else ""


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

    for variable in ("CLAUDE_CONFIG_DIR", "CODEX_HOME"):
        value = os.environ.get(variable)
        if value:
            add(Path(value) / "plugins" / "cache")

    home = Path.home()
    add(home / ".claude" / "plugins" / "cache")
    add(home / ".codex" / "plugins" / "cache")
    return roots


def declarations(roots=None):
    found = {}
    for root in cache_roots() if roots is None else roots:
        try:
            paths = sorted(Path(root).glob("*/*/*/" + DECLARATION_NAME))
        except OSError:
            continue
        for path in paths:
            version_directory = path.parent
            plugin = version_directory.parent.name
            marketplace = version_directory.parent.parent.name
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, UnicodeError, ValueError):
                continue
            if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
                continue
            if not _text(data.get("tier")) or data.get("applies") not in ("always", "stack-present"):
                continue
            declaration = Declaration(plugin, marketplace, data)
            found[declaration.id] = declaration
    return sorted(found.values(), key=lambda declaration: declaration.tier)


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


def assess(root, found=None):
    found = declarations() if found is None else found
    if not found:
        return [], [], []

    forced = overridden()
    identity = None
    ubiquitous, applicable, blocked = [], [], []
    for declaration in found:
        if not declaration.gated:
            ubiquitous.append(declaration)
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
    return ubiquitous, applicable, blocked


def statement(root, found=None):
    ubiquitous, applicable, blocked = assess(root, found)
    if not applicable and not blocked:
        return ""

    lines = ["base:stack-tiers - which standards apply in this project"]
    if ubiquitous:
        names = ", ".join(declaration.tier for declaration in ubiquitous)
        lines.append("Ubiquitous, always applies: " + names + ".")
    for declaration, reason in applicable:
        lines.append("Applies here: `" + declaration.plugin + ":*` - " + reason + ".")
    if blocked:
        names = ", ".join(
            "`" + declaration.plugin + ":*` (no " + declaration.stack + " here)"
            for declaration in blocked
        )
        lines.append(
            "Does not apply here: " + names + ". Those standards describe code this project does "
            "not contain - do not read, invoke or cite them here. A PreToolUse gate blocks them."
        )
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


def refusal(declaration, subject, root):
    markers = [*(declaration.detect.get("files") or []), *(declaration.detect.get("globs") or [])]
    patterns = ", ".join(str(marker) for marker in markers) or "its declared markers"
    owner = declaration.owner_repositories[0] if declaration.owner_repositories else declaration.id
    return (
        "base:stack-tiers blocked " + subject + ".\n"
        "It belongs to the `" + declaration.tier + "` tier, which applies only to projects with "
        + declaration.stack + ". " + str(root) + " has no match for " + patterns + ", so that "
        "standard describes code this project does not contain. Use the ubiquitous core standards "
        "here instead.\n"
        "If this project really is " + declaration.stack + ", the detection is wrong: fix "
        "`tier.json` in " + owner + " rather than working around it. To force it for this session "
        "only, set " + OVERRIDE_VARIABLE + "=" + declaration.tier + "."
    )


def gate(payload, found=None):
    root = project_root(payload)
    _, _, blocked = assess(root, found)
    if not blocked:
        return 0

    name = requested_skill(payload)
    plugin, separator, skill = name.partition(":")
    if separator and skill:
        for declaration in blocked:
            if declaration.plugin == plugin:
                print(refusal(declaration, "`" + name + "`", root), file=sys.stderr)
                return 2

    command = shell_command(payload)
    if command and "SKILL.md" in command:
        haystack = command.replace("\\", "/")
        for declaration in blocked:
            if "/" + declaration.marketplace + "/" + declaration.plugin + "/" in haystack:
                subject = "that read of a `" + declaration.tier + "` standard"
                print(refusal(declaration, subject, root), file=sys.stderr)
                return 2
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-context", action="store_true")
    parser.add_argument("--instruction-fragment", action="store_true")
    parser.add_argument("--project", default=None)
    arguments = parser.parse_args()

    if sys.version_info < (3, 9):
        print("stack-tiers: Python 3.9 or newer is required.", file=sys.stderr)
        return 0

    emitting = arguments.session_context or arguments.instruction_fragment
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

    if emitting:
        context = statement(project_root(payload))
        if not context:
            return 0
        if arguments.instruction_fragment:
            print("<!-- BEGIN base:stack-tiers -->\n" + context + "\n<!-- END base:stack-tiers -->")
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
