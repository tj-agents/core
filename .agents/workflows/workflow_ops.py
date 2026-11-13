"""Deterministic workflow operations: compact command runs, repository inspection, delivery
preflight, PR body checks and the reconnect-safe remote monitor."""

import argparse
import errno
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from process_runtime import process
from pr_body import validate_pr_body


SCHEMA_VERSION = 1
DEFAULT_SUMMARY_LINES = 8
DEFAULT_FAILURE_ITEMS = 20
DEFAULT_SUMMARY_BYTES = 4096
DEFAULT_POLL_SECONDS = 60
DEFAULT_MONITOR_SECONDS = 21600
DEFAULT_OFFLINE_GAP_SECONDS = 300
BRANCH_NAME = re.compile(r"[A-Z][A-Za-z0-9-]*/[A-Z][A-Za-z0-9-]*")
# MoveFileEx reports a conflicting open handle as either access denied or sharing violation.
WINDOWS_REPLACE_CONFLICTS = (5, 32)
FAILURE_PATTERN = re.compile(
    r"(?:\bfailed\b|\bfailure\b|\berror\b|\bfatal\b|\bexception\b|\bpanic\b|\btimeout\b)",
    re.IGNORECASE,
)


class WorkflowOperationError(RuntimeError):
    pass


class MonitorLease:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            handle = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                owner = json.loads(self.path.read_text(encoding="utf-8"))
                owner_pid = int(owner["pid"])
                if owner_pid != os.getpid():
                    os.kill(owner_pid, 0)
            except (OSError, ValueError, KeyError, json.JSONDecodeError):
                self.path.unlink(missing_ok=True)
                handle = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            else:
                raise WorkflowOperationError("another process already owns this exact monitor identity")
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump({"pid": os.getpid(), "started_at": utc_now()}, stream)
        return self

    def __exit__(self, exception_type, exception, traceback):
        self.path.unlink(missing_ok=True)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value):
    return hashlib.sha256(json_bytes(value)).hexdigest()


