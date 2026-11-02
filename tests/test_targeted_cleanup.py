import importlib.util
import os
import sys
import tempfile
import types
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/engineering/workflow/merge/scripts"
SPEC = importlib.util.spec_from_file_location(
    "targeted_cleanup", SCRIPTS / "targeted_cleanup.py"
)
assert SPEC is not None and SPEC.loader is not None
TARGETED: Any = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TARGETED)


class SessionClose:
    __file__ = str(ROOT / "outside-session-close.py")

    def __init__(self) -> None:
        self.states: dict[tuple[int, float], str] = {}
        self.started = 10.0
        self.started_calls: list[Any] = []
        self.start_detached: Any = self._start_detached

    def process_info(self, pid: int) -> SimpleNamespace:
        return SimpleNamespace(pid=pid, started_at=self.started, name="python")

    def valid_identity(self, pid: int, started_at: float) -> bool:
        return pid > 0 and started_at > 0

    def identity_status(self, pid: int, started_at: float) -> str:
        return self.states.get((pid, started_at), "exited")

    def process_state(self, pid: int) -> tuple[str, None]:
        return "absent", None

    def verified_live(self, pid: int, started_at: float) -> bool:
        return self.identity_status(pid, started_at) == "live"

    def under_or_equal(self, child: str | Path, parent: str | Path) -> bool:
        child_path = Path(child).resolve()
        parent_path = Path(parent).resolve()
        return child_path == parent_path or parent_path in child_path.parents

    def _start_detached(
        self, script: str | Path, arguments: list[Any], extra: tuple[Any, ...] = ()
    ) -> None:
        self.started_calls.append((Path(script), list(arguments), list(extra)))


class CleanupCase:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.primary = root / "primary"
        self.worktree = root / "worktree"
        self.primary.mkdir()
        self.worktree.mkdir()
        self.session_close = SessionClose()

    def holder(self, pid: int = 91, started_at: float = 20.0) -> dict[str, Any]:
        return {"pid": pid, "started_at": started_at}

    def prepare(
        self,
        holders: list[dict[str, float | int]] | None = None,
        retained: bool = False,
    ) -> tuple[Path, dict[str, Any]]:
        return cast(
            tuple[Path, dict[str, Any]],
            TARGETED.prepare(
                self.primary,
                self.worktree,
                "Fix/Target",
                "a" * 40,
                42,
                "example/test",
                {"host": "codex", "session_id": "s1"},
                [self.holder()] if holders is None else holders,
                retained,
            ),
        )

    def prepare_next_delivery(self) -> tuple[Path, dict[str, Any]]:
        return cast(
            tuple[Path, dict[str, Any]],
            TARGETED.prepare(
                self.primary,
                self.worktree,
                "Fix/Next",
                "b" * 40,
                43,
                "example/test",
                {"host": "codex", "session_id": "s2"},
                [],
                session_close_path="declared-helper.py",
            ),
        )

    def arm(self, path: Path) -> dict[str, Any]:
        obligation = TARGETED.load(path)
        obligation["launch"] = {
            "token": obligation["launch_token"],
            "launcher": {"pid": 71, "started_at": 30.0},
        }
        return cast(dict[str, Any], TARGETED.save(path, obligation))

    def run_worker(self, path: Path, **kwargs: Any) -> dict[str, Any]:
        self.arm(path)
        token = TARGETED.load(path)["launch_token"]
        return cast(dict[str, Any], TARGETED.run(path, launch_token=token, **kwargs))

    def acknowledge_worker(
        self, path: Path, started_at: float | None = None
    ) -> dict[str, Any]:
        value = self.session_close.started if started_at is None else started_at
        obligation = TARGETED.load(path)
        obligation["worker"] = {"pid": os.getpid(), "started_at": value}
        self.session_close.states[(os.getpid(), value)] = "live"
        return cast(dict[str, Any], TARGETED.save(path, obligation, "running", None))


@pytest.fixture
def cleanup(monkeypatch: pytest.MonkeyPatch) -> Iterator[CleanupCase]:
    with tempfile.TemporaryDirectory() as directory:
        case = CleanupCase(Path(directory))
        monkeypatch.setenv("AGENT_STATE_DIRECTORY", str(case.root / "state"))
        with mock.patch.object(
            TARGETED, "process_info", side_effect=case.session_close.process_info
        ):
            yield case


