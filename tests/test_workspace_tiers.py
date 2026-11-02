import contextlib
import importlib.util
import json
import os
import subprocess
from collections.abc import Iterator, Sequence
from pathlib import Path
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[1]
WORK = {
    "schema_version": 3,
    "tier": "work",
    "applies": "stack-present",
    "detect": {"fact": "employer"},
    "session_context": "Load work:ask-person before drafting and clip the draft.",
}
EMPLOYER = {
    "schema_version": 3,
    "tier": "employer-a",
    "applies": "stack-present",
    "owner_repository": "publisher/employer-a",
    "detect": {"all": [{"remote_host": "example.test"}, {"remote": "^employer-a/"}]},
    "employer": {"context_skill": "communication-context"},
}


def _load_gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "workspace_tier_gate", ROOT / ".agents/hooks/tier_gate.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = _load_gate()


def _install_payload(cache: Path, plugin: str, data: dict[str, object]) -> Path:
    payload = cache / "test-market" / plugin / "1"
    skill = payload / "skills/communication-context"
    skill.mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text(
        "---\nname: communication-context\nkind: knowledge\n---\nEmployer contacts.\n",
        encoding="utf-8",
    )
    (payload / "tier.json").write_text(json.dumps(data), encoding="utf-8")
    registry_path = cache.parent / "installed_plugins.json"
    registry = (
        json.loads(registry_path.read_text(encoding="utf-8"))
        if registry_path.exists()
        else {"plugins": {}}
    )
    registry["plugins"][plugin + "@test-market"] = [{"installPath": str(payload)}]
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    return payload


def _git(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
    )


def _repository(path: Path, url: str) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "--quiet")
    _git(path, "config", "remote.origin.url", url)
    return path


@pytest.fixture
def project(tmp_path: Path) -> Path:
    path = tmp_path / "project"
    path.mkdir()
    return path


@pytest.fixture
def cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.delenv(gate.OVERRIDE_VARIABLE, raising=False)
    path = tmp_path / "profile/plugins/cache"
    _install_payload(path, "work", WORK)
    return path


def test_folder_of_employer_repositories_applies_employer_and_work(
    project: Path, cache: Path
) -> None:
    employer = _install_payload(cache, "employer-a", EMPLOYER)
    _repository(project / "personal-tool", "git@example.test:personal/tool.git")
    child = _repository(
        project / "service α", "git@example.test:employer-a/service.git"
    )
    (project / "service.worktrees").mkdir()
    found = list(gate.declarations([cache], project=project))

    result = gate.assess(project, found)

    assert {item.plugin for item, _ in result.applicable} == {"work", "employer-a"}
    selection = next(
        item
        for item in result.selections
        if item["plugin_id"] == "employer-a@test-market"
    )
    assert selection["scope"] == str(child)
    context = gate.statement(project, found)
    assert WORK["session_context"] in context
    assert (
        str((employer / "skills/communication-context/SKILL.md").resolve()) in context
    )