def emit(value):
    sys.stdout.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def redact(text):
    text = re.sub(
        r"(?im)\bauthorization\s*[:=]\s*[^\r\n]+",
        "Authorization: [REDACTED]",
        text,
    )
    text = re.sub(
        r"(?i)(?<![A-Za-z0-9_-])([A-Za-z0-9_-]*(?:token|secret|password|api[_-]?key)[A-Za-z0-9_-]*)(\s*[:=]\s*)([^\s,;]+)",
        r"\1\2[REDACTED]",
        text,
    )
    return re.sub(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [REDACTED]", text)

def run_process(arguments, cwd, text=True, check=True):
    executable = shutil.which(arguments[0]) or arguments[0]
    completed = process.run(
        [executable, *arguments[1:]],
        cwd=str(cwd),
        capture_output=True,
        text=text,
        encoding="utf-8" if text else None,
        errors="replace" if text else None,
    )
    if check and completed.returncode:
        stderr = completed.stderr if text else completed.stderr.decode("utf-8", errors="replace")
        raise WorkflowOperationError(redact(stderr.strip()) or f"{arguments[0]} exited {completed.returncode}")
    return completed


def git(root, *arguments):
    return run_process(["git", *arguments], root).stdout.strip()


def repository_root(start):
    return Path(git(start, "rev-parse", "--show-toplevel")).resolve()


def repository_slug(root):
    remote = git(root, "remote", "get-url", "origin")
    match = re.search(r"(?:[:/])([^/:]+)/([^/]+?)(?:\.git)?$", remote)
    if not match:
        raise WorkflowOperationError("origin is not a supported forge repository URL")
    return f"{match.group(1)}/{match.group(2)}"


def common_git_directory(root):
    common = Path(git(root, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    if not common.is_absolute():
        common = root / common
    return common.resolve()

def state_root(root):
    target = common_git_directory(root) / "agent-workflow"
    target.mkdir(parents=True, exist_ok=True)
    return target


def run_root(root, workflow_run_id):
    if not isinstance(workflow_run_id, str) or not workflow_run_id.strip():
        raise WorkflowOperationError("workflow run id is required")
    runs = state_root(root) / "runs"
    candidate = runs / workflow_run_id
    try:
        parts = candidate.relative_to(runs).parts
    except ValueError as error:
        raise WorkflowOperationError("workflow run id escapes the workflow state root") from error
    current = runs
    if is_redirect(runs.parent) or is_redirect(current):
        raise WorkflowOperationError("workflow run id contains a redirected owned directory")
    for part in parts:
        current = current / part
        if is_redirect(current):
            raise WorkflowOperationError("workflow run id contains a redirected owned directory")
    runs = runs.resolve()
    candidate = candidate.resolve()
    try:
        candidate.relative_to(runs)
    except ValueError as error:
        raise WorkflowOperationError("workflow run id escapes the workflow state root") from error
    if candidate == runs:
        raise WorkflowOperationError("workflow run id must identify a run below the workflow state root")
    return candidate


def is_redirect(path):
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    attributes = getattr(metadata, "st_file_attributes", 0)
    return path.is_symlink() or stat.S_ISLNK(metadata.st_mode) or bool(
        attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    )


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        retry_windows_sharing_violation(lambda: os.replace(temporary, path))
    finally:
        if temporary.exists():
            temporary.unlink()


def retry_windows_sharing_violation(action, timeout=2):
    deadline = time.monotonic() + timeout
    while True:
        try:
            return action()
        except PermissionError as error:
            winerror = getattr(error, "winerror", None)
            conflict = winerror in WINDOWS_REPLACE_CONFLICTS or winerror is None and error.errno == errno.EACCES
            if (os.name != "nt" or not conflict
                    or time.monotonic() >= deadline):
                raise
            time.sleep(0.01)

def bounded_lines(text, maximum_lines, maximum_bytes):
    selected = [line.strip() for line in text.splitlines() if line.strip()][-maximum_lines:]
    result = []
    used = 0
    for line in selected:
        encoded = line.encode("utf-8")
        remaining = maximum_bytes - used
        if remaining <= 0:
            break
        if len(encoded) > remaining:
            line = encoded[:remaining].decode("utf-8", errors="ignore")
            encoded = line.encode("utf-8")
        result.append(line)
        used += len(encoded)
    return result


def failing_items(text, maximum_items, maximum_bytes):
    matches = []
    used = 0
    for line in text.splitlines():
        candidate = line.strip()
        if not candidate or not FAILURE_PATTERN.search(candidate):
            continue
        encoded = candidate.encode("utf-8")
        remaining = maximum_bytes - used
        if remaining <= 0:
            break
        if len(encoded) > remaining:
            candidate = encoded[:remaining].decode("utf-8", errors="ignore")
            encoded = candidate.encode("utf-8")
        if candidate not in matches:
            matches.append(candidate)
            used += len(encoded)
        if len(matches) >= maximum_items:
            break
    return matches


def command_identity(label, command):
    safe_program = Path(command[0]).name
    return {
        "label": label,
        "program": safe_program,
        "argument_count": max(0, len(command) - 1),
        "digest": digest(command),
    }


def compact_run(root, workflow_run_id, label, command, summary_lines, failure_items_limit, summary_bytes):
    if not command:
        raise WorkflowOperationError("a command is required after --")
    summary_bytes = min(max(0, summary_bytes), DEFAULT_SUMMARY_BYTES)
    failure_items_limit = min(max(0, failure_items_limit), DEFAULT_FAILURE_ITEMS)
    summary_lines = min(max(0, summary_lines), DEFAULT_FAILURE_ITEMS)
    identity = command_identity(label, command)
    artifact_dir = run_root(root, workflow_run_id) / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact = artifact_dir / f"{identity['digest'][:16]}-{re.sub(r'[^a-zA-Z0-9_.-]+', '-', label)}.log"
    started = time.monotonic()
    completed = run_process(command, root, check=False)
    duration = time.monotonic() - started
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    combined = redact(stdout + ("\n" if stdout and stderr else "") + stderr)
    artifact.write_text(combined, encoding="utf-8")
    failures = [] if completed.returncode == 0 else failing_items(combined, failure_items_limit, summary_bytes)
    summary = [] if completed.returncode == 0 else bounded_lines(combined, summary_lines, summary_bytes)
    return {
        "schema_version": SCHEMA_VERSION,
        "operation": "run",
        "command": identity,
        "duration_seconds": round(duration, 3),
        "exit_state": "succeeded" if completed.returncode == 0 else "failed",
        "exit_code": completed.returncode,
        "failing_items": failures,
        "summary": summary,
        "captured_lines": len(combined.splitlines()),
        "artifact": str(artifact),
    }


def inspect_repository(root):
    branch = git(root, "branch", "--show-current")
    head = git(root, "rev-parse", "HEAD")
    status = run_process(
        ["git", "status", "--porcelain=v1", "--untracked-files=all", "-z"], root
    ).stdout
    dirty_paths = []
    entries = iter(status.split("\0"))
    for entry in entries:
        if entry:
            dirty_paths.append(entry[3:])
            if "R" in entry[:2] or "C" in entry[:2]:
                dirty_paths.append(next(entries))
    upstream = run_process(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
        root,
        check=False,
    ).stdout.strip()
    ahead = behind = None
    if upstream:
        counts = git(root, "rev-list", "--left-right", "--count", f"{upstream}...HEAD").split()
        if len(counts) == 2:
            behind, ahead = (int(counts[0]), int(counts[1]))
    return {
        "schema_version": SCHEMA_VERSION,
        "operation": "inspect",
        "repository": repository_slug(root),
        "root": str(root),
        "branch": branch,
        "head": head,
        "upstream": upstream or None,
        "ahead": ahead,
        "behind": behind,
        "dirty_paths": dirty_paths,
    }


def parse_status_checks(checks):
    failures = []
    pending = []
    for check in checks or []:
        name = check.get("name") or check.get("context") or "unknown"
        status = str(check.get("status") or "").lower()
        legacy_state = str(check.get("state") or "").lower()
        conclusion = str(check.get("conclusion") or "").lower()
        if legacy_state in {"error", "failure", "failed"}:
            failures.append(name)
        elif legacy_state in {"success", "neutral", "skipped"}:
            continue
        elif conclusion and conclusion not in {"success", "neutral", "skipped"}:
            failures.append(name)
        elif status not in {"completed", "success"} or not conclusion:
            pending.append(name)
    return failures, pending


def forge_observation(root, identity):
    if identity["target_kind"] == "run":
        fields = "databaseId,headSha,status,conclusion,workflowName,attempt,url,event"
        completed = run_process(["gh", "run", "view", str(identity["target_id"]), "--json", fields], root)
        value = json.loads(completed.stdout)
        if str(value.get("headSha")) != identity["head"]:
            raise WorkflowOperationError("run head differs from the bound head")
        if identity.get("workflow") and value.get("workflowName") != identity["workflow"]:
            raise WorkflowOperationError("run workflow differs from the bound workflow")
        if identity.get("attempt") is not None and value.get("attempt") != identity["attempt"]:
            raise WorkflowOperationError("run attempt differs from the bound attempt")
        return {
            "state": str(value.get("status") or "unknown").lower(),
            "conclusion": str(value.get("conclusion") or "").lower() or None,
            "workflow": value.get("workflowName"),
            "attempt": value.get("attempt"),
            "url": value.get("url"),
        }
    fields = "number,headRefOid,state,mergeStateStatus,autoMergeRequest,statusCheckRollup,url"
    completed = run_process(["gh", "pr", "view", str(identity["target_id"]), "--json", fields], root)
    value = json.loads(completed.stdout)
    if str(value.get("headRefOid")) != identity["head"]:
        raise WorkflowOperationError("PR head differs from the bound head")
    failures, pending = parse_status_checks(value.get("statusCheckRollup"))
    owner, name = identity["repository"].split("/", 1)
    query = "query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){mergeQueueEntry{state}}}}"
    queue = run_process(
        [
            "gh",
            "api",
            "graphql",
            "-F",
            f"owner={owner}",
            "-F",
            f"name={name}",
            "-F",
            f"number={identity['target_id']}",
            "-f",
            f"query={query}",
        ],
        root,
    )
    queue_value = json.loads(queue.stdout)
    queue_entry = queue_value.get("data", {}).get("repository", {}).get("pullRequest", {}).get("mergeQueueEntry")
    runs = run_process(
        ["gh", "run", "list", "--event", "merge_group", "--limit", "50", "--json", "conclusion,headBranch,databaseId,headSha,status,workflowName,url"],
        root,
    )
    branch_marker = f"pr-{identity['target_id']}-{identity['head']}"
    merge_group_runs = [
        run
        for run in json.loads(runs.stdout)
        if branch_marker in str(run.get("headBranch") or "")
    ]
    merge_group_failures = [
        str(run.get("workflowName") or run.get("databaseId") or "merge-group")
        for run in merge_group_runs
        if str(run.get("conclusion") or "").lower() not in {"", "success", "neutral", "skipped"}
    ]
    return {
        "state": str(value.get("state") or "unknown").lower(),
        "merge_state": str(value.get("mergeStateStatus") or "unknown").lower(),
        "auto_merge": value.get("autoMergeRequest") is not None,
        "check_count": len(value.get("statusCheckRollup") or []),
        "queue_state": str(queue_entry.get("state")).lower() if queue_entry else None,
        "failing_items": failures,
        "pending_items": pending,
        "merge_group_failures": merge_group_failures,
        "merge_group_runs": [str(run.get("databaseId")) for run in merge_group_runs],
        "url": value.get("url"),
    }


def observation_tuple(value):
    return digest(value)


def observation_terminal(kind, value):
    if kind == "run":
        return value.get("state") == "completed"
    return (
        value.get("state") in {"closed", "merged"}
        or value.get("merge_state") == "dirty"
        or bool(value.get("failing_items"))
        or bool(value.get("merge_group_failures"))
    )


def remote_identity(root, target_kind, target_id, head, workflow, attempt):
    return {
        "schema_version": SCHEMA_VERSION,
        "repository": repository_slug(root),
        "repository_root": str(root),
        "branch": git(root, "branch", "--show-current"),
        "head": git(root, "rev-parse", head),
        "target_kind": target_kind,
        "target_id": str(target_id),
        "workflow": workflow,
        "attempt": attempt,
    }


def monitor_remote(root, workflow_run_id, target_kind, target_id, head, workflow, attempt, poll_seconds, timeout_seconds, observer=None):
    """Watch one PR, head or run until a material transition, without model turns.

    One monitor owns each exact identity; rerunning the same command after process loss reconnects to
    its persisted state. Unchanged observations stay silent. A PR wake resolves to one state: merged,
    closed, a failed check or merge-group run, a conflicted (`dirty`) PR whose auto-merge GitHub
    disabled, green but never admitted (`green-unadmitted`), a query error, or timeout. Report the
    terminal once; never retry or toggle a genuine failure.
    """
    identity = remote_identity(root, target_kind, target_id, head, workflow, attempt)
    monitor_id = digest(identity)
    path = state_root(root) / "monitors" / f"{monitor_id}.json"
    with MonitorLease(path.with_suffix(".lock")):
        return monitor_remote_owned(root, workflow_run_id, target_kind, poll_seconds, timeout_seconds, observer, identity, monitor_id, path)


def monitor_remote_owned(root, workflow_run_id, target_kind, poll_seconds, timeout_seconds, observer, identity, monitor_id, path):
    if path.is_file():
        state = json.loads(path.read_text(encoding="utf-8"))
        expected = {key: identity[key] for key in identity}
        actual = {key: state["identity"][key] for key in identity}
        if expected != actual:
            raise WorkflowOperationError("persisted monitor identity differs from the requested identity")
        reconnected = True
    else:
        state = {
            "schema_version": SCHEMA_VERSION,
            "monitor_id": monitor_id,
            "identity": identity,
            "created_at": utc_now(),
            "last_observed_at": None,
            "last_observation": None,
            "last_signature": None,
            "active_execution_seconds": 0.0,
            "remote_waiting_seconds": 0.0,
            "suspended_offline_seconds": 0.0,
            "queries": 0,
            "unadmitted_observations": 0,
        }
        atomic_json(path, state)
        reconnected = False
    started = time.monotonic()
    while True:
        if time.monotonic() - started >= timeout_seconds:
            transition = "timeout"
            terminal = True
            observation = state["last_observation"]
            break
        wall_before = time.time()
        if state["last_observed_at"] is not None:
            gap = wall_before - state["last_observed_at"]
            expected_gap = poll_seconds
            if gap > max(DEFAULT_OFFLINE_GAP_SECONDS, expected_gap * 3):
                state["suspended_offline_seconds"] += max(0.0, gap - expected_gap)
        query_started = time.monotonic()
        try:
            observation = (observer or forge_observation)(root, state["identity"])
        except Exception as error:
            observation = {"state": "query-error", "error": str(error)[:DEFAULT_SUMMARY_BYTES]}
        state["active_execution_seconds"] += time.monotonic() - query_started
        state["queries"] += 1
        signature = observation_tuple(observation)
        initial_ready = (
            state["last_signature"] is None
            and target_kind == "pr"
            and observation.get("state") == "open"
            and observation.get("check_count", 0) > 0
            and not observation.get("pending_items")
            and not observation.get("failing_items")
            and not observation.get("merge_group_failures")
        )
        changed = initial_ready or (state["last_signature"] is not None and signature != state["last_signature"])
        terminal = observation_terminal(target_kind, observation) or observation.get("state") == "query-error"
        if (
            target_kind == "pr"
            and observation.get("state") == "open"
            and observation.get("merge_state") == "clean"
            and observation.get("auto_merge")
            and observation.get("queue_state") is None
            and not observation.get("pending_items")
            and not observation.get("failing_items")
            and not observation.get("merge_group_runs")
        ):
            state["unadmitted_observations"] += 1
        else:
            state["unadmitted_observations"] = 0
        if state["unadmitted_observations"] >= 6:
            observation["state"] = "green-unadmitted"
            terminal = True
        state["last_observed_at"] = time.time()
        state["last_observation"] = observation
        state["last_signature"] = signature
        atomic_json(path, state)
        if terminal or changed:
            transition = "terminal" if terminal else "material-transition"
            break
        wait_started = time.monotonic()
        time.sleep(poll_seconds)
        state["remote_waiting_seconds"] += time.monotonic() - wait_started
        atomic_json(path, state)
    return {
        "schema_version": SCHEMA_VERSION,
        "operation": "monitor",
        "monitor_id": monitor_id,
        "identity": state["identity"],
        "reconnected": reconnected,
        "transition": transition,
        "terminal": terminal,
        "observation": observation,
        "timing": {
            "active_execution_seconds": round(state["active_execution_seconds"], 3),
            "remote_waiting_seconds": round(state["remote_waiting_seconds"], 3),
            "suspended_offline_seconds": round(state["suspended_offline_seconds"], 3),
        },
        "queries": state["queries"],
        "state_artifact": str(path),
    }


def default_branch(root):
    completed = run_process(["git", "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"], root, check=False)
    value = completed.stdout.strip()
    return value.removeprefix("origin/") if value else "main"


def owning_pull_request(root, branch, pr_url=None):
    repository = repository_slug(root)
    fields = "number,url,headRefName,headRefOid,baseRefName,state,isCrossRepository,mergeStateStatus"
    if pr_url:
        match = re.fullmatch(r"https://github\.com/([^/\s]+/[^/\s]+)/pull/([1-9][0-9]*)", pr_url)
        if not match or match[1].casefold() != repository.casefold():
            raise WorkflowOperationError("owning PR must be a GitHub URL in this repository")
        return json.loads(run_process(
            ["gh", "pr", "view", match[2], "--repo", repository, "--json", fields], root
        ).stdout)
    matches = json.loads(run_process(
        ["gh", "pr", "list", "--repo", repository, "--head", branch, "--state", "open",
         "--limit", "2", "--json", fields], root
    ).stdout)
    if len(matches) > 1:
        raise WorkflowOperationError("several open PRs use this branch; resolve which one owns the work")
    return matches[0] if matches else None


def delivery_preflight(root, pr_url=None):
    """Read-only check that the current branch is clear to publish or land.

    No PR yet is green. A branch name outside `<Type>/<Name>` only warns. Base currency blocks only
    when GitHub reports the PR `BEHIND`, which it does only when the base requires an up-to-date branch.
    """
    inspection = inspect_repository(root)
    branch = inspection["branch"]
    blockers = []
    warnings = []
    if not branch:
        blockers.append("detached-head")
    elif branch == default_branch(root):
        blockers.append("default-branch")
    elif not BRANCH_NAME.fullmatch(branch):
        warnings.append("branch-name")
    if inspection["behind"]:
        blockers.append("local-behind-upstream")
    code_dirty = [path for path in inspection["dirty_paths"] if Path(path).suffix.lower() != ".md"]
    if code_dirty:
        blockers.append("uncommitted-code")
    on_feature_branch = bool(branch) and "default-branch" not in blockers
    pull_request = owning_pull_request(root, branch, pr_url) if on_feature_branch else None
    if pull_request is None:
        ownership = {"pr_url": None, "action": "create"}
    else:
        state = str(pull_request.get("state") or "").upper()
        merge_state = str(pull_request.get("mergeStateStatus") or "").upper()
        if state != "OPEN" or pull_request.get("isCrossRepository"):
            action = "reconcile-review"
        else:
            action = "update" if pull_request.get("headRefName") == branch else "integrate"
        ownership = {
            "pr_url": pull_request.get("url"),
            "branch": pull_request.get("headRefName"),
            "head": pull_request.get("headRefOid"),
            "base": pull_request.get("baseRefName"),
            "action": action,
        }
        if action != "update":
            blockers.append("delivery-" + action)
        if merge_state == "BEHIND":
            blockers.append("base-update-required")
        elif merge_state == "DIRTY":
            blockers.append("merge-conflict")
    return {
        "schema_version": SCHEMA_VERSION,
        "operation": "delivery-preflight",
        "ownership": ownership,
        "identity": {key: inspection[key] for key in ("repository", "root", "branch", "head", "upstream", "ahead", "behind")},
        "code_dirty_paths": code_dirty,
        "documentation_dirty_paths": [path for path in inspection["dirty_paths"] if path not in code_dirty],
        "warnings": warnings,
        "blockers": blockers,
        "ready": not blockers,
    }


def pull_request_state(root, pr, repo=None):
    arguments = ["gh", "pr", "view"]
    if pr is not None:
        arguments.append(str(pr))
    arguments += ["--json", "number,url,body,headRefOid"]
    if repo is not None:
        arguments += ["--repo", repo]
    return json.loads(run_process(arguments, root).stdout)


def pr_body_check(root, pr, repo=None):
    value = pull_request_state(root, pr, repo)
    validation = validate_pr_body(value.get("body"))
    if not isinstance(value.get("number"), int) or not value.get("url") or not value.get("headRefOid"):
        raise WorkflowOperationError("gh pr view returned no usable PR identity")
    return {
        "schema_version": SCHEMA_VERSION,
        "operation": "pr-body-check",
        "pr": value["number"],
        "url": value["url"],
        "head": value["headRefOid"],
        "validation": validation,
        "exit_state": "passed" if validation["valid"] else "failed",
    }


def cleanup(root, retention_days):
    cutoff = time.time() - retention_days * 86400
    removed = 0
    for path in state_root(root).rglob("*"):
        if path.is_file() and path.stat().st_mtime < cutoff:
            path.unlink()
            removed += 1
    return {"schema_version": SCHEMA_VERSION, "operation": "cleanup", "removed_count": removed, "retention_days": retention_days}


def parser():
    result = argparse.ArgumentParser()
    result.add_argument("--root", default=".")
    result.add_argument("--workflow-run-id", required=True)
    commands = result.add_subparsers(dest="operation", required=True)

    run = commands.add_parser("run")
    run.add_argument("--label", required=True)
    run.add_argument("--summary-lines", type=int, default=DEFAULT_SUMMARY_LINES)
    run.add_argument("--failure-items", type=int, default=DEFAULT_FAILURE_ITEMS)
    run.add_argument("--summary-bytes", type=int, default=DEFAULT_SUMMARY_BYTES)
    run.add_argument("command", nargs=argparse.REMAINDER)

    commands.add_parser("inspect")

    monitor = commands.add_parser("monitor")
    monitor.add_argument("--kind", choices=("run", "pr"), required=True)
    monitor.add_argument("--id", required=True)
    monitor.add_argument("--head", default="HEAD")
    monitor.add_argument("--workflow")
    monitor.add_argument("--attempt", type=int)
    monitor.add_argument("--poll-seconds", type=float, default=DEFAULT_POLL_SECONDS)
    monitor.add_argument("--timeout-seconds", type=float, default=DEFAULT_MONITOR_SECONDS)

    preflight = commands.add_parser("delivery-preflight")
    preflight.add_argument("--pr-url")

    body_check = commands.add_parser("pr-body-check")
    body_check.add_argument("--pr", required=True)
    body_check.add_argument("--repo")

    cleanup_parser = commands.add_parser("cleanup")
    cleanup_parser.add_argument("--retention-days", type=int, default=14)
    return result


def main(argv=None):
    arguments = parser().parse_args(argv)
    root = repository_root(Path(arguments.root).resolve())
    if arguments.operation != "pr-body-check":
        run_root(root, arguments.workflow_run_id)
    if arguments.operation == "run":
        command = arguments.command[1:] if arguments.command[:1] == ["--"] else arguments.command
        result = compact_run(root, arguments.workflow_run_id, arguments.label, command, arguments.summary_lines, arguments.failure_items, arguments.summary_bytes)
    elif arguments.operation == "inspect":
        result = inspect_repository(root)
    elif arguments.operation == "monitor":
        result = monitor_remote(root, arguments.workflow_run_id, arguments.kind, arguments.id, arguments.head, arguments.workflow, arguments.attempt, arguments.poll_seconds, arguments.timeout_seconds)
    elif arguments.operation == "delivery-preflight":
        result = delivery_preflight(root, arguments.pr_url)
    elif arguments.operation == "pr-body-check":
        result = pr_body_check(root, arguments.pr, arguments.repo)
    else:
        result = cleanup(root, arguments.retention_days)
    emit(result)
    if arguments.operation == "delivery-preflight" and not result["ready"]:
        return 1
    return 0 if result.get("exit_state") != "failed" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (WorkflowOperationError, OSError, ValueError, json.JSONDecodeError) as error:
        emit({"schema_version": SCHEMA_VERSION, "operation": "error", "error": str(error)[:DEFAULT_SUMMARY_BYTES]})
        raise SystemExit(2)
