r"""Enforce merge Step 5 cleanup after a `gh pr merge`: record an obligation, nag Codex
with a cooldown after grace, hard-block Claude's Stop once GitHub confirms the merge,
and surface a reminder to any session whose checkout still owns it. `--clear <worktree>`
is the deliberate-retention escape.
"""

import os
import sys


def has_obligations():
    root = os.environ.get("AGENT_STATE_DIRECTORY") or os.path.join(os.path.expanduser("~"), ".agents-state")
    try:
        with os.scandir(os.path.join(root, "merge-cleanup", "obligations")) as entries:
            return any(entry.name.endswith(".json") for entry in entries)
    except OSError:
        return False


STDIN = None
if __name__ == "__main__" and sys.argv[1:2] != ["--clear"]:
    try:
        STDIN = sys.stdin.buffer.read()
        idle = b"merge" not in STDIN.lower() and not has_obligations()
    except Exception:
        idle = False
    if idle:
        sys.exit(0)

import hashlib
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path


STATE_DIRECTORY_ENV = "AGENT_STATE_DIRECTORY"
GRACE_ENV = "AGENT_MERGE_CLEANUP_GRACE_SECONDS"
NAG_COOLDOWN_ENV = "AGENT_MERGE_CLEANUP_NAG_COOLDOWN_SECONDS"

DIRECT_GRACE_SECONDS = 120
QUEUED_GRACE_SECONDS = 1800
NAG_COOLDOWN_SECONDS = 600
TRANSFER_REARM_SECONDS = 3600
RECONCILE_MAX_AGE_SECONDS = 7 * 24 * 60 * 60
GIT_TIMEOUT_SECONDS = 5

CLEANUP_PROOF_RELATIVE = "engineering/workflow/merge/scripts/cleanup_proof.py"

RESULT_KEYS = ("tool_response", "tool_result", "tool_output", "tool_error", "error")
TEXT_FIELDS = ("stdout", "stderr", "output", "content", "error", "message")

EXEMPT_GIT_VERBS = (
    "status", "fetch", "worktree", "branch", "checkout", "switch", "pull", "push",
    "rev-parse", "log", "diff", "show", "add", "commit", "merge", "remote",
    "ls-files", "ls-remote",
)
EXEMPT_GH_VERBS = (
    r"pr\s+(?:view|checks|list|create|edit|ready|comment|merge)",
    r"run\s+(?:list|view|watch|rerun)",
)
EXEMPT_PY_SCRIPTS = (
    "workflow_ops.py", "cleanup_proof.py", "agent_cli.py", "transfer.py", "merge_cleanup_gate.py",
)
EXEMPT_PS1_SCRIPTS = (
    "worktrees.ps1", "peer-cli.ps1", "close-tab.ps1", "launch-codex.ps1",
    "launch-claude.ps1", "finish.ps1", "finish_reaper.ps1",
)

NEUTRAL_SEGMENT_RE = re.compile(
    r"\A(?:Select-String|Select-Object|Where-Object|ForEach-Object|Sort-Object|Measure-Object|Out-String"
    r"|Out-Null|ConvertFrom-Json|ConvertTo-Json|Format-\w+|Write-Output|Write-Host|echo|head|tail|grep"
    r"|jq|sort|wc|cat|popd|Pop-Location|Set-Location|Push-Location|cd|pushd)\b",
    re.IGNORECASE,
)
GIT_SEGMENT_RE = re.compile(
    r'\Agit(?:\s+-C\s+(?:"[^"]*"|\S+))?\s+(?:' + "|".join(EXEMPT_GIT_VERBS) + r')\b',
    re.IGNORECASE,
)
GH_SEGMENT_RE = re.compile(r'\Agh\s+(?:' + "|".join(EXEMPT_GH_VERBS) + r')\b', re.IGNORECASE)
PY_SEGMENT_RE = re.compile(
    r'\A\S*?\bpython3?(?:\.exe)?\b.*?\b(?:' + "|".join(re.escape(s) for s in EXEMPT_PY_SCRIPTS) + r')\b',
    re.IGNORECASE,
)
PS1_SEGMENT_RE = re.compile(
    r'\A\S*?\b(?:powershell|pwsh)(?:\.exe)?\b.*?\b(?:' + "|".join(re.escape(s) for s in EXEMPT_PS1_SCRIPTS) + r')\b',
    re.IGNORECASE,
)

