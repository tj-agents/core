"""Bind managed Codex launches to their frontend process (Python 3.9+)."""

import json
import math
import os
from pathlib import Path
import re
import secrets
import subprocess
import time


TOKEN_ENV = "TJ_AGENTS_CLI_CLIENT"
TOKEN_KEY = "shell_environment_policy.set." + TOKEN_ENV
TOKEN = re.compile(r"[0-9a-f]{64}\Z")
OTHER_COMMANDS = {
    "agents", "login", "logout", "mcp", "plugin", "app-server", "remote-control", "app",
    "completion", "update", "doctor", "sandbox", "debug", "apply", "a", "queue", "archive",
    "delete", "migrate-rollouts", "migrate-nfs-db", "unarchive", "cloud", "exec-server", "features", "help",
}
VALUE_OPTIONS = {
    "-c", "--config", "-i", "--image", "-m", "--model", "-p", "--profile", "-s", "--sandbox",
    "-a", "--ask-for-approval", "-C", "--cd", "--add-dir", "--enable", "--disable",
    "--remote", "--remote-auth-token-env", "--local-provider",
}


def command_position(arguments):
    index = 0
    while index < len(arguments):
        value = arguments[index]
        if value == "--":
            return None
        option, separator, _value = value.partition("=")
        attached = len(value) > 2 and value[:2] in VALUE_OPTIONS
        if option in VALUE_OPTIONS:
            index += 1 if separator else 2
        elif attached or value.startswith("-"):
            index += 1
        else:
            return index
    return None


def command_name(arguments):
    index = command_position(arguments)
    return arguments[index] if index is not None else None


def is_session(arguments):
    options = arguments[:arguments.index("--")] if "--" in arguments else arguments
    return (not any(value in {"--help", "-h", "--version", "-V"} for value in options)
            and command_name(arguments) not in OTHER_COMMANDS)


def profile_directory(environ=None):
    values = os.environ if environ is None else environ
    return Path(values.get("CODEX_HOME") or Path.home() / ".codex").resolve()


def binding_path(token):
    if not isinstance(token, str) or TOKEN.fullmatch(token) is None:
        raise RuntimeError("Invalid CLI client binding token")
    state = Path(os.environ.get("AGENT_STATE_DIRECTORY") or Path.home() / ".agents-state")
    return state / "cli-clients" / (token + ".json")


def prepare(host, arguments, project, environment):
    values = dict(environment)
    values.pop(TOKEN_ENV, None)
    arguments = list(arguments)
    if host != "codex" or not is_session(arguments):
        return arguments, values, None
    token = secrets.token_hex(32)
    ticket = {
        "schema_version": 1, "token": token, "host": host,
        "profile": str(profile_directory(values)), "launch_cwd": str(Path(project).resolve()),
        "created_at": time.time(),
        "title": values.get("AGENT_CLI_TAB_TITLE"),
        "terminal_environment": {key: values[key] for key in (
            "TMUX", "TMUX_PANE", "KITTY_WINDOW_ID", "KITTY_LISTEN_ON", "KONSOLE_DBUS_SERVICE",
            "KONSOLE_DBUS_SESSION", "KONSOLE_DBUS_WINDOW", "WT_SESSION", "AGENT_WINDOWS_TERMINAL_TAB_ID",
        ) if key in values},
    }
    return ["--config", TOKEN_KEY + '="' + token + '"', *arguments], values, ticket


def attach(ticket, pid):
    if ticket is None:
        return
    path = binding_path(ticket["token"])
    path.parent.mkdir(parents=True, exist_ok=True)
    value = {**ticket, "pid": pid, "recorded_at": time.time()}
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    ticket["_attached"] = True
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True)
        stream.write("\n")


def release(ticket):
    if ticket is not None and ticket.get("_attached"):
        binding_path(ticket["token"]).unlink(missing_ok=True)


def resolve(token, lookup, command_arguments):
    path = binding_path(token)
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise RuntimeError("The managed CLI client binding is unavailable") from error
    if not isinstance(record, dict):
        raise RuntimeError("The managed CLI client binding is invalid")
    times = [record.get(key) for key in ("created_at", "recorded_at")]
    if (record.get("schema_version") != 1 or record.get("token") != token
            or record.get("host") != "codex"
            or not isinstance(record.get("profile"), str)
            or not isinstance(record.get("launch_cwd"), str)
            or Path(record.get("profile", "")).resolve() != profile_directory()
            or type(record.get("pid")) is not int or record["pid"] <= 0
            or not all(type(value) in (int, float) and math.isfinite(value) and value > 0 for value in times)
            or times[0] > times[1]):
        raise RuntimeError("The managed CLI client binding does not match this profile")
    info = lookup(record["pid"])
    if info is None or Path(info.name).stem.casefold() != "codex":
        raise RuntimeError("The managed Codex client is no longer running")
    arguments = command_arguments(info.pid)
    expected = TOKEN_KEY + '="' + token + '"'
    if (expected not in arguments or not is_session(arguments[1:])
            or type(info.started_at) not in (int, float) or not math.isfinite(info.started_at)
            or not times[0] - 2 <= info.started_at <= times[1] + 2):
        raise RuntimeError("The recorded process is not this managed Codex frontend")
    return info, record


