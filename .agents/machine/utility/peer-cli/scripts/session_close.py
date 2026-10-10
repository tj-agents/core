"""Shared verified-session and cleanup primitives for peer-cli (Python 3.9+)."""

import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

import register_session


RECEIPT_MAX_AGE_SECONDS = 3600.0
IDENTITY_TOLERANCE_SECONDS = 2.0
SUBPROCESS_TIMEOUT_SECONDS = 20


class Refusal(RuntimeError):
    pass


def state_directory():
    return Path(os.environ.get("AGENT_STATE_DIRECTORY") or Path.home() / ".agents-state")


def now():
    return time.time()


def path_key(value):
    path = Path(value).resolve()
    text = path.as_posix().rstrip("/")
    return text.casefold() if os.name == "nt" else text


def under_or_equal(candidate, root):
    candidate_key, root_key = path_key(candidate), path_key(root)
    return candidate_key == root_key or candidate_key.startswith(root_key + "/")


def read_json(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def write_json(path, value, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(value, sort_keys=True) + "\n").encode("utf-8")
    if exclusive:
        try:
            descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            return False
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
        return True
    descriptor, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True


def process_info(pid):
    state, info = process_state(pid)
    return info if state == "present" else None


def valid_identity(pid, started_at):
    return (isinstance(pid, int) and not isinstance(pid, bool) and pid > 0
            and isinstance(started_at, (int, float)) and not isinstance(started_at, bool)
            and math.isfinite(started_at) and started_at > 0)


def process_state(pid):
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return "unknown", None
    try:
        info = register_session.build_process_lookup()(pid)
    except (OSError, ValueError, OverflowError):
        return "unknown", None
    except Exception:
        return "unknown", None
    if info is None:
        return "absent", None
    if not valid_identity(info.pid, info.started_at):
        return "unknown", None
    return "present", info


def verified_live(pid, started_at):
    if not valid_identity(pid, started_at):
        return False
    state, current = process_state(pid)
    return (state == "present" and
            abs(current.started_at - started_at) <= IDENTITY_TOLERANCE_SECONDS)


def identity_status(pid, started_at):
    """Classify a recorded process without treating failed inspection as exit."""
    if not valid_identity(pid, started_at):
        return "unknown"
    state, current = process_state(pid)
    if state == "absent":
        return "exited"
    if state != "present":
        return "unknown"
    if sys.platform == "linux" and process_is_zombie(pid):
        return "exited"
    if abs(current.started_at - started_at) <= IDENTITY_TOLERANCE_SECONDS:
        return "live"
    return "reused"


def process_is_zombie(pid):
    if sys.platform != "linux":
        return False
    try:
        raw = Path("/proc") / str(pid) / "stat"
        fields = raw.read_text(encoding="utf-8").rsplit(")", 1)[1].split()
    except (OSError, IndexError):
        return False
    return bool(fields and fields[0] == "Z")


def verified_exited(pid, started_at):
    return identity_status(pid, started_at) == "exited"


def entries():
    directory = state_directory() / "cli-sessions"
    for path in directory.glob("*.json") if directory.is_dir() else ():
        entry = read_json(path)
        if entry:
            yield path, entry


def liveness(entry):
    started = entry.get("pid_started_at")
    if started is not None:
        status = identity_status(entry.get("pid"), started)
        return True if status == "live" else False if status == "exited" else None
    state, info = process_state(entry.get("pid"))
    if state != "present":
        return None
    recorded = entry.get("started_at")
    return bool(isinstance(recorded, (int, float)) and info.started_at <= recorded + 60)


def own_host_and_entry(cwd=None):
    cwd = Path(cwd or os.getcwd()).resolve()
    ancestry = []
    current = os.getppid()
    for _ in range(register_session.MAX_ANCESTOR_DEPTH):
        info = process_info(current)
        if info is None or info.pid in ancestry:
            break
        ancestry.append(info.pid)
        current = info.ppid
    nearest = None
    for pid in ancestry:
        info = process_info(pid)
        if info and register_session.stem(info.name) in register_session.read_host_names():
            nearest = info
            break
    if nearest is None:
        raise Refusal("current process is not attached to a recognized registered host")
    matches = []
    for _path, entry in entries():
        if not under_or_equal(cwd, entry.get("cwd", cwd)):
            continue
        recorded_at = entry.get("started_at")
        if not isinstance(recorded_at, (int, float)) or not math.isfinite(recorded_at):
            continue
        if (entry.get("pid") == nearest.pid and entry.get("host") == register_session.stem(nearest.name)
                and verified_live(entry.get("pid"), entry.get("pid_started_at"))):
            matches.append(entry)
    if matches:
        matches.sort(key=lambda item: item.get("started_at", 0), reverse=True)
        if len(matches) == 1 or matches[0].get("started_at") != matches[1].get("started_at"):
            return matches[0]
        raise Refusal("multiple equally recent verified registry attachments match this host")
    raise Refusal("cannot resolve a verified registry attachment for this host and current directory")


def other_live_claimant(worktree, own_session):
    for _path, entry in entries():
        if entry.get("session_id") == own_session:
            continue
        if verified_live(entry.get("pid"), entry.get("pid_started_at")) and entry.get("cwd") and under_or_equal(entry["cwd"], worktree):
            return entry
    return None


def git(cwd, *arguments):
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), *arguments], text=True, encoding="utf-8",
            capture_output=True, check=False, timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return 1, "", "git command failed: " + str(error)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def worktree_from_cwd(cwd=None):
    code, output, _error = git(cwd or os.getcwd(), "rev-parse", "--show-toplevel")
    if code:
        raise Refusal("the current directory is not inside a Git worktree")
    return Path(output).resolve()