DIRECT_SCRIPT_SEGMENT_RE = re.compile(
    r"""\A(?:&\s*)?['"]?[^\s'"]*?\b(?:"""
    + "|".join(re.escape(s) for s in EXEMPT_PY_SCRIPTS + EXEMPT_PS1_SCRIPTS)
    + r""")['"]?(?:\s|\Z)""",
    re.IGNORECASE,
)

PUSHD_RE = re.compile(r"""\bpushd\s+(?:"([^"]+)"|'([^']+)'|(\S+))""", re.IGNORECASE)
LAUNCHER_RE = re.compile(
    r"launch-codex\.ps1|launch-claude\.ps1|agent_cli\.py|transfer\.py", re.IGNORECASE
)


def segment_is_exempt(segment):
    segment = segment.strip()
    if not segment:
        return True
    return bool(
        GIT_SEGMENT_RE.match(segment)
        or GH_SEGMENT_RE.match(segment)
        or PY_SEGMENT_RE.match(segment)
        or PS1_SEGMENT_RE.match(segment)
        or DIRECT_SCRIPT_SEGMENT_RE.match(segment)
    )


def shell_segments(command):
    segments, current, quote, index = [], [], None, 0
    while index < len(command):
        char = command[index]
        if quote:
            current.append(char)
            if char == quote:
                quote = None
        elif char in "'\"":
            quote = char
            current.append(char)
        elif command.startswith("&&", index) or command.startswith("||", index):
            segments.append("".join(current))
            current = []
            index += 1
        elif char in ";|":
            segments.append("".join(current))
            current = []
        else:
            current.append(char)
        index += 1
    segments.append("".join(current))
    return [segment.strip() for segment in segments if segment.strip()]


def segment_is_neutral(segment):
    return ">" not in segment and NEUTRAL_SEGMENT_RE.match(segment) is not None


def command_is_exempt(command):
    segments = shell_segments(command)
    meaningful = [segment for segment in segments if not segment_is_neutral(segment)]
    if not meaningful:
        return not segments
    return all(segment_is_exempt(segment) for segment in meaningful)


MESSAGE = (
    "MERGE CLEANUP GATE: `gh pr merge` for PR #{pr} ({branch}) ran from {worktree} at {time} "
    "and merge Step 5 cleanup has not completed.\n"
    "- Not merged yet? Keep monitoring — `python .agents/workflows/workflow_ops.py ... "
    "monitor --kind pr --id {pr} --head {head}`, `gh pr view/checks` and `gh run list/view/watch` "
    "are never blocked.\n"
    "- Merged? Finish Step 6 and the report, then from inside {worktree} run `python -B {cleanup_proof}` "
    "and `powershell.exe -NoProfile -ExecutionPolicy Bypass -File <machine:peer-cli skill-directory>"
    "/scripts/finish.ps1`, exactly, with no arguments: it closes this CLI and removes the worktree. "
    "Elsewhere, follow `engineering:merge` Step 5.\n"
    "- Deliberately retaining the worktree (preserve verdict, closed-unmerged PR)? "
    "`python \"{hook_path}\" --clear \"{worktree}\"`.\n"
    "This repeats every 10 minutes until cleanup completes, a handoff launcher transfers it, "
    "or it is cleared."
)


def state_directory():
    configured = os.environ.get(STATE_DIRECTORY_ENV)
    return Path(configured) if configured else Path.home() / ".agents-state"


