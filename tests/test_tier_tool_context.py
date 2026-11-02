import importlib.util
import io
import json
import subprocess
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "tier_tool_context_gate", ROOT / ".agents/hooks/tier_gate.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = _load_gate()


def test_native_utf8_payload_is_independent_of_windows_console_encoding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "tool_name": "Read",
        "tool_input": {"file_path": "workspace café/東京.py"},
    }
    stream = io.TextIOWrapper(
        io.BytesIO(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
        encoding="cp1252",
    )
    monkeypatch.setattr(gate.sys, "stdin", stream)

    assert gate._stdin_payload() == payload


def test_unicode_repository_boundary_survives_git_output(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "workspace café 東京", "personal")

    selection = gate.path_selection(str(repository / "new.py"))

    assert selection["repository"] == str(repository)
    assert selection["complete"]


@pytest.fixture(autouse=True)
def isolated_plugins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "cache_roots", list)
    monkeypatch.delenv(gate.OVERRIDE_VARIABLE, raising=False)


def _repository(path: Path, name: str) -> Path:
    path.mkdir(parents=True)
    subprocess.run(["git", "-C", str(path), "init", "--quiet"], check=True, timeout=10)
    subprocess.run(
        [
            "git",
            "-C",
            str(path),
            "config",
            "remote.origin.url",
            f"git@example.test:{name}/project.git",
        ],
        check=True,
        timeout=10,
    )
    return path


def test_claude_typed_paths_are_extracted_without_shell_or_mentions() -> None:
    assert gate.tool_paths(
        {"tool_name": "Read", "tool_input": {"file_path": "src/a.py"}}
    ) == ["src/a.py"]
    assert gate.tool_paths({"tool_name": "Glob", "tool_input": {"path": "src"}}) == [
        "src"
    ]
    assert (
        gate.tool_paths(
            {"tool_name": "Bash", "tool_input": {"command": "cat src/a.py"}}
        )
        == []
    )
    assert gate.tool_paths(
        {
            "tool_name": "Read",
            "tool_input": {"file_path": "src/a.py", "mentions": ["other.py"]},
        }
    ) == ["src/a.py"]


def test_codex_apply_patch_extracts_each_supported_source_and_move_destination() -> (
    None
):
    payload = {
        "tool_name": "apply_patch",
        "tool_input": {
            "command": (
                "*** Begin Patch\n*** Update File: src/old.py\n"
                "*** Move to: src/new.py\n"
                "@@\n-x\n+y\n*** Add File: docs/new.md\n+x\n"
                "*** Delete File: docs/old.md\n*** End Patch"
            )
        },
    }

    assert gate.tool_paths(payload) == [
        "src/old.py",
        "src/new.py",
        "docs/new.md",
        "docs/old.md",
    ]


def test_unsupported_patch_forms_and_opaque_tools_require_explicit_resolution() -> None:
    assert (
        gate.tool_paths(
            {"tool_name": "apply_patch", "tool_input": {"patch": "diff --git a/a b/a"}}
        )
        == []
    )
    assert "Resolve target paths" in gate.tool_context(
        {"tool_name": "exec_command", "tool_input": {"cmd": "type secret.txt"}}
    )


def test_claude_search_without_path_uses_the_event_cwd(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository", "personal")

    assert gate.tool_paths(
        {"tool_name": "Grep", "cwd": str(repository), "tool_input": {}}
    ) == [str(repository)]


def test_typed_relative_path_uses_the_event_cwd(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository", "personal")
    (repository / "src").mkdir()

    selection = gate.path_selection("src", str(repository))

    assert selection["repository"] == str(repository)
    assert "Repository scope excludes nested Git roots" in selection["context"]


def test_path_selection_keeps_mixed_repositories_separate(tmp_path: Path) -> None:
    first = _repository(tmp_path / "first", "personal")
    second = _repository(tmp_path / "second", "employer-a")
    (first / "src").mkdir()
    (second / "src").mkdir()

    selections = [
        gate.path_selection(str(first / "src")),
        gate.path_selection(str(second / "src")),
    ]

    assert [selection["repository"] for selection in selections] == [
        str(first),
        str(second),
    ]
    assert all(selection["scope"] == "repository" for selection in selections)


def test_new_file_uses_nearest_existing_parent_repository(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repository", "personal")
    target = repository / "new" / "deep" / "file.py"

    selection = gate.path_selection(str(target))

    assert selection["anchor"] == str(repository)
    assert selection["repository"] == str(repository)


@pytest.mark.parametrize("existing", [True, False])
def test_file_beside_repositories_does_not_inherit_their_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, existing: bool
) -> None:
    repository = _repository(tmp_path / "personal", "personal")
    (repository / ".agents").mkdir()
    (repository / ".agents/plugins.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "plugins": ["personal@tj-agents"],
                "marketplaces": {"tj-agents": {"repository": "tj-agents/marketplace"}},
            }
        ),
        encoding="utf-8",
    )
    declarations = [
        gate.Declaration(
            "personal",
            "tj-agents",
            {"schema_version": 1, "tier": "personal", "applies": "always"},
        )
    ]
    monkeypatch.setattr(gate, "declarations", lambda project: declarations)
    target = tmp_path / "notes.txt"
    if existing:
        target.write_text("outside the repository", encoding="utf-8")

    assert gate.path_selection(str(tmp_path))["scope_state"] == "personal"
    selection = gate.path_selection(str(target))

    assert selection["repository"] is None
    assert selection["scope_state"] == "undetermined"
    assert selection["applicable"] == []
    assert selection["repositories"] == []


