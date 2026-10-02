import argparse
import contextlib
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from delivery_runtime import BINDING_FILE, PersistentDeliveryRouter, binding_from_artifact, DeliveryContractViolation
from workflow_ops import atomic_json, parse_status_checks, repository_slug


class Gate(RuntimeError):
    pass


def command(args, root, timeout=30):
    result = subprocess.run(args, cwd=root, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"{args[0]} exited {result.returncode}")
    return result.stdout.strip()


def git(root, *args):
    return command(["git", *args], root)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def process_identity(pid):
    if os.name == "nt":
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
        kernel.GetProcessTimes.argtypes = [ctypes.c_void_p] * 5
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return "unknown" if ctypes.get_last_error() == 5 else None
        try:
            exit_code = ctypes.c_uint32()
            kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
            if kernel.GetExitCodeProcess(handle, ctypes.byref(exit_code)) and exit_code.value != 259:
                return None
            values = [ctypes.c_uint64() for _ in range(4)]
            if not kernel.GetProcessTimes(handle, *(ctypes.byref(v) for v in values)):
                return "unknown"
            return str(values[0].value)
        finally:
            kernel.CloseHandle(handle)
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
        fields = raw[raw.rfind(")") + 2:].split()
        return None if fields[0] == "Z" else fields[19]
    except FileNotFoundError:
        return None
    except OSError:
        try:
            os.kill(pid, 0)
            return "unknown"
        except ProcessLookupError:
            return None


def alive(record):
    current = process_identity(record["pid"])
    return current is not None and (current == "unknown" or current == record["identity"])


@contextlib.contextmanager
def locked(directory):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "owner.lock").open("a+b") as stream:
        stream.seek(0)
        if os.name == "nt":
            import msvcrt
            if os.fstat(stream.fileno()).st_size == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                yield False
                return
        else:
            import fcntl
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                yield False
                return
        try:
            yield True
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def save(path, state, event):
    state["updated_at"] = time.time()
    atomic_json(path, state)
    record = {"at": state["updated_at"], "owner_id": state["owner_id"],
              "event": event, "state": state["state"], "reason": state.get("reason")}
    with (path.parent / "events.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")


def transition(state, status, reason, next_action=""):
    state.update(state=status, reason=reason, next_action=next_action)


def identity(root):
    return {"repo": repository_slug(root), "worktree": str(root),
            "branch": git(root, "branch", "--show-current"),
            "head": git(root, "rev-parse", "HEAD")}


def check_identity(state, allow_terminal_release=False):
    root = Path(state["worktree"])
    current = identity(root)
    for key in ("repo", "worktree", "branch", "head"):
        if current[key] != state[key]:
            raise Gate(f"owner-{key}-changed")
    goal = Path(state["goal"])
    if not goal.is_file() or not goal.resolve().is_relative_to(root):
        raise Gate("canonical-goal-unavailable")
    binding_path = root / BINDING_FILE
    binding = read(binding_path) if binding_path.exists() else None
    if binding is not None:
        try:
            PersistentDeliveryRouter().validate_binding(binding_from_artifact(binding))
        except (DeliveryContractViolation, KeyError, TypeError) as error:
            raise Gate(f"delivery-binding-invalid: {error}") from error
        for key in ("repo", "worktree", "branch", "head"):
            actual = str(Path(binding.get(key, "")).resolve()) if key == "worktree" else binding.get(key)
            if actual != current[key]:
                raise Gate(f"binding-{key}-changed")
        if not isinstance(binding.get("pr"), int) or binding["pr"] < 1:
            raise Gate("binding-pr-invalid")
        if state.get("pr") is not None and state["pr"] != binding["pr"]:
            raise Gate("binding-pr-changed")
        state["pr"] = binding["pr"]
    elif state.get("pr") is not None and not allow_terminal_release:
        raise Gate("binding-removed")
    return binding


def observe(state, binding, observer=None):
    if binding is None:
        return {"kind": "actionable" if state.get("next_action") else "pending",
                "next_action": state.get("next_action", "")}
    args = observer or ["gh", "pr", "view", str(binding["pr"]), "--repo", binding["repo"],
                        "--json", "number,headRefOid,headRefName,state,statusCheckRollup,url"]
    value = json.loads(command(args, state["worktree"]))
    if (value.get("number") != binding["pr"] or value.get("headRefOid") != binding["head"]
            or value.get("headRefName") != binding["branch"]
            or value.get("url") != f"https://github.com/{binding['repo']}/pull/{binding['pr']}"):
        raise Gate("forge-identity-changed")
    failures, pending = parse_status_checks(value.get("statusCheckRollup"))
    if value.get("state") == "CLOSED":
        raise Gate("pull-request-closed-without-merge")
    if value.get("state") not in {"OPEN", "MERGED"}:
        raise Gate("forge-state-unsupported")
    kind = "failure" if failures else "pending" if pending else "ready"
    return {"kind": kind, "pr_state": value["state"], "failures": failures,
            "pending": pending, "head": binding["head"],
            "checks": sorted(value.get("statusCheckRollup") or [], key=lambda item: json.dumps(item, sort_keys=True)),
            "delivery": {key: binding.get(key) for key in
                         ("pending_evidence", "review", "merge_authorization", "completion_condition")}}