def obligations_directory():
    return state_directory() / "merge-cleanup" / "obligations"


def obligation_path(worktree):
    digest = hashlib.sha256(Path(worktree).as_posix().encode("utf-8")).hexdigest()
    return obligations_directory() / f"{digest}.json"


def iter_obligation_paths():
    try:
        return list(obligations_directory().glob("*.json"))
    except OSError:
        return []


def load_obligation(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def save_obligation(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, sort_keys=True)
            handle.write("\n")
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def git(cwd, *args, timeout=GIT_TIMEOUT_SECONDS):
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def worktree_still_exists(obligation):
    worktree = obligation.get("worktree")
    return isinstance(worktree, str) and Path(worktree).is_dir()


def grace_seconds(obligation):
    override = os.environ.get(GRACE_ENV)
    if override:
        try:
            return float(override)
        except ValueError:
            pass
    return QUEUED_GRACE_SECONDS if obligation.get("merge_mode") == "queued" else DIRECT_GRACE_SECONDS


def nag_cooldown_seconds():
    override = os.environ.get(NAG_COOLDOWN_ENV)
    if override:
        try:
            return float(override)
        except ValueError:
            pass
    return NAG_COOLDOWN_SECONDS


def normalize_path_text(value):
    return str(value).replace("\\", "/").rstrip("/").casefold()


def under_or_equal(candidate, root):
    candidate = normalize_path_text(candidate)
    root = normalize_path_text(root)
    return candidate == root or candidate.startswith(root + "/")


def cwd_matches(cwd, obligation):
    if not cwd:
        return False
    for key in ("worktree", "primary"):
        root = obligation.get(key)
        if root and under_or_equal(cwd, root):
            return True
    return False


def resolve_cleanup_proof_path(codex):
    from hook_runtime import own_payload_root

    root = own_payload_root(__file__)
    skill_root = "codex-skills" if codex else "skills"
    host_entry = root / skill_root / "merge" / "scripts" / "cleanup_proof.py"
    if host_entry.is_file():
        return host_entry.as_posix()
    for candidate in (root / ".agents" / CLEANUP_PROOF_RELATIVE, root / CLEANUP_PROOF_RELATIVE):
        if candidate.is_file():
            return candidate.as_posix()
    return None


def deny_message(obligation, codex):
    cleanup_proof = resolve_cleanup_proof_path(codex) or "engineering:merge Step 5's cleanup_proof.py"
    recorded_at = obligation.get("recorded_at")
    stamp = (
        time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(recorded_at))
        if isinstance(recorded_at, (int, float)) else "an earlier time"
    )
    return MESSAGE.format(
        pr=obligation.get("pr") or "?",
        branch=obligation.get("branch") or "?",
        head=obligation.get("head") or "<head>",
        worktree=obligation.get("worktree"),
        time=stamp,
        cleanup_proof=cleanup_proof,
        hook_path=str(Path(__file__).resolve()),
    )


def pushd_target(command):
    position = command.lower().find("gh pr " "merge")
    prefix = command if position < 0 else command[:position]
    matches = list(PUSHD_RE.finditer(prefix))
    if not matches:
        return None
    last = matches[-1]
    return last.group(1) or last.group(2) or last.group(3)


