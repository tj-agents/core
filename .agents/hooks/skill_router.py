r"""PreToolUse hook: the file you are about to write decides which standard you must read.

The failure this exists for: an agent added a test, never invoked `unit-testing` or
`integration-testing` though both were installed and listed, misclassified the test, and its own
`/review` repeated the blind spot and returned clean. Nothing was unreachable. The standard was
optional, and optional lost.

So the trigger stops being "the model decided this topic is relevant" and becomes "the path being
written". `.agents/skill-routes.json` maps path -> owning skill; a new concern is a new row there.

Two behaviours, and the difference matters:

- **First write into a routed path in a session -> block** with the owning skills and their own
  descriptions, then allow a later write to that route once its skills are *proven* loaded - see the
  session-proof paragraph below. PreToolUse has no way to add context without stopping the call, and
  stopping is the point: it puts the standard in context *before* the file exists, which costs one tool
  call.
- **A deny pattern -> block every time.** Those are mechanically decidable violations, so they are not
  advice. A repo whose rules are also expressible in its build should enforce them there too - a hook
  matcher is per-tool and never sees `dotnet new`, a shell heredoc or an MCP write.
  A deny rule marked `require_clean` also reads the touched file's existing content. It refuses unrelated
  edits while a violation remains and permits the edit that removes every matched occurrence.

**Session proof, not a one-time nag.** The failure this closes: a plugin can be installed/enabled at
project scope *after* a session already started. The session's own `Skill`-tool registry does not
hot-reload, so `Skill({skill: "<name>"})` returns `Unknown skill` even though the skill's `SKILL.md` is
sitting right there on disk - `skill_description()` below finds it fine, because that is a filesystem
check, not a query of the live session. A hook process cannot ask the running agent's tool registry
whether a name resolves (no such channel exists), so it cannot detect this *before* the agent tries.
What it CAN do is read the session transcript (`transcript_path`, on every hook's stdin payload) after
the fact. A harness exposing `Skill` supplies the `Skill` tool_use/tool_result pair itself: a
harness-authored `is_error: true` on that result is unambiguous proof the name did not resolve *in this
session*, no matter what sits on disk. Codex exposes no such tool: its contract is a successful read of
the applicable filesystem-backed `SKILL.md`, recorded as an `exec` call and its matching result. So a
route no longer trusts a single nag forever - it re-checks the transcript on every write and only lets one
through once every owed skill has its harness's successful proof. A name the transcript shows was invoked
and rejected blocks with a distinct message (restart the session - a stale registry is a session problem,
not a fixable classification) instead of the ordinary "go invoke this" nag. Where no `transcript_path`
is supplied at all (undocumented for some caller), this layer cannot run and the route falls back to the
pre-existing single-nag-then-trust behaviour, so a caller that cannot supply the proof is not wedged shut
by demanding one.

Contract: exit 0 = allow, exit 2 = block with stderr fed back to the agent. Anything unexpected exits
0 - a broken router must not wedge every write, since a build gate is the tier that guarantees.

The same table also answers the question after the fact: `--skills-for <paths>` (or paths on stdin)
prints which skills a set of changed files obliges a reader to load. That is what a review runs, so a
review cannot miss what its author was required to load - the other half of the failure above, where
the follow-up review repeated the identical blind spot and returned clean.

Ships in the ubiquitous `base` plugin, so both harnesses run this one file. `engineering` also packages
it for review-time queries. They share the exit-2 block
contract but NOT the payload: Claude sends a PascalCase tool name and one path under `file_path`,
while Codex sends `apply_patch` with the paths named inside the patch body. Matching only Claude's
shape is not a partial rollout - it is a hook that allows every Codex write while looking wired. A
repo opts in by carrying `.agents/skill-routes.json`; without one the hook exits 0 and does nothing.

A Bash/PowerShell/Codex-shell call is also a candidate write - `cat >>`, `sed -i`, `tee` and a
heredoc all reach a routed path exactly like `Write`/`Edit` do, and matching only the edit-tool
shapes left every one of those unchecked. A shell call is not itself proof of a write, though:
`shell_write_targets()` reads the command text for a short list of named shapes (output redirects,
`tee`, in-place `sed`, `cp`/`mv`, a heredoc supplying the redirected content) and finds nothing for
anything else, deliberately - a `grep`, `cat` or `sed -n` naming a routed path must read as a read,
never a write.
"""

import functools
import hashlib
import json
import os
import re
import shutil
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

from hook_runtime import claim_invocation, own_payload_root

# Skill descriptions carry non-ASCII punctuation, and this text is what the agent acts on.
# Windows defaults these streams to cp1252, which renders it as mojibake.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


ROUTES_FILE = ".agents/skill-routes.json"
# A carved service repo carries no table. The tables and the registry naming which repo gets which one
# ship inside this plugin, beside this file, so adding a service repo is one registry row rather than a
# generated table committed into that repo and drifting there.
SHIPPED_ROUTES_DIR = Path(__file__).resolve().parent.parent / "routes"
REGISTRY_FILE = "registry.json"
# A rename moves a skill between plugins; the qualified name in a route, a plan or a habit does not move
# with it. `.agents/plugins/compatibility.json` already records every such move - it simply had no
# reader, which is how the base: -> engineering: reorganisation made `base:review-lifecycle` resolve
# nowhere and deadlocked the very route that demanded it. Packaged beside this file; one level up in the
# source tree.
ALIAS_CANDIDATES = (
    Path(__file__).resolve().parent / "compatibility.json",
    Path(__file__).resolve().parent.parent / "plugins" / "compatibility.json",
)
REMOTE_URL = re.compile(r'\[remote "origin"\][^\[]*?\burl\s*=\s*([^\r\n]+)', re.DOTALL)
# Lowercased, because the two harnesses do not agree on casing or on names. Claude writes through
# Write/Edit/MultiEdit/NotebookEdit; Codex writes through apply_patch, and matching only Claude's
# vocabulary is how this hook spent its first life doing nothing at all in a Codex session.
# Bash/PowerShell and Codex's shell tool names belong here too - a shell can write a routed path
# exactly like an edit tool can - but a shell call is not itself proof of a write; SHELL_TOOLS
# below decides that from the command text, never from the tool name alone.
CLAUDE_WRITE_TOOLS = {
    "write",
    "edit",
    "multiedit",
    "notebookedit",
    "bash",
    "powershell",
}
CODEX_WRITE_TOOLS = {
    "functions.exec",
    "exec",
    "apply_patch",
    "edit_file",
    "write_file",
    "multi_edit",
    "exec_command",
    "unified_exec",
    "local_shell",
    "shell",
}
WRITE_TOOLS = CLAUDE_WRITE_TOOLS | CODEX_WRITE_TOOLS
# The subset of WRITE_TOOLS that names a shell rather than an edit tool - these carry a `command`
# string, not a `file_path`, so main() routes them through shell_write_targets() instead of
# written_targets().
SHELL_TOOLS = {"bash", "powershell", "exec_command", "unified_exec", "local_shell", "shell"}
PATH_KEYS = ("file_path", "notebook_path", "path", "filepath")
# An apply_patch envelope names its files inside the patch body, so a key lookup alone sees none of them.
PATCH_FILE_TARGET = re.compile(r"\*\*\*\s+(?:Add|Update|Delete)\s+File:\s*([^\r\n]+)", re.IGNORECASE)
PATCH_ADDED_LINE = re.compile(r"^\+(?!\+\+)(.*)$", re.MULTILINE)
PATCH_REMOVED_LINE = re.compile(r"^-(?!--)(.*)$", re.MULTILINE)
PATCH_DELETED_TARGET = re.compile(r"\*\*\*\s+Delete\s+File:\s*([^\r\n]+)", re.IGNORECASE)
PATCH_FILE_BLOCK = re.compile(
    r"^\*\*\*\s+(?:Add|Update|Delete)\s+File:\s*([^\r\n]+)\r?\n"
    r"(.*?)(?=^\*\*\*\s+(?:Add|Update|Delete)\s+File:|^\*\*\*\s+End Patch|\Z)",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)
