r"""Prove a merged worktree/branch is safe to remove, print the exact commands, record a receipt.

Run from the primary checkout, or argument-less from inside the worktree being finished: with
`--worktree`/`--branch`/`--head` omitted, each is derived from the invocation `cwd` (`git rev-parse
--show-toplevel`, its branch and HEAD); with `--pr` omitted, it is resolved via `gh pr view <branch>`
and cross-checked against a slice-3 cleanup obligation for that worktree when one is recorded. Resolves
the primary from the first `git worktree list --porcelain` entry, then applies these gates in order:

1. the target is a registered, non-primary, attached (non-detached) worktree on exactly the given
   branch and head;
2. a fresh `gh pr view <pr>` reports `MERGED` with `headRefOid` equal to the given head;
3. the merge commit is an ancestor of `origin/<default>` (fetched first);
4. `gh pr list --state open --head <branch>` returns no PRs;
5. `git status --porcelain=v2 --untracked-files=all` in the target is empty, or (argument-less from
   inside the target) remaining changes are archived under `<state>/merge-cleanup/set-aside/` and the
   tree is re-checked clean.

All gates pass: prints `removable` and the exact `worktree remove`/`branch -d`/`branch -D` commands,
exit 0. Any gate fails: prints `preserve: <reason>`, exit 1. Either way, a JSON receipt is written
under `<AGENT_STATE_DIRECTORY|~/.agents-state>/merge-cleanup/receipts/`.

`CLEANUP_PROOF_FORGE_FIXTURE` names a JSON file with optional `pr_view`, `open_prs` and (for the
argument-less `--pr` resolution) `pr_for_branch` keys to replace the `gh` calls for offline tests;
absent, all three call the real `gh` CLI.
"""

import argparse
import hashlib
import json
import os
import shutil
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


def run_git_binary(cwd, *args, timeout=GIT_TIMEOUT_SECONDS):
    try:
        return subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True, timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise Preserve(f"git {' '.join(args)} failed: {error}") from error


def derive_context(cwd):
    result = run_git(cwd, "rev-parse", "--show-toplevel")
    if result.returncode != 0:
        raise Preserve("not inside a Git worktree; pass --worktree explicitly")
    worktree = result.stdout.strip()
    branch_result = run_git(worktree, "rev-parse", "--abbrev-ref", "HEAD")
    branch = branch_result.stdout.strip() if branch_result.returncode == 0 else ""
    if branch_result.returncode != 0 or branch in ("", "HEAD"):
        raise Preserve(f"{worktree} HEAD is detached; pass --branch explicitly")
    head_result = run_git(worktree, "rev-parse", "HEAD")
    if head_result.returncode != 0:
        raise Preserve(f"cannot resolve HEAD in {worktree}; pass --head explicitly")
    return worktree, branch, head_result.stdout.strip()


def obligation_for_worktree(worktree):
    digest = hashlib.sha256(Path(worktree).resolve().as_posix().encode("utf-8")).hexdigest()
    path = state_directory() / "merge-cleanup" / "obligations" / f"{digest}.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def resolve_pr(branch, repo, fixture, obligation):
    if fixture is not None:
        value = fixture.get("pr_for_branch")
        if value is None:
            raise Preserve(f"no PR recorded for branch {branch}; pass --pr explicitly")
        number = int(value)
    else:
        result = gh(repo, "pr", "view", branch, "--json", "number")
        if result.returncode != 0:
            raise Preserve(f"gh pr view {branch} failed: {result.stderr.strip()}")
        try:
            data = json.loads(result.stdout)
        except ValueError as error:
            raise Preserve(f"gh pr view {branch} returned invalid JSON: {error}") from error
        value = data.get("number") if isinstance(data, dict) else None
        if not isinstance(value, int):
            raise Preserve(f"gh pr view {branch} did not return a PR number")
        number = value
    if obligation is not None:
        recorded_pr = obligation.get("pr")
        if recorded_pr is not None and str(recorded_pr) != str(number):
            raise Preserve(f"PR #{number} disagrees with the recorded obligation PR #{recorded_pr}")
    return number


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


def status_entries(target):
    result = run_git(target, "status", "--porcelain=v2", "-z", "--untracked-files=all")
    if result.returncode != 0:
        raise Preserve(f"git status failed: {result.stderr.strip()}")
    tokens = result.stdout.split("\0")
    if tokens and tokens[-1] == "":
        tokens.pop()
    records = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.startswith("2 "):
            orig = tokens[index + 1] if index + 1 < len(tokens) else ""
            records.append(f"{token}\t{orig}")
            index += 2
            continue
        if token.startswith("u "):
            raise Preserve(f"{target} has unmerged paths")
        records.append(token)
        index += 1
    return records


def cwd_is_inside_target(cwd, target):
    try:
        Path(cwd).resolve().relative_to(target)
    except ValueError:
        return False
    return True


