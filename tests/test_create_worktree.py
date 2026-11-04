import json
import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".agents/engineering/operation/open-worktree/scripts/create_worktree.py"
)


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
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPT), branch, *arguments],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )


def create(repo: Path, branch: str, *arguments: str) -> dict[str, str]:
    result = invoke(repo, branch, *arguments)
    assert result.returncode == 0, result.stdout + result.stderr
    return cast(dict[str, str], json.loads(result.stdout))


@pytest.mark.parametrize("branch", ["Feature/BrowserCredentials", "Fix/Nested/Branch"])
def test_new_branch_uses_nested_flattened_path(repo: Path, branch: str) -> None:
    result = create(repo, branch)
    expected = repo / ".worktrees" / branch.replace("/", "-")
    assert Path(result["path"]) == expected
    assert git(expected, "branch", "--show-current") == branch
    assert git(expected, "status", "--porcelain") == ""
    assert result["head"] == git(repo, "rev-parse", "HEAD")
    assert not (repo.parent / f"{repo.name}.worktrees").exists()


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


def test_existing_destination_is_preserved(repo: Path) -> None:
    first = create(repo, "Feature/Repeated")
    result = invoke(repo, "Feature/Repeated")
    assert result.returncode == 1
    assert "already exists" in result.stdout
    assert git(Path(first["path"]), "rev-parse", "HEAD") == first["head"]


def test_linked_checkout_resolves_primary_repository(repo: Path) -> None:
    first = create(repo, "Feature/First")
    result = create(Path(first["path"]), "Feature/Second")
    assert Path(result["repository"]) == repo
    assert Path(result["path"]) == repo / ".worktrees" / "Feature-Second"


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


@pytest.mark.parametrize("branch", ["../Escape", "Bad?Branch", "Bad Branch"])
def test_invalid_branch_fails_before_fetch_or_creation(repo: Path, branch: str) -> None:
    git(repo, "remote", "add", "origin", str(repo / "missing-origin"))
    result = invoke(repo, branch)
    assert result.returncode == 1
    assert "invalid branch name" in result.stdout
    assert not (repo / ".worktrees").exists()


def test_case_variant_of_existing_branch_is_not_created(repo: Path) -> None:
    git(repo, "branch", "Feature/Existing")
    result = invoke(repo, "feature/existing")
    assert result.returncode == 1
    assert "existing branch casing: Feature/Existing" in result.stdout
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
