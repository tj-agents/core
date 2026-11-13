import importlib
import importlib.util
import io
import json
import os
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / ".agents/hooks/tier_gate.py"


def _load_gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location("selected_standards_gate", GATE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = _load_gate()
selected = importlib.import_module("selected_standards")
RUST = {
    "schema_version": 1,
    "tier": "rust",
    "applies": "stack-present",
    "detect": {"files": ["Cargo.toml"], "globs": ["*.rs"]},
}
PYTHON = {
    "schema_version": 1,
    "tier": "python",
    "applies": "stack-present",
    "detect": {"files": ["pyproject.toml"], "globs": ["*.py"]},
}
ACTIONS = {
    "schema_version": 1,
    "tier": "github-actions",
    "applies": "stack-present",
    "detect": {"globs": [".github/workflows/*.yml"]},
}
BASE = {"schema_version": 1, "tier": "base", "applies": "always"}
SELECTED = ("rust@market", "python@market", "github-actions@market", "base@market")


@dataclass(frozen=True, slots=True)
class Skill:
    name: str
    kind: str = "convention"
    profile: str = "core"


@dataclass(frozen=True, slots=True)
class PluginCache:
    root: Path

    def install(
        self, plugin: str, tier: dict[str, object], skills: Sequence[Skill]
    ) -> None:
        payload = self.root / "market" / plugin / "1.0.0"
        for skill in skills:
            header = (
                f"---\nname: {skill.name}\ndescription: {skill.name} rule.\n"
                f"kind: {skill.kind}\nprofile: {skill.profile}\n---\n"
            )
            discovery = payload / "skills" / skill.name / "SKILL.md"
            discovery.parent.mkdir(parents=True)
            discovery.write_text(
                header + "Read the canonical file.\n", encoding="utf-8"
            )
            canonical = payload / ".agents" / plugin / skill.kind / skill.name
            canonical.mkdir(parents=True)
            (canonical / "SKILL.md").write_text(
                header + "Rule body.\n", encoding="utf-8"
            )
        (payload / "tier.json").write_text(json.dumps(tier), encoding="utf-8")
        registry = self.root.parent / "installed_plugins.json"
        data = (
            json.loads(registry.read_text(encoding="utf-8"))
            if registry.exists()
            else {"plugins": {}}
        )
        data["plugins"][plugin + "@market"] = [
            {"scope": "user", "installPath": str(payload)}
        ]
        registry.write_text(json.dumps(data), encoding="utf-8")

    def canonical(self, plugin: str, name: str, kind: str = "convention") -> Path:
        path = self.root / "market" / plugin / "1.0.0" / ".agents" / plugin
        return (path / kind / name / "SKILL.md").resolve()


@pytest.fixture(autouse=True)
def cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> PluginCache:
    plugins = PluginCache(tmp_path / "profile" / "plugins" / "cache")
    plugins.root.mkdir(parents=True)
    monkeypatch.setattr(gate, "cache_roots", lambda: [plugins.root])
    plugins.install(
        "rust",
        RUST,
        [
            Skill("style"),
            Skill("testing"),
            Skill("persistence", profile="persistence"),
            Skill("scaffold", kind="utility"),
        ],
    )
    plugins.install("python", PYTHON, [Skill("style")])
    plugins.install("github-actions", ACTIONS, [Skill("workflows")])
    plugins.install("base", BASE, [Skill("process")])
    return plugins


@pytest.fixture
def state(tmp_path: Path) -> Path:
    return tmp_path / "state"


def _repository(path: Path, plugins: Sequence[str] = SELECTED) -> Path:
    (path / ".git").mkdir(parents=True)
    (path / ".agents").mkdir()
    selection = {
        "schema_version": 1,
        "marketplaces": {"market": {"repository": "example/marketplace"}},
        "plugins": list(plugins),
    }
    (path / ".agents" / "plugins.json").write_text(
        json.dumps(selection), encoding="utf-8"
    )
    return path


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    return _repository(tmp_path / "repository")


def _write(
    path: Path | str, cwd: Path, session: str = "session-1", agent: str | None = None
) -> dict[str, object]:
    payload: dict[str, object] = {
        "hook_event_name": "PreToolUse",
        "session_id": session,
        "tool_name": "Write",
        "tool_input": {"file_path": str(path), "content": "fn main() {}\n"},
        "cwd": str(cwd),
    }
    if agent is not None:
        payload["agent_id"] = agent
    return payload


def _read(path: Path, agent: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "hook_event_name": "PreToolUse",
        "session_id": "session-1",
        "tool_name": "Read",
        "tool_input": {"file_path": str(path)},
    }
    if agent is not None:
        payload["agent_id"] = agent
    return payload


def _listed(reason: str) -> list[str]:
    return [
        line[2:].split(": ", 1)[0] for line in reason.splitlines() if line[:2] == "- "
    ]


def _run_main(
    monkeypatch: pytest.MonkeyPatch, state: Path, flag: str, payload: object
) -> int:
    stream = io.TextIOWrapper(
        io.BytesIO(json.dumps(payload).encode("utf-8")), encoding="utf-8"
    )
    monkeypatch.setattr(gate.sys, "stdin", stream)
    monkeypatch.setattr(gate.sys, "argv", ["tier_gate.py", flag])
    monkeypatch.setenv(gate.STATE_DIRECTORY_VARIABLE, str(state))
    result: int = gate.main()
    return result


def test_write_gate_requires_only_the_matching_stack_core_standards(
    repository: Path, state: Path
) -> None:
    reason = gate.write_gate(_write(repository / "src" / "main.rs", repository), state)

    assert _listed(reason) == ["rust:style", "rust:testing"]


def test_write_gate_lists_each_missing_standard_with_its_canonical_path(
    repository: Path, state: Path, cache: PluginCache
) -> None:
    target = repository / "src" / "main.rs"

    reason = gate.write_gate(_write(target, repository), state)

    assert str(target) in reason
    assert f"- rust:style: {cache.canonical('rust', 'style')}" in reason
    assert f"- rust:testing: {cache.canonical('rust', 'testing')}" in reason
    assert len(reason) < 1_000


def test_write_gate_allows_the_write_silently_once_every_standard_is_read(
    repository: Path,
    state: Path,
    cache: PluginCache,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = repository / "src" / "main.rs"
    for name in ("style", "testing"):
        gate.record_read(_read(cache.canonical("rust", name)), state, 0.0)

    assert (
        _run_main(monkeypatch, state, "--write-gate", _write(target, repository)) == 0
    )
    assert capsys.readouterr().out == ""


def test_write_gate_names_only_the_standards_still_unread(
    repository: Path, state: Path, cache: PluginCache
) -> None:
    gate.record_read(_read(cache.canonical("rust", "style")), state, 0.0)

    reason = gate.write_gate(_write(repository / "lib.rs", repository), state)

    assert _listed(reason) == ["rust:testing"]


def test_write_gate_denies_with_the_host_permission_decision_shape(
    repository: Path,
    state: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = _write(repository / "main.rs", repository)

    assert _run_main(monkeypatch, state, "--write-gate", payload) == 0
    output = json.loads(capsys.readouterr().out)

    assert set(output) == {"hookSpecificOutput"}
    decision = output["hookSpecificOutput"]
    assert decision["hookEventName"] == "PreToolUse"
    assert decision["permissionDecision"] == "deny"
    assert _listed(decision["permissionDecisionReason"]) == [
        "rust:style",
        "rust:testing",
    ]


def test_each_agent_must_read_the_standards_itself(
    repository: Path, state: Path, cache: PluginCache
) -> None:
    target = repository / "main.rs"
    for name in ("style", "testing"):
        gate.record_read(_read(cache.canonical("rust", name)), state, 0.0)

    assert gate.write_gate(_write(target, repository), state) == ""
    assert gate.write_gate(_write(target, repository, agent="agent-a"), state)
    assert gate.write_gate(_write(target, repository, session="session-2"), state)


def test_compaction_forgets_only_the_compacted_agent(
    repository: Path,
    state: Path,
    cache: PluginCache,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = repository / "main.rs"
    for agent in (None, "agent-a"):
        for name in ("style", "testing"):
            gate.record_read(_read(cache.canonical("rust", name), agent), state, 0.0)
    compacted = {"hook_event_name": "PostCompact", "session_id": "session-1"}

    assert _run_main(monkeypatch, state, "--compacted", compacted) == 0

    assert gate.write_gate(_write(target, repository), state)
    assert gate.write_gate(_write(target, repository, agent="agent-a"), state) == ""


@pytest.mark.parametrize("name", ["README.md", "notes/plan.txt", "Cargo.lock"])
def test_write_gate_allows_files_no_selected_stack_declares(
    repository: Path, state: Path, name: str
) -> None:
    assert gate.write_gate(_write(repository / name, repository), state) == ""


def test_write_gate_allows_a_repository_without_a_selection(
    repository: Path, state: Path
) -> None:
    (repository / ".agents" / "plugins.json").unlink()

    assert gate.write_gate(_write(repository / "main.rs", repository), state) == ""


def test_write_gate_allows_a_file_outside_any_repository(
    tmp_path: Path, state: Path
) -> None:
    outside = tmp_path / "loose"

    assert gate.write_gate(_write(outside / "main.rs", outside), state) == ""


def test_write_gate_ignores_an_unselected_stack(tmp_path: Path, state: Path) -> None:
    repository = _repository(tmp_path / "python-only", ["python@market"])

    assert gate.write_gate(_write(repository / "main.rs", repository), state) == ""
    reason = gate.write_gate(_write(repository / "app.py", repository), state)
    assert _listed(reason) == ["python:style"]


def test_write_gate_without_a_session_cannot_track_and_allows(
    repository: Path, state: Path
) -> None:
    payload = _write(repository / "main.rs", repository)
    del payload["session_id"]

    assert gate.write_gate(payload, state) == ""


def test_write_gate_covers_codex_apply_patch_targets(
    repository: Path, state: Path
) -> None:
    payload = {
        "hook_event_name": "PreToolUse",
        "session_id": "codex-session",
        "tool_name": "apply_patch",
        "tool_input": {
            "command": (
                "*** Begin Patch\n*** Add File: docs/notes.md\n+x\n"
                "*** Add File: src/new.rs\n+fn x() {}\n*** End Patch"
            )
        },
        "cwd": str(repository),
    }

    reason = gate.write_gate(payload, state)

    assert "src/new.rs" in reason
    assert _listed(reason) == ["rust:style", "rust:testing"]


def test_record_read_ignores_files_other_than_skill_definitions(
    repository: Path, state: Path
) -> None:
    gate.record_read(_read(repository / "README.md"), state, 0.0)

    assert not (state / selected.LEDGER_DIRECTORY).exists()


def test_codex_shell_command_naming_a_canonical_path_records_it(
    repository: Path, state: Path, cache: PluginCache
) -> None:
    style = cache.canonical("rust", "style")
    payload = {
        "hook_event_name": "PreToolUse",
        "session_id": "session-1",
        "tool_name": "Bash",
        "tool_input": {"command": f'cat "{style}" README.md'},
        "cwd": str(repository),
    }

    gate.record_command(payload, state, 0.0)

    reason = gate.write_gate(_write(repository / "main.rs", repository), state)
    assert _listed(reason) == ["rust:testing"]


def test_codex_shell_command_without_a_canonical_path_records_nothing(
    repository: Path, state: Path, cache: PluginCache
) -> None:
    discovery = cache.root / "market" / "rust" / "1.0.0" / "skills" / "style"
    for command in ("git status", f"cat {discovery / 'SKILL.md'}"):
        payload = {
            "session_id": "session-1",
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": str(repository),
        }
        gate.record_command(payload, state, 0.0)

    assert not (state / selected.LEDGER_DIRECTORY).exists()


def test_hook_errors_fail_open(
    repository: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (repository / ".agents" / "plugins.json").write_text("{", encoding="utf-8")
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv(gate.STATE_DIRECTORY_VARIABLE, str(tmp_path / "state"))
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)

    result = subprocess.run(
        [sys.executable, "-B", str(GATE), "--write-gate"],
        input=json.dumps(_write(repository / "main.rs", repository)),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert "Invalid repository plugin selection" in result.stderr


def test_stale_ledgers_are_pruned_when_a_new_agent_ledger_starts(state: Path) -> None:
    old = selected.LoadLedger.for_agent(
        state, selected.AgentIdentity("old-session", "")
    )
    old.record(["/standards/style/SKILL.md"], 0.0)
    os.utime(old.directory, (1_000.0, 1_000.0))
    current = selected.LoadLedger.for_agent(
        state, selected.AgentIdentity("new-session", "")
    )

    current.record(
        ["/standards/style/SKILL.md"], 1_000.0 + selected.LEDGER_RETENTION_SECONDS + 1
    )

    assert not old.directory.exists()
    assert current.loaded("/standards/style/SKILL.md")
