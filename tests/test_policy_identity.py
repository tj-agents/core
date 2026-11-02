import json
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".agents/hooks"))

import installed_skills
from problem_records import installed_skill


def plugin(
    root: Path, marketplace: str, version: str = "local"
) -> tuple[Path, dict[str, object]]:
    payload = root / "plugins/cache" / marketplace / "personal" / version
    skill = payload / "skills/rules/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\ndescription: Fixture policy\n---\n", encoding="utf-8")
    return skill, {
        "id": f"personal@{marketplace}",
        "enabled": False,
        "name": "personal",
        "marketplaceName": marketplace,
        "version": version,
        "installPath": str(payload),
    }


@contextmanager
def inventory(host: str, entries: list[dict[str, object]]) -> Iterator[None]:
    roster = {"installed": entries} if host == "codex" else entries
    installed_skills._native_install_roots.cache_clear()
    try:
        with (
            patch("installed_skills.shutil.which", return_value=host),
            patch(
                "installed_skills.plugin_inventory_command", return_value=([host], {})
            ),
            patch(
                "installed_skills.process.run",
                return_value=subprocess.CompletedProcess([], 0, json.dumps(roster), ""),
            ),
        ):
            yield
    finally:
        installed_skills._native_install_roots.cache_clear()


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_source_policy_ignores_foreign_marketplace_first(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, host: str
) -> None:
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    _, foreign = plugin(tmp_path, "foreign")
    expected, selected = plugin(tmp_path, "tj-agents")
    with inventory(host, [foreign, selected]):
        assert installed_skill("personal:rules", host, policy_only=True) == expected
        assert installed_skill("personal:rules", host) is None


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_foreign_policy_cannot_supply_source_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, host: str
) -> None:
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    _, foreign = plugin(tmp_path, "foreign")
    with inventory(host, [foreign]):
        assert installed_skill("personal:rules", host, policy_only=True) is None


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_ambiguous_native_policies_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, host: str
) -> None:
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    _, first = plugin(tmp_path, "tj-agents", "one")
    _, second = plugin(tmp_path, "tj-agents", "two")
    with inventory(host, [first, second]):
        assert installed_skill("personal:rules", host, policy_only=True) is None
