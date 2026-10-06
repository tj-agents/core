r"""Prove a merged worktree/branch is safe to remove, print the exact commands, record a receipt.

Run from the primary checkout. Resolves the primary from the first `git worktree list --porcelain`
entry, then applies these gates in order:

1. the target is a registered, non-primary, attached (non-detached) worktree on exactly the given
   branch and head;
2. `git status --porcelain=v2 --untracked-files=all` in the target is empty;
3. a fresh `gh pr view <pr>` reports `MERGED` with `headRefOid` equal to the given head;
4. the merge commit is an ancestor of `origin/<default>` (fetched first);
5. `gh pr list --state open --head <branch>` returns no PRs.

All gates pass: prints `removable` and the exact `worktree remove`/`branch -d`/`branch -D` commands,
exit 0. Any gate fails: prints `preserve: <reason>`, exit 1. Either way, a JSON receipt is written
under `<AGENT_STATE_DIRECTORY|~/.agents-state>/merge-cleanup/receipts/`.

`CLEANUP_PROOF_FORGE_FIXTURE` names a JSON file with optional `pr_view` and `open_prs` keys to replace
the two `gh` calls for offline tests; absent, both call the real `gh` CLI.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


STATE_DIRECTORY_ENV = "AGENT_STATE_DIRECTORY"
FORGE_FIXTURE_ENV = "CLEANUP_PROOF_FORGE_FIXTURE"
GIT_TIMEOUT_SECONDS = 10
FORGE_TIMEOUT_SECONDS = 20


class Preserve(Exception):
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def state_directory():
    configured = os.environ.get(STATE_DIRECTORY_ENV)
    return Path(configured) if configured else Path.home() / ".agents-state"


def receipt_path(worktree):
    digest = hashlib.sha256(worktree.as_posix().encode("utf-8")).hexdigest()
    return state_directory() / "merge-cleanup" / "receipts" / f"{digest}.json"


def save_receipt(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, sort_keys=True)
            handle.write("\n")
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def run_git(cwd, *args, timeout=GIT_TIMEOUT_SECONDS):
    try:
        return subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True, text=True, timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise Preserve(f"git {' '.join(args)} failed: {error}") from error


def git_succeeds(cwd, *args, timeout=GIT_TIMEOUT_SECONDS):
    return run_git(cwd, *args, timeout=timeout).returncode == 0


def default_branch(cwd):
    result = run_git(cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if result.returncode != 0:
        raise Preserve("origin/HEAD is not resolvable; pass --default")
    ref = result.stdout.strip()
    if not ref.startswith("origin/"):
        raise Preserve("origin/HEAD is not resolvable; pass --default")
    return ref[len("origin/"):]


def list_worktrees(cwd):
    result = run_git(cwd, "worktree", "list", "--porcelain")
    if result.returncode != 0:
        raise Preserve(f"git worktree list failed: {result.stderr.strip()}")
    entries = []
    for block in result.stdout.split("\n\n"):
        block = block.strip("\n")
        if not block.strip():
            continue
        fields = {}
        detached = False
        for line in block.splitlines():
            if line.strip() == "detached":
                detached = True
                continue
            if " " in line:
                key, value = line.split(" ", 1)
                fields[key] = value
        path = fields.get("worktree")
        if path is None:
            continue
        branch_ref = fields.get("branch")
        branch = (
            branch_ref[len("refs/heads/"):]
            if branch_ref and branch_ref.startswith("refs/heads/")
            else None
        )
        entries.append({
            "path": Path(path).resolve(),
            "head": fields.get("HEAD"),
            "branch": branch,
            "detached": detached or branch is None,
        })
    return entries


def resolve_target(cwd, worktree, branch, head):
    entries = list_worktrees(cwd)
    if not entries:
        raise Preserve("no worktree records found")
    primary = entries[0]["path"]
    target = Path(worktree).resolve()
    if target == primary:
        raise Preserve(f"{target} is the primary checkout")
    matches = [entry for entry in entries if entry["path"] == target]
    if not matches:
        raise Preserve(f"{target} is not a registered worktree")
    entry = matches[0]
    if entry["detached"]:
        raise Preserve(f"{target} is detached")
    if entry["branch"] != branch:
        raise Preserve(f"{target} is on branch {entry['branch']!r}, not {branch!r}")
    if entry["head"] != head:
        raise Preserve(f"{target} is at {entry['head']!r}, not {head!r}")
    return primary, target


def require_clean(target):
    result = run_git(target, "status", "--porcelain=v2", "--untracked-files=all")
    if result.returncode != 0:
        raise Preserve(f"git status failed: {result.stderr.strip()}")
    if result.stdout.strip():
        raise Preserve(f"{target} has uncommitted or untracked changes")


def load_fixture():
    path = os.environ.get(FORGE_FIXTURE_ENV)
    if not path:
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Preserve(f"forge fixture unreadable: {error}") from error


def gh(repo, *args):
    command = ["gh", *args]
    if repo:
        command += ["--repo", repo]
    try:
        return subprocess.run(
            command, capture_output=True, text=True, timeout=FORGE_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as error:
        raise Preserve("the gh CLI is required") from error
    except subprocess.SubprocessError as error:
        raise Preserve(f"gh {' '.join(args)} failed: {error}") from error


def pr_view(pr, repo, fixture):
    if fixture is not None:
        return fixture.get("pr_view")
    result = gh(repo, "pr", "view", str(pr), "--json", "state,headRefOid,mergeCommit")
    if result.returncode != 0:
        raise Preserve(f"gh pr view {pr} failed: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout)
    except ValueError as error:
        raise Preserve(f"gh pr view {pr} returned invalid JSON: {error}") from error


def require_merged(pr, head, repo, fixture):
    view = pr_view(pr, repo, fixture)
    if not isinstance(view, dict):
        raise Preserve(f"PR #{pr} query returned nothing")
    if view.get("state") != "MERGED":
        raise Preserve(f"PR #{pr} is not MERGED")
    if view.get("headRefOid") != head:
        raise Preserve(f"PR #{pr} head {view.get('headRefOid')!r} does not match {head!r}")
    merge_commit = view.get("mergeCommit") or {}
    oid = merge_commit.get("oid")
    if not oid:
        raise Preserve(f"PR #{pr} has no recorded merge commit")
    return oid


def require_contained(primary, default, merge_oid):
    fetch = run_git(primary, "fetch", "origin", default, "--quiet")
    if fetch.returncode != 0:
        raise Preserve(f"git fetch origin {default} failed: {fetch.stderr.strip()}")
    if not git_succeeds(primary, "merge-base", "--is-ancestor", merge_oid, "origin/" + default):
        raise Preserve(f"merge commit {merge_oid} is not an ancestor of origin/{default}")


def open_prs(branch, repo, fixture):
    if fixture is not None:
        return fixture.get("open_prs", [])
    result = gh(repo, "pr", "list", "--state", "open", "--head", branch, "--json", "number")
    if result.returncode != 0:
        raise Preserve(f"gh pr list for {branch} failed: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout)
    except ValueError as error:
        raise Preserve(f"gh pr list for {branch} returned invalid JSON: {error}") from error


def require_no_open_pr(branch, repo, fixture):
    prs = open_prs(branch, repo, fixture)
    if prs:
        raise Preserve(f"an open PR exists for branch {branch}")


def branch_deletion_command(primary, branch, default):
    if git_succeeds(primary, "merge-base", "--is-ancestor", "refs/heads/" + branch, "origin/" + default):
        return f'git -C "{primary}" branch -d {branch}'
    return f'git -C "{primary}" branch -D {branch}'


def run(args):
    cwd = Path.cwd()
    default = args.default or default_branch(cwd)
    fixture = load_fixture()
    worktree = Path(args.worktree).resolve()
    verdict = "removable"
    reason = None
    merge_oid = None
    primary = None
    commands = []
    try:
        primary, target = resolve_target(cwd, args.worktree, args.branch, args.head)
        require_clean(target)
        merge_oid = require_merged(args.pr, args.head, args.repo, fixture)
        require_contained(primary, default, merge_oid)
        require_no_open_pr(args.branch, args.repo, fixture)
        commands = [
            f'git -C "{primary}" worktree remove -- "{target}"',
            branch_deletion_command(primary, args.branch, default),
        ]
    except Preserve as error:
        verdict = "preserve"
        reason = error.reason

    save_receipt(receipt_path(worktree), {
        "worktree": str(worktree),
        "primary": str(primary) if primary is not None else None,
        "branch": args.branch,
        "head": args.head,
        "pr": args.pr,
        "merge_oid": merge_oid,
        "default": default,
        "verdict": verdict,
        "recorded_at": time.time(),
    })

    if verdict == "removable":
        print("removable")
        for command in commands:
            print(command)
        return 0
    print(f"preserve: {reason}")
    return 1


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--pr", required=True, type=int)
    parser.add_argument("--default")
    parser.add_argument("--repo")
    return parser.parse_args(argv)


def main(argv=None):
    try:
        return run(parse_args(argv))
    except Preserve as error:
        print(f"preserve: {error.reason}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
