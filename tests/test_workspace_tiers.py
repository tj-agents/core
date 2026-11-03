import importlib.util
import json
import os
import subprocess
from collections.abc import Iterator
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
PERSONAL = {"schema_version": 1, "tier": "personal", "applies": "always"}


def _load_gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "workspace_tier_gate", ROOT / ".agents/hooks/tier_gate.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = _load_gate()


def _install_payload(
    cache: Path, plugin: str, data: dict[str, object], marketplace: str = "test-market"
) -> Path:
    payload = cache / marketplace / plugin / "1"
    skill = payload / "skills/communication-context"
    skill.mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text(
        "---\nname: communication-context\nmetadata:\n  tj-agents-kind: reference\n---\nEmployer contacts.\n",
        encoding="utf-8",
    )
    (payload / "tier.json").write_text(json.dumps(data), encoding="utf-8")
    registry_path = cache.parent / "installed_plugins.json"
    registry = (
        json.loads(registry_path.read_text(encoding="utf-8"))
        if registry_path.exists()
        else {"plugins": {}}
    )
    registry["plugins"][plugin + "@" + marketplace] = [{"installPath": str(payload)}]
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


def _adopt_personal(root: Path) -> None:
    selection = {
        "schema_version": 1,
        "marketplaces": {"tj-agents": {"repository": "tj-agents/marketplace"}},
        "plugins": ["personal@tj-agents"],
    }
    path = root / ".agents/plugins.json"
    path.parent.mkdir()
    path.write_text(json.dumps(selection), encoding="utf-8")


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


def _found(cache: Path, project: Path) -> list[object]:
    return list(gate.declarations([cache], project=project))


def test_complete_all_work_folder_applies_only_common_employer_context(
    project: Path, cache: Path
) -> None:
    employer = _install_payload(cache, "employer-a", EMPLOYER)
    first = _repository(
        project / "services" / "first", "git@example.test:employer-a/first.git"
    )
    _repository(
        project / "services" / "second", "git@example.test:employer-a/second.git"
    )

    result = gate.assess(project, _found(cache, project))

    assert {item.plugin for item, _ in result.applicable} == {"work", "employer-a"}
    assert result.inventory.complete
    assert result.scope_state == "work"
    assert set(result.inventory) == {first, project / "services" / "second"}
    context = gate.statement(project, _found(cache, project))
    assert WORK["session_context"] in context
    assert (
        str((employer / "skills/communication-context/SKILL.md").resolve()) in context
    )


@pytest.mark.parametrize("target", ["", "marker.txt"])
def test_non_git_markers_establish_only_technical_scope(
    project: Path, cache: Path, target: str
) -> None:
    marker_predicate = {"file": "marker.txt"}
    _install_payload(cache, "employer-a", {**EMPLOYER, "detect": marker_predicate})
    _install_payload(
        cache,
        "technical",
        {
            "schema_version": 3,
            "tier": "technical",
            "applies": "stack-present",
            "detect": marker_predicate,
        },
    )
    (project / "marker.txt").write_text("local marker", encoding="utf-8")

    result = gate.assess(project / target, _found(cache, project))

    assert result.scope_state == "undetermined"
    assert result.employers == ()
    assert {item.plugin for item, _ in result.applicable} == {"technical"}


def test_complete_all_personal_folder_requires_each_repository_to_adopt(
    project: Path, cache: Path
) -> None:
    _install_payload(cache, "personal", PERSONAL, marketplace="tj-agents")
    first = _repository(project / "one", "git@example.test:personal/one.git")
    second = _repository(project / "two", "git@example.test:personal/two.git")
    _adopt_personal(first)
    _adopt_personal(second)

    result = gate.assess(project, _found(cache, project))

    assert [item.plugin for item, _ in result.applicable] == ["personal"]
    assert [item.plugin for item in result.ubiquitous] == []
    assert result.scope_state == "personal"


