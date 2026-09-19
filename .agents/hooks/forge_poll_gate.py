r"""PreToolUse hook: no repeated model-driven forge polling for an unchanged PR/head.

The recurring token waste this blocks: an agent waiting on a merge queue or a CI
run calls ``gh pr checks`` / ``gh pr view --json statusCheckRollup`` / ``gh run
list`` / ``gh run view`` from one model turn after another, each call a fresh
model round-trip that observes the same state and makes no progress. The
``merging`` / ``merge`` / ``remote-validation`` / ``persistent-*`` skills already
say to park on one silent capped monitor and never wake the model at the poll
interval, but prose was ignored; a hook cannot be.

What is allowed, so ordinary work is never in the way:

* The FIRST forge read for a given repo + PR/head/run identity. One-off
  inspection and failure triage are first reads.
* One authoritative read after an externally-initiated turn — the user typing
  again, a background monitor completing, a ``Monitor`` / scheduled wake firing.
  Detected from the transcript: an allowed read follows a turn the model did not
  start itself.
* One authoritative read when the observed state actually moved (a check flipped
  to ``fail``, the queue admitted the PR, ``MERGED``). The hook confirms this by
  making one authoritative read of its own before it blocks.
* Any command that is not forge polling: ``gh run view --log`` and friends
  (failure diagnosis), ``gh pr diff``, ``gh pr view`` for title/body, ``gh pr
  comment``, every non-``gh`` command.
* Exactly one invocation of ``.agents/workflows/workflow_ops.py monitor`` per
  identity. It persists the exact binding and emits only material transitions or
  a terminal result; a second concurrent monitor for that identity is blocked.

What is blocked: a second/third/... ``gh`` poll for the same identity, from a
later model turn, with no intervening wake and no state change. It fails CLOSED —
if the hook cannot prove the state moved it still blocks, because the whole point
is to stop the loop. The message names the monitor workflow to use instead.

Wired for BOTH harnesses. Claude's matcher is ``Bash|PowerShell``; Codex's is
``exec_command|unified_exec|local_shell|shell`` — its observed and candidate
unified-exec names. ``command`` arriving as an argv list (``["bash","-lc",...]``),
or under ``cmd`` / ``input`` / ``action.command``, is unwrapped; a Codex payload
is told apart by its ``turn_id``. Unlike ``merge_review_gate.py`` this gate fails
OPEN on any shape it does not recognise, so covering a name that turns out wrong
costs nothing, where a wrong guess in the merge gate would block a real merge.

A repo opts in by carrying ``.agents/forge-poll-gate.json``; without one the hook
exits 0 and claims no jurisdiction. A present-but-unreadable table is a loud stop
for a poll command only — never for an unrelated shell call.

Contract: exit 0 = allow; exit 2 = block (stderr is fed back to the agent).
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from hook_runtime import claim_invocation

# This message is what the agent acts on, and Windows defaults these streams to cp1252.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

CONFIG_FILE = ".agents/forge-poll-gate.json"
HOOK_NAME = "forge-poll-gate"

# Lowercased. A shell tool not named here cannot be wired to this gate, because a matcher the hook
# ignores is enforcement that is inert while looking wired. `bash`/`powershell` are Claude's; the
# Codex names are the observed and candidate unified-exec spellings, handled so the gate is ready
# the day Codex's PreToolUse shell payload is confirmed.
SHELL_TOOLS = {"bash", "powershell", "shell", "exec_command", "unified_exec", "local_shell"}

# Transcript-less fallback: a repeat this long after the previous read is treated as a fresh human
# turn rather than a poll loop. A genuine loop re-fires in seconds, never minutes.
IDLE_RESUME_SECONDS = 180
# A registered monitor older than this is treated as finished/abandoned rather than still running.
MONITOR_TTL_SECONDS = 60 * 60
STATE_RETENTION_SECONDS = 7 * 24 * 60 * 60
AUTHORITATIVE_READ_TIMEOUT = 8


class ConfigUnusable(Exception):
    """The repo opted into the gate and the table cannot be read. Never silently ignored."""


# --------------------------------------------------------------------------- command extraction


def _shell_script_from_list(parts):
    """A shell tool invoked as ``["bash", "-lc", "<script>"]`` carries its script in the last arg."""
    cleaned = [str(p) for p in parts if isinstance(p, (str, int, float))]
    if not cleaned:
        return None
    if len(cleaned) >= 2 and re.fullmatch(r"-[a-z]*c", cleaned[1]) and Path(cleaned[0]).name in (
        "bash",
        "sh",
        "zsh",
        "dash",
        "pwsh",
        "powershell",
    ):
        return cleaned[-1]
    return " ".join(cleaned)


def extract_command(tool_name, tool_input):
    """The shell text a Claude Bash/PowerShell or Codex exec/unified-exec call would run, or None."""
    if not isinstance(tool_input, dict):
        return None
    if str(tool_name).lower() not in SHELL_TOOLS:
        return None
    for key in ("command", "cmd", "script", "input"):
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(value, list):
            joined = _shell_script_from_list(value)
            if joined and joined.strip():
                return joined
    action = tool_input.get("action")
    if isinstance(action, dict):
        value = action.get("command") or action.get("cmd")
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(value, list):
            joined = _shell_script_from_list(value)
            if joined and joined.strip():
                return joined
    return None


def is_codex_invocation(data):
    """Codex hook payloads carry a turn id; Claude hook payloads do not."""
    return "turn_id" in data or "turnId" in data


# --------------------------------------------------------------------------- classification


_LOG_FLAG_RE = re.compile(r"--log(?:-failed)?\b")
_POLL_PATTERNS = (
    re.compile(r"\bgh\s+pr\s+checks\b"),
    re.compile(r"\bgh\s+pr\s+status\b"),
    re.compile(r"\bgh\s+run\s+list\b"),
    re.compile(r"\bgh\s+run\s+watch\b"),
)
_PR_VIEW_RE = re.compile(r"\bgh\s+pr\s+view\b")
_RUN_VIEW_RE = re.compile(r"\bgh\s+run\s+view\b")
_STATUS_FIELD_RE = re.compile(
    r"\b(statusCheckRollup|mergeStateStatus|mergeable|reviewDecision|state)\b"
)
_API_POLL_RE = re.compile(
    r"\bgh\s+api\b.*?(check-runs|check-suites|/commits/[^\s'\"]+/status|actions/runs)", re.DOTALL
)
_GRAPHQL_POLL_RE = re.compile(
    r"\bgh\s+api\s+graphql\b.*?(mergeQueueEntry|statusCheckRollup|checkSuites)", re.DOTALL
)
_LOOP_RE = re.compile(r"\b(while|until|for)\b")
_SLEEP_RE = re.compile(r"\bsleep\b")
_GH_FORGE_RE = re.compile(r"\bgh\s+(pr|run|api)\b")
_MONITOR_RE = re.compile(
    r"^\s*(?:python(?:3)?(?:\s+-B)?\s+)?\"?(?:\.[\\/])?\.agents[\\/]workflows[\\/]workflow_ops\.py\"?(?=\s).*\bmonitor\b.*$",
    re.DOTALL,
)
_SHELL_CONTROL_RE = re.compile(r"[;&`\r\n]|\||\$\(|[<>]\s*\(")


def is_monitor_shape(command):
    return bool(_MONITOR_RE.fullmatch(command)) and not _SHELL_CONTROL_RE.search(command)


def is_forbidden_monitor_shape(command):
    return bool(
        re.search(r"\bgh\s+run\s+watch\b", command)
        or (_LOOP_RE.search(command) and _SLEEP_RE.search(command) and _GH_FORGE_RE.search(command))
    )


def is_forge_poll(command, extra_patterns=()):
    """True when the command's purpose is to observe PR / check / run status."""
    if _LOG_FLAG_RE.search(command):
        return False  # `gh run view --log*` is failure diagnosis, never gated
    for pattern in _POLL_PATTERNS:
        if pattern.search(command):
            return True
    if _PR_VIEW_RE.search(command):
        # A bare `gh pr view <n>` prints the check rollup; `--json title,body` does not.
        if "--json" in command and not _STATUS_FIELD_RE.search(command):
            return False
        return True
    if _RUN_VIEW_RE.search(command):
        return True
    if _API_POLL_RE.search(command) or _GRAPHQL_POLL_RE.search(command):
        return True
    for pattern in extra_patterns:
        if pattern.search(command):
            return True
    return False


