import argparse
import ctypes
import json
import math
import os
import signal
import subprocess
import sys
import threading
import time


def deny(reason):
    response = {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                "permissionDecision": "deny", "permissionDecisionReason": reason}}
    sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    return 0


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
        raise OSError("hook lifetime job unavailable")
    limits = Extended()
    limits.basic.flags = 0x2000
    if not kernel.SetInformationJobObject(handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
        kernel.CloseHandle(handle)
        raise OSError("hook lifetime job limits unavailable")
    return kernel, handle


def read_object():
    data = bytearray()
    depth = 0
    quoted = escaped = started = False
    while True:
        chunk = sys.stdin.buffer.read1(4096)
        if not chunk:
            raise ValueError("incomplete JSON object")
        for index, byte in enumerate(chunk):
            data.append(byte)
            if not started:
                if byte in b" \t\r\n":
                    continue
                if byte != ord("{"):
                    raise ValueError("expected a JSON object")
                started = True
            if quoted:
                if escaped:
                    escaped = False
                elif byte == ord("\\"):
                    escaped = True
                elif byte == ord('"'):
                    quoted = False
            elif byte == ord('"'):
                quoted = True
            elif byte in b"{[":
                depth += 1
            elif byte in b"}]":
                depth -= 1
                if depth == 0:
                    value = json.loads(data.decode("utf-8"))
                    if not isinstance(value, dict) or chunk[index + 1:].strip():
                        raise ValueError("expected one JSON object")
                    return bytes(data)


def run_until(action, deadline):
    done = threading.Event()
    result = []

    def run():
        try:
            result.append((True, action()))
        except Exception as error:
            result.append((False, error))
        finally:
            done.set()

    threading.Thread(target=run, daemon=True).start()
    if not done.wait(max(0, deadline - time.monotonic())):
        raise TimeoutError()
    okay, value = result[0]
    if not okay:
        raise value
    return value


def stop_tree(state, deadline):
    job = state.get("job")
    process = state.get("process")
    if job:
        job[0].CloseHandle(job[1])
    elif process:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if process:
        try:
            process.wait(timeout=max(0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            pass


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=12)
    parser.add_argument("script")
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    try:
        args = parser.parse_args()
    except SystemExit:
        return deny("The Codex pre-tool hook has invalid adapter arguments.")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        return deny(f"The Codex pre-tool hook {args.script} has an invalid timeout.")
    deadline = started + args.timeout
    active_deadline = deadline - min(0.5, args.timeout / 4)
    state = {}
    cancelled = threading.Event()
    lock = threading.Lock()
    stage = "input"
    failure = result = None

    def execute(payload):
        if cancelled.is_set():
            raise TimeoutError()
        if os.name == "nt":
            job = windows_job()
            with lock:
                if cancelled.is_set():
                    job[0].CloseHandle(job[1])
                    raise TimeoutError()
                state["job"] = job
        process = subprocess.Popen(
            [sys.executable, "-B", args.script, *args.arguments],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=(subprocess.CREATE_NO_WINDOW | 4) if os.name == "nt" else 0,
            start_new_session=os.name != "nt",
        )
        with lock:
            state["process"] = process
            if cancelled.is_set():
                process.kill()
                if os.name != "nt":
                    os.killpg(process.pid, signal.SIGKILL)
                raise TimeoutError()
            if os.name == "nt":
                kernel, handle = state["job"]
                if not kernel.AssignProcessToJobObject(handle, int(process._handle)):
                    process.kill()
                    raise OSError("cannot assign hook to lifetime job")
                ntdll = ctypes.WinDLL("ntdll")
                ntdll.NtResumeProcess.argtypes = [ctypes.c_void_p]
                if ntdll.NtResumeProcess(int(process._handle)) != 0:
                    raise OSError("cannot resume hook")
        stdout, stderr = process.communicate(payload)
        return process.returncode, stdout, stderr

    try:
        payload = run_until(read_object, active_deadline)
        stage = "child execution/output collection"
        result = run_until(lambda: execute(payload), active_deadline)
    except TimeoutError:
        failure = f"The Codex pre-tool hook {args.script} timed out during {stage}."
    except Exception as error:
        failure = f"The Codex pre-tool hook {args.script} failed during {stage}: {error}"
    finally:
        with lock:
            cancelled.set()
        stop_tree(state, deadline - min(0.1, args.timeout / 20))

    def output():
        if failure:
            return deny(failure)
        code, stdout, stderr = result
        if code == 0:
            sys.stdout.buffer.write(stdout)
            sys.stdout.buffer.flush()
            sys.stderr.buffer.write(stderr)
            sys.stderr.buffer.flush()
            return 0
        detail = stderr.decode("utf-8", errors="replace").strip()
        if code == 2:
            return deny(detail or f"The Codex pre-tool hook {args.script} denied this tool call.")
        return deny(f"The Codex pre-tool hook {args.script} failed with exit code {code}: {detail}".strip())

    try:
        return run_until(output, deadline)
    except TimeoutError:
        return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    os._exit(main())
