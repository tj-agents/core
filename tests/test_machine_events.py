import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

SCRIPTS = Path(__file__).resolve().parents[1] / ".agents/machine/scripts"
sys.path.insert(0, str(SCRIPTS))
import machine_events as events
import setup_machine as setup


def current(repository="tj-agents/core", revision="a", policy="policy", marketplace=True):
    return {"nameWithOwner": repository, "defaultBranchRef": {"name": "main", "target": {"oid": revision}},
            "policy": {"oid": policy} if policy else None,
            "marketplace": {"oid": "manifest"} if marketplace else None}


class HintTests(unittest.TestCase):
    def test_only_valid_repo_hints_enter_the_queue(self):
        for message in ({"v": 1, "repo": "other/repo"}, {"v": 1, "repo": "tj-agents/../x"},
                        {"v": True, "repo": "tj-agents/core"}, [], "garbage"):
            self.assertIsNone(events.parse_hint({"event": "message", "message": json.dumps(message)}))
        message = {"v": 1, "repo": "tj-agents/core", "policy": {"agents_may_merge": True}, "command": "evil"}
        self.assertEqual("tj-agents/core", events.parse_hint({"event": "message", "message": json.dumps(message)}))
        self.assertIsNone(events.parse_hint({"event": "keepalive"}))

    def test_pending_work_coalesces_and_is_bounded(self):
        pending = events.Pending()
        for _ in range(1000):
            pending.put("tj-agents/core")
        self.assertEqual(1, len(pending.items))
        for index in range(500):
            pending.put(f"tj-agents/r{index}")
        self.assertEqual(256, len(pending.items))
        self.assertEqual("tj-agents/core", pending.get())

    def test_keepalive_is_idle_and_replay_cursor_is_saved_after_enqueue(self):
        with tempfile.TemporaryDirectory() as directory:
            cursor = Path(directory) / "cursor.json"
            lines = [{"event": "open"}, {"event": "keepalive"},
                     {"event": "message", "id": "abc123", "message": json.dumps({"v": 1, "repo": "tj-agents/core"})}]
            response = io.BytesIO(b"\n".join(json.dumps(line).encode() for line in lines) + b"\n")
            pending = events.Pending()
            opener = mock.Mock(return_value=response)
            with mock.patch.object(events.time, "sleep", side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
                events.subscribe("a" * 48, pending, cursor, opener=opener)
            self.assertEqual([None, "tj-agents/core"], list(pending.items))
            self.assertEqual({"since": "abc123"}, json.loads(cursor.read_text(encoding="utf-8")))
            self.assertIn("since=all", opener.call_args.args[0])


class ReconcileTests(unittest.TestCase):
    def setUp(self):
        self.refresh = mock.Mock(return_value=0)
        self.policy = mock.Mock()
        self.sweep = mock.Mock()
        self.reconciler = events.Reconciler(refresh=self.refresh, policy=self.policy, sweep=self.sweep)

    def test_duplicate_hint_does_not_repeat_work_and_changed_policy_uses_only_repo(self):
        self.reconciler.repository(current())
        self.reconciler.repository(current())
        self.refresh.assert_called_once_with()
        self.policy.assert_called_once_with("tj-agents/core")
        self.reconciler.repository(current(revision="b", policy="new-policy", marketplace=False))
        self.assertEqual(2, self.policy.call_count)

    def test_catch_up_refreshes_once_for_many_marketplaces(self):
        self.reconciler.catch_up([current(f"tj-agents/repo{i}") for i in range(50)])
        self.refresh.assert_called_once_with()
        self.assertEqual(50, self.policy.call_count)
        self.sweep.assert_called_once_with()

    def test_absent_policy_never_gets_a_default_gate(self):
        self.reconciler.repository(current(policy=None, marketplace=False))
        self.policy.assert_not_called()
        self.refresh.assert_not_called()

    def test_catch_up_isolates_one_policy_failure_and_continues(self):
        self.policy.side_effect = [RuntimeError("private repo"), None]
        with self.assertLogs(events.LOG, level="ERROR"):
            failures = self.reconciler.catch_up([current("tj-agents/private"), current("tj-agents/other")])
        self.assertEqual(["tj-agents/private"], failures)
        self.assertIn("tj-agents/other", self.reconciler.state)
        self.assertNotIn("tj-agents/private", self.reconciler.state)

    def test_failed_action_is_not_acknowledged(self):
        self.policy.side_effect = RuntimeError("offline")
        with self.assertRaises(RuntimeError):
            self.reconciler.repository(current())
        self.assertEqual({}, self.reconciler.state)


class IdentityTests(unittest.TestCase):
    def test_saved_tommy_login_is_required(self):
        with self.assertRaises(RuntimeError):
            events.require_tommy(lambda _: {"login": "tomjseery-bot[bot]"})

    def test_tokens_and_agent_git_overrides_never_reach_policy_subprocess(self):
        run = mock.Mock(return_value=mock.Mock(returncode=0))
        environment = {"TJ_AGENT": "1", "GH_TOKEN": "bot", "GITHUB_TOKEN": "bot",
                       "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_VALUE_0": "helper", "KEEP_ME": "yes"}
        with mock.patch.dict(os.environ, environment), mock.patch.object(events, "policy_script", return_value=Path("/installed/merge_policy.py")):
            events.reconcile_policy("tj-agents/core", run=run)
        saved = run.call_args.kwargs["env"]
        self.assertEqual("yes", saved["KEEP_ME"])
        self.assertFalse(any(key.startswith("GIT_CONFIG_") or key in {"TJ_AGENT", "GH_TOKEN", "GITHUB_TOKEN"} for key in saved))
        self.assertEqual(["reconcile", "--repo", "tj-agents/core"], run.call_args.args[0][-3:])
        self.assertEqual(events.plugins.NO_WINDOW, run.call_args.kwargs["creationflags"])

    def test_native_exit_notification_uses_a_dummy_process(self):
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(0.1)"],
                                 creationflags=events.plugins.NO_WINDOW)
        try:
            events.wait_for_exit(child.pid)
            self.assertEqual(0, child.wait(timeout=5))
        finally:
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=5)

    def test_listener_lock_has_no_age_expiry_and_releases_with_handle(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lock"
            first = events.acquire_listener_lock(path)
            self.assertIsNotNone(first)
            try:
                self.assertIsNone(events.acquire_listener_lock(path))
            finally:
                first.close()
            again = events.acquire_listener_lock(path)
            self.assertIsNotNone(again)
            again.close()


class SetupTests(unittest.TestCase):
    def test_windows_registration_is_logon_only_hidden_and_restarts_without_time_limit(self):
        xml = setup.windows_task_xml("PC\\Tommy & Co", "C:/Python/pythonw.exe", Path("C:/state dir/event.py"))
        root = ET.fromstring(xml)
        ns = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}
        self.assertIsNotNone(root.find("t:Triggers/t:LogonTrigger", ns))
        self.assertIsNone(root.find("t:Triggers/t:TimeTrigger", ns))
        self.assertEqual("PT0S", root.find("t:Settings/t:ExecutionTimeLimit", ns).text)
        self.assertIsNotNone(root.find("t:Settings/t:RestartOnFailure", ns))
        self.assertEqual("true", root.find("t:Settings/t:Hidden", ns).text)

    def test_linux_service_quotes_paths_and_has_no_timer(self):
        with tempfile.TemporaryDirectory(prefix="machine ü ") as directory:
            calls = []
            run = lambda command, **kwargs: calls.append(command)
            home = Path(directory)
            setup.schedule_systemd(home / "100% state/event.py", home, run=run)
            unit = (home / ".config/systemd/user/tj-agents-machine-events.service").read_text(encoding="utf-8")
            self.assertIn("100%% state", unit)
            self.assertIn("Restart=always", unit)
            self.assertNotIn("OnCalendar", unit)
            self.assertEqual("restart", calls[-1][2])

    def test_only_retired_cron_jobs_are_removed_idempotently(self):
        text = "0 5 * * * backup\n@reboot old # tj-agents-plugin-autoupdate\n17 * * * * old # tj-agents-merge-gates\n"
        run = mock.Mock(return_value=mock.Mock(returncode=0, stdout=text))
        setup.remove_retired_cron(run=run)
        self.assertEqual("0 5 * * * backup\n", run.call_args.kwargs["input"])
        run = mock.Mock(return_value=mock.Mock(returncode=0, stdout="0 5 * * * backup\n"))
        setup.remove_retired_cron(run=run)
        self.assertEqual(1, run.call_count)

    def test_shared_topic_is_reused_without_writing_github_on_rerun(self):
        with tempfile.TemporaryDirectory() as directory:
            api = mock.Mock(return_value={"variables": [{"name": "MACHINE_EVENTS_TOPIC", "value": "a" * 48}]})
            self.assertEqual("a" * 48, setup.configure_topic(Path(directory), api=api))
            self.assertEqual(1, api.call_count)
            api.reset_mock()
            self.assertEqual("a" * 48, setup.configure_topic(Path(directory), api=api))
            self.assertEqual(1, api.call_count)

    def test_publisher_configuration_writes_only_a_missing_or_different_variable(self):
        rows = [current("tj-agents/current"), current("tj-agents/new")]
        api = mock.Mock(side_effect=[{"variables": [{"name": "MACHINE_EVENTS_TOPIC", "value": "a" * 48}]},
                                    {"variables": []}, None])
        self.assertEqual(1, setup.configure_publishers("a" * 48, rows, api=api))
        self.assertEqual("POST", api.call_args.args[0][1])
        self.assertEqual("repos/tj-agents/new/actions/variables", api.call_args.args[0][2])

    def test_installation_copies_the_complete_standalone_runtime(self):
        with tempfile.TemporaryDirectory(prefix="runtime ü ") as directory:
            script = setup.install_listener(Path(directory))
            self.assertEqual("machine_events.py", script.name)
            for name in ("machine_events.py", "plugin_autoupdate.py"):
                self.assertEqual((SCRIPTS / name).read_bytes(), (Path(directory) / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
