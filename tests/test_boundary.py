import importlib
import importlib.util
import json
import os
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
boundary = importlib.import_module("boundary")
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


@pytest.mark.parametrize(
    ("text", "identifier"),
    [
        ("Configured by personal-tools.", "personal-tools"),
        ("Reviewed with base:review.", "base:review"),
        ("See https://github.com/tool-owner/base", "tool-owner"),
        ("Mirrors side-project", "side-project"),
        ("Opened by helper-bot", "helper-bot"),
    ],
)
def test_boundary_reason_blocks_personal_identifiers_written_into_a_work_repository(
    machine: Machine, text: str, identifier: str
) -> None:
    target = machine.work / "src" / "notes.md"
    reason = _reason(
        machine, "Write", {"file_path": str(target), "content": text}, machine.work
    )
    assert f"`{identifier}`" in reason
    assert str(machine.work) in reason


@pytest.mark.parametrize(
    "text",
    [
        "Approved by the-human.",
        "A base review of the service.",
        "personal tools are useful",
    ],
)
def test_boundary_reason_allows_ordinary_work_content(
    machine: Machine, text: str
) -> None:
    target = machine.work / "README.md"
    assert (
        _reason(
            machine,
            "Edit",
            {"file_path": str(target), "new_string": text},
            machine.work,
        )
        == ""
    )


def test_boundary_reason_allows_personal_identifiers_outside_work(
    machine: Machine,
) -> None:
    target = machine.personal / "README.md"
    tool_input = {
        "file_path": str(target),
        "content": "Uses personal-tools and base:review.",
    }
    assert _reason(machine, "Write", tool_input, machine.work) == ""


def test_boundary_reason_blocks_a_commit_message_in_a_work_repository(
    machine: Machine,
) -> None:
    command = 'git commit -m "Follow base:review"'
    assert "`base:review`" in _reason(
        machine, "Bash", {"command": command}, machine.work
    )


def test_boundary_reason_reads_the_files_a_work_command_sends(
    machine: Machine, tmp_path: Path
) -> None:
    body = tmp_path / "body.md"
    body.write_text("Drafted with personal-tools.\n", encoding="utf-8")
    command = f'gh pr create --title "Fix" --body-file "{body}"'
    assert "`personal-tools`" in _reason(
        machine, "Bash", {"command": command}, machine.work
    )


def test_boundary_reason_ignores_installed_plugin_paths_in_work_commands(
    machine: Machine,
) -> None:
    script = machine.plugin / "scripts" / "check.py"
    script.parent.mkdir()
    script.write_text("# personal-tools helper\n", encoding="utf-8")
    assert (
        _reason(
            machine, "Bash", {"command": f'python -B "{script}" --check'}, machine.work
        )
        == ""
    )


def test_boundary_reason_follows_a_leading_cd_into_a_work_repository(
    machine: Machine,
) -> None:
    command = f'cd "{machine.work}" && git commit -m "personal-tools fix"'
    assert "`personal-tools`" in _reason(
        machine, "PowerShell", {"command": command}, machine.personal
    )


def test_boundary_reason_blocks_a_command_naming_a_remote_work_repository(
    machine: Machine,
) -> None:
    command = 'gh pr comment 4 --repo employer-a/service --body "via helper-bot"'
    assert "`helper-bot`" in _reason(
        machine, "Bash", {"command": command}, machine.personal
    )


def test_boundary_reason_blocks_mcp_writes_from_a_work_session(
    machine: Machine,
) -> None:
    tool_input = {
        "project": "Product",
        "fields": [{"name": "System.Tags", "value": "personal-tools"}],
    }
    reason = _reason(
        machine, "mcp__boards__wit_create_work_item", tool_input, machine.work
    )
    assert "`personal-tools`" in reason


def test_boundary_reason_blocks_mcp_writes_to_a_named_work_repository(
    machine: Machine,
) -> None:
    tool_input = {
        "owner": "employer-a",
        "repo": "service",
        "body": "Generated by base:review",
    }
    reason = _reason(
        machine, "mcp__github__add_issue_comment", tool_input, machine.personal
    )
    assert "`base:review`" in reason


def test_boundary_reason_allows_without_installed_identifiers(
    machine: Machine, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT")
    target = machine.work / "notes.md"
    assert (
        _reason(
            machine,
            "Write",
            {"file_path": str(target), "content": "personal-tools"},
            machine.work,
        )
        == ""
    )


def test_origin_reads_a_linked_worktree_configuration(tmp_path: Path) -> None:
    main = _repository(tmp_path / "main", "https://github.com/employer-a/service.git")
    gitdir = main / ".git" / "worktrees" / "feature"
    gitdir.mkdir(parents=True)
    (gitdir / "commondir").write_text("../..\n", encoding="utf-8")
    worktree = tmp_path / "feature"
    worktree.mkdir()
    (worktree / ".git").write_text(f"gitdir: {gitdir}\n", encoding="utf-8")
    assert boundary.origin(worktree) == boundary.Remote(
        "github.com", "employer-a/service"
    )


@pytest.mark.parametrize(
    ("remote", "matched"),
    [
        (("github.com", "employer-a/service"), True),
        (("github.com", "employer-b/service"), False),
        (("gitlab.com", "employer-a/service"), False),
        ((None, "employer-a/service"), True),
    ],
)
def test_remote_matches_evaluates_origin_predicates(
    remote: tuple[str | None, str], matched: bool
) -> None:
    assert (
        boundary.remote_matches(EMPLOYER["detect"], boundary.Remote(*remote)) is matched
    )


def test_tool_gate_prints_a_deny_decision(machine: Machine) -> None:
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": 'git commit -m "personal-tools"'},
        "cwd": str(machine.work),
    }
    environment = {"AGENT_STATE_DIRECTORY": str(machine.state)}
    result = subprocess.run(
        [sys.executable, "-B", str(GATE), "--tool-gate"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, **environment},
        check=False,
    )
    decision = json.loads(result.stdout)["hookSpecificOutput"]
    assert result.returncode == 0
    assert decision["permissionDecision"] == "deny"
    assert "`personal-tools`" in decision["permissionDecisionReason"]


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