def test_repeat_prepare_reuses_existing_obligation_and_launch_token(
    cleanup: CleanupCase,
) -> None:
    path, first = cleanup.prepare()
    repeated_path, second = cleanup.prepare()
    assert path == repeated_path
    assert first["obligation_id"] == second["obligation_id"]
    assert first["launch_token"] == second["launch_token"]


def test_later_delivery_preserves_a_retained_terminal_obligation(
    cleanup: CleanupCase,
) -> None:
    path, original = cleanup.prepare(retained=True)
    next_path, next_obligation = cleanup.prepare_next_delivery()
    assert path != next_path
    assert original == TARGETED.load(path)
    assert original == TARGETED.load(TARGETED.receipt_path(original))
    assert next_obligation["state"] == "pending"
    with pytest.raises(TARGETED.CleanupError, match="unresolved obligation"):
        TARGETED.prepare(
            cleanup.primary,
            cleanup.worktree,
            "Fix/Third",
            "c" * 40,
            44,
            "example/test",
            {"host": "codex", "session_id": "s3"},
        )


def test_later_delivery_reconciles_the_exited_verified_worker(
    cleanup: CleanupCase,
) -> None:
    path, _ = cleanup.prepare()
    cleanup.arm(path)
    original = TARGETED.save(path, cleanup.acknowledge_worker(path), "verified", None)
    cleanup.session_close.states[
        (original["worker"]["pid"], original["worker"]["started_at"])
    ] = "exited"
    with mock.patch.object(
        TARGETED, "load_session_close", return_value=cleanup.session_close
    ) as loader:
        next_path, next_obligation = cleanup.prepare_next_delivery()
    loader.assert_called_once_with("declared-helper.py")
    assert path != next_path
    assert original == TARGETED.load(path)
    assert original == TARGETED.load(TARGETED.receipt_path(original))
    assert next_obligation["state"] == "pending"


def test_later_delivery_never_replaces_an_unresolved_or_unsafe_worker(
    cleanup: CleanupCase,
) -> None:
    path, original = cleanup.prepare()
    for state in ("pending", "running", "refused", "timed_out"):
        original = TARGETED.save(path, original, state, "fixture")
        with pytest.raises(TARGETED.CleanupError, match="unresolved obligation"):
            cleanup.prepare_next_delivery()
        assert original == TARGETED.load(path)
    cleanup.arm(path)
    original = cleanup.acknowledge_worker(path)
    for terminal in ("retained", "verified"):
        original = TARGETED.save(path, original, terminal, None)
        for worker_state in ("live", "unknown", "reused"):
            cleanup.session_close.states[
                (original["worker"]["pid"], original["worker"]["started_at"])
            ] = worker_state
            with (
                mock.patch.object(
                    TARGETED, "load_session_close", return_value=cleanup.session_close
                ),
                pytest.raises(TARGETED.CleanupError, match="not safely reconciled"),
            ):
                cleanup.prepare_next_delivery()
            assert original == TARGETED.load(path)
    original["worker"] = None
    TARGETED.save(path, original, "verified", None)
    with pytest.raises(TARGETED.CleanupError, match="no worker acknowledgement"):
        cleanup.prepare_next_delivery()


def test_fast_verified_worker_acknowledges_launch_after_exit(
    cleanup: CleanupCase,
) -> None:
    path, _ = cleanup.prepare()

    def finish(_script: Any, _arguments: Any, extra: tuple[Any, ...] = ()) -> None:
        obligation = cleanup.acknowledge_worker(path)
        cleanup.session_close.states[
            (obligation["worker"]["pid"], obligation["worker"]["started_at"])
        ] = "exited"
        TARGETED.save(path, obligation, "verified", None)

    cleanup.session_close.start_detached = finish
    with mock.patch.object(
        TARGETED, "load_session_close", return_value=cleanup.session_close
    ):
        result = TARGETED.launch(path, "ignored", acknowledgement_timeout=0.1)
    assert result["state"] == "verified"


@pytest.mark.parametrize("worker_state", ["exited", "unknown", "reused"])
def test_pending_worker_acknowledgement_requires_exact_live_start(
    cleanup: CleanupCase, worker_state: str
) -> None:
    path, _ = cleanup.prepare()
    cleanup.arm(path)
    obligation = cleanup.acknowledge_worker(path)
    cleanup.session_close.states[
        (obligation["worker"]["pid"], obligation["worker"]["started_at"])
    ] = worker_state
    with pytest.raises(TARGETED.CleanupError, match="did not acknowledge launch"):
        TARGETED.wait_for_worker(
            path,
            cleanup.session_close,
            obligation["launch_token"],
            obligation["identity_sha256"],
            0.01,
        )


