import importlib.util
import os
import py_compile
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def snapshot() -> ModuleType:
    return load_module("source_snapshot", ROOT / ".codex/hooks/snapshot.py")


@pytest.fixture
def package(tmp_path: Path) -> Path:
    root = tmp_path / "base/payload"
    (root / "hooks/codex").mkdir(parents=True)
    (root / "hooks/codex/snapshot.py").write_bytes(
        (ROOT / ".codex/hooks/snapshot.py").read_bytes()
    )
    (root / "hooks/probe.py").write_text(
        "import frozen_source\nprint(frozen_source.VALUE)\n", encoding="utf-8"
    )
    (root / "hooks/frozen_source.py").write_text("VALUE = 'SOURCE'\n", encoding="utf-8")
    return root


def stale_cache(path: Path, mode: py_compile.PycInvalidationMode) -> Path:
    path.write_text("VALUE = 'CACHED'\n", encoding="utf-8")
    stamp = path.stat().st_mtime_ns
    cache = Path(importlib.util.cache_from_source(str(path)))
    py_compile.compile(
        str(path), cfile=str(cache), doraise=True, invalidation_mode=mode
    )
    path.write_text("VALUE = 'SOURCE'\n", encoding="utf-8")
    os.utime(path, ns=(stamp, stamp))
    return cache


def execute(
    package: Path, digest: str, snapshots: Path | None
) -> subprocess.CompletedProcess[str]:
    generator = load_module(
        "source_generator", ROOT / "scripts/sync_plugin_packages.py"
    )
    loader = (ROOT / ".codex/hooks/snapshot.py").read_text(encoding="utf-8")
    bootstrap = generator.codex_snapshot_bootstrap(ROOT, loader)
    environment = dict(os.environ)
    environment.pop("PLUGIN_DATA", None)
    environment.pop("TJ_AGENTS_STARTUP_SNAPSHOT_DIRECTORY", None)
    if snapshots is not None:
        environment["TJ_AGENTS_STARTUP_SNAPSHOT_DIRECTORY"] = str(snapshots)
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            bootstrap,
            str(package),
            digest,
            "base",
            str(package / "hooks/probe.py"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
        timeout=30,
        check=False,
    )


@pytest.mark.parametrize(
    "mode",
    [
        py_compile.PycInvalidationMode.TIMESTAMP,
        py_compile.PycInvalidationMode.UNCHECKED_HASH,
    ],
)
@pytest.mark.parametrize("cached_snapshot", [False, True])
def test_bootstrap_executes_pinned_source_despite_stale_bytecode(
    snapshot: ModuleType,
    package: Path,
    tmp_path: Path,
    mode: py_compile.PycInvalidationMode,
    cached_snapshot: bool,
) -> None:
    stale_cache(package / "hooks/frozen_source.py", mode)
    digest = snapshot.digest_tree(package)
    snapshots = tmp_path / "snapshots" if cached_snapshot else None
    result = execute(package, digest, snapshots)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "SOURCE\n"
    if snapshots is not None:
        selected = snapshot.Snapshot.for_package(package, digest, snapshots).path
        stale_cache(selected / "hooks/frozen_source.py", mode)
        result = execute(package, digest, snapshots)
        assert result.returncode == 0, result.stderr
        assert result.stdout == "SOURCE\n"


def test_generated_cache_does_not_change_package_identity(
    snapshot: ModuleType, package: Path
) -> None:
    digest = snapshot.digest_tree(package)
    stale_cache(
        package / "hooks/frozen_source.py", py_compile.PycInvalidationMode.TIMESTAMP
    )
    assert snapshot.digest_tree(package) == digest


@pytest.mark.parametrize(
    "relative",
    [
        "hooks/frozen_source.py",
        "hooks/legacy.pyc",
        "hooks/__pycache__/legacy.pyc",
        "hooks/__pycache__/unexpected.bin",
        "hooks/__pycache__/probe.cpython-312.pyc.extra",
    ],
)
def test_source_and_unexpected_cache_bytes_still_invalidate_identity(
    snapshot: ModuleType, package: Path, relative: str
) -> None:
    digest = snapshot.digest_tree(package)
    path = package / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"changed")
    assert snapshot.digest_tree(package) != digest
    with pytest.raises(SystemExit) as failure:
        snapshot.verified(package, digest)
    assert failure.value.code == 2


def test_snapshot_copy_omits_only_recognized_source_caches(
    snapshot: ModuleType, package: Path, tmp_path: Path
) -> None:
    cache = stale_cache(
        package / "hooks/frozen_source.py", py_compile.PycInvalidationMode.TIMESTAMP
    )
    unexpected = ["hooks/legacy.pyc", "hooks/__pycache__/legacy.pyc"]
    for relative in unexpected:
        (package / relative).write_bytes(b"retained")
    digest = snapshot.digest_tree(package)
    bound = snapshot.Snapshot.for_package(package, digest, tmp_path / "snapshots")
    selected = bound.resolve()
    assert not (selected / cache.relative_to(package)).exists()
    for relative in unexpected:
        assert (selected / relative).read_bytes() == b"retained"
    for path in (package / "hooks/probe.py", selected / "hooks/probe.py"):
        py_compile.compile(str(path), doraise=True)
    assert snapshot.digest_tree(package) == digest
    assert bound.resolve() == selected


@pytest.mark.parametrize(
    "relative", ["", "hooks/codex.json", "hooks/__pycache__/probe.cpython-312.pyc"]
)
def test_junctions_are_rejected_before_identity_and_copy_exclusions(
    snapshot: ModuleType,
    package: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative: str,
) -> None:
    target = package / relative
    if relative:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"unexpected")

    def junction(path: Path) -> bool:
        return path == target

    monkeypatch.setattr(Path, "is_junction", junction, raising=False)
    with pytest.raises(SystemExit) as failure:
        snapshot.digest_tree(package)
    assert failure.value.code == 2
    if relative:
        with pytest.raises(SystemExit) as failure:
            snapshot.generated_caches(str(target.parent), [target.name])
        assert failure.value.code == 2


@pytest.mark.skipif(sys.platform != "win32", reason="Windows directory junction")
def test_real_windows_junction_cannot_hide_in_a_cache_directory(
    snapshot: ModuleType, package: Path, tmp_path: Path
) -> None:
    target = tmp_path / "outside"
    target.mkdir()
    (target / "probe.cpython-312.pyc").write_bytes(b"unexpected")
    link = package / "hooks/__pycache__"
    result = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    try:
        assert link.is_junction() and link.resolve() == target.resolve()
        with pytest.raises(SystemExit) as failure:
            snapshot.digest_tree(package)
        assert failure.value.code == 2
        with pytest.raises(SystemExit) as failure:
            snapshot.generated_caches(str(link.parent), [link.name])
        assert failure.value.code == 2
    finally:
        link.rmdir()
    assert (target / "probe.cpython-312.pyc").read_bytes() == b"unexpected"
