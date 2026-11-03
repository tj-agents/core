import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
from types import ModuleType

import pytest


def runtime_sources() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "pinned_runtime_sources",
        Path(__file__).resolve().parents[1] / "scripts/runtime_sources.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def publication(tmp_path: Path) -> tuple[Path, Path, str]:
    consumer, publisher = tmp_path / "consumer", tmp_path / "publisher"
    (consumer / ".agents/plugins").mkdir(parents=True)
    runtime = publisher / "plugins/agent/.agents/agent/runtime"
    runtime.mkdir(parents=True)
    (runtime / "guard.py").write_text("VALUE = 42\n", encoding="utf-8")
    (runtime / "binary.bin").write_bytes(bytes(range(256)))
    for arguments in (
        ["init", "--quiet"],
        ["add", "."],
        [
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "Published fixture",
        ],
    ):
        subprocess.run(
            ["git", "-C", str(publisher), *arguments], check=True, capture_output=True
        )
    revision = subprocess.check_output(
        ["git", "-C", str(publisher), "rev-parse", "HEAD"], text=True
    ).strip()
    declaration = {
        "schema_version": 1,
        "sources": {
            "agent": {
                "repository": "tj-agents/agent",
                "package": "plugins/agent",
                "revision": revision,
                "exports": [".agents/agent/runtime"],
            }
        },
    }
    (consumer / ".agents/plugins/runtime-sources.json").write_text(
        json.dumps(declaration), encoding="utf-8"
    )
    return consumer, publisher, revision


def test_exact_publication_override_records_revision_and_digest(
    publication: tuple[Path, Path, str],
) -> None:
    consumer, publisher, revision = publication
    sources = runtime_sources()
    assert sources.stage(consumer, {"agent": publisher})[0]["revision"] == revision
    assert sources.stage(consumer, {}, check=True)[0]["revision"] == revision
    receipt = json.loads(
        (consumer / ".agents/dependencies/agent/source.json").read_text()
    )
    assert receipt["sha256"] == sources.digest(
        sources.export_contents(
            consumer / ".agents/dependencies/agent", [".agents/agent/runtime"]
        )
    )
    assert (
        consumer / ".agents/dependencies/agent/.agents/agent/runtime/binary.bin"
    ).read_bytes() == bytes(range(256))


def publisher_git(publisher: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(publisher), *arguments],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    ).stdout.strip()


def test_ignored_working_files_cannot_change_a_pinned_export(
    publication: tuple[Path, Path, str],
) -> None:
    consumer, publisher, revision = publication
    runtime = publisher / "plugins/agent/.agents/agent/runtime"
    (publisher / ".git/info/exclude").write_text(
        "unpublished.py\n__pycache__/\n", encoding="utf-8"
    )
    (runtime / "unpublished.py").write_text("VALUE = 99\n", encoding="utf-8")
    cache = runtime / "__pycache__/guard.cpython-312.pyc"
    cache.parent.mkdir()
    cache.write_bytes(b"ordinary generated cache")
    assert publisher_git(publisher, "status", "--porcelain") == ""
    sources = runtime_sources()
    assert sources.stage(consumer, {"agent": publisher})[0]["revision"] == revision
    staged = consumer / ".agents/dependencies/agent/.agents/agent/runtime"
    assert (staged / "guard.py").read_text(encoding="utf-8") == "VALUE = 42\n"
    assert not (staged / "unpublished.py").exists()
    assert not (staged / "__pycache__").exists()
    assert sources.stage(consumer, {}, check=True)[0]["revision"] == revision


def test_replacement_refs_cannot_supply_the_pinned_publication(
    publication: tuple[Path, Path, str],
) -> None:
    consumer, publisher, revision = publication
    guard = publisher / "plugins/agent/.agents/agent/runtime/guard.py"
    guard.write_text("VALUE = 99\n", encoding="utf-8")
    publisher_git(publisher, "add", ".")
    publisher_git(
        publisher,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "Replacement fixture",
    )
    replacement = publisher_git(publisher, "rev-parse", "HEAD")
    publisher_git(publisher, "reset", "--hard", revision)
    publisher_git(publisher, "replace", revision, replacement)
    sources = runtime_sources()
    sources.stage(consumer, {"agent": publisher})
    staged = consumer / ".agents/dependencies/agent/.agents/agent/runtime/guard.py"
    assert staged.read_text(encoding="utf-8") == "VALUE = 42\n"
    assert sources.stage(consumer, {}, check=True)[0]["revision"] == revision
    publisher_git(publisher, "reset", "--hard", "HEAD")
    assert guard.read_text(encoding="utf-8") == "VALUE = 99\n"
    assert publisher_git(publisher, "status", "--porcelain") == ""
    with pytest.raises(ValueError, match="declared immutable"):
        sources.stage(consumer, {"agent": publisher})
    assert publisher_git(publisher, "replace", "-l") == revision