_PR_NUM_RE = re.compile(r"\bgh\s+pr\s+(?:checks|view|status|merge)\s+(\d+)")
_GRAPHQL_PR_RE = re.compile(r"pullRequest\s*\(\s*number\s*:\s*(\d+)")
_RUN_ID_RE = re.compile(r"\bgh\s+run\s+(?:view|watch)\s+(\d+)")


def identity_key(command, repo_slug, branch):
    """Stable identity for the thing being polled: repo + PR number / run id / branch / forge."""
    slug = repo_slug or "local"
    match = _PR_NUM_RE.search(command) or _GRAPHQL_PR_RE.search(command)
    if match:
        return f"{slug}#pr{match.group(1)}"
    match = _RUN_ID_RE.search(command)
    if match:
        return f"{slug}#run{match.group(1)}"
    if re.search(r"\bgh\s+pr\b", command):
        return f"{slug}#pr:{branch or 'current'}"
    if re.search(r"\bgh\s+run\s+list\b", command):
        return f"{slug}#runs"
    return f"{slug}#forge"


# --------------------------------------------------------------------------- environment reads


_SLUG_RE = re.compile(r"[:/]?([^/:]+)/([^/:]+?)(?:\.git)?/?$")
_CD_RE = re.compile(r"(?:^|[;&|]|&&)\s*(?:cd|pushd)\s+((?:\"[^\"]*\")|(?:'[^']*')|(?:[^\s;&|]+))")


