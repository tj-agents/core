import importlib.util
import json
import os
import queue
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/native_host_acceptance.py"
specification = importlib.util.spec_from_file_location("native_host_acceptance", SCRIPT)
assert specification is not None and specification.loader is not None
NATIVE = importlib.util.module_from_spec(specification)
specification.loader.exec_module(NATIVE)


def test_fixture_selects_required_packages_without_personal(tmp_path: Path) -> None:
    NATIVE.write_fixture(tmp_path)
    value = json.loads((tmp_path / ".agents/plugins.json").read_text(encoding="utf-8"))
    assert value["plugins"] == list(NATIVE.IDENTITIES)
    assert "personal@tj-agents" not in value["plugins"]


def test_claude_plugin_inventory_requires_listed_enabled_identities() -> None:
    completed = SimpleNamespace(
        stdout=json.dumps(
            [{"id": identity, "enabled": True} for identity in NATIVE.IDENTITIES]
        )
    )
    NATIVE.require_plugins(NATIVE.claude_plugin_inventory(completed))
    completed = SimpleNamespace(stdout=json.dumps({"installed": []}))
    with pytest.raises(NATIVE.AcceptanceError, match="did not return a list"):
        NATIVE.claude_plugin_inventory(completed)


def test_plugin_discovery_requires_enabled_installed_identities() -> None:
    inventory = {
        "installed": [
            {"pluginId": identity, "installed": True, "enabled": True}
            for identity in NATIVE.IDENTITIES
        ]
    }
    NATIVE.require_plugins(inventory)
    inventory["installed"][-1]["enabled"] = False
    with pytest.raises(NATIVE.AcceptanceError, match="engineering@tj-agents"):
        NATIVE.require_plugins(inventory)


def test_tier_context_requires_the_probe_in_actual_host_evidence() -> None:
    NATIVE.require_context(
        "prefix " + NATIVE.CONTEXT_PROBE, NATIVE.CONTEXT_PROBE, "host"
    )
    with pytest.raises(NATIVE.AcceptanceError, match="did not include"):
        NATIVE.require_context(
            "base:task-routing old-policy-hash", NATIVE.CONTEXT_PROBE, "host"
        )


