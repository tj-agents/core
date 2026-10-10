"""Shared verified-session and cleanup primitives for peer-cli (Python 3.9+)."""

import json
import math
import os
import re
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
DEFAULT_TIMEOUTS = {
    "AGENT_FINISH_SPAWN_TIMEOUT_SECONDS": 15.0,
    "AGENT_FINISH_ARMED_TIMEOUT_SECONDS": 10.0,
    "AGENT_FINISH_ACCEPT_TIMEOUT_SECONDS": 60.0,
    "AGENT_FINISH_REAPER_TIMEOUT_SECONDS": 600.0,
}
MAX_TIMEOUTS = {
    "AGENT_FINISH_SPAWN_TIMEOUT_SECONDS": 60.0,
    "AGENT_FINISH_ARMED_TIMEOUT_SECONDS": 60.0,
    "AGENT_FINISH_ACCEPT_TIMEOUT_SECONDS": 300.0,
    "AGENT_FINISH_REAPER_TIMEOUT_SECONDS": 3600.0,
}
FINAL_RESULT_STATUSES = frozenset({
    "cancelled", "not-accepted", "failed", "timeout", "succeeded",
    "branch-preserved", "session-closed",
})


class Refusal(RuntimeError):
    pass


def state_directory():
    return Path(os.environ.get("AGENT_STATE_DIRECTORY") or Path.home() / ".agents-state")


def now():
    return time.time()


def finite_positive(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value > 0)


def nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def bounded_timeout(name):
    default = DEFAULT_TIMEOUTS[name]
    try:
        value = float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default
    if not math.isfinite(value) or value <= 0 or value > MAX_TIMEOUTS[name]:
        return default
    return value


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
            and finite_positive(started_at))


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
    if abs(current.started_at - started_at) > IDENTITY_TOLERANCE_SECONDS:
        return "reused"
    if sys.platform == "linux" and process_is_zombie(pid):
        return "exited"
    return "live"


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


def qualified_windows_wrapper(entry):
    """Return only the shell launcher demonstrably attached to this host."""
    if os.name != "nt" or not valid_entry(entry):
        return None
    host = process_info(entry["pid"])
    if (host is None or abs(host.started_at - entry["pid_started_at"])
            > IDENTITY_TOLERANCE_SECONDS):
        return None
    try:
        table = register_session._windows_process_table()
    except (OSError, ValueError):
        return None
    wrapper = table.get(host.ppid)
    shell_names = {"pwsh", "powershell", "cmd", "bash", "sh", "zsh", "fish", "nu"}
    if (wrapper is None or register_session.stem(wrapper.name) not in shell_names
            or not valid_identity(wrapper.pid, wrapper.started_at)
            or wrapper.started_at > host.started_at
            or host.started_at - wrapper.started_at > 10.0):
        return None
    console_names = {"conhost", "openconsole"}
    for child in table.values():
        if child.ppid != wrapper.pid or child.pid == host.pid:
            continue
        if register_session.stem(child.name) not in console_names:
            return None
    try:
        command = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             "(Get-CimInstance -Class Win32_Process -Filter 'ProcessId = %d').CommandLine" % wrapper.pid],
            capture_output=True, text=True, encoding="utf-8", check=False,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    host_name = re.escape(register_session.stem(host.name))
    if command.returncode or not re.search(r"(?<![A-Za-z0-9_.-])" + host_name + r"(?:\.exe)?(?![A-Za-z0-9_.-])", command.stdout, re.IGNORECASE):
        return None
    return {"pid": wrapper.pid, "started_at": wrapper.started_at}


def entries():
    directory = state_directory() / "cli-sessions"
    for path in directory.glob("*.json") if directory.is_dir() else ():
        entry = read_json(path)
        if entry:
            yield path, entry


def valid_entry(entry):
    return (isinstance(entry, dict)
            and nonempty_string(entry.get("cwd"))
            and nonempty_string(entry.get("session_id"))
            and nonempty_string(entry.get("host"))
            and valid_identity(entry.get("pid"), entry.get("pid_started_at"))
            and finite_positive(entry.get("started_at")))


def liveness(entry):
    if not valid_entry(entry):
        return None
    status = identity_status(entry["pid"], entry["pid_started_at"])
    return True if status == "live" else False if status in {"exited", "reused"} else None


