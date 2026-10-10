#!/usr/bin/env python3
"""Register deterministic, receipt-owned delivery continuation wakes (Python 3.9+)."""

import sys

if sys.version_info < (3, 9):
    raise RuntimeError("delivery_continuation requires Python 3.9 or later")

import argparse
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess


def resource(name):
    here = Path(__file__).resolve()
    for directory in (here.parent, *here.parents):
        for relative in ("workflows", ".agents/workflows"):
            candidate = directory / relative / name
            if candidate.is_file():
                return candidate
    raise RuntimeError("continuation resource unavailable: " + name)


SCHEDULER_PATH = resource("continuation_scheduler.py")
spec = importlib.util.spec_from_file_location("continuation_scheduler", SCHEDULER_PATH)
scheduler = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = scheduler
spec.loader.exec_module(scheduler)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def owner_path(args):
    if args.owner:
        path = Path(args.owner)
        if not path.is_absolute():
            raise scheduler.SchedulerError("owner path must be absolute")
        return path.resolve()
    if args.worktree:
        path = Path(args.worktree)
        if not path.is_absolute():
            raise scheduler.SchedulerError("worktree must be absolute")
        return path.resolve() / ".agents/continuation/owner.json"
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                            encoding="utf-8", timeout=10, check=False)
    if result.returncode:
        raise scheduler.SchedulerError("specify --worktree or --owner outside a git checkout")
    return Path(result.stdout.strip()).resolve() / ".agents/continuation/owner.json"


def load_owner(path, requested_worktree=None):
    if not path.is_file():
        raise scheduler.SchedulerError("continuation owner is missing: " + str(path))
    owner = read_json(path)
    owner_id = owner.get("owner_id")
    worktree = owner.get("worktree")
    if not isinstance(owner_id, str) or not owner_id.strip() or owner.get("harness") not in {"codex", "claude"}:
        raise scheduler.SchedulerError("invalid continuation runtime owner")
    if not isinstance(worktree, str) or not Path(worktree).is_absolute():
        raise scheduler.SchedulerError("owner worktree must be absolute")
    root = Path(worktree).resolve()
    if not root.is_dir() or path != root / ".agents/continuation/owner.json":
        raise scheduler.SchedulerError("canonical owner path or worktree is invalid")
    if requested_worktree and Path(requested_worktree).resolve() != root:
        raise scheduler.SchedulerError("worktree does not match continuation owner")
    return owner, root


def existing_host(owner, explicit, windows=None):
    pinned = owner.get("host_executable")
    if pinned and explicit and Path(pinned).resolve() != Path(explicit).resolve():
        raise scheduler.SchedulerError("explicit host executable differs from the owner pin")
    value = pinned or explicit
    if not value:
        raise scheduler.SchedulerError("register requires --host-executable or a pinned owner host executable")
    path = Path(value)
    if not path.is_absolute() or not path.is_file():
        raise scheduler.SchedulerError("pinned host executable must be an existing absolute path")
    windows = os.name == "nt" if windows is None else windows
    if windows:
        if path.suffix.lower() != ".exe":
            raise scheduler.SchedulerError("pinned Windows host executable must be a native .exe")
    elif not os.access(str(path), os.X_OK):
        raise scheduler.SchedulerError("pinned POSIX host executable must have execute permission")
    return str(path.resolve())


def prerequisites(owner, host):
    runtime = resource("continuation_runtime.py")
    python = Path(sys.executable).resolve()
    if not python.is_file() or not runtime.is_file() or not Path(host).is_file():
        raise scheduler.SchedulerError("registered continuation prerequisite is missing")
    package = runtime.parent.parent
    if not (package / "lanes" / (owner["harness"] + ".json")).is_file() and not (package / ".agents/lanes" / (owner["harness"] + ".json")).is_file():
        raise scheduler.SchedulerError("package is missing selected host lane resource")
    return runtime, python


def receipt_for(owner, path, interval, host, windows=None):
    runtime, python = prerequisites(owner, host)
    windows = os.name == "nt" if windows is None else windows
    if windows:
        return scheduler.windows_receipt(owner, path, __file__, runtime, python, host, interval, os.environ)
    return scheduler.linux_receipt(owner, path, __file__, runtime, python, host, interval, os.environ)


LEGACY_WINDOWS_SCRIPT = r'''$ErrorActionPreference='Stop';[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);$tasks=@(Get-ScheduledTask|Where-Object {$_.TaskPath -ceq '\' -and $_.TaskName.StartsWith('AgentStandards-Delivery-',[StringComparison]::OrdinalIgnoreCase)}|ForEach-Object {[pscustomobject]@{TaskName=$_.TaskName;TaskPath=$_.TaskPath;Actions=@($_.Actions|Select-Object WorkingDirectory)}});[pscustomobject]@{Tasks=$tasks}|ConvertTo-Json -Compress'''


