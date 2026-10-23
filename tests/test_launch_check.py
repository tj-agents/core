"""Launch check fixtures: a fake event server and fake CLIs; no network, plugin cache or real profile."""

import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/machine/scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECK = load("launch_check")
import setup_machine as SETUP  # noqa: E402
TOPIC = "t" * 40


def hint(identifier, repository):
    return {"id": identifier, "event": "message", "message": json.dumps({"v": 1, "repo": repository})}


class Server:
    """Answers each poll with the messages after `since`, like ntfy's cache."""

    def __init__(self, messages=(), error=None):
        self.messages = list(messages)
        self.error = error
        self.paths = []

    def __call__(self, path):
        self.paths.append(path)
        if self.error:
            raise self.error
        since = path.rsplit("since=", 1)[1]
        identifiers = [message["id"] for message in self.messages]
        start = identifiers.index(since) + 1 if since in identifiers else 0
        return b"".join(json.dumps(message).encode() + b"\n" for message in self.messages[start:])


class LaunchCheckTests(unittest.TestCase):
    def test_shell_admission_refuses_unverifiable_codex_override_before_optional_updates(self):
        selection = self.state / ".agents/plugins.json"
        selection.parent.mkdir()
        selection.write_text('{"schema_version":1,"plugins":["base@tj-agents"]}', encoding="utf-8")
        with mock.patch.object(CHECK, "check") as optional, mock.patch.object(sys, "stderr", io.StringIO()):
            self.assertEqual(1, CHECK.main([
                "--host", "codex", "--project", str(self.state), "--target", "native-cli",
                "--", "--profile=alternate",
            ]))
        optional.assert_not_called()

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="launch check ")
        self.addCleanup(temp.cleanup)
        self.state = Path(temp.name)
        patcher = mock.patch.dict(os.environ, {"AGENT_STATE_DIRECTORY": str(self.state),
                                               "CLAUDE_CONFIG_DIR": str(self.state / "claude")})
        patcher.start()
        self.addCleanup(patcher.stop)
        (self.state / "machine-events.json").write_text(json.dumps({"topic": TOPIC}), encoding="utf-8")
        self.cursor = self.state / "machine-events-cursor.json"
        self.updates = []

    def update(self, outcomes=None):
        def run(host, repositories, project):
            self.updates.append((host, frozenset(repositories) if repositories is not None else None))
            return (outcomes or {}).get(host, True)
        return run

    def saved(self):
        return json.loads(self.cursor.read_text(encoding="utf-8"))

    def test_no_event_polls_once_and_starts_no_process(self):
        server = Server()
        self.cursor.write_text(json.dumps({"since": "abc"}), encoding="utf-8")
        with mock.patch.object(subprocess, "Popen", side_effect=AssertionError("subprocess")) as popen, \
                mock.patch.object(subprocess, "run", side_effect=AssertionError("subprocess")):
            self.assertEqual("current", CHECK.check(ROOT, fetch=server, update=self.update()))
        self.assertEqual([f"/{TOPIC}/json?poll=1&since=abc"], server.paths)
        popen.assert_not_called()
        self.assertEqual([], self.updates)
        self.assertEqual({"since": "abc"}, self.saved())

    def test_a_launch_without_events_updates_only_what_the_install_check_finds_behind(self):
        self.cursor.write_text(json.dumps({"since": "abc"}), encoding="utf-8")
        for outcome, expected in ((["dotnet@tj-agents"], "updated"), ([], "current"), (RuntimeError("cli"), "failed")):
            seen = []

            def reconcile(project, outcome=outcome):
                seen.append(project)
                if isinstance(outcome, Exception):
                    raise outcome
                return outcome
            with self.subTest(outcome=outcome), mock.patch.object(sys, "stderr", io.StringIO()):
                self.assertEqual(expected, CHECK.check(ROOT, fetch=Server(), update=self.update(), reconcile=reconcile))
                self.assertEqual([ROOT], seen)
        self.assertEqual({"since": "abc"}, self.saved())

    def test_the_install_check_waits_for_a_launch_already_applying_events(self):
        import plugin_autoupdate

        held = plugin_autoupdate.acquire_lock(self.state / "launch-check.lock")
        self.addCleanup(held.close)
        self.assertEqual("busy", CHECK.check(ROOT, fetch=Server(), update=self.update(),
                                             reconcile=lambda project: self.fail("ran while locked")))

    def test_a_codex_launch_leaves_claude_installs_alone(self):
        self.cursor.write_text(json.dumps({"since": "abc"}), encoding="utf-8")
        for value, host in (("codex", "codex"), (" Codex ", "codex"), ("cursor", None)):
            with self.subTest(value=value), mock.patch.object(CHECK, "check") as check,                     mock.patch.dict(os.environ, {CHECK.HOST_VARIABLE: value}):
                self.assertEqual(0, CHECK.main(["--project", str(ROOT)]))
                self.assertEqual(host, check.call_args.kwargs["host"])
        self.assertEqual("current", CHECK.check(ROOT, fetch=Server(), update=self.update(), host="codex",
                                                reconcile=lambda project: self.fail("checked Claude installs")))
        self.assertEqual("updated", CHECK.check(ROOT, fetch=Server(), update=self.update(), host="claude",
                                                reconcile=lambda project: ["base@tj-agents"]))

    def test_an_unconfigured_machine_never_polls(self):
        (self.state / "machine-events.json").unlink()
        server = Server()
        self.assertEqual("unconfigured", CHECK.check(ROOT, fetch=server, update=self.update()))
        self.assertEqual([], server.paths)

    def test_offline_starts_anyway_with_one_line_and_keeps_the_cursor(self):
        self.cursor.write_text(json.dumps({"since": "abc"}), encoding="utf-8")
        stderr = io.StringIO()
        with mock.patch.object(sys, "stderr", stderr):
            result = CHECK.check(ROOT, fetch=Server(error=OSError("offline")), update=self.update())
        self.assertEqual("offline", result)
        self.assertEqual(1, len(stderr.getvalue().splitlines()))
        self.assertEqual({"since": "abc"}, self.saved())
        self.assertEqual([], self.updates)

    def test_events_update_only_the_named_repositories_on_both_hosts(self):
        server = Server([hint("m1", "tj-agents/core"), {"id": "m2", "event": "message", "message": "noise"},
                         hint("m3", "Concertable/Agents"), hint("m4", "other/repo")])
        with mock.patch.object(sys, "stderr", io.StringIO()):
            self.assertEqual("updated", CHECK.check(ROOT, fetch=server, update=self.update(), now=1234))
        named = frozenset({"tj-agents/core", "concertable/agents"})
        self.assertEqual({("claude", named), ("codex", named)}, set(self.updates))
        self.assertEqual({"since": "m4", "since_at": 1234}, self.saved())
        self.assertIn("since=all", server.paths[0])

    def test_events_for_repositories_without_plugins_only_advance_the_cursor(self):
        server = Server([{"id": "m1", "event": "message", "message": "{}"}])
        self.assertEqual("current", CHECK.check(ROOT, fetch=server, update=self.update(), now=1234))
        self.assertEqual([], self.updates)
        self.assertEqual({"since": "m1", "since_at": 1234}, self.saved())

    def test_the_cursor_advances_only_after_every_host_succeeds(self):
        server = Server([hint("m1", "tj-agents/core")])
        with mock.patch.object(sys, "stderr", io.StringIO()):
            self.assertEqual("failed", CHECK.check(ROOT, fetch=server, update=self.update({"codex": False}),
                                                   now=1000))
        self.assertEqual("all", self.saved()["since"])
        self.assertEqual({"applied": "m1"}, self.saved()["hosts"]["claude"])
        self.assertEqual({"applied": None}, self.saved()["hosts"]["codex"])

        self.updates.clear()
        with mock.patch.object(sys, "stderr", io.StringIO()):
            self.assertEqual("updated", CHECK.check(ROOT, fetch=server, update=self.update(), now=1001))
        self.assertEqual([("codex", frozenset({"tj-agents/core"}))], self.updates)
        self.assertEqual({"since": "m1", "since_at": 1001}, self.saved())

        self.updates.clear()
        server.messages.append(hint("m2", "tj-agents/kit"))
        with mock.patch.object(sys, "stderr", io.StringIO()):
            self.assertEqual("updated", CHECK.check(ROOT, fetch=server, update=self.update(), now=1200))
        self.assertEqual({("claude", frozenset({"tj-agents/kit"})),
                          ("codex", frozenset({"tj-agents/kit"}))}, set(self.updates))
        self.assertEqual({"since": "m2", "since_at": 1200}, self.saved())

    def test_a_failed_host_is_retried_on_the_very_next_check(self):
        server = Server([hint("m1", "tj-agents/core")])
        with mock.patch.object(sys, "stderr", io.StringIO()):
            CHECK.check(ROOT, fetch=server, update=self.update({"claude": False}), now=1000)
            self.updates.clear()
            self.assertEqual("updated", CHECK.check(ROOT, fetch=server, update=self.update(), now=1000))
        self.assertEqual([("claude", frozenset({"tj-agents/core"}))], self.updates)
        self.assertEqual({"since": "m1", "since_at": 1000}, self.saved())

    def test_an_expired_cursor_falls_back_to_a_full_comparison_on_both_hosts(self):
        self.cursor.write_text(json.dumps({"since": "old", "since_at": 0}), encoding="utf-8")
        server = Server([hint("old", "tj-agents/kit"), hint("new", "tj-agents/core")])
        with mock.patch.object(sys, "stderr", io.StringIO()):
            self.assertEqual("updated", CHECK.check(ROOT, fetch=server, update=self.update(),
                                                    now=CHECK.EXPIRY_SECONDS + 1))
        self.assertEqual({("claude", None), ("codex", None)}, set(self.updates))
        self.assertIn("since=all", server.paths[0])
        self.assertEqual({"since": "new", "since_at": CHECK.EXPIRY_SECONDS + 1}, self.saved())

    def test_a_cursor_within_the_expiry_window_polls_only_since_the_recorded_event(self):
        self.cursor.write_text(json.dumps({"since": "old", "since_at": 1000}), encoding="utf-8")
        server = Server([hint("old", "tj-agents/kit"), hint("new", "tj-agents/core")])
        with mock.patch.object(sys, "stderr", io.StringIO()):
            self.assertEqual("updated", CHECK.check(ROOT, fetch=server, update=self.update(),
                                                    now=1000 + CHECK.EXPIRY_SECONDS))
        self.assertEqual({("claude", frozenset({"tj-agents/core"})),
                          ("codex", frozenset({"tj-agents/core"}))}, set(self.updates))
        self.assertIn("since=old", server.paths[0])

    def test_a_concurrent_check_leaves_the_events_to_the_one_holding_the_lock(self):
        import plugin_autoupdate

        held = plugin_autoupdate.acquire_lock(self.state / "launch-check.lock")
        self.addCleanup(held.close)
        self.assertEqual("busy", CHECK.check(ROOT, fetch=Server([hint("m1", "tj-agents/core")]),
                                             update=self.update()))
        self.assertEqual([], self.updates)
        self.assertFalse(self.cursor.exists())

    def test_codex_updates_go_through_the_repository_filtered_updater(self):
        import plugin_autoupdate

        with mock.patch.object(plugin_autoupdate, "main", return_value=0) as main:
            self.assertTrue(CHECK.update_host("codex", {"tj-agents/kit", "tj-agents/core"}, ROOT))
        self.assertEqual(["--no-sweep", "--no-self-update", "--retry-failures", "--repository", "tj-agents/core",
                          "--repository", "tj-agents/kit"], main.call_args.args[0])
        with mock.patch.object(plugin_autoupdate, "main", side_effect=RuntimeError("broken")), \
                mock.patch.object(sys, "stderr", io.StringIO()):
            self.assertFalse(CHECK.update_host("codex", {"tj-agents/core"}, ROOT))

    def test_setup_marks_the_newest_event_current(self):
        server = Server([hint("m1", "tj-agents/core"), hint("m2", "tj-agents/kit")])
        self.assertTrue(CHECK.mark_current(fetch=server, now=1234))
        self.assertEqual({"since": "m2", "since_at": 1234}, self.saved())