def lane_command(state, prompt, executable=None):
    host = state["harness"]
    if host not in {"codex", "claude"}:
        raise Gate("unsupported-host")
    base = Path(__file__).resolve().parent.parent
    tables = [base / "lanes" / f"{host}.json", base / ".agents/lanes" / f"{host}.json"]
    lane_path = next((p for p in tables if p.is_file()), None)
    if lane_path is None:
        raise Gate("packaged-lane-table-unavailable")
    table = read(lane_path)
    lane = table["lanes"]["L4"]
    prefix = executable or [state.get("host_executable") or shutil.which(host) or host]
    if executable is None and not state.get("host_executable") and not shutil.which(host):
        raise Gate("host-cli-unavailable")
    if os.name == "nt" and Path(prefix[0]).suffix.lower() in {".cmd", ".bat"}:
        raise Gate("native-host-executable-required")
    if host == "codex":
        return [*prefix, "exec", "--model", lane["model"], "--config",
                f'model_reasoning_effort="{lane[table["effort_key"]]}"',
                "--cd", state["worktree"], prompt]
    return [*prefix, "-p", prompt, "--model", lane["model"], "--effort", lane[table["effort_key"]]]


def apply_receipt(state, receipt):
    if receipt.get("nonce") != state.get("launch_nonce") or receipt.get("owner_id") != state["owner_id"]:
        raise Gate("checkpoint-identity-invalid")
    status = receipt.get("state")
    if status not in {"waiting", "complete", "blocked"}:
        raise Gate("checkpoint-state-invalid")
    if not isinstance(receipt.get("reason"), str) or not receipt["reason"].strip():
        raise Gate("checkpoint-reason-required")
    if status != "complete" and not receipt.get("next_action"):
        raise Gate("checkpoint-next-action-required")
    current = identity(Path(state["worktree"]))
    if current["head"] != state["head"]:
        rebind = receipt.get("rebind") or {}
        binding_path = Path(state["worktree"]) / BINDING_FILE
        binding = read(binding_path) if binding_path.exists() else None
        old = {key: state[key] for key in ("repo", "worktree", "branch", "head")}
        if (rebind.get("old") != old or rebind.get("new") != current
                or any(current[k] != state[k] for k in ("repo", "branch", "worktree"))
                or (state.get("pr") and (binding is None or binding.get("pr") != state["pr"]))):
            raise Gate("repair-rebind-invalid")
        if binding is not None and any(binding.get(key) != current[key] for key in current):
            raise Gate("repair-binding-not-refreshed")
        state["head"] = current["head"]
        state["evidence"] = None
    check_identity(state, allow_terminal_release=status in {"complete", "blocked"})
    transition(state, status, receipt["reason"], receipt.get("next_action", ""))
    state["failures"] = 0


def child(args):
    path = Path(args.owner)
    until = time.monotonic() + 10
    while time.monotonic() < until:
        state = read(path)
        if (state.get("child") or {}).get("pid") == os.getpid():
            break
        time.sleep(0.05)
    else:
        return 2
    payload = read(args.payload)
    env = dict(os.environ, **payload["environment"])
    job = windows_job() if os.name == "nt" else None
    process = subprocess.Popen(payload["command"], cwd=state["worktree"], env=env,
                               creationflags=4 if job else 0,
                               preexec_fn=parent_death_signal if os.name == "posix" else None)
    assigned = False
    try:
        if job:
            kernel, handle = job
            if not kernel.AssignProcessToJobObject(handle, int(process._handle)):
                raise OSError("cannot assign supervised host to lifetime job")
            assigned = True
        atomic_json(Path(payload["child_path"]), {"pid": process.pid,
                                                "identity": process_identity(process.pid)})
        if job:
            ntdll = ctypes.WinDLL("ntdll")
            ntdll.NtResumeProcess.argtypes = [ctypes.c_void_p]
            if ntdll.NtResumeProcess(int(process._handle)) != 0:
                raise OSError("cannot resume supervised host")
        return process.wait()
    except BaseException:
        if job and assigned:
            kernel.TerminateJobObject(handle, 1)
        elif process.poll() is None:
            process.kill()
        process.wait(timeout=15)
        raise
    finally:
        if job:
            kernel.CloseHandle(handle)


