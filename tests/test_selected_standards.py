import importlib
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
        "selected_standards_gate", ROOT / ".agents/hooks/tier_gate.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = _load_gate()
selected = importlib.import_module("selected_standards")


def _git(repository: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True,
        encoding="utf-8",
        check=True,
        timeout=10,
    )


@pytest.fixture
def worktrees(tmp_path: Path) -> tuple[Path, Path]:
    primary = tmp_path / "repository café"
    primary.mkdir()
    _git(primary, "init", "--quiet")
    _git(
        primary,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.test",
        "commit",
        "--quiet",
        "--allow-empty",
        "-m",
        "Fixture",
    )
    selection = primary / ".agents/plugins.json"
    selection.parent.mkdir()
    selection.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "plugins": ["python@market"],
                "marketplaces": {"market": {"repository": "example/marketplace"}},
            }
        ),
        encoding="utf-8",
    )
    (primary / ".git/info/exclude").write_text("/.agents/\n", encoding="utf-8")
    linked = tmp_path / "linked 東京"
    _git(primary, "worktree", "add", "--quiet", "--detach", str(linked))
    return primary, linked


def test_selection_inherits_an_excluded_primary_file(
    worktrees: tuple[Path, Path],
) -> None:
    primary, linked = worktrees
    assert not (linked / ".agents/plugins.json").exists()
    selection = selected.PluginSelection.read(linked)
    assert selection is not None
    assert selection.path == primary / ".agents/plugins.json"
    assert selection.identities == ("python@market",)


def test_invalid_local_selection_is_never_hidden_by_inheritance(
    worktrees: tuple[Path, Path],
) -> None:
    _, linked = worktrees
    (linked / ".agents").mkdir()
    (linked / ".agents/plugins.json").write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid repository plugin selection"):
        selected.PluginSelection.read(linked)


def test_missing_selection_does_not_use_an_enclosing_repository(
    worktrees: tuple[Path, Path],
) -> None:
    primary, _ = worktrees
    nested = primary / "nested"
    nested.mkdir()
    _git(nested, "init", "--quiet")
    assert selected.PluginSelection.read(nested) is None


def test_session_context_identifies_the_worktree_and_inherited_source(
    worktrees: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    primary, linked = worktrees
    declaration = gate.Declaration(
        "python",
        "market",
        {
            "schema_version": 1,
            "tier": "python",
            "applies": "stack-present",
            "detect": {"globs": ["*.py"]},
        },
    )
    monkeypatch.setattr(gate, "declarations", lambda project: [declaration])

    def unexpected(*args: object, **kwargs: object) -> None:
        raise AssertionError("SessionStart must not scan Git for a selected repository")

    monkeypatch.setattr(gate, "_git", unexpected)
    context = gate.statement(linked)
    assert str(linked) in context
    assert str(primary / ".agents/plugins.json") in context
    assert "Selected stacks: python." in context
    assert "descriptions match the task" in context


@pytest.mark.parametrize("tool", ["Write", "apply_patch"])
def test_normal_writes_do_not_require_a_standards_read_ledger(
    worktrees: tuple[Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tool: str,
) -> None:
    _, linked = worktrees
    state = tmp_path / "state"
    payload = {
        "session_id": "fresh-session",
        "cwd": str(linked),
        "tool_name": tool,
        "tool_input": {
            "file_path": str(linked / "new.py"),
            "command": "*** Begin Patch\n*** Add File: new.py\n+x = 1\n*** End Patch",
        },
    }
    monkeypatch.setenv(gate.STATE_DIRECTORY_VARIABLE, str(state))
    monkeypatch.setattr(gate.sys, "argv", ["tier_gate.py", "--tool-gate"])
    monkeypatch.setattr(
        gate.sys,
        "stdin",
        io.TextIOWrapper(
            io.BytesIO(json.dumps(payload).encode("utf-8")),
            encoding="utf-8",
        ),
    )
    assert gate.main() == 0
    assert capsys.readouterr().out == ""
    assert not state.exists()


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_host_hooks_retain_boundaries_without_read_tracking(host: str) -> None:
    path = ROOT / ".agents/plugins/manifests" / host / "base-hooks.json"
    hooks = json.loads(path.read_text(encoding="utf-8"))["hooks"]
    assert "PostCompact" not in hooks
    assert all(group.get("matcher") != "Read" for group in hooks["PreToolUse"])
    write_matcher = (
        "Edit|Write|MultiEdit|NotebookEdit" if host == "claude" else "apply_patch"
    )
    group = next(
        group for group in hooks["PreToolUse"] if group["matcher"] == write_matcher
    )
    assert "--tool-gate" in json.dumps(group)


def test_session_event_directory_takes_precedence_over_the_launch_directory(
    worktrees: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    primary, linked = worktrees
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(primary))
    monkeypatch.setattr(gate, "declarations", lambda project: [])
    monkeypatch.setattr(gate.sys, "argv", ["tier_gate.py", "--session-context"])
    monkeypatch.setattr(
        gate.sys,
        "stdin",
        io.TextIOWrapper(
            io.BytesIO(json.dumps({"cwd": str(linked)}).encode("utf-8")),
            encoding="utf-8",
        ),
    )
    assert gate.main() == 0
    context = json.loads(capsys.readouterr().out)["hookSpecificOutput"][
        "additionalContext"
    ]
    assert f"Repository standards for {linked}" in context
    assert str(primary / ".agents/plugins.json") in context
