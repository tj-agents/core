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