def parent_death_signal():
    if sys.platform.startswith("linux"):
        ctypes.CDLL(None).prctl(1, signal.SIGKILL)


def windows_job():
    from ctypes import wintypes
    class Basic(ctypes.Structure):
        _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                    ("flags", wintypes.DWORD), ("min_working", ctypes.c_size_t),
                    ("max_working", ctypes.c_size_t), ("active_limit", wintypes.DWORD),
                    ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                    ("scheduling", wintypes.DWORD)]
    class IO(ctypes.Structure):
        _fields_ = [(name, ctypes.c_uint64) for name in
                    ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]
    class Extended(ctypes.Structure):
        _fields_ = [("basic", Basic), ("io", IO), ("process_memory", ctypes.c_size_t),
                    ("job_memory", ctypes.c_size_t), ("peak_process", ctypes.c_size_t),
                    ("peak_job", ctypes.c_size_t)]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
    kernel.CreateJobObjectW.restype = ctypes.c_void_p
    kernel.SetInformationJobObject.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    kernel.TerminateJobObject.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.CreateJobObjectW(None, None)
    if not handle:
        raise OSError("supervised lifetime job unavailable")
    limits = Extended()
    limits.basic.flags = 0x2000
    if not kernel.SetInformationJobObject(handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
        kernel.CloseHandle(handle)
        raise OSError("supervised lifetime job limits unavailable")
    return kernel, handle


def stop_child(process):
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       capture_output=True, timeout=15)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=15)


def launch(path, state, binding, evidence, executable):
    nonce = uuid.uuid4().hex
    result = path.parent / f"result-{nonce}.json"
    child_path = path.parent / f"child-{nonce}.json"
    payload_path = path.parent / f"launch-{nonce}.json"
    prompt = (f"Continue this authorized goal in a fresh headless context. Read {state['goal']}. "
              f"Completion: {state['completion']}. Authority: {state['authority']}. "
              f"Authorized actions: {json.dumps(state['actions'])}. "
              f"Owner: {state['owner_id']}; identity: {json.dumps(identity(Path(state['worktree'])))}. "
              f"Fresh delivery binding: {json.dumps(binding)}. Evidence: {json.dumps(evidence)}. "
              f"Next action: {state['next_action']}. Use L4. "
              f"Write a JSON checkpoint to {result} with nonce={nonce}, owner_id={state['owner_id']}, "
              "state waiting|complete|blocked, reason, next_action (required unless complete). "
              "If repairing HEAD, include rebind.old and rebind.new exact repo/worktree/branch/head "
              "identities and refresh the delivery binding. Successful process exit is not completion. "
              "For a PR, load persistent-delivery and honor its review/evidence/authority decisions. "
              "The supervisor already owns the writer and scheduler; do not recursively initialize, "
              "claim, register or wake this owner. Preserve user host safeguards. "
              "Do not claim same-chat continuation. Stop at an actual authority or human decision gate.")
    args = lane_command(state, prompt, executable)
    state.update(launch_nonce=nonce, launches=state["launches"] + 1, result_path=str(result),
                 child_path=str(child_path))
    transition(state, "working", "headless-launch", state["next_action"])
    atomic_json(payload_path, {"command": args, "child_path": str(child_path), "environment": {
        "CONTINUATION_RESULT_PATH": str(result), "CONTINUATION_NONCE": nonce,
        "CONTINUATION_OWNER_ID": state["owner_id"]}})
    with (path.parent / f"launch-{nonce}.log").open("wb") as output:
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "_child",
                                    "--owner", str(path), "--payload", str(payload_path)],
                                   stdout=output, stderr=output,
                                   start_new_session=os.name != "nt")
        state["child"] = {"pid": process.pid, "identity": process_identity(process.pid)}
        save(path, state, "launch")
        try:
            code = process.wait(timeout=min(state["timeout_seconds"], max(1, state["deadline"] - time.time())))
        except subprocess.TimeoutExpired:
            stop_child(process)
            code = -1
    state["child"] = None
    if code != 0:
        tail = (path.parent / f"launch-{nonce}.log").read_bytes()[-8192:].decode("utf-8", errors="replace").lower()
        if any(marker in tail for marker in ("model is not supported", "unsupported model", "not supported when using",
                "authentication required", "authentication failed", "not logged in", "invalid api key",
                "permission denied", "401 unauthorized", "approval required", "requires approval")):
            raise Gate("host-capability-or-permission-unavailable")
        raise RuntimeError(f"host-launch-exited-{code}")
    if not result.exists():
        raise RuntimeError("host-checkpoint-missing")
    apply_receipt(state, read(result))
    state["last_result"] = str(result)
    save(path, state, "checkpoint")