@unittest.skipUnless(shutil.which("pwsh"), "PowerShell 7 is not installed")
class TerminalFunctionTests(unittest.TestCase):
    def test_powershell_functions_check_first_then_pass_arguments_and_exit_code_through(self):
        with tempfile.TemporaryDirectory(prefix="terminal ") as temp:
            directory = Path(temp)
            log = directory / "log.jsonl"
            check = directory / "launch_check.py"
            check.write_text(f"import os, sys\nopen({str(log)!r}, 'a').write(' '.join(['check', *sys.argv[1:], "
                             f"os.environ.get({CHECK.HOST_VARIABLE!r}, '')]) + '\\n')\n", encoding="utf-8")
            echo = directory / "echo.py"
            echo.write_text(f"import json, sys\nopen({str(log)!r}, 'a').write(json.dumps(sys.argv[1:]) + '\\n')\n"
                            "raise SystemExit(7)\n", encoding="utf-8")
            bin_directory = directory / "bin"
            bin_directory.mkdir()
            for name in ("claude", "codex"):
                if os.name == "nt":
                    (bin_directory / f"{name}.cmd").write_text(
                        f'@"{sys.executable}" "{echo}" %*\r\n@exit /b %ERRORLEVEL%\r\n', encoding="utf-8")
                else:
                    target = bin_directory / name
                    target.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{echo}" "$@"\n', encoding="utf-8")
                    target.chmod(0o755)
            profile = directory / "profile.ps1"
            SETUP.install_shell_profiles([profile], sys.executable, check)
            for name in ("claude", "codex"):
                with self.subTest(name=name):
                    log.unlink(missing_ok=True)
                    result = subprocess.run(
                        ["pwsh", "-NoProfile", "-NonInteractive", "-Command",
                         f". '{profile}'; {name} 'two words' --flag; exit $LASTEXITCODE"],
                        env=dict(os.environ, PATH=str(bin_directory) + os.pathsep + os.environ["PATH"]),
                        capture_output=True, text=True, timeout=60)
                    self.assertEqual(7, result.returncode, result.stderr)
                    target = bin_directory / (f"{name}.cmd" if os.name == "nt" else name)
                    self.assertEqual([f"check --host {name} --target {target} -- two words --flag {name}", json.dumps(["two words", "--flag"])],
                                     log.read_text(encoding="utf-8").splitlines())
                    previous = log.read_text(encoding="utf-8")
                    check.write_text("raise SystemExit(2)\n", encoding="utf-8")
                    blocked = subprocess.run(
                        ["pwsh", "-NoProfile", "-NonInteractive", "-Command",
                         f". '{profile}'; {name} 'two words' --flag; exit $LASTEXITCODE"],
                        env=dict(os.environ, PATH=str(bin_directory) + os.pathsep + os.environ["PATH"]),
                        capture_output=True, text=True, timeout=60)
                    self.assertEqual(2, blocked.returncode, blocked.stderr)
                    self.assertEqual(previous, log.read_text(encoding="utf-8"))
                    check.write_text(f"import os, sys\nopen({str(log)!r}, 'a').write(' '.join(['check', *sys.argv[1:], "
                                     f"os.environ.get({CHECK.HOST_VARIABLE!r}, '')]) + '\\n')\n", encoding="utf-8")


