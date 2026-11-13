import importlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
LARGE = 6_000


def _load_gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "selected_standards_gate", ROOT / ".agents/hooks/tier_gate.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = _load_gate()
selected = importlib.import_module("selected_standards")
PYTHON = {
    "schema_version": 1,
    "tier": "python",
    "stack": "Python",
    "applies": "stack-present",
    "detect": {"files": ["pyproject.toml"], "globs": ["*.py"]},
}
ACTIONS = {
    "schema_version": 1,
    "tier": "actions",
    "stack": "Actions",
    "applies": "stack-present",
    "detect": {"globs": ["*.yml"]},
}
BASE = {"schema_version": 1, "tier": "base", "applies": "always"}
ACME = {
    "schema_version": 3,
    "tier": "acme",
    "applies": "stack-present",
    "detect": {"all": [{"remote_host": "example.test"}, {"remote": "^acme/"}]},
    "employer": {"context_skill": "context"},
}
ACME_PYTHON = {"schema_version": 1, "tier": "acme-python", "applies": "always"}


@dataclass(frozen=True, slots=True)
class Skill:
    name: str
    body: str
    kind: str = "convention"
    profile: str = "core"


@dataclass(frozen=True, slots=True)
class PluginCache:
    root: Path

    def install(
        self, plugin: str, tier: dict[str, object], skills: Sequence[Skill]
    ) -> None:
        payload = self.root / "market" / plugin / "1.0.0"
        if payload.exists():
            shutil.rmtree(payload)
        for skill in skills:
            header = (
                f"---\nname: {skill.name}\ndescription: {skill.name} rule.\n"
                f"kind: {skill.kind}\nprofile: {skill.profile}\n---\n"
            )
            discovery = payload / "skills" / skill.name / "SKILL.md"
            discovery.parent.mkdir(parents=True)
            discovery.write_text(
                header + "Read the canonical definition.\n", encoding="utf-8"
            )
            canonical = payload / ".agents" / plugin / skill.kind / skill.name
            canonical.mkdir(parents=True)
            (canonical / "SKILL.md").write_text(header + skill.body, encoding="utf-8")
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


@pytest.fixture(autouse=True)
def cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> PluginCache:
    plugins = PluginCache(tmp_path / "profile" / "plugins" / "cache")
    plugins.root.mkdir(parents=True)
    monkeypatch.setattr(gate, "cache_roots", lambda: [plugins.root])
    monkeypatch.delenv(gate.OVERRIDE_VARIABLE, raising=False)
    plugins.install(
        "python",
        PYTHON,
        [
            Skill("style", "Canonical Python style body."),
            Skill("testing", "Canonical Python testing body."),
            Skill("scaffold", "Scaffold utility body.", kind="utility"),
        ],
    )
    plugins.install("base", BASE, [Skill("process", "Base process body.")])
    return plugins


@pytest.fixture
def state(tmp_path: Path) -> Path:
    return tmp_path / "state"