def test_cli_path_output_is_json_and_repeatable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = _repository(tmp_path / "first", "personal")
    second = _repository(tmp_path / "second", "employer-a")
    monkeypatch.setattr(
        gate.sys, "argv", ["tier_gate.py", "--path", str(first), "--path", str(second)]
    )
    output: list[str] = []
    monkeypatch.setattr(gate, "print", output.append, raising=False)

    assert gate.main() == 0
    value = json.loads(output[0])
    assert [item["repository"] for item in value["paths"]] == [str(first), str(second)]


@pytest.mark.parametrize(
    "patch",
    [
        "*** Update File: one.py\n@@\n-a\n+b",
        "*** Begin Patch\n*** Delete File: one.py\n*** Move to: two.py\n*** End Patch",
        (
            "*** Begin Patch\n*** Add File: one.py\n+x\n"
            "*** Unknown File: two.py\n*** End Patch"
        ),
    ],
)
def test_partial_or_unknown_patch_is_not_claimed_as_resolved(patch: str) -> None:
    assert (
        gate.tool_paths({"tool_name": "apply_patch", "tool_input": {"command": patch}})
        == []
    )


def test_personal_work_personal_operations_use_current_target_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    personal = _repository(tmp_path / "personal", "personal")
    work = _repository(tmp_path / "work", "employer-a")
    (personal / ".agents").mkdir()
    adoption = personal / ".agents/plugins.json"
    adoption.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "plugins": ["personal@tj-agents"],
                "marketplaces": {"tj-agents": {"repository": "tj-agents/marketplace"}},
            }
        ),
        encoding="utf-8",
    )
    payload = tmp_path / "employer-payload"
    context = payload / "skills/communication-context"
    context.mkdir(parents=True)
    (context / "SKILL.md").write_text(
        "---\nname: communication-context\nkind: knowledge\n---\nEmployer contacts.\n",
        encoding="utf-8",
    )
    declarations = [
        gate.Declaration(
            "personal",
            "tj-agents",
            {"schema_version": 1, "tier": "personal", "applies": "always"},
        ),
        gate.Declaration(
            "work",
            "tj-agents",
            {
                "schema_version": 3,
                "tier": "work",
                "applies": "stack-present",
                "detect": {"fact": "employer"},
            },
        ),
        gate.Declaration(
            "employer-a",
            "tj-agents",
            {
                "schema_version": 3,
                "tier": "employer-a",
                "applies": "stack-present",
                "detect": {"remote": "^employer-a/"},
                "employer": {"context_skill": "communication-context"},
            },
            payload,
        ),
    ]
    monkeypatch.setattr(gate, "declarations", lambda project: declarations)

    selections = [
        gate.path_selection(str(path / "new.py")) for path in (personal, work, personal)
    ]
    assert [item["scope_state"] for item in selections] == [
        "personal",
        "work",
        "personal",
    ]
    assert [set(item["applicable"]) for item in selections] == [
        {"personal@tj-agents"},
        {"work@tj-agents", "employer-a@tj-agents"},
        {"personal@tj-agents"},
    ]
    assert "employer-a:*" not in selections[2]["context"]
    search = gate.tool_context(
        {"tool_name": "Grep", "cwd": str(tmp_path), "tool_input": {}}
    )
    assert "Organizational scope: mixed" in search
    assert "Applies here:" not in search
    patch = (
        f"*** Begin Patch\n*** Add File: {personal}/one.py\n+x\n"
        f"*** Add File: {work}/two.py\n+y\n*** End Patch"
    )
    contexts = gate.tool_context(
        {"tool_name": "apply_patch", "tool_input": {"command": patch}}
    )
    assert str(personal) in contexts and str(work) in contexts
    assert (
        "Organizational scope: personal" in contexts
        and "Organizational scope: work" in contexts
    )
    adoption.unlink()
    assert gate.path_selection(str(personal))["scope_state"] == "unclassified"
    subprocess.run(
        [
            "git",
            "-C",
            str(work),
            "config",
            "remote.origin.url",
            "git@example.test:unknown/project.git",
        ],
        check=True,
        timeout=10,
    )
    assert gate.path_selection(str(work))["scope_state"] == "unclassified"