@unittest.skipIf(os.name == "nt" or not shutil.which("bash"), "POSIX bash is required")
class PosixFunctionTests(unittest.TestCase):
    def test_bash_functions_check_first_then_pass_arguments_and_exit_code_through(self):
        with tempfile.TemporaryDirectory(prefix="terminal ") as temp:
            directory = Path(temp)
            log = directory / "log"
            check = directory / "launch_check.py"
            check.write_text(f"import os, sys\nopen({str(log)!r}, 'a').write(' '.join(['check', *sys.argv[1:], "
                             f"os.environ.get({CHECK.HOST_VARIABLE!r}, '')]) + '\\n')\n", encoding="utf-8")
            bin_directory = directory / "bin"
            bin_directory.mkdir()
            target = bin_directory / "claude"
            target.write_text(f'#!/bin/sh\nprintf "%s|" "$@" >> "{log}"\nexit 7\n', encoding="utf-8")
            target.chmod(0o755)
            rc = directory / ".bashrc"
            SETUP.install_shell_profiles([rc], sys.executable, check)
            result = subprocess.run(["bash", "-c", f". '{rc}'; claude 'two words' --flag"],
                                    env=dict(os.environ, PATH=str(bin_directory) + os.pathsep + os.environ["PATH"]),
                                    capture_output=True, text=True, timeout=60)
            self.assertEqual(7, result.returncode, result.stderr)
            self.assertEqual(f"check --host claude --target {target} -- two words --flag claude\ntwo words|--flag|", log.read_text(encoding="utf-8"))
            previous = log.read_text(encoding="utf-8")
            check.write_text("raise SystemExit(2)\n", encoding="utf-8")
            blocked = subprocess.run(["bash", "-c", f". '{rc}'; claude 'two words' --flag"],
                                     env=dict(os.environ, PATH=str(bin_directory) + os.pathsep + os.environ["PATH"]),
                                     capture_output=True, text=True, timeout=60)
            self.assertEqual(2, blocked.returncode, blocked.stderr)
            self.assertEqual(previous, log.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
