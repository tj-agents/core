import io
import json
import runpy
import shutil
import subprocess
import sys
from collections.abc import Callable
from contextlib import chdir, redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".agents/engineering/operation/open-worktree/scripts/create_worktree.py"
)


@dataclass
class Ownership:
    calls: list[Path] = field(default_factory=list)
    claimed: list[Path] = field(default_factory=list)
    refusal: str | None = None
    available: bool = True
    session: str | None = "codex:test-session"
    error: OSError | subprocess.TimeoutExpired | None = None


@pytest.fixture(autouse=True)
def ownership(monkeypatch: pytest.MonkeyPatch) -> Ownership:
    boundary = Ownership()
    actual_run = subprocess.run

    def which(command: str) -> str | None:
        assert command == ("tj.exe" if sys.platform == "win32" else "tj")
        return "fake-tj" if boundary.available else None

    def run(
        command: list[str],
        *,
        cwd: Path | None = None,
        check: bool = False,
        capture_output: bool = False,
        text: bool = False,
        encoding: str = "utf-8",
        errors: str = "strict",
        timeout: int = 30,
    ) -> subprocess.CompletedProcess[str]:
        if command[0] != "fake-tj":
            return actual_run(
                command,
                cwd=cwd,
                check=check,
                capture_output=capture_output,
                text=text,
                encoding=encoding,
                errors=errors,
                timeout=timeout,
            )
        assert command[1:4] == ["session", "claim-worktree", "--path"]
        path = Path(command[4])
        assert cwd == path
        assert (path / ".git").is_file()
        boundary.calls.append(path)
        if boundary.error is not None:
            raise boundary.error
        if boundary.refusal is not None:
            return subprocess.CompletedProcess(command, 1, "", boundary.refusal)
        if boundary.session is not None:
            boundary.claimed.append(path)
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps(
                {
                    "ownership": (
                        {
                            "path": str(path),
                            "session": boundary.session,
                            "launch_id": "test-launch",
                            "claimed_at": "2026-11-11T00:00:00Z",
                        }
                        if boundary.session is not None
                        else None
                    )
                }
            ),
            "",
        )

    monkeypatch.setattr(shutil, "which", which)
    monkeypatch.setattr(subprocess, "run", run)
    return boundary


def git(cwd: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(cwd), *arguments],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    ).stdout.strip()


def commit(repo: Path, message: str) -> str:
    git(
        repo,
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@t",
        "commit",
        "-q",
        "--allow-empty",
        "-m",
        message,
    )
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    path = tmp_path / "repo ü space"
    path.mkdir()
    git(path, "init", "-q", "-b", "main")
    commit(path, "initial")
    return path


@pytest.fixture
def remote(repo: Path, tmp_path: Path) -> Path:
    path = tmp_path / "origin ü space.git"
    git(repo, "branch", "-m", "trunk")
    git(repo, "clone", "--bare", str(repo), str(path))
    git(repo, "remote", "add", "origin", str(path))
    return path


def invoke(
    repo: Path, branch: str, *arguments: str
) -> subprocess.CompletedProcess[str]:
    main = cast(Callable[[list[str]], int], runpy.run_path(str(SCRIPT))["main"])
    output = io.StringIO()
    with chdir(repo), redirect_stdout(output):
        returncode = main([branch, *arguments])
    return subprocess.CompletedProcess(
        [str(SCRIPT), branch, *arguments], returncode, output.getvalue(), ""
    )


def create(repo: Path, branch: str, *arguments: str) -> dict[str, str]:
    result = invoke(repo, branch, *arguments)
    assert result.returncode == 0, result.stdout + result.stderr
    return cast(dict[str, str], json.loads(result.stdout))


@pytest.mark.parametrize("branch", ["Feature/BrowserCredentials", "Fix/Nested/Branch"])
def test_new_branch_uses_nested_flattened_path(
    repo: Path, branch: str, ownership: Ownership
) -> None:
    result = create(repo, branch)
    expected = repo / ".worktrees" / branch.replace("/", "-")
    assert Path(result["path"]) == expected
    assert git(expected, "branch", "--show-current") == branch
    assert git(expected, "status", "--porcelain") == ""
    assert result["head"] == git(repo, "rev-parse", "HEAD")
    assert not (repo.parent / f"{repo.name}.worktrees").exists()
    assert ownership.claimed == [expected]


def test_existing_local_branch_keeps_its_tip(repo: Path) -> None:
    existing_tip = commit(repo, "existing")
    git(repo, "branch", "Feature/Existing")
    commit(repo, "newer default")
    result = create(repo, "Feature/Existing")
    assert result["head"] == existing_tip
    assert result["base"] == "(existing branch)"
    assert result["base_head"] == existing_tip


