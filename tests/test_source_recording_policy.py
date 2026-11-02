import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".agents" / "hooks"))
from problem_records import RecordError, operation_skill


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_target_policy_is_imported_without_selecting_the_observer(
    tmp_path: Path, host: str
) -> None:
    source = tmp_path / "source"
    observer = tmp_path / "employer"
    (source / ".agents").mkdir(parents=True)
    observer.mkdir()
    selection = {
        "schema_version": 1,
        "plugins": ["personal@tj-agents"],
        "marketplaces": {"tj-agents": {"repository": "tj-agents/marketplace"}},
    }
    (source / ".agents/plugins.json").write_text(
        json.dumps(selection), encoding="utf-8"
    )
    provider = tmp_path / "installed/github/create-work-item/SKILL.md"
    rules = tmp_path / "installed/personal/rules/SKILL.md"
    policy = rules.parent / "resources/work-items.md"
    policy.parent.mkdir(parents=True)
    policy.write_text("Source recording policy", encoding="utf-8")
    installed = {"github:create-work-item": provider, "personal:rules": rules}
    with (
        patch("problem_records.primary_checkout", return_value=source),
        patch(
            "problem_records.installed_skill",
            side_effect=lambda name, _, **kwargs: installed[name],
        ) as resolve,
    ):
        result = operation_skill(source, "create", host)
    assert result["provider"] == "github:work-item"
    assert result["operation"] == "github:create-work-item"
    assert result["policy"] == str(policy)
    assert resolve.call_args_list[-1].kwargs == {"policy_only": True}
    assert not list(observer.iterdir())


def test_explicit_neutral_provider_does_not_require_personal(tmp_path: Path) -> None:
    (tmp_path / ".problem-records.json").write_text(
        json.dumps({"schema_version": 1, "provider": "github:work-item"}),
        encoding="utf-8",
    )
    skill = tmp_path / "installed/SKILL.md"
    with (
        patch("problem_records.primary_checkout", return_value=tmp_path),
        patch("problem_records.installed_skill", return_value=skill) as resolve,
    ):
        result = operation_skill(tmp_path, "address", "codex")
    assert result["policy"] is None
    assert result["operation"] == "github:address-work-item"
    resolve.assert_called_once_with("github:address-work-item", "codex")


def test_selected_source_policy_missing_blocks_the_operation(tmp_path: Path) -> None:
    agents = tmp_path / ".agents"
    agents.mkdir()
    (agents / "plugins.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "plugins": ["personal@tj-agents"],
                "marketplaces": {"tj-agents": {"repository": "tj-agents/marketplace"}},
            }
        ),
        encoding="utf-8",
    )
    with (
        patch("problem_records.primary_checkout", return_value=tmp_path),
        patch("problem_records.installed_skill", return_value=tmp_path / "SKILL.md"),
        pytest.raises(RecordError, match="policy is unavailable"),
    ):
        operation_skill(tmp_path, "create", "codex")
