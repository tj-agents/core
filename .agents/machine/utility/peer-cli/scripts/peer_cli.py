"""List, resolve and safely close registered Claude/Codex sessions (Python 3.9+)."""
import argparse
import os
import signal
import sys
from pathlib import Path
import register_session
import session_close


def repo_root(path):
    code, output, _ = session_close.git(path, "rev-parse", "--show-toplevel")
    return Path(output).resolve() if code == 0 else None


def scoped(items, all_items, under):
    if all_items:
        return items
    root = Path(under).resolve() if under else repo_root(os.getcwd())
    root = root.parent if root and not under else root
    return items if root is None else [item for item in items if not item.get("cwd") or session_close.under_or_equal(item["cwd"], root)]


def records():
    result = []
    for _path, entry in session_close.entries():
        value = dict(entry)
        value["alive"] = session_close.liveness(value)
        result.append(value)
    return result


def unrecorded(items):
    known = {item.get("pid") for item in items}
    if sys.platform != "linux":
        return []
    found = []
    for directory in Path("/proc").iterdir():
        if not directory.name.isdigit():
            continue
        pid = int(directory.name)
        if pid in known:
            continue
        info = session_close.process_info(pid)
        if info and Path(info.name).stem.casefold() in register_session.read_host_names():
            found.append({"pid": pid, "title": None, "session_id": None, "cwd": None,
                          "alive": True, "recorded": False})
    return found


def select(items, needle):
    exact = [item for item in items if needle in (item.get("session_id"), item.get("title"))]
    matches = exact or [item for item in items if item.get("title") and item["title"].casefold().startswith(needle.casefold())]
    if len(matches) != 1:
        raise session_close.Refusal("no unique session matches; use list and an exact session id")
    return matches[0]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("list", "resolve", "close"))
    parser.add_argument("session", nargs="?")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--under")
    parser.add_argument("--include-unrecorded", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    items = records()
    if args.include_unrecorded:
        items += unrecorded(items)
    if args.action == "list":
        for item in scoped(items, args.all, args.under):
            print("{title}\t{session}\t{alive}\t{pid}\t{cwd}".format(title=item.get("title") or "", session=item.get("session_id") or "", alive="?" if item["alive"] is None else item["alive"], pid=item.get("pid", ""), cwd=item.get("cwd") or ""))
        return 0
    if not args.session:
        parser.error("resolve and close require a session title or id")
    target = select(items, args.session)
    if args.action == "resolve":
        print(target["session_id"])
        return 0
    if target["alive"] is False:
        print("already gone")
        return 0
    if target["alive"] is not True:
        raise session_close.Refusal("liveness is unknown; refusing to kill an unverified identity")
    if not args.force and input("Close {!r} (pid {})? [y/N] ".format(target.get("title") or target["session_id"], target["pid"])).strip().casefold() not in ("y", "yes"):
        print("Left running.")
        return 0
    if not session_close.verified_live(target["pid"], target.get("pid_started_at")):
        raise session_close.Refusal("host identity changed before close")
    os.kill(target["pid"], signal.SIGTERM)
    print("Closed {!r}.".format(target.get("title") or target["session_id"]))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except session_close.Refusal as error:
        print("peer-cli: " + str(error), file=sys.stderr)
        raise SystemExit(2)
