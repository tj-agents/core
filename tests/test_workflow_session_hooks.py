import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("plugin", ["base", "workflow", "engineering", "docs"])
@pytest.mark.parametrize("host", ["claude", "codex"])
def test_packages_register_admission_before_base_tier_context(
    plugin: str, host: str
) -> None:
    manifest_root = ROOT / ".agents/plugins/manifests" / host
    manifest = json.loads(
        (manifest_root / f"{plugin}.json").read_text(encoding="utf-8")
    )
    assert manifest["hooks"] == f"./hooks/{host}.json"
    document = json.loads(
        (manifest_root / f"{plugin}-hooks.json").read_text(encoding="utf-8")
    )
    hooks = document["hooks"]
    assert set(hooks) == {"SessionStart", "UserPromptSubmit", "PreToolUse"}
    for event, groups in hooks.items():
        commands = [hook for group in groups for hook in group["hooks"]]
        assert "managed_admission.py" in json.dumps(commands[0])
        expected_tier_hooks = int(plugin == "base" and event != "UserPromptSubmit")
        assert len(commands) == 1 + expected_tier_hooks
        if expected_tier_hooks:
            assert "hooks/tier_gate.py" in json.dumps(commands[1])
