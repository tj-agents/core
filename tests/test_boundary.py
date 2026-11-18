import importlib.util
import json
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / ".agents/hooks/tier_gate.py"


def _load_gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location("boundary_gate", GATE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = _load_gate()
EMPLOYER = {
    "schema_version": 3,
    "tier": "employer-a",
    "applies": "stack-present",
    "detect": {"all": [{"remote_host": "github.com"}, {"remote": "^employer-a/"}]},
    "employer": {"context_skill": "communication-context"},
}


@dataclass(frozen=True, slots=True)
class Machine:
    home: Path
    state: Path
    plugin: Path
    work: Path
    personal: Path


def _repository(path: Path, url: str) -> Path:
    (path / ".git").mkdir(parents=True)
    (path / ".git" / "config").write_text(
        f'[remote "origin"]\n\turl = {url}\n', encoding="utf-8"
    )
    return path


def _payload(
    cache: Path, plugin: str, skills: tuple[str, ...], repository: str
) -> Path:
    payload = cache / "personal-tools" / plugin / "1"
    for skill in skills:
        (payload / "skills" / skill).mkdir(parents=True)
        (payload / "skills" / skill / "SKILL.md").write_text(
            f"---\nname: {skill}\nkind: knowledge\n---\nBody.\n", encoding="utf-8"
        )
    (payload / ".claude-plugin").mkdir(parents=True)
    manifest = {"name": plugin, "repository": f"https://github.com/{repository}"}
    (payload / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    return payload


@pytest.fixture
def machine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Machine:
    home = tmp_path / "home"
    cache = home / ".claude" / "plugins" / "cache"
    plugin = _payload(cache, "base", ("review",), "tool-owner/base")
    employer = _payload(
        cache, "employer-a", ("communication-context",), "tool-owner/employer-a"
    )
    (employer / "tier.json").write_text(json.dumps(EMPLOYER), encoding="utf-8")
    state = tmp_path / "state"
    (state / "github-app").mkdir(parents=True)
    identity = {
        "reviewer": "the-human",
        "accounts": ["the-human", "side-project"],
        "app": {"slug": "helper-bot"},
    }
    (state / "github-app" / "identity.json").write_text(
        json.dumps(identity), encoding="utf-8"
    )
    for variable in (
        "CLAUDE_CONFIG_DIR",
        "CODEX_HOME",
        "PLUGIN_ROOT",
        "CODEX_PLUGIN_ROOT",
        "RIPGREP_CONFIG_PATH",
    ):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin))
    work = _repository(tmp_path / "work", "git@github.com:employer-a/service.git")
    personal = _repository(
        tmp_path / "personal", "https://github.com/side-project/app.git"
    )
    return Machine(home, state, plugin, work, personal)


def _reason(
    machine: Machine, tool: str, tool_input: Mapping[str, object], cwd: Path
) -> str:
    payload = {"tool_name": tool, "tool_input": dict(tool_input), "cwd": str(cwd)}
    reason: str = gate.boundary_reason(payload, machine.state)
    return reason


@pytest.mark.parametrize(
    "relative",
    [
        ".claude/projects/some-project/memory/lesson.md",
        ".claude/projects/some-project/memory/MEMORY.md",
        ".codex/memories/a.md",
    ],
)
def test_boundary_reason_blocks_every_host_memory_write(
    machine: Machine, relative: str
) -> None:
    target = machine.home / relative
    reason = _reason(
        machine,
        "Write",
        {"file_path": str(target), "content": "Remember this."},
        machine.personal,
    )
    assert "is host memory" in reason
    assert "template:self-repair" in reason


def test_boundary_reason_allows_other_host_project_files(machine: Machine) -> None:
    target = machine.home / ".claude/projects/some-project/session.jsonl"
    assert (
        _reason(
            machine,
            "Write",
            {"file_path": str(target), "content": "x"},
            machine.personal,
        )
        == ""
    )


def test_personal_tool_reads_are_allowed_in_work(machine: Machine) -> None:
    skill = machine.plugin / "skills" / "review" / "SKILL.md"
    command = f'Get-Content "{skill}","{machine.plugin}/other"'
    assert _reason(machine, "PowerShell", {"command": command}, machine.work) == ""


def test_personal_tool_invocation_is_allowed_in_work(machine: Machine) -> None:
    assert (
        _reason(machine, "Bash", {"command": "personal-tools check"}, machine.work)
        == ""
    )


