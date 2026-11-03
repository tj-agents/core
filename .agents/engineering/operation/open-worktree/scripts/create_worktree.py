#!/usr/bin/env python3
"""Create an isolated checkout at the one supported location: <repo-root>/.worktrees/<flattened-branch>
(Python 3.9+).

Never a sibling `<repo-root-parent>/<repo-name>.worktrees/<branch>` folder. A sibling layout sits outside
the repository's own directory tree, so a native host's project-local settings and plugin registrations -
resolved by walking up from the working directory - never reach it; skills enabled in the main checkout
silently stay unavailable there, permanently, because no amount of session refresh changes where the host
looks. Nesting under the repository root is what makes the checkout inherit that registration for free.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

GIT_TIMEOUT_SECONDS = 60


class CreateWorktreeError(RuntimeError):
    pass


def git(cwd: Path, *arguments: str, timeout: int = GIT_TIMEOUT_SECONDS) -> subprocess.CompletedProcess:
    command = ["git", "-C", str(cwd), *arguments]
    try:
        return subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CreateWorktreeError(f"{' '.join(command)}: {error}") from error


def run(cwd: Path, *arguments: str, timeout: int = GIT_TIMEOUT_SECONDS) -> str:
    result = git(cwd, *arguments, timeout=timeout)
    if result.returncode:
        raise CreateWorktreeError(f"git {' '.join(arguments)} failed: {(result.stderr or result.stdout).strip()}")
    return result.stdout.strip()


def repository_root(start: Path) -> Path:
    common = run(start, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common).resolve().parent


def default_base(repo: Path, has_origin: bool) -> str:
    if has_origin:
        ref = git(repo, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
        if ref.returncode == 0 and ref.stdout.strip():
            return ref.stdout.strip()
        return "origin/main"
    local = git(repo, "symbolic-ref", "--quiet", "--short", "HEAD")
    return local.stdout.strip() if local.returncode == 0 and local.stdout.strip() else "main"


def ref_exists(repo: Path, ref: str) -> bool:
    return git(repo, "rev-parse", "--verify", "--quiet", ref).returncode == 0


def worktree_path(repo: Path, branch: str) -> Path:
    if not branch or branch.strip() != branch or "\\" in branch:
        raise CreateWorktreeError(f"invalid branch name: {branch!r}")
    return repo / ".worktrees" / branch.replace("/", "-")


def create(branch: str, start_point: str | None = None, *, cwd: Path | None = None) -> dict:
    repo = repository_root(cwd or Path.cwd())
    path = worktree_path(repo, branch)
    if path.exists():
        raise CreateWorktreeError(f"{path} already exists")
    has_origin = "origin" in run(repo, "remote").splitlines()
    if has_origin:
        run(repo, "fetch", "origin", "--prune")
    local_branch_exists = ref_exists(repo, f"refs/heads/{branch}")
    remote_branch_exists = has_origin and ref_exists(repo, f"refs/remotes/origin/{branch}")
    if local_branch_exists:
        arguments = ["worktree", "add", str(path), branch]
    elif remote_branch_exists:
        arguments = ["worktree", "add", str(path), "-b", branch, "--track", f"origin/{branch}"]
    else:
        base = start_point or default_base(repo, has_origin)
        arguments = ["worktree", "add", str(path), "-b", branch, base]
    run(repo, *arguments)
    head = run(path, "rev-parse", "HEAD")
    base_description = start_point or ("(existing branch)" if local_branch_exists or remote_branch_exists
                                       else default_base(repo, has_origin))
    return {"repository": str(repo), "branch": branch, "path": str(path), "head": head, "base": base_description}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("branch", help="<Type>/<Name> branch to check out, e.g. Feature/BrowserCredentials")
    parser.add_argument("--from", dest="start_point", default=None,
                        help="start point for a new branch (default: the fetched remote default branch); "
                             "required for a dependent stack layer, where it is the parent branch's verified tip")
    arguments = parser.parse_args(argv)
    try:
        result = create(arguments.branch, arguments.start_point)
    except CreateWorktreeError as error:
        print(json.dumps({"error": str(error)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
