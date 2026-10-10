"""Close one exact, verified terminal tab without focus keystrokes (Python 3.9+)."""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
import session_close


class TerminalRefusal(RuntimeError):
    pass


def run(command):
    return subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)


def close_entry(entry):
    if not session_close.verified_live(entry.get("pid"), entry.get("pid_started_at")):
        raise TerminalRefusal("registered host identity is not currently verified live")
    identity = entry.get("terminal")
    if not isinstance(identity, dict):
        raise TerminalRefusal("no native terminal identity was recorded")
    kind = identity.get("kind")
    if kind == "kitty":
        window, listen = identity.get("window_id"), identity.get("listen_on")
        if not window or not listen:
            raise TerminalRefusal("kitty identity is incomplete")
        inventory = run(["kitty", "@", "--to", listen, "ls"])
        if inventory.returncode or '"id": ' + str(window) not in inventory.stdout:
            raise TerminalRefusal("the exact kitty window no longer exists")
        result = run(["kitty", "@", "--to", listen, "close-window", "--match", "id:" + str(window)])
    elif kind == "tmux":
        pane = identity.get("pane_id")
        if not pane or run(["tmux", "display-message", "-p", "-t", pane, "#{pane_id}"]).stdout.strip() != pane:
            raise TerminalRefusal("the exact tmux pane no longer exists")
        result = run(["tmux", "kill-pane", "-t", pane])
    elif kind == "konsole":
        qdbus = shutil.which("qdbus") or shutil.which("qdbus-qt5")
        session = identity.get("session")
        if not qdbus or not session or not identity.get("window"):
            raise TerminalRefusal("Konsole needs qdbus and its exact registered session/window")
        result = run([qdbus, "org.kde.konsole", "/Sessions/" + str(session), "org.kde.konsole.Session.close"])
    elif kind == "windows-terminal":
        adapter = Path(__file__).with_name("windows_terminal_uia.ps1")
        tab = identity.get("automation_id")
        if os.name != "nt" or not tab or not adapter.is_file():
            raise TerminalRefusal("Windows Terminal has no recorded exact UI Automation tab identity")
        result = run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(adapter), "-TabId", str(tab)])
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
        print(json.dumps([{"session_id": item.get("session_id"), "title": item.get("title"), "terminal": item.get("terminal"), "live": session_close.liveness(item)} for _path, item in session_close.entries() if item.get("terminal")], sort_keys=True))
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