def failure(state, reason):
    state["failures"] += 1
    terminal = state["failures"] >= state["max_failures"] or state["launches"] >= state["max_launches"]
    transition(state, "blocked" if terminal else "waiting", reason,
               "Resolve transport/checkpoint failure and explicitly reconcile owner" if terminal
               else "Retry recorded action within remaining limits")
    state["retry"] = not terminal


def writer_records(state):
    yield state.get("child")
    if state.get("child_path") and Path(state["child_path"]).exists():
        yield read(state["child_path"])


def wake(path, state, args):
    if state["state"] in {"blocked", "complete"}:
        return
    if any(record and alive(record) for record in writer_records(state)):
        raise Gate("interrupted-writer-still-alive")
    if state.get("child"):
        if state.get("result_path") and Path(state["result_path"]).exists():
            apply_receipt(state, read(state["result_path"]))
            state["last_result"] = state["result_path"]
            state["child"] = None
            if state["state"] in {"blocked", "complete"}:
                return
        else:
            state["child"] = None
            failure(state, "interrupted-writer-without-checkpoint")
            return
    if time.time() >= state["deadline"]:
        transition(state, "blocked", "continuation-budget-exhausted", "Obtain renewed finite authority")
        return
    lease = state.get("foreground")
    if lease and alive(lease):
        if time.time() - lease["activity"] <= state["lease_seconds"]:
            return
        raise Gate("stale-live-foreground-reconciliation")
    state["foreground"] = None
    binding = check_identity(state)
    evidence = observe(state, binding, args.observer_command)
    token = fingerprint(evidence)
    retry = state.pop("retry", False)
    if evidence["kind"] == "pending" or (token == state.get("evidence") and not retry):
        transition(state, "waiting", "evidence-pending-or-unchanged", state["next_action"])
        state["evidence"] = token
        return
    if state["launches"] >= state["max_launches"]:
        transition(state, "blocked", "continuation-budget-exhausted", "Obtain renewed finite authority")
        return
    state["evidence"] = token
    launch(path, state, binding, evidence, args.host_command)


def initialize(path, args):
    if not args.root:
        raise Gate("init-root-required")
    root = Path(args.root).resolve()
    if Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise Gate("canonical-worktree-root-required")
    goal = Path(args.goal)
    goal = (root / goal).resolve() if not goal.is_absolute() else goal.resolve()
    if not goal.is_file() or not goal.is_relative_to(root):
        raise Gate("goal-must-exist-inside-worktree")
    if not args.authority.strip() or not args.completion.strip() or not all(a.strip() for a in args.actions):
        raise Gate("explicit-authority-completion-actions-required")
    bound = identity(root)
    if not bound["branch"]:
        raise Gate("detached-head-unsupported")
    owner_id = fingerprint([bound["repo"], str(root), str(goal)])[:24]
    if path.exists():
        state = read(path)
        if any(state.get(key) != value for key, value in {
                "owner_id": owner_id, "completion": args.completion, "actions": args.actions,
                "authority": args.authority, "harness": args.harness}.items()):
            raise Gate("existing-owner-authority-mismatch")
        check_identity(state)
        if min(args.max_launches, args.max_failures, args.deadline_hours, args.timeout_seconds, args.lease_seconds) <= 0:
            raise Gate("limits-must-be-positive")
        state["max_launches"] = min(state["max_launches"], args.max_launches)
        state["max_failures"] = min(state["max_failures"], args.max_failures)
        state["deadline"] = min(state["deadline"], time.time() + args.deadline_hours * 3600)
        state["timeout_seconds"] = min(state["timeout_seconds"], args.timeout_seconds)
        state["lease_seconds"] = min(state["lease_seconds"], args.lease_seconds)
        save(path, state, "registration-preserved")
        return state
    now = time.time()
    state = dict(bound, owner_id=owner_id, goal=str(goal), completion=args.completion,
                 actions=args.actions, authority=args.authority, harness=args.harness,
                 state="waiting", reason="accepted", next_action="Resume canonical authorized goal",
                 launches=0, failures=0, evidence=None, foreground=None, child=None,
                 max_launches=min(6, args.max_launches), max_failures=min(3, args.max_failures),
                 deadline=now + min(24, args.deadline_hours) * 3600,
                 timeout_seconds=min(900, args.timeout_seconds), lease_seconds=min(300, args.lease_seconds),
                 host_executable=args.host_executable)
    if min(state["max_launches"], state["max_failures"], args.deadline_hours,
           args.timeout_seconds, args.lease_seconds) <= 0:
        raise Gate("limits-must-be-positive")
    save(path, state, "init")
    return state


