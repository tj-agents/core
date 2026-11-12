import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

GIT_TIMEOUT_SECONDS = 60
MINIMUM_PYTHON = (3, 12)


class CreateWorktreeError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class Worktree:
    path: Path
    branch: str | None
    bare: bool


@dataclass(frozen=True, slots=True)
class Checkout:
    repository: str
    branch: str
    path: str
    head: str
    base: str
    base_head: str


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
    return result.stdout.rstrip("\r\n")


def worktrees(start: Path) -> list[Worktree]:
    entries = []
    for record in run(start, "worktree", "list", "--porcelain", "-z").split("\0\0"):
        if not record:
            continue
        fields = dict(field.partition(" ")[::2] for field in record.split("\0"))
        branch = fields.get("branch")
        entries.append(
            Worktree(
                Path(fields["worktree"]).resolve(),
                branch.removeprefix("refs/heads/") if branch else None,
                "bare" in fields,
            )
        )
    return entries


def repository_root(start: Path) -> Path:
    root = Path(run(start, "rev-parse", "--show-toplevel")).resolve()
    directory = run(root, "rev-parse", "--path-format=absolute", "--git-dir")
    common = run(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if Path(directory).resolve() == Path(common).resolve():
        return root
    entries = worktrees(start)
    if not entries or entries[0].bare:
        raise CreateWorktreeError("a non-bare primary repository is required")
    primary = entries[0].path
    if Path(run(primary, "rev-parse", "--show-toplevel")).resolve() != primary:
        raise CreateWorktreeError("cannot resolve the primary repository")
    return primary


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
    if directory.resolve() != directory or path.resolve() != path:
        raise CreateWorktreeError(f"worktree destination is redirected: {path}")
    return path


def validate_destination(repo: Path, destination: Path) -> None:
    directory = repo / ".worktrees"
    if (
        directory.resolve() != directory
        or destination.resolve().parent != directory
        or destination.absolute() != destination.resolve()
    ):
        raise CreateWorktreeError(
            f"worktrees must be direct children of {directory}: {destination}"
        )


def ensure_available(path: Path) -> None:
    directory = path.parent
    if directory.is_dir():
        for existing in directory.iterdir():
            if existing.name.casefold() == path.name.casefold():
                raise CreateWorktreeError(f"{existing} already exists")


def claim_worktree(path: Path) -> None:
    executable = shutil.which("tj.exe" if sys.platform == "win32" else "tj")
    if executable is None:
        raise CreateWorktreeError(
            f"worktree created at {path}; ownership claim failed: tj is not installed"
        )
    try:
        result = subprocess.run(
            [executable, "session", "claim-worktree", "--path", str(path)],
            cwd=path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CreateWorktreeError(
            f"worktree created at {path}; ownership claim failed: {error}"
        ) from error
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise CreateWorktreeError(
            f"worktree created at {path}; ownership claim failed: {detail}"
        )


def create(branch: str, start_point: str | None = None, *, cwd: Path) -> Checkout:
    repo = repository_root(cwd)
    validate_branch(repo, branch)
    path = worktree_path(repo, branch)
    has_origin = "origin" in run(repo, "remote").splitlines()
    if has_origin:
        run(repo, "fetch", "origin", "--prune")
    validate_branch_casing(repo, branch)
    for entry in worktrees(repo):
        if entry.branch != branch:
            continue
        if entry.path != path:
            raise CreateWorktreeError(
                f"{branch} is already checked out at {entry.path}; "
                f"resolve its ownership and migrate it to {path} before reuse"
            )
        if (
            not path.is_dir()
            or Path(run(path, "rev-parse", "--show-toplevel")).resolve() != path
        ):
            raise CreateWorktreeError(f"registered checkout needs repair: {path}")
        claim_worktree(path)
        head = run(path, "rev-parse", "HEAD")
        return Checkout(str(repo), branch, str(path), head, "(existing worktree)", head)
    ensure_available(path)
    if ref_exists(repo, f"refs/heads/{branch}"):
        base = "(existing branch)"
        base_head = run(repo, "rev-parse", f"refs/heads/{branch}^{{commit}}")
        arguments = ["worktree", "add", str(path), branch]
    elif has_origin and ref_exists(repo, f"refs/remotes/origin/{branch}"):
        base = f"origin/{branch}"
        base_head = run(repo, "rev-parse", f"refs/remotes/origin/{branch}^{{commit}}")
        arguments = ["worktree", "add", str(path), "-b", branch, "--track", base]
    else:
        if not re.fullmatch(r"[A-Z][A-Za-z0-9]*/.+", branch):
            raise CreateWorktreeError(
                "new branches require capitalized <Type>/<Name>, "
                "for example Feature/BrowserCredentials"
            )
        base = start_point or default_base(repo, has_origin)
        base_head = run(repo, "rev-parse", "--verify", f"{base}^{{commit}}")
        arguments = ["worktree", "add", str(path), "-b", branch, base_head]
    run(repo, *arguments)
    claim_worktree(path)
    return Checkout(
        str(repo), branch, str(path), run(path, "rev-parse", "HEAD"), base, base_head
    )


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < MINIMUM_PYTHON:
        print("create_worktree.py requires Python 3.12 or newer", file=sys.stderr)
        return 1
    parser = argparse.ArgumentParser(
        description=(
            "Create a worktree at "
            "<primary-repository>/.worktrees/<flattened-branch> (Python 3.12+)."
        )
    )
    parser.add_argument(
        "branch", help="branch to check out, e.g. Feature/BrowserCredentials"
    )
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--from",
        dest="start_point",
        help="verified parent ref for a new layer (default: fetched remote default)",
    )
    arguments = parser.parse_args(argv)
    try:
        result = create(arguments.branch, arguments.start_point, cwd=arguments.repo)
    except CreateWorktreeError as error:
        print(json.dumps({"error": str(error)}))
        return 1
    print(json.dumps(asdict(result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