def test_explicit_parent_uses_recorded_tip(repo: Path) -> None:
    parent_tip = git(repo, "rev-parse", "HEAD")
    commit(repo, "newer default")
    result = create(repo, "Feature/DependentLayer", "--from", parent_tip)
    assert result["head"] == parent_tip
    assert result["base"] == parent_tip
    assert result["base_head"] == parent_tip


def test_existing_checkout_is_reused_with_dirty_work_preserved(
    repo: Path, ownership: Ownership
) -> None:
    first = create(repo, "Feature/Repeated")
    worktree = Path(first["path"])
    (worktree / "unfinished.txt").write_text("keep this work", encoding="utf-8")
    result = invoke(repo, "Feature/Repeated")
    assert result.returncode == 0, result.stdout
    repeated = json.loads(result.stdout)
    assert repeated["path"] == first["path"]
    assert repeated["head"] == first["head"]
    assert git(worktree, "status", "--porcelain") == "?? unfinished.txt"
    assert (worktree / "unfinished.txt").read_text(encoding="utf-8") == "keep this work"
    assert ownership.calls == [worktree, worktree]


def test_existing_checkout_owned_by_another_session_is_not_reused(
    repo: Path, ownership: Ownership
) -> None:
    first = create(repo, "Feature/Owned")
    ownership.refusal = "checkout belongs to another live session"
    result = invoke(repo, "Feature/Owned")
    assert result.returncode == 1
    assert ownership.refusal in result.stdout
    assert git(Path(first["path"]), "rev-parse", "HEAD") == first["head"]


def test_unregistered_destination_is_preserved(repo: Path) -> None:
    path = repo / ".worktrees" / "Feature-Unregistered"
    path.mkdir(parents=True)
    (path / "keep.txt").write_text("keep", encoding="utf-8")
    result = invoke(repo, "Feature/Unregistered")
    assert result.returncode == 1
    assert "already exists" in result.stdout
    assert (path / "keep.txt").read_text(encoding="utf-8") == "keep"


def test_flattened_branch_collision_preserves_original_checkout(repo: Path) -> None:
    first = create(repo, "Feature/Two-Parts")
    result = invoke(repo, "Feature/Two/Parts")
    assert result.returncode == 1
    assert "already exists" in result.stdout
    assert git(Path(first["path"]), "branch", "--show-current") == "Feature/Two-Parts"


def test_legacy_checkout_is_reported_without_moving_or_claiming(
    repo: Path, ownership: Ownership
) -> None:
    path = repo.parent / f"{repo.name}.worktrees" / "Feature-Legacy"
    git(repo, "worktree", "add", "-b", "Feature/Legacy", str(path))
    result = invoke(repo, "Feature/Legacy")
    assert result.returncode == 1
    assert "migrate it" in result.stdout
    assert path.is_dir()
    assert ownership.calls == []


def test_explicit_repository_is_resolved_outside_a_checkout(
    repo: Path, tmp_path: Path
) -> None:
    result = create(tmp_path, "Feature/Explicit", "--repo", str(repo))
    assert Path(result["repository"]) == repo
    assert Path(result["path"]) == repo / ".worktrees" / "Feature-Explicit"