@pytest.mark.parametrize("terminal", ["refused", "timed_out"])
def test_fast_worker_failure_is_reported_explicitly(
    cleanup: CleanupCase, terminal: str
) -> None:
    path, _ = cleanup.prepare()
    cleanup.arm(path)
    obligation = cleanup.acknowledge_worker(path)
    TARGETED.save(path, obligation, terminal, "fixture failure")
    with pytest.raises(
        TARGETED.CleanupError, match=f"ended with {terminal}: fixture failure"
    ):
        TARGETED.wait_for_worker(
            path,
            cleanup.session_close,
            obligation["launch_token"],
            obligation["identity_sha256"],
            0.1,
        )


@pytest.mark.parametrize(
    "token, identity, message",
    [
        ("wrong-token", "current", "launch token changed"),
        ("current", "0" * 64, "identity changed"),
    ],
)
def test_fast_success_refuses_a_different_token_or_immutable_identity(
    cleanup: CleanupCase, token: str, identity: str, message: str
) -> None:
    path, _ = cleanup.prepare()
    cleanup.arm(path)
    obligation = cleanup.acknowledge_worker(path)
    TARGETED.save(path, obligation, "verified", None)
    selected_token = obligation["launch_token"] if token == "current" else token
    selected_identity = (
        obligation["identity_sha256"] if identity == "current" else identity
    )
    with pytest.raises(TARGETED.CleanupError, match=message):
        TARGETED.wait_for_worker(
            path, cleanup.session_close, selected_token, selected_identity, 0.1
        )


def test_fast_success_receipt_requires_the_pinned_worker_and_launch(
    cleanup: CleanupCase,
) -> None:
    path, _ = cleanup.prepare()
    cleanup.arm(path)
    obligation = TARGETED.save(path, cleanup.acknowledge_worker(path), "verified", None)
    receipt = dict(obligation)
    receipt["worker"] = {"pid": 92, "started_at": 22.0}
    TARGETED.atomic_json(TARGETED.receipt_path(obligation), receipt)
    with pytest.raises(TARGETED.CleanupError, match="different worker ownership"):
        TARGETED.wait_for_worker(
            path,
            cleanup.session_close,
            obligation["launch_token"],
            obligation["identity_sha256"],
            0.1,
        )
    receipt = dict(obligation)
    receipt["launch_token"] = "other-launch-token"
    receipt["launch"] = {**receipt["launch"], "token": receipt["launch_token"]}
    TARGETED.atomic_json(TARGETED.receipt_path(obligation), receipt)
    with pytest.raises(TARGETED.CleanupError, match="launch token changed"):
        TARGETED.wait_for_worker(
            path,
            cleanup.session_close,
            obligation["launch_token"],
            obligation["identity_sha256"],
            0.1,
        )


def test_unknown_lock_file_is_not_deleted(cleanup: CleanupCase) -> None:
    path = TARGETED.obligation_path(
        cleanup.worktree, "a" * 64
    ).parent / TARGETED.target_key(cleanup.worktree)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = TARGETED.lock_path(path)
    lock.write_text("not-an-identity", encoding="utf-8")
    cleanup.prepare()
    assert lock.is_file()


def test_lock_acquisition_times_out(cleanup: CleanupCase) -> None:
    path = TARGETED.obligation_path(cleanup.worktree, "a" * 64)
    fake_msvcrt = types.SimpleNamespace(
        LK_NBLCK=1, LK_UNLCK=2, locking=mock.Mock(side_effect=OSError("held"))
    )
    with (
        mock.patch.object(TARGETED.os, "name", "nt"),
        mock.patch.dict(sys.modules, {"msvcrt": fake_msvcrt}),
        mock.patch.object(TARGETED.time, "monotonic", side_effect=[0.0, 2.1]),
        mock.patch.object(TARGETED.time, "sleep"),
        pytest.raises(TARGETED.CleanupError, match="lock acquisition timed out"),
        TARGETED.obligation_lock(path),
    ):
        pass


