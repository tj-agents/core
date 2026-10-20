#!/usr/bin/env python3
"""Remove linked worktrees whose work is merged, clean and no longer in use (Python 3.9+).

A worktree is removed only when no live registered session works inside it, no open pull request uses its
branch as a base, and cleanup_proof.py proves its pull request merged at exactly its head with the merge
commit on the default branch. Leftover changes in a proven worktree are archived by cleanup_proof.py under
<state>/merge-cleanup/set-aside/ before removal. Everything else is kept and reported. Safe to run at any
time, as often as wanted.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cleanup_proof

GIT_TIMEOUT_SECONDS = 60
GH_TIMEOUT_SECONDS = 60
STILL_ACTIVE = 259
RECENT_EDIT_SECONDS = 30 * 60
ORPHAN_AGE_SECONDS = 10 * 60


class UnreadableSessions(Exception):
    pass


def state_directory() -> Path:
    return Path(os.environ.get("AGENT_STATE_DIRECTORY") or Path.home() / ".agents-state")


def git(cwd: Path, *arguments: str) -> subprocess.CompletedProcess:
    command = ["git", "-C", str(cwd), *arguments]
    try:
        return subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=GIT_TIMEOUT_SECONDS, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        return subprocess.CompletedProcess(command, 1, "", str(error))


def process_alive(pid: object) -> bool:
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            return bool(kernel32.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def session_rows(database: Path) -> list[sqlite3.Row]:
    if not database.exists():
        return []
    try:
        connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True, timeout=5)
    except sqlite3.Error as error:
        raise UnreadableSessions(f"cannot open {database}: {error}") from error
    try:
        connection.row_factory = sqlite3.Row
        return list(connection.execute("SELECT cwd, pid, ended_at FROM sessions"))
    except sqlite3.Error as error:
        raise UnreadableSessions(f"cannot read {database}: {error}") from error
    finally:
        connection.close()


def inside(child: str, parent: Path) -> bool:
    try:
        Path(child).resolve().relative_to(parent.resolve())
    except (OSError, ValueError):
        return False
    return True


def live_session_directories(rows: list[sqlite3.Row], alive=process_alive) -> list[str]:
    return [row["cwd"] for row in rows
            if row["ended_at"] is None and isinstance(row["cwd"], str) and alive(row["pid"])]


def parse_worktrees(porcelain: str) -> list[dict]:
    worktrees, current = [], {}
    for line in porcelain.splitlines() + [""]:
        if not line:
            if current:
                worktrees.append(current)
            current = {}
        elif line.startswith("worktree "):
            current["path"] = line[len("worktree "):]
        elif line.startswith("HEAD "):
            current["head"] = line[len("HEAD "):]
        elif line.startswith("branch refs/heads/"):
            current["branch"] = line[len("branch refs/heads/"):]
    return worktrees


def primary_checkout(directory: Path) -> Path | None:
    if not directory.is_dir():
        return None
    result = git(directory, "worktree", "list", "--porcelain")
    if result.returncode:
        return None
    worktrees = parse_worktrees(result.stdout)
    return Path(worktrees[0]["path"]).resolve() if worktrees else None


def discover_repositories(rows: list[sqlite3.Row]) -> list[Path]:
    seen: dict[str, Path] = {}
    for directory in sorted({row["cwd"] for row in rows if isinstance(row["cwd"], str)}):
        primary = primary_checkout(Path(directory))
        if primary is not None:
            seen.setdefault(str(primary).casefold(), primary)
    return list(seen.values())


def bases_an_open_pull_request(primary: Path, branch: str) -> bool:
    try:
        result = subprocess.run(["gh", "pr", "list", "--state", "open", "--base", branch, "--json", "number"],
                                cwd=primary, capture_output=True, text=True, encoding="utf-8", errors="replace",
                                timeout=GH_TIMEOUT_SECONDS, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return True
    if result.returncode:
        return True
    try:
        return bool(json.loads(result.stdout or "[]"))
    except ValueError:
        return True


def proven_removable(primary: Path, worktree: dict, archive: bool = True) -> tuple[bool, str]:
    try:
        default = cleanup_proof.default_branch(primary)
    except cleanup_proof.Preserve as error:
        return False, error.reason
    arguments = argparse.Namespace(worktree=worktree["path"], branch=worktree["branch"], head=worktree["head"],
                                   pr=None, default=default, repo=None)
    output = io.StringIO()
    previous = Path.cwd()
    try:
        os.chdir(worktree["path"] if archive else primary)
        with contextlib.redirect_stdout(output):
            code = cleanup_proof.run(arguments)
    except cleanup_proof.Preserve as error:
        return False, error.reason
    except (OSError, subprocess.SubprocessError) as error:
        return False, f"proof error: {error}"
    finally:
        os.chdir(previous)
    lines = output.getvalue().splitlines()
    if code == 0 and lines and lines[0] == "removable":
        return True, "merged"
    reason = lines[0].removeprefix("preserve: ") if lines else "proof failed"
    if not archive and reason.endswith("has uncommitted or untracked changes"):
        return True, "merged, leftovers would be archived"
    return False, reason


def recently_edited(worktree: Path, now: float | None = None) -> bool:
    status = git(worktree, "status", "--porcelain=v1", "--untracked-files=all", "-z")
    if status.returncode:
        return True
    limit = (now if now is not None else time.time()) - RECENT_EDIT_SECONDS
    for record in status.stdout.split("\0"):
        if len(record) > 3:
            try:
                if (worktree / record[3:]).stat().st_mtime >= limit:
                    return True
            except OSError:
                continue
    return False


def is_link(path: Path) -> bool:
    try:
        info = os.lstat(path)
    except OSError:
        return False
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & reparse)


def unlink_links(root: Path) -> list[Path]:
    removed, pending = [], [root]
    while pending:
        directory = pending.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError:
            continue
        for entry in entries:
            path = Path(entry.path)
            if is_link(path):
                for unlink in ((os.rmdir, os.unlink) if os.name == "nt" else (os.unlink,)):
                    try:
                        unlink(path)
                        removed.append(path)
                        break
                    except OSError:
                        continue
            elif entry.is_dir(follow_symlinks=False):
                pending.append(path)
    return removed


def remove(primary: Path, worktree: dict) -> tuple[bool, str]:
    target = Path(worktree["path"])
    unlink_links(target)
    result = git(primary, "worktree", "remove", "--", str(target))
    registered = result.returncode != 0 and any(
        Path(entry["path"]).resolve() == target.resolve()
        for entry in parse_worktrees(git(primary, "worktree", "list", "--porcelain").stdout))
    if registered:
        return False, "removal failed, retried next run: " + (result.stderr.strip().splitlines() or ["?"])[-1]
    tip = git(primary, "rev-parse", "--verify", "refs/heads/" + worktree["branch"]).stdout.strip()
    if tip != worktree["head"]:
        return True, "removed; branch kept because it moved past the proven commit"
    try:
        default = cleanup_proof.default_branch(primary)
    except cleanup_proof.Preserve:
        return True, "removed; branch kept because the default branch is unknown"
    contained = git(primary, "merge-base", "--is-ancestor", "refs/heads/" + worktree["branch"],
                    "origin/" + default).returncode == 0
    git(primary, "branch", "-d" if contained else "-D", worktree["branch"])
    if target.exists():
        return True, "removed; its empty folder stays until the process using it exits"
    return True, "removed"


def remove_empty_orphans(primary: Path, registered: list[dict], now: float | None = None) -> list[str]:
    root = primary / ".worktrees"
    if not root.is_dir():
        return []
    known = {Path(entry["path"]).resolve() for entry in registered if entry.get("path")}
    removed = []
    limit = (now if now is not None else time.time()) - ORPHAN_AGE_SECONDS
    for child in root.iterdir():
        if (child.is_dir() and not is_link(child) and child.resolve() not in known
                and child.stat().st_mtime < limit and not any(child.iterdir())):
            try:
                child.rmdir()
                removed.append(str(child))
            except OSError:
                pass
    return removed


def sweep_repository(primary: Path, live: list[str], removable=proven_removable, based=bases_an_open_pull_request,
                     delete=remove, edited=recently_edited) -> dict[str, str]:
    listing = git(primary, "worktree", "list", "--porcelain")
    if listing.returncode:
        return {}
    worktrees = parse_worktrees(listing.stdout)
    outcomes: dict[str, str] = {path: "removed empty leftover folder"
                                for path in remove_empty_orphans(primary, worktrees)}
    for worktree in worktrees[1:]:
        path = worktree.get("path")
        if not path or not Path(path).is_dir():
            continue
        if "branch" not in worktree or "head" not in worktree:
            outcomes[path] = "kept: detached"
            continue
        if any(inside(directory, Path(path)) for directory in live):
            outcomes[path] = "kept: a session is working in it"
            continue
        if edited(Path(path)):
            outcomes[path] = "kept: changed files were edited in the last 30 minutes"
            continue
        if based(primary, worktree["branch"]):
            outcomes[path] = "kept: an open pull request is based on its branch"
            continue
        ok, reason = removable(primary, worktree)
        if not ok:
            outcomes[path] = "kept: " + reason
            continue
        try:
            _done, result = delete(primary, worktree)
        except (OSError, subprocess.SubprocessError) as error:
            result = f"kept: removal error, retried next run: {error}"
        outcomes[path] = result
    return outcomes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", action="append", default=[],
                        help="primary checkout to sweep; default: every repository a recorded session used")
    parser.add_argument("--dry-run", action="store_true", help="report what would be removed without removing it")
    arguments = parser.parse_args(argv)
    try:
        rows = session_rows(state_directory() / "sessions.db")
    except UnreadableSessions as error:
        print(json.dumps({"error": f"nothing removed: {error}"}))
        return 1
    live = live_session_directories(rows)
    repositories = [primary for primary in (primary_checkout(Path(value)) for value in arguments.repo) if primary]
    if not arguments.repo:
        repositories = discover_repositories(rows)
    if arguments.dry_run:
        report = {str(primary): sweep_repository(
            primary, live, removable=lambda root, worktree: proven_removable(root, worktree, archive=False),
            delete=lambda root, worktree: (True, "would remove")) for primary in repositories}
    else:
        report = {str(primary): sweep_repository(primary, live) for primary in repositories}
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