def _repository(path: Path, owner: str, plugins: Sequence[str]) -> Path:
    path.mkdir(parents=True)
    subprocess.run(["git", "-C", str(path), "init", "--quiet"], check=True, timeout=10)
    subprocess.run(
        [
            "git",
            "-C",
            str(path),
            "config",
            "remote.origin.url",
            f"git@example.test:{owner}/project.git",
        ],
        check=True,
        timeout=10,
    )
    (path / ".agents").mkdir()
    selection = {
        "schema_version": 1,
        "marketplaces": {"market": {"repository": "example/marketplace"}},
        "plugins": list(plugins),
    }
    (path / ".agents" / "plugins.json").write_text(
        json.dumps(selection), encoding="utf-8"
    )
    (path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (path / "src").mkdir()
    return path


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    return _repository(
        tmp_path / "repository", "tommy", ["python@market", "base@market"]
    )


def _write(
    path: Path, session: str = "session-1", agent: str | None = None
) -> dict[str, object]:
    payload: dict[str, object] = {
        "hook_event_name": "PreToolUse",
        "session_id": session,
        "tool_name": "Write",
        "tool_input": {"file_path": str(path), "content": "value = 1\n"},
        "cwd": str(path.parent),
    }
    if agent is not None:
        payload["agent_id"] = agent
    return payload


def _injected(context: str) -> list[str]:
    return [
        line.split('"')[1]
        for line in context.splitlines()
        if line.startswith("<standard name=")
    ]


def test_python_write_injects_the_canonical_standard_text(
    repository: Path, state: Path
) -> None:
    context = gate.tool_context(_write(repository / "src" / "app.py"), state)

    assert _injected(context) == ["python:style", "python:testing"]
    assert "Canonical Python style body." in context
    assert "Read the canonical definition." not in context
    assert "Scaffold utility body." not in context
    assert "Base process body." not in context


def test_second_write_by_the_same_agent_injects_nothing_new(
    repository: Path, state: Path
) -> None:
    gate.tool_context(_write(repository / "src" / "app.py"), state)

    context = gate.tool_context(_write(repository / "src" / "other.py"), state)

    assert _injected(context) == []
    assert "Applies here: `python:*`" in context


def test_each_agent_receives_the_standards_on_its_first_write(
    repository: Path, state: Path
) -> None:
    target = repository / "src" / "app.py"
    gate.tool_context(_write(target), state)

    subagent = gate.tool_context(_write(target, agent="agent-a"), state)
    repeated = gate.tool_context(_write(target, agent="agent-a"), state)
    other_session = gate.tool_context(_write(target, session="session-2"), state)

    assert _injected(subagent) == ["python:style", "python:testing"]
    assert _injected(repeated) == []
    assert _injected(other_session) == ["python:style", "python:testing"]


@pytest.mark.parametrize("name", ["README.md", "notes/plan.txt"])
def test_non_stack_path_injects_nothing_and_records_nothing(
    repository: Path, state: Path, name: str
) -> None:
    context = gate.tool_context(_write(repository / name), state)

    assert _injected(context) == []
    assert not (state / "standards-injection").exists()


def test_read_of_a_stack_file_injects_nothing(repository: Path, state: Path) -> None:
    payload = {
        "session_id": "session-1",
        "tool_name": "Read",
        "tool_input": {"file_path": str(repository / "pyproject.toml")},
    }

    assert _injected(gate.tool_context(payload, state)) == []


def test_repository_without_a_plugin_selection_injects_nothing(
    repository: Path, state: Path
) -> None:
    (repository / ".agents" / "plugins.json").unlink()

    context = gate.tool_context(_write(repository / "src" / "app.py"), state)

    assert _injected(context) == []


def test_unavailable_selection_is_reported_instead_of_injected(
    tmp_path: Path, state: Path
) -> None:
    repository = _repository(
        tmp_path / "broken", "tommy", ["python@market", "missing@market"]
    )

    context = gate.tool_context(_write(repository / "src" / "app.py"), state)

    assert _injected(context) == []
    assert "not available in this host: missing@market" in context


def test_codex_apply_patch_injects_the_standards(repository: Path, state: Path) -> None:
    payload = {
        "hook_event_name": "PreToolUse",
        "session_id": "codex-session",
        "turn_id": "turn-1",
        "tool_name": "apply_patch",
        "tool_input": {
            "command": (
                "*** Begin Patch\n*** Add File: src/new.py\n+value = 1\n*** End Patch"
            )
        },
        "cwd": str(repository),
    }

    context = gate.tool_context(payload, state)

    assert _injected(context) == ["python:style", "python:testing"]


def test_employer_replacement_injects_the_company_skill(
    tmp_path: Path, state: Path, cache: PluginCache
) -> None:
    cache.install("acme", ACME, [Skill("context", "Acme contacts.", kind="knowledge")])
    cache.install("acme-python", ACME_PYTHON, [Skill("style", "Acme Python style.")])
    repository = _repository(
        tmp_path / "work",
        "acme",
        ["python@market", "base@market", "acme@market", "acme-python@market"],
    )

    context = gate.tool_context(_write(repository / "src" / "app.py"), state)

    assert _injected(context) == ["acme-python:style", "python:testing"]
    assert "Acme Python style." in context
    assert "Canonical Python style body." not in context


def test_size_bound_injects_the_most_specific_first_and_names_the_rest(
    tmp_path: Path, state: Path, cache: PluginCache
) -> None:
    cache.install(
        "python",
        PYTHON,
        [
            Skill("style", "S" * LARGE),
            Skill("extras", "E" * LARGE, profile="advanced"),
        ],
    )
    cache.install("actions", ACTIONS, [Skill("workflows", "W" * LARGE)])
    repository = _repository(
        tmp_path / "bounded", "tommy", ["python@market", "actions@market"]
    )
    (repository / "deploy.yml").write_text("on: push\n", encoding="utf-8")
    target = repository / "src" / "app.py"

    writes = [gate.tool_context(_write(target), state) for _ in range(4)]

    assert [_injected(context) for context in writes] == [
        ["python:style"],
        ["python:extras"],
        ["actions:workflows"],
        [],
    ]
    deferred = writes[0].split("character hook context bound")[1]
    assert deferred.index("`python:extras`") < deferred.index("`actions:workflows`")
    assert max(len(context) for context in writes) <= selected.HOOK_CONTEXT_CHARACTERS


def test_an_oversized_standard_is_named_without_blocking_smaller_ones(
    tmp_path: Path, state: Path, cache: PluginCache
) -> None:
    oversized = selected.HOOK_CONTEXT_CHARACTERS + 1
    cache.install(
        "python",
        PYTHON,
        [Skill("errors", "E" * oversized), Skill("style", "Small style body.")],
    )
    repository = _repository(tmp_path / "oversized", "tommy", ["python@market"])
    target = repository / "src" / "app.py"

    writes = [gate.tool_context(_write(target), state) for _ in range(2)]

    assert [_injected(context) for context in writes] == [["python:style"], []]
    assert all("`python:errors`" in context for context in writes)
    assert max(len(context) for context in writes) <= selected.HOOK_CONTEXT_CHARACTERS


@pytest.mark.parametrize(
    "sizes", [(1,), (9_000,), (4_000, 4_000, 4_000), (12_000, 10, 3_000)]
)
def test_an_injection_never_exceeds_its_limit(
    tmp_path: Path, sizes: tuple[int, ...]
) -> None:
    standards = []
    for index, size in enumerate(sizes):
        path = tmp_path / f"standard-{index}.md"
        path.write_text("x" * size, encoding="utf-8")
        standards.append(
            selected.Standard(f"stack:standard-{index}", "stack", path, "core")
        )

    injection = selected.compose_injection(standards, selected.HOOK_CONTEXT_CHARACTERS)

    assert len(injection.text) <= selected.HOOK_CONTEXT_CHARACTERS


def test_codex_inlines_at_least_the_hook_context_bound() -> None:
    manifest = json.loads(
        (ROOT / ".agents/plugins/manifests/codex/base-hooks.json").read_text(
            encoding="utf-8"
        )
    )
    handlers = [
        handler
        for entry in manifest["hooks"]["PreToolUse"]
        for handler in entry["hooks"]
        if "--tool-context" in handler["command"]
    ]
    worst_case_characters_per_token = 2

    assert handlers
    assert all(
        handler["additionalContextLimit"] * worst_case_characters_per_token
        >= selected.HOOK_CONTEXT_CHARACTERS
        for handler in handlers
    )


def test_matching_tier_is_injected_before_other_stack_tiers(
    tmp_path: Path, state: Path, cache: PluginCache
) -> None:
    cache.install("actions", ACTIONS, [Skill("workflows", "Actions body.")])
    repository = _repository(
        tmp_path / "ordered", "tommy", ["python@market", "actions@market"]
    )
    (repository / "deploy.yml").write_text("on: push\n", encoding="utf-8")

    context = gate.tool_context(_write(repository / "release.yml"), state)

    assert _injected(context) == ["actions:workflows", "python:style", "python:testing"]


def test_compaction_clears_only_the_compacted_agent_record(
    repository: Path, state: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = repository / "src" / "app.py"
    gate.tool_context(_write(target), state)
    gate.tool_context(_write(target, agent="agent-a"), state)
    compacted = {"hook_event_name": "PostCompact", "session_id": "session-1"}
    stream = io.TextIOWrapper(io.BytesIO(json.dumps(compacted).encode("utf-8")))
    monkeypatch.setattr(gate.sys, "stdin", stream)
    monkeypatch.setattr(gate.sys, "argv", ["tier_gate.py", "--compacted"])
    monkeypatch.setenv(gate.STATE_DIRECTORY_VARIABLE, str(state))

    assert gate.main() == 0
    main_agent = gate.tool_context(_write(target), state)
    subagent = gate.tool_context(_write(target, agent="agent-a"), state)

    assert _injected(main_agent) == ["python:style", "python:testing"]
    assert _injected(subagent) == []


def test_stale_records_are_pruned_when_a_new_agent_record_starts(state: Path) -> None:
    old = selected.InjectionLedger.for_agent(
        state, selected.AgentIdentity("old-session", "")
    )
    old.record(["python:style"], 0.0)
    os.utime(old.path, (1_000.0, 1_000.0))
    current = selected.InjectionLedger.for_agent(
        state, selected.AgentIdentity("new-session", "")
    )

    current.record(["python:style"], 1_000.0 + selected.LEDGER_RETENTION_SECONDS + 1)

    assert not old.path.exists()
    assert current.injected() == frozenset({"python:style"})