def record_obligation(command, data):
    from merge_review_gate import canonical_merge_target_dir, merge_target_dir, normalize_slug, pr_number

    target = canonical_merge_target_dir(command) or pushd_target(command) or merge_target_dir(command, data)
    try:
        worktree = Path(target).resolve()
    except OSError:
        return
    if not worktree.is_dir():
        return
    branch = git(worktree, "rev-parse", "--abbrev-ref", "HEAD")
    head = git(worktree, "rev-parse", "HEAD")
    common_dir_raw = git(worktree, "rev-parse", "--path-format=absolute", "--git-common-dir")
    common_dir = primary = None
    if common_dir_raw:
        try:
            common_path = Path(common_dir_raw).resolve()
        except OSError:
            common_path = None
        if common_path is not None:
            common_dir = str(common_path)
            primary = str(common_path.parent) if common_path.name == ".git" else str(common_path)
    origin_url = git(worktree, "remote", "get-url", "origin")
    session = data.get("session_id") or data.get("sessionId")
    save_obligation(obligation_path(worktree), {
        "session_id": session,
        "worktree": str(worktree),
        "primary": primary,
        "common_dir": common_dir,
        "branch": branch,
        "head": head,
        "pr": pr_number(command),
        "repo": normalize_slug(origin_url) if origin_url else None,
        "recorded_at": time.time(),
        "confirmed_merged": False,
        "merge_mode": "queued" if "--auto" in command else "direct",
        "nagged_at": None,
        "transferred_at": None,
        "transferred_by": None,
    })


def stamp_transfer(command, data):
    if not LAUNCHER_RE.search(command):
        return
    session = data.get("session_id") or data.get("sessionId")
    if not session:
        return
    for path in iter_obligation_paths():
        obligation = load_obligation(path)
        if obligation is None:
            continue
        if obligation.get("transferred_at") is None and obligation.get("session_id") == session:
            obligation["transferred_at"] = time.time()
            obligation["transferred_by"] = session
            save_obligation(path, obligation)


def evaluate_codex_obligation(obligation, session, cwd, now):
    if not worktree_still_exists(obligation):
        return None
    transferred_at = obligation.get("transferred_at")
    if transferred_at is None:
        if obligation.get("session_id") != session:
            return None
        recorded_at = obligation.get("recorded_at")
        if not isinstance(recorded_at, (int, float)):
            return None
        if now - recorded_at < grace_seconds(obligation):
            return None
    else:
        if not isinstance(transferred_at, (int, float)) or now - transferred_at < TRANSFER_REARM_SECONDS:
            return None
        if not cwd_matches(cwd, obligation):
            return None
    nagged_at = obligation.get("nagged_at")
    if isinstance(nagged_at, (int, float)) and now - nagged_at < nag_cooldown_seconds():
        return None
    return deny_message(obligation, True)


def codex_enforce(command, data):
    paths = iter_obligation_paths()
    if not paths or command_is_exempt(command):
        return 0
    session = data.get("session_id") or data.get("sessionId")
    cwd = data.get("cwd")
    now = time.time()
    for path in paths:
        obligation = load_obligation(path)
        if obligation is None:
            continue
        message = evaluate_codex_obligation(obligation, session, cwd, now)
        if message is not None:
            obligation["nagged_at"] = now
            save_obligation(path, obligation)
            sys.stderr.write(message)
            return 2
    return 0


def handle_pretooluse(data):
    from git_auth_scope_gate import extract_command
    from merge_review_gate import is_codex_invocation, is_merge_enable

    command = extract_command(data.get("tool_name", ""), data.get("tool_input") or {})
    if not command:
        return 0
    if is_merge_enable(command):
        record_obligation(command, data)
        return 0
    stamp_transfer(command, data)
    if not is_codex_invocation(data):
        return 0
    return codex_enforce(command, data)


def collect_text(value, parts):
    if isinstance(value, str):
        parts.append(value)
    elif isinstance(value, dict):
        fields = [value[field] for field in TEXT_FIELDS if isinstance(value.get(field), str)]
        if fields:
            parts.extend(fields)
            return
        try:
            parts.append(json.dumps(value))
        except TypeError:
            parts.append(str(value))
    elif isinstance(value, list):
        for item in value:
            collect_text(item, parts)
    elif value is not None:
        parts.append(str(value))


def response_text(data):
    parts = []
    for key in RESULT_KEYS:
        collect_text(data.get(key), parts)
    return "\n".join(parts)


