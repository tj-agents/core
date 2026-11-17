import io
import json
import re
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


def invoke(
    repo: Path, tool: str, arguments: dict[str, object], *, script: Path = SCRIPT
) -> str | None:
    result = subprocess.run(
        [sys.executable, "-B", str(script)],
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
def test_literal_canonical_move_is_allowed(repo: Path, tool: str) -> None:
    command = 'git worktree move old ".worktrees/Feature-Allowed"'
    assert invoke(repo, tool, {"command": command}) is None
    assert not (repo / ".worktrees").exists()


@pytest.mark.parametrize(
    "command",
    [
        "git worktree add -b Feature/Allowed .worktrees/Feature-Allowed",
        "git.exe worktree add .worktrees/Feature-Allowed",
    ],
)
def test_direct_git_worktree_add_is_denied_at_a_canonical_destination(
    repo: Path, command: str
) -> None:
    assert invoke(repo, "Bash", {"command": command}) is not None
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
        'git -c "alias.openwt=worktree add" openwt ../outside Feature/Bypass',
        'git -c "Alias.openwt=worktree add" openwt ../outside Feature/Bypass',
        "git -cALIAS.openwt=worktree openwt add ../outside Feature/Bypass",
        "git -calias.openwt=worktree openwt add ../outside Feature/Bypass",
        "git --config-env=alias.openwt=EXPANSION openwt ../outside Feature/Bypass",
        "git --config-env=Alias.openwt=EXPANSION openwt ../outside Feature/Bypass",
        'g -c "alias.openwt=worktree add" openwt ../outside Feature/Bypass',
        "g --config-env=Alias.openwt=EXPANSION openwt ../outside Feature/Bypass",
        '& $env:GIT -c "Alias.openwt=worktree add" openwt ../outside Feature/Bypass',
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
        'git worktree list; echo "$(git worktree add ../outside)"',
        "cat <<'DOC'\nLiteral git worktree documentation\nDOC\n"
        "git worktree add ../outside",
        "bash <<'SH'\ngit worktree add ../outside\nSH",
        "<<'SH' bash\ngit worktree add ../outside\nSH",
        "FLAG=value bash <<'SH'\ngit worktree add ../outside\nSH",
        "FLAG='value with spaces'post bash <<'SH'\ngit worktree add ../outside\nSH",
        "exec bash <<'SH'\ngit worktree add ../outside\nSH",
        "cat <<'SH' | bash\ngit worktree add ../outside\nSH",
        "cat <<'SH' | \\\nbash\ngit worktree add ../outside\nSH",
        "bash \\\n<<'SH'\ngit worktree add ../outside\nSH",
        'cat <<<"SH"\ngit worktree add ../outside\nSH',
        "# <<'DOC'\ngit worktree add ../outside\nDOC",
        "note=@'\n'\ngit worktree add ../outside\n: '\n'@ # '",
        "cat <<DOC\n'$(git worktree add ../outside)'\nDOC",
        "$text = @'\nLiteral git worktree documentation\n'@\n"
        "git worktree add ../outside",
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
        "git diff -- worktree README.md",
        "git status -- worktree",
        "git log -- wt",
        "rg worktree",
        "rg worktree $path",
        "rg git worktree",
        "g worktree list",
        "main=$(git symbolic-ref --short refs/remotes/origin/HEAD); git worktree prune",
        'echo "$(git worktree list --porcelain)"',
        "cd $project; git status --short",
        "echo 'git worktree add ../outside'",
        "python - <<'PY'\nprint(\"isn't balanced in the shell lexer\")\nPY",
        "bash <<'SH'\n# Use `git worktree add` in documentation.\nSH",
        "bash <<'SH'\nprintf '%s' 'Use `git worktree add` literally.'\nSH",
        "bash <<'SH'\necho git worktree add ../outside\nSH",
        "bash <<'SH'\nwt list\nSH",
        "env -i cat <<'DOC' > README.md\nUse git worktree add\nDOC",
        pytest.param(
            "cat <<'DOC' > README.md\nUse `git worktree add`; it isn't executed.\nDOC",
            id="quoted_doc_posix_here_document",
        ),
        pytest.param(
            'cat <<"DOC" > README.md\n$(git worktree add ../outside) is literal.\nDOC',
            id="quoted_doc_double_quoted_delimiter",
        ),
        pytest.param(
            "printf '%s' 'Use `git worktree add` or $(git worktree add ../outside)' "
            "> README.md",
            id="quoted_doc_single_quoted_argument",
        ),
        pytest.param(
            'Set-Content -LiteralPath README.md -Value "Use git worktree add"',
            id="quoted_doc_double_quoted_argument",
        ),
        pytest.param(
            'printf "%s" "$(cat <<\'DOC\'\n'
            'Use `git worktree add` in the guide.\nDOC\n)"',
            id="quoted_doc_inside_substitution",
        ),
    ],
)
def test_nonmutating_commands_and_literal_text_are_allowed(
    repo: Path, command: str
) -> None:
    assert invoke(repo, "Bash", {"command": command}) is None


@pytest.mark.parametrize(
    ("command", "denied"),
    [
        (
            "$text = @'\nUse `git worktree add` in the user's guide.\n'@\n"
            "Set-Content -LiteralPath README.md -Value $text",
            False,
        ),
        ('Write-Output "\\$(git worktree add ../outside)"', True),
        ('Write-Output "Use `$(git worktree add ../outside)"', False),
        ('$text = @"\n$(git worktree add ../outside)\n"@', True),
        ('pwsh -NoProfile -Command @"\ngit worktree add ../outside\n"@', True),
        ("pwsh -NoProfile -Command @'\ngit worktree add ../outside\n'@", True),
        ("pwsh -Command @'\nWrite-Output \"Use git worktree add\"\n'@", False),
    ],
)
def test_powershell_literals_and_expansions_use_powershell_syntax(
    repo: Path,
    command: str,
    denied: bool,
) -> None:
    assert (invoke(repo, "PowerShell", {"command": command}) is not None) is denied