@pytest.mark.parametrize("name", ["link.py", "__pycache__/guard.cpython-312.pyc"])
def test_pinned_git_links_are_rejected_before_cache_exclusion(
    publication: tuple[Path, Path, str], name: str
) -> None:
    _consumer, publisher, revision = publication
    object_id = publisher_git(
        publisher,
        "rev-parse",
        revision + ":plugins/agent/.agents/agent/runtime/guard.py",
    )
    publisher_git(
        publisher,
        "update-index",
        "--add",
        "--cacheinfo",
        "120000," + object_id + ",plugins/agent/.agents/agent/runtime/" + name,
    )
    tree = publisher_git(publisher, "write-tree")
    with pytest.raises(ValueError, match="link"):
        runtime_sources().pinned_contents(
            publisher,
            {"package": "plugins/agent", "exports": [".agents/agent/runtime"]},
            tree,
        )


@pytest.mark.parametrize(
    "relative", ["unpublished.py", "legacy.pyc", "__pycache__/legacy.pyc"]
)
def test_unexpected_staged_files_invalidate_the_receipt(
    publication: tuple[Path, Path, str], relative: str
) -> None:
    consumer, publisher, _revision = publication
    sources = runtime_sources()
    sources.stage(consumer, {"agent": publisher})
    target = consumer / ".agents/dependencies/agent/.agents/agent/runtime" / relative
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(b"unpublished")
    with pytest.raises(ValueError, match="Stale or modified"):
        sources.stage(consumer, {}, check=True)


def test_wrong_or_dirty_local_publication_cannot_satisfy_pin(
    publication: tuple[Path, Path, str],
) -> None:
    consumer, publisher, _revision = publication
    sources = runtime_sources()
    (publisher / "plugins/agent/.agents/agent/runtime/guard.py").write_text(
        "unpublished", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="declared immutable"):
        sources.stage(consumer, {"agent": publisher})


def test_receipt_revision_and_changed_export_are_checked_independently(
    publication: tuple[Path, Path, str],
) -> None:
    consumer, publisher, revision = publication
    sources = runtime_sources()
    sources.stage(consumer, {"agent": publisher})
    path = consumer / ".agents/dependencies/agent/source.json"
    receipt = json.loads(path.read_text())
    receipt["revision"] = "0" * 40
    path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="Stale or modified"):
        sources.stage(consumer, {}, check=True)
    receipt["revision"] = revision
    path.write_text(json.dumps(receipt), encoding="utf-8")
    (consumer / ".agents/dependencies/agent/.agents/agent/runtime/guard.py").write_text(
        "changed", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="Stale or modified"):
        sources.stage(consumer, {}, check=True)


def test_remote_export_fetches_exact_declared_revision(
    publication: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    consumer, publisher, revision = publication
    sources = runtime_sources()
    commands: list[tuple[str, ...]] = []

    def git(*arguments: str) -> str:
        commands.append(arguments)
        if arguments[0] == "init":
            shutil.copytree(publisher, Path(arguments[-1]))
        return revision if "rev-parse" in arguments else ""

    monkeypatch.setattr(sources, "git", git)
    sources.stage(consumer, {})
    fetch = next(command for command in commands if "fetch" in command)
    assert fetch[-1] == revision
    assert "main" not in fetch
    assert sources.stage(consumer, {}, check=True)[0]["revision"] == revision


@pytest.mark.parametrize("revision", ["main", "a" * 39, "A" * 40, None])
def test_invalid_declared_revision_is_rejected(
    publication: tuple[Path, Path, str], revision: object
) -> None:
    consumer, _publisher, _revision = publication
    path = consumer / ".agents/plugins/runtime-sources.json"
    document = json.loads(path.read_text())
    document["sources"]["agent"]["revision"] = revision
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="immutable runtime revision"):
        runtime_sources().declarations(consumer)
