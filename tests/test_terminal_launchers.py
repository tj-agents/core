"""Focused command-dispatch and profile-adapter checks for terminal launchers."""

from __future__ import annotations

import contextlib
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
SCRIPTS = ROOT / ".agents" / "machine" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


CLAUDE = module("claude_terminal_launcher")
CODEX = module("codex_terminal_launcher")
SYNC = module("codex_marketplace_sync")
COMMAND = module("terminal_command")
PROFILE = module("claude_terminal_profile")
CODEX_PROFILE = module("codex_terminal_profile")


class TerminalLaunchersTests(unittest.TestCase):
    def test_codex_disables_daemon_for_windows_interactive_sessions(self):
        cases = (
            ([], ["--no-daemon"]),
            (["resume", "--last"], ["--no-daemon", "resume", "--last"]),
            (["fork", "--last"], ["--no-daemon", "fork", "--last"]),
            (["prompt with spaces"], ["--no-daemon", "prompt with spaces"]),
            (["-C", "project", "prompt"], ["--no-daemon", "-C", "project", "prompt"]),
            (["plugin", "list"], ["plugin", "list"]),
            (["-C", "project", "plugin", "list"], ["-C", "project", "plugin", "list"]),
            (["--config", "model=default", "exec"], ["--config", "model=default", "exec"]),
            (["exec", "--json"], ["exec", "--json"]),
            (["--help"], ["--help"]),
            (["--remote", "ws://127.0.0.1:8080"], ["--remote", "ws://127.0.0.1:8080"]),
            (["--remote=ws://127.0.0.1:8080"], ["--remote=ws://127.0.0.1:8080"]),
            (["--no-daemon", "resume"], ["--no-daemon", "resume"]),
        )
        with mock.patch.object(CODEX.sys, "platform", "win32"):
            for arguments, expected in cases:
                with self.subTest(arguments=arguments):
                    self.assertEqual(expected, CODEX.without_daemon_for_interactive(arguments))
        with mock.patch.object(CODEX.sys, "platform", "linux"):
            self.assertEqual(["resume"], CODEX.without_daemon_for_interactive(["resume"]))

    def test_codex_only_disables_a_daemon_when_the_installed_cli_supports_it(self):
        with mock.patch.object(CODEX.sys, "platform", "win32"), \
                mock.patch.object(CODEX, "supports_no_daemon", return_value=False):
            self.assertEqual(["resume"], CODEX.without_daemon_for_interactive(["resume"], "codex"))
        with mock.patch.object(CODEX.sys, "platform", "win32"), \
                mock.patch.object(CODEX, "supports_no_daemon", return_value=True):
            self.assertEqual(["--no-daemon", "resume"], CODEX.without_daemon_for_interactive(["resume"], "codex"))

    def test_codex_help_capability_probe(self):
        with mock.patch.object(CODEX, "command_for_target", return_value=["native-codex", "--help"]), \
                mock.patch.object(CODEX.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "  --no-daemon\n", "")):
            self.assertTrue(CODEX.supports_no_daemon("codex.cmd"))
        with mock.patch.object(CODEX, "command_for_target", return_value=["native-codex", "--help"]), \
                mock.patch.object(CODEX.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "older CLI", "")):
            self.assertFalse(CODEX.supports_no_daemon("codex.cmd"))
        with mock.patch.object(CODEX, "command_for_target", side_effect=COMMAND.agent_cli.LaunchError("native missing")):
            self.assertFalse(CODEX.supports_no_daemon("codex.cmd"))

    def test_typed_hook_option_reaches_the_cli_argument_list(self):
        with tempfile.TemporaryDirectory(prefix="literal terminal option ") as directory:
            root = Path(directory)
            cache = root / "cache"
            cache.mkdir()
            package = cache / "tj-agents" / "machine" / "current"
            launcher = package / "resources/machine/scripts/claude_terminal_launcher.py"
            launcher.parent.mkdir(parents=True)
            (package / "catalog").mkdir()
            (package / "catalog" / "catalog.json").write_text("{}", encoding="utf-8")
            launcher.write_text("import json, sys\nprint(json.dumps(sys.argv[1:]))\n", encoding="utf-8")
            (cache / "installed_plugins.json").write_text(json.dumps({"plugins": {
                "machine@tj-agents": [{"scope": "user", "installPath": str(package)}]
            }}), encoding="utf-8")
            (cache / "known_marketplaces.json").write_text(json.dumps({
                "tj-agents": {"source": {"repo": "tj-agents/marketplace"}},
            }), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-B", "-c", PROFILE.BOOTSTRAP, "claude", "typed-cli", directory, "--hooks"],
                env=dict(os.environ, CLAUDE_CODE_PLUGIN_CACHE_DIR=str(cache)),
                text=True, encoding="utf-8", capture_output=True, check=False,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["--", "--hooks"], json.loads(result.stdout)[-2:])

    def test_claude_exempts_non_sessions_and_binds_bare_sessions(self):
        with mock.patch.object(CLAUDE, "run_session", return_value=17) as session, \
                mock.patch.object(CLAUDE, "run_target", return_value=17) as run, \
                mock.patch.object(CLAUDE, "claude_label", return_value="repo/topic"):
            self.assertEqual(17, CLAUDE.main(["--project", "/work", "--target", "claude", "plugin", "list"]))
            session.assert_not_called()
            run.assert_called_once_with("claude", ["plugin", "list"])
            run.reset_mock()
            self.assertEqual(17, CLAUDE.main(["--project", "/work", "--target", "claude", "--", "--help"]))
            session.assert_not_called()
            run.assert_called_once_with("claude", ["--help"])
            run.reset_mock()
            self.assertEqual(17, CLAUDE.main(["--project", "/work", "--target", "claude"]))
            session.assert_called_once_with("claude", "claude", Path("/work"), ["-n", "repo/topic"], on_launch=mock.ANY,
                                            keep_unacknowledged_session=True)
            run.assert_not_called()

    def test_claude_binds_the_typed_shim_in_the_child_session(self):
        for suffix in (".cmd", ".ps1"):
            with self.subTest(suffix=suffix), \
                    mock.patch.object(CLAUDE, "run_session", return_value=0) as session:
                target = "C:/npm/claude" + suffix
                self.assertEqual(0, CLAUDE.main(["--project", "/work", "--target", target, "chat"]))
                session.assert_called_once_with("claude", target, Path("/work"), ["chat"], on_launch=mock.ANY,
                                            keep_unacknowledged_session=True)

    def test_claude_refresh_failure_falls_back_to_the_typed_cli(self):
        buffer = io.StringIO()
        with mock.patch.object(CLAUDE, "run_session", side_effect=CLAUDE.StartupBindingError("offline")) as session, \
                mock.patch.object(CLAUDE, "run_target", return_value=23) as run, \
                mock.patch.dict(os.environ, {"TJ_AGENTS_STARTUP_SNAPSHOT_DIRECTORY": "parent"}), \
                contextlib.redirect_stderr(buffer):
            self.assertEqual(23, CLAUDE.main(["--project", "/work", "--target", "claude", "chat"]))
        session.assert_called_once()
        run.assert_called_once_with("claude", ["chat"], mock.ANY)
        self.assertNotIn("TJ_AGENTS_STARTUP_SNAPSHOT_DIRECTORY", run.call_args.args[2])
        self.assertIn("starting Claude without the standards refresh", buffer.getvalue())

    def test_claude_successful_session_does_not_run_the_typed_cli_again(self):
        with mock.patch.object(CLAUDE, "run_session", return_value=0) as session, \
                mock.patch.object(CLAUDE, "run_target") as run:
            self.assertEqual(0, CLAUDE.main(["--project", "/work", "--target", "claude", "chat"]))
        session.assert_called_once()
        run.assert_not_called()

    def test_codex_binds_the_typed_shim_and_args_in_the_child_session(self):
        special = ["exec", "space arg", "café", 'quote"arg']
        with mock.patch.object(CODEX, "run_session", return_value=23) as session, \
                mock.patch.object(CODEX, "without_daemon_for_interactive", side_effect=lambda values, *_: values):
            self.assertEqual(23, CODEX.main(["--project", "/work", "--target", "C:/npm/codex.cmd", *special]))
            session.assert_called_once_with("codex", "C:/npm/codex.cmd", Path("/work"), special, on_launch=mock.ANY,
                                            keep_unacknowledged_session=True)

    def test_codex_maintenance_commands_bypass_refresh_and_session_commands_fall_back(self):
        buffer = io.StringIO()
        with mock.patch.object(CODEX, "run_session", side_effect=CODEX.StartupBindingError("bad registry")) as session, \
                mock.patch.object(CODEX, "run_target", return_value=9) as run, \
                contextlib.redirect_stderr(buffer):
            self.assertEqual(9, CODEX.main(["--project", "/work", "--target", "codex", "plugin", "list"]))
            session.assert_not_called()
            self.assertEqual(9, CODEX.main(["--project", "/work", "--target", "codex", "--", "--version"]))
            self.assertEqual(9, CODEX.main(["--project", "/work", "--target", "codex", "--", "--help"]))
            for command in (["exec"], ["review"], ["exec", "--version"]):
                with self.subTest(command=command):
                    self.assertEqual(9, CODEX.main(["--project", "/work", "--target", "codex", *command]))
            self.assertEqual(session.call_count, 3)
            self.assertEqual(run.call_count, 6)
        self.assertIn("starting Codex without the standards refresh", buffer.getvalue())

    def test_codex_successful_session_does_not_run_the_typed_cli_again(self):
        with mock.patch.object(CODEX, "run_session", return_value=0) as session, \
                mock.patch.object(CODEX, "run_target") as run:
            self.assertEqual(0, CODEX.main(["--project", "/work", "--target", "codex", "exec"]))
        session.assert_called_once()
        run.assert_not_called()

    def test_codex_launcher_binds_session_commands_and_routes_hook_control(self):
        events = []
        with mock.patch.object(CODEX, "run_session", side_effect=lambda host, target, project, arguments, **_options: events.append(("session", arguments)) or 41), \
                mock.patch.object(CODEX, "run_target", side_effect=lambda target, arguments: events.append(("cli", arguments)) or 41), \
                mock.patch.object(CODEX, "hook_control", side_effect=lambda arguments: events.append(("hooks", arguments)) or 42):
            self.assertEqual(41, CODEX.main(["--project", "/work", "--target", "codex", "exec", "--json"]))
            self.assertEqual([("session", ["exec", "--json"])], events)
            events.clear()
            self.assertEqual(41, CODEX.main(["--project", "/work", "--target", "codex", "plugin", "list"]))
            self.assertEqual([("cli", ["plugin", "list"])], events)
            events.clear()
            self.assertEqual(42, CODEX.main(["--project", "/work", "--target", "codex", "--hooks", "status"]))
            self.assertEqual([("hooks", ["status"])], events)

    def test_codex_error_after_the_session_started_does_not_launch_again(self):
        def started_then_failed(host, target, project, arguments, **options):
            options["on_launch"]()
            raise CODEX.StartupBindingError("unlock failed")

        with mock.patch.object(CODEX, "run_session", side_effect=started_then_failed),                 mock.patch.object(CODEX, "run_target") as target,                 mock.patch("sys.stderr", new_callable=io.StringIO) as stderr:
            self.assertEqual(1, CODEX.main(["--project", "/work", "--target", "codex", "resume", "id"]))
        target.assert_not_called()
        self.assertIn("session ended with a standards error: unlock failed", stderr.getvalue())

    def test_claude_error_after_the_session_started_does_not_launch_again(self):
        def started_then_failed(host, target, project, arguments, **options):
            options["on_launch"]()
            raise CLAUDE.StartupBindingError("unlock failed")

        with mock.patch.object(CLAUDE, "run_session", side_effect=started_then_failed),                 mock.patch.object(CLAUDE, "run_target") as target,                 mock.patch("sys.stderr", new_callable=io.StringIO) as stderr:
            self.assertEqual(1, CLAUDE.main(["--project", "/work", "--target", "claude", "chat"]))
        target.assert_not_called()
        self.assertIn("session ended with a standards error: unlock failed", stderr.getvalue())

    def test_hook_control_missing_dependency_fails_closed(self):
        with mock.patch.object(CODEX.Path, "is_file", return_value=False):
            self.assertEqual(1, CODEX.hook_control(["status"]))

    def test_shim_resolution_uses_agent_cli_native_executable(self):
        agent_cli = mock.Mock()
        agent_cli.resolve_codex_executable.return_value = ("/native/codex", {"text": "0.1"})
        agent_cli.LaunchError = RuntimeError
        with mock.patch.object(SYNC, "is_codex_shim", return_value=True), \
                mock.patch.object(SYNC, "_load_agent_cli", return_value=agent_cli):
            self.assertEqual("/native/codex", SYNC.resolve_codex_for_sync("C:/npm/codex.cmd"))
        agent_cli.resolve_codex_executable.assert_called_once_with()

    def test_target_stdio_arguments_and_exit_status_are_unchanged(self):
        with tempfile.TemporaryDirectory(prefix="terminal args ") as directory:
            recorder = Path(directory) / "record.py"
            recorder.write_text(
                "import json, sys\nprint('stdout:' + json.dumps(sys.argv[1:], ensure_ascii=False))\nsys.exit(19)\n",
                encoding="utf-8",
            )
            dispatch = (
                "import sys; sys.path.insert(0, " + repr(str(SCRIPTS)) + "); "
                "from terminal_command import run_target; "
                "raise SystemExit(run_target(" + repr(sys.executable) + ", "
                + repr([str(recorder), "a b", "café", 'd"e']) + "))"
            )
            completed = subprocess.run([sys.executable, "-B", "-c", dispatch], text=True,
                                       capture_output=True, check=False)
        self.assertEqual(19, completed.returncode)
        self.assertEqual('stdout:["a b", "café", "d\\"e"]\n', completed.stdout)
        self.assertEqual("", completed.stderr)

    def test_windows_batch_shims_resolve_native_executables_without_cmd(self):
        arguments = ["x&echo injected", "%USERPROFILE%", "café", 'quote"arg']
        with mock.patch.object(COMMAND.os, "name", "nt"), \
                mock.patch.object(COMMAND.agent_cli, "resolve_claude_executable", return_value="C:/native/claude.exe") as claude, \
                mock.patch.object(COMMAND.agent_cli, "resolve_codex_executable", return_value=("C:/native/codex.exe", {})) as codex:
            claude_command = COMMAND.command_for_target(r"C:\\npm\\claude.cmd", arguments)
            codex_command = COMMAND.command_for_target(r"C:\\npm\\codex.bat", arguments)
        self.assertEqual(["C:/native/claude.exe", *arguments], claude_command)
        self.assertEqual(["C:/native/codex.exe", *arguments], codex_command)
        self.assertNotIn("cmd.exe", [part.casefold() for part in [*claude_command, *codex_command]])
        claude.assert_called_once_with()
        codex.assert_called_once_with()

    def test_windows_supported_powershell_shims_use_native_without_powershell(self):
        arguments = ['quote"arg', '', 'a b', 'café', '%USERPROFILE%', 'x&echo injected']
        with mock.patch.object(COMMAND.os, "name", "nt"), \
                mock.patch.object(COMMAND.agent_cli, "resolve_claude_executable", return_value="C:/native/claude.exe"), \
                mock.patch.object(COMMAND.agent_cli, "resolve_codex_executable", return_value=("C:/native/codex.exe", {})), \
                mock.patch.object(COMMAND.shutil, "which", side_effect=AssertionError("PowerShell must not be needed")):
            self.assertEqual(["C:/native/claude.exe", *arguments], COMMAND.command_for_target("C:/npm/claude.ps1", arguments))
            self.assertEqual(["C:/native/codex.exe", *arguments], COMMAND.command_for_target("C:/npm/codex.ps1", arguments))

    def test_windows_unknown_batch_launcher_fails_without_cmd(self):
        with mock.patch.object(COMMAND.os, "name", "nt"):
            with self.assertRaisesRegex(OSError, "unsupported batch launcher"):
                COMMAND.command_for_target(r"C:\\npm\\other.cmd", ["x&echo injected"])

    @unittest.skipUnless(os.name == "nt", "PowerShell script dispatch is Windows-specific")
    def test_windows_powershell_script_target_preserves_literal_arguments(self):
        with tempfile.TemporaryDirectory(prefix="terminal ps args ") as directory:
            target = Path(directory) / "record.ps1"
            target.write_text("@($args) | ConvertTo-Json -Compress\nexit 29\n", encoding="utf-8")
            arguments = ["x&echo injected", "%USERPROFILE%", "a b", "café"]
            dispatch = (
                "import sys; sys.path.insert(0, " + repr(str(SCRIPTS)) + "); "
                "from terminal_command import run_target; "
                "raise SystemExit(run_target(" + repr(str(target)) + ", " + repr(arguments) + "))"
            )
            completed = subprocess.run([sys.executable, "-B", "-c", dispatch], text=True,
                                       encoding="utf-8", capture_output=True, check=False)
        self.assertEqual(29, completed.returncode)
        self.assertEqual(json.dumps(arguments, ensure_ascii=False, separators=(",", ":")) + "\n", completed.stdout)

    @unittest.skipIf(os.name == "nt", "Bash adapter integration runs on Linux")
    def test_bash_set_eu_bare_command_falls_back_when_the_registry_is_missing(self):
        if shutil.which("bash") is None:
            self.skipTest("Bash is unavailable")
        with tempfile.TemporaryDirectory(prefix="terminal bash ") as directory:
            root = Path(directory)
            home, bin_dir = root / "home", root / "bin"
            calls = root / "calls"
            bin_dir.mkdir()
            cli = bin_dir / "claude"
            cli.write_text("#!/usr/bin/env bash\nprintf 'typed:%s\\n' \"$#\"\nprintf 'cli\\n' >> \"$CALLS\"\n", encoding="utf-8")
            cli.chmod(cli.stat().st_mode | 0o111)
            profile = home / ".bashrc"
            profile.parent.mkdir()
            profile.write_text(PROFILE.BASH_BLOCK, encoding="utf-8")
            env = dict(os.environ, HOME=str(home), PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}", CALLS=str(calls),
                       CLAUDE_CODE_PLUGIN_CACHE_DIR=str(root / "missing"))
            result = subprocess.run(["bash", "--noprofile", "--norc", "-c", f"set -eu; . '{profile}'; claude"],
                                    env=env, text=True, capture_output=True, check=False)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("typed:0\n", result.stdout)
            self.assertEqual("cli\n", calls.read_text(encoding="utf-8"))
            self.assertIn("registry could not be read", result.stderr)
            self.assertIn("starting Claude without the standards refresh", result.stderr)

    def test_bootstrap_warns_for_malformed_registry_shapes(self):
        with tempfile.TemporaryDirectory(prefix="terminal registry ") as directory:
            registry = Path(directory) / "installed_plugins.json"
            (Path(directory) / "known_marketplaces.json").write_text(json.dumps({
                "tj-agents": {"source": {"repo": "tj-agents/marketplace"}},
            }), encoding="utf-8")
            for value in ("{not json", json.dumps([]), json.dumps(None),
                          json.dumps({"plugins": None}),
                          json.dumps({"plugins": {"machine@tj-agents": None}}),
                          json.dumps({"plugins": {"machine@tj-agents": [None]}})):
                registry.write_text(value, encoding="utf-8")
                env = dict(os.environ, CLAUDE_CODE_PLUGIN_CACHE_DIR=str(Path(directory)))
                result = subprocess.run(
                    [sys.executable, "-B", "-c", PROFILE.BOOTSTRAP, "claude", "/bin/true", directory],
                    env=env, text=True, capture_output=True, check=False,
                )
                self.assertEqual(125, result.returncode)
                self.assertIn("registry is malformed", result.stderr)

    @unittest.skipIf(os.name == "nt", "Bash adapter integration runs on Linux")
    def test_bash_falls_back_without_a_usable_python(self):
        if shutil.which("bash") is None:
            self.skipTest("Bash is unavailable")
        with tempfile.TemporaryDirectory(prefix="terminal no python ") as directory:
            root = Path(directory)
            home, bin_dir = root / "home", root / "bin"
            bin_dir.mkdir()
            cli = bin_dir / "claude"
            cli.write_text("#!/bin/sh\nprintf 'fallback\\n'\n", encoding="utf-8")
            cli.chmod(cli.stat().st_mode | 0o111)
            profile = home / ".bashrc"
            profile.parent.mkdir()
            profile.write_text(PROFILE.BASH_BLOCK, encoding="utf-8")
            result = subprocess.run(["/bin/bash", "--noprofile", "--norc", "-c", f". '{profile}'; claude"],
                                    env=dict(os.environ, HOME=str(home), PATH=str(bin_dir)),
                                    text=True, capture_output=True, check=False)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("fallback\n", result.stdout)
        self.assertIn("no usable Python", result.stderr)
        self.assertIn("starting Claude without the standards refresh", result.stderr)

    @unittest.skipIf(os.name == "nt", "Bash adapter integration runs on Linux")
    def test_bash_preserves_a_real_cli_exit_125_without_a_second_launch(self):
        if shutil.which("bash") is None:
            self.skipTest("Bash is unavailable")
        with tempfile.TemporaryDirectory(prefix="terminal status ") as directory:
            root = Path(directory)
            home, bin_dir, cache = root / "home", root / "bin", root / "cache"
            bin_dir.mkdir()
            calls = root / "calls"
            cli = bin_dir / "claude"
            cli.write_text("#!/bin/sh\nprintf 'cli\\n' >> \"$CALLS\"\nexit 125\n", encoding="utf-8")
            cli.chmod(cli.stat().st_mode | 0o111)
            active = cache / "tj-agents" / "machine" / "test"
            launcher = active / "resources" / "machine" / "scripts" / "claude_terminal_launcher.py"
            launcher.parent.mkdir(parents=True)
            (active / "catalog").mkdir()
            (active / "catalog" / "catalog.json").write_text("{}", encoding="utf-8")
            launcher.write_text(
                "import argparse, subprocess\n"
                "parser = argparse.ArgumentParser(); parser.add_argument('--project'); parser.add_argument('--target'); parser.add_argument('args', nargs='*')\n"
                "parsed = parser.parse_args(); args = parsed.args[1:] if parsed.args[:1] == ['--'] else parsed.args\n"
                "raise SystemExit(subprocess.run([parsed.target, *args]).returncode)\n",
                encoding="utf-8",
            )
            (cache / "installed_plugins.json").write_text(json.dumps({"plugins": {"machine@tj-agents": [{"scope": "user", "installPath": str(active)}]}}), encoding="utf-8")
            (cache / "known_marketplaces.json").write_text(json.dumps({
                "tj-agents": {"source": {"repo": "tj-agents/marketplace"}},
            }), encoding="utf-8")
            profile = home / ".bashrc"
            profile.parent.mkdir()
            profile.write_text(PROFILE.BASH_BLOCK, encoding="utf-8")
            completed = subprocess.run(["bash", "--noprofile", "--norc", "-c", f". '{profile}'; claude"],
                                       env=dict(os.environ, HOME=str(home), PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
                                                CALLS=str(calls), CLAUDE_CODE_PLUGIN_CACHE_DIR=str(cache)),
                                       text=True, capture_output=True, check=False)
            actual_calls = calls.read_text(encoding="utf-8")
        self.assertEqual(125, completed.returncode)
        self.assertEqual("cli\n", actual_calls)

    @unittest.skipIf(os.name == "nt", "Bash adapter integration runs on Linux")
    def test_bash_reads_the_active_claude_package_on_each_invocation(self):
        if shutil.which("bash") is None:
            self.skipTest("Bash is unavailable")
        with tempfile.TemporaryDirectory(prefix="terminal active package ") as directory:
            root = Path(directory)
            home, bin_dir, cache = root / "home", root / "bin", root / "cache"
            bin_dir.mkdir()
            cache.mkdir()
            calls = root / "calls"
            cli = bin_dir / "claude"
            cli.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
            cli.chmod(cli.stat().st_mode | 0o111)
            active = []
            for label in ("first", "second"):
                package = cache / "tj-agents" / "machine" / label
                launcher = package / "resources" / "machine" / "scripts" / "claude_terminal_launcher.py"
                launcher.parent.mkdir(parents=True)
                (package / "catalog").mkdir()
                (package / "catalog" / "catalog.json").write_text("{}", encoding="utf-8")
                launcher.write_text("from pathlib import Path\nimport os\nPath(os.environ['CALLS']).open('a', encoding='utf-8').write('" + label + "\\n')\n", encoding="utf-8")
                active.append(package)
            registry = cache / "installed_plugins.json"
            second = cache / "second.json"
            registry.write_text(json.dumps({"plugins": {"machine@tj-agents": [{"scope": "user", "installPath": str(active[0])}]}}), encoding="utf-8")
            second.write_text(json.dumps({"plugins": {"machine@tj-agents": [{"scope": "user", "installPath": str(active[1])}]}}), encoding="utf-8")
            (cache / "known_marketplaces.json").write_text(json.dumps({
                "tj-agents": {"source": {"repo": "tj-agents/marketplace"}},
            }), encoding="utf-8")
            profile = home / ".bashrc"
            profile.parent.mkdir()
            profile.write_text(PROFILE.BASH_BLOCK, encoding="utf-8")
            completed = subprocess.run(["bash", "--noprofile", "--norc", "-c", f". '{profile}'; claude; cp '{second}' '{registry}'; claude"],
                                       env=dict(os.environ, HOME=str(home), PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
                                                CALLS=str(calls), CLAUDE_CODE_PLUGIN_CACHE_DIR=str(cache)),
                                       text=True, capture_output=True, check=False)
            actual_calls = calls.read_text(encoding="utf-8")
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("first\nsecond\n", actual_calls)

    @unittest.skipIf(os.name == "nt", "Bash adapter integration runs on Linux")
    def test_bash_bootstraps_ignore_project_local_standard_library_shadows(self):
        if shutil.which("bash") is None:
            self.skipTest("Bash is unavailable")
        with tempfile.TemporaryDirectory(prefix="terminal isolated bootstrap ") as directory:
            root = Path(directory)
            home, bin_dir, project = root / "home", root / "bin", root / "project"
            bin_dir.mkdir()
            project.mkdir()
            for shadow in ("json.py", "subprocess.py"):
                (project / shadow).write_text("raise RuntimeError('project module was imported')\n", encoding="utf-8")
            environment = dict(os.environ, HOME=str(home), PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
            pythonpath_shadow = root / "pythonpath-shadow"
            pythonpath_shadow.mkdir()
            for shadow in ("json.py", "subprocess.py"):
                (pythonpath_shadow / shadow).write_text("raise RuntimeError('PYTHONPATH module was imported')\n", encoding="utf-8")
            environment["PYTHONPATH"] = str(pythonpath_shadow)
            for host, profile in (("claude", PROFILE), ("codex", CODEX_PROFILE)):
                cli = bin_dir / host
                if host == "claude":
                    cache = root / "claude-cache"
                    active = cache / "tj-agents" / "machine" / "test"
                    launcher = active / "resources" / "machine" / "scripts" / "claude_terminal_launcher.py"
                    launcher.parent.mkdir(parents=True)
                    (active / "catalog").mkdir()
                    (active / "catalog" / "catalog.json").write_text("{}", encoding="utf-8")
                    launcher.write_text("import json, sys\nprint(json.dumps(sys.argv[1:]))\n", encoding="utf-8")
                    cli.write_text("#!/bin/sh\nexit 88\n", encoding="utf-8")
                    cli.chmod(cli.stat().st_mode | 0o111)
                    (cache / "installed_plugins.json").write_text(json.dumps({"plugins": {
                        "machine@tj-agents": [{"scope": "user", "installPath": str(active)}]
                    }}), encoding="utf-8")
                    (cache / "known_marketplaces.json").write_text(json.dumps({
                        "tj-agents": {"source": {"repo": "tj-agents/marketplace"}},
                    }), encoding="utf-8")
                    environment["CLAUDE_CODE_PLUGIN_CACHE_DIR"] = str(cache)
                else:
                    codex_home = root / "codex-home"
                    active = codex_home / "plugins" / "cache" / "tj-agents" / "machine" / "test"
                    launcher = active / "resources" / "machine" / "scripts" / "codex_terminal_launcher.py"
                    launcher.parent.mkdir(parents=True)
                    (active / "catalog").mkdir()
                    (active / "catalog" / "catalog.json").write_text("{}", encoding="utf-8")
                    launcher.write_text("import json, sys\nprint(json.dumps(sys.argv[1:]))\n", encoding="utf-8")
                    cli.write_text(
                        "#!/bin/sh\n"
                        "if [ \"$1 $2 $3\" = \"plugin list --json\" ]; then\n"
                        "  printf '%s\\n' '{\"installed\":[{\"pluginId\":\"machine@tj-agents\",\"marketplaceName\":\"tj-agents\",\"name\":\"machine\",\"version\":\"test\",\"enabled\":true,\"marketplaceSource\":{\"sourceType\":\"git\",\"source\":{\"repo\":\"tj-agents/marketplace\"}}}]}'\n"
                        "  exit 0\n"
                        "fi\n"
                        "exit 88\n",
                        encoding="utf-8",
                    )
                    cli.chmod(cli.stat().st_mode | 0o111)
                    environment["CODEX_HOME"] = str(codex_home)
                profile_path = home / ".bashrc"
                profile_path.parent.mkdir(exist_ok=True)
                profile_path.write_text(profile.BASH_BLOCK, encoding="utf-8")
                completed = subprocess.run(
                    ["bash", "--noprofile", "--norc", "-c", f". '{profile_path}'; cd '{project}'; {host} 'a b'"],
                    env=environment, text=True, encoding="utf-8", capture_output=True, check=False,
                )
                self.assertEqual(0, completed.returncode, completed.stderr)
                self.assertIn('"a b"', completed.stdout)

    def _legacy_launcher_mains_isolate_maintenance_children_on_every_platform(self):
        with tempfile.TemporaryDirectory(prefix="terminal maintenance child isolation ") as directory:
            root = Path(directory)
            shadow = root / "hostile"
            shadow.mkdir()
            marker = root / "hostile-sitecustomize-ran"
            (shadow / "sitecustomize.py").write_text(
                "from pathlib import Path\nimport os\nPath(os.environ['HOSTILE_MARKER']).write_text('ran')\n",
                encoding="utf-8",
            )
            recorder = root / "native.py"
            recorder.write_text(
                "from pathlib import Path\nimport os\nPath(os.environ['NATIVE_PYTHONPATH']).write_text(os.environ['PYTHONPATH'])\n",
                encoding="utf-8",
            )

            for host in ("claude", "codex"):
                with self.subTest(host=host):
                    host_root = root / host
                    home = host_root / "home"
                    config = host_root / "config"
                    cache = host_root / "claude-cache"
                    codex_home = host_root / "codex-home"
                    state = host_root / "state"
                    project = host_root / "project"
                    package = host_root / "package"
                    native_environment = host_root / "native-pythonpath"
                    project.mkdir(parents=True)
                    package.mkdir()
                    (package / "harness.json").write_text(json.dumps({
                        "requires": {
                            "marketplaces": [], "plugins": [], "hooks": [],
                            "permissions": {"claude_allow": ["Bash(echo trusted)"], "codex_prefix_rules": []},
                        },
                    }), encoding="utf-8")
                    cache.mkdir(parents=True)
                    registry = {"plugins": {
                        "machine@tj-agents": [{"scope": "user", "installPath": str(package)}],
                    }}
                    for plugins in (config / "plugins", cache):
                        plugins.mkdir(parents=True, exist_ok=True)
                        (plugins / "installed_plugins.json").write_text(json.dumps(registry), encoding="utf-8")
                        (plugins / "known_marketplaces.json").write_text(json.dumps({
                            "tj-agents": {"source": {"source": "github", "repo": "tj-agents/marketplace"}},
                        }), encoding="utf-8")
                    environment = {
                        "AGENT_STATE_DIRECTORY": str(state),
                        "BASE_AGENTS_CODEX_HOOK_TRUST": "off",
                        "BASE_AGENTS_HARNESS_PERMISSIONS": "on",
                        "CLAUDE_CODE_PLUGIN_CACHE_DIR": str(cache),
                        "CLAUDE_CONFIG_DIR": str(config),
                        "CODEX_HOME": str(codex_home),
                        "HOME": str(home),
                        "HOSTILE_MARKER": str(marker),
                        "NATIVE_PYTHONPATH": str(native_environment),
                        "PYTHONPATH": str(shadow),
                        "USERPROFILE": str(home),
                    }

                    def run_native(_target, _arguments):
                        return subprocess.run(
                            [sys.executable, "-I", "-B", str(recorder)], check=False,
                        ).returncode

                    hook_trust = None
                    with mock.patch.dict(os.environ, environment):
                        if host == "claude":
                            with mock.patch.object(CLAUDE, "run_target", side_effect=run_native):
                                code = CLAUDE.main(["--project", str(project), "--target", "trusted-native", "session"])
                        else:
                            def codex_sync_command(_executable, arguments, **_kwargs):
                                if arguments == ["plugin", "marketplace", "upgrade", "--json"]:
                                    return {"errors": []}
                                if arguments == ["plugin", "list", "--available", "--json"]:
                                    return {"installed": [{
                                        "pluginId": "machine@tj-agents", "enabled": True,
                                        "marketplaceSource": {"sourceType": "git"},
                                    }], "available": []}
                                if arguments == ["plugin", "add", "machine@tj-agents", "--json"]:
                                    return {"pluginId": "machine@tj-agents"}
                                raise AssertionError(arguments)

                            hook_trust = mock.Mock(
                                wraps=CODEX.sync_codex_standards.__globals__["invoke_codex_hook_trust"],
                            )
                            with mock.patch.object(CODEX, "resolve_codex_for_sync", return_value=sys.executable), \
                                    mock.patch.object(CODEX, "run_target", side_effect=run_native), \
                                    mock.patch.dict(
                                        CODEX.sync_codex_standards.__globals__,
                                        {
                                            "invoke_codex_sync_command": codex_sync_command,
                                            "invoke_codex_hook_trust": hook_trust,
                                        },
                                    ):
                                code = CODEX.main(["--project", str(project), "--target", "trusted-native", "session"])

                    self.assertEqual(0, code)
                    if hook_trust is not None:
                        hook_trust.assert_called_once()
                    self.assertFalse(marker.exists(), marker.read_text(encoding="utf-8") if marker.exists() else "")
                    self.assertEqual(str(shadow), native_environment.read_text(encoding="utf-8"))
                    settings = json.loads((config / "settings.json").read_text(encoding="utf-8"))
                    self.assertIn("Bash(echo trusted)", settings["permissions"]["allow"])

    def test_isolated_packaged_launchers_use_only_their_script_directory(self):
        with tempfile.TemporaryDirectory(prefix="terminal launcher pythonpath ") as directory:
            shadow = Path(directory) / "shadow"
            shadow.mkdir()
            for name in ("agent_cli.py", "codex_marketplace_sync.py", "json.py", "subprocess.py", "terminal_command.py"):
                (shadow / name).write_text("raise RuntimeError('PYTHONPATH module was imported')\n", encoding="utf-8")
            environment = dict(os.environ, PYTHONPATH=str(shadow))
            for script in ("claude_terminal_launcher.py", "codex_terminal_launcher.py"):
                with self.subTest(script=script):
                    completed = subprocess.run(
                        [sys.executable, "-I", "-B", str(SCRIPTS / script), "--help"],
                        env=environment, text=True, encoding="utf-8", capture_output=True, check=False,
                    )
                    self.assertEqual(0, completed.returncode, completed.stderr)


if __name__ == "__main__":
    unittest.main()