def test_separate_git_directory_does_not_become_the_primary_root(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "separate primary"
    metadata = tmp_path / "metadata"
    repo.mkdir()
    git(repo, "init", "-b", "main", "--separate-git-dir", str(metadata))
    commit(repo, "initial")
    result = create(repo, "Feature/SeparateGitDir")
    assert Path(result["path"]) == repo / ".worktrees" / "Feature-SeparateGitDir"


def test_linked_checkout_resolves_primary_repository(
    repo: Path, ownership: Ownership
) -> None:
    first = create(repo, "Feature/First")
    result = create(Path(first["path"]), "Feature/Second")
    assert Path(result["repository"]) == repo
    assert Path(result["path"]) == repo / ".worktrees" / "Feature-Second"
    assert ownership.claimed == [Path(first["path"]), Path(result["path"])]


def test_refused_ownership_preserves_created_checkout(
    repo: Path, ownership: Ownership
) -> None:
    ownership.refusal = "checkout already belongs to another session"
    result = invoke(repo, "Feature/Refused")
    path = repo / ".worktrees" / "Feature-Refused"
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert str(path) in payload["error"]
    assert ownership.refusal in payload["error"]
    assert "head" not in payload
    assert git(path, "branch", "--show-current") == "Feature/Refused"
    assert ownership.calls == [path]
    assert ownership.claimed == []


def test_creation_outside_agent_session_keeps_existing_output(
    repo: Path, ownership: Ownership
) -> None:
    ownership.session = None
    result = create(repo, "Feature/OutsideSession")
    assert set(result) == {"repository", "branch", "path", "head", "base", "base_head"}
    assert ownership.calls == [Path(result["path"])]
    assert ownership.claimed == []


def test_checked_out_branch_refusal_does_not_claim(
    repo: Path, ownership: Ownership
) -> None:
    result = invoke(repo, "main")
    assert result.returncode == 1
    assert "main" in json.loads(result.stdout)["error"]
    assert not (repo / ".worktrees" / "main").exists()
    assert ownership.calls == []


def test_missing_tj_reports_created_checkout(repo: Path, ownership: Ownership) -> None:
    ownership.available = False
    result = invoke(repo, "Feature/MissingTj")
    path = repo / ".worktrees" / "Feature-MissingTj"
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert str(path) in payload["error"]
    assert "tj is not installed" in payload["error"]
    assert git(path, "branch", "--show-current") == "Feature/MissingTj"
    assert ownership.calls == []


@pytest.mark.parametrize(
    "error",
    [OSError("cannot execute tj"), subprocess.TimeoutExpired("tj", 60)],
)
def test_ownership_process_error_reports_created_checkout(
    repo: Path,
    ownership: Ownership,
    error: OSError | subprocess.TimeoutExpired,
) -> None:
    ownership.error = error
    result = invoke(repo, "Feature/FailedProcess")
    path = repo / ".worktrees" / "Feature-FailedProcess"
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert str(path) in payload["error"]
    assert "ownership claim failed" in payload["error"]
    assert git(path, "branch", "--show-current") == "Feature/FailedProcess"
    assert ownership.claimed == []


def test_fetches_current_non_main_remote_default_without_origin_head(
    repo: Path, remote: Path, tmp_path: Path
) -> None:
    writer = tmp_path / "writer"
    git(repo, "clone", str(remote), str(writer))
    remote_tip = commit(writer, "new remote default")
    git(writer, "push", "origin", "trunk")
    assert git(repo, "for-each-ref", "refs/remotes/origin/HEAD") == ""
    result = create(repo, "Feature/FetchedDefault")
    assert result["head"] == remote_tip
    assert result["base"] == "origin/trunk"
    assert result["base_head"] == remote_tip


def test_remote_only_branch_is_created_with_tracking(repo: Path, remote: Path) -> None:
    remote_tip = git(repo, "rev-parse", "HEAD")
    git(repo, "push", "origin", "HEAD:refs/heads/Feature/Remote")
    result = create(repo, "Feature/Remote")
    assert result["head"] == remote_tip
    assert result["base"] == "origin/Feature/Remote"
    assert git(Path(result["path"]), "rev-parse", "--abbrev-ref", "@{upstream}") == (
        "origin/Feature/Remote"
    )


def test_deleted_remote_branch_is_pruned_before_casing_check(
    repo: Path, remote: Path
) -> None:
    git(repo, "push", "origin", "HEAD:refs/heads/feature/Gone")
    git(repo, "fetch", "origin")
    git(remote, "update-ref", "-d", "refs/heads/feature/Gone")
    result = create(repo, "Feature/Gone")
    assert Path(result["path"]) == repo / ".worktrees" / "Feature-Gone"
    assert result["base"] == "origin/trunk"


@pytest.mark.parametrize("branch", ["../Escape", "Bad?Branch", "Bad Branch"])
def test_invalid_branch_fails_before_fetch_or_creation(repo: Path, branch: str) -> None:
    git(repo, "remote", "add", "origin", str(repo / "missing-origin"))
    result = invoke(repo, branch)
    assert result.returncode == 1
    assert "invalid branch name" in result.stdout
    assert not (repo / ".worktrees").exists()


def test_case_variant_of_existing_branch_is_not_created(
    repo: Path, ownership: Ownership
) -> None:
    git(repo, "branch", "Feature/Existing")
    result = invoke(repo, "feature/existing")
    assert result.returncode == 1
    assert "existing branch casing: Feature/Existing" in result.stdout
    assert not (repo / ".worktrees").exists()
    assert ownership.calls == []


@pytest.mark.parametrize("branch", ["feature/New", "new-feature"])
def test_new_branch_requires_capitalized_type(repo: Path, branch: str) -> None:
    result = invoke(repo, branch)
    assert result.returncode == 1
    assert "capitalized <Type>/<Name>" in result.stdout
    assert not (repo / ".worktrees").exists()


def test_redirected_worktree_directory_does_not_create_outside_repo(
    repo: Path, tmp_path: Path
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (repo / ".worktrees").symlink_to(outside, target_is_directory=True)
    except OSError as error:
        if sys.platform != "win32":
            pytest.skip(f"directory symlink permission unavailable: {error}")
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(repo / ".worktrees"), str(outside)],
            check=True,
            capture_output=True,
            timeout=30,
        )
    result = invoke(repo, "Feature/Outside")
    assert result.returncode == 1
    assert "destination is redirected" in result.stdout
    assert list(outside.iterdir()) == []
    assert git(repo, "branch", "--list", "Feature/Outside") == ""
