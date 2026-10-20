from __future__ import annotations

import importlib.util
import json
import os
import shutil
import signal
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents" / "machine" / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("startup_binding_test", SCRIPTS / "startup_binding.py")
BINDING = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BINDING)


class StartupBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="startup binding ")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)

    def test_status_file_reports_preparation_failure_and_exit(self):
        status = self.project / "launch.status.json"
        seen = []

        def failing(*_args, **_kwargs):
            seen.append(json.loads(status.read_text(encoding="utf-8"))["state"])
            raise BINDING.StartupBindingError("unsupported value")

        arguments = ["--host", "codex", "--project", str(self.project), "--target", "codex", "--status-file",
                     str(status), "--", "resume", "id"]
        with mock.patch.object(BINDING, "run_session", side_effect=failing), mock.patch("sys.stderr"):
            self.assertEqual(1, BINDING.main(arguments))
        self.assertEqual(["preparing"], seen)
        failed = json.loads(status.read_text(encoding="utf-8"))
        self.assertEqual("failed", failed["state"])
        self.assertIn("unsupported value", failed["error"])
        status.unlink()
        states = []

        def running(*_args, on_running, **_kwargs):
            on_running(4242)
            states.append(json.loads(status.read_text(encoding="utf-8"))["state"])
            self.assertEqual(4242, json.loads(status.read_text(encoding="utf-8"))["child_pid"])
            return 0

        with mock.patch.object(BINDING, "run_session", side_effect=running):
            self.assertEqual(0, BINDING.main(arguments))
        self.assertEqual(["running"], states)
        self.assertEqual({"state": "exited", "returncode": 0},
                         {key: value for key, value in json.loads(status.read_text(encoding="utf-8")).items()
                          if key in {"state", "returncode"}})

    def test_handoff_failure_retains_native_debug_destination_and_last_phase(self):
        status = self.project / "handoff.json"
        captured = []
        phases = []

        def failing(host, target, project, arguments, *, on_phase=None, **kwargs):
            captured.extend(arguments)
            if on_phase is not None:
                on_phase("starting-native")
                phases.append(json.loads(status.read_text(encoding="utf-8"))["phase"])
            raise BINDING.StartupBindingError("fixture startup failed")

        arguments = ["--host", "claude", "--project", str(self.project), "--target", "claude",
                     "--status-file", str(status), "--require-session-start", "--", "fixture prompt"]
        with mock.patch.object(BINDING, "run_session", side_effect=failing), \
                mock.patch("sys.stdout") as output, mock.patch("sys.stderr"):
            self.assertEqual(1, BINDING.main(arguments))
        self.assertEqual(["starting-native"], phases)
        failed = json.loads(status.read_text(encoding="utf-8"))
        self.assertEqual("failed", failed["state"])
        self.assertEqual("starting-native", failed["phase"])
        debug_log = self.project.resolve() / "native-debug.log"
        self.assertEqual(str(debug_log), failed["debug_log"])
        self.assertEqual(["--debug-file", str(debug_log), "fixture prompt"], captured)
        output.write.assert_any_call("launch: claude startup: starting-native")

    def test_handoff_keeps_an_explicit_debug_file_and_leaves_ordinary_launches_alone(self):
        for flags in (("--require-session-start",), ()):
            with self.subTest(flags=flags):
                status = self.project / "explicit.json"
                status.unlink(missing_ok=True)
                captured = []

                def run(host, target, project, arguments, **kwargs):
                    captured.extend(arguments)
                    return 0

                arguments = ["--host", "claude", "--project", str(self.project), "--target", "claude",
                             "--status-file", str(status), *flags, "--", "--debug-file", "explicit.log",
                             "fixture prompt"]
                with mock.patch.object(BINDING, "run_session", side_effect=run):
                    self.assertEqual(0, BINDING.main(arguments))
                self.assertEqual(["--debug-file", "explicit.log", "fixture prompt"], captured)
                self.assertNotIn("debug_log", json.loads(status.read_text(encoding="utf-8")))

    def test_an_abandoned_launch_never_starts(self):
        status = self.project / "launch.status.json"
        status.write_text(json.dumps({"state": "abandoned"}), encoding="utf-8")
        arguments = ["--host", "codex", "--project", str(self.project), "--target", "codex", "--status-file",
                     str(status), "--", "resume", "id"]
        with mock.patch.object(BINDING, "run_session") as run, mock.patch("sys.stderr"):
            self.assertEqual(1, BINDING.main(arguments))
        run.assert_not_called()

    def test_native_child_receives_arguments_and_no_parent_binding_state(self):
        script = self.project / "child \u00fc.py"
        output = self.project / "result.json"
        script.write_text("import os,sys,json\nfrom pathlib import Path\nPath(sys.argv[1]).write_text(json.dumps([sys.argv[2:], {k:v for k,v in os.environ.items() if k.startswith('TJ_AGENTS_STARTUP_')}]))", encoding="utf-8")
        with mock.patch.dict(os.environ, {"TJ_AGENTS_STARTUP_ACK_TOKEN": "parent"}):
            self.assertEqual(0, BINDING.run_session("codex", sys.executable, self.project,
                                                   [str(script), str(output), "a b", "\u00fc"]))
        self.assertEqual([["a b", "\u00fc"], {}], json.loads(output.read_text()))

    def test_native_session_acknowledgement_and_exit_are_observed(self):
        script = self.project / "ack.py"
        script.write_text("import os\nfrom pathlib import Path\np=Path(os.environ['TJ_AGENTS_STARTUP_ACK_DIRECTORY'])/os.environ['TJ_AGENTS_STARTUP_ACK_TOKEN']\np.write_text(p.name)", encoding="utf-8")
        running = mock.Mock()
        self.assertEqual(0, BINDING.run_session("claude", sys.executable, self.project, [str(script)],
                                               require_session_start=True, on_running=running))
        running.assert_called_once()

    @unittest.skipUnless(os.name == "nt", "Windows taskkill fallback")
    def test_taskkill_failure_falls_back_to_direct_termination(self):
        for error in (OSError("unavailable"), subprocess.TimeoutExpired("taskkill", 10)):
            with self.subTest(error=error):
                process = mock.Mock(pid=4242)
                with mock.patch.object(BINDING.subprocess, "run", side_effect=error):
                    BINDING._terminate(process)
                process.kill.assert_called_once()
                process.wait.assert_called_once_with(timeout=5)

    @unittest.skipIf(os.name == "nt", "POSIX process groups")
    def test_termination_escalates_to_the_entire_process_group(self):
        process = mock.Mock(pid=4242)
        process.wait.side_effect = [subprocess.TimeoutExpired("native", 5), 0]
        with mock.patch.object(BINDING.os, "killpg") as killpg:
            BINDING._terminate(process)
        self.assertEqual([mock.call(4242, signal.SIGTERM), mock.call(4242, signal.SIGKILL)], killpg.call_args_list)
        process.kill.assert_not_called()

    def test_missing_acknowledgement_preserves_the_child_and_its_exit_code(self):
        survived = self.project / "survived.json"
        script = self.project / "unacknowledged child \u00fc.py"
        script.write_text(
            "import sys,time\nfrom pathlib import Path\n"
            "time.sleep(0.3)\nPath(sys.argv[1]).write_text('survived')\nsys.exit(7)\n",
            encoding="utf-8",
        )
        for host in ("codex", "claude"):
            with self.subTest(host=host), mock.patch("sys.stderr"):
                survived.unlink(missing_ok=True)
                running, unconfirmed = mock.Mock(), mock.Mock()
                self.assertEqual(7, BINDING.run_session(
                    host, sys.executable, self.project, [str(script), str(survived)],
                    require_session_start=True, timeout=0, on_running=running,
                    on_unconfirmed=unconfirmed,
                ))
                self.assertEqual("survived", survived.read_text(encoding="utf-8"))
                running.assert_not_called()
                unconfirmed.assert_called_once()
                self.assertIsInstance(unconfirmed.call_args.args[0], int)

    def test_late_acknowledgement_confirms_the_original_child(self):
        script = self.project / "late acknowledgement.py"
        script.write_text(
            "import os,time\nfrom pathlib import Path\n"
            "time.sleep(0.2)\n"
            "token=os.environ['TJ_AGENTS_STARTUP_ACK_TOKEN']\n"
            "(Path(os.environ['TJ_AGENTS_STARTUP_ACK_DIRECTORY'])/token).write_text(token)\n"
            "time.sleep(0.1)\n", encoding="utf-8",
        )
        events = mock.Mock()
        with mock.patch("sys.stderr"):
            self.assertEqual(0, BINDING.run_session(
                "codex", sys.executable, self.project, [str(script)], require_session_start=True,
                timeout=0, on_running=events.running, on_unconfirmed=events.unconfirmed,
            ))
        self.assertEqual(["unconfirmed", "running"], [call[0] for call in events.mock_calls])
        self.assertEqual(events.unconfirmed.call_args, events.running.call_args)

    def test_missing_acknowledgement_receipt_never_claims_verified_startup(self):
        status = self.project / "unconfirmed.json"
        observed = []

        def run(*_args, on_unconfirmed, **_kwargs):
            on_unconfirmed(4242)
            observed.append(json.loads(status.read_text(encoding="utf-8")))
            return 0

        arguments = ["--host", "codex", "--project", str(self.project), "--target", "codex",
                     "--status-file", str(status), "--require-session-start", "--"]
        with mock.patch.object(BINDING, "run_session", side_effect=run):
            self.assertEqual(0, BINDING.main(arguments))
        self.assertEqual("unconfirmed", observed[0]["state"])
        self.assertEqual(4242, observed[0]["child_pid"])
        self.assertNotIn("running_at", observed[0])
        final = json.loads(status.read_text(encoding="utf-8"))
        self.assertEqual("exited", final["state"])
        self.assertNotIn("running_at", final)


if __name__ == "__main__":
    unittest.main()