def test_workspace_host_and_owner_must_match_the_same_repository(
    project: Path, cache: Path
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    _repository(project / "wrong-host", "git@other.test:employer-a/service.git")
    _repository(project / "personal-tool", "git@example.test:personal/tool.git")

    result = gate.assess(project, gate.declarations([cache], project=project))

    assert result.applicable == []


@pytest.mark.parametrize("relative_scope", [".", "workspace"])
def test_repository_and_subdirectory_never_borrow_a_nested_employer_remote(
    project: Path, cache: Path, relative_scope: str
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    _repository(project, "git@example.test:personal/project.git")
    scope = project / relative_scope
    _repository(scope / "vendored", "git@example.test:employer-a/service.git")

    result = gate.assess(scope, gate.declarations([cache], project=scope))

    assert result.applicable == []


def test_workspace_predicate_cannot_combine_a_root_marker_with_a_child_remote(
    project: Path, cache: Path
) -> None:
    predicate = {"all": [{"file": "marker"}, {"remote": "^employer-a/"}]}
    _install_payload(cache, "employer-a", dict(EMPLOYER, detect=predicate))
    (project / "marker").touch()
    child = _repository(project / "service", "git@example.test:employer-a/service.git")
    found = list(gate.declarations([cache], project=project))

    assert gate.assess(project, found).applicable == []

    (child / "marker").touch()
    result = gate.assess(project, found)

    assert {item.plugin for item, _ in result.applicable} == {"work", "employer-a"}


def test_workspace_detects_a_linked_worktree(project: Path, cache: Path) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    source = _repository(project / "source", "git@example.test:employer-a/service.git")
    _git(
        source,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.test",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "--quiet",
        "--allow-empty",
        "-m",
        "initial",
    )
    workspace = project / "worktrees"
    workspace.mkdir()
    child = workspace / "service"
    _git(source, "worktree", "add", "--quiet", "--detach", str(child))
    assert (child / ".git").is_file()

    result = gate.assess(workspace, gate.declarations([cache], project=workspace))

    selection = next(
        item
        for item in result.selections
        if item["plugin_id"] == "employer-a@test-market"
    )
    assert selection["matched"]
    assert selection["scope"] == str(child)


@pytest.mark.parametrize("schema_version", [1, 2])
def test_legacy_remote_declarations_detect_workspace_repositories(
    project: Path, cache: Path, schema_version: int
) -> None:
    _install_payload(
        cache,
        "legacy",
        {
            "schema_version": schema_version,
            "tier": "legacy",
            "applies": "stack-present",
            "detect": {"remote": ["^employer-a/"]},
        },
    )
    _repository(project / "service", "git@example.test:employer-a/service.git")

    result = gate.assess(project, gate.declarations([cache], project=project))

    assert [item.plugin for item, _ in result.applicable] == ["legacy"]


def test_workspace_employer_fact_cannot_borrow_evidence_from_a_sibling(
    project: Path, cache: Path
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    _install_payload(
        cache,
        "combined",
        dict(
            WORK,
            tier="combined",
            detect={"all": [{"fact": "employer"}, {"remote": "^personal/"}]},
        ),
    )
    _repository(project / "a-employer", "git@example.test:employer-a/service.git")
    _repository(project / "b-personal", "git@example.test:personal/tool.git")

    result = gate.assess(project, gate.declarations([cache], project=project))

    assert {item.plugin for item, _ in result.applicable} == {"work", "employer-a"}
    selection = next(
        item
        for item in result.selections
        if item["plugin_id"] == "combined@test-market"
    )
    assert not selection["matched"]


def test_workspace_composite_uses_the_second_matching_childs_own_employer_evidence(
    project: Path, cache: Path
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    _install_payload(
        cache,
        "combined",
        dict(
            WORK,
            tier="combined",
            detect={"all": [{"fact": "employer"}, {"remote": "^employer-a/second$"}]},
        ),
    )
    _repository(project / "a-first", "git@example.test:employer-a/first.git")
    second = _repository(project / "z-second", "git@example.test:employer-a/second.git")

    result = gate.assess(project, gate.declarations([cache], project=project))

    assert {item.plugin for item, _ in result.applicable} == {
        "work",
        "employer-a",
        "combined",
    }
    selection = next(
        item
        for item in result.selections
        if item["plugin_id"] == "combined@test-market"
    )
    assert selection["matched"]
    assert selection["scope"] == str(second)
    assert selection["evidence"] == (
        "employer-a@test-market: origin host example.test",
        "employer-a@test-market: origin employer-a/second",
        "origin employer-a/second",
    )


@pytest.mark.parametrize("relative_scope", [".", "workspace"])
def test_failed_parent_git_probe_does_not_allow_a_nested_employer_remote(
    project: Path, cache: Path, relative_scope: str
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    _repository(project, "git@example.test:personal/project.git")
    scope = project / relative_scope
    _repository(scope / "vendored", "git@example.test:employer-a/service.git")
    (project / ".git/config").write_text("[broken\n", encoding="utf-8")
    probe = subprocess.run(
        ["git", "-C", str(scope), "rev-parse", "--is-inside-work-tree"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
    )
    assert probe.returncode != 0

    result = gate.assess(scope, gate.declarations([cache], project=scope))

    assert result.applicable == []


def test_workspace_repository_discovery_and_remote_queries_are_bounded_and_cached(
    project: Path, cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    _install_payload(cache, "employer-b", dict(EMPLOYER, tier="employer-b"))
    for index in range(gate.WORKSPACE_REPOSITORIES + 5):
        (project / f"repository-{index:03}" / ".git").mkdir(parents=True)
    found = list(gate.declarations([cache], project=project))
    calls: list[tuple[Path, tuple[str, ...]]] = []
    scans: list[Path] = []
    visited: list[str] = []
    scandir = os.scandir

    def git(root: Path, arguments: Sequence[str]) -> None:
        calls.append((root, tuple(arguments)))

    def entries(source: Iterator[os.DirEntry[str]]) -> Iterator[os.DirEntry[str]]:
        for entry in source:
            visited.append(entry.name)
            yield entry

    @contextlib.contextmanager
    def scan(path: Path) -> Iterator[Iterator[os.DirEntry[str]]]:
        scans.append(path)
        with scandir(path) as source:
            yield entries(source)

    def monotonic() -> float:
        return 0.0

    monkeypatch.setattr(gate, "_run_git", git)
    monkeypatch.setattr(gate.os, "scandir", scan)
    monkeypatch.setattr(gate.time, "monotonic", monotonic)

    assert gate.assess(project, found).applicable == []

    assert scans == [project]
    assert len(visited) == gate.WORKSPACE_REPOSITORIES
    assert len(calls) == gate.WORKSPACE_REPOSITORIES + 2
    assert len(set(calls)) == len(calls)


def test_workspace_directory_enumeration_stops_at_the_entry_limit_and_is_cached(
    project: Path, cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    _install_payload(cache, "employer-b", dict(EMPLOYER, tier="employer-b"))
    (project / "ordinary-directory").mkdir()
    found = list(gate.declarations([cache], project=project))
    scans: list[Path] = []
    visited: list[int] = []
    scandir = os.scandir

    def entries(entry: os.DirEntry[str]) -> Iterator[os.DirEntry[str]]:
        for index in range(gate.WORKSPACE_ENTRIES + 5):
            visited.append(index)
            yield entry

    @contextlib.contextmanager
    def scan(path: Path) -> Iterator[Iterator[os.DirEntry[str]]]:
        scans.append(path)
        with scandir(path) as source:
            yield entries(next(source))

    def git(root: Path, arguments: Sequence[str]) -> None:
        return None

    def monotonic() -> float:
        return 0.0

    monkeypatch.setattr(gate, "_run_git", git)
    monkeypatch.setattr(gate.os, "scandir", scan)
    monkeypatch.setattr(gate.time, "monotonic", monotonic)

    assert gate.assess(project, found).applicable == []

    assert scans == [project]
    assert len(visited) == gate.WORKSPACE_ENTRIES


def test_workspace_directory_enumeration_stops_when_the_assessment_budget_expires(
    project: Path, cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    _install_payload(cache, "employer-b", dict(EMPLOYER, tier="employer-b"))
    (project / "ordinary-directory").mkdir()
    found = list(gate.declarations([cache], project=project))
    scans: list[Path] = []
    visited: list[int] = []
    elapsed = 0.0
    scandir = os.scandir

    def entries(entry: os.DirEntry[str]) -> Iterator[os.DirEntry[str]]:
        nonlocal elapsed
        for index in range(gate.WORKSPACE_ENTRIES + 5):
            elapsed += 1
            visited.append(index)
            yield entry

    @contextlib.contextmanager
    def scan(path: Path) -> Iterator[Iterator[os.DirEntry[str]]]:
        scans.append(path)
        with scandir(path) as source:
            yield entries(next(source))

    def git(root: Path, arguments: Sequence[str]) -> None:
        return None

    def monotonic() -> float:
        return elapsed

    monkeypatch.setattr(gate, "_run_git", git)
    monkeypatch.setattr(gate.os, "scandir", scan)
    monkeypatch.setattr(gate.time, "monotonic", monotonic)

    assert gate.assess(project, found).applicable == []

    assert scans == [project]
    assert len(visited) == gate.GIT_TIMEOUT
    assert elapsed == gate.GIT_TIMEOUT
    assert gate.GIT_DEADLINE.get() is None


def test_git_timeouts_share_one_assessment_budget(
    project: Path, cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    for name in ("first", "second"):
        (project / name / ".git").mkdir(parents=True)
    found = list(gate.declarations([cache], project=project))
    elapsed = 0.0
    timeouts: list[float] = []

    def run(
        arguments: list[str],
        *,
        capture_output: bool,
        text: bool,
        timeout: float,
    ) -> subprocess.CompletedProcess[str]:
        nonlocal elapsed
        timeouts.append(timeout)
        if len(timeouts) < 3:
            elapsed += 1
            return subprocess.CompletedProcess(arguments, 1, stdout="")
        elapsed += timeout
        raise subprocess.TimeoutExpired(arguments, timeout)

    def monotonic() -> float:
        return elapsed

    monkeypatch.setattr(gate.time, "monotonic", monotonic)
    monkeypatch.setattr(gate.process, "run", run)

    assert gate.assess(project, found).applicable == []

    assert timeouts == [gate.GIT_TIMEOUT, gate.GIT_TIMEOUT - 1, gate.GIT_TIMEOUT - 2]
    assert elapsed == gate.GIT_TIMEOUT
    assert gate.GIT_DEADLINE.get() is None