def matching_receipt(worktree):
    best = None
    directory = state_directory() / "merge-cleanup" / "receipts"
    for path in directory.glob("*.json") if directory.is_dir() else ():
        receipt = read_json(path)
        if receipt and receipt.get("worktree") and path_key(receipt["worktree"]) == path_key(worktree):
            recorded_at = receipt.get("recorded_at")
            if not isinstance(recorded_at, (int, float)) or not math.isfinite(recorded_at):
                continue
            if best is None or recorded_at > best[1].get("recorded_at", 0):
                best = path, receipt
    if best is None:
        raise Refusal("no cleanup_proof.py receipt recorded for this worktree")
    return best[1]


def fresh_removable_receipt(worktree):
    receipt = matching_receipt(worktree)
    required = ("worktree", "primary", "branch", "head", "default", "verdict", "recorded_at")
    if any(not receipt.get(key) for key in required):
        raise Refusal("the cleanup receipt is incomplete")
    if receipt.get("verdict") != "removable":
        raise Refusal("the cleanup receipt is not removable")
    if (not isinstance(receipt.get("recorded_at"), (int, float)) or
            not math.isfinite(receipt["recorded_at"]) or
            receipt["recorded_at"] > now() + IDENTITY_TOLERANCE_SECONDS or
            now() - receipt["recorded_at"] > RECEIPT_MAX_AGE_SECONDS):
        raise Refusal("the cleanup receipt is stale; run cleanup_proof.py again")
    code, head, _ = git(worktree, "rev-parse", "HEAD")
    branch_code, branch, _ = git(worktree, "rev-parse", "--abbrev-ref", "HEAD")
    if code or branch_code or head != receipt.get("head") or branch != receipt.get("branch"):
        raise Refusal("worktree HEAD/branch no longer match the cleanup receipt")
    if path_key(worktree) == path_key(receipt.get("primary", "")):
        raise Refusal("the primary checkout cannot be removed; use close.py")
    primary = Path(receipt["primary"])
    if not primary.is_dir() or not Path(worktree).is_dir():
        raise Refusal("the cleanup receipt names a missing worktree or primary checkout")
    code, listing, error = git(primary, "worktree", "list", "--porcelain")
    marker = "worktree " + str(Path(worktree).resolve())
    if code or marker not in listing.splitlines():
        raise Refusal("the cleanup target is no longer a registered linked worktree: " + error)
    return receipt


def observer_path():
    return Path(__file__).with_name("finish_reaper.py")


def start_observer(arguments):
    staging = state_directory() / "merge-cleanup" / "observers" / uuid.uuid4().hex
    staging.mkdir(parents=True, exist_ok=False)
    for name in ("finish_reaper.py", "session_close.py", "register_session.py"):
        shutil.copy2(Path(__file__).with_name(name), staging / name)
    command = [sys.executable, str(staging / "finish_reaper.py"), *arguments]
    kwargs = {"cwd": str(state_directory()), "stdin": subprocess.DEVNULL,
              "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if os.name == "nt":
        # A one-shot scheduled task is outside the terminal's job object.
        task = "agent-finish-reaper-" + uuid.uuid4().hex
        command_text = subprocess.list2cmdline(command)
        create = subprocess.run(["schtasks.exe", "/create", "/tn", task, "/sc", "once", "/st", "00:00", "/f", "/tr", command_text],
                                **kwargs, check=False)
        if create.returncode:
            raise Refusal("could not create a detached cleanup observer")
        try:
            if subprocess.run(["schtasks.exe", "/run", "/tn", task], **kwargs, check=False).returncode:
                raise Refusal("could not start a detached cleanup observer")
        finally:
            subprocess.run(["schtasks.exe", "/delete", "/tn", task, "/f"], **kwargs, check=False)
        return None
    return subprocess.Popen(command, start_new_session=True, **kwargs).pid


def wait_for_record(path, timeout):
    deadline = now() + timeout
    while now() < deadline:
        record = read_json(path)
        if record:
            return record
        time.sleep(.05)
    return None


def cancel_observer(result_path, reason):
    write_json(str(result_path) + ".cancelled", {"cancelled": now(), "reason": reason})


def valid_observer_start(record, observer_pid, host_pid, host_start, worktree, session_id):
    if not isinstance(record, dict):
        return False
    if (record.get("host_pid") != host_pid or record.get("host_start") != host_start
            or record.get("worktree") != str(worktree) or record.get("session_id") != session_id):
        return False
    if not valid_identity(record.get("reaper_pid"), record.get("reaper_started_at")):
        return False
    if observer_pid is not None and record["reaper_pid"] != observer_pid:
        return False
    return verified_live(record["reaper_pid"], record["reaper_started_at"])


def results_path():
    return state_directory() / "merge-cleanup" / "results" / (uuid.uuid4().hex + ".json")


def remove_matching_obligations(worktree=None, session_id=None):
    directory = state_directory() / "merge-cleanup" / "obligations"
    for path in directory.glob("*.json") if directory.is_dir() else ():
        obligation = read_json(path)
        if not obligation:
            continue
        matches = ((worktree is not None and obligation.get("worktree") and path_key(worktree) == path_key(obligation["worktree"])) or
                   (session_id is not None and obligation.get("session_id") == session_id))
        if matches:
            path.unlink(missing_ok=True)