@pytest.mark.parametrize(
    "command",
    [
        "wt switch Feature/Bad",
        "wt.exe switch Feature/Bad",
        "WT.EXE switch Feature/Bad",
        "git-wt switch Feature/Bad",
        "git-wt.exe switch Feature/Bad",
        "GIT-WT.EXE switch Feature/Bad",
        "git wt switch Feature/Bad",
        "git.exe wt switch Feature/Bad",
        "bash -c 'wt switch Feature/Bad'",
        "pwsh -Command 'git-wt switch Feature/Bad'",
        "cmd.exe /c 'git wt switch Feature/Bad'",
        "env SETTING=value wt switch Feature/Bad",
        "command -p git-wt switch Feature/Bad",
        "git -c wt.setting=value wt switch Feature/Bad",
    ],
)
def test_worktrunk_mutation_entry_points_are_denied(repo: Path, command: str) -> None:
    assert invoke(repo, "Bash", {"command": command}) is not None


@pytest.mark.parametrize(
    "command",
    [
        "wt list",
        "wt.exe list",
        "git-wt list",
        "git-wt.exe list",
        "git wt list",
        "git.exe wt list",
        "wt step diff",
        "git-wt step diff",
        "git wt step diff",
        "bash -c 'wt list'",
        "pwsh -Command 'git-wt list'",
        "cmd.exe /c 'git wt list'",
    ],
)
def test_worktrunk_passive_inventory_entry_points_are_allowed(
    repo: Path, command: str
) -> None:
    assert invoke(repo, "Bash", {"command": command}) is None


def test_shared_creator_command_is_allowed(repo: Path) -> None:
    creator = SCRIPT.with_name("create_worktree.py")
    command = f'python -B "{creator}" --repo "{repo}" Feature/Allowed'
    assert invoke(repo, "Bash", {"command": command}) is None


@pytest.mark.parametrize("tool", ("Bash", "PowerShell", "exec_command"))
def test_packaged_base_dispatcher_enforces_the_creator(repo: Path, tool: str) -> None:
    script = ROOT / "plugins/base/hooks/worktree_tool_gate.py"
    assert invoke(repo, tool, {"command": "git worktree add ../outside"}, script=script)
    assert (
        invoke(repo, tool, {"command": "git worktree list --porcelain"}, script=script)
        is None
    )
    assert (
        invoke(
            repo,
            tool,
            {"command": "echo 'Use `git worktree add` literally.'"},
            script=script,
        )
        is None
    )


def test_packaged_base_dispatcher_preserves_machine_settings_boundary(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    profile = tmp_path / "codex home"
    profile.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(profile))
    target = profile / "config.toml"
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            str(ROOT / "plugins/base/hooks/worktree_tool_gate.py"),
        ],
        input=json.dumps(
            {
                "tool_name": "PowerShell",
                "cwd": str(repo),
                "tool_input": {
                    "command": f'Set-Content -LiteralPath "{target}" -Value ignored'
                },
            }
        ),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=True,
    )
    decision = json.loads(result.stdout)["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny"
    assert "machine state" in decision["permissionDecisionReason"]


@pytest.mark.parametrize(
    ("skill", "block"),
    [("prune-worktrees", 0), ("prune-worktrees", 1), ("unmerged", 3)],
)
def test_shipped_inventory_and_pruning_commands_are_allowed(
    repo: Path, skill: str, block: int
) -> None:
    source = ROOT / ".agents/engineering/utility" / skill / "SKILL.md"
    commands = re.findall(
        r"```bash\n(.*?)\n```", source.read_text(encoding="utf-8"), re.DOTALL
    )
    assert invoke(repo, "Bash", {"command": commands[block]}) is None


def test_git_directory_switch_resolves_the_target_repository(
    repo: Path, tmp_path: Path
) -> None:
    command = f'git -C "{repo}" worktree move old ".worktrees/Feature-Allowed"'
    assert invoke(tmp_path, "exec_command", {"cmd": command}) is None


@pytest.mark.parametrize("prefix", ["cd", "Set-Location -LiteralPath"])
def test_shell_directory_switch_resolves_the_target_repository(
    repo: Path, tmp_path: Path, prefix: str
) -> None:
    command = f'{prefix} "{repo}"; git worktree move old .worktrees/Feature-Allowed'
    assert invoke(tmp_path, "PowerShell", {"command": command}) is None


def test_linked_checkout_uses_the_primary_repository(repo: Path) -> None:
    linked = repo / ".worktrees" / "Feature-First"
    git(repo, "worktree", "add", "-b", "Feature/First", str(linked))
    canonical = repo / ".worktrees" / "Feature-Second"
    assert (
        invoke(linked, "Bash", {"command": f'git worktree move old "{canonical}"'})
        is None
    )
    assert (
        invoke(
            linked,
            "Bash",
            {"command": "git worktree move old .worktrees/Feature-Second"},
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
                "cmd": "git worktree move old .worktrees/Feature-Allowed",
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
    monkeypatch.setattr("time.monotonic", lambda: 100.0)

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
                    "tool_input": {"cmd": "git worktree move old ../outside"},
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
