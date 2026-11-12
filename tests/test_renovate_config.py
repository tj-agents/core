import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RENOVATE_CONFIG = ROOT / ".github/renovate.json"
RUNTIME_SOURCES = ROOT / ".agents/plugins/runtime-sources.json"


def test_renovate_config_extends_the_organization_preset() -> None:
    config = json.loads(RENOVATE_CONFIG.read_text(encoding="utf-8"))
    assert config["extends"] == ["github>tj-agents/renovate-config"]
    assert config["customManagers"]
    assert config["packageRules"]


def test_renovate_custom_manager_is_grouped_and_requires_ci_full() -> None:
    config = json.loads(RENOVATE_CONFIG.read_text(encoding="utf-8"))
    rule = next(
        rule
        for rule in config["packageRules"]
        if "custom.regex" in rule["matchManagers"]
    )
    assert rule["groupName"] == "runtime sources"
    assert rule["labels"] == ["ci:full"]


def test_renovate_custom_manager_regex_matches_every_declared_runtime_source() -> None:
    config = json.loads(RENOVATE_CONFIG.read_text(encoding="utf-8"))
    manager = config["customManagers"][0]
    pattern = re.sub(r"\(\?<(\w+)>", r"(?P<\1>", manager["matchStrings"][0])
    sources = json.loads(RUNTIME_SOURCES.read_text(encoding="utf-8"))["sources"]
    text = RUNTIME_SOURCES.read_text(encoding="utf-8")
    matches = {
        match.group("depName"): match.group("currentDigest")
        for match in re.finditer(pattern, text)
    }
    assert set(matches) == set(sources)
    for name, source in sources.items():
        assert matches[name] == source["revision"]
