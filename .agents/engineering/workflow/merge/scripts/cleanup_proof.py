r"""Prove a merged worktree/branch is safe to remove, print the exact commands, record a receipt.

Run from the primary checkout, or argument-less from inside the worktree being finished: with
`--worktree`/`--branch`/`--head` omitted, each is derived from the invocation `cwd` (`git rev-parse
--show-toplevel`, its branch and HEAD); with `--pr` omitted, it is resolved via `gh pr view <branch>`
and cross-checked against a slice-3 cleanup obligation for that worktree when one is recorded. Resolves
the primary from the first `git worktree list --porcelain` entry, then applies these gates in order:

1. the target is a registered attached worktree on exactly the given branch and head, or the primary
   checkout on the default branch with a separately verified saved branch ref;
2. a fresh `gh pr view <pr>` reports `MERGED` with `headRefOid` equal to the given head;
3. the merge commit is an ancestor of `origin/<default>` (fetched first);
4. fresh authoritative open-PR evidence returns neither HEAD users nor BASE dependents for `<branch>`;
5. `git status --porcelain=v2 --untracked-files=all` in the target is empty, or (argument-less from
   inside the target) remaining changes are archived under `<state>/merge-cleanup/set-aside/` and the
   tree is re-checked clean.

All deletion gates pass: prints `removable` and the exact deletion commands, exit 0. An open BASE
dependent prints `retained-dependency`, exit 0, and keeps the checkout and branch. Any other gate fails:
prints `preserve: <reason>`, exit 1. Either way, a JSON receipt is written
under `<AGENT_STATE_DIRECTORY|~/.agents-state>/merge-cleanup/receipts/`.

`CLEANUP_PROOF_FORGE_FIXTURE` names a JSON file with `pr_view`, `open_head_prs`, `open_base_prs` and
(for the argument-less `--pr` resolution) `pr_for_branch` keys to replace the `gh` calls for offline
tests; absent, all calls use the real `gh` CLI.
"""

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def dependency_helper_directory():
    source = Path(__file__).resolve()
    for parent in source.parents:
        for candidate in (parent / "hooks", parent / ".agents" / "hooks"):
            if (candidate / "cleanup_dependency.py").is_file():
                return candidate
    raise RuntimeError("cleanup dependency helper is unavailable")


sys.path.insert(0, str(dependency_helper_directory()))
from cleanup_dependency import (EvidenceError, canonical_github_repository, checkout_github_repository, github_repository_from_origin, observe_open_prs)


STATE_DIRECTORY_ENV = "AGENT_STATE_DIRECTORY"
FORGE_FIXTURE_ENV = "CLEANUP_PROOF_FORGE_FIXTURE"
GIT_TIMEOUT_SECONDS = 10
FORGE_TIMEOUT_SECONDS = 20


class Preserve(Exception):
    def __init__(self, reason, set_aside=None):
        super().__init__(reason)
        self.reason = reason
        self.set_aside = set_aside


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
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
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


def resolve_pr(branch, repo, fixture, obligation, cwd=None):
    if fixture is not None:
        value = fixture.get("pr_for_branch")
        if value is None:
            raise Preserve(f"no PR recorded for branch {branch}; pass --pr explicitly")
        number = int(value)
    else:
        result = gh(repo, "pr", "view", branch, "--json", "number", cwd=cwd)
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


def resolve_target(cwd, worktree, branch, head, default):
    entries = list_worktrees(cwd)
    if not entries:
        raise Preserve("no worktree records found")
    primary = entries[0]["path"]
    target = Path(worktree).resolve()
    if target == primary:
        current = entries[0]
        if current["branch"] != default:
            raise Preserve(f"{target} is on {current['branch']!r}, not the default branch {default!r}")
        saved = run_git(primary, "rev-parse", "refs/heads/" + branch)
        if saved.returncode != 0 or saved.stdout.strip() != head:
            raise Preserve(f"saved branch {branch!r} does not resolve to {head!r}")
        return primary, target, True
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
    return primary, target, False


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

    try:
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
        except OSError as error:
            raise Preserve(f"set-aside manifest unreadable: {error}") from error
        except ValueError as error:
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
    except Preserve as error:
        if error.set_aside is None:
            error.set_aside = str(archive)
        raise
    except OSError as error:
        raise Preserve(f"set-aside failed for {target}: {error}", str(archive)) from error


