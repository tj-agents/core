import io
import json
import runpy
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/engineering/operation/open-worktree/scripts/worktree_gate.py"


def git(cwd: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(cwd), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=True,
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    path = tmp_path / "repo ü space"
    path.mkdir()
    git(path, "init", "-q", "-b", "main")
    git(
        path,
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@t",
        "commit",
        "--allow-empty",
        "-qm",
        "initial",
    )
    return path


def invoke(repo: Path, tool: str, arguments: dict[str, object]) -> str | None:
    result = subprocess.run(
        [sys.executable, "-B", str(SCRIPT)],
        input=json.dumps(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": tool,
                "tool_input": arguments,
                "cwd": str(repo),
            }
        ),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=True,
    )
    if not result.stdout:
        return None
    decision = json.loads(result.stdout)["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny"
    reason = str(decision["permissionDecisionReason"])
    assert "create_worktree.py" in reason
    return reason


@pytest.mark.parametrize("tool", ["Bash", "PowerShell", "exec_command"])
@pytest.mark.parametrize("operation", ["add -b Feature/Allowed", "move old"])
def test_literal_canonical_destination_is_allowed(
    repo: Path, tool: str, operation: str
) -> None:
    command = f'git worktree {operation} ".worktrees/Feature-Allowed"'
    assert invoke(repo, tool, {"command": command}) is None
    assert not (repo / ".worktrees").exists()


@pytest.mark.parametrize(
    "command",
    [
        "git worktree add ../repo.worktrees/Feature-Bad",
        "git worktree add .claude/worktrees/Feature-Bad",
        "git worktree add .codex/worktrees/Feature-Bad",
        "git worktree add .worktrees/Feature/Bad",
        "git worktree add .worktrees/../../outside",
        "git worktree move old ../outside",
        'git worktree add "$target"',
        "git worktree $'add' ../outside",
        "git worktree a${e}dd ../outside",
        "git -c core.worktree=elsewhere worktree add .worktrees/Feature-Bad",
        "git worktree add --unknown .worktrees/Feature-Bad",
        "if true; then git worktree add ../outside; fi",
        "GIT_DIR=elsewhere git worktree add ../outside",
        "GIT_DIR=elsewhere; git worktree add .worktrees/Feature-Bad",
        "(cd elsewhere); git worktree add .worktrees/Feature-Bad",
        "cd elsewhere || git worktree add .worktrees/Feature-Bad",
        "pushd elsewhere; popd; git worktree add .worktrees/Feature-Bad",
        "claude --worktree=example",
        "$GIT worktree add ../outside",
        "& $env:GIT worktree add ../outside",
        "g worktree add ../outside",
        "g worktree a${e}dd ../outside",
        "& $env:GIT worktree $action ../outside",
        "rg `git worktree add ../outside`",
        'echo "`git worktree add ../outside`"',
        'printf "%s" "$(git worktree add ../outside)"',
        'rg "$(git worktree move old ../outside)"',
    ],
)
def test_noncanonical_or_unresolved_mutation_is_denied(
    repo: Path, command: str
) -> None:
    assert invoke(repo, "Bash", {"command": command}) is not None
    assert not (repo / ".worktrees").exists()


@pytest.mark.parametrize(
    "command",
    [
        "git worktree list --porcelain",
        "git worktree prune --dry-run",
        "git status --short",
        "rg worktree",
        "rg worktree $path",
        "rg git worktree",
        "g worktree list",
        "cd $project; git status --short",
        "echo 'git worktree add ../outside'",
        "python - <<'PY'\nprint(\"isn't balanced in the shell lexer\")\nPY",
    ],
)
def test_nonmutating_commands_and_literal_text_are_allowed(
    repo: Path, command: str
) -> None:
    assert invoke(repo, "Bash", {"command": command}) is None


def test_git_directory_switch_resolves_the_target_repository(
    repo: Path, tmp_path: Path
) -> None:
    command = f'git -C "{repo}" worktree add ".worktrees/Feature-Allowed"'
    assert invoke(tmp_path, "exec_command", {"cmd": command}) is None


@pytest.mark.parametrize("prefix", ["cd", "Set-Location -LiteralPath"])
def test_shell_directory_switch_resolves_the_target_repository(
    repo: Path, tmp_path: Path, prefix: str
) -> None:
    command = f'{prefix} "{repo}"; git worktree add .worktrees/Feature-Allowed'
    assert invoke(tmp_path, "PowerShell", {"command": command}) is None


def test_linked_checkout_uses_the_primary_repository(repo: Path) -> None:
    linked = repo / ".worktrees" / "Feature-First"
    git(repo, "worktree", "add", "-b", "Feature/First", str(linked))
    canonical = repo / ".worktrees" / "Feature-Second"
    assert (
        invoke(linked, "Bash", {"command": f'git worktree add "{canonical}"'}) is None
    )
    assert (
        invoke(
            linked, "Bash", {"command": "git worktree add .worktrees/Feature-Second"}
        )
        is not None
    )


def test_tool_workdir_takes_precedence_over_session_directory(
    repo: Path, tmp_path: Path
) -> None:
    assert (
        invoke(
            tmp_path,
            "exec_command",
            {
                "cmd": "git worktree add .worktrees/Feature-Allowed",
                "workdir": str(repo),
            },
        )
        is None
    )


@pytest.mark.parametrize(
    ("tool", "arguments"),
    [
        ("EnterWorktree", {"name": "bad"}),
        ("Agent", {"isolation": "worktree"}),
        ("Task", {"isolation": "worktree"}),
        ("mcp__codex_tui__create_worktree", {}),
    ],
)
def test_native_creation_routes_to_core(
    repo: Path, tool: str, arguments: dict[str, object]
) -> None:
    assert invoke(repo, tool, arguments) is not None


def test_claude_worktree_create_event_refuses_default_placement(repo: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-B", str(SCRIPT)],
        input=json.dumps(
            {"hook_event_name": "WorktreeCreate", "name": "example", "cwd": str(repo)}
        ),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )
    assert result.returncode == 2
    assert "create_worktree.py" in result.stderr
    assert not result.stdout


def test_git_timeout_returns_denial_before_the_host_deadline(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def stalled_git(
        command: list[str], *, timeout: float, **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        assert 0 < timeout <= 10
        raise subprocess.TimeoutExpired(command, timeout)

    monkeypatch.syspath_prepend(str(SCRIPT.parent))
    monkeypatch.setattr(subprocess, "run", stalled_git)
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(
            json.dumps(
                {
                    "tool_name": "exec_command",
                    "tool_input": {"cmd": "git worktree add ../outside"},
                    "cwd": str(repo),
                }
            )
        ),
    )
    main = cast(Callable[[], int], runpy.run_path(str(SCRIPT))["main"])
    assert main() == 0
    decision = json.loads(capsys.readouterr().out)["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny"
    assert "timed out" in decision["permissionDecisionReason"]
