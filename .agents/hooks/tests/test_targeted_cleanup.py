import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import sys
import types
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / ".agents/engineering/workflow/merge/scripts"
SPEC = importlib.util.spec_from_file_location("targeted_cleanup", SCRIPTS / "targeted_cleanup.py")
TARGETED = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TARGETED)


class SessionClose:
    __file__ = str(ROOT / "outside-session-close.py")

    def __init__(self):
        self.states = {}
        self.started = 10.0
        self.started_calls = []

    def process_info(self, pid):
        return SimpleNamespace(pid=pid, started_at=self.started, name="python")

    def valid_identity(self, pid, started_at):
        return type(pid) is int and pid > 0 and isinstance(started_at, (int, float)) and started_at > 0

    def identity_status(self, pid, started_at):
        return self.states.get((pid, started_at), "exited")

    def process_state(self, pid):
        return "absent", None

    def verified_live(self, pid, started_at):
        return self.identity_status(pid, started_at) == "live"

    def under_or_equal(self, child, parent):
        child_path = Path(child).resolve()
        parent_path = Path(parent).resolve()
        return child_path == parent_path or parent_path in child_path.parents

    def start_detached(self, script, arguments, extra=()):
        self.started_calls.append((Path(script), list(arguments), list(extra)))


class TargetedCleanupTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.primary = self.root / "primary"
        self.worktree = self.root / "worktree"
        self.primary.mkdir()
        self.worktree.mkdir()
        self.session_close = SessionClose()
        self.process_info = mock.patch.object(TARGETED, "process_info", side_effect=self.session_close.process_info)
        self.process_info.start()
        self.addCleanup(self.process_info.stop)
        self.environment = mock.patch.dict(os.environ, {"AGENT_STATE_DIRECTORY": str(self.root / "state")})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def holder(self, pid=91, started_at=20.0):
        return {"pid": pid, "started_at": started_at}

    def prepare(self, holders=None, retained=False):
        return TARGETED.prepare(
            self.primary, self.worktree, "Fix/Target", "a" * 40, 42, "example/test",
            {"host": "codex", "session_id": "s1"}, [self.holder()] if holders is None else holders, retained,
        )

    def arm(self, path):
        obligation = TARGETED.load(path)
        obligation["launch"] = {
            "token": obligation["launch_token"],
            "launcher": {"pid": 71, "started_at": 30.0},
        }
        return TARGETED.save(path, obligation)

    def run_worker(self, path, **kwargs):
        self.arm(path)
        token = TARGETED.load(path)["launch_token"]
        return TARGETED.run(path, launch_token=token, **kwargs)

    def acknowledge_worker(self, path, started_at=None):
        started_at = self.session_close.started if started_at is None else started_at
        obligation = TARGETED.load(path)
        obligation["worker"] = {"pid": os.getpid(), "started_at": started_at}
        self.session_close.states[(os.getpid(), started_at)] = "live"
        return TARGETED.save(path, obligation, "running", None)

    def test_repeat_prepare_reuses_existing_obligation_and_launch_token(self):
        path, first = self.prepare()
        repeated_path, second = self.prepare()

        self.assertEqual(path, repeated_path)
        self.assertEqual(first["obligation_id"], second["obligation_id"])
        self.assertEqual(first["launch_token"], second["launch_token"])

    def test_unknown_lock_file_is_not_deleted(self):
        path = TARGETED.obligation_path(self.worktree)
        path.parent.mkdir(parents=True, exist_ok=True)
        lock = TARGETED.lock_path(path)
        lock.write_text("not-an-identity", encoding="utf-8")

        self.prepare()

        self.assertTrue(lock.is_file())

    def test_lock_acquisition_times_out(self):
        path = TARGETED.obligation_path(self.worktree)
        fake_msvcrt = types.SimpleNamespace(
            LK_NBLCK=1,
            LK_UNLCK=2,
            locking=mock.Mock(side_effect=OSError("held")),
        )

        with mock.patch.object(TARGETED.os, "name", "nt"), \
             mock.patch.dict(sys.modules, {"msvcrt": fake_msvcrt}), \
             mock.patch.object(TARGETED.time, "monotonic", side_effect=[0.0, 2.1]), \
             mock.patch.object(TARGETED.time, "sleep"):
            with self.assertRaisesRegex(TARGETED.CleanupError, "lock acquisition timed out"):
                with TARGETED.obligation_lock(path):
                    pass

    def test_retained_target_remains_durable_without_removal(self):
        path, obligation = self.prepare(retained=True)
        with mock.patch.object(TARGETED, "load_session_close", return_value=self.session_close):
            result = self.run_worker(path)

        self.assertEqual("retained", obligation["state"])
        self.assertEqual("retained", result["state"])
        self.assertTrue(self.worktree.is_dir())
        self.assertTrue(TARGETED.receipt_path(result).is_file())

    def test_wrong_holder_identity_refuses_cleanup(self):
        path, _obligation = self.prepare()
        holder = self.holder()
        self.session_close.states[(holder["pid"], holder["started_at"])] = "reused"
        with mock.patch.object(TARGETED, "load_session_close", return_value=self.session_close):
            result = self.run_worker(path)

        self.assertEqual("refused", result["state"])
        self.assertEqual("cleanup holder identity is unknown", result["reason"])

    def test_second_live_worker_is_refused_without_overwriting_obligation(self):
        path, obligation = self.prepare()
        obligation["worker"] = {"pid": 72, "started_at": 30.0}
        TARGETED.save(path, obligation)
        self.session_close.states[(72, 30.0)] = "live"
        with mock.patch.object(TARGETED, "load_session_close", return_value=self.session_close):
            with self.assertRaisesRegex(TARGETED.CleanupError, "already live"):
                self.run_worker(path)

        self.assertEqual({"pid": 72, "started_at": 30.0}, TARGETED.load(path)["worker"])

    def test_changed_obligation_identity_is_rejected_before_worker_start(self):
        path, obligation = self.prepare()
        obligation["worktree"] = str(self.root / "moved")
        TARGETED.atomic_json(path, obligation)
        with mock.patch.object(TARGETED, "load_session_close", return_value=self.session_close):
            with self.assertRaisesRegex(TARGETED.CleanupError, "identity changed"):
                self.run_worker(path)

    def test_worker_rejects_a_rehashed_immutable_change_before_proof(self):
        path, _obligation = self.prepare()

        def change_identity(_module, _obligation, _target):
            changed = TARGETED.load(path)
            changed["branch"] = "Fix/Changed"
            changed["identity_sha256"] = TARGETED.immutable_digest(changed)
            TARGETED.atomic_json(path, changed)
            return True, None

        with mock.patch.object(TARGETED, "load_session_close", return_value=self.session_close), \
             mock.patch.object(TARGETED, "ready_for_removal", side_effect=change_identity):
            with self.assertRaisesRegex(TARGETED.CleanupError, "identity changed"):
                self.run_worker(path)

    def test_launch_waits_for_exact_worker_acknowledgement(self):
        path, _obligation = self.prepare()

        def start_detached(_script, arguments, extra=()):
            self.session_close.started_calls.append((arguments, extra))
            self.acknowledge_worker(path)

        self.session_close.start_detached = start_detached
        with mock.patch.object(TARGETED, "load_session_close", return_value=self.session_close):
            started = TARGETED.launch(path, "ignored", acknowledgement_timeout=1)

        self.assertEqual("running", started["state"])
        self.assertEqual({"pid": os.getpid(), "started_at": self.session_close.started}, started["worker"])
        self.assertEqual(started["launch_token"], started["launch"]["token"])
        self.assertEqual(1, len(self.session_close.started_calls))

    def test_retry_refuses_an_unacknowledged_prior_launch(self):
        path, obligation = self.prepare()
        obligation["launch"] = {"token": obligation["launch_token"], "launcher": {"pid": 71, "started_at": 30.0}}
        TARGETED.save(path, obligation)
        with mock.patch.object(TARGETED, "load_session_close", return_value=self.session_close):
            with self.assertRaisesRegex(TARGETED.CleanupError, "no worker acknowledgement"):
                TARGETED.launch(path, "ignored", retry=True)

    def test_retry_refuses_a_reused_worker_identity(self):
        path, _obligation = self.prepare()
        self.arm(path)
        obligation = TARGETED.load(path)
        obligation["worker"] = {"pid": 72, "started_at": 30.0}
        TARGETED.save(path, obligation)
        self.session_close.states[(72, 30.0)] = "reused"

        with mock.patch.object(TARGETED, "load_session_close", return_value=self.session_close):
            with self.assertRaisesRegex(TARGETED.CleanupError, "not safely reconciled"):
                TARGETED.run(path, retry=True, launch_token=obligation["launch_token"])

    def test_concurrent_launch_dispatches_only_once(self):
        path, _obligation = self.prepare()
        concurrent_errors = []

        def start_detached(_script, _arguments, extra=()):
            self.session_close.started_calls.append(extra)
            try:
                TARGETED.launch(path, "ignored", acknowledgement_timeout=0.05)
            except TARGETED.CleanupError as error:
                concurrent_errors.append(str(error))
            self.acknowledge_worker(path)

        self.session_close.start_detached = start_detached

        with mock.patch.object(TARGETED, "load_session_close", return_value=self.session_close):
            TARGETED.launch(path, "ignored", acknowledgement_timeout=1)

        self.assertEqual(1, len(self.session_close.started_calls))
        self.assertEqual(["targeted cleanup launch has no worker acknowledgement"], concurrent_errors)

    def test_retry_replaces_an_exited_worker_and_worker_can_run(self):
        path, obligation = self.prepare()
        obligation["launch"] = {
            "token": obligation["launch_token"],
            "launcher": {"pid": 71, "started_at": 30.0},
        }
        obligation["worker"] = {"pid": 72, "started_at": 30.0}
        TARGETED.save(path, obligation, "timed_out", "old worker ended")
        self.session_close.states[(72, 30.0)] = "exited"

        def start_detached(_script, _arguments, extra=()):
            self.acknowledge_worker(path)

        self.session_close.start_detached = start_detached
        with mock.patch.object(TARGETED, "load_session_close", return_value=self.session_close):
            TARGETED.launch(path, "ignored", acknowledgement_timeout=1, retry=True)
        with mock.patch.object(TARGETED, "load_session_close", return_value=self.session_close), \
             mock.patch.object(TARGETED, "ready_for_removal", return_value=(True, None)), \
             mock.patch.object(TARGETED, "exact_target", return_value=True), \
             mock.patch.object(TARGETED.cleanup_proof, "run", return_value=0), \
             mock.patch.object(TARGETED.worktree_sweep, "remove", return_value=(True, "removed")), \
             mock.patch.object(TARGETED, "verify_removal", return_value=True):
            result = TARGETED.run(path, launch_token=TARGETED.load(path)["launch_token"])

        self.assertEqual("verified", result["state"])

    def test_worker_requires_a_recorded_launch(self):
        path, _obligation = self.prepare()
        token = TARGETED.load(path)["launch_token"]

        with mock.patch.object(TARGETED, "load_session_close", return_value=self.session_close):
            with self.assertRaisesRegex(TARGETED.CleanupError, "requires a recorded launch"):
                TARGETED.run(path, launch_token=token)

    def test_worker_only_marks_verified_after_post_removal_verification(self):
        path, _obligation = self.prepare()
        with mock.patch.object(TARGETED, "load_session_close", return_value=self.session_close), \
             mock.patch.object(TARGETED, "ready_for_removal", return_value=(True, None)), \
             mock.patch.object(TARGETED, "exact_target", return_value=True), \
             mock.patch.object(TARGETED.cleanup_proof, "run", return_value=0), \
             mock.patch.object(TARGETED.worktree_sweep, "remove", return_value=(True, "removed")), \
             mock.patch.object(TARGETED, "verify_removal", return_value=False):
            result = self.run_worker(path)

        self.assertEqual("pending", result["state"])
        self.assertEqual("removed", result["reason"])


if __name__ == "__main__":
    unittest.main()
