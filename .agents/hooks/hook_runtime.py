"""Shared runtime helpers for plugin-delivered and vendored hook copies."""

import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path


PLUGIN_ROOT_VARIABLES = ("PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT", "CODEX_PLUGIN_ROOT")
CLAIM_PREFIX = "agents-hook-"
CLAIM_RETENTION_SECONDS = 7 * 24 * 60 * 60
CLAIM_PRUNE_INTERVAL_SECONDS = 60 * 60
PRUNE_LOCK_NAME = f"{CLAIM_PREFIX}prune.lock"
PRUNE_MARKER_NAME = f"{CLAIM_PREFIX}last-pruned"
COMMAND_TIMEOUT_SECONDS = 5
NETWORK_COMMAND_TIMEOUT_SECONDS = 10
TEARDOWN_TIMEOUT_SECONDS = 1
CREATE_SUSPENDED = 0x00000004


class CommandTimeout(RuntimeError):
    """A hook's child process outlived its ceiling."""


def _windows_job():
    import ctypes
    from ctypes import wintypes

    class Basic(ctypes.Structure):
        _fields_ = [
            ("process_time", ctypes.c_int64),
            ("job_time", ctypes.c_int64),
            ("flags", wintypes.DWORD),
            ("min_working", ctypes.c_size_t),
            ("max_working", ctypes.c_size_t),
            ("active_limit", wintypes.DWORD),
            ("affinity", ctypes.c_size_t),
            ("priority", wintypes.DWORD),
            ("scheduling", wintypes.DWORD),
        ]

    class IO(ctypes.Structure):
        _fields_ = [
            (name, ctypes.c_uint64)
            for name in (
                "read_ops",
                "write_ops",
                "other_ops",
                "read_bytes",
                "write_bytes",
                "other_bytes",
            )
        ]

    class Extended(ctypes.Structure):
        _fields_ = [
            ("basic", Basic),
            ("io", IO),
            ("process_memory", ctypes.c_size_t),
            ("job_memory", ctypes.c_size_t),
            ("peak_process", ctypes.c_size_t),
            ("peak_job", ctypes.c_size_t),
        ]

    class Accounting(ctypes.Structure):
        _fields_ = [
            ("total_user", ctypes.c_int64),
            ("total_kernel", ctypes.c_int64),
            ("period_user", ctypes.c_int64),
            ("period_kernel", ctypes.c_int64),
            ("page_faults", wintypes.DWORD),
            ("total_processes", wintypes.DWORD),
            ("active_processes", wintypes.DWORD),
            ("terminated_processes", wintypes.DWORD),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
    kernel.CreateJobObjectW.restype = ctypes.c_void_p
    kernel.SetInformationJobObject.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    kernel.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel.TerminateJobObject.argtypes = [ctypes.c_void_p, wintypes.UINT]
    kernel.TerminateJobObject.restype = wintypes.BOOL
    kernel.QueryInformationJobObject.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p]
    kernel.QueryInformationJobObject.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.CreateJobObjectW(None, None)
    if not handle:
        raise OSError("owned command job unavailable")
    limits = Extended()
    limits.basic.flags = 0x2000
    if not kernel.SetInformationJobObject(handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
        kernel.CloseHandle(handle)
        raise OSError("owned command job limits unavailable")
    return kernel, handle, Accounting


def _resume_windows_process(process):
    import ctypes

    ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
    ntdll.NtResumeProcess.argtypes = [ctypes.c_void_p]
    ntdll.NtResumeProcess.restype = ctypes.c_long
    if ntdll.NtResumeProcess(int(process._handle)) != 0:
        raise OSError("cannot resume owned command")


def _rendered_command(command):
    return command if isinstance(command, str) else " ".join(str(part) for part in command)


def _drain_owned_process(process, job):
    import ctypes

    deadline = time.monotonic() + TEARDOWN_TIMEOUT_SECONDS
    if job is not None:
        kernel, handle, accounting_type = job
        if not kernel.TerminateJobObject(handle, 1):
            raise OSError("cannot terminate owned command job")
        while True:
            accounting = accounting_type()
            if not kernel.QueryInformationJobObject(
                handle, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None
            ):
                raise OSError("cannot inspect owned command job")
            if accounting.active_processes == 0:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError("owned command job did not drain")
            time.sleep(0.01)
    elif os.name == "nt":
        try:
            process.terminate()
        except ProcessLookupError:
            pass
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        process.communicate(timeout=max(0.01, deadline - time.monotonic()))
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("owned command pipes did not drain") from error
    if job is None and os.name != "nt":
        while True:
            try:
                os.killpg(process.pid, 0)
            except ProcessLookupError:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError("owned command group did not drain")
            time.sleep(0.01)


def run_command(command, timeout=COMMAND_TIMEOUT_SECONDS, **kwargs):
    """Run a hook command within an invocation-owned process tree."""
    deadline = time.monotonic() + timeout
    check = kwargs.pop("check", False)
    capture_output = kwargs.pop("capture_output", False)
    input_data = kwargs.pop("input", None)
    if capture_output:
        if "stdout" in kwargs or "stderr" in kwargs:
            raise ValueError("stdout and stderr arguments may not be used with capture_output")
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    if input_data is not None:
        if "stdin" in kwargs:
            raise ValueError("stdin and input arguments may not both be used")
        kwargs["stdin"] = subprocess.PIPE

    job = None
    process = None
    job_assigned = False
    drained = False
    try:
        if os.name == "nt":
            job = _windows_job()
            flags = kwargs.pop("creationflags", subprocess.CREATE_NO_WINDOW)
            process = subprocess.Popen(
                command, creationflags=flags | CREATE_SUSPENDED, **kwargs
            )
            kernel, handle, _ = job
            if not kernel.AssignProcessToJobObject(handle, int(process._handle)):
                raise OSError("cannot assign owned command to job")
            job_assigned = True
            _resume_windows_process(process)
        else:
            kwargs["start_new_session"] = True
            process = subprocess.Popen(command, **kwargs)

        try:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(command, timeout)
            stdout, stderr = process.communicate(input_data, timeout=remaining)
        except subprocess.TimeoutExpired:
            _drain_owned_process(process, job)
            drained = True
            raise CommandTimeout(f"`{_rendered_command(command)}` exceeded {timeout}s") from None
        completed = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
        if check:
            completed.check_returncode()
        return completed
    except BaseException:
        if process is not None and not drained:
            try:
                _drain_owned_process(process, job if job_assigned else None)
            except BaseException:
                pass
        raise
    finally:
        if job is not None:
            job[0].CloseHandle(job[1])


def declared_plugin_root(hook_file):
    """Return the injected plugin root only for its exact ``hooks/<running-hook>`` copy."""
    hook = Path(hook_file).resolve()
    for name in PLUGIN_ROOT_VARIABLES:
        value = os.environ.get(name)
        if not value:
            continue
        try:
            root = Path(value).resolve()
        except OSError:
            continue
        if (root / "hooks" / hook.name).resolve() == hook:
            return root
    return None


def own_payload_root(hook_file):
    """Resolve the payload beside a hook without depending on a harness variable name."""
    root = declared_plugin_root(hook_file)
    if root is not None:
        return root
    return Path(hook_file).resolve().parent.parent


def _invocation_identity(data, hook_name):
    session = data.get("session_id") or data.get("sessionId")
    if not session:
        return None

    tool_use = data.get("tool_use_id") or data.get("toolUseId")
    if tool_use:
        return f"{hook_name}\0{session}\0tool\0{tool_use}"

    event = data.get("hook_event_name") or data.get("hookEventName")
    if not event:
        return None
    turn = data.get("turn_id") or data.get("turnId")
    if not turn:
        transcript = data.get("transcript_path") or data.get("transcriptPath")
        if not transcript:
            return None
        try:
            stat = Path(transcript).stat()
        except OSError:
            return None
        turn = f"transcript:{Path(transcript).resolve()}:{stat.st_size}:{stat.st_mtime_ns}"
    retry = bool(data.get("stop_hook_active") or data.get("stopHookActive"))
    message = data.get("last_assistant_message") or data.get("lastAssistantMessage") or ""
    digest = hashlib.sha256(str(message).encode("utf-8", errors="replace")).hexdigest()
    return f"{hook_name}\0{session}\0{turn}\0{event}\0{retry}\0{digest}"


def _try_acquire_prune_lock(directory):
    """Take the shared pruning lock without delaying hook enforcement."""
    path = directory / PRUNE_LOCK_NAME
    descriptor = None
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_RDWR)
        if os.name == "nt":
            import msvcrt

            if os.fstat(descriptor).st_size == 0:
                os.write(descriptor, b"\0")
            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        return None
    return descriptor