def process_arguments(pid):
    if os.name != "nt":
        return [value.decode("utf-8", errors="surrogateescape")
                for value in (Path("/proc") / str(pid) / "cmdline").read_bytes().split(b"\0") if value]
    import ctypes
    from ctypes import wintypes

    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
         "(Get-CimInstance Win32_Process -Filter 'ProcessId = %d').CommandLine | ConvertTo-Json -Compress" % pid],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10, check=True,
    )
    line = json.loads(result.stdout)
    if not isinstance(line, str):
        raise RuntimeError("Native client command line is unavailable")
    api = ctypes.WinDLL("shell32", use_last_error=True)
    api.CommandLineToArgvW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    api.CommandLineToArgvW.restype = ctypes.POINTER(wintypes.LPWSTR)
    count = ctypes.c_int()
    values = api.CommandLineToArgvW(line, ctypes.byref(count))
    if not values:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return [values[index] for index in range(count.value)]
    finally:
        kernel = ctypes.WinDLL("kernel32")
        kernel.LocalFree.argtypes = [ctypes.c_void_p]
        kernel.LocalFree(values)


def resumed_session(arguments):
    values = arguments[1:]
    index = command_position(values)
    if index is not None and values[index] == "resume":
        return command_name(values[index + 1:])
    return None


def process_profile(pid):
    if os.name != "nt":
        entries = (Path("/proc") / str(pid) / "environ").read_bytes().split(b"\0")
        values = dict(entry.split(b"=", 1) for entry in entries if b"=" in entry)
        return Path(os.fsdecode(values.get(b"CODEX_HOME", os.fsencode(Path.home() / ".codex")))).resolve()
    import ctypes
    from ctypes import wintypes

    if ctypes.sizeof(ctypes.c_void_p) != 8:
        raise RuntimeError("Reading an unmanaged Codex client requires 64-bit Python on Windows")

    class Basic(ctypes.Structure):
        _fields_ = [("reserved", ctypes.c_void_p), ("peb", ctypes.c_void_p),
                    ("reserved2", ctypes.c_void_p * 2), ("pid", ctypes.c_size_t), ("reserved3", ctypes.c_void_p)]

    class Region(ctypes.Structure):
        _fields_ = [("base", ctypes.c_void_p), ("allocation", ctypes.c_void_p), ("protection", wintypes.DWORD),
                    ("size", ctypes.c_size_t), ("state", wintypes.DWORD), ("protect", wintypes.DWORD),
                    ("kind", wintypes.DWORD)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    native = ctypes.WinDLL("ntdll")
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                       ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    kernel.VirtualQueryEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.POINTER(Region), ctypes.c_size_t]
    kernel.VirtualQueryEx.restype = ctypes.c_size_t
    native.NtQueryInformationProcess.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p,
                                                wintypes.ULONG, ctypes.c_void_p]
    handle = kernel.OpenProcess(0x410, False, pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        basic = Basic()
        if native.NtQueryInformationProcess(handle, 0, ctypes.byref(basic), ctypes.sizeof(basic), None):
            raise RuntimeError("Native client process information is unavailable")

        def read(address, size):
            buffer = ctypes.create_string_buffer(size)
            done = ctypes.c_size_t()
            if not kernel.ReadProcessMemory(handle, address, buffer, size, ctypes.byref(done)):
                raise ctypes.WinError(ctypes.get_last_error())
            return buffer.raw[:done.value]

        parameters = int.from_bytes(read(basic.peb + 0x20, 8), "little")
        address = int.from_bytes(read(parameters + 0x80, 8), "little")
        region = Region()
        if not kernel.VirtualQueryEx(handle, address, ctypes.byref(region), ctypes.sizeof(region)):
            raise ctypes.WinError(ctypes.get_last_error())
        raw = read(address, min(65536, region.base + region.size - address))
        end = next((index + 4 for index in range(0, len(raw) - 3, 2) if raw[index:index + 4] == b"\0" * 4), None)
        if end is None:
            raise RuntimeError("Native client environment is incomplete")
        text = raw[:end].decode("utf-16-le")
        for entry in text.split("\0"):
            if not entry:
                break
            key, separator, value = entry.partition("=")
            if key.casefold() == "codex_home" and separator:
                return Path(value).resolve()
        return Path.home().joinpath(".codex").resolve()
    finally:
        kernel.CloseHandle(handle)