def legacy_conflict(root, transport, windows=None):
    windows = os.name == "nt" if windows is None else windows
    if not windows:
        return
    result = transport.run([scheduler._powershell(), "-NoProfile", "-NonInteractive", "-Command",
                            LEGACY_WINDOWS_SCRIPT], timeout=8)
    if result.returncode:
        detail = (result.stderr or result.stdout or "").strip()
        raise scheduler.SchedulerError("legacy ScheduledTasks query failed" + ((": " + detail) if detail else ""))
    try:
        payload = json.loads(result.stdout)
    except ValueError as error:
        raise scheduler.SchedulerError("legacy ScheduledTasks query returned invalid JSON") from error
    tasks = payload.get("Tasks") if isinstance(payload, dict) else None
    if not isinstance(tasks, list):
        raise scheduler.SchedulerError("legacy ScheduledTasks query returned invalid entries")
    for task in tasks:
        for action in task.get("Actions", []) if isinstance(task, dict) else []:
            if scheduler.exact_path(action.get("WorkingDirectory")) == str(root):
                raise scheduler.SchedulerError("legacy delivery task targets this worktree; inspect and retire it explicitly")


def write_linux(receipt, owner_path, owner, root, transport):
    scheduler.assert_linux_write_paths(receipt)
    service, timer = scheduler.linux_units(receipt)
    transport.write(receipt["service_path"], service)
    transport.write(receipt["timer_path"], timer)
    scheduler._result(transport, ["systemctl", "--user", "daemon-reload"], timeout=15)
    if not scheduler.verify_linux_ownership(receipt, owner_path, owner, root, transport):
        raise scheduler.SchedulerError("scheduler differs from its exact ownership receipt after reload; preserving transaction evidence")
    scheduler._result(transport, ["systemctl", "--user", "enable", "--now", receipt["timer_unit"]], timeout=15)


def write_windows(receipt, transport):
    payload = {"operation": "register", "task_name": receipt["task_name"], "execute": receipt["execute"],
               "arguments": receipt["arguments"], "worktree": receipt["worktree"],
               "interval": receipt["interval_minutes"], "description": receipt["description"]}
    scheduler._result(transport, [scheduler._powershell(), "-NoProfile", "-NonInteractive", "-Command", scheduler.WINDOWS_SCRIPT],
                      input_text=json.dumps(payload), timeout=20)


def scheduler_missing(receipt, transport, windows=None):
    windows = scheduler.receipt_is_windows(receipt) if windows is None else windows
    if windows:
        try:
            return scheduler._windows_task(receipt, transport) is None
        except scheduler.SchedulerError:
            raise
    for path in (receipt["service_path"], receipt["timer_path"]):
        try:
            transport.read(path)
            return False
        except FileNotFoundError:
            continue
    return True


def remove_platform(receipt, transport, windows=None):
    windows = scheduler.receipt_is_windows(receipt) if windows is None else windows
    if windows:
        scheduler._result(transport, [scheduler._powershell(), "-NoProfile", "-NonInteractive", "-Command", scheduler.WINDOWS_SCRIPT],
                          input_text=json.dumps({"operation": "remove", "task_name": receipt["task_name"]}), timeout=15)
        return
    # Do not stop the service: terminal cleanup can be executing inside it.
    scheduler._result(transport, ["systemctl", "--user", "disable", "--now", receipt["timer_unit"]], timeout=15)
    service, timer = scheduler.linux_units(receipt)
    for path, expected in ((receipt["service_path"], service), (receipt["timer_path"], timer)):
        if not scheduler._unit_matches(transport, path, expected, scheduler.unit_hash(expected)):
            raise scheduler.SchedulerError("scheduler differs from its exact ownership receipt; refusing to change it")
    link = Path(receipt["timer_enable_path"])
    if link.exists() or link.is_symlink():
        if not link.is_symlink() or not scheduler._link_points_to(link, Path(receipt["timer_path"])):
            raise scheduler.SchedulerError("timer enable link differs from its exact ownership receipt")
    transport.remove(receipt["timer_path"])
    transport.remove(receipt["service_path"])
    if link.is_symlink():
        transport.remove(link)
    scheduler._result(transport, ["systemctl", "--user", "daemon-reload"], timeout=15)


