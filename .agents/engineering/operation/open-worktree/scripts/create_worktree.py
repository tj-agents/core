import argparse
import json
import subprocess
from pathlib import Path

GIT_TIMEOUT_SECONDS = 60


class CreateWorktreeError(RuntimeError):
    pass


def git(cwd: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    command = ["git", "-C", str(cwd), *arguments]
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CreateWorktreeError(f"{' '.join(command)}: {error}") from error


def run(cwd: Path, *arguments: str) -> str:
    result = git(cwd, *arguments)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise CreateWorktreeError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout.strip()


def repository_root(start: Path) -> Path:
    common = run(start, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common).resolve().parent


def default_base(repo: Path, has_origin: bool) -> str:
    if has_origin:
        for line in run(repo, "ls-remote", "--symref", "origin", "HEAD").splitlines():
            if line.startswith("ref: refs/heads/") and line.endswith("\tHEAD"):
                remote_branch = line.removeprefix("ref: refs/heads/").split("\t")[0]
                return f"origin/{remote_branch}"
        raise CreateWorktreeError("origin does not advertise a default branch")
    return run(repo, "symbolic-ref", "--quiet", "--short", "HEAD")


def ref_exists(repo: Path, ref: str) -> bool:
    return git(repo, "show-ref", "--verify", "--quiet", ref).returncode == 0


def validate_branch(repo: Path, branch: str) -> None:
    checked = git(repo, "check-ref-format", "--branch", branch)
    if checked.returncode or checked.stdout.strip() != branch:
        raise CreateWorktreeError(f"invalid branch name: {branch!r}")


def validate_branch_casing(repo: Path, branch: str) -> None:
    refs = run(
        repo, "for-each-ref", "--format=%(refname)", "refs/heads", "refs/remotes/origin"
    )
    for ref in refs.splitlines():
        existing = ref.removeprefix("refs/heads/").removeprefix("refs/remotes/origin/")
        if existing.casefold() == branch.casefold() and existing != branch:
            raise CreateWorktreeError(f"use the existing branch casing: {existing}")


def worktree_path(repo: Path, branch: str) -> Path:
    directory = repo / ".worktrees"
    path = directory / branch.replace("/", "-")
    if directory.resolve() != directory or path.resolve().parent != directory:
        raise CreateWorktreeError(f"worktree destination is redirected: {path}")
    if directory.is_dir():
        for existing in directory.iterdir():
            if existing.name.casefold() == path.name.casefold():
                raise CreateWorktreeError(f"{existing} already exists")
    return path


def create(
    branch: str, start_point: str | None = None, *, cwd: Path | None = None
) -> dict[str, str]:
    repo = repository_root(cwd or Path.cwd())
    validate_branch(repo, branch)
    path = worktree_path(repo, branch)
    has_origin = "origin" in run(repo, "remote").splitlines()
    if has_origin:
        run(repo, "fetch", "origin", "--prune")
    validate_branch_casing(repo, branch)
    if ref_exists(repo, f"refs/heads/{branch}"):
        base = "(existing branch)"
        base_head = run(repo, "rev-parse", f"refs/heads/{branch}^{{commit}}")
        arguments = ["worktree", "add", str(path), branch]
    elif has_origin and ref_exists(repo, f"refs/remotes/origin/{branch}"):
        base = f"origin/{branch}"
        base_head = run(repo, "rev-parse", f"refs/remotes/origin/{branch}^{{commit}}")
        arguments = ["worktree", "add", str(path), "-b", branch, "--track", base]
    else:
        base = start_point or default_base(repo, has_origin)
        base_head = run(repo, "rev-parse", "--verify", f"{base}^{{commit}}")
        arguments = ["worktree", "add", str(path), "-b", branch, base_head]
    run(repo, *arguments)
    return {
        "repository": str(repo),
        "branch": branch,
        "path": str(path),
        "head": run(path, "rev-parse", "HEAD"),
        "base": base,
        "base_head": base_head,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create a worktree at "
            "<primary-repository>/.worktrees/<flattened-branch> (Python 3.12+)."
        )
    )
    parser.add_argument(
        "branch", help="branch to check out, e.g. Feature/BrowserCredentials"
    )
    parser.add_argument(
        "--from",
        dest="start_point",
        help="verified parent ref for a new layer (default: fetched remote default)",
    )
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
