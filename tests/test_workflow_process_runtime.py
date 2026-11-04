import runpy
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLI_RUNTIME = Path(".agents/dependencies/cli/.agents/cli/runtime")
CONTINUATION = ".codex/runtime/continuation/"


def run_help(
    root: Path, script: str, *, installed_dependencies: bool = False
) -> subprocess.CompletedProcess[str]:
    python = (
        sys.executable
        if installed_dependencies
        else str(getattr(sys, "_base_executable", sys.executable))
    )
    isolation = ["-I"] if installed_dependencies else ["-I", "-S"]
    return subprocess.run(
        [python, *isolation, "-X", "utf8", "-B", str(root / script), "--help"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )


def source_bundle(root: Path) -> Path:
    for relative in (
        ".agents/workflows",
        ".codex/runtime/continuation",
        ".agents/dependencies/cli",
        ".agents/dependencies/agent/.agents/agent/resources/lanes",
    ):
        shutil.copytree(
            ROOT / relative,
            root / relative,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
    (root / ".agents/workflow").mkdir(parents=True)
    marker = root / ".agents/plugins/sources.json"
    marker.parent.mkdir(parents=True)
    shutil.copy2(ROOT / ".agents/plugins/sources.json", marker)
    return root


@pytest.mark.parametrize(
    ("package", "script"),
    [
        ("engineering", "workflows/workflow_ops.py"),
        ("workflow", "workflows/workflow_ops.py"),
        ("workflow", CONTINUATION + "continuation_runtime.py"),
        ("workflow", CONTINUATION + "delivery_continuation.py"),
    ],
)
def test_relocated_entry_points_load_the_shipped_cli_without_site_packages(
    tmp_path: Path, package: str, script: str
) -> None:
    relocated = tmp_path / "relocated package ü"
    shutil.copytree(
        ROOT / "plugins" / package,
        relocated,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    result = run_help(relocated, script)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "script",
    [
        ".agents/workflows/workflow_ops.py",
        CONTINUATION + "continuation_runtime.py",
        CONTINUATION + "delivery_continuation.py",
    ],
)
def test_source_entry_points_load_only_the_staged_cli(
    tmp_path: Path, script: str
) -> None:
    root = source_bundle(tmp_path / "source bundle ü")
    result = run_help(root, script)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("packaged", [False, True])
def test_missing_owned_cli_cannot_use_the_installed_dependency(
    tmp_path: Path, packaged: bool
) -> None:
    root = tmp_path / "missing runtime"
    if packaged:
        shutil.copytree(
            ROOT / "plugins/workflow",
            root,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        runtime = root / "hooks/tj_cli"
        script = "workflows/workflow_ops.py"
    else:
        source_bundle(root)
        runtime = root / CLI_RUNTIME / "tj_cli"
        script = ".agents/workflows/workflow_ops.py"
    shutil.rmtree(runtime)
    result = run_help(root, script, installed_dependencies=True)
    assert result.returncode != 0
    assert "shipped CLI process runtime is unavailable" in result.stderr


@pytest.mark.parametrize(
    "script",
    [".agents/workflows/process_runtime.py", CONTINUATION + "continuation_runtime.py"],
)
def test_python_floor_is_checked_before_loading_dependencies(
    monkeypatch: pytest.MonkeyPatch, script: str
) -> None:
    monkeypatch.setattr(sys, "version_info", (3, 11, 0))
    with pytest.raises(RuntimeError, match=r"Python 3\.12"):
        runpy.run_path(str(ROOT / script))
