"""Focused command-dispatch and profile-adapter checks for terminal launchers."""

from __future__ import annotations

import importlib.util
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
    def test_typed_hook_option_reaches_the_cli_argument_list(self):
        with tempfile.TemporaryDirectory(prefix="literal terminal option ") as directory:
            root = Path(directory)
            launcher = root / "package/resources/machine/scripts/claude_terminal_launcher.py"
            launcher.parent.mkdir(parents=True)
            launcher.write_text("import json, sys\nprint(json.dumps(sys.argv[1:]))\n", encoding="utf-8")
            cache = root / "cache"
            cache.mkdir()
            (cache / "installed_plugins.json").write_text(json.dumps({"plugins": {
                "machine@base-agents": [{"scope": "user", "installPath": str(root / "package")}]
            }}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-B", "-c", PROFILE.BOOTSTRAP, "claude", "typed-cli", directory, "--hooks"],
                env=dict(os.environ, CLAUDE_CODE_PLUGIN_CACHE_DIR=str(cache)),
                text=True, encoding="utf-8", capture_output=True, check=False,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["--", "--hooks"], json.loads(result.stdout)[-2:])

    def test_claude_exempts_non_sessions_and_makes_bare_name_in_python(self):
        with mock.patch.object(CLAUDE, "native_target_for_batch", side_effect=lambda target: target), \
                mock.patch.object(CLAUDE, "sync_claude_standards") as sync, \
                mock.patch.object(CLAUDE, "run_target", return_value=17) as run, \
                mock.patch.object(CLAUDE, "claude_label", return_value="repo/topic"):
            self.assertEqual(17, CLAUDE.main(["--project", "/work", "--target", "claude", "plugin", "list"]))
            sync.assert_not_called()
            run.assert_called_once_with("claude", ["plugin", "list"])
            run.reset_mock()
            self.assertEqual(17, CLAUDE.main(["--project", "/work", "--target", "claude", "--", "--help"]))
            sync.assert_not_called()
            run.assert_called_once_with("claude", ["--help"])
            run.reset_mock()
            self.assertEqual(17, CLAUDE.main(["--project", "/work", "--target", "claude"]))
            sync.assert_called_once_with(Path("/work"), claude="claude")
            run.assert_called_once_with("claude", ["-n", "repo/topic"])

    def test_claude_uses_native_for_refresh_when_the_typed_target_is_a_batch_shim(self):
        with mock.patch.object(CLAUDE, "native_target_for_batch", return_value="C:/native/claude.exe") as resolve, \
                mock.patch.object(CLAUDE, "sync_claude_standards") as sync, \
                mock.patch.object(CLAUDE, "run_target", return_value=0):
            self.assertEqual(0, CLAUDE.main(["--project", "/work", "--target", "C:/npm/claude.cmd", "chat"]))
        resolve.assert_called_once_with("C:/npm/claude.cmd")
        sync.assert_called_once_with(Path("/work"), claude="C:/native/claude.exe")

    def test_codex_uses_native_for_refresh_but_preserves_typed_shim_and_args(self):
        special = ["exec", "space arg", "café", 'quote"arg']
        with mock.patch.object(CODEX, "resolve_codex_for_sync", return_value="/native/codex") as resolve, \
                mock.patch.object(CODEX, "sync_codex_standards") as sync, \
                mock.patch.object(CODEX, "run_target", return_value=23) as run:
            self.assertEqual(23, CODEX.main(["--project", "/work", "--target", "C:/npm/codex.cmd", *special]))
            resolve.assert_called_once_with("C:/npm/codex.cmd")
            sync.assert_called_once_with("/native/codex", Path("/work"))
            run.assert_called_once_with("C:/npm/codex.cmd", special)

    def test_codex_plugin_is_exempt_and_refresh_failure_is_fail_open(self):
        with mock.patch.object(CODEX, "resolve_codex_for_sync") as resolve, \
                mock.patch.object(CODEX, "sync_codex_standards", side_effect=CODEX.SyncError("bad registry")) as sync, \
                mock.patch.object(CODEX, "run_target", return_value=9) as run:
            self.assertEqual(9, CODEX.main(["--project", "/work", "--target", "codex", "plugin", "list"]))
            resolve.assert_not_called()
            sync.assert_not_called()
            self.assertEqual(9, CODEX.main(["--project", "/work", "--target", "codex", "exec"]))
            self.assertEqual(run.call_count, 2)

    def test_codex_launcher_orders_refresh_before_cli_and_routes_hook_control(self):
        events = []
        with mock.patch.object(CODEX, "resolve_codex_for_sync", side_effect=lambda target: events.append("resolve") or target), \
                mock.patch.object(CODEX, "sync_codex_standards", side_effect=lambda target, project: events.append("sync")), \
                mock.patch.object(CODEX, "run_target", side_effect=lambda target, arguments: events.append(("cli", arguments)) or 41), \
                mock.patch.object(CODEX, "hook_control", side_effect=lambda arguments: events.append(("hooks", arguments)) or 42):
            self.assertEqual(41, CODEX.main(["--project", "/work", "--target", "codex", "exec", "--json"]))
            self.assertEqual(["resolve", "sync", ("cli", ["exec", "--json"])], events)
            events.clear()
            self.assertEqual(41, CODEX.main(["--project", "/work", "--target", "codex", "plugin", "list"]))
            self.assertEqual([("cli", ["plugin", "list"])], events)
            events.clear()
            self.assertEqual(42, CODEX.main(["--project", "/work", "--target", "codex", "--hooks", "status"]))
            self.assertEqual([("hooks", ["status"])], events)

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
                                       capture_output=True, check=False)
        self.assertEqual(29, completed.returncode)
        self.assertEqual(json.dumps(arguments, ensure_ascii=False, separators=(",", ":")) + "\n", completed.stdout)

    def test_bash_set_eu_bare_command_and_missing_registry_fall_back(self):
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
            actual_calls = calls.read_text(encoding="utf-8")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("typed:0\n", result.stdout)
        self.assertEqual("cli\n", actual_calls)
        self.assertIn("registry could not be read", result.stderr)

    def test_bootstrap_warns_for_malformed_registry_shapes(self):
        with tempfile.TemporaryDirectory(prefix="terminal registry ") as directory:
            registry = Path(directory) / "installed_plugins.json"
            for value in ("{not json", json.dumps([]), json.dumps(None),
                          json.dumps({"plugins": None}),
                          json.dumps({"plugins": {"machine@base-agents": None}}),
                          json.dumps({"plugins": {"machine@base-agents": [None]}})):
                registry.write_text(value, encoding="utf-8")
                env = dict(os.environ, CLAUDE_CODE_PLUGIN_CACHE_DIR=str(Path(directory)))
                result = subprocess.run(
                    [sys.executable, "-B", "-c", PROFILE.BOOTSTRAP, "claude", "/bin/true", directory],
                    env=env, text=True, capture_output=True, check=False,
                )
                self.assertEqual(125, result.returncode)
                self.assertIn("registry is malformed", result.stderr)

    def test_bash_missing_interpreter_warns_and_falls_back(self):
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

    def test_bash_preserves_a_real_cli_exit_125_without_a_second_launch(self):
        if shutil.which("bash") is None:
            self.skipTest("Bash is unavailable")
        with tempfile.TemporaryDirectory(prefix="terminal status ") as directory:
            root = Path(directory)
            home, bin_dir, active = root / "home", root / "bin", root / "active"
            bin_dir.mkdir()
            calls = root / "calls"
            cli = bin_dir / "claude"
            cli.write_text("#!/bin/sh\nprintf 'cli\\n' >> \"$CALLS\"\nexit 125\n", encoding="utf-8")
            cli.chmod(cli.stat().st_mode | 0o111)
            launcher = active / "resources" / "machine" / "scripts" / "claude_terminal_launcher.py"
            launcher.parent.mkdir(parents=True)
            launcher.write_text(
                "import argparse, subprocess\n"
                "parser = argparse.ArgumentParser(); parser.add_argument('--project'); parser.add_argument('--target'); parser.add_argument('args', nargs='*')\n"
                "parsed = parser.parse_args(); args = parsed.args[1:] if parsed.args[:1] == ['--'] else parsed.args\n"
                "raise SystemExit(subprocess.run([parsed.target, *args]).returncode)\n",
                encoding="utf-8",
            )
            cache = root / "cache"
            cache.mkdir()
            (cache / "installed_plugins.json").write_text(json.dumps({"plugins": {"machine@base-agents": [{"scope": "user", "installPath": str(active)}]}}), encoding="utf-8")
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
                package = root / label
                launcher = package / "resources" / "machine" / "scripts" / "claude_terminal_launcher.py"
                launcher.parent.mkdir(parents=True)
                launcher.write_text("from pathlib import Path\nimport os\nPath(os.environ['CALLS']).open('a', encoding='utf-8').write('" + label + "\\n')\n", encoding="utf-8")
                active.append(package)
            registry = cache / "installed_plugins.json"
            second = cache / "second.json"
            registry.write_text(json.dumps({"plugins": {"machine@base-agents": [{"scope": "user", "installPath": str(active[0])}]}}), encoding="utf-8")
            second.write_text(json.dumps({"plugins": {"machine@base-agents": [{"scope": "user", "installPath": str(active[1])}]}}), encoding="utf-8")
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
                cli.write_text("#!/bin/sh\nexit 88\n", encoding="utf-8")
                cli.chmod(cli.stat().st_mode | 0o111)
                active = root / f"{host}-active"
                launcher = active / "resources" / "machine" / "scripts" / f"{host}_terminal_launcher.py"
                launcher.parent.mkdir(parents=True)
                launcher.write_text("import json, sys\nprint(json.dumps(sys.argv[1:]))\n", encoding="utf-8")
                if host == "claude":
                    cache = root / "claude-cache"
                    cache.mkdir()
                    (cache / "installed_plugins.json").write_text(json.dumps({"plugins": {
                        "machine@base-agents": [{"scope": "user", "installPath": str(active)}]
                    }}), encoding="utf-8")
                    environment["CLAUDE_CODE_PLUGIN_CACHE_DIR"] = str(cache)
                else:
                    native = bin_dir / "node_modules" / "@openai" / "codex" / "node_modules" / "@openai" / "codex-test" / "vendor" / "test" / "bin" / "codex"
                    native.parent.mkdir(parents=True)
                    native.write_text("#!/bin/sh\nprintf '%s\\n' '{\"installed\":[{\"pluginId\":\"machine@base-agents\",\"version\":\"test\",\"enabled\":true}]}'\n", encoding="utf-8")
                    native.chmod(native.stat().st_mode | 0o111)
                    codex_home = root / "codex-home"
                    cache = codex_home / "plugins" / "cache" / "base-agents" / "machine" / "test"
                    cache.parent.mkdir(parents=True)
                    shutil.copytree(active, cache)
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
