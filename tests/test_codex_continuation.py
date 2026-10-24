import argparse
from contextlib import closing, redirect_stdout
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".agents/machine/scripts"))
import codex_continuation as CONTINUE
import reload_plugins as REFRESH


class CodexContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="continuation space caf\u00e9 ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.previous = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, self.previous)
        patcher = mock.patch.dict(os.environ, {
            "CODEX_THREAD_ID": "predecessor", "CODEX_SESSION_ID": "predecessor",
            "CODEX_HOME": str(self.root / "profile"), "AGENT_STATE_DIRECTORY": str(self.root / "state"),
        })
        patcher.start()
        self.addCleanup(patcher.stop)
        self.receipt = CONTINUE.receipt_path(self.root)
        self.goal = self.root / "goal.md"
        self.goal.write_text(
            "# Authorized task\nUser limits: open a PR, do not merge.\n"
            "Current state: uncommitted work preserved. Tests and decisions are linked here.\n"
            "## Execution readiness\nVerdict: ready\nExecution authorization: implementation\n"
            f"Transfer: required\nReceipt: {self.receipt}\n"
            "## Next Steps\nFinish the authorized repair, run its tests, and open the PR.\n", encoding="utf-8")
        self.transfer = CONTINUE.session_relaunch.load(CONTINUE.transfer_script(), "continuation_test_transfer")
        self.refresh = mock.Mock(return_value=0)
        self.launch = mock.Mock(return_value=0)
        self.launcher = argparse.Namespace(main=self.launch)
        original = CONTINUE.session_relaunch.load

        def load(path, name):
            return self.launcher if name == "refresh_codex_launcher" else original(path, name)

        patcher = mock.patch.object(CONTINUE.session_relaunch, "load", side_effect=load)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_continuation(self):
        with redirect_stdout(io.StringIO()):
            return CONTINUE.continue_session(self.root, self.goal, self.refresh)

    def data(self):
        return json.loads(self.receipt.read_text(encoding="utf-8"))

    def test_success_refreshes_launches_once_and_allows_only_one_pickup(self):
        self.assertEqual(self.run_continuation(), 0)
        self.assertEqual(self.run_continuation(), 0)
        self.refresh.assert_called_once()
        self.launch.assert_called_once()
        data = self.data()
        self.assertEqual(data["state"], "submitted")
        arguments = self.launch.call_args.args[0]
        self.assertNotIn("--bypass-hook-trust", arguments)
        self.assertEqual(arguments[arguments.index("--working-directory") + 1], str(self.root))
        self.assertEqual(arguments[arguments.index("--codex-home") + 1], str(self.root / "profile"))
        prompt = Path(arguments[arguments.index("--prompt-path") + 1]).read_text(encoding="utf-8")
        self.assertIn(str(self.goal), prompt)
        self.assertIn(data["attempt"], prompt)
        self.assertIn("Before any deliverable write", prompt)
        acknowledge = argparse.Namespace(command="acknowledge", receipt=str(self.receipt),
                                         attempt=data["attempt"], harness="codex", successor="successor")
        self.transfer.mutate(acknowledge)
        acknowledge.successor = "competitor"
        with self.assertRaisesRegex(ValueError, "another successor"):
            self.transfer.mutate(acknowledge)

    def test_refresh_failure_never_launches_and_same_checkpoint_can_retry(self):
        self.refresh.return_value = 1
        self.assertEqual(self.run_continuation(), 1)
        self.launch.assert_not_called()
        self.assertEqual(self.data()["state"], "prepared")
        self.refresh.return_value = 0
        self.assertEqual(self.run_continuation(), 0)

    def test_uncertain_launch_and_repeated_command_never_launch_again(self):
        self.launch.return_value = 3
        self.assertEqual(self.run_continuation(), 3)
        self.assertEqual(self.data()["state"], "uncertain")
        self.assertEqual(self.run_continuation(), 3)
        self.launch.assert_called_once()

    def test_confirmed_failure_allows_retry_after_fixing_prerequisite(self):
        self.launch.return_value = 1
        self.assertEqual(self.run_continuation(), 1)
        self.assertIn("failed_launch", self.data())
        self.assertEqual(self.data()["state"], "prepared")
        self.launch.return_value = 0
        self.assertEqual(self.run_continuation(), 0)

    def test_interruption_reserves_attempt_without_a_second_launch(self):
        self.launch.side_effect = RuntimeError("transport lost")
        with self.assertRaisesRegex(RuntimeError, "transport lost"):
            self.run_continuation()
        self.assertTrue(Path(self.data()["launch_status"]).is_absolute())
        self.assertTrue(self.receipt.with_suffix(".json.launch.txt").exists())
        self.assertEqual(self.run_continuation(), 3)
        self.launch.assert_called_once()

    def test_changed_checkpoint_is_rejected_before_refresh_or_pickup(self):
        self.refresh.return_value = 1
        self.assertEqual(self.run_continuation(), 1)
        self.goal.write_text(self.goal.read_text(encoding="utf-8") + "Changed user limit\n", encoding="utf-8")
        self.refresh.reset_mock()
        with self.assertRaisesRegex(ValueError, "goal changed"):
            self.run_continuation()
        self.refresh.assert_not_called()
        self.launch.assert_not_called()

    def test_inflight_attempt_is_not_retried(self):
        self.refresh.return_value = 1
        self.assertEqual(self.run_continuation(), 1)
        data = self.data()
        self.transfer.mutate(argparse.Namespace(command="begin", receipt=str(self.receipt),
                                                attempt=data["attempt"], predecessor="predecessor"))
        self.assertEqual(self.run_continuation(), 3)
        self.launch.assert_not_called()

    def test_native_identity_is_required_and_receipt_is_bound_to_profile_and_checkout(self):
        initial = self.receipt
        with mock.patch.dict(os.environ, {"CODEX_HOME": str(self.root / "another profile")}):
            self.assertNotEqual(initial, CONTINUE.receipt_path(self.root))
        self.assertNotEqual(initial, CONTINUE.receipt_path(self.root / "other checkout"))
        with mock.patch.dict(os.environ, {"CODEX_SESSION_ID": "wrong"}):
            with self.assertRaisesRegex(ValueError, "single native"):
                self.run_continuation()
        self.launch.assert_not_called()

    def create_association(self, role=None):
        self.receipt.parent.parent.mkdir(parents=True)
        with closing(sqlite3.connect(self.receipt.parent.parent / "sessions.db")) as connection:
            connection.execute("CREATE TABLE sessions (host TEXT, session_id TEXT, work_item TEXT, "
                               "role TEXT, ended_at REAL, handle TEXT)")
            connection.execute("INSERT INTO sessions VALUES ('codex', 'predecessor', 'execution:owned', ?, NULL, 'codex:predecessor')", (role,))
            connection.commit()

    def test_registered_execution_requires_its_existing_lease_transfer(self):
        self.create_association("owner")
        with self.assertRaisesRegex(ValueError, "owner release/claim"):
            self.run_continuation()
        self.refresh.assert_not_called()
        self.launch.assert_not_called()

    def test_metadata_association_without_a_claim_does_not_block_continuation(self):
        self.create_association()
        self.assertEqual(self.run_continuation(), 0)
        self.launch.assert_called_once()

    def test_another_recorded_owner_prevents_unclaimed_session_from_launching(self):
        self.create_association()
        with closing(sqlite3.connect(self.receipt.parent.parent / "sessions.db")) as connection:
            connection.execute("INSERT INTO sessions VALUES ('codex', 'other', 'execution:owned', 'owner', NULL, 'codex:other')")
            connection.commit()
        with self.assertRaisesRegex(ValueError, "owner release/claim"):
            self.run_continuation()
        self.launch.assert_not_called()

    def test_bounded_role_retains_its_existing_lease_transfer(self):
        self.create_association("bounded: parser")
        with self.assertRaisesRegex(ValueError, "owner release/claim"):
            self.run_continuation()
        self.launch.assert_not_called()

    def test_sync_entrypoint_refreshes_codex_before_continuing_even_when_current(self):
        with mock.patch.object(REFRESH, "review_legacy", return_value=([], {})), \
                mock.patch.object(REFRESH.launch_check, "check", return_value="current") as check, \
                redirect_stdout(io.StringIO()):
            self.assertEqual(REFRESH.main(["--project", str(self.root), "--host", "codex",
                                           "--continue-codex", str(self.goal)]), 0)
        self.assertEqual(check.call_args.kwargs["host"], "codex")
        self.launch.assert_called_once()

    def test_status_is_read_only_and_invalid_modes_never_launch(self):
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(REFRESH.main(["--continuation-status", "--project", str(self.root)]), 0)
        self.assertEqual(json.loads(output.getvalue())["receipt"], str(self.receipt))
        self.assertFalse(self.receipt.exists())
        for arguments in (["--continue-codex", str(self.goal)],
                          ["--host", "codex", "--verify-only", "--continue-codex", str(self.goal)]):
            with self.subTest(arguments=arguments), mock.patch("sys.stderr"), self.assertRaises(SystemExit):
                REFRESH.main(arguments)
        self.launch.assert_not_called()

    def test_packaged_helper_and_discovery_entrypoint_work_without_author_checkout_imports(self):
        import subprocess

        package = ROOT / "plugins/machine"
        packaged_script = package / "resources/machine/scripts/codex_continuation.py"
        with mock.patch.object(CONTINUE, "__file__", str(packaged_script)):
            helper = CONTINUE.transfer_script()
        self.assertEqual(helper.read_text(encoding="utf-8"),
                         (ROOT / ".agents/workflow/workflow/handoff/scripts/transfer.py").read_text(encoding="utf-8"))
        result = subprocess.run([
            sys.executable, "-I", "-B", str(package / "codex-skills/sync-plugins/scripts/sync_plugins.py"),
            "--project", str(self.root), "--continuation-status"], capture_output=True, text=True,
            encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["receipt"], str(self.receipt))

    def test_real_launcher_rejects_an_existing_startup_receipt_without_opening_a_tab(self):
        launcher = CONTINUE.session_relaunch.load(
            ROOT / ".agents/machine/utility/handoff-codex/scripts/launch_codex.py", "test_real_launcher")
        startup = self.root / "startup.json"
        startup.write_text('{"state": "preparing"}', encoding="utf-8")
        with mock.patch.object(launcher, "_load_agent_cli", return_value=REFRESH.agent_cli), \
                mock.patch.object(REFRESH.agent_cli, "launch_tab") as launch, \
                mock.patch("sys.stdout"), mock.patch("sys.stderr"):
            self.assertEqual(launcher.main(["--working-directory", str(self.root), "--prompt-path", str(self.goal),
                                           "--status-file", str(startup)]), 3)
        launch.assert_not_called()

    def test_real_launcher_preserves_explicit_profile_through_terminal_environment(self):
        launcher = CONTINUE.session_relaunch.load(
            ROOT / ".agents/machine/utility/handoff-codex/scripts/launch_codex.py", "test_profile_launcher")
        profile = self.root / "refreshed profile"
        with mock.patch.object(launcher, "_load_agent_cli", return_value=REFRESH.agent_cli), \
                mock.patch.object(REFRESH.agent_cli, "resolve_codex_executable", return_value=("codex", {
                    "core": (0, 164, 0), "text": "0.164.0"})), \
                mock.patch.object(REFRESH.agent_cli, "launch_tab") as launch, \
                mock.patch.object(REFRESH.agent_cli, "await_handoff_startup"), \
                mock.patch("sys.stdout"), mock.patch("sys.stderr"):
            self.assertEqual(launcher.main(["--working-directory", str(self.root), "--prompt-path", str(self.goal),
                                           "--codex-home", str(profile)]), 0)
        self.assertEqual(launch.call_args.kwargs["force"], {"CODEX_HOME": str(profile)})
        inner = REFRESH.agent_cli.posix_inner_command(self.root, [], {"CODEX_HOME": str(profile)}, "python3", [])
        self.assertIn("CODEX_HOME=" + str(profile), inner)


if __name__ == "__main__":
    unittest.main()
