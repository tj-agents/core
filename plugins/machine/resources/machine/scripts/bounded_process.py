from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile


class WindowsJob:
    def __init__(self):
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.api.CreateJobObjectW.restype = wintypes.HANDLE
        self.api.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.api.AssignProcessToJobObject.restype = wintypes.BOOL
        self.api.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self.api.TerminateJobObject.restype = wintypes.BOOL
        self.api.CloseHandle.argtypes = [wintypes.HANDLE]
        self.api.CloseHandle.restype = wintypes.BOOL
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())

    def assign(self, process: subprocess.Popen) -> None:
        if not self.api.AssignProcessToJobObject(self.handle, wintypes.HANDLE(int(process._handle))):
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self) -> None:
        try:
            if not self.api.TerminateJobObject(self.handle, 124):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            self.api.CloseHandle(self.handle)


def stop_tree(process: subprocess.Popen, job: WindowsJob | None) -> None:
    if job is None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    else:
        job.close()
    if process.poll() is None:
        process.kill()
    process.wait(timeout=5)


def run(command: list[str], cwd: Path | None = None, timeout: float = 60,
        env: dict[str, str] | None = None) -> tuple[int | None, str, str]:
    if timeout <= 0:
        return None, "", "refresh time budget exhausted"
    options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as error:
        job = WindowsJob() if os.name == "nt" else None
        process = None
        try:
            launched = [sys.executable, "-B", str(Path(__file__).resolve()), "--child", *command] if job else command
            process = subprocess.Popen(
                launched, cwd=cwd, env=env, stdin=subprocess.PIPE if job else subprocess.DEVNULL,
                stdout=output, stderr=error, **options,
            )
            if job is not None:
                job.assign(process)
                process.stdin.write(b"1")
                process.stdin.close()
            code = process.wait(timeout=timeout)
            output.seek(0)
            error.seek(0)
            return code, output.read().decode("utf-8", "replace"), error.read().decode("utf-8", "replace")
        except subprocess.TimeoutExpired:
            return None, "", f"timed out after {timeout:g}s"
        except OSError as failure:
            return None, "", str(failure)
        finally:
            if process is not None:
                stop_tree(process, job)
            elif job is not None:
                job.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    arguments = parser.parse_args(argv)
    command = arguments.command
    if command[:1] == ["--"]:
        command = command[1:]
    if not command:
        parser.error("a command is required")
    environment = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    code, output, error = run(command, timeout=arguments.timeout, env=environment)
    sys.stdout.write(output)
    sys.stderr.write(error)
    return code if code is not None else 124


if __name__ == "__main__":
    if sys.argv[1:2] == ["--child"]:
        if sys.stdin.buffer.read(1) != b"1":
            sys.exit(124)
        sys.exit(subprocess.call(sys.argv[2:], stdin=subprocess.DEVNULL,
                                 creationflags=subprocess.CREATE_NO_WINDOW))
    sys.exit(main())