def command_cwd(command, data):
    """The directory the command runs in: the last cd/pushd before the first gh, else payload cwd."""
    head = command
    marker = re.search(r"\bgh\b", command)
    if marker:
        head = command[: marker.start()]
    target = None
    for match in _CD_RE.finditer(head):
        target = match.group(1)
        if len(target) >= 2 and target[0] == target[-1] and target[0] in "\"'":
            target = target[1:-1]
    if target:
        return target
    for key in ("cwd", "workdir", "workspace", "workspaceRoot", "project_dir", "projectDir"):
        value = data.get(key)
        if value:
            return value
    return "."


def _run(args, cwd):
    # Resolve through PATH/PATHEXT so `gh`/`git` are found on native Windows, where CreateProcess
    # does not add `.cmd`/`.exe` to a bare program name the way the shells do.
    resolved = shutil.which(args[0])
    if resolved is None:
        raise FileNotFoundError(args[0])
    return subprocess.run(
        [resolved, *args[1:]], capture_output=True, text=True, cwd=cwd,
        timeout=AUTHORITATIVE_READ_TIMEOUT,
    )


def repo_slug(cwd):
    try:
        out = _run(["git", "remote", "get-url", "origin"], cwd)
        if out.returncode != 0:
            return None
        match = _SLUG_RE.search(out.stdout.strip())
        return (match.group(1) + "/" + match.group(2)).lower() if match else None
    except (OSError, subprocess.SubprocessError):
        return None


def current_branch(cwd):
    try:
        out = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd)
        return out.stdout.strip() if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def authoritative_signature(identity, command, cwd):
    """One direct forge read the hook makes itself, to tell an unchanged loop from a real move."""
    try:
        if "#run" in identity:
            run_id = identity.rsplit("run", 1)[-1]
            out = _run(
                ["gh", "run", "view", run_id, "--json", "status,conclusion", "--jq",
                 '.status+"/"+(.conclusion // "")'],
                cwd,
            )
        elif "#runs" in identity or "#forge" in identity:
            out = _run(
                ["gh", "run", "list", "-L", "8", "--json", "databaseId,status,conclusion", "--jq",
                 '[.[]|(.databaseId|tostring)+":"+.status+"/"+(.conclusion // "")]|join(",")'],
                cwd,
            )
        else:
            pr = identity.split("#pr", 1)[-1]
            args = ["gh", "pr", "view"]
            if pr.isdigit():
                args.append(pr)
            args += ["--json", "state,mergeStateStatus,statusCheckRollup", "--jq",
                     '[.state,.mergeStateStatus,'
                     '([.statusCheckRollup[]?|((.name // .context))+":"'
                     '+((.conclusion // .state // .status) // "")]|sort|join(","))]|join("|")']
            out = _run(args, cwd)
        if out.returncode != 0:
            return None
        return out.stdout.strip() or "∅"
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