def test_retained_target_remains_durable_without_removal(cleanup: CleanupCase) -> None:
    path, obligation = cleanup.prepare(retained=True)
    with mock.patch.object(
        TARGETED, "load_session_close", return_value=cleanup.session_close
    ):
        result = cleanup.run_worker(path)
    assert obligation["state"] == "retained"
    assert result["state"] == "retained"
    assert cleanup.worktree.is_dir()
    assert TARGETED.receipt_path(result).is_file()


def test_wrong_holder_identity_refuses_cleanup(cleanup: CleanupCase) -> None:
    path, _ = cleanup.prepare()
    holder = cleanup.holder()
    cleanup.session_close.states[(int(holder["pid"]), float(holder["started_at"]))] = (
        "reused"
    )
    with mock.patch.object(
        TARGETED, "load_session_close", return_value=cleanup.session_close
    ):
        result = cleanup.run_worker(path)
    assert result["state"] == "refused"
    assert result["reason"] == "cleanup holder identity is unknown"


def test_second_live_worker_is_refused_without_overwriting_obligation(
    cleanup: CleanupCase,
) -> None:
    path, obligation = cleanup.prepare()
    obligation["worker"] = {"pid": 72, "started_at": 30.0}
    TARGETED.save(path, obligation)
    cleanup.session_close.states[(72, 30.0)] = "live"
    with (
        mock.patch.object(
            TARGETED, "load_session_close", return_value=cleanup.session_close
        ),
        pytest.raises(TARGETED.CleanupError, match="already live"),
    ):
        cleanup.run_worker(path)
    assert TARGETED.load(path)["worker"] == {"pid": 72, "started_at": 30.0}


def test_changed_obligation_identity_is_rejected_before_worker_start(
    cleanup: CleanupCase,
) -> None:
    path, obligation = cleanup.prepare()
    obligation["worktree"] = str(cleanup.root / "moved")
    TARGETED.atomic_json(path, obligation)
    with (
        mock.patch.object(
            TARGETED, "load_session_close", return_value=cleanup.session_close
        ),
        pytest.raises(TARGETED.CleanupError, match="identity changed"),
    ):
        cleanup.run_worker(path)


def test_worker_rejects_a_rehashed_immutable_change_before_proof(
    cleanup: CleanupCase,
) -> None:
    path, _ = cleanup.prepare()

    def change_identity(
        _module: Any, _obligation: Any, _target: Any
    ) -> tuple[bool, None]:
        changed = TARGETED.load(path)
        changed["branch"] = "Fix/Changed"
        changed["identity_sha256"] = TARGETED.immutable_digest(changed)
        TARGETED.atomic_json(path, changed)
        return True, None

    with (
        mock.patch.object(
            TARGETED, "load_session_close", return_value=cleanup.session_close
        ),
        mock.patch.object(TARGETED, "ready_for_removal", side_effect=change_identity),
        pytest.raises(TARGETED.CleanupError, match="identity changed"),
    ):
        cleanup.run_worker(path)


def test_launch_waits_for_exact_worker_acknowledgement(cleanup: CleanupCase) -> None:
    path, _ = cleanup.prepare()

    def start_detached(
        _script: Any, arguments: Any, extra: tuple[Any, ...] = ()
    ) -> None:
        cleanup.session_close.started_calls.append((arguments, extra))
        cleanup.acknowledge_worker(path)

    cleanup.session_close.start_detached = start_detached
    with mock.patch.object(
        TARGETED, "load_session_close", return_value=cleanup.session_close
    ):
        started = TARGETED.launch(path, "ignored", acknowledgement_timeout=1)
    assert started["state"] == "running"
    assert started["worker"] == {
        "pid": os.getpid(),
        "started_at": cleanup.session_close.started,
    }
    assert started["launch_token"] == started["launch"]["token"]
    assert len(cleanup.session_close.started_calls) == 1


def test_retry_refuses_an_unacknowledged_prior_launch(cleanup: CleanupCase) -> None:
    path, obligation = cleanup.prepare()
    obligation["launch"] = {
        "token": obligation["launch_token"],
        "launcher": {"pid": 71, "started_at": 30.0},
    }
    TARGETED.save(path, obligation)
    with (
        mock.patch.object(
            TARGETED, "load_session_close", return_value=cleanup.session_close
        ),
        pytest.raises(TARGETED.CleanupError, match="no worker acknowledgement"),
    ):
        TARGETED.launch(path, "ignored", retry=True)