def own_host_and_entry(cwd=None):
    cwd = Path(cwd or os.getcwd()).resolve()
    host_names = register_session.read_host_names()
    seen = set()
    current = os.getppid()
    nearest = None
    for _ in range(register_session.MAX_ANCESTOR_DEPTH):
        if current in seen:
            break
        seen.add(current)
        info = process_info(current)
        if info is None:
            break
        if register_session.stem(info.name) in host_names:
            nearest = info
            break
        current = info.ppid
    if nearest is None:
        raise Refusal("current process is not attached to a recognized registered host")
    matches = []
    for _path, entry in entries():
        if not valid_entry(entry) or not under_or_equal(cwd, entry["cwd"]):
            continue
        if (entry["pid"] == nearest.pid
                and entry["host"] == register_session.stem(nearest.name)
                and entry["pid_started_at"] == nearest.started_at
                and verified_live(entry["pid"], entry["pid_started_at"])):
            matches.append(entry)
    if matches:
        latest = max(item["started_at"] for item in matches)
        recent = [item for item in matches if item["started_at"] == latest]
        if len(recent) == 1:
            return recent[0]
        raise Refusal("multiple equally recent verified registry attachments match this host")
    raise Refusal("cannot resolve a verified registry attachment for this host and current directory")


def other_live_claimant(worktree, own_session):
    for _path, entry in entries():
        if entry.get("session_id") == own_session:
            continue
        if not nonempty_string(entry.get("cwd")) or not under_or_equal(entry["cwd"], worktree):
            continue
        # Unknown inspection is not evidence that an attached session is dead.
        if identity_status(entry.get("pid"), entry.get("pid_started_at")) not in {"exited", "reused"}:
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


def worktree_registrations(primary):
    code, output, error = git(primary, "worktree", "list", "--porcelain")
    if code:
        raise Refusal("could not enumerate Git worktrees: " + error)
    records = []
    for block in output.split("\n\n"):
        fields = {}
        detached = False
        for line in block.splitlines():
            if line == "detached":
                detached = True
            elif " " in line:
                key, value = line.split(" ", 1)
                fields[key] = value
        if fields.get("worktree"):
            records.append({
                "worktree": Path(fields["worktree"]).resolve(),
                "head": fields.get("HEAD"),
                "branch": fields.get("branch"),
                "detached": detached,
            })
    if not records:
        raise Refusal("Git returned no worktree registrations")
    return records


def matching_receipt(worktree):
    best = None
    directory = state_directory() / "merge-cleanup" / "receipts"
    for path in directory.glob("*.json") if directory.is_dir() else ():
        receipt = read_json(path)
        if receipt and nonempty_string(receipt.get("worktree")) and path_key(receipt["worktree"]) == path_key(worktree):
            recorded_at = receipt.get("recorded_at")
            if not finite_positive(recorded_at):
                continue
            if best is None or recorded_at > best[1].get("recorded_at", 0):
                best = path, receipt
    if best is None:
        raise Refusal("no cleanup_proof.py receipt recorded for this worktree")
    return best[1]


def fresh_removable_receipt(worktree):
    receipt = matching_receipt(worktree)
    required = ("worktree", "primary", "branch", "head", "default", "verdict", "recorded_at")
    if any(not nonempty_string(receipt.get(key)) for key in required if key != "recorded_at"):
        raise Refusal("the cleanup receipt is incomplete")
    if receipt.get("verdict") != "removable":
        raise Refusal("the cleanup receipt is not removable")
    if (not finite_positive(receipt.get("recorded_at")) or
            receipt["recorded_at"] > now() + IDENTITY_TOLERANCE_SECONDS or
            now() - receipt["recorded_at"] > RECEIPT_MAX_AGE_SECONDS):
        raise Refusal("the cleanup receipt is stale; run cleanup_proof.py again")
    target = Path(worktree).resolve()
    primary = Path(receipt["primary"]).resolve()
    if path_key(receipt["worktree"]) != path_key(target):
        raise Refusal("the cleanup receipt target no longer matches this worktree")
    if target == primary:
        raise Refusal("the primary checkout cannot be removed; use close.py")
    if not primary.is_dir() or not target.is_dir():
        raise Refusal("the cleanup receipt names a missing worktree or primary checkout")
    records = worktree_registrations(primary)
    if records[0]["worktree"] != primary:
        raise Refusal("the cleanup receipt primary is not the main checkout")
    matching = [record for record in records if record["worktree"] == target]
    expected_ref = "refs/heads/" + receipt["branch"]
    if (len(matching) != 1 or matching[0]["detached"]
            or matching[0]["branch"] != expected_ref
            or matching[0]["head"] != receipt["head"]):
        raise Refusal("the cleanup target is not the registered receipt worktree")
    code, head, _ = git(target, "rev-parse", "HEAD")
    branch_code, branch, _ = git(target, "symbolic-ref", "--quiet", "--short", "HEAD")
    if code or branch_code or head != receipt.get("head") or branch != receipt.get("branch"):
        raise Refusal("worktree HEAD/branch no longer match the cleanup receipt")
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
    timeout = bounded_timeout("AGENT_FINISH_SPAWN_TIMEOUT_SECONDS")
    if os.name == "nt":
        # A one-shot scheduled task is outside the terminal's job object.
        task = "agent-finish-reaper-" + uuid.uuid4().hex
        command_text = subprocess.list2cmdline(command)
        try:
            create = subprocess.run(
                ["schtasks.exe", "/create", "/tn", task, "/sc", "once", "/st", "00:00",
                 "/f", "/tr", command_text], **kwargs, check=False, timeout=timeout,
            )
            if create.returncode:
                raise Refusal("could not create a detached cleanup observer")
            run = subprocess.run(["schtasks.exe", "/run", "/tn", task], **kwargs,
                                 check=False, timeout=timeout)
            if run.returncode:
                raise Refusal("could not start a detached cleanup observer")
        except subprocess.TimeoutExpired as error:
            raise Refusal("timed out starting detached cleanup observer") from error
        finally:
            try:
                subprocess.run(["schtasks.exe", "/delete", "/tn", task, "/f"], **kwargs,
                               check=False, timeout=timeout)
            except subprocess.TimeoutExpired:
                pass
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