MERGED_OUTPUT_RE = re.compile(
    r"merged pull request\s+(?:[\w.-]+/[\w.-]+)?#?(?P<pr>\d+)", re.IGNORECASE
)
MERGE_STATE_RE = re.compile(r'\\?"state\\?"\s*:\s*\\?"merged\\?"', re.IGNORECASE)
QUEUED_OUTPUT_RE = re.compile(r"merge queue|automatically merged|auto-merge", re.IGNORECASE)
MONITOR_COMMAND_RE = re.compile(
    r"--id\s+(?P<monitor_pr>\d+)"
    r"|\bpr\s+view\s+(?P<view_pr>\d+)\b"
    r"|\bpr\s+checks\s+(?P<checks_pr>\d+)\b",
    re.IGNORECASE,
)


def confirm_obligation_for_pr(pr):
    for path in iter_obligation_paths():
        obligation = load_obligation(path)
        if obligation is not None and obligation.get("pr") == pr:
            obligation["confirmed_merged"] = True
            save_obligation(path, obligation)


def merge_is_final_segment(command):
    segments = shell_segments(command)
    return bool(segments) and re.match(r"gh\s+pr\s+merge\b", segments[-1], re.IGNORECASE) is not None


def confirm_obligation_for_target(command, data):
    from merge_review_gate import canonical_merge_target_dir, merge_target_dir

    target = canonical_merge_target_dir(command) or pushd_target(command) or merge_target_dir(command, data)
    try:
        path = obligation_path(Path(target).resolve())
    except OSError:
        return
    obligation = load_obligation(path)
    if obligation is not None:
        obligation["confirmed_merged"] = True
        save_obligation(path, obligation)


def confirm_owning_session_obligations(session, pr):
    for path in iter_obligation_paths():
        obligation = load_obligation(path)
        if obligation is None or obligation.get("session_id") != session:
            continue
        recorded_pr = obligation.get("pr")
        if pr is not None and recorded_pr is not None and recorded_pr != pr:
            continue
        obligation["confirmed_merged"] = True
        save_obligation(path, obligation)


def handle_posttooluse(data):
    from git_auth_scope_gate import extract_command
    from merge_review_gate import is_merge_enable

    command = extract_command(data.get("tool_name", ""), data.get("tool_input") or {})
    if not command:
        return
    text = response_text(data)

    if is_merge_enable(command):
        if "--auto" in command or QUEUED_OUTPUT_RE.search(text) or not merge_is_final_segment(command):
            return
        confirm_obligation_for_target(command, data)
        return

    match = MONITOR_COMMAND_RE.search(command)
    if not match or not MERGE_STATE_RE.search(text):
        return
    session = data.get("session_id") or data.get("sessionId")
    if not session:
        return
    pr = match.group("monitor_pr") or match.group("view_pr") or match.group("checks_pr")
    confirm_owning_session_obligations(session, pr)


def handle_posttoolusefailure(data):
    from git_auth_scope_gate import extract_command
    from merge_review_gate import is_merge_enable

    command = extract_command(data.get("tool_name", ""), data.get("tool_input") or {})
    if not command or not is_merge_enable(command):
        return
    match = MERGED_OUTPUT_RE.search(response_text(data))
    if match:
        confirm_obligation_for_pr(match.group("pr"))


def handle_stop(data):
    from merge_review_gate import is_codex_invocation

    if data.get("stop_hook_active") or data.get("stopHookActive"):
        return
    session = data.get("session_id") or data.get("sessionId")
    if not session:
        return
    codex = is_codex_invocation(data)
    for path in iter_obligation_paths():
        obligation = load_obligation(path)
        if (
            obligation is not None
            and obligation.get("session_id") == session
            and obligation.get("confirmed_merged")
            and worktree_still_exists(obligation)
        ):
            json.dump({"decision": "block", "reason": deny_message(obligation, codex)}, sys.stdout)
            sys.stdout.write("\n")
            return


