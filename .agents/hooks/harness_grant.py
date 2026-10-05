r"""PreToolUse hook: approve the harness's own base sync and merged-branch cleanup.

Approves exactly the commands the merge procedures prescribe, and only in a repository whose
origin is a trusted GitHub owner (`harness-trust.json` beside this file):

- `git -C "<checkout>" merge --no-edit origin/<default>` from a branch other than the default;
- `git -C "<checkout>" worktree remove -- "<worktree>"` for a linked worktree whose head is
  already on `origin/<default>`;
- `git -C "<checkout>" branch -d <branch>` for a branch already on `origin/<default>`;
- `gh secret set TJ_AGENTS_READ_TOKEN -R <owner>/<repo> --body "$(gh auth token)"` where the target
  owner is trusted — the CI read token refresh, trusted by the `-R` target rather than a checkout.

Each must be the whole command. A PreToolUse allow covers the entire tool call, so a compound
command, an unquoted or relative path, or a `--force` never matches. Anything that does not match
exits 0 with no output and is left to the normal permission flow. Codex is not granted here: its
hook contract has no equivalent allow decision yet.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

from hook_runtime import grant, is_trusted_checkout, trusted_owners

SHELL_TOOLS = {"bash", "powershell"}

_UNSAFE_PATH_CHARS = frozenset('$%!`&|;<>^\r\n')
_PATH = r'"(?P<{}>[^"\r\n]+)"'
_REF = r"(?P<{}>(?!-)[A-Za-z0-9._/-]+)"

_SYNC_RE = re.compile(
    r"\Agit -C " + _PATH.format("checkout") + r" merge --no-edit origin/" + _REF.format("ref") + r"\Z"
)
_REMOVE_RE = re.compile(
    r"\Agit -C " + _PATH.format("checkout") + r" worktree remove -- " + _PATH.format("worktree") + r"\Z"
)
_BRANCH_RE = re.compile(
    r"\Agit -C " + _PATH.format("checkout") + r" branch -d " + _REF.format("branch") + r"\Z"
)
_SECRET_RE = re.compile(
    r"\Agh secret set TJ_AGENTS_READ_TOKEN -R (?P<owner>[A-Za-z0-9-]+)/[A-Za-z0-9._-]+"
    r' --body "\$\(gh auth token\)"\Z'
)


def is_codex_invocation(data):
    return "turn_id" in data or "turnId" in data


def git(checkout, *args):
    return subprocess.run(
        ["git", "-C", str(checkout), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def git_succeeds(checkout, *args):
    try:
        git(checkout, *args)
    except (OSError, subprocess.CalledProcessError):
        return False
    return True


def absolute_dir(raw):
    if raw.endswith("\\") or any(char in raw for char in _UNSAFE_PATH_CHARS):
        return None
    path = Path(raw)
    if not path.is_absolute() or not path.is_dir():
        return None
    try:
        return path.resolve(strict=True)
    except OSError:
        return None


def default_branch(checkout):
    try:
        ref = git(checkout, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    except (OSError, subprocess.CalledProcessError):
        return None
    return ref[len("origin/"):] if ref.startswith("origin/") else None


def on_default(checkout, commit, default):
    return git_succeeds(checkout, "merge-base", "--is-ancestor", commit, "origin/" + default)


def linked_worktrees(checkout):
    """``{resolved path: head}`` for every linked worktree, excluding the main one."""
    try:
        porcelain = git(checkout, "worktree", "list", "--porcelain")
    except (OSError, subprocess.CalledProcessError):
        return {}
    entries = [block for block in porcelain.split("\n\n") if block.strip()]
    linked = {}
    for block in entries[1:]:
        fields = dict(line.split(" ", 1) for line in block.splitlines() if " " in line)
        path, head = fields.get("worktree"), fields.get("HEAD")
        if path and head:
            try:
                linked[Path(path).resolve()] = head
            except OSError:
                continue
    return linked


def sync_is_safe(checkout, ref, default):
    if ref != default:
        return False
    try:
        current = git(checkout, "symbolic-ref", "--short", "HEAD")
    except (OSError, subprocess.CalledProcessError):
        return False
    return current != default


def remove_is_safe(checkout, raw_worktree, default):
    target = absolute_dir(raw_worktree)
    if target is None:
        return False
    head = linked_worktrees(checkout).get(target)
    return head is not None and on_default(checkout, head, default)


def branch_delete_is_safe(checkout, branch, default):
    if branch == default:
        return False
    if not git_succeeds(checkout, "show-ref", "--verify", "--quiet", "refs/heads/" + branch):
        return False
    return on_default(checkout, "refs/heads/" + branch, default)


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)
    if str(data.get("tool_name", "")).lower() not in SHELL_TOOLS or is_codex_invocation(data):
        sys.exit(0)
    command = (data.get("tool_input") or {}).get("command", "")
    if not isinstance(command, str):
        sys.exit(0)
    command = command.strip()

    secret = _SECRET_RE.fullmatch(command)
    if secret:
        if secret.group("owner").casefold() in trusted_owners(__file__):
            grant("harness-grant: refreshing TJ_AGENTS_READ_TOKEN from the gh login in a trusted owner's repository.")
        sys.exit(0)

    for pattern in (_SYNC_RE, _REMOVE_RE, _BRANCH_RE):
        match = pattern.fullmatch(command)
        if match:
            break
    else:
        sys.exit(0)

    checkout = absolute_dir(match.group("checkout"))
    if checkout is None or not is_trusted_checkout(__file__, checkout):
        sys.exit(0)
    default = default_branch(checkout)
    if default is None:
        sys.exit(0)

    if pattern is _SYNC_RE:
        safe = sync_is_safe(checkout, match.group("ref"), default)
        reason = "harness-grant: syncing a feature branch with origin/" + default
    elif pattern is _REMOVE_RE:
        safe = remove_is_safe(checkout, match.group("worktree"), default)
        reason = "harness-grant: removing a worktree already merged into origin/" + default
    else:
        safe = branch_delete_is_safe(checkout, match.group("branch"), default)
        reason = "harness-grant: deleting a branch already merged into origin/" + default

    if safe:
        grant(reason + " in a trusted repository.")
    sys.exit(0)


if __name__ == "__main__":
    main()