def test_retry_refuses_a_reused_worker_identity(cleanup: CleanupCase) -> None:
    path, _ = cleanup.prepare()
    cleanup.arm(path)
    obligation = TARGETED.load(path)
    obligation["worker"] = {"pid": 72, "started_at": 30.0}
    TARGETED.save(path, obligation)
    cleanup.session_close.states[(72, 30.0)] = "reused"
    with (
        mock.patch.object(
            TARGETED, "load_session_close", return_value=cleanup.session_close
        ),
        pytest.raises(TARGETED.CleanupError, match="not safely reconciled"),
    ):
        TARGETED.run(path, retry=True, launch_token=obligation["launch_token"])


def test_concurrent_launch_dispatches_only_once(cleanup: CleanupCase) -> None:
    path, _ = cleanup.prepare()
    concurrent_errors: list[str] = []

    def start_detached(
        _script: Any, _arguments: Any, extra: tuple[Any, ...] = ()
    ) -> None:
        cleanup.session_close.started_calls.append(extra)
        try:
            TARGETED.launch(path, "ignored", acknowledgement_timeout=0.05)
        except TARGETED.CleanupError as error:
            concurrent_errors.append(str(error))
        cleanup.acknowledge_worker(path)

    cleanup.session_close.start_detached = start_detached
    with mock.patch.object(
        TARGETED, "load_session_close", return_value=cleanup.session_close
    ):
        TARGETED.launch(path, "ignored", acknowledgement_timeout=1)
    assert len(cleanup.session_close.started_calls) == 1
    assert concurrent_errors == [
        "targeted cleanup launch has no worker acknowledgement"
    ]


def test_retry_replaces_an_exited_worker_and_worker_can_run(
    cleanup: CleanupCase,
) -> None:
    path, obligation = cleanup.prepare()
    obligation["launch"] = {
        "token": obligation["launch_token"],
        "launcher": {"pid": 71, "started_at": 30.0},
    }
    obligation["worker"] = {"pid": 72, "started_at": 30.0}
    TARGETED.save(path, obligation, "timed_out", "old worker ended")
    cleanup.session_close.states[(72, 30.0)] = "exited"

    def start_detached(
        _script: Any, _arguments: Any, extra: tuple[Any, ...] = ()
    ) -> None:
        cleanup.acknowledge_worker(path)

    cleanup.session_close.start_detached = start_detached
    with mock.patch.object(
        TARGETED, "load_session_close", return_value=cleanup.session_close
    ):
        TARGETED.launch(path, "ignored", acknowledgement_timeout=1, retry=True)
    with (
        mock.patch.object(
            TARGETED, "load_session_close", return_value=cleanup.session_close
        ),
        mock.patch.object(TARGETED, "ready_for_removal", return_value=(True, None)),
        mock.patch.object(TARGETED, "exact_target", return_value=True),
        mock.patch.object(TARGETED.cleanup_proof, "run", return_value=0),
        mock.patch.object(
            TARGETED.worktree_sweep, "remove", return_value=(True, "removed")
        ),
        mock.patch.object(TARGETED, "verify_removal", return_value=True),
    ):
        result = TARGETED.run(path, launch_token=TARGETED.load(path)["launch_token"])
    assert result["state"] == "verified"


def test_worker_requires_a_recorded_launch(cleanup: CleanupCase) -> None:
    path, _ = cleanup.prepare()
    token = TARGETED.load(path)["launch_token"]
    with (
        mock.patch.object(
            TARGETED, "load_session_close", return_value=cleanup.session_close
        ),
        pytest.raises(TARGETED.CleanupError, match="requires a recorded launch"),
    ):
        TARGETED.run(path, launch_token=token)


def test_worker_only_marks_verified_after_post_removal_verification(
    cleanup: CleanupCase,
) -> None:
    path, _ = cleanup.prepare()
    with (
        mock.patch.object(
            TARGETED, "load_session_close", return_value=cleanup.session_close
        ),
        mock.patch.object(TARGETED, "ready_for_removal", return_value=(True, None)),
        mock.patch.object(TARGETED, "exact_target", return_value=True),
        mock.patch.object(TARGETED.cleanup_proof, "run", return_value=0),
        mock.patch.object(
            TARGETED.worktree_sweep, "remove", return_value=(True, "removed")
        ),
        mock.patch.object(TARGETED, "verify_removal", return_value=False),
    ):
        result = cleanup.run_worker(path)
    assert result["state"] == "pending"
    assert result["reason"] == "removed"