@pytest.mark.parametrize("error", [None, {"message": "500 Server Error"}])
def test_transcript_rejects_an_unexpected_completion(
    tmp_path: Path, error: object
) -> None:
    transcript = tmp_path / "session.jsonl"
    transcript.write_text(
        json.dumps(
            {"type": "response_item", "payload": {"content": NATIVE.CONTEXT_PROBE}}
        )
        + "\n"
        + json.dumps(
            {"type": "event_msg", "payload": {"type": "task_complete", "error": error}}
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(NATIVE.AcceptanceError, match="expected unauthenticated 401"):
        NATIVE.require_failed_turn(transcript, NATIVE.CONTEXT_PROBE, 0.1)


def test_transcript_requires_tier_context_and_unauthenticated_completion(
    tmp_path: Path,
) -> None:
    transcript = tmp_path / "session.jsonl"
    completion = (
        json.dumps(
            {
                "type": "event_msg",
                "payload": {
                    "type": "task_complete",
                    "error": {"message": "401 Unauthorized"},
                },
            }
        )
        + "\n"
    )
    transcript.write_text(completion, encoding="utf-8")
    with pytest.raises(NATIVE.AcceptanceError, match="expected tier context"):
        NATIVE.require_failed_turn(transcript, NATIVE.CONTEXT_PROBE, 0.01)
    transcript.write_text(
        json.dumps(
            {"type": "response_item", "payload": {"content": NATIVE.CONTEXT_PROBE}}
        )
        + "\n"
        + completion,
        encoding="utf-8",
    )
    NATIVE.require_failed_turn(transcript, NATIVE.CONTEXT_PROBE, 0.1)


def test_transcript_waits_for_initial_appearance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    entries = [
        {"type": "response_item", "payload": {"content": NATIVE.CONTEXT_PROBE}},
        {
            "type": "event_msg",
            "payload": {
                "type": "task_complete",
                "error": {"message": "401 Unauthorized"},
            },
        },
    ]
    reads = iter([None, entries])
    monkeypatch.setattr(NATIVE, "transcript_entries", lambda _path: next(reads))
    NATIVE.require_failed_turn(tmp_path / "session.jsonl", NATIVE.CONTEXT_PROBE, 0.2)


def test_native_fixture_changes_declaration_without_changing_candidate_code(
    tmp_path: Path,
) -> None:
    original = (ROOT / "plugins/base/tier.json").read_bytes()
    contextual = NATIVE.context_marketplace(ROOT, ROOT, tmp_path / "context")
    declaration = json.loads(
        (contextual / "plugins/base/tier.json").read_text(encoding="utf-8")
    )
    assert declaration["schema_version"] == 3
    assert declaration["session_context"] == NATIVE.CONTEXT_PROBE
    assert (ROOT / "plugins/base/tier.json").read_bytes() == original
    assert (contextual / "plugins/base/hooks/tier_gate.py").read_bytes() == (
        ROOT / "plugins/base/hooks/tier_gate.py"
    ).read_bytes()
    failed = NATIVE.failure_marketplace(ROOT, contextual, tmp_path / "failure")
    failure_evidence = tmp_path / "failure.txt"
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(failed / "plugins/base/hooks/tier_gate.py"),
            "--session-context",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
        check=False,
        env={**os.environ, "TJ_NATIVE_GATE_FAILURE_EVIDENCE": str(failure_evidence)},
    )
    assert result.returncode == 0
    assert "tier gate failed: " + NATIVE.FAILURE_PROBE in result.stderr
    assert result.stdout == ""
    NATIVE.require_failure_evidence(failure_evidence)


def test_failure_probe_cannot_claim_an_unrelated_startup_error() -> None:
    with pytest.raises(NATIVE.AcceptanceError, match="did not include"):
        NATIVE.require_context(
            "unrelated startup failure", NATIVE.FAILURE_PROBE, "hook"
        )


def test_claude_initialize_requires_qualified_command_inventory() -> None:
    NATIVE.require_claude_discovery(
        {
            "commands": [
                {"name": "workflow:run"},
                {"name": "engineering:commit"},
            ]
        }
    )
    with pytest.raises(NATIVE.AcceptanceError, match="workflow:run"):
        NATIVE.require_claude_discovery(
            {"commands": [{"name": "run"}, {"name": "engineering:commit"}]}
        )


def test_discovery_rejects_substrings_without_exact_skill_names() -> None:
    with pytest.raises(NATIVE.AcceptanceError, match="workflow skill"):
        NATIVE.require_discovery(
            {"description": "workflow run engineering commit"}, "native"
        )
    with pytest.raises(NATIVE.AcceptanceError, match="workflow skill"):
        NATIVE.require_discovery(
            {"commands": [{"name": "run"}, {"name": "commit"}]}, "native"
        )
    NATIVE.require_discovery(
        {
            "commands": [
                {"name": "run", "pluginId": "workflow@tj-agents"},
                {
                    "name": "commit",
                    "path": "/cache/plugins/engineering/skills/commit/SKILL.md",
                },
            ]
        },
        "native",
    )


def test_restarted_startup_hooks_require_trusted_current_hashes() -> None:
    hooks = {
        "data": [
            {
                "hooks": [
                    {
                        "pluginId": "base@tj-agents",
                        "source": "plugin",
                        "enabled": True,
                        "key": "base",
                        "trustStatus": "trusted",
                        "currentHash": "sha256:base",
                        "trustedHash": "sha256:base",
                    }
                ]
            }
        ]
    }
    trusted = {"base": {"trusted_hash": "sha256:base"}}
    NATIVE.require_startup_hooks(hooks, trusted=True, trusted_hashes=trusted)
    trusted["base"]["trusted_hash"] = "sha256:stale"
    with pytest.raises(NATIVE.AcceptanceError, match="did not trust"):
        NATIVE.require_startup_hooks(hooks, trusted=True, trusted_hashes=trusted)


def test_isolated_environment_precedes_direct_native_directories(
    tmp_path: Path,
) -> None:
    codex = tmp_path / "codex/codex"
    claude = tmp_path / "claude/claude"
    codex.parent.mkdir()
    claude.parent.mkdir()
    codex.write_text("", encoding="utf-8")
    claude.write_text("", encoding="utf-8")
    environment = NATIVE.isolated_environment(
        tmp_path / "temporary", codex, claude, "http://127.0.0.1:1/v1"
    )
    assert environment["PATH"].split(os.pathsep)[:2] == [
        str(codex.resolve().parent),
        str(claude.resolve().parent),
    ]
    assert Path(environment["HOME"]) == tmp_path / "temporary/home"
    assert Path(environment["USERPROFILE"]) == tmp_path / "temporary/home"
    for key in ("CODEX_HOME", "CLAUDE_CONFIG_DIR", "AGENT_STATE_DIRECTORY"):
        assert Path(environment[key]).is_dir()
    config = (Path(environment["CODEX_HOME"]) / "config.toml").read_text(
        encoding="utf-8"
    )
    assert 'cli_auth_credentials_store = "file"' in config
    assert "hooks = true" in config


@pytest.mark.parametrize("status", ["failed", "blocked", "stopped"])
def test_native_hook_failure_is_rejected(status: str) -> None:
    with pytest.raises(NATIVE.AcceptanceError, match="did not complete"):
        NATIVE.require_hook_completion(
            [
                {
                    "method": "hook/completed",
                    "params": {
                        "run": {
                            "eventName": "sessionStart",
                            "source": "plugin",
                            "sourcePath": "/cache/base/local/hooks/codex.json",
                            "status": status,
                        }
                    },
                }
            ]
        )


def test_native_startup_requires_completed_base_hook() -> None:
    with pytest.raises(NATIVE.AcceptanceError, match="did not complete"):
        NATIVE.require_hook_completion([])
    NATIVE.require_hook_completion(
        [
            {
                "method": "hook/completed",
                "params": {
                    "run": {
                        "eventName": "sessionStart",
                        "source": "plugin",
                        "sourcePath": "/cache/base/local/hooks/codex.json",
                        "status": "completed",
                    }
                },
            }
        ]
    )


def test_fail_open_probe_requires_fresh_exact_diagnostic(tmp_path: Path) -> None:
    evidence = tmp_path / "failure.txt"
    with pytest.raises(NATIVE.AcceptanceError, match="no diagnostic evidence"):
        NATIVE.require_failure_evidence(evidence)
    evidence.write_text("unrelated failure", encoding="utf-8")
    with pytest.raises(NATIVE.AcceptanceError, match="unrelated error"):
        NATIVE.require_failure_evidence(evidence)


@pytest.mark.parametrize("host", ["codex", "claude"])
def test_previous_failure_marker_cannot_satisfy_current_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, host: str
) -> None:
    marketplace = tmp_path / "marketplace"
    (marketplace / "plugins").mkdir(parents=True)
    artifacts = tmp_path / "artifacts"
    for name in ("codex", "claude"):
        evidence = artifacts / ("failure-" + name) / "tier-gate-failure.txt"
        evidence.parent.mkdir(parents=True)
        evidence.write_text(NATIVE.FAILURE_PROBE, encoding="utf-8")

    def fixture(project: Path, _environment: dict) -> Path:
        project.mkdir(parents=True, exist_ok=True)
        return project

    def operation(*args: object, **kwargs: object) -> None:
        if kwargs.get("expected_context", True) is None:
            evidence = Path(args[5]) / "tier-gate-failure.txt"
            if evidence.parent.name != "failure-" + host:
                evidence.write_text(NATIVE.FAILURE_PROBE, encoding="utf-8")

    monkeypatch.setattr(NATIVE, "write_fixture", fixture)
    monkeypatch.setattr(NATIVE, "isolated_environment", lambda *args: {})
    monkeypatch.setattr(NATIVE, "context_marketplace", lambda *args: marketplace)
    monkeypatch.setattr(NATIVE, "failure_marketplace", lambda *args: marketplace)
    monkeypatch.setattr(NATIVE, "accept_codex", operation)
    monkeypatch.setattr(NATIVE, "accept_claude", operation)
    with pytest.raises(NATIVE.AcceptanceError, match="no diagnostic evidence"):
        NATIVE.accept(ROOT, marketplace, SCRIPT, SCRIPT, artifacts, 1)