def load_fixture():
    path = os.environ.get(FORGE_FIXTURE_ENV)
    if not path:
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Preserve(f"forge fixture unreadable: {error}") from error


def gh(repo, *args, cwd=None):
    command = ["gh", *args]
    if repo:
        command += ["--repo", repo]
    try:
        return subprocess.run(
            command, cwd=str(cwd) if cwd is not None else None, capture_output=True, text=True,
            timeout=FORGE_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as error:
        raise Preserve("the gh CLI is required") from error
    except subprocess.SubprocessError as error:
        raise Preserve(f"gh {' '.join(args)} failed: {error}") from error


def pr_view(pr, repo, fixture, cwd=None):
    if fixture is not None:
        return fixture.get("pr_view")
    result = gh(repo, "pr", "view", str(pr), "--json", "state,headRefOid,mergeCommit", cwd=cwd)
    if result.returncode != 0:
        raise Preserve(f"gh pr view {pr} failed: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout)
    except ValueError as error:
        raise Preserve(f"gh pr view {pr} returned invalid JSON: {error}") from error


def require_merged(pr, head, repo, fixture, cwd=None):
    view = pr_view(pr, repo, fixture, cwd=cwd)
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


def require_safe_dependencies(branch, repo, primary, fixture):
    try:
        evidence = observe_open_prs(branch, repo=repo, cwd=primary, fixture=fixture)
    except EvidenceError as error:
        raise Preserve(str(error)) from error
    if evidence["head"]:
        raise Preserve(f"an open PR exists for branch {branch}")
    return evidence


def branch_deletion_command(primary, branch, default):
    if git_succeeds(primary, "merge-base", "--is-ancestor", "refs/heads/" + branch, "origin/" + default):
        return f'git -C "{primary}" branch -d {branch}'
    return f'git -C "{primary}" branch -D {branch}'


def validate_branch(branch):
    if not isinstance(branch, str) or not branch or branch.startswith("-") or any(
            char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._/-" for char in branch):
        raise Preserve(f"branch {branch!r} cannot be emitted in a cleanup command")


def validate_head(head):
    if not isinstance(head, str) or len(head) not in (40, 64) or any(char not in "0123456789abcdef" for char in head):
        raise Preserve(f"head {head!r} cannot be used for remote cleanup")


def validate_command_path(value, label):
    path = Path(value)
    if not path.is_absolute() or any(not (char.isalnum() or char in "._-/\\: ") for char in str(path)):
        raise Preserve(f"{label} {value!r} cannot be emitted in a cleanup command")
    return path.resolve()


def validate_repo(repo):
    if repo is None:
        return None
    try:
        return canonical_github_repository(repo)
    except EvidenceError as error:
        raise Preserve(f"repository {repo!r} cannot be emitted in a cleanup command") from error


def primary_github_repository(primary, repo=None):
    try:
        return checkout_github_repository(primary, repo)
    except EvidenceError as error:
        raise Preserve(str(error)) from error


def push_destination(primary, expected_repo):
    result = run_git(primary, "remote", "get-url", "--push", "--all", "origin")
    if result.returncode != 0:
        raise Preserve("primary push origin is unavailable")
    destinations = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    if len(destinations) != 1:
        raise Preserve("primary push origin has no unique destination")
    destination = destinations.pop()
    rules = run_git(primary, "config", "-z", "--get-regexp", r"^url\..*\.(insteadof|pushinsteadof)$")
    if rules.returncode not in (0, 1):
        raise Preserve("Git URL rewrite rules are unavailable")
    if rules.returncode == 0:
        for record in rules.stdout.split("\0"):
            if not record:
                continue
            fields = record.split("\n")
            if len(fields) != 2 or not fields[0] or not fields[1] or not fields[0].startswith("url."):
                raise Preserve("Git URL rewrite rules are malformed")
            if destination.startswith(fields[1]):
                raise Preserve("primary push origin is subject to a Git URL rewrite")
    try:
        actual = github_repository_from_origin(destination)
    except EvidenceError as error:
        raise Preserve("primary push origin is not a GitHub repository") from error
    if actual.lower() != expected_repo.lower():
        raise Preserve("primary push origin does not match the checkout origin")
    return destination


def remote_deletion_command(worktree, branch, head, pr, default, repo):
    validate_command_path(worktree, "worktree")
    validate_branch(branch)
    validate_head(head)
    validate_branch(default)
    validate_repo(repo)
    script = validate_command_path(Path(__file__).resolve(), "cleanup proof script")
    interpreter = "python" if os.name == "nt" else "python3"
    command = (
        f'{interpreter} -B "{script}" --delete-remote '
        f'--worktree "{worktree}" --branch {branch} --head {head} --pr {pr} --default {default}'
    )
    if repo:
        command += f" --repo {repo}"
    return command


def run(args):
    cwd = Path.cwd()
    default = args.default
    fixture = None
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
    dependencies = []
    dependency_evidence = None
    try:
        default = default or default_branch(cwd)
        fixture = load_fixture()
        if worktree_value is None or branch is None or head is None:
            derived_worktree, derived_branch, derived_head = derive_context(cwd)
            worktree_value = worktree_value or derived_worktree
            branch = branch or derived_branch
            head = head or derived_head
        validate_branch(branch)
        if branch == default:
            raise Preserve("the default branch cannot be deleted")
        worktree = Path(worktree_value).resolve()
        obligation = obligation_for_worktree(worktree)
        primary, target, primary_branch_route = resolve_target(cwd, worktree_value, branch, head, default)
        repo = args.repo if fixture is not None else primary_github_repository(primary, args.repo)
        if pr is None:
            pr = resolve_pr(branch, repo, fixture, obligation, cwd=primary)
        records = [] if primary_branch_route else status_entries(target)
        merge_oid = require_merged(pr, head, repo, fixture, cwd=primary)
        require_contained(primary, default, merge_oid)
        dependency_evidence = require_safe_dependencies(branch, repo, primary, fixture)
        dependencies = dependency_evidence["base"]
        if dependencies:
            verdict = "retained-dependency"
            reason = f"open PRs depend on branch {branch} as their base"
        else:
            if records:
                if cwd_is_inside_target(cwd, target):
                    try:
                        set_aside_path = set_aside(target, records, branch, head, pr)
                    except OSError as error:
                        raise Preserve(f"set-aside failed for {target}: {error}") from error
                else:
                    raise Preserve(f"{target} has uncommitted or untracked changes")
            commands.append(remote_deletion_command(worktree, branch, head, pr, default, repo))
            if not primary_branch_route:
                require_clean(target)
                commands.append(f'git -C "{primary}" worktree remove -- "{target}"')
            commands.append(branch_deletion_command(primary, branch, default))
    except Preserve as error:
        verdict = "preserve"
        reason = error.reason
        set_aside_path = error.set_aside or set_aside_path
        if worktree_value is None:
            worktree_value = str(cwd)

    worktree = Path(worktree_value or cwd).resolve()
    save_receipt(receipt_path(worktree), {
        "worktree": str(worktree),
        "primary": str(primary) if primary is not None else None,
        "branch": branch,
        "head": head,
        "pr": pr,
        "merge_oid": merge_oid,
        "default": default,
        "repo": repo if "repo" in locals() else args.repo,
        "verdict": verdict,
        "dependencies": dependencies,
        "dependency_evidence": dependency_evidence,
        "set_aside": set_aside_path,
        "recorded_at": time.time(),
    })

    if verdict == "removable":
        print("removable")
        for command in commands:
            print(command)
        return 0
    if verdict == "retained-dependency":
        print("retained-dependency")
        for dependency in dependencies:
            print(f"PR #{dependency['number']} ({dependency['head_ref_name']} at {dependency['head_ref_oid']})")
        return 0
    print(f"preserve: {reason}")
    return 1


def removable_receipt(worktree, branch, head, pr, default, repo):
    path = receipt_path(worktree)
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Preserve(f"removable receipt is unavailable: {error}") from error
    if not isinstance(receipt, dict) or receipt.get("verdict") != "removable":
        raise Preserve("removable receipt is unavailable")
    recorded_at = receipt.get("recorded_at")
    if isinstance(recorded_at, bool) or not isinstance(recorded_at, (int, float)) or not math.isfinite(recorded_at):
        raise Preserve("removable receipt has no valid timestamp")
    age = time.time() - recorded_at
    if age < 0 or age > 3600:
        raise Preserve("removable receipt is stale")
    expected = {
        "worktree": str(worktree),
        "branch": branch,
        "head": head,
        "pr": pr,
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            raise Preserve(f"removable receipt {field} does not match this cleanup")
    recorded_default = receipt.get("default")
    if not isinstance(recorded_default, str):
        raise Preserve("removable receipt default is unavailable")
    validate_branch(recorded_default)
    if default is not None and default != recorded_default:
        raise Preserve("removable receipt default does not match this cleanup")
    if repo is not None:
        recorded_repo = receipt.get("repo")
        if not isinstance(recorded_repo, str) or validate_repo(recorded_repo).lower() != validate_repo(repo).lower():
            raise Preserve("removable receipt repository does not match this cleanup")
    recorded_primary = receipt.get("primary")
    if not isinstance(recorded_primary, str):
        raise Preserve("removable receipt primary is unavailable")
    return validate_command_path(recorded_primary, "primary"), recorded_default


def record_remote_deleted(worktree, repo, branch, head, pr):
    path = receipt_path(worktree)
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Preserve(f"removable receipt is unavailable: {error}") from error
    if not isinstance(receipt, dict) or receipt.get("verdict") != "removable":
        raise Preserve("removable receipt is unavailable")
    if any(receipt.get(key) != value for key, value in (("worktree", str(worktree)), ("repo", repo), ("branch", branch), ("head", head), ("pr", pr))):
        raise Preserve("removable receipt no longer matches this cleanup")
    receipt["remote_deleted"] = {
        "repo": repo,
        "branch": branch,
        "head": head,
        "pr": pr,
        "recorded_at": time.time(),
    }
    save_receipt(path, receipt)

def remote_ref_matches(primary, destination, branch, head):
    result = run_git(primary, "ls-remote", "--refs", destination, "refs/heads/" + branch)
    if result.returncode != 0:
        raise Preserve(f"git ls-remote failed: {result.stderr.strip()}")
    output = result.stdout.strip()
    if not output:
        return False
    lines = output.splitlines()
    if len(lines) != 1:
        raise Preserve("git ls-remote returned malformed branch evidence")
    fields = lines[0].split("\t")
    if fields != [head, "refs/heads/" + branch]:
        raise Preserve("remote branch does not match the saved head")
    return True


def run_delete_remote(args):
    if FORGE_FIXTURE_ENV in os.environ:
        raise Preserve("forge fixtures cannot authorize remote deletion")
    if args.worktree is None or args.branch is None or args.head is None or args.pr is None:
        raise Preserve("remote deletion requires saved worktree, branch, head, and PR")
    worktree = validate_command_path(args.worktree, "worktree")
    validate_branch(args.branch)
    validate_head(args.head)
    supplied_repo = validate_repo(args.repo)
    primary, default = removable_receipt(worktree, args.branch, args.head, args.pr, args.default, args.repo)
    if args.branch == default:
        raise Preserve("the default branch cannot be deleted")
    entries = list_worktrees(primary)
    if not entries or entries[0]["path"] != primary:
        raise Preserve("removable receipt primary is not the actual primary checkout")
    if default_branch(primary) != default:
        raise Preserve("removable receipt default is not the current origin default")
    origin_repo = primary_github_repository(primary, supplied_repo)
    destination = push_destination(primary, origin_repo)
    merge_oid = require_merged(args.pr, args.head, origin_repo, None, cwd=primary)
    require_contained(primary, default, merge_oid)
    evidence = require_safe_dependencies(args.branch, origin_repo, primary, None)
    if evidence["base"]:
        raise Preserve(f"open PRs depend on branch {args.branch} as their base")
    if not remote_ref_matches(primary, destination, args.branch, args.head):
        record_remote_deleted(worktree, origin_repo, args.branch, args.head, args.pr)
        print("remote-deleted")
        return 0
    result = run_git(
        primary,
        "push",
        f"--force-with-lease=refs/heads/{args.branch}:{args.head}",
        destination,
        f":refs/heads/{args.branch}",
    )
    if result.returncode != 0:
        raise Preserve(f"git push remote deletion failed: {result.stderr.strip()}")
    record_remote_deleted(worktree, origin_repo, args.branch, args.head, args.pr)
    print("remote-deleted")
    return 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--worktree")
    parser.add_argument("--branch")
    parser.add_argument("--head")
    parser.add_argument("--pr", type=int)
    parser.add_argument("--default")
    parser.add_argument("--repo")
    parser.add_argument("--delete-remote", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    try:
        args = parse_args(argv)
        return run_delete_remote(args) if args.delete_remote else run(args)
    except Preserve as error:
        print(f"preserve: {error.reason}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
