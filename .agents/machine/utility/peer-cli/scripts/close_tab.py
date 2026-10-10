"""Close one exact, verified terminal tab without focus keystrokes (Python 3.9+)."""
import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path
import session_close


class TerminalRefusal(RuntimeError):
    pass


def run(command):
    try:
        return subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8", check=False,
            timeout=session_close.SUBPROCESS_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise TerminalRefusal("terminal control command failed: " + str(error)) from error


def host_belongs_to(entry, roots):
    if not session_close.verified_live(entry.get("pid"), entry.get("pid_started_at")):
        return False
    target = entry["pid"]
    seen = set()
    while target not in seen:
        if target in roots:
            return True
        seen.add(target)
        info = session_close.process_info(target)
        if info is None:
            return False
        target = info.ppid
    return False


def exact_process(value):
    try:
        pid = int(value)
    except (TypeError, ValueError):
        return None
    return session_close.process_info(pid)


def kitty_target(identity):
    result = run(["kitty", "@", "--to", identity["listen_on"], "ls"])
    if result.returncode:
        raise TerminalRefusal((result.stderr or result.stdout or "kitty inventory failed").strip())
    try:
        inventory = json.loads(result.stdout)
    except ValueError as error:
        raise TerminalRefusal("kitty returned malformed inventory") from error
    matches = []
    for os_window in inventory if isinstance(inventory, list) else []:
        for tab in os_window.get("tabs", []):
            for window in tab.get("windows", []):
                if str(window.get("id")) == str(identity["window_id"]):
                    matches.append((tab, window))
    if len(matches) != 1:
        raise TerminalRefusal("the exact kitty window is absent or ambiguous")
    return matches[0]


def tmux_target(identity):
    command = ["tmux"]
    if identity.get("socket"):
        command.extend(["-S", identity["socket"]])
    command.extend(["list-panes", "-a", "-F", "#{pane_id}\t#{pane_pid}"])
    result = run(command)
    if result.returncode:
        raise TerminalRefusal((result.stderr or result.stdout or "tmux inventory failed").strip())
    matches = []
    for line in result.stdout.splitlines():
        pane, separator, pid = line.partition("\t")
        if separator and pane == identity.get("pane_id"):
            matches.append((pane, exact_process(pid)))
    if len(matches) != 1 or matches[0][1] is None:
        raise TerminalRefusal("the exact tmux pane no longer has a queryable root process")
    return matches[0]


def windows_inventory():
    if os.name != "nt":
        return None
    adapter = Path(__file__).with_name("windows_terminal_uia.ps1")
    if not adapter.is_file():
        raise TerminalRefusal("Windows Terminal adapter is unavailable")
    result = run([
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(adapter),
        "-Json",
    ])
    if result.returncode:
        raise TerminalRefusal((result.stderr or result.stdout or "Windows Terminal inventory failed").strip())
    try:
        value = json.loads(result.stdout or "[]")
    except ValueError as error:
        raise TerminalRefusal("Windows Terminal returned malformed inventory") from error
    return value if isinstance(value, list) else []


def close_entry(entry, force=False):
    identity = entry.get("terminal")
    if not isinstance(identity, dict):
        raise TerminalRefusal("no native terminal identity was recorded")
    kind = identity.get("kind")
    live = session_close.liveness(entry)
    if live is None:
        raise TerminalRefusal("registered host identity is unknown")
    if kind == "kitty":
        window, listen = identity.get("window_id"), identity.get("listen_on")
        if not window or not listen:
            raise TerminalRefusal("kitty identity is incomplete")
        if live is not True:
            raise TerminalRefusal("a stale kitty window cannot be safely attributed after its host exited")
        _tab, target = kitty_target(identity)
        roots = [target.get("pid")]
        roots.extend(item.get("pid") for item in target.get("foreground_processes", [])
                     if isinstance(item, dict))
        root_pids = [info.pid for item in roots if (info := exact_process(item))]
        if not host_belongs_to(entry, root_pids):
            raise TerminalRefusal("registered host is not owned by the exact kitty window")
        result = run(["kitty", "@", "--to", listen, "close-window", "--match", "id:" + str(window)])
    elif kind == "tmux":
        if live is not True:
            raise TerminalRefusal("a stale tmux pane cannot be safely attributed after its host exited")
        pane, root = tmux_target(identity)
        if not host_belongs_to(entry, [root.pid]):
            raise TerminalRefusal("registered host is not owned by the exact tmux pane")
        command = ["tmux"]
        if identity.get("socket"):
            command.extend(["-S", identity["socket"]])
        command.extend(["kill-pane", "-t", pane])
        result = run(command)
    elif kind == "konsole":
        if live is not True:
            raise TerminalRefusal("a stale Konsole session cannot be safely attributed after its host exited")
        qdbus = shutil.which("qdbus6") or shutil.which("qdbus") or shutil.which("qdbus-qt5")
        service = identity.get("service")
        session = identity.get("session")
        if not qdbus or not service or not session or not str(session).startswith("/"):
            raise TerminalRefusal("Konsole needs qdbus6/qdbus and its recorded service and full session path")
        roots = []
        for method in ("org.kde.konsole.Session.processId", "org.kde.konsole.Session.foregroundProcessId"):
            queried = run([qdbus, service, session, method])
            if queried.returncode:
                raise TerminalRefusal((queried.stderr or queried.stdout or "Konsole query failed").strip())
            info = exact_process(queried.stdout.strip())
            if info:
                roots.append(info.pid)
        if not host_belongs_to(entry, roots):
            raise TerminalRefusal("registered host is not owned by the exact Konsole session")
        try:
            os.kill(roots[0], signal.SIGTERM)
        except OSError as error:
            raise TerminalRefusal("could not signal the exact Konsole terminal process: " + str(error)) from error
        result = subprocess.CompletedProcess([], 0)
    elif kind == "windows-terminal":
        adapter = Path(__file__).with_name("windows_terminal_uia.ps1")
        tab = identity.get("automation_id")
        if os.name != "nt" or not adapter.is_file():
            raise TerminalRefusal("Windows Terminal control is available only on Windows")
        if tab:
            arguments = ["-TabId", str(tab)]
        else:
            title = entry.get("title")
            matched = [item for _path, item in session_close.entries() if item.get("title") == title]
            if not title or len(matched) != 1:
                raise TerminalRefusal("Windows Terminal fallback requires a unique registered tab title")
            arguments = ["-Title", title]
        result = run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(adapter), *arguments])
    else:
        raise TerminalRefusal("unsupported terminal kind")
    if result.returncode:
        raise TerminalRefusal((result.stderr or result.stdout or "terminal refused close").strip())


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--session")
    args = parser.parse_args(argv)
    if args.list:
        actual = windows_inventory()
        if actual is None:
            actual = [{"session_id": item.get("session_id"), "title": item.get("title"),
                       "terminal": item.get("terminal"), "live": session_close.liveness(item)}
                      for _path, item in session_close.entries() if item.get("terminal")]
        print(json.dumps(actual, sort_keys=True))
        return 0
    if not args.session:
        parser.error("--session is required unless --list is used")
    found = [item for _path, item in session_close.entries() if item.get("session_id") == args.session]
    if len(found) != 1:
        raise TerminalRefusal("the requested session is absent or ambiguous")
    close_entry(found[0])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except TerminalRefusal as error:
        print("close-tab: " + str(error), file=sys.stderr)
        raise SystemExit(2)