def register(owner, root, path, args, transport, windows=None):
    windows = os.name == "nt" if windows is None else windows
    if owner.get("state") in {"blocked", "complete"}:
        raise scheduler.SchedulerError("a terminal owner cannot be scheduled")
    host = existing_host(owner, args.host_executable, windows=windows)
    proposed = receipt_for(owner, path, args.interval_minutes, host, windows=windows)
    receipt_path, pending_path = path.parent / "scheduler.json", path.parent / "scheduler.pending.json"
    current = scheduler.reconcile_pending(pending_path, receipt_path, path, owner, root, transport,
                                          windows=windows, dry_run=args.dry_run)
    stale_current = None
    if current and not scheduler.verify_ownership(current, path, owner, root, transport, windows=windows):
        if not scheduler_missing(current, transport, windows=windows):
            raise scheduler.SchedulerError("scheduler differs from its exact ownership receipt; refusing to change it")
        stale_current = current
        current = None
    if not current and not windows:
        for candidate in (proposed["service_path"], proposed["timer_path"]):
            try:
                transport.read(candidate)
            except FileNotFoundError:
                continue
            raise scheduler.SchedulerError("existing systemd unit has no matching receipt; refusing to overwrite it")
    if not current and windows and not scheduler_missing(proposed, transport, windows=windows):
        raise scheduler.SchedulerError("existing scheduled task has no matching receipt; refusing to overwrite it")
    if not windows:
        scheduler._validate_linux_recovery_evidence((stale_current, current, proposed), transport)
    legacy_conflict(root, transport, windows=windows)
    if args.dry_run:
        return {"action": "register", "dry_run": True, "proposed": proposed, "previous": current}
    scheduler.atomic_json(pending_path, {"previous": stale_current or current, "proposed": proposed,
                                         "previous_missing": stale_current is not None})
    if windows:
        write_windows(proposed, transport)
    else:
        scheduler.systemd_available(transport)
        write_linux(proposed, path, owner, root, transport)
    if not scheduler.verify_receipt(proposed, path, owner, root, transport, windows=windows):
        raise scheduler.SchedulerError("scheduler registration did not verify as enabled and active")
    scheduler.atomic_json(receipt_path, proposed)
    pending_path.unlink()
    return {"action": "register", "registered": proposed.get("timer_unit", proposed.get("task_name"))}


def remove(owner, root, path, args, transport, windows=None):
    receipt_path, pending_path = path.parent / "scheduler.json", path.parent / "scheduler.pending.json"
    recorded = read_json(receipt_path) if receipt_path.exists() else None
    platform_windows = scheduler.receipt_is_windows(recorded) if recorded is not None else (os.name == "nt" if windows is None else windows)
    receipt = scheduler.reconcile_pending(pending_path, receipt_path, path, owner, root, transport,
                                          windows=platform_windows, dry_run=args.dry_run)
    if receipt is None:
        return {"action": "remove", "removed": False}
    receipt_windows = scheduler.receipt_is_windows(receipt)
    owned = scheduler.verify_ownership(receipt, path, owner, root, transport, windows=receipt_windows)
    missing = scheduler_missing(receipt, transport, windows=receipt_windows)
    if not owned and not missing:
        raise scheduler.SchedulerError("scheduler differs from its exact ownership receipt; refusing to change it")
    if args.dry_run:
        return {"action": "remove", "dry_run": True, "receipt": receipt}
    if owned:
        remove_platform(receipt, transport, windows=receipt_windows)
    receipt_path.unlink()
    try:
        pending_path.unlink()
    except FileNotFoundError:
        pass
    return {"action": "remove", "removed": True}


def wake_environment(receipt):
    environment = dict(os.environ)
    for name in scheduler.CONTROL_VARIABLES:
        environment.pop(name, None)
    environment.update(receipt.get("profile_environment", {}))
    return environment


def terminal_pending_is_owned(path, receipt, owner, root):
    pending_path = path.parent / "scheduler.pending.json"
    try:
        pending = read_json(pending_path)
    except FileNotFoundError:
        return pending_path
    if not isinstance(pending, dict):
        raise scheduler.SchedulerError("terminal cleanup found invalid pending scheduler evidence")
    candidates = (pending.get("previous"), pending.get("proposed"))
    if receipt not in candidates or any(candidate is not None and not scheduler._same_owner(candidate, path, owner, root)
                                        for candidate in candidates):
        raise scheduler.SchedulerError("terminal cleanup found foreign pending scheduler evidence")
    return pending_path