def _release_prune_lock(descriptor):
    try:
        try:
            if os.name == "nt":
                import msvcrt

                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(descriptor, fcntl.LOCK_UN)
        except OSError:
            pass
    finally:
        try:
            os.close(descriptor)
        except OSError:
            pass


def _pruning_is_due(marker, now):
    try:
        last_pruned = marker.stat().st_mtime
    except OSError:
        return True
    return last_pruned > now or now - last_pruned >= CLAIM_PRUNE_INTERVAL_SECONDS


def _remove_expired_claims(directory, current_path, cutoff):
    for path in directory.glob(f"{CLAIM_PREFIX}*.claim"):
        if path == current_path:
            continue
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
        except OSError:
            continue


def _prune_stale_claims(directory, current_path):
    """Periodically remove expired claims without racing another pruner or the current claim."""
    marker = directory / PRUNE_MARKER_NAME
    if not _pruning_is_due(marker, time.time()):
        return

    descriptor = _try_acquire_prune_lock(directory)
    if descriptor is None:
        return
    try:
        now = time.time()
        if not _pruning_is_due(marker, now):
            return
        _remove_expired_claims(directory, current_path, now - CLAIM_RETENTION_SECONDS)
        try:
            marker.touch(exist_ok=True)
            os.utime(marker, (now, now))
        except OSError:
            pass
    finally:
        _release_prune_lock(descriptor)


def claim_invocation(data, hook_name):
    """Atomically select one of duplicate plugin/project registrations for this event.

    A consuming repo keeps vendored hooks so enforcement exists on an unprovisioned machine. An
    installed plugin registers the same mechanisms. Both receive the same hook invocation id; the
    first copy claims it and the other exits neutrally. If a harness supplies no stable id, do not
    deduplicate: preserving enforcement is more important than avoiding an extra process.
    """
    identity = _invocation_identity(data, hook_name)
    if identity is None:
        return True
    key = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    directory = Path(tempfile.gettempdir())
    path = directory / f"{CLAIM_PREFIX}{key}.claim"
    _prune_stale_claims(directory, path)
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    except OSError:
        return True
    try:
        os.write(descriptor, json.dumps({"hook": hook_name}).encode("utf-8"))
    finally:
        os.close(descriptor)
    return True