def test_mixed_folder_does_not_apply_work_or_personal_to_every_repository(
    project: Path, cache: Path
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    _install_payload(cache, "personal", PERSONAL, marketplace="tj-agents")
    _repository(project / "work", "git@example.test:employer-a/service.git")
    personal = _repository(project / "personal", "git@example.test:personal/tool.git")
    _adopt_personal(personal)

    result = gate.assess(project, _found(cache, project))
    context = gate.statement(project, _found(cache, project))

    assert {item.plugin for item, _ in result.applicable}.isdisjoint(
        {"work", "employer-a", "personal"}
    )
    assert result.scope_state == "mixed"
    assert "Organizational scope is mixed" in context
    assert "Work or Personal standards" in context


def test_personal_adoption_conflicts_with_employer_evidence(
    project: Path, cache: Path
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    _install_payload(cache, "personal", PERSONAL, marketplace="tj-agents")
    repository = _repository(project, "git@example.test:employer-a/service.git")
    _adopt_personal(repository)

    result = gate.assess(project, _found(cache, project))

    assert {item.plugin for item, _ in result.applicable}.isdisjoint(
        {"work", "employer-a", "personal"}
    )
    assert result.scope_state == "undetermined"
    personal = next(
        item for item in result.selections if item["plugin_id"] == "personal@tj-agents"
    )
    assert personal["diagnostics"][0]["code"] == "organizational-scope-conflict"


def test_over_repository_limit_is_undetermined_not_non_work(
    project: Path, cache: Path
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    for index in range(gate.WORKSPACE_REPOSITORIES + 1):
        (project / f"repository-{index:03}" / ".git").mkdir(parents=True)

    result = gate.assess(project, _found(cache, project))

    assert not result.inventory.complete
    assert result.inventory.reason == "repository limit reached"
    assert result.scope_state == "undetermined"
    assert {item.plugin for item, _ in result.applicable}.isdisjoint(
        {"work", "employer-a"}
    )
    assert any(
        problem["code"] == "incomplete-workspace-inventory"
        for problem in result.diagnostics
    )


def test_nested_wrappers_are_scanned_until_a_repository_boundary(
    project: Path, cache: Path
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    child = _repository(
        project / "wrappers" / "team" / "service",
        "git@example.test:employer-a/service.git",
    )
    nested = _repository(child / "nested", "git@example.test:personal/nested.git")

    result = gate.assess(project, _found(cache, project))

    assert set(result.inventory) == {child}
    assert nested not in result.inventory
    assert {item.plugin for item, _ in result.applicable} == {"work", "employer-a"}


def test_repository_subdirectory_cannot_borrow_nested_employer_remote(
    project: Path, cache: Path
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    _repository(project, "git@example.test:personal/project.git")
    scope = project / "workspace"
    _repository(scope / "vendored", "git@example.test:employer-a/service.git")

    result = gate.assess(scope, _found(cache, scope))

    assert result.applicable == []


def test_employer_predicate_keeps_host_and_repository_identity_in_one_repository(
    project: Path, cache: Path
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    _repository(project / "wrong-host", "git@other.test:employer-a/service.git")
    _repository(project / "wrong-owner", "git@example.test:personal/tool.git")

    result = gate.assess(project, _found(cache, project))

    assert result.applicable == []


def test_composite_employer_predicate_uses_each_repositorys_own_facts(
    project: Path, cache: Path
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    _install_payload(
        cache,
        "combined",
        dict(
            WORK,
            tier="combined",
            detect={"all": [{"fact": "employer"}, {"remote": "^employer-a/"}]},
        ),
    )
    _repository(project / "first", "git@example.test:employer-a/first.git")
    _repository(project / "second", "git@example.test:employer-a/second.git")

    result = gate.assess(project, _found(cache, project))

    assert {item.plugin for item, _ in result.applicable} == {
        "work",
        "employer-a",
        "combined",
    }


def test_non_git_project_keeps_its_own_technical_marker_without_organizational_scope(
    project: Path, cache: Path
) -> None:
    _install_payload(
        cache,
        "python",
        {
            "schema_version": 1,
            "tier": "python",
            "applies": "stack-present",
            "detect": {"files": ["pyproject.toml"]},
        },
    )
    (project / "pyproject.toml").write_text(
        "[project]\nname='test'\n", encoding="utf-8"
    )

    result = gate.assess(project, _found(cache, project))

    assert [item.plugin for item, _ in result.applicable] == ["python"]
    assert result.scope_state == "undetermined"


def test_repeated_assessments_re_read_changed_adoption_without_sticky_scope(
    project: Path, cache: Path
) -> None:
    _install_payload(cache, "personal", PERSONAL, marketplace="tj-agents")
    _repository(project, "git@example.test:personal/project.git")

    assert [
        item.plugin
        for item, _ in gate.assess(project, _found(cache, project)).applicable
    ] == []
    _adopt_personal(project)
    assert [
        item.plugin
        for item, _ in gate.assess(project, _found(cache, project)).applicable
    ] == ["personal"]


def test_workspace_inventory_marks_unreadable_frontiers_incomplete(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = os.scandir

    def scan(path: Path) -> Iterator[os.DirEntry[str]]:
        if Path(path) == project / "blocked":
            raise PermissionError(path)
        return original(path)

    (project / "blocked").mkdir()
    monkeypatch.setattr(gate.os, "scandir", scan)

    result = gate.assess(project, [])

    assert not result.inventory.complete
    assert result.inventory.reason == "directory could not be read"


def test_known_work_and_unknown_repository_remain_undetermined(
    project: Path, cache: Path
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    _repository(project / "work", "git@example.test:employer-a/service.git")
    _repository(project / "unknown", "git@example.test:personal/tool.git")

    result = gate.assess(project, _found(cache, project))

    assert result.scope_state == "undetermined"
    assert not result.applicable


def test_different_employers_share_work_but_not_employer_context(
    project: Path, cache: Path
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    _install_payload(
        cache,
        "employer-b",
        dict(EMPLOYER, tier="employer-b", detect={"remote": "^employer-b/"}),
    )
    _repository(project / "one", "git@example.test:employer-a/service.git")
    _repository(project / "two", "git@example.test:employer-b/service.git")

    result = gate.assess(project, _found(cache, project))

    assert result.scope_state == "work"
    assert [item.plugin for item, _ in result.applicable] == ["work"]
    assert result.employers == ()


def test_adoption_establishes_scope_even_without_installed_personal(
    project: Path, cache: Path
) -> None:
    _repository(project, "git@example.test:personal/tool.git")
    _adopt_personal(project)

    assert gate.assess(project, _found(cache, project)).scope_state == "personal"
    _install_payload(cache, "employer-a", EMPLOYER)
    _git(
        project,
        "config",
        "remote.origin.url",
        "git@example.test:employer-a/service.git",
    )
    result = gate.assess(project, _found(cache, project))
    assert result.scope_state == "undetermined"
    assert not result.applicable


@pytest.mark.parametrize("schema", [True, "1", 2])
def test_invalid_personal_adoption_cannot_establish_scope(
    project: Path, cache: Path, schema: object
) -> None:
    _install_payload(cache, "personal", PERSONAL, marketplace="tj-agents")
    _repository(project, "git@example.test:personal/tool.git")
    _adopt_personal(project)
    path = project / ".agents/plugins.json"
    selection = json.loads(path.read_text(encoding="utf-8"))
    selection["schema_version"] = schema
    path.write_text(json.dumps(selection), encoding="utf-8")

    result = gate.assess(project, _found(cache, project))

    assert result.scope_state == "undetermined"
    assert not result.applicable
    assert result.diagnostics[0]["code"] == "invalid-repository-adoption"


def test_project_installation_is_selected_for_each_child(
    project: Path, cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = _repository(project / "one", "git@example.test:employer-a/first.git")
    second = _repository(project / "two", "git@example.test:employer-a/second.git")
    payload = _install_payload(cache, "employer-a", EMPLOYER)
    registry_path = cache.parent / "installed_plugins.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["plugins"]["employer-a@test-market"][0]["projectPath"] = str(first)
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    monkeypatch.setattr(gate, "cache_roots", lambda: [cache])

    result = gate.assess(project)

    assert payload.exists()
    assert result.scope_state == "undetermined"
    assert {item.scope: item.scope_state for item in result.repository_results} == {
        str(first): "work",
        str(second): "unclassified",
    }
    assert not result.applicable


@pytest.mark.parametrize(
    "scope", ["folder", "repository", "subdirectory", "file", "new-file"]
)
def test_corrupt_repository_boundary_is_undetermined(
    project: Path, cache: Path, scope: str
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    child = _repository(project / "broken", "git@example.test:employer-a/service.git")
    nested = _repository(child / "nested", "git@example.test:employer-a/nested.git")
    (child / ".git/config").write_text("[broken\n", encoding="utf-8")
    directory = child / "src"
    directory.mkdir()
    existing_file = directory / "existing.py"
    existing_file.touch()

    result = gate.assess(
        {
            "folder": project,
            "repository": child,
            "subdirectory": directory,
            "file": existing_file,
            "new-file": directory / "new.py",
        }[scope],
        _found(cache, project),
    )

    assert result.scope_state == "undetermined"
    assert not result.applicable
    assert nested not in result.inventory
    if scope == "folder":
        assert not result.repository_results[0].inventory.complete
    else:
        assert not result.inventory.complete


def test_folder_marker_cannot_combine_with_child_remote(
    project: Path, cache: Path
) -> None:
    _install_payload(
        cache,
        "employer-a",
        dict(
            EMPLOYER, detect={"all": [{"file": "marker"}, {"remote": "^employer-a/"}]}
        ),
    )
    (project / "marker").touch()
    child = _repository(project / "service", "git@example.test:employer-a/service.git")
    assert not gate.assess(project, _found(cache, project)).applicable
    (child / "marker").touch()
    assert gate.assess(project, _found(cache, project)).scope_state == "work"


@pytest.mark.parametrize(
    "detect",
    [
        {"files": ["nested/marker.py"]},
        {"globs": ["*.py"]},
        {"content": [{"glob": "*.py", "pattern": "marker"}]},
    ],
)
def test_nested_git_markers_do_not_establish_outer_technical_tiers(
    project: Path, cache: Path, detect: dict[str, object]
) -> None:
    _repository(project, "git@example.test:personal/tool.git")
    nested = _repository(project / "nested", "git@example.test:personal/nested.git")
    (nested / "marker.py").write_text("marker", encoding="utf-8")
    _install_payload(
        cache,
        "technical",
        {
            "schema_version": 1,
            "tier": "technical",
            "applies": "stack-present",
            "detect": detect,
        },
    )

    assert not gate.assess(project, _found(cache, project)).applicable


def test_linked_worktree_is_a_repository_boundary(project: Path, cache: Path) -> None:
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

    result = gate.assess(workspace, _found(cache, workspace))

    assert result.scope_state == "work"
    assert result.inventory == [child]


def test_entry_limit_never_produces_a_negative_scope(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for index in range(4):
        (project / str(index)).touch()
    monkeypatch.setattr(gate, "WORKSPACE_ENTRIES", 3)

    result = gate.assess(project, [])

    assert result.scope_state == "undetermined"
    assert not result.inventory.complete
    assert result.inventory.reason == "directory entry limit reached"


def test_git_queries_share_one_deadline_and_cache(
    project: Path, cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    _repository(project, "git@example.test:employer-a/service.git")
    elapsed = 0.0
    calls = []

    def run(
        arguments: list[str],
        *,
        capture_output: bool,
        text: bool,
        encoding: str,
        timeout: float,
    ) -> subprocess.CompletedProcess[str]:
        nonlocal elapsed
        calls.append((arguments[3:], timeout))
        if arguments[3] == "rev-parse":
            elapsed += 1
            return subprocess.CompletedProcess(arguments, 0, stdout=str(project))
        elapsed += timeout
        raise subprocess.TimeoutExpired(arguments, timeout)

    monkeypatch.setattr(gate.time, "monotonic", lambda: elapsed)
    monkeypatch.setattr(gate.process, "run", run)
    result = gate.assess(project, _found(cache, project))

    assert result.scope_state == "undetermined"
    assert not result.inventory.complete
    assert [timeout for _, timeout in calls] == [gate.GIT_TIMEOUT, gate.GIT_TIMEOUT - 1]
    assert gate.GIT_DEADLINE.get() is None


def _directory_link(link: Path, target: Path) -> None:
    if os.name == "nt":
        subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
            check=True,
            capture_output=True,
            timeout=10,
        )
    else:
        link.symlink_to(target, target_is_directory=True)


def test_directory_links_are_deduplicated_without_escaping_workspace(
    project: Path,
    tmp_path: Path,
    cache: Path,
) -> None:
    _install_payload(cache, "employer-a", EMPLOYER)
    child = _repository(project / "service", "git@example.test:employer-a/service.git")
    _directory_link(project / "alias", child)
    result = gate.assess(project, _found(cache, project))
    assert result.inventory == [child]
    assert result.scope_state == "work"

    outside = _repository(tmp_path / "outside", "git@example.test:personal/tool.git")
    _directory_link(project / "outside-link", outside)
    result = gate.assess(project, _found(cache, project))
    assert not result.inventory.complete
    assert result.scope_state == "undetermined"
    assert not result.applicable


def test_personal_adoption_cannot_be_borrowed_through_directory_link(
    project: Path,
    tmp_path: Path,
    cache: Path,
) -> None:
    _install_payload(cache, "personal", PERSONAL, marketplace="tj-agents")
    _repository(project, "git@example.test:personal/tool.git")
    outside = _repository(tmp_path / "outside", "git@example.test:personal/outside.git")
    _adopt_personal(outside)
    _directory_link(project / ".agents", outside / ".agents")

    result = gate.assess(project, _found(cache, project))

    assert result.scope_state == "undetermined"
    assert not result.applicable
