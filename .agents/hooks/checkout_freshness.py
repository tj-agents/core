"""Tell a starting session when its checkout is behind the remote default branch.

SessionStart runs this once per session on both hosts. It fetches `origin` within a
short timeout, fast-forwards a clean default branch, and reports a feature branch
that is behind, whether it has shipped and the next action. It also reports a
checkout without the plugin selection its default branch carries, because no
repository plugin loads in that session. A failure is a one-line notice or nothing;
it never blocks a session and never rewrites a feature branch.
"""

from __future__ import annotations

import json
import subprocess
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from tj_cli import process

FETCH_SECONDS = 5.0
LOOKUP_SECONDS = 4.0
GIT_SECONDS = 3.0
TOTAL_SECONDS = 12.0
REMOTE = "origin"
SELECTION = ".agents/plugins.json"
SYNC = "engineering:sync-checkout"
SHIPPED_STATES = frozenset({"MERGED", "CLOSED"})
FAILURES = (OSError, UnicodeError, ValueError, RuntimeError, subprocess.SubprocessError)
QUIET = ("-c", "credential.interactive=never")


@dataclass(frozen=True, slots=True)
class Result:
    code: int
    out: str
    err: str


@dataclass(frozen=True, slots=True)
class Checkout:
    top: Path
    deadline: float

    def run(
        self, program: str, *arguments: str, limit: float = GIT_SECONDS
    ) -> Result | None:
        timeout = min(limit, self.deadline - time.monotonic())
        if timeout <= 0:
            return None
        git = [program, *QUIET, "-C", str(self.top)]
        prefix = git if program == "git" else [program]
        try:
            completed = process.run(
                [*prefix, *arguments],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                cwd=str(self.top),
                stdin=subprocess.DEVNULL,
            )
        except FAILURES:
            return None
        return Result(
            completed.returncode, completed.stdout or "", completed.stderr or ""
        )

    def git(self, *arguments: str, limit: float = GIT_SECONDS) -> str | None:
        result = self.run("git", *arguments, limit=limit)
        if result is None or result.code != 0:
            return None
        return result.out.strip()

    def succeeds(self, *arguments: str) -> bool:
        result = self.run("git", *arguments)
        return result is not None and result.code == 0


@dataclass(frozen=True, slots=True)
class Fetched:
    checkout: Checkout
    branch: str
    had_selection: bool
    failure: str


def first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def commits(count: int) -> str:
    return f"{count} commit" + ("" if count == 1 else "s")


def fetched(directory: Path, deadline: float) -> Fetched | None:
    probe = Checkout(directory, deadline)
    output = probe.git("rev-parse", "--show-toplevel", "--abbrev-ref", "HEAD")
    lines = output.splitlines() if output else []
    if len(lines) != 2 or lines[1] == "HEAD":
        return None
    checkout = Checkout(Path(lines[0]), deadline)
    if checkout.git("config", "--get", f"remote.{REMOTE}.url") is None:
        return None
    had_selection = (checkout.top / SELECTION).is_file()
    fetch = ("fetch", "--quiet", "--prune", "--no-tags", REMOTE)
    result = checkout.run("git", *fetch, limit=FETCH_SECONDS)
    failure = ""
    if result is None:
        failure = f"could not fetch {REMOTE} (timed out or could not start)"
    elif result.code != 0:
        failure = f"could not fetch {REMOTE} ({first_line(result.err) or 'failed'})"
    return Fetched(checkout, lines[1], had_selection, failure)


def remote_default(checkout: Checkout) -> str | None:
    output = checkout.git("ls-remote", "--symref", REMOTE, "HEAD", limit=FETCH_SECONDS)
    for line in (output or "").splitlines():
        reference, _, name = line.partition("	")
        if name == "HEAD" and reference.startswith("ref: refs/heads/"):
            return reference.removeprefix("ref: refs/heads/")
    return None


def default_branch(checkout: Checkout, *, reachable: bool = True) -> str | None:
    remote = remote_default(checkout) if reachable else None
    if remote and checkout.succeeds(
        "rev-parse", "--verify", "--quiet", f"refs/remotes/{REMOTE}/{remote}"
    ):
        return remote
    head = checkout.git(
        "symbolic-ref", "--quiet", "--short", f"refs/remotes/{REMOTE}/HEAD"
    )
    if head and head.startswith(REMOTE + "/"):
        return head.removeprefix(REMOTE + "/")
    for candidate in ("main", "master"):
        reference = f"refs/remotes/{REMOTE}/{candidate}"
        if checkout.succeeds("rev-parse", "--verify", "--quiet", reference):
            return candidate
    return None


def counts(checkout: Checkout, upstream: str) -> tuple[int, int] | None:
    output = checkout.git("rev-list", "--left-right", "--count", f"{upstream}...HEAD")
    values = output.split() if output else []
    if len(values) != 2 or not all(value.isdigit() for value in values):
        return None
    return int(values[0]), int(values[1])


def pull_request(
    checkout: Checkout, branch: str
) -> tuple[bool, dict[str, object] | None]:
    query = ("pr", "list", "--head", branch, "--state", "all", "--limit", "1")
    result = checkout.run(
        "gh", *query, "--json", "number,state,url", limit=LOOKUP_SECONDS
    )
    if result is None or result.code != 0:
        return False, None
    try:
        found = json.loads(result.out or "[]")
    except ValueError:
        return False, None
    if not isinstance(found, list):
        return False, None
    return True, found[0] if found and isinstance(found[0], dict) else None