def reminder_line(obligation):
    return (
        f"merge-cleanup: PR #{obligation.get('pr') or '?'} ({obligation.get('branch') or '?'}) "
        f"at {obligation.get('worktree')} still needs merge Step 5 cleanup "
        f"(`python \"{Path(__file__).resolve()}\" --clear \"{obligation.get('worktree')}\"` to clear)."
    )


def emit(event, context):
    print(json.dumps({
        "hookSpecificOutput": {"hookEventName": event, "additionalContext": context}
    }, ensure_ascii=True))


def handle_reminder(event, data):
    obligations = [
        obligation for obligation in (load_obligation(path) for path in iter_obligation_paths())
        if obligation is not None and worktree_still_exists(obligation)
    ]
    if not obligations:
        return
    cwd = data.get("cwd")
    if not cwd:
        return
    matched = [obligation for obligation in obligations if cwd_matches(cwd, obligation)]
    if not matched:
        common_dir = git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
        if common_dir:
            try:
                common_dir = str(Path(common_dir).resolve())
            except OSError:
                common_dir = None
        if common_dir:
            matched = [o for o in obligations if o.get("common_dir") == common_dir]
    if matched:
        emit(event, "\n".join(reminder_line(obligation) for obligation in matched))


def branch_ref_missing(primary, branch):
    try:
        result = subprocess.run(
            ["git", "-C", str(primary), "show-ref", "--verify", "--quiet", "refs/heads/" + branch],
            capture_output=True, text=True, timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 1


def should_reconcile(obligation, now):
    worktree = obligation.get("worktree")
    if not isinstance(worktree, str) or not Path(worktree).is_dir():
        return True
    recorded_at = obligation.get("recorded_at")
    if isinstance(recorded_at, (int, float)) and now - recorded_at > RECONCILE_MAX_AGE_SECONDS:
        return True
    primary, branch = obligation.get("primary"), obligation.get("branch")
    if primary and branch and branch != "HEAD" and branch_ref_missing(primary, branch):
        return True
    return False


def reconcile():
    paths = iter_obligation_paths()
    if not paths:
        return
    now = time.time()
    for path in paths:
        obligation = load_obligation(path)
        if obligation is None or should_reconcile(obligation, now):
            try:
                path.unlink()
            except OSError:
                pass


def cli_clear(args):
    if not args:
        print("merge-cleanup-gate: --clear requires a worktree path.", file=sys.stderr)
        return 1
    try:
        target = Path(args[0]).resolve()
    except OSError:
        print(f"merge-cleanup-gate: cannot resolve {args[0]}", file=sys.stderr)
        return 1
    try:
        obligation_path(target).unlink()
    except FileNotFoundError:
        print(f"merge-cleanup-gate: no obligation recorded for {target}")
        return 0
    except OSError as error:
        print(f"merge-cleanup-gate: cannot clear {target}: {error}", file=sys.stderr)
        return 1
    print(f"merge-cleanup-gate: cleared the obligation for {target}")
    return 0


def dispatch(argv):
    if argv and argv[0] == "--clear":
        return cli_clear(argv[1:])
    raw = STDIN if STDIN is not None else sys.stdin.buffer.read()
    try:
        data = json.loads(raw.decode("utf-8-sig")) if raw.strip() else {}
    except (UnicodeError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    event = data.get("hook_event_name") or data.get("hookEventName") or ""
    reconcile()
    if event == "PreToolUse":
        return handle_pretooluse(data)
    if event == "PostToolUse":
        handle_posttooluse(data)
    elif event == "PostToolUseFailure":
        handle_posttoolusefailure(data)
    elif event == "Stop":
        handle_stop(data)
    elif event in ("UserPromptSubmit", "SessionStart"):
        handle_reminder(event, data)
    return 0


def main():
    # Load-bearing: the Codex adapter maps any non-0/2 exit to a deny, so an internal fault here
    # must still return a neutral 0 rather than silently blocking every tool call.
    try:
        return dispatch(sys.argv[1:])
    except Exception:
        return 0


if __name__ == "__main__":
    sys.exit(main())