QUERY_FLAG = "--skills-for"
VERIFY_FLAG = "--verify-install"
DIFF_FLAG = "--check-diff"
ENFORCEMENT_RULES_FILE = "enforcement-rules.json"
EXCEPTIONS_FILE = ".agents/standards-exceptions.json"
# Junction/copy deployment: one flat namespace per harness root.
LINKED_SKILL_ROOTS = {
    "claude": ("skills",),
    "codex": (".agents/skills", ".codex/skills"),
}
@functools.lru_cache(maxsize=2)
def native_install_roots(harness):
    binary = shutil.which(harness)
    if binary is None:
        return ()
    try:
        result = subprocess.run(
            [binary, "plugin", "list", "--json"], capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=8, check=False,
        )
        if result.returncode != 0:
            return ()
        data = json.loads(result.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return ()
    plugins = data.get("installed", []) if harness == "codex" and isinstance(data, dict) else data
    if not isinstance(plugins, list):
        return ()
    roots = []
    for plugin in plugins:
        if not isinstance(plugin, dict) or not plugin.get("enabled"):
            continue
        if harness == "codex":
            marketplace = plugin.get("marketplaceName")
            name = plugin.get("name")
            version = plugin.get("version")
            if not all(isinstance(value, str) for value in (marketplace, name, version)):
                continue
            codex_root = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
            path = codex_root / "plugins" / "cache" / marketplace / name / version
        else:
            path = plugin.get("installPath")
        if isinstance(path, (str, Path)):
            roots.append(Path(path))
    return tuple(roots)


def active_harness(tool_name):
    lowered = tool_name.lower()
    if lowered in CLAUDE_WRITE_TOOLS:
        return "claude"
    if lowered in CODEX_WRITE_TOOLS:
        return "codex"
    return None


def skill_search_dirs(harness):
    """Every directory that may hold `<name>/SKILL.md`, nearest delivery first.

    Ordered own-plugin, then linked roots, then other plugins: the first is exact and needs no globbing,
    and it is the one that answers when this hook is itself running from an installed plugin.
    """
    home = Path.home()

    # The hook's own payload is independent of the harness variable vocabulary. Codex injects
    # PLUGIN_ROOT; Claude injects CLAUDE_PLUGIN_ROOT; a vendored copy resolves beside itself.
    yield own_payload_root(__file__) / "skills"

    configured = os.environ.get("CLAUDE_CONFIG_DIR")
    linked_base = Path(configured) if configured and harness == "claude" else (
        home / ".claude" if harness == "claude" else home
    )
    for relative in LINKED_SKILL_ROOTS[harness]:
        yield linked_base / relative
    for root in native_install_roots(harness):
        yield root / "skills"


def repo_relative(path, cwd):
    """POSIX repo-relative path, so a route regex never has to know about drive letters.

    Resolved against the payload's cwd, not the hook process's - a patch body names its files
    relative to the session, and `Path.resolve()` alone would anchor them wherever python started.
    """
    try:
        p = Path(path)
        if not p.is_absolute():
            p = Path(cwd) / p
        p = p.resolve()
    except OSError:
        return str(path).replace("\\", "/")
    for base in (Path(cwd).resolve(), *Path(cwd).resolve().parents):
        if (base / ROUTES_FILE).is_file() or (base / ".git").exists():
            try:
                return p.relative_to(base).as_posix()
            except ValueError:
                break
    return p.as_posix()


def strings(value):
    """Every string anywhere in the payload - the two harnesses nest their write differently."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def written_content(tool_input):
    """Every string the tool would put into the file, concatenated for pattern matching.

    Only text being ADDED. A deny pattern must never fire on the text a call is deleting - matching a
    patch blob whole would block the very edit that removes the violation.
    """
    parts = [
        tool_input.get("content"),
        tool_input.get("new_string"),
        tool_input.get("new_source"),
    ]
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict):
            parts.append(edit.get("new_string"))
    for blob in strings(tool_input):
        if PATCH_FILE_TARGET.search(blob):
            parts.extend(PATCH_ADDED_LINE.findall(blob))
    return "\n".join(p for p in parts if isinstance(p, str))


def candidate_content(tool_input, existing):
    for key in ("content", "new_source"):
        value = tool_input.get(key)
        if isinstance(value, str):
            return value
    edits = tool_input.get("edits")
    if not isinstance(edits, list):
        edits = [tool_input]
    candidate = existing
    changed = False
    for edit in edits:
        if not isinstance(edit, dict):
            continue
        old = edit.get("old_string")
        new = edit.get("new_string")
        if not isinstance(old, str) or not isinstance(new, str) or old not in candidate:
            continue
        candidate = candidate.replace(old, new) if edit.get("replace_all") else candidate.replace(old, new, 1)
        changed = True
    return candidate if changed else None


# A small set of named shapes a POSIX or PowerShell command line puts bytes into a file with -
# output redirects, `tee`, in-place `sed`, `cp`/`mv` - never a general shell grammar. An
# unrecognised shape is UNDECIDABLE, and undecidable must read as "no write": the alternative
# blocks every `grep`, `cat` or `sed -n` that merely names a routed path, which is the regression
# this module's own docstring warns against. Heredoc bodies are extracted first and excised from
# the text every other regex below scans, so a stray `>` or quote inside the content being written
# can never be mistaken for shell syntax.
_HEREDOC_RE = re.compile(
    r"<<-?\s*['\"]?(?P<delim>\w+)['\"]?(?P<rest>[^\n]*)\n(?P<body>.*?)\n[ \t]*(?P=delim)\s*(?:[\n;&|)]|$)",
    re.DOTALL,
)
# Excludes a numbered/duplicated descriptor (`2>`, `2>&1`, `>&2`) - those redirect a stream, not a
# file, and admitting them would flag every `2>&1` idiom as a write to a path named "&1".
_REDIRECT_RE = re.compile(r"(?<![<>&0-9])(>{1,2})(?!&)\s*([^\s|&;()<>]+)")
_ECHO_RE = re.compile(
    r"\b(?:echo|printf)\b\s+((?:\"[^\"]*\"|'[^']*'|\S+)(?:\s+(?:\"[^\"]*\"|'[^']*'|\S+))*?)"
    r"\s*(>{1,2})\s*([^\s|&;()<>]+)"
)
_TEE_RE = re.compile(r"\btee\b([^\n;|&)]*)")
_SED_RE = re.compile(r"\bsed\b([^\n;|&)]*)")
_CP_MV_RE = re.compile(r"\b(?:cp|mv)\b([^\n;|&)]*)")
_IGNORED_TARGETS = {"/dev/null", "nul", "&1", "&2"}


def _strip_quotes(token):
    if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
        return token[1:-1]
    return token


def _shell_tokens(args):
    """Quote-aware split, or None when the fragment cannot be tokenized (e.g. an unbalanced quote
    left by a heredoc marker the excision above didn't catch). None means undecidable, not empty.

    `posix=False`: POSIX mode treats a bare backslash as an escape character and drops it, which
    silently destroys a Windows-style path (`C:\\repo\\x.cs` -> `C:repox.cs`) - exactly the shape
    `cp`/`mv`/`sed -i`/`tee` targets take on this platform. A leftover surrounding quote is still
    stripped explicitly in `record()`.
    """
    try:
        return shlex.split(args, posix=False)
    except ValueError:
        return None


def shell_write_targets(command):
    """Every path this shell command line actually writes, paired with its best-known added text
    and whether the write fully replaces that path's content (a plain `>` redirect, a heredoc
    feeding one, `tee` without `-a`, or `cp`/`mv`) rather than merely touching it (`>>` append,
    `sed -i`, `tee -a`) - the caller needs this to know whether a `require_clean` violation already
    in the file was actually cleared by this write, the same way it does for the `Write` tool.

    Deliberately narrow - see the module note above. `[]` means no recognised write shape matched,
    which the caller treats exactly like a read: no target, no route, no block.
    """
    if not command:
        return []

    heredoc_bodies = []
    skeleton = []
    cursor = 0
    for match in _HEREDOC_RE.finditer(command):
        skeleton.append(command[cursor:match.start()])
        # The heredoc marker's own line can carry a real redirect after it (`cat <<EOF > file`) -
        # keep that trailing text in the skeleton so the redirect scan below still sees it, rather
        # than excising it along with the body it introduces.
        skeleton.append(match.group("rest"))
        heredoc_bodies.append(match.group("body"))
        cursor = match.end()
    skeleton.append(command[cursor:])
    skeleton = "".join(skeleton)
    heredoc_text = "\n".join(heredoc_bodies)

    writes = {}

    def record(raw_path, text, replaces=False):
        path = _strip_quotes(raw_path) if raw_path else ""
        if not path or path.lower() in _IGNORED_TARGETS:
            return
        existing_text, existing_replaces = writes.get(path, (None, False))
        merged = "\n".join(part for part in (existing_text, text) if part)
        writes[path] = (merged, existing_replaces or replaces)

    for op, target in _REDIRECT_RE.findall(skeleton):
        record(target, heredoc_text, replaces=(op == ">"))
    for text, op, target in _ECHO_RE.findall(skeleton):
        record(target, text, replaces=(op == ">"))

    for args in _TEE_RE.findall(skeleton):
        tokens = _shell_tokens(args)
        if not tokens:
            continue
        appends = any(t in ("-a", "--append") for t in tokens)
        for token in tokens:
            if not token.startswith("-"):
                record(token, None, replaces=not appends)

    for args in _SED_RE.findall(skeleton):
        tokens = _shell_tokens(args)
        if not tokens:
            continue
        in_place = any(
            t == "--in-place" or t.startswith("--in-place=") or re.match(r"^-[a-zA-Z]*i", t)
            for t in tokens
        )
        if not in_place:
            continue
        non_flags = [t for t in tokens if not t.startswith("-")]
        if non_flags:
            record(non_flags[-1], None)

    for args in _CP_MV_RE.findall(skeleton):
        tokens = _shell_tokens(args)
        if not tokens:
            continue
        non_flags = [t for t in tokens if not t.startswith("-")]
        if len(non_flags) >= 2:
            record(non_flags[-1], None, replaces=True)

    return [(path, text, replaces) for path, (text, replaces) in writes.items()]


def removed_content_by_target(tool_input, cwd):
    direct = [tool_input.get("old_string"), tool_input.get("old_source")]
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict):
            direct.append(edit.get("old_string"))
    removed = {}
    targets = written_targets(tool_input)
    if len(targets) == 1:
        rel = repo_relative(targets[0], cwd)
        removed[rel] = "\n".join(part for part in direct if isinstance(part, str))
    for blob in strings(tool_input):
        for target, body in PATCH_FILE_BLOCK.findall(blob):
            rel = repo_relative(target.strip().strip("\"'"), cwd)
            lines = PATCH_REMOVED_LINE.findall(body)
            if lines:
                removed[rel] = "\n".join(filter(None, (removed.get(rel), *lines)))
    return removed


def deleted_targets(tool_input):
    found = set()
    for blob in strings(tool_input):
        for match in PATCH_DELETED_TARGET.findall(blob):
            found.add(match.strip().strip("\"'"))
    return found


def written_targets(tool_input):
    """Every path this call would write, in order and deduplicated.

    Claude names one file per call under a known key; Codex's apply_patch can carry many, named only
    inside the patch body.
    """
    found = []
    for key in PATH_KEYS:
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            found.append(value)
    for blob in strings(tool_input):
        for match in PATCH_FILE_TARGET.findall(blob):
            found.append(match.strip().strip("\"'"))

    ordered, seen = [], set()
    for target in found:
        if target and target not in seen:
            seen.add(target)
            ordered.append(target)
    return ordered


def plugin_of(skills_dir):
    """The plugin a `<...>/skills` directory belongs to, or None for a linked (non-plugin) root.

    Cache layout is `<cache>/<marketplace>/<plugin>/<version>/skills`, so the plugin is two levels up
    from the yielded directory; an own-plugin root is `<plugin-root>/skills`, one level up. A linked
    root is `~/.claude/skills`, which belongs to no plugin - checked by name, since it is the only
    shape without a plugin above it.
    """
    parents = skills_dir.parents
    # <cache>/<marketplace>/<plugin>/<version>/skills - plugin is two above, cache four above.
    if len(parents) >= 4 and parents[3].name == "cache":
        return parents[1].name
    parent = skills_dir.parent
    if parent.name in {".agents", ".claude"}:
        return None
    return parent.name


PROOF_ANCHOR_BYTES = 400


@functools.lru_cache(maxsize=1)
def skill_aliases():
    """Superseded plugin-qualified skill name -> its current name.

    Unreadable or absent resolves to no aliases, never to an error: an alias is a recovery path for a
    name that would otherwise resolve nowhere, so losing it can only restore today's behaviour.
    """
    for candidate in ALIAS_CANDIDATES:
        try:
            data = json.loads(candidate.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        skills = data.get("skills") if isinstance(data, dict) else None
        if not isinstance(skills, dict):
            continue
        return {
            superseded: current
            for superseded, current in skills.items()
            if isinstance(superseded, str) and isinstance(current, str) and superseded != current
        }
    return {}


def resolved_skill(name, harness, following_alias=False):
    """The installed skill file and body, or ``None`` when it cannot be read.

    The FIRST readable copy wins, deliberately: nearest delivery answers, and every later root holds a
    generated copy of the same bytes. A copy with no parsable `description:` is skipped rather than
    accepted, because the description is what decides whether a skill loads at all - accepting a
    malformed first copy would report a correctly-installed skill as NOT INSTALLED.

    A name may be plugin-qualified (`product:persistence`). It has to be able to be: a local roster and
    its generic counterpart deliberately share a skill name, so an unqualified lookup returns whichever
    root is walked first and silently hides the other - the same shadowing that once made
    agents' PERSISTENCE.md resolve to dotagents'. Unqualified still works for a skill with one
    home, which is every utility and every route that names only one side.
    """
    wanted_plugin, _, bare = name.rpartition(":")
    # A descriptionless copy is the last resort, not the answer: the description is what decides whether
    # a skill loads at all, so a malformed nearest copy must not mask a good one behind it. Keeping it as
    # a fallback still reports the skill present, which is honest - it IS installed, just unparsable.
    first = None
    for root in skill_search_dirs(harness):
        if wanted_plugin and plugin_of(root) != wanted_plugin:
            continue
        skill = root / bare / "SKILL.md"
        if not skill.is_file():
            continue
        try:
            text = skill.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        if description_of(text) is None:
            first = first or (skill, text)
            continue
        return skill, text
    if first is not None:
        return first
    # Nothing answers to this name anywhere, which is what a rename looks like from here. One hop only:
    # the alias table is a rename record, not a chain to walk.
    current = None if following_alias else skill_aliases().get(name)
    return resolved_skill(current, harness, True) if current else None


def description_of(body):
    """The one parse of a skill's front-matter description. Both callers below go through it."""
    m = re.search(r"^description:[ \t]*(.+?)(?=^\w+:|^---)", body, re.M | re.S)
    return " ".join(m.group(1).split()) if m else None


def skill_description(name, harness):
    """The skill's own description, so the rule text has exactly one home."""
    resolved = resolved_skill(name, harness)
    return None if resolved is None else description_of(resolved[1])


def transcript_skill_outcomes(transcript_path, codex_skills=()):
    """Bare skill name -> whether the transcript proves it resolved this session, or None if unreadable.

    Scans the session's own JSONL transcript for `Skill` tool_use blocks and the `tool_result` each
    one's `id` pairs with. A result carrying `is_error: true` is the harness itself saying the name did
    not resolve - not a guess, not a re-derivation, the exact fact this hook cannot otherwise observe.
    A later success overrides an earlier failure (the registry can recover mid-session, e.g. after the
    user restarts and resumes); a later failure never downgrades an earlier proven success.

    Codex has no `Skill` tool in this environment. Its skill contract instead requires the agent to read
    the applicable filesystem-backed `SKILL.md`. A real Codex transcript records that as an `exec`
    `custom_tool_call` plus its paired `custom_tool_call_output`, nested under a `response_item` payload.
    That proves a skill only when a SUCCESSFUL call names some delivery root's copy of that skill AND its
    output carries an anchor of the real body. A path mention, an error result, or a foreign body is not
    proof.

    Two things the proof deliberately does NOT require, because demanding either blocks a correct read:

    - **The exact path the router resolved.** The same skill exists at several real paths on a provisioned
      machine (plugin cache, `~/.claude/skills`, `~/.agents/skills`, a repo's own `.agents/skills`), all
      generated copies of one authored file. Matching on the trailing `skills/<name>/SKILL.md` segment
      means the copy the agent could most easily find counts.
    - **The whole body verbatim.** Codex truncates `exec` output (`max_output_tokens`), and the biggest
      bodies are the most-loaded skills. So the head OR the tail of the body is the anchor, plus enough
      matched bytes that a two-line excerpt cannot pass.

    Returns `None` - not `{}` - when the transcript itself could not be read at all, so the caller can
    tell "proof is unavailable, fall back" apart from "proof was checked and found nothing yet".
    """
    if not transcript_path:
        return None

    def normalized_path(value):
        # Codex records JavaScript source, so a Windows path inside an exec command still has its
        # backslashes escaped (`C:\\\\...`) after the outer JSON is decoded. Collapse both forms before
        # comparing it with the filesystem path the router resolved.
        return re.sub(r"/+", "/", value.replace("\\", "/")).lower()

    outcomes = {}
    pending = {}
    pending_codex = {}
    def anchors(body):
        """Head and tail slices of the real body: one of them survives truncation from either end."""
        normalized = body.replace("\r\n", "\n")
        span = min(len(normalized), PROOF_ANCHOR_BYTES)
        return normalized[:span], normalized[-span:] if span else ""

    codex_proofs = [
        # Keyed on the trailing delivery segment, not the resolved absolute path - see the docstring.
        (name, "/skills/%s/skill.md" % name.lower(), anchors(body))
        for name, _, body in codex_skills
    ]
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                payload = entry.get("payload") or {}
                if entry.get("type") == "response_item" and isinstance(payload, dict):
                    payload_type = payload.get("type")
                    if payload_type == "custom_tool_call" and payload.get("name") == "exec":
                        call_id = payload.get("call_id")
                        call_input = payload.get("input")
                        if call_id and isinstance(call_input, str):
                            pending_codex[call_id] = normalized_path(call_input)
                    elif payload_type == "custom_tool_call_output":
                        call_id = payload.get("call_id")
                        call_input = pending_codex.pop(call_id, None) if call_id else None
                        output = payload.get("output") or []
                        output_text = "".join(
                            block.get("text", "") for block in output if isinstance(block, dict)
                        )
                        # This is Codex's successful `functions.exec` result shape. Do not treat a
                        # command which merely mentioned a path, or one which failed, as a skill load.
                        if call_input and output_text.startswith("Script completed\n"):
                            output_text = output_text.replace("\r\n", "\n")
                            for name, segment, (head, tail) in codex_proofs:
                                if segment not in call_input:
                                    continue
                                if head and (head in output_text or tail in output_text):
                                    outcomes[name] = True
                content = (entry.get("message") or {}).get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    block_type = block.get("type")
                    if block_type == "tool_use" and block.get("name") == "Skill":
                        tool_id = block.get("id")
                        name = (block.get("input") or {}).get("skill")
                        if tool_id and isinstance(name, str) and name:
                            pending[tool_id] = name.rpartition(":")[2] or name
                    elif block_type == "tool_result":
                        tool_id = block.get("tool_use_id")
                        name = pending.pop(tool_id, None) if tool_id else None
                        if name is None:
                            continue
                        succeeded = not bool(block.get("is_error"))
                        if outcomes.get(name) is not True:
                            outcomes[name] = succeeded
    except OSError:
        return None
    return outcomes


def state_path(session_id):
    key = hashlib.sha256((session_id or "nosession").encode()).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"skill-router-{key}.json"


def load_seen(session_id):
    try:
        return set(json.loads(state_path(session_id).read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return set()


def save_seen(session_id, seen):
    try:
        state_path(session_id).write_text(json.dumps(sorted(seen)), encoding="utf-8")
    except OSError:
        pass  # a router that cannot persist should nag, never crash


def find_repo_root(cwd):
    """The repo's own table wins wherever one exists; otherwise the git root, which the registry keys on."""
    base = Path(cwd).resolve()
    for candidate in (base, *base.parents):
        if (candidate / ROUTES_FILE).is_file():
            return candidate
    for candidate in (base, *base.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def git_common_dir(root):
    """The real .git directory, following the `gitdir:` pointer a worktree checkout carries instead."""
    marker = root / ".git"
    if marker.is_dir():
        return marker
    try:
        pointer = marker.read_text(encoding="utf-8")
    except OSError:
        return None
    _, _, target = pointer.partition("gitdir:")
    target = target.strip()
    if not target:
        return None
    worktree_dir = Path(target)
    if not worktree_dir.is_absolute():
        worktree_dir = (root / worktree_dir).resolve()
    common = worktree_dir / "commondir"
    if common.is_file():
        try:
            relative = common.read_text(encoding="utf-8").strip()
        except OSError:
            return None
        return (worktree_dir / relative).resolve()
    return worktree_dir


def repo_identity(root):
    """`owner/name` lowercased from the origin remote - what the registry keys on. None when unresolvable."""
    common = git_common_dir(root)
    if common is None:
        return None
    config = common / "config"
    try:
        text = config.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    match = REMOTE_URL.search(text)
    if not match:
        return None
    url = match.group(1).strip()
    url = re.sub(r"\.git$", "", url)
    url = re.sub(r"^[^@]+@[^:/]+[:/]", "", url)
    url = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.-]*://[^/]+/", "", url)
    parts = [part for part in url.replace("\\", "/").split("/") if part]
    if len(parts) < 2:
        return None
    return "/".join(parts[-2:]).lower()


class RoutesUnusable(Exception):
    """The repo opted into routing and the table cannot be read. Never silently ignored."""


def registry_routes(root):
    """The shipped table this repo is registered for. None when the repo is not registered."""
    registry_path = SHIPPED_ROUTES_DIR / REGISTRY_FILE
    if not registry_path.is_file():
        return None
    identity = repo_identity(root)
    if identity is None:
        return None
    try:
        registered = (json.loads(registry_path.read_text(encoding="utf-8")) or {}).get("repos") or {}
    except (OSError, ValueError) as error:
        raise RoutesUnusable(f"the shipped {REGISTRY_FILE} could not be read: {error}") from error
    kind = registered.get(identity)
    if kind is None:
        return None
    table = SHIPPED_ROUTES_DIR / f"{kind}.json"
    try:
        parsed = json.loads(table.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise RoutesUnusable(
            f"{identity} is registered as kind {kind!r} but the shipped {kind}.json is unusable: {error}"
        ) from error
    routes = parsed.get("routes")
    if not isinstance(routes, list):
        raise RoutesUnusable(f"the shipped {kind}.json has no usable `routes` list.")
    return routes


def load_routes(root):
    """No table and not registered -> None. Present but unusable, either tier -> raises.

    Failing open on a malformed table is the ENF1 failure exactly: enforcement that is inert while
    looking wired. A repo that created this file asked for routing, so a typo in it is a loud stop.
    """
    path = root / ROUTES_FILE
    if not path.is_file():
        return registry_routes(root)
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise RoutesUnusable(f"{ROUTES_FILE} exists but could not be read: {error}") from error
    except ValueError as error:
        raise RoutesUnusable(f"{ROUTES_FILE} exists but is not valid JSON: {error}") from error
    routes = parsed.get("routes")
    if routes is None:
        raise RoutesUnusable(f"{ROUTES_FILE} has no `routes` key.")
    if not isinstance(routes, list):
        raise RoutesUnusable(f"{ROUTES_FILE} `routes` must be a list, got {type(routes).__name__}.")
    return routes


def matching_routes(routes, rel, content):
    """One matcher for both callers, so a review resolves a path exactly as the write-time block did."""
    for route in routes:
        pattern = route.get("path")
        if not pattern or not re.search(pattern, rel):
            continue
        needle = route.get("content_requires")
        if needle and not re.search(needle, content):
            continue
        yield route


def deny_hits(route, rel, content):
    for rule in route.get("deny") or []:
        pattern = rule.get("pattern")
        if pattern and re.search(pattern, content):
            yield rel, rule.get("reason", "")


def enforcement_rules(root):
    candidates = [root / ".agents", own_payload_root(__file__)]
    seen = set()
    for root in candidates:
        path = root / ENFORCEMENT_RULES_FILE
        if path in seen:
            continue
        seen.add(path)
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            continue
        rules = value.get("rules") if isinstance(value, dict) else None
        if isinstance(rules, list):
            return rules
    return None


def enforcement_exceptions(root):
    path = root / EXCEPTIONS_FILE
    if not path.is_file():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as error:
        raise RoutesUnusable(f"{EXCEPTIONS_FILE} is unusable: {error}") from error
    exceptions = value.get("exceptions") if isinstance(value, dict) else None
    if not isinstance(exceptions, list):
        raise RoutesUnusable(f"{EXCEPTIONS_FILE} has no usable `exceptions` list.")
    return exceptions


def excepted(rule, rel, exceptions):
    for exception in exceptions:
        if not isinstance(exception, dict) or exception.get("rule") != rule.get("id"):
            continue
        evidence = exception.get("evidence")
        pattern = exception.get("path")
        if isinstance(evidence, str) and len(evidence.strip()) >= 10 and pattern:
            try:
                if re.search(pattern, rel):
                    return True
            except re.error:
                continue
    return False


CSHARP_METHOD = re.compile(
    r"(?m)^\s*(?:(?:public|internal|protected|private|static|virtual|override|abstract|sealed|async|partial|new)\s+)+"
    r"(?:[A-Za-z_][A-Za-z0-9_<>,.?\[\]]*\s+)+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*"
    r"\((?P<parameters>[^)]*)\)"
)


def method_counts(content):
    counts = {}
    for match in CSHARP_METHOD.finditer(content or ""):
        name = match.group("name")
        counts[name] = counts.get(name, 0) + 1
    return counts


def enforcement_hits(
    rules,
    root,
    rel,
    content,
    exceptions,
    existing_text=None,
    candidate_text=None,
    removed_text="",
):
    for rule in rules:
        if not isinstance(rule, dict) or not rule.get("paths") or not re.search(rule["paths"], rel):
            continue
        if excepted(rule, rel, exceptions):
            continue
        kind = rule.get("kind")
        pattern = rule.get("pattern")
        hit = bool(content) if kind == "path-only" else bool(pattern and re.search(pattern, content))
        if hit and kind == "csharp-provider-overload":
            existing = existing_text
            if existing is None:
                try:
                    existing = (root / rel).read_text(encoding="utf-8", errors="replace")
                except OSError:
                    existing = ""
            existing_counts = method_counts(existing)
            provider_methods = {
                match.group("name")
                for match in CSHARP_METHOD.finditer(candidate_text if candidate_text is not None else content)
                if pattern and re.search(pattern, match.group(0))
            }
            if candidate_text is not None:
                candidate_counts = method_counts(candidate_text)
                hit = any(
                    existing_counts.get(name, 0) > 0
                    and candidate_counts.get(name, 0) > existing_counts.get(name, 0)
                    for name in provider_methods
                )
            else:
                removed_counts = method_counts(removed_text)
                hit = any(
                    existing_counts.get(name, 0) > removed_counts.get(name, 0)
                    for name in provider_methods
                )
        if hit:
            yield rule


def diff_additions(root, revision, mode="working"):
    command = ["git", "-c", f"core.excludesFile={os.devnull}", "diff", "--no-ext-diff", "--unified=0"]
    if mode == "index":
        command.append("--cached")
    command.append(revision)
    if mode == "head":
        command.append("HEAD")
    command.append("--")
    completed = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RoutesUnusable(completed.stderr.strip() or f"git diff {revision} failed")
    additions = {}
    current = None
    for line in completed.stdout.splitlines():
        if line.startswith("+++ "):
            target = line[4:]
            current = None if target == "/dev/null" else re.sub(r"^b/", "", target)
            continue
        if current and line.startswith("+") and not line.startswith("+++"):
            additions.setdefault(current, []).append(line[1:])
    if mode != "working":
        return {path: "\n".join(lines) for path, lines in additions.items()}
    untracked = subprocess.run(
        ["git", "-c", f"core.excludesFile={os.devnull}", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if untracked.returncode != 0:
        raise RoutesUnusable("git ls-files for untracked paths failed")
    for raw in untracked.stdout.split(b"\0"):
        if not raw:
            continue
        rel = raw.decode("utf-8", errors="replace").replace("\\", "/")
        try:
            additions[rel] = (root / rel).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
    return {path: "\n".join(lines) for path, lines in additions.items()}


def revision_text(root, revision, rel):
    completed = subprocess.run(
        ["git", "-c", f"core.excludesFile={os.devnull}", "show", f"{revision}:{rel}"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return completed.stdout if completed.returncode == 0 else ""


def index_text(root, rel):
    completed = subprocess.run(
        ["git", "-c", f"core.excludesFile={os.devnull}", "show", f":{rel}"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return completed.stdout if completed.returncode == 0 else ""


def check_diff(argv):
    index = argv.index(DIFF_FLAG)
    revision = argv[index + 1] if len(argv) > index + 1 else "HEAD"
    root = find_repo_root(os.getcwd())
    if root is None:
        print("not inside a Git repository", file=sys.stderr)
        return 2
    rules = enforcement_rules(root) or []
    try:
        exceptions = enforcement_exceptions(root)
        additions = diff_additions(root, revision)
    except RoutesUnusable as error:
        print(f"STANDARDS ENFORCEMENT - {error}", file=sys.stderr)
        return 2
    violations = []
    for rel, content in additions.items():
        existing = revision_text(root, revision, rel)
        try:
            candidate = (root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            candidate = None
        for rule in enforcement_hits(
            rules, root, rel, content, exceptions, existing, candidate_text=candidate
        ):
            violations.append({
                "path": rel,
                "rule": rule.get("id"),
                "source": rule.get("source"),
                "reason": rule.get("reason", ""),
            })
    if "--json" in argv:
        json.dump({"revision": revision, "violations": violations}, sys.stdout, indent=2)
        sys.stdout.write("\n")
    elif violations:
        for violation in violations:
            print(
                f"DENY PATTERN HIT [{violation['rule']}] - {violation['path']}\n"
                f"  {violation['reason']}\n  Source: {violation['source']}"
            )
    else:
        print(f"standards enforcement passed for diff from {revision}")
    return 2 if violations else 0


def unresolved_existing_deny_hits(route, rel, content, removed, replaces, deletes):
    if replaces or deletes:
        return
    folded_removed = removed.casefold()
    for rule in route.get("deny") or []:
        if not rule.get("require_clean"):
            continue
        pattern = rule.get("pattern")
        if not pattern:
            continue
        removed_counts = {}
        for match in re.finditer(pattern, content):
            value = match.group(0).casefold()
            removed_counts[value] = removed_counts.get(value, 0) + 1
        for value, count in removed_counts.items():
            if folded_removed.count(value) < count:
                yield rel, rule.get("reason", "")


def query(argv):
    """`--skills-for <paths>` / paths on stdin -> the skills those files oblige a reader to load."""
    paths = [arg for arg in argv if not arg.startswith("-")]
    if not paths:
        paths = [line.strip() for line in sys.stdin.read().splitlines() if line.strip()]

    cwd = os.getcwd()
    root = find_repo_root(cwd)
    try:
        routes = load_routes(root) if root else None
    except RoutesUnusable as error:
        print(f"SKILL ROUTER - {error}")
        print("The table exists, so routing was asked for. Fix it; do not review against a dead table.")
        return 2
    if not routes:
        print(f"no readable {ROUTES_FILE} above {cwd} - no skill is owed")
        return 0

    owed, violations = {}, []
    for given in paths:
        rel = repo_relative(given, cwd)
        try:
            content = (root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            content = ""  # deleted or unreadable: the path still routes, the content gates cannot
        for route in matching_routes(routes, rel, content):
            for name in route.get("skills") or []:
                files = owed.setdefault(name, [])
                if rel not in files:
                    files.append(rel)
            violations.extend(deny_hits(route, rel, content))

    if "--json" in argv:
        json.dump({"skills": owed, "violations": violations}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    if not owed:
        print(f"no routed paths among the {len(paths)} given - no skill is owed")
    else:
        print("skill-routes.json owns these changed paths. Load each skill before judging its files:")
        for name in sorted(owed):
            files = sorted(set(owed[name]))
            print(f"\n  * {name}  ({len(files)} file(s))")
            for rel in files:
                print(f"      {rel}")
    for rel, reason in violations:
        print(f"\nDENY PATTERN HIT - a decidable violation in the tree, report it:\n  {rel}\n      {reason}")
    return 0


def missing_routed_skills(routes, harness):
    names = {name for route in routes for name in route.get("skills") or []}
    return sorted(name for name in names if skill_description(name, harness) is None)


def verify_install(argv):
    index = argv.index(VERIFY_FLAG)
    harness = argv[index + 1].lower() if len(argv) > index + 1 else ""
    if harness not in {"claude", "codex"}:
        print(f"usage: {VERIFY_FLAG} <claude|codex>")
        return 2

    cwd = os.getcwd()
    root = find_repo_root(cwd)
    try:
        routes = load_routes(root) if root else None
    except RoutesUnusable as error:
        print(f"SKILL ROUTER - {error}")
        return 2
    if routes is None:
        print(f"no readable {ROUTES_FILE} above {cwd} - no installation to verify")
        return 2

    names = sorted({name for route in routes for name in route.get("skills") or []})
    missing = [name for name in names if skill_description(name, harness) is None]
    if missing:
        print(f"{harness} is missing {len(missing)} of {len(names)} routed skill(s):")
        for name in missing:
            print(f"  {name}")
        return 2

    print(f"{harness} resolves all {len(names)} routed skill(s) from {ROUTES_FILE}")
    return 0


def main():
    if DIFF_FLAG in sys.argv[1:]:
        sys.exit(check_diff(sys.argv[1:]))
    if QUERY_FLAG in sys.argv[1:]:
        sys.exit(query(sys.argv[1:]))
    if VERIFY_FLAG in sys.argv[1:]:
        sys.exit(verify_install(sys.argv[1:]))

    try:
        data = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)

    tool_name = data.get("tool_name")
    if not isinstance(tool_name, str):
        sys.exit(0)
    harness = active_harness(tool_name)
    if harness is None:
        sys.exit(0)

    tool_input = data.get("tool_input") or {}
    is_shell = tool_name.lower() in SHELL_TOOLS
    if is_shell:
        # A shell call is a candidate, not a write: `written_targets` finds nothing here (there is
        # no `file_path`), so only a recognised write shape in the command text produces a target -
        # a bare `grep`/`cat`/`sed -n` naming a routed path falls straight through to exit 0 below.
        shell_writes = shell_write_targets("\n".join(strings(tool_input)))
        targets = [path for path, _, _ in shell_writes]
    else:
        shell_writes = []
        targets = written_targets(tool_input)
    cwd = data.get("cwd") or os.getcwd()
    root = find_repo_root(cwd)
    if root is None:
        sys.exit(0)
    try:
        routes = load_routes(root)
    except RoutesUnusable as error:
        sys.stderr.write(
            "SKILL ROUTER - blocked, the routing table itself is broken:"
            "\n\n"
            f"  {error}"
            "\n\n"
            "This repo opted into routing by carrying the file, so a table that cannot be read is a"
            " stop, not a silent pass - otherwise every write from here on is unenforced and looks"
            " fine.\n"
        )
        sys.exit(2)
    if not routes:
        sys.exit(0)

    missing_install = missing_routed_skills(routes, harness)
    if missing_install:
        sys.stderr.write(
            "SKILL ROUTER - blocked, this repository requires unavailable standards:\n\n"
            + "\n".join(f"  {name}" for name in missing_install)
            + f"\n\nInstall or enable the owning plugin(s) for {harness}, then start a new "
            "session. This tool call was NOT run.\n"
        )
        sys.exit(2)
    if not targets:
        sys.exit(0)

    rules = enforcement_rules(root) or []
    try:
        exceptions = enforcement_exceptions(root)
    except RoutesUnusable as error:
        sys.stderr.write(f"SKILL ROUTER - blocked, {error}\n")
        sys.exit(2)

    content = (
        "\n".join(text for _, text, _ in shell_writes if text) if is_shell else written_content(tool_input)
    )
    removed_by_rel = removed_content_by_target(tool_input, cwd)
    deleted = {repo_relative(target, cwd) for target in deleted_targets(tool_input)}
    replaces = tool_name.casefold() in {"write", "write_file"}
    # A shell write that fully replaces its target's content (a plain `>`/heredoc redirect, `tee`
    # without `-a`, `cp`/`mv`) proves a `require_clean` violation cleared the same way the `Write`
    # tool does; `removed_by_rel` never carries that signal for a shell call, since there is no
    # `old_string`/`edits` to diff. Without this, once a routed file had one require_clean hit, no
    # shell write could ever satisfy it again - not even the write that overwrote the file clean.
    replaces_by_rel = (
        {repo_relative(path, cwd): full for path, _, full in shell_writes} if is_shell else {}
    )

    for target in targets:
        rel = repo_relative(target, cwd)
        try:
            existing = (root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            existing = ""
        candidate = candidate_content(tool_input, existing)
        for rule in enforcement_hits(
            rules,
            root,
            rel,
            content,
            exceptions,
            existing_text=existing,
            candidate_text=candidate,
            removed_text=removed_by_rel.get(rel, ""),
        ):
            sys.stderr.write(
                "SKILL ROUTER - blocked, this is a mechanically decidable rule violation:\n\n"
                f"  {rel}\n  [{rule.get('id')}] {rule.get('reason', '')}\n"
                f"  Source: {rule.get('source')}\n\n"
                f"Read the {rule.get('skill', 'owning')} skill and replace the violating shape. "
                "The file was NOT written."
            )
            sys.exit(2)

    matched = []
    for target in targets:
        rel = repo_relative(target, cwd)
        for route in matching_routes(routes, rel, content):
            matched.append((rel, route))
    if not matched:
        sys.exit(0)

    if not claim_invocation(data, "skill-router"):
        sys.exit(0)

    # Deny patterns first: a decidable violation blocks every time, not once per session.
    for rel, route in matched:
        for _, reason in deny_hits(route, rel, content):
            sys.stderr.write(
                "SKILL ROUTER - blocked, this is a rule violation, not a reminder:\n\n"
                f"  {rel}\n  {reason}\n\n"
                f"Read the {', '.join(route.get('skills') or []) or 'owning'} skill and fix the "
                "classification before writing this file. The file was NOT written."
            )
            sys.exit(2)
        try:
            existing = (root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            existing = ""
        for _, reason in unresolved_existing_deny_hits(
            route,
            rel,
            existing,
            removed_by_rel.get(rel, ""),
            replaces_by_rel.get(rel, replaces),
            rel in deleted,
        ):
            sys.stderr.write(
                "SKILL ROUTER - blocked, this file still contains a pre-launch rule violation:\n\n"
                f"  {rel}\n  {reason}\n\n"
                "Remove the existing violation in this edit before making any unrelated change. "
                "The file was NOT written."
            )
            sys.exit(2)

    session = data.get("session_id")
    seen = load_seen(session)
    pending = []
    for rel, route in matched:
        key = route.get("path")
        if key in seen:
            continue
        pending.append((rel, route))

    if not pending:
        sys.exit(0)

    descriptions = {}
    resolved_paths = {}
    codex_skills = []
    missing = set()
    for _, route in pending:
        for name in route.get("skills") or []:
            if name not in descriptions:
                resolved = resolved_skill(name, harness)
                if resolved is None:
                    descriptions[name] = None
                else:
                    skill, body = resolved
                    descriptions[name] = description_of(body)
                    resolved_paths[name] = skill
                    if harness == "codex" and descriptions[name] is not None:
                        codex_skills.append((name.rpartition(":")[2] or name, skill, body))
            if descriptions[name] is None:
                missing.add(name)

    # Proof, not a filesystem check alone: a name present on disk can still be `Unknown skill` in THIS
    # session's own registry (a plugin enabled after the session started never hot-reloads into it).
    # `missing` alone already forces the permanent block below, so the transcript is only worth reading
    # when every name at least resolves on disk. No transcript -> outcomes is None -> reproduce the
    # pre-existing single-nag-then-trust behaviour exactly, so a caller that cannot supply the proof is
    # not wedged shut by demanding one.
    outcomes = None if missing else transcript_skill_outcomes(
        data.get("transcript_path"), codex_skills
    )
    fallback = not missing and outcomes is None
    rejected, unproven = set(), set()
    if not missing and outcomes is not None:
        for name in descriptions:
            outcome = outcomes.get(name.rpartition(":")[2] or name)
            if outcome is False:
                rejected.add(name)
            elif outcome is not True:
                unproven.add(name)

    if not missing and not fallback and not rejected and not unproven:
        for _, route in pending:
            seen.add(route.get("path"))
        save_seen(session, seen)
        sys.exit(0)

    lines = ["SKILL ROUTER - a standard owns this path, and it is not proven loaded this session:", ""]
    for rel, route in pending:
        lines += [f"  {rel}", ""]
        for name in route.get("skills") or []:
            desc = descriptions[name]
            lines.append(f"  * {name}")
            if name in missing:
                lines.append(
                    f"      NOT INSTALLED FOR {harness.upper()} - no SKILL.md is available to the "
                    "active harness. A route pointing at a missing skill is a deployment fault, not "
                    "a reason to proceed."
                )
            elif name in rejected:
                lines.append(
                    "      REJECTED THIS SESSION - its file is present, but invoking it returned an "
                    "error (e.g. `Unknown skill`), so this session's own registry does not resolve it "
                    "- typically a plugin enabled or updated after the session started, which does not "
                    "hot-reload. Restart the session (exit and relaunch); if it still fails afterward, "
                    "this is a genuine bug, report it. Do not read the standard's file directly and "
                    "code from precedent as a substitute for actually invoking it."
                    if harness != "codex" else
                    "      REJECTED THIS SESSION - the read of its file did not succeed. Re-run it and "
                    "check the command completed."
                )
            elif desc:
                lines.append(f"      {desc}")
                # Codex exposes no `Skill` tool, so "invoke it" names an action it cannot take. Its
                # contract is a completed read of the file, which it can only do if told which one.
                if harness == "codex" and name in resolved_paths:
                    lines.append(f"      READ THIS WHOLE FILE: {resolved_paths[name]}")
        if route.get("note"):
            lines.append(f"      NOTE: {route['note']}")
    if missing:
        lines += [
            "",
            f"Install or enable the missing skill(s) for {harness}, then start a new session. The file "
            "was NOT written. This route remains blocked on every attempt until every owning skill "
            "is available.",
        ]
    elif rejected:
        lines += [
            "",
            "The file was NOT written. This route stays blocked on every attempt until every owning "
            "skill records a successful invocation in this session's transcript.",
        ]
    elif fallback:
        # No transcript to prove anything either way - reproduce the pre-existing behaviour verbatim
        # rather than demanding proof a caller was never able to supply.
        for _, route in pending:
            seen.add(route.get("path"))
        save_seen(session, seen)
        lines += [
            "",
            "Invoke the skill(s) above, then repeat this write. The file was NOT written. This fires "
            "once per path pattern per session, so it will not interrupt you again for this route.",
        ]
    else:
        lines += [
            "",
            (
                "Read each file named above in full with one command that completes, then repeat this "
                "write. The file was NOT written. This route stays blocked on every attempt until this "
                "session's transcript records that read for every owning skill."
                if harness == "codex" else
                "Invoke the skill(s) above, then repeat this write. The file was NOT written. This route "
                "stays blocked on every attempt until a successful invocation of every owning skill is "
                "recorded in this session's transcript - not merely attempted once."
            ),
        ]
    sys.stderr.write("\n".join(lines))
    sys.exit(2)


if __name__ == "__main__":
    main()