def wake(owner, root, path, args, transport):
    receipt_path = path.parent / "scheduler.json"
    if not receipt_path.exists():
        raise scheduler.SchedulerError("scheduled wake requires an exact registration receipt")
    receipt = read_json(receipt_path)
    receipt_windows = scheduler.receipt_is_windows(receipt)
    host = existing_host(owner, args.host_executable, windows=receipt_windows)
    if receipt.get("host_executable") != host:
        raise scheduler.SchedulerError("registered host executable differs from the owner host pin")
    runtime, python = prerequisites(owner, host)
    if receipt.get("script") != str(Path(__file__).resolve()):
        raise scheduler.SchedulerError("wake adapter does not match this invocation's pinned script")
    if scheduler.exact_path(receipt.get("helper")) != str(runtime.resolve()) or scheduler.exact_path(receipt.get("python")) != str(python):
        raise scheduler.SchedulerError("wake package resources do not match canonical helper and Python")
    if receipt.get("adapter_command") != scheduler.adapter_command(receipt):
        raise scheduler.SchedulerError("wake adapter command is not the exact pinned adapter invocation")
    if receipt.get("runtime_command") != scheduler.runtime_command(receipt):
        raise scheduler.SchedulerError("wake runtime command is not the exact pinned runtime invocation")
    if not scheduler.verify_receipt(receipt, path, owner, root, transport,
                                    windows=receipt_windows):
        raise scheduler.SchedulerError("registered continuation scheduler is unavailable, disabled, or mismatched")
    for item in ("helper", "python", "script", "host_executable"):
        if not Path(receipt[item]).is_file():
            raise scheduler.SchedulerError("registered package prerequisite is missing: " + receipt[item])
    if args.dry_run:
        return {"action": "wake", "dry_run": True}
    result = subprocess.run(receipt["runtime_command"], cwd=str(root), capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=930, env=wake_environment(receipt), check=False)
    if result.returncode:
        raise scheduler.SchedulerError("continuation runtime wake failed with exit code " + str(result.returncode))
    state = read_json(path)
    if state.get("state") in {"blocked", "complete"}:
        pending_path = terminal_pending_is_owned(path, receipt, owner, root)
        remove_platform(receipt, transport, windows=receipt_windows)
        receipt_path.unlink()
        try:
            pending_path.unlink()
        except FileNotFoundError:
            pass
    return {"action": "wake", "state": state.get("state")}


def list_registrations(transport):
    if os.name == "nt":
        result = scheduler._result(transport, [scheduler._powershell(), "-NoProfile", "-NonInteractive", "-Command",
            "[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);Get-ScheduledTask -TaskName 'AgentStandards-Continuation-*' -ErrorAction SilentlyContinue|Select-Object TaskName,TaskPath,State,Description|ConvertTo-Json -Compress"], timeout=8)
        try:
            entries = json.loads(result.stdout) if result.stdout.strip() else []
        except ValueError as error:
            raise scheduler.SchedulerError("ScheduledTasks list returned invalid JSON") from error
        return {"platform": "windows-scheduledtasks", "entries": entries if isinstance(entries, list) else [entries]}
    scheduler.systemd_available(transport)
    result = scheduler._result(transport, ["systemctl", "--user", "list-timers", "--all", "--no-legend", "--plain",
                                            "agent-standards-continuation-*.timer"], timeout=10)
    return {"platform": "linux-systemd", "entries": [line for line in result.stdout.splitlines() if line.strip()]}


def parser():
    result = argparse.ArgumentParser()
    result.add_argument("command", choices=("register", "remove", "list", "wake"), nargs="?", default="list")
    result.add_argument("--owner")
    result.add_argument("--worktree")
    result.add_argument("--interval-minutes", type=int, default=20, choices=range(5, 721))
    result.add_argument("--reason", default="")
    result.add_argument("--host-executable")
    result.add_argument("--dry-run", action="store_true")
    return result


def main(argv=None, transport=None):
    args = parser().parse_args(argv)
    transport = transport or scheduler.SchedulerTransport()
    if args.command == "list":
        print(json.dumps(list_registrations(transport), sort_keys=True))
        return 0
    path = owner_path(args)
    owner, root = load_owner(path, args.worktree)
    lock = contextlib.nullcontext(True) if args.dry_run else scheduler.lifecycle_lock(path.parent)
    with lock as acquired:
        if not acquired:
            raise scheduler.SchedulerError("another scheduler lifecycle operation holds this owner")
        if args.command == "register":
            result = register(owner, root, path, args, transport)
        elif args.command == "remove":
            result = remove(owner, root, path, args, transport)
        else:
            result = wake(owner, root, path, args, transport)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (scheduler.SchedulerError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(json.dumps({"state": "blocked", "reason": str(error)}))
        raise SystemExit(2)