def test_failure_diagnostics_drain_pending_hook_events_and_decode_errors() -> None:
    server = object.__new__(NATIVE.AppServer)
    server.messages = queue.Queue()
    server.notifications = []
    event = {"method": "hook/completed", "params": {"run": {"status": "failed"}}}
    server.messages.put(event)
    server.messages.put(ValueError("malformed hook response"))
    server.drain_notifications()
    assert server.notifications == [
        event,
        {"diagnosticError": "malformed hook response"},
    ]
    server.drain_notifications()
    assert len(server.notifications) == 2


def test_fixture_hashes_canonical_text_and_preserves_binary_members(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate"
    shutil.copytree(ROOT / "plugins/base", candidate / "plugins/base")
    for relative in (
        ".agents/plugins/marketplace.json",
        ".claude-plugin/marketplace.json",
    ):
        target = candidate / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    payload = candidate / "plugins/base/payload.txt"
    payload.write_bytes(b"first\r\nsecond\r\n")
    binary = b"\xff\x00\r\n"
    (candidate / "plugins/base/payload.bin").write_bytes(binary)
    fixture = NATIVE.fixture_marketplace(
        ROOT,
        candidate,
        tmp_path / "fixture",
        {"plugins/base/changed.txt": b"changed\r\ntext\r"},
    )
    package = fixture / "plugins/base"
    manifest = json.loads((package / "hooks/codex.json").read_text(encoding="utf-8"))
    command = manifest["hooks"]["SessionStart"][0]["hooks"][0]["commandWindows"]
    expected = re.findall(r"sha256:[a-f0-9]{64}", command)
    snapshot = NATIVE.load_module(
        "native_fixture_snapshot", ROOT / ".codex/hooks/snapshot.py"
    )
    assert expected == [snapshot.digest_tree(package)]
    assert (package / "payload.txt").read_bytes() == b"first\nsecond\n"
    assert (package / "changed.txt").read_bytes() == b"changed\ntext\n"
    assert (package / "payload.bin").read_bytes() == binary
