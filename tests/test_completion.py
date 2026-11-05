import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, cast
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".agents/workflows"))
SPEC = importlib.util.spec_from_file_location(
    "completion", ROOT / ".agents/workflows/completion.py"
)
assert SPEC is not None and SPEC.loader is not None
COMPLETION: Any = importlib.util.module_from_spec(SPEC)
sys.modules["completion"] = COMPLETION
SPEC.loader.exec_module(COMPLETION)
HEAD = "a" * 40


def goal() -> str:
    document = {
        "outcome": "The requested user-visible outcome is observed.",
        "acceptance": [
            {
                "id": "verified",
                "criterion": "The runtime gate rejects unsupported completion.",
                "evidence": [{"source": "focused test", "result": "passed"}],
                "owner": "delivery owner",
                "next_action": "None.",
            }
        ],
        "deliveries": [],
        "open_tasks": [],
    }
    return f"# Goal\n\n```completion\n{json.dumps(document)}\n```\n"


@pytest.fixture
def state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    value = tmp_path / "state"
    monkeypatch.setenv("AGENT_STATE_DIRECTORY", str(value))
    return value


def terminal_files(
    tmp_path: Path, aggregate: dict[str, Any] | None = None
) -> tuple[Path, Path, Path, Path]:
    root = tmp_path / "terminal"
    root.mkdir()
    goal_path = root / "GOAL.md"
    goal_path.write_text(goal(), encoding="utf-8")
    aggregate_path = root / "aggregate.json"
    aggregate_path.write_text(
        json.dumps(
            aggregate
            or {
                "known": True,
                "owned": [],
                "responsibilities": [],
                "children": [],
                "waits": [],
            }
        ),
        encoding="utf-8",
    )
    artifact = root / "evidence.txt"
    artifact.write_text("passed\n", encoding="utf-8")
    return root, goal_path, aggregate_path, artifact


def accept(path: Path, root: Path) -> dict[str, Any]:
    reserved, _ = COMPLETION.reserve_terminal_audit(path)
    bound = COMPLETION.bind_terminal_audit(
        path, reserved["audit"]["reservation_id"], "native-1"
    )
    result = root / "audit.json"
    result.write_text(
        json.dumps(
            {
                "candidate_id": bound["candidate_id"],
                "reservation_id": bound["audit"]["reservation_id"],
                "native_child_id": bound["audit"]["native_child_id"],
                "sources_sha256": bound["audit"]["sources_sha256"],
                "state": "passed",
                "findings": [],
            }
        ),
        encoding="utf-8",
    )
    COMPLETION.record_terminal_audit(path, bound["audit"]["reservation_id"], result)
    return cast(dict[str, Any], COMPLETION.recheck_terminal_acceptance(path))


