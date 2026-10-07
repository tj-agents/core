import argparse
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path


GIT_SELECTORS = {
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_COMMON_DIR",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CEILING_DIRECTORIES",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
}
BRANCH = re.compile(r"^(Feature|Refactor|Bug|Fix|Docs|Chore)/.+$")
SHA = re.compile(r"^[0-9a-fA-F]{40,64}$")
TIMEOUT = 30


class Refusal(RuntimeError):
    pass


def environment():
    return {key: value for key, value in os.environ.items() if key.upper() not in GIT_SELECTORS}


def git(cwd, *args, timeout=TIMEOUT):
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            env=environment(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Refusal(f"Git could not run: {error}") from error
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise Refusal(detail or f"Git exited {result.returncode}")
    return result.stdout.strip()


def identity(path):
    return str(Path(path).resolve()).replace("\\", "/").casefold()


def read_pointer(path, prefixed):
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise Refusal(f"Cannot read Git registration {path}: {error}") from error
    prefix = "gitdir:"
    if prefixed:
        if not value.lower().startswith(prefix):
            raise Refusal(f"Invalid Git registration {path}")
        target = value[len(prefix):].strip()
    else:
        target = value
    if not target:
        raise Refusal(f"Invalid Git registration {path}")
    return (path.parent / target).resolve()


def resolve_repository(caller):
    common = Path(git(caller, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()
    caller_root = Path(git(caller, "rev-parse", "--show-toplevel")).resolve()
    caller_git = Path(git(caller, "rev-parse", "--absolute-git-dir")).resolve()
    repository = common.parent
    if caller_git == common:
        if caller_root != repository or not (caller_root / ".git").is_dir():
            raise Refusal("Separately relocated primary Git directories are unsupported")
    else:
        if caller_git.parent != common / "worktrees":
            raise Refusal("The caller is not a conventional linked worktree")
        if read_pointer(caller_root / ".git", prefixed=True) != caller_git:
            raise Refusal("Linked worktree registration does not match the caller")
        if read_pointer(caller_git / "gitdir", prefixed=False) != caller_root / ".git":
            raise Refusal("Linked worktree registration does not match the caller")
    if common.name != ".git" or git(repository, "rev-parse", "--is-bare-repository") != "false":
        raise Refusal("An ordinary non-bare repository with its common .git directory is required")
    checked_common = Path(git(repository, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()
    if checked_common != common:
        raise Refusal("Common repository identity does not match")
    if git(repository, "rev-parse", "--is-inside-work-tree") != "true":
        raise Refusal("The common directory parent is not the primary worktree")
    if Path(git(repository, "rev-parse", "--show-toplevel")).resolve() != repository:
        raise Refusal("Separately relocated Git directories are unsupported")
    return repository, common


def validate_branch(repository, value, name, typed=True):
    if not value or value.startswith("-") or (typed and not BRANCH.fullmatch(value)):
        raise Refusal(f"{name} must use a capitalized supported type prefix")
    if git(repository, "check-ref-format", "--branch", value) != value:
        raise Refusal(f"Invalid {name}: {value}")


def validate_sha(value, name):
    if not value or not SHA.fullmatch(value):
        raise Refusal(f"{name} must be a full hexadecimal commit ID")
    return value.lower()


def worktrees(repository):
    records = []
    current = {}
    for line in git(repository, "worktree", "list", "--porcelain", "-z").split("\0"):
        if not line:
            if current:
                records.append(current)
                current = {}
        elif " " in line:
            key, value = line.split(" ", 1)
            current[key] = value
        else:
            current[line] = ""
    if current:
        records.append(current)
    return records


def advertised_branches(repository, remote):
    output = git(repository, "ls-remote", "--symref", remote, "HEAD", "refs/heads/*")
    heads = {}
    default = None
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) != 2:
            continue
        value, ref = parts
        if value.startswith("ref: ") and ref == "HEAD":
            target = value[5:]
            if target.startswith("refs/heads/"):
                default = target.removeprefix("refs/heads/")
        elif ref.startswith("refs/heads/") and SHA.fullmatch(value):
            heads[ref] = value.lower()
    if not heads:
        raise Refusal(f"Remote {remote} advertises no branches")
    return default, heads


def local_branches(repository):
    return [line for line in git(repository, "for-each-ref", "--format=%(refname:strip=2)", "refs/heads").splitlines() if line]


def registered_conflict(records, branch, target):
    desired_branch = branch.casefold()
    desired_path = identity(target)
    for record in records:
        path = record.get("worktree")
        registered = record.get("branch", "").removeprefix("refs/heads/")
        if path and identity(path) == desired_path:
            raise Refusal(f"Target is already registered as a worktree: {path}")
        if registered and registered.casefold() == desired_branch:
            raise Refusal(f"Branch is already registered at: {path}")


def collision(branch, names, allowed=()):
    allowed_folded = {value.casefold() for value in allowed}
    for name in names:
        if name.casefold() == branch.casefold() and name not in allowed:
            raise Refusal(f"Branch collides with existing ref: {name}")
    if branch.casefold() in allowed_folded and branch not in allowed:
        raise Refusal(f"Branch casing differs from existing ref: {branch}")


def reparse(path):
    if path.is_symlink():
        return True
    try:
        return bool(path.lstat().st_file_attributes & 0x400)
    except (AttributeError, OSError):
        return False


def prepare_target(repository, common, branch):
    root = repository / ".worktrees"
    target = root / branch.replace("/", "-")
    if target.exists() or target.is_symlink():
        raise Refusal(f"Target path already exists: {target}")
    if root.exists() and (not root.is_dir() or reparse(root)):
        raise Refusal(".worktrees must be a normal directory")
    resolved_parent = root.resolve()
    try:
        resolved_parent.relative_to(repository.resolve())
    except ValueError as error:
        raise Refusal("The worktree parent escapes the repository") from error
    tracked = git(repository, "ls-files", "--", ".worktrees")
    if tracked:
        raise Refusal("Tracked paths exist beneath .worktrees")
    return root, target


def ensure_ignored(repository, common, target):
    exclude = common / "info" / "exclude"
    try:
        existing = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
        lines = existing.splitlines()
        if "/.worktrees/" not in lines:
            exclude.parent.mkdir(parents=True, exist_ok=True)
            suffix = "" if not existing or existing.endswith(("\n", "\r")) else "\n"
            exclude.write_text(existing + suffix + "/.worktrees/\n", encoding="utf-8")
    except OSError as error:
        raise Refusal(f"Cannot update common Git exclude file: {error}") from error
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", "--no-index", str(target)],
            cwd=str(repository), env=environment(), capture_output=True, text=True, timeout=TIMEOUT, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Refusal(f"Git could not check worktree exclusion: {error}") from error
    if result.returncode:
        raise Refusal(".worktrees is not ignored by the common Git exclude file")


def acquire_lock(common, branch, target):
    path = common / "agent-worktree-allocation.lock"
    token = uuid.uuid4().hex
    try:
        descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as error:
        raise Refusal("An allocation lock already exists; reconcile its owner") from error
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump({"pid": os.getpid(), "branch": branch, "target": str(target), "token": token}, stream)
    except OSError:
        try:
            path.unlink()
        except OSError:
            pass
        raise
    return path, token


def release_lock(lock):
    path, token = lock
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("token") != token:
            raise Refusal(f"Allocation lock ownership changed: {path}")
        path.unlink()
    except FileNotFoundError:
        pass
    except OSError as error:
        raise Refusal(f"Cannot release allocation lock {path}: {error}") from error


def verify(repository, common, target, branch, base_ref, base_head):
    records = worktrees(repository)
    if not any(identity(record.get("worktree", "")) == identity(target) and record.get("branch") == f"refs/heads/{branch}" for record in records):
        raise Refusal("Git did not register the new worktree as expected")
    head = git(target, "rev-parse", "--verify", "HEAD^{commit}").lower()
    if head != base_head:
        raise Refusal("The new worktree HEAD does not match its verified base")
    actual_common = Path(git(target, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()
    if actual_common != common:
        raise Refusal("The new worktree has an unexpected common Git directory")
    if git(target, "status", "--porcelain"):
        raise Refusal("The new worktree is not clean")
    return {"repository": str(repository), "worktree": str(target), "branch": branch, "head": head, "base_ref": base_ref, "base_head": base_head, "created": True}


def create(args):
    caller = Path(args.repository).resolve()
    repository, common = resolve_repository(caller)
    validate_branch(repository, args.branch, "branch")
    if args.base:
        validate_branch(repository, args.base, "base", typed=False)
    if args.expected_base:
        expected_base = validate_sha(args.expected_base, "--expected-base")
    else:
        expected_base = None
    if args.expected_head:
        expected_head = validate_sha(args.expected_head, "--expected-head")
    else:
        expected_head = None
    if args.existing and (args.base or expected_base):
        raise Refusal("--existing cannot be combined with --base or --expected-base")
    if args.existing != bool(expected_head):
        raise Refusal("--expected-head is required exactly when --existing is used")
    remotes = git(repository, "remote").splitlines()
    if not args.remote or args.remote.startswith("-") or args.remote not in remotes:
        raise Refusal(f"Unknown remote: {args.remote}")
    try:
        git(repository, "check-ref-format", "refs/remotes/" + args.remote)
    except Refusal as error:
        raise Refusal(f"Invalid remote name: {args.remote}") from error
    root, target = prepare_target(repository, common, args.branch)
    lock = acquire_lock(common, args.branch, target)
    try:
        root.mkdir(exist_ok=True)
        if reparse(root):
            raise Refusal(".worktrees must not be a symlink, junction, or reparse point")
        ensure_ignored(repository, common, target)
        records = worktrees(repository)
        registered_conflict(records, args.branch, target)
        default, advertised = advertised_branches(repository, args.remote)
        local = local_branches(repository)
        remote_names = [ref.removeprefix("refs/heads/") for ref in advertised]
        if args.existing:
            remote_match = next((name for name in remote_names if name.casefold() == args.branch.casefold()), None)
            if remote_match and remote_match != args.branch:
                raise Refusal(f"Branch casing differs from existing ref: {remote_match}")
            git(repository, "fetch", "--prune", args.remote)
            local_match = next((name for name in local_branches(repository) if name.casefold() == args.branch.casefold()), None)
            if local_match and local_match != args.branch:
                raise Refusal(f"Branch casing differs from existing ref: {local_match}")
            if local_match:
                base_ref = f"refs/heads/{args.branch}"
                base_head = git(repository, "rev-parse", "--verify", base_ref + "^{commit}").lower()
                if base_head != expected_head:
                    raise Refusal("The local existing branch does not match --expected-head")
                git(repository, "worktree", "add", str(target), args.branch)
            else:
                source_ref = "refs/heads/" + args.branch
                if source_ref not in advertised:
                    raise Refusal(f"Remote branch does not exist: {args.branch}")
                base_ref = f"refs/remotes/{args.remote}/{args.branch}"
                git(repository, "fetch", "--prune", args.remote, "+" + source_ref + ":" + base_ref)
                base_head = git(repository, "rev-parse", "--verify", base_ref + "^{commit}").lower()
                if base_head != advertised[source_ref] or base_head != expected_head:
                    raise Refusal("The remote existing branch does not match --expected-head")
                git(repository, "worktree", "add", "--no-track", "-b", args.branch, str(target), base_head)
                git(repository, "branch", "--set-upstream-to=" + base_ref, args.branch)
        else:
            collision(args.branch, local + remote_names)
            selected = args.base or default
            if selected is None:
                raise Refusal(f"Remote {args.remote} does not advertise a symbolic default branch")
            source_ref = "refs/heads/" + selected
            if source_ref not in advertised:
                raise Refusal(f"Remote base branch does not exist: {selected}")
            base_ref = f"refs/remotes/{args.remote}/{selected}"
            git(repository, "fetch", "--prune", args.remote, "+" + source_ref + ":" + base_ref)
            base_head = git(repository, "rev-parse", "--verify", base_ref + "^{commit}").lower()
            if base_head != advertised[source_ref]:
                raise Refusal("The selected remote branch changed; inspect and retry")
            if expected_base and base_head != expected_base:
                raise Refusal("The selected remote branch does not match --expected-base")
            git(repository, "worktree", "add", "--no-track", "-b", args.branch, str(target), base_head)
        return verify(repository, common, target, args.branch, base_ref, base_head)
    finally:
        release_lock(lock)


def parser():
    result = argparse.ArgumentParser()
    commands = result.add_subparsers(dest="command", required=True)
    create_parser = commands.add_parser("create")
    create_parser.add_argument("--repository", required=True)
    create_parser.add_argument("--branch", required=True)
    create_parser.add_argument("--remote", default="origin")
    create_parser.add_argument("--base")
    create_parser.add_argument("--expected-base")
    create_parser.add_argument("--existing", action="store_true")
    create_parser.add_argument("--expected-head")
    create_parser.set_defaults(action=create)
    return result


def main():
    try:
        args = parser().parse_args()
        print(json.dumps(args.action(args), separators=(",", ":")))
        return 0
    except Refusal as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