_TOOL_RESULT_TYPES = {"tool_result", "function_call_output", "tool_call_output", "local_shell_call_output"}
_EXTERNAL_NON_USER_TYPES = {"system", "notification", "progress", "summary", "reasoning_summary"}


def _is_external_turn(entry):
    """Whether a transcript entry is a turn the model did not start itself.

    Claude uses ``type`` (``user``/``assistant``/``system``); Codex rollout entries carry ``role``
    and message/response-item types. In both, a plain user message counts and a tool result the
    model's own call produced does not.
    """
    role = entry.get("role") or (entry.get("message") or {}).get("role")
    entry_type = entry.get("type")
    if role == "assistant" or entry_type == "assistant":
        return False
    if role == "user" or entry_type == "user" or entry_type == "message":
        message = entry.get("message") if isinstance(entry.get("message"), dict) else entry
        content = message.get("content")
        if isinstance(content, list) and content and all(
            isinstance(part, dict) and part.get("type") in _TOOL_RESULT_TYPES for part in content
        ):
            return False
        return role == "user" or entry_type == "user" or bool(content)
    return entry_type in _EXTERNAL_NON_USER_TYPES


def latest_external_turn_marker(transcript_path):
    """Id of the most recent turn the model did not start itself.

    A human message, a system notification, a completed background task. During a model-driven poll
    loop the transcript only grows by assistant messages and tool results the model's own calls
    produced, so this marker is constant; any real wake moves it.
    """
    if not transcript_path:
        return None
    try:
        lines = Path(transcript_path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    marker = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if not isinstance(entry, dict) or entry.get("isSidechain") or not _is_external_turn(entry):
            continue
        marker = entry.get("uuid") or entry.get("id") or entry.get("timestamp") or hashlib.sha256(
            line.encode("utf-8", "replace")
        ).hexdigest()
    return marker


# --------------------------------------------------------------------------- state store


def _session_key(data, cwd):
    """Claude sends ``session_id``; Codex payloads may carry a conversation/thread id or neither.

    Fall back to the resolved checkout path — one agent owns one worktree, so that still keeps two
    concurrent agents' poll state apart.
    """
    for key in ("session_id", "sessionId", "conversation_id", "conversationId", "thread_id"):
        value = data.get(key)
        if value:
            return str(value)
    try:
        return f"cwd:{Path(cwd).resolve()}"
    except (OSError, TypeError, ValueError):
        return "no-session"


def _state_dir():
    override = os.environ.get("FORGE_POLL_GATE_STATE_DIR")
    directory = Path(override) if override else Path(tempfile.gettempdir()) / "agents-forge-poll"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _state_path(directory, session_id, identity):
    key = hashlib.sha256(f"{session_id}\0{identity}".encode("utf-8")).hexdigest()
    return directory / f"{key}.json"


def _prune(directory, keep):
    cutoff = time.time() - STATE_RETENTION_SECONDS
    for path in directory.glob("*.json"):
        if path == keep:
            continue
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
        except OSError:
            continue


def load_state(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def save_state(path, state):
    try:
        path.write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        pass


# --------------------------------------------------------------------------- decision


MONITOR_WORKFLOW = (
    "Do not poll the forge again from a model turn. Start `.agents/workflows/workflow_ops.py "
    "monitor` once with the exact repository, head, and run or PR identity through the host's "
    "background notification primitive. Reconnect to its persisted monitor identity after a "
    "restart. It emits only a material transition, terminal result, query error, or bounded timeout."
)


def decide(command, identity, state, *, now, marker, monitor_shape, signature_fn):
    """Pure gate: ('allow'|'block', new_state|None, message).

    ``signature_fn`` makes one authoritative forge read; it is invoked at most once per event and
    only when its answer matters — establishing a baseline on an allowed read, or confirming a
    repeat's state before blocking it.
    """
    if monitor_shape:
        if state and state.get("monitor") and now - state["monitor"] < MONITOR_TTL_SECONDS:
            return (
                "block",
                None,
                f"FORGE POLL GATE: a background monitor already owns {identity} "
                f"(started {int(now - state['monitor'])}s ago). Run exactly one. Wait for it "
                f"to wake you, then make one authoritative read.",
            )
        new_state = dict(state or {})
        new_state.update(monitor=now, ts=now, marker=marker)
        new_state.setdefault("sig", None)
        return ("allow", new_state, None)

    def allowed(_why):
        merged = {k: v for k, v in (state or {}).items() if k != "monitor"}
        merged.update(ts=now, marker=marker, sig=signature_fn())
        return ("allow", merged, None)

    if state is None:
        return allowed("first read of this identity")

    if state.get("monitor"):
        return allowed("first read after a monitor was registered — the post-wake read")

    if marker is not None and marker != state.get("marker"):
        return allowed("externally-initiated turn — user, monitor completion, scheduled wake")

    if marker is None and now - state.get("ts", 0) > IDLE_RESUME_SECONDS:
        return allowed("idle long enough to be a fresh human turn")

    current = signature_fn()
    if current is not None and state.get("sig") is not None and current != state["sig"]:
        return allowed("observed state moved since the last read")

    frozen = {k: v for k, v in state.items() if k != "monitor"}
    frozen["sig"] = current if current is not None else state.get("sig")
    return (
        "block",
        frozen,
        f"FORGE POLL GATE: repeated forge read of {identity} with no state change since the "
        f"last read and no wake in between. {MONITOR_WORKFLOW}",
    )


# --------------------------------------------------------------------------- config / jurisdiction


def find_config(cwd):
    try:
        base = Path(cwd).resolve()
    except OSError:
        return None
    for candidate in (base, *base.parents):
        if (candidate / CONFIG_FILE).is_file():
            return candidate / CONFIG_FILE
    return None


def extra_poll_patterns(config_path):
    try:
        parsed = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ConfigUnusable(f"{CONFIG_FILE} exists but could not be read: {error}") from error
    declared = parsed.get("extra_poll_patterns", [])
    if not isinstance(declared, list):
        raise ConfigUnusable(f"{CONFIG_FILE} `extra_poll_patterns` must be a list.")
    compiled = []
    for entry in declared:
        try:
            compiled.append(re.compile(entry))
        except (TypeError, re.error) as error:
            raise ConfigUnusable(
                f"{CONFIG_FILE} `extra_poll_patterns` entry {entry!r}: {error}"
            ) from error
    return compiled


def block(reason):
    sys.stderr.write(reason)
    sys.exit(2)


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)

    command = extract_command(data.get("tool_name", ""), data.get("tool_input") or {})
    if not command:
        sys.exit(0)

    cwd = command_cwd(command, data)
    config_path = find_config(cwd)
    if config_path is None:
        sys.exit(0)

    monitor_shape = is_monitor_shape(command)
    forbidden_monitor = is_forbidden_monitor_shape(command)
    try:
        extra = extra_poll_patterns(config_path)
    except ConfigUnusable as error:
        if monitor_shape or forbidden_monitor or is_forge_poll(command):
            block(f"FORGE POLL GATE: {error}")
        sys.exit(0)

    if forbidden_monitor:
        block(
            "FORGE POLL GATE: direct `gh run watch` and ad hoc sleeping forge loops are not "
            f"reconnect-safe. {MONITOR_WORKFLOW}"
        )

    if not monitor_shape and not is_forge_poll(command, extra):
        sys.exit(0)

    if not claim_invocation(data, HOOK_NAME):
        sys.exit(0)

    session_id = _session_key(data, cwd)
    slug = repo_slug(cwd)
    needs_branch = bool(re.search(r"\bgh\s+pr\b", command)) and not (
        _PR_NUM_RE.search(command) or _GRAPHQL_PR_RE.search(command)
    )
    branch = current_branch(cwd) if needs_branch else None
    identity = identity_key(command, slug, branch)

    directory = _state_dir()
    path = _state_path(directory, session_id, identity)
    _prune(directory, path)
    state = load_state(path)
    marker = latest_external_turn_marker(data.get("transcript_path") or data.get("transcriptPath"))

    cached = []

    def signature_fn():
        if not cached:
            cached.append(authoritative_signature(identity, command, cwd))
        return cached[0]

    verdict, new_state, message = decide(
        command,
        identity,
        state,
        now=time.time(),
        marker=marker,
        monitor_shape=monitor_shape,
        signature_fn=signature_fn,
    )
    if new_state is not None:
        save_state(path, new_state)
    if verdict == "block":
        block(message)
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001 - a broken poll gate must never wedge an unrelated command
        sys.exit(0)