def test_tool_gate_fails_open_on_malformed_input() -> None:
    result = subprocess.run(
        [sys.executable, "-B", str(GATE), "--tool-gate"],
        input="not json",
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert (result.returncode, result.stdout) == (0, "")


SETTINGS = (
    ".claude/settings.json",
    ".claude/settings.local.json",
    ".codex/config.toml",
    ".codex/rules/default.rules",
)


@pytest.fixture
def settings(machine: Machine) -> Machine:
    for relative in SETTINGS:
        (machine.home / relative).parent.mkdir(parents=True, exist_ok=True)
        (machine.home / relative).write_text("{}\n", encoding="utf-8")
    return machine


def _writer_input(tool: str, target: Path) -> dict[str, object]:
    match tool:
        case "Write":
            return {"file_path": str(target), "content": "{}"}
        case "Edit":
            return {"file_path": str(target), "old_string": "{", "new_string": "["}
        case "MultiEdit":
            edits = [{"old_string": "{", "new_string": "["}]
            return {"file_path": str(target), "edits": edits}
        case "NotebookEdit":
            return {"notebook_path": str(target), "new_source": "x"}
        case "apply_patch":
            patch = f"*** Begin Patch\n*** Update File: {target}\n+x\n*** End Patch"
            return {"command": patch}
        case _:
            raise AssertionError(tool)


@pytest.mark.parametrize("relative", SETTINGS)
def test_boundary_reason_blocks_writes_to_user_host_settings(
    machine: Machine, relative: str
) -> None:
    reason = _reason(
        machine,
        "Write",
        _writer_input("Write", machine.home / relative),
        machine.personal,
    )
    assert "is user-level host settings or machine state" in reason
    assert "base:machine-agnostic" in reason


def test_boundary_reason_blocks_writes_into_the_agent_state_directory(
    machine: Machine,
) -> None:
    target = machine.state / "github-app" / "identity.json"
    reason = _reason(machine, "Write", _writer_input("Write", target), machine.personal)
    assert "is user-level host settings or machine state" in reason


@pytest.mark.parametrize(
    "tool", ["Write", "Edit", "MultiEdit", "NotebookEdit", "apply_patch"]
)
def test_boundary_reason_blocks_every_file_writer_on_host_settings(
    settings: Machine, tool: str
) -> None:
    target = settings.home / ".codex" / "config.toml"
    reason = _reason(settings, tool, _writer_input(tool, target), settings.personal)
    assert "is user-level host settings or machine state" in reason


def test_boundary_reason_follows_configured_host_homes(
    machine: Machine, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude home"))
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex home"))
    for relative in ("claude home/settings.json", "codex home/rules/a.rules"):
        target = tmp_path / relative
        reason = _reason(
            machine, "Write", _writer_input("Write", target), machine.personal
        )
        assert "is user-level host settings or machine state" in reason


@pytest.mark.parametrize(
    ("tool", "command"),
    [
        ("Bash", "echo '{}' > ~/.claude/settings.json"),
        ("Bash", 'cp new.toml "$HOME/.codex/config.toml"'),
        ("PowerShell", "Set-Content $env:USERPROFILE\\.codex\\rules\\new.rules x"),
        ("PowerShell", "Copy-Item a.json ~/.claude/settings.local.json"),
    ],
)
def test_boundary_reason_blocks_shell_commands_naming_host_settings(
    settings: Machine, tool: str, command: str
) -> None:
    reason = _reason(settings, tool, {"command": command}, settings.personal)
    assert "is user-level host settings or machine state" in reason


def test_boundary_reason_blocks_shell_commands_naming_machine_state(
    machine: Machine,
) -> None:
    command = ["bash", "-lc", f"echo x > {machine.state.as_posix()}/new.json"]
    reason = _reason(machine, "exec_command", {"command": command}, machine.personal)
    assert "is user-level host settings or machine state" in reason


@pytest.mark.parametrize("tool", ["PowerShell", "Bash", "shell", "exec_command"])
@pytest.mark.parametrize(
    "command",
    [
        "Get-Content '{target}' -TotalCount 75",
        'Get-Content "{target}" | Select-Object -First 35',
        "rg -n 'credential|account|token|scope|configuration' '{target}' "
        "| Select-Object -First 35",
        "cat '{target}' | head -n 75",
        "grep -n 'credential' '{target}' | tail -n 35",
        "Get-Content '{target}'; rg -n 'configuration' '{target}'",
        "cat '{target}' && head -n 15 '{target}'",
        "cat '{target}' || head -n 15 '{target}'",
        "cat '{target}'\nhead -n 15 '{target}'",
        "cat '{target}';\nhead -n 15 '{target}'",
        "Get-Content '{target}'\rGet-Content '{target}'",
    ],
)
def test_boundary_reason_allows_literal_inspection(
    settings: Machine, tool: str, command: str
) -> None:
    targets = [
        settings.home / ".codex/config.toml",
        settings.state / "runtime with spaces/github_gate.py",
        settings.home / ".claude/projects/example/memory/lesson.md",
    ]
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("configuration\n", encoding="utf-8")
        for spelling in (target.as_posix(), str(target).replace("/", "\\")):
            assert (
                _reason(
                    settings,
                    tool,
                    {"command": command.format(target=spelling)},
                    settings.personal,
                )
                == ""
            )


def test_boundary_reason_allows_reported_inspection_pipeline(settings: Machine) -> None:
    runtime = settings.state / "github-gate/runtime/github_gate.py"
    runtime.parent.mkdir(parents=True)
    runtime.write_text("configuration\n", encoding="utf-8")
    bindings = settings.state / "bin/.agents"
    bindings.mkdir(parents=True)
    config = settings.home / ".codex/config.toml"
    command = (
        f"Get-Content '{runtime.as_posix()}' -TotalCount 75; "
        "rg -n 'credential|account|token|scope|configuration' "
        f"'{runtime.as_posix()}' | Select-Object -First 35; "
        f"rg -n 'GIT_CONFIG_COUNT|bot_identity.py' '{config.as_posix()}' "
        f"'{bindings.as_posix()}' | Select-Object -First 15"
    )
    assert (
        _reason(settings, "PowerShell", {"command": command}, settings.personal) == ""
    )


@pytest.mark.parametrize(
    "command",
    [
        'cat "$HOME/.codex/config.toml"',
        "Get-Content $env:USERPROFILE\\.codex\\config.toml",
        "Get-Content ~/.codex/config.toml",
        "rg -n configuration .",
    ],
)
def test_boundary_reason_allows_inspection_from_machine_state(
    settings: Machine, command: str
) -> None:
    assert _reason(settings, "shell", {"command": command}, settings.state) == ""


@pytest.mark.parametrize(
    "command",
    [
        "Set-Content '{target}' x",
        "Remove-Item '{target}'",
        "rm '{target}'",
        "sed -i 's/a/b/' '{target}'",
        "cat local.txt > '{target}'",
        "cat local.txt >> '{target}'",
        "rg x local.txt 2> '{target}'",
        "Get-Content local.txt *> '{target}'",
        "Get-Content local.txt | Set-Content '{target}' x",
        "Get-Content local.txt; Set-Content '{target}' x",
        "cat local.txt && rm '{target}'",
        "cat local.txt || rm '{target}'",
        "cat local.txt\nrm '{target}'",
        "cat local.txt;\nrm '{target}'",
        "cat local.txt\n\nrm '{target}'",
        "Get-Content local.txt;\r\nSet-Content '{target}' x",
        "Get-Content local.txt\rSet-Content '{target}' x",
        "cat local.txt & rm '{target}'",
        "cat local.txt | tee '{target}'",
        "rg --pre=mutator pattern '{target}'",
        "rg --pre mutator pattern '{target}'",
        "rg --hostname-bin=mutator pattern '{target}'",
        "cat $(rm '{target}')",
        "Get-Content \"$(Set-Content '{target}' x)\"",
        "Get-Content local.txt | ForEach-Object {{ Set-Content '{target}' x }}",
        "cat `rm '{target}'`",
        "unknown-command '{target}'",
        "cat local.txt; unknown-command '{target}'",
        "cat local.txt; 'unterminated '{target}'",
    ],
)
def test_boundary_reason_retains_protection_for_mutating_or_uncertain_commands(
    settings: Machine, command: str
) -> None:
    for target in (
        settings.home / ".codex/config.toml",
        settings.state / "identity.json",
    ):
        reason = _reason(
            settings,
            "shell",
            {"command": command.format(target=target.as_posix())},
            settings.personal,
        )
        assert "is user-level host settings or machine state" in reason


@pytest.mark.parametrize("mutating", [False, True])
def test_hook_entry_point_distinguishes_inspection_from_later_write(
    settings: Machine, monkeypatch: pytest.MonkeyPatch, mutating: bool
) -> None:
    monkeypatch.setenv("AGENT_STATE_DIRECTORY", str(settings.state))
    target = (settings.home / ".codex/config.toml").as_posix()
    command = f"Get-Content '{target}' | Select-Object -First 15"
    if mutating:
        command += f"; Set-Content '{target}' x"
    result = subprocess.run(
        [sys.executable, "-B", str(GATE), "--tool-gate"],
        input=json.dumps(
            {
                "tool_name": "PowerShell",
                "tool_input": {"command": command},
                "cwd": str(settings.personal),
            }
        ),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=15,
    )
    assert result.returncode == 0
    if mutating:
        decision = json.loads(result.stdout)["hookSpecificOutput"]
        assert decision["permissionDecision"] == "deny"
    else:
        assert result.stdout == ""


@pytest.mark.parametrize(
    "command",
    [
        "cat local.txt; rm '{target}'",
        "Get-Content local.txt | Set-Content '{target}' x",
        "cat local.txt >> '{target}'",
    ],
)
def test_boundary_reason_retains_host_memory_protection(
    settings: Machine, command: str
) -> None:
    target = settings.home / ".codex/memories/lesson.md"
    target.parent.mkdir(parents=True)
    reason = _reason(
        settings,
        "shell",
        {"command": command.format(target=target.as_posix())},
        settings.personal,
    )
    assert "is host memory" in reason


@pytest.mark.parametrize(
    ("command", "allowed"),
    [
        ("rg pattern '{target}'", False),
        ("rg --no-config pattern '{target}'", True),
        ("rg -e --no-config '{target}'", False),
        ("rg -- --no-config '{target}'", False),
        ("rg --no-config pattern local.txt; rg pattern '{target}'", False),
    ],
)
def test_boundary_reason_accounts_for_ripgrep_configuration(
    settings: Machine, monkeypatch: pytest.MonkeyPatch, command: str, allowed: bool
) -> None:
    config = settings.personal / "ripgrep.conf"
    config.write_text("--pre=mutator\n", encoding="utf-8")
    monkeypatch.setenv("RIPGREP_CONFIG_PATH", str(config))
    target = settings.home / ".codex/config.toml"
    reason = _reason(
        settings,
        "shell",
        {"command": command.format(target=target.as_posix())},
        settings.personal,
    )
    if allowed:
        assert reason == ""
    else:
        assert "is user-level host settings or machine state" in reason


@pytest.mark.parametrize(
    "command",
    [
        "tj install",
        "tj install --step 'plugin setup'",
        "tj plugins update --host claude",
        'python -B "{claude}" setup --check',
        'python3 -B "{codex}" setup',
    ],
)
def test_boundary_reason_allows_scripted_commands_that_own_host_settings(
    settings: Machine, command: str
) -> None:
    caches = {
        "claude": settings.home / ".claude/plugins/cache/tools/agent/1/setup.py",
        "codex": settings.home / ".codex/plugins/cache/tools/agent/1/setup.py",
    }
    for script in caches.values():
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("", encoding="utf-8")
    command = command.format(**{host: path.as_posix() for host, path in caches.items()})
    assert _reason(settings, "Bash", {"command": command}, settings.personal) == ""


@pytest.mark.parametrize(
    "relative", [".claude/settings.json", ".codex/config.toml", ".codex/rules/a.rules"]
)
def test_boundary_reason_allows_repository_host_settings(
    settings: Machine, relative: str
) -> None:
    target = settings.personal / relative
    assert (
        _reason(settings, "Write", _writer_input("Write", target), settings.personal)
        == ""
    )


@pytest.mark.parametrize(
    ("option", "tool", "tool_input"),
    [
        ("--tool-gate", "Write", {"file_path": "~/.claude/settings.json"}),
        ("--tool-gate", "Bash", {"command": "echo x > ~/.codex/config.toml"}),
    ],
)
def test_hook_entry_points_deny_host_settings_writes(
    settings: Machine,
    monkeypatch: pytest.MonkeyPatch,
    option: str,
    tool: str,
    tool_input: dict[str, object],
) -> None:
    monkeypatch.setenv("AGENT_STATE_DIRECTORY", str(settings.state))
    payload = {
        "tool_name": tool,
        "tool_input": tool_input,
        "cwd": str(settings.personal),
    }
    result = subprocess.run(
        [sys.executable, "-B", str(GATE), option],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    decision = json.loads(result.stdout)["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny"
    assert "user-level host settings" in decision["permissionDecisionReason"]