def operate(path, state, args):
    operation = args.operation
    if operation == "wake":
        try:
            wake(path, state, args)
        except Gate as error:
            transition(state, "blocked", str(error), "Explicitly reconcile recorded identity or owner")
        except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as error:
            failure(state, str(error))
    elif operation == "claim":
        check_identity(state)
        lease = state.get("foreground")
        if lease and alive(lease):
            raise Gate("foreground-already-owned")
        if any(record and alive(record) for record in writer_records(state)):
            raise Gate("headless-writer-already-owned")
        pid = args.pid or os.getppid()
        creation = process_identity(pid)
        if creation is None or creation == "unknown":
            raise Gate("foreground-process-identity-unavailable")
        state["foreground"] = {"pid": pid, "identity": creation, "activity": time.time(),
                               "token": uuid.uuid4().hex}
        transition(state, "working", "foreground-owned", state["next_action"])
    else:
        lease = state.get("foreground")
        if not lease or args.token != lease["token"] or not alive(lease):
            raise Gate("foreground-token-invalid")
        if operation == "heartbeat":
            lease["activity"] = time.time()
        elif operation == "yield":
            state["foreground"] = None
            transition(state, "waiting", args.reason or "foreground-yielded", args.next_action or state["next_action"])
        elif operation == "checkpoint":
            receipt = {"nonce": state.get("launch_nonce"), "owner_id": state["owner_id"],
                       "state": args.state, "reason": args.reason, "next_action": args.next_action}
            if args.rebind:
                receipt["rebind"] = read(args.rebind)
            apply_receipt(state, receipt)
            state["foreground"] = None
    save(path, state, operation)


def parser():
    result = argparse.ArgumentParser()
    subs = result.add_subparsers(dest="operation", required=True)
    for name in ("init", "claim", "heartbeat", "yield", "checkpoint", "status", "wake", "_child"):
        p = subs.add_parser(name)
        p.add_argument("--root")
        p.add_argument("--owner")
        if name == "init":
            p.add_argument("--goal", required=True)
            p.add_argument("--completion", required=True)
            p.add_argument("--actions", nargs="+", required=True)
            p.add_argument("--authority", required=True)
            p.add_argument("--harness", choices=("codex", "claude"), required=True)
            p.add_argument("--host-executable")
            for flag, default, kind in (("max-launches", 6, int), ("max-failures", 3, int),
                                       ("deadline-hours", 24, float), ("timeout-seconds", 900, float),
                                       ("lease-seconds", 300, float)):
                p.add_argument(f"--{flag}", type=kind, default=default)
        if name == "claim":
            p.add_argument("--pid", type=int)
        if name in {"heartbeat", "yield", "checkpoint"}:
            p.add_argument("--token", required=True)
            p.add_argument("--reason", default="")
            p.add_argument("--next-action", default="")
        if name == "checkpoint":
            p.add_argument("--state", choices=("waiting", "blocked", "complete"), required=True)
            p.add_argument("--rebind")
        if name == "wake":
            p.add_argument("--observer-command", nargs="+")
            p.add_argument("--host-command", nargs="+")
        if name == "_child":
            p.add_argument("--payload", required=True)
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    if args.operation == "_child":
        return child(args)
    if not args.root and not args.owner:
        raise Gate("root-or-owner-required")
    path = Path(args.owner).resolve() if args.owner else Path(args.root).resolve() / ".agents/continuation/owner.json"
    root = Path(args.root).resolve() if args.root else Path(read(path)["worktree"]).resolve()
    expected = root / ".agents/continuation/owner.json"
    if path != expected or path.parent.resolve() != expected.parent:
        raise Gate("canonical-owner-path-required")
    if Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise Gate("canonical-worktree-root-required")
    if args.operation == "status":
        print(json.dumps(read(path), sort_keys=True))
        return 0
    with locked(path.parent) as acquired:
        if not acquired:
            print(json.dumps({"state": "working", "reason": "owner-lock-busy"}))
            return 0
        state = initialize(path, args) if args.operation == "init" else read(path)
        if args.operation != "init":
            operate(path, state, args)
        print(json.dumps(state, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (Gate, OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(json.dumps({"state": "blocked", "reason": str(error)}))
        sys.exit(2)