def test_workflow_package_invokes_completion_without_an_author_checkout(
    tmp_path: Path,
) -> None:
    mappings = json.loads(
        (ROOT / ".agents/plugins/sources.json").read_text(encoding="utf-8")
    )["resources"]
    mapping = next(
        item
        for item in mappings
        if item["plugin"] == "workflow" and item["destination"] == "workflows"
    )
    root = tmp_path / "package"
    root.mkdir()
    for filename in ("completion.py", "pr_body.py"):
        relative = Path(mapping["destination"]) / filename
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        packaged = ROOT / "plugins/workflow" / relative
        assert (
            ROOT / mapping["source"] / filename
        ).read_bytes() == packaged.read_bytes()
        shutil.copyfile(packaged, destination)
    goal_path = root / "GOAL.md"
    goal_path.write_text(goal(), encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "-E",
            "-s",
            "-B",
            str(root / "workflows/completion.py"),
            "--goal",
            str(goal_path),
            "--root",
            str(root),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["ready"]


def test_terminal_acceptance_requires_a_bound_passing_audit_then_rechecks(
    tmp_path: Path, state: Path
) -> None:
    root, goal_path, aggregate_path, artifact = terminal_files(tmp_path)
    receipt_path, receipt = COMPLETION.prepare_terminal_acceptance(
        goal_path,
        aggregate_path,
        {"host": "codex", "session_id": "s1"},
        root,
        [artifact],
        None,
    )
    assert receipt["state"] == "candidate"
    assert receipt["audit"]["state"] == "required"
    assert len(receipt["sources"]) == 3
    early = COMPLETION.recheck_terminal_acceptance(receipt_path)
    assert early["deterministic"]["blockers"] == []
    assert "native audit is not accepted" in early["audit"]["blockers"]
    repeated_path, _ = COMPLETION.prepare_terminal_acceptance(
        goal_path,
        aggregate_path,
        {"host": "codex", "session_id": "s1"},
        root,
        [artifact],
        None,
    )
    assert receipt_path == repeated_path
    accepted = accept(receipt_path, root)
    accepted_again = COMPLETION.recheck_terminal_acceptance(receipt_path)
    reused, dispatch = COMPLETION.reserve_terminal_audit(receipt_path)
    assert accepted["state"] == "accepted"
    assert accepted["audit"]["state"] == "passed"
    assert accepted_again["state"] == "accepted"
    assert not dispatch
    assert reused["audit"]["state"] == "passed"


def test_terminal_acceptance_binds_main_follow_up_to_the_audited_goal(
    tmp_path: Path, state: Path
) -> None:
    root, goal_path, aggregate_path, artifact = terminal_files(tmp_path)
    _, document = COMPLETION.completion_document(goal_path)
    document["follow_up"] = [
        {
            "repository": "example/publisher",
            "pr": 9,
            "head": HEAD,
            "text": "Publish the independent next version.",
            "owner": "publisher owner",
            "next_action": "Continue in the publisher work item.",
            "scope_evidence": "The requested delivery is complete at its recorded pin.",
        }
    ]
    goal_path.write_text(
        f"# Goal\n\n```completion\n{json.dumps(document)}\n```\n", encoding="utf-8"
    )
    receipt_path, _ = COMPLETION.prepare_terminal_acceptance(
        goal_path,
        aggregate_path,
        {"host": "codex", "session_id": "s1"},
        root,
        [artifact],
    )
    assert accept(receipt_path, root)["state"] == "accepted"
    goal_path.write_text(goal(), encoding="utf-8")
    assert COMPLETION.recheck_terminal_acceptance(receipt_path)["state"] == "candidate"


def test_terminal_acceptance_rejects_changed_sources_after_audit(
    tmp_path: Path, state: Path
) -> None:
    root, goal_path, aggregate_path, artifact = terminal_files(tmp_path)
    receipt_path, _ = COMPLETION.prepare_terminal_acceptance(
        goal_path,
        aggregate_path,
        {"host": "codex", "session_id": "s1"},
        root,
        [artifact],
        None,
    )
    accept(receipt_path, root)
    artifact.write_text("changed\n", encoding="utf-8")
    rechecked = COMPLETION.recheck_terminal_acceptance(receipt_path)
    assert rechecked["state"] == "candidate"
    assert rechecked["audit"]["state"] == "failed"
    assert (
        "frozen terminal acceptance sources changed"
        in rechecked["deterministic"]["blockers"]
    )


def test_terminal_acceptance_fails_closed_for_unknown_aggregate_or_unbound_reservation(
    tmp_path: Path, state: Path
) -> None:
    root, goal_path, aggregate_path, artifact = terminal_files(
        tmp_path,
        {
            "known": False,
            "owned": [],
            "responsibilities": [],
            "children": [],
            "waits": [],
        },
    )
    receipt_path, receipt = COMPLETION.prepare_terminal_acceptance(
        goal_path,
        aggregate_path,
        {"host": "codex", "session_id": "s1"},
        root,
        [artifact],
        None,
    )
    assert (
        "aggregate responsibility inventory is unknown"
        in receipt["deterministic"]["blockers"]
    )
    with pytest.raises(COMPLETION.CompletionError, match="deterministic blockers"):
        COMPLETION.reserve_terminal_audit(receipt_path)
    assert receipt["audit"]["state"] == "required"


def test_terminal_acceptance_marks_an_unbound_audit_reservation_unknown(
    tmp_path: Path, state: Path
) -> None:
    root, goal_path, aggregate_path, artifact = terminal_files(tmp_path)
    receipt_path, _ = COMPLETION.prepare_terminal_acceptance(
        goal_path,
        aggregate_path,
        {"host": "codex", "session_id": "s1"},
        root,
        [artifact],
        None,
    )
    reserved, _ = COMPLETION.reserve_terminal_audit(receipt_path)
    rechecked = COMPLETION.recheck_terminal_acceptance(receipt_path)
    with pytest.raises(COMPLETION.CompletionError):
        COMPLETION.bind_terminal_audit(
            receipt_path, reserved["audit"]["reservation_id"], "native-1"
        )
    bound = COMPLETION.bind_terminal_audit(
        receipt_path, reserved["audit"]["reservation_id"], "native-1", reconciled=True
    )
    assert reserved["audit"]["state"] == "reserved"
    assert rechecked["audit"]["state"] == "unknown"
    assert (
        "native audit reservation has no bound child" in rechecked["audit"]["blockers"]
    )
    assert bound["audit"]["state"] == "bound"


def test_audit_reservation_refreshes_transient_deterministic_blockers(
    tmp_path: Path, state: Path
) -> None:
    root, goal_path, aggregate_path, artifact = terminal_files(tmp_path)
    with mock.patch.object(
        COMPLETION, "terminal_check", return_value=(["forge unavailable"], None)
    ):
        path, receipt = COMPLETION.prepare_terminal_acceptance(
            goal_path,
            aggregate_path,
            {"host": "codex", "session_id": "s1"},
            root,
            [artifact],
        )
    assert receipt["deterministic"]["blockers"] == ["forge unavailable"]
    refreshed, dispatch = COMPLETION.reserve_terminal_audit(path)
    assert dispatch
    assert refreshed["deterministic"]["blockers"] == []
    COMPLETION.recheck_terminal_acceptance(path)
    repeated, dispatch = COMPLETION.reserve_terminal_audit(path)
    assert not dispatch
    assert repeated["audit"]["state"] == "unknown"
    assert refreshed["audit"]["reservation_id"] == repeated["audit"]["reservation_id"]


def test_only_the_first_reservation_can_dispatch_a_native_audit(
    tmp_path: Path, state: Path
) -> None:
    root, goal_path, aggregate_path, artifact = terminal_files(tmp_path)
    path, _ = COMPLETION.prepare_terminal_acceptance(
        goal_path,
        aggregate_path,
        {"host": "codex", "session_id": "s1"},
        root,
        [artifact],
    )
    first, dispatch_first = COMPLETION.reserve_terminal_audit(path)
    repeated, dispatch_again = COMPLETION.reserve_terminal_audit(path)
    assert dispatch_first
    assert not dispatch_again
    assert first["audit"]["reservation_id"] == repeated["audit"]["reservation_id"]


def test_a_concurrent_receipt_writer_cannot_reserve_an_audit(
    tmp_path: Path, state: Path
) -> None:
    root, goal_path, aggregate_path, artifact = terminal_files(tmp_path)
    path, _ = COMPLETION.prepare_terminal_acceptance(
        goal_path,
        aggregate_path,
        {"host": "codex", "session_id": "s1"},
        root,
        [artifact],
    )
    with (
        COMPLETION.receipt_lock(path),
        pytest.raises(
            COMPLETION.CompletionError, match="another terminal receipt operation"
        ),
    ):
        COMPLETION.reserve_terminal_audit(path)
    _, dispatch = COMPLETION.reserve_terminal_audit(path)
    assert dispatch


def test_retired_goal_reuses_the_accepted_audit_and_preserves_evidence(
    tmp_path: Path, state: Path
) -> None:
    root, goal_path, aggregate_path, artifact = terminal_files(tmp_path)
    path, _ = COMPLETION.prepare_terminal_acceptance(
        goal_path,
        aggregate_path,
        {"host": "codex", "session_id": "s1"},
        root,
        [artifact],
    )
    with pytest.raises(COMPLETION.CompletionError, match="only an accepted goal"):
        COMPLETION.retire_terminal_goal(path)
    accepted = accept(path, root)
    retired = COMPLETION.retire_terminal_goal(path)
    assert goal_path.exists()
    assert retired["checkpoint"]["retired_sources"] == [str(goal_path.resolve())]
    for snapshot in retired["checkpoint"]["sources"]:
        assert not Path(snapshot["path"]).is_relative_to(root)
        assert Path(snapshot["path"]).is_file()
    goal_path.unlink()
    (root / "audit.json").unlink()
    rechecked = COMPLETION.recheck_terminal_acceptance(path)
    assert rechecked["state"] == "accepted"
    assert accepted["audit"] == rechecked["audit"]
    assert not COMPLETION.reserve_terminal_audit(path)[1]
    Path(retired["checkpoint"]["sources"][0]["path"]).write_text(
        "changed", encoding="utf-8"
    )
    assert COMPLETION.recheck_terminal_acceptance(path)["state"] == "candidate"


def test_plan_and_ledger_retirement_preserves_only_explicitly_eligible_sources(
    tmp_path: Path, state: Path
) -> None:
    root, ledger, aggregate, evidence = terminal_files(tmp_path)
    plan = root / "PLAN.md"
    plan.write_text("# Completed plan\n", encoding="utf-8")
    path, _ = COMPLETION.prepare_terminal_acceptance(
        ledger, aggregate, {"host": "codex", "session_id": "s1"}, root, [plan, evidence]
    )
    accepted = accept(path, root)
    for ineligible in (aggregate, root / "undeclared.md"):
        with pytest.raises(COMPLETION.CompletionError, match="explicitly declared"):
            COMPLETION.retire_terminal_goal(path, [ineligible])
    retired = COMPLETION.retire_terminal_goal(path, [plan])
    assert retired["checkpoint"]["retired_sources"] == sorted(
        [str(ledger.resolve()), str(plan.resolve())]
    )
    ledger.unlink()
    plan.unlink()
    rechecked = COMPLETION.recheck_terminal_acceptance(path)
    assert rechecked["state"] == "accepted"
    assert accepted["audit"] == rechecked["audit"]
    assert not COMPLETION.reserve_terminal_audit(path)[1]
    plan.write_text("changed plan", encoding="utf-8")
    assert COMPLETION.recheck_terminal_acceptance(path)["state"] == "candidate"
    plan.unlink()
    evidence.unlink()
    assert COMPLETION.recheck_terminal_acceptance(path)["state"] == "candidate"
    evidence.write_text("passed\n", encoding="utf-8")
    aggregate.unlink()
    assert COMPLETION.recheck_terminal_acceptance(path)["state"] == "candidate"


def test_retirement_rejects_a_changed_companion_before_deletion(
    tmp_path: Path, state: Path
) -> None:
    root, ledger, aggregate, plan = terminal_files(tmp_path)
    path, receipt = COMPLETION.prepare_terminal_acceptance(
        ledger, aggregate, {"host": "codex", "session_id": "s1"}, root, [plan]
    )
    receipt["state"] = "accepted"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    plan.write_text("changed", encoding="utf-8")
    with pytest.raises(COMPLETION.CompletionError, match="sources changed"):
        COMPLETION.retire_terminal_goal(path, [plan])


def test_audit_from_another_native_child_cannot_accept_the_candidate(
    tmp_path: Path, state: Path
) -> None:
    root, goal_path, aggregate_path, artifact = terminal_files(tmp_path)
    path, _ = COMPLETION.prepare_terminal_acceptance(
        goal_path,
        aggregate_path,
        {"host": "codex", "session_id": "s1"},
        root,
        [artifact],
    )
    reserved, _ = COMPLETION.reserve_terminal_audit(path)
    bound = COMPLETION.bind_terminal_audit(
        path, reserved["audit"]["reservation_id"], "native-1"
    )
    result = root / "audit.json"
    result.write_text(
        json.dumps(
            {
                "candidate_id": bound["candidate_id"],
                "reservation_id": bound["audit"]["reservation_id"],
                "native_child_id": "other-native-child",
                "sources_sha256": bound["audit"]["sources_sha256"],
                "state": "passed",
                "findings": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(COMPLETION.CompletionError, match="reserved child"):
        COMPLETION.record_terminal_audit(path, bound["audit"]["reservation_id"], result)
    assert COMPLETION.recheck_terminal_acceptance(path)["state"] == "candidate"


def test_terminal_acceptance_keeps_cleanup_separate_from_acceptance(
    tmp_path: Path, state: Path
) -> None:
    root, goal_path, aggregate_path, artifact = terminal_files(tmp_path)
    obligations = state / "merge-cleanup" / "targeted-obligations"
    obligations.mkdir(parents=True)
    cleanup = obligations / "pending.json"
    cleanup.write_text(
        json.dumps(
            {
                "kind": "targeted-cleanup",
                "obligation_id": "cleanup-1",
                "state": "pending",
                "owner": {"host": "codex", "session_id": "s1"},
                "worktree": str(root),
            }
        ),
        encoding="utf-8",
    )
    receipt_path, _ = COMPLETION.prepare_terminal_acceptance(
        goal_path,
        aggregate_path,
        {"host": "codex", "session_id": "s1"},
        root,
        [artifact],
        None,
        cleanup,
    )
    accepted = accept(receipt_path, root)
    assert accepted["state"] == "accepted"
    assert accepted["cleanup"]["state"] == "pending"