def branch_state(checkout: Checkout, branch: str, upstream: str) -> tuple[str, bool]:
    if checkout.succeeds("merge-base", "--is-ancestor", "HEAD", upstream):
        return f"It is fully contained in {upstream}.", True
    track_format = "--format=%(upstream:short)%00%(upstream:track)"
    track = checkout.git("for-each-ref", track_format, f"refs/heads/{branch}") or ""
    tracked, _, status = track.partition("\0")
    gone = bool(tracked) and "gone" in status
    known, request = pull_request(checkout, branch)
    if request is not None:
        state = str(request.get("state", "")).upper()
        url = request.get("url")
        described = f"Its PR #{request.get('number')} is {state}"
        described += f" ({url})." if url else "."
        return described, state in SHIPPED_STATES or gone
    if gone:
        return f"Its remote branch {tracked} is gone.", True
    if known:
        return "No pull request exists for it.", False
    return "Its pull request state is unknown.", False


def feature_notice(checkout: Checkout, branch: str, default: str, behind: int) -> str:
    upstream = f"{REMOTE}/{default}"
    state, shipped = branch_state(checkout, branch, upstream)
    fresh = f"start new work in a fresh worktree from {upstream}"
    if shipped:
        switch = f"`git switch {default}`, then `git merge --ff-only {upstream}`"
        retire = f"or run `{SYNC}` to retire this branch"
        action = f"switch to {default} ({switch}) {retire}; {fresh}"
    else:
        merge = f"run `{SYNC}` to merge {upstream} into this branch"
        action = f"{merge} before continuing; {fresh}"
    return (
        f"STALE CHECKOUT: branch {branch} is {commits(behind)} behind {upstream}. "
        f"{state} Next: {action}. This branch was not changed."
    )


def default_notice(checkout: Checkout, default: str, behind: int, ahead: int) -> str:
    upstream = f"{REMOTE}/{default}"
    stale = f"STALE CHECKOUT: {default} is {commits(behind)} behind"
    if ahead:
        return (
            f"{stale} and {commits(ahead)} ahead of {upstream}, so it cannot "
            f"fast-forward. Next: run `{SYNC}` and move the local commits to a "
            f"feature branch."
        )
    status = ("--no-optional-locks", "status", "--porcelain", "--untracked-files=no")
    if checkout.git(*status) != "":
        return (
            f"{stale} {upstream} and has uncommitted changes, so it was not "
            f"fast-forwarded. Next: commit or set aside those changes, then run "
            f"`{SYNC}`."
        )
    merged = checkout.run("git", "merge", "--ff-only", "--quiet", upstream)
    if merged is None or merged.code != 0:
        reason = "timed out" if merged is None else first_line(merged.err) or "failed"
        return (
            f"{stale} {upstream} and the fast-forward failed ({reason}). "
            f"Next: run `{SYNC}`."
        )
    revision = checkout.git("rev-parse", "--short", "HEAD") or upstream
    return (
        f"Checkout freshness: fast-forwarded {default} by {commits(behind)} "
        f"to {upstream} ({revision})."
    )


def selection_notice(checkout: Checkout, default: str, had_selection: bool) -> str:
    upstream = f"{REMOTE}/{default}"
    if (checkout.top / SELECTION).is_file():
        if had_selection:
            return ""
        return f"The update added {SELECTION}; restart the session so its plugins load."
    if not checkout.succeeds("cat-file", "-e", f"{upstream}:{SELECTION}"):
        return ""
    return (
        f"PLUGINS WILL NOT LOAD: this checkout has no {SELECTION}, but {upstream} "
        f"selects plugins, so no repository plugin or standard is active in this "
        f"session. Next: bring this checkout up to date with {upstream}, then restart "
        f"the session."
    )


def report(state: Fetched | None) -> str:
    if state is None:
        return ""
    checkout = state.checkout
    default = default_branch(checkout, reachable=not state.failure)
    lines = []
    if state.failure:
        compared = f"compared with the last fetched {REMOTE}/{default}"
        lines.append(
            f"Checkout freshness: {state.failure}; "
            f"{compared if default else 'freshness unknown'}."
        )
    if default is None:
        return "\n".join(lines)
    position = counts(checkout, f"{REMOTE}/{default}")
    if position is not None and position[0]:
        behind, ahead = position
        if state.branch == default:
            lines.append(default_notice(checkout, default, behind, ahead))
        else:
            lines.append(feature_notice(checkout, state.branch, default, behind))
    selection = selection_notice(checkout, default, state.had_selection)
    if selection:
        lines.append(selection)
    return "\n".join(lines)


def notice(directory: Path) -> str:
    return report(fetched(directory, time.monotonic() + TOTAL_SECONDS))


def begin(directory: Path) -> Callable[[], str]:
    deadline = time.monotonic() + TOTAL_SECONDS
    try:
        pool = ThreadPoolExecutor(max_workers=1)
        future = pool.submit(fetched, directory, deadline)
        pool.shutdown(wait=False)
    except FAILURES:
        return lambda: ""

    def finish() -> str:
        try:
            return report(future.result(timeout=max(0.0, deadline - time.monotonic())))
        except Exception:
            return ""

    return finish