def binding(host_pid, host_start, worktree, session_id, invocation_id, cleanup=None):
    value = {
        "host_pid": host_pid,
        "host_start": host_start,
        "worktree": str(Path(worktree).resolve()),
        "session_id": session_id,
        "invocation_id": invocation_id,
    }
    if cleanup:
        value.update(cleanup)
    return value


def record_matches_binding(record, expected):
    return isinstance(record, dict) and all(record.get(key) == value for key, value in expected.items())


def valid_observer_start(record, observer_pid, host_pid, host_start, worktree, session_id,
                         invocation_id=None, cleanup=None, minimum_started=None):
    expected = binding(host_pid, host_start, worktree, session_id, invocation_id, cleanup)
    if (not valid_identity(host_pid, host_start) or not nonempty_string(session_id)
            or not nonempty_string(invocation_id)):
        return False
    if not record_matches_binding(record, expected):
        return False
    if record.get("status") in FINAL_RESULT_STATUSES:
        return False
    if not finite_positive(record.get("started")) or record["started"] > now() + IDENTITY_TOLERANCE_SECONDS:
        return False
    if minimum_started is not None and record["started"] + IDENTITY_TOLERANCE_SECONDS < minimum_started:
        return False
    if not valid_identity(record.get("reaper_pid"), record.get("reaper_started_at")):
        return False
    if observer_pid is not None and record["reaper_pid"] != observer_pid:
        return False
    return verified_live(record["reaper_pid"], record["reaper_started_at"])


def valid_acknowledgement(record, expected, observer_record):
    if not record_matches_binding(record, expected):
        return False
    if not finite_positive(record.get("accepted")) or record["accepted"] < observer_record["started"]:
        return False
    if record["accepted"] > now() + IDENTITY_TOLERANCE_SECONDS:
        return False
    return (record.get("reaper_pid") == observer_record.get("reaper_pid")
            and record.get("reaper_started_at") == observer_record.get("reaper_started_at")
            and record.get("observer_pid") == observer_record.get("reaper_pid")
            and record.get("observer_started_at") == observer_record.get("reaper_started_at"))


def valid_armed(record, expected, observer_record, accepted):
    if not record_matches_binding(record, expected):
        return False
    if not finite_positive(record.get("armed")) or record["armed"] < accepted["accepted"]:
        return False
    if record["armed"] > now() + IDENTITY_TOLERANCE_SECONDS:
        return False
    return (record.get("reaper_pid") == observer_record.get("reaper_pid")
            and record.get("reaper_started_at") == observer_record.get("reaper_started_at")
            and record.get("observer_pid") == observer_record.get("reaper_pid")
            and record.get("observer_started_at") == observer_record.get("reaper_started_at")
            and verified_live(record["observer_pid"], record["observer_started_at"]))


def results_path():
    return state_directory() / "merge-cleanup" / "results" / (uuid.uuid4().hex + ".json")


def remove_matching_obligations(worktree, session_id):
    directory = state_directory() / "merge-cleanup" / "obligations"
    for path in directory.glob("*.json") if directory.is_dir() else ():
        obligation = read_json(path)
        if not obligation:
            continue
        if (obligation.get("session_id") == session_id and obligation.get("worktree")
                and path_key(worktree) == path_key(obligation["worktree"])):
            path.unlink(missing_ok=True)
