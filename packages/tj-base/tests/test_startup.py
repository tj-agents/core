import hashlib
import json
from pathlib import Path

import pytest
from tj_base import startup


@pytest.fixture
def environment(tmp_path: Path) -> dict[str, str]:
    return {
        "TJ_AGENTS_STARTUP_ACK_DIRECTORY": str(tmp_path),
        "TJ_AGENTS_STARTUP_ACK_TOKEN": "native-startup-" + "x" * 32,
        "TJ_AGENTS_STARTUP_REQUIRED_HOOKS": json.dumps(
            ["base@tj-agents", "agent@tj-agents"]
        ),
    }


@pytest.mark.parametrize(
    "participants",
    [("base@tj-agents", "agent@tj-agents"), ("agent@tj-agents", "base@tj-agents")],
)
def test_every_required_participant_must_finish(
    environment: dict[str, str], participants: tuple[str, str]
) -> None:
    startup.acknowledge(environment, participants[0], succeeded=True)
    assert startup.outcome(environment).state is startup.State.WAITING
    startup.acknowledge(environment, participants[1], succeeded=True)
    assert startup.outcome(environment).state is startup.State.CONFIRMED


def test_failure_overrides_an_existing_aggregate(environment: dict[str, str]) -> None:
    for identity in ("base@tj-agents", "agent@tj-agents"):
        startup.acknowledge(environment, identity, succeeded=True)
    startup.acknowledge(
        environment, "base@tj-agents", succeeded=False, detail="import failed"
    )
    result = startup.outcome(environment)
    assert result.state is startup.State.FAILED
    assert (
        result.detail is not None
        and "base@tj-agents" in result.detail
        and "import failed" in result.detail
    )


@pytest.mark.parametrize("contents", ["", "another-token"])
def test_receipt_contents_must_match_exact_token(
    environment: dict[str, str], contents: str
) -> None:
    selected = startup.request(environment)
    assert selected is not None
    startup.acknowledge(environment, "agent@tj-agents", succeeded=True)
    receipt = selected.directory / (
        selected.token + "." + hashlib.sha256(b"base@tj-agents").hexdigest()
    )
    receipt.write_text(contents, encoding="utf-8")
    (selected.directory / selected.token).write_text(selected.token, encoding="utf-8")
    assert startup.outcome(environment).state is startup.State.WAITING


@pytest.mark.parametrize(
    "roster",
    ["[]", "{}", "null", "not-json", '["base@tj-agents","base@tj-agents"]', "[true]"],
)
def test_invalid_roster_records_failure_without_success(
    environment: dict[str, str], roster: str
) -> None:
    environment["TJ_AGENTS_STARTUP_REQUIRED_HOOKS"] = roster
    with pytest.raises(startup.ProtocolError):
        startup.acknowledge(environment, "base@tj-agents", succeeded=True)
    directory = Path(environment["TJ_AGENTS_STARTUP_ACK_DIRECTORY"])
    token = environment["TJ_AGENTS_STARTUP_ACK_TOKEN"]
    assert (directory / (token + ".failed")).is_file()
    assert not (directory / token).exists()


def test_unmanaged_hook_has_no_filesystem_effect(tmp_path: Path) -> None:
    assert startup.request({}) is None
    startup.acknowledge({}, "base@tj-agents", succeeded=True)
    assert startup.outcome({}).state is startup.State.UNMANAGED
    assert list(tmp_path.iterdir()) == []


def test_unknown_participant_cannot_confirm_startup(
    environment: dict[str, str],
) -> None:
    startup.acknowledge(environment, "unselected@tj-agents", succeeded=True)
    assert startup.outcome(environment).state is startup.State.WAITING


def test_partial_environment_and_unsafe_token_are_refused(tmp_path: Path) -> None:
    with pytest.raises(startup.ProtocolError):
        startup.request({"TJ_AGENTS_STARTUP_ACK_DIRECTORY": str(tmp_path)})
    with pytest.raises(startup.ProtocolError):
        startup.request(
            {
                "TJ_AGENTS_STARTUP_ACK_DIRECTORY": str(tmp_path),
                "TJ_AGENTS_STARTUP_ACK_TOKEN": "../outside",
            }
        )