def set_aside_directory(target):
    digest = hashlib.sha256(target.as_posix().encode("utf-8")).hexdigest()
    return state_directory() / "merge-cleanup" / "set-aside" / f"{digest}-{int(time.time() * 1000)}"


def set_aside(target, records, branch, head, pr):
    archive = set_aside_directory(target)
    try:
        archive.mkdir(parents=True)
    except OSError as error:
        raise Preserve(f"cannot create set-aside archive {archive}: {error}") from error

    patch_entry = None
    diff_result = run_git_binary(target, "diff", "HEAD", "--binary")
    if diff_result.returncode != 0:
        raise Preserve(f"git diff HEAD --binary failed in {target}")
    if diff_result.stdout:
        patch_path = archive / "tracked.patch"
        patch_path.write_bytes(diff_result.stdout)
        if patch_path.read_bytes() != diff_result.stdout:
            raise Preserve(f"set-aside patch verification failed for {patch_path}")
        patch_entry = {
            "file": "tracked.patch",
            "sha256": hashlib.sha256(diff_result.stdout).hexdigest(),
            "bytes": len(diff_result.stdout),
            "note": "staged and unstaged tracked changes are flattened into one patch",
        }

    untracked_entries = []
    for record in records:
        if not record.startswith("? "):
            continue
        relative_path = record[2:]
        source = target / relative_path
        try:
            source_bytes = source.read_bytes()
        except OSError as error:
            raise Preserve(f"cannot read untracked file {source}: {error}") from error
        source_hash = hashlib.sha256(source_bytes).hexdigest()
        destination = archive / "untracked" / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        try:
            copy_bytes = destination.read_bytes()
        except OSError as error:
            raise Preserve(f"cannot verify set-aside copy {destination}: {error}") from error
        if hashlib.sha256(copy_bytes).hexdigest() != source_hash:
            raise Preserve(f"set-aside copy hash mismatch for {relative_path}")
        untracked_entries.append({
            "path": relative_path,
            "sha256": source_hash,
            "bytes": len(source_bytes),
        })

    manifest_path = archive / "manifest.json"
    manifest_path.write_text(json.dumps({
        "worktree": str(target),
        "branch": branch,
        "head": head,
        "pr": pr,
        "created_at": time.time(),
        "status_records": records,
        "patch": patch_entry,
        "untracked": untracked_entries,
    }, sort_keys=True), encoding="utf-8")
    try:
        json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Preserve(f"set-aside manifest unreadable: {error}") from error

    reset = run_git(target, "reset", "--hard", "HEAD")
    if reset.returncode != 0:
        raise Preserve(f"git reset --hard HEAD failed in {target}: {reset.stderr.strip()}")
    for entry in untracked_entries:
        path = target / entry["path"]
        try:
            path.unlink(missing_ok=True)
        except OSError as error:
            raise Preserve(f"cannot remove set-aside source {path}: {error}") from error

    return str(archive)


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
    worktree_value = args.worktree
    branch = args.branch
    head = args.head
    pr = args.pr
    verdict = "removable"
    reason = None
    merge_oid = None
    primary = None
    set_aside_path = None
    commands = []
    try:
        if worktree_value is None or branch is None or head is None:
            derived_worktree, derived_branch, derived_head = derive_context(cwd)
            worktree_value = worktree_value or derived_worktree
            branch = branch or derived_branch
            head = head or derived_head
        worktree = Path(worktree_value).resolve()
        obligation = obligation_for_worktree(worktree)
        if pr is None:
            pr = resolve_pr(branch, args.repo, fixture, obligation)
        primary, target = resolve_target(cwd, worktree_value, branch, head)
        records = status_entries(target)
        merge_oid = require_merged(pr, head, args.repo, fixture)
        require_contained(primary, default, merge_oid)
        require_no_open_pr(branch, args.repo, fixture)
        if records:
            if cwd_is_inside_target(cwd, target):
                try:
                    set_aside_path = set_aside(target, records, branch, head, pr)
                except OSError as error:
                    raise Preserve(f"set-aside failed for {target}: {error}") from error
            else:
                raise Preserve(f"{target} has uncommitted or untracked changes")
        require_clean(target)
        commands = [
            f'git -C "{primary}" worktree remove -- "{target}"',
            branch_deletion_command(primary, branch, default),
        ]
    except Preserve as error:
        verdict = "preserve"
        reason = error.reason
        if worktree_value is None:
            worktree_value = str(cwd)

    worktree = Path(worktree_value).resolve()
    save_receipt(receipt_path(worktree), {
        "worktree": str(worktree),
        "primary": str(primary) if primary is not None else None,
        "branch": branch,
        "head": head,
        "pr": pr,
        "merge_oid": merge_oid,
        "default": default,
        "verdict": verdict,
        "set_aside": set_aside_path,
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
    parser.add_argument("--worktree")
    parser.add_argument("--branch")
    parser.add_argument("--head")
    parser.add_argument("--pr", type=int)
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
