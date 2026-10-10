"""Actual Bash and PowerShell execution of terminal profile adapters in disposable homes."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents" / "machine" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def profile(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CLAUDE = profile("claude_terminal_profile")
CODEX = profile("codex_terminal_profile")


class TerminalProfileWiringTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="terminal profile wiring ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.documents = self.root / "Documents"
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.calls = self.root / "calls.txt"
        self.environment = os.environ.copy()
        self.environment.update({"HOME": str(self.home), "PATH": f"{self.bin}{os.pathsep}{self.environment['PATH']}", "CALLS": str(self.calls)})

    def executable(self, name: str, body: str) -> Path:
        if os.name == "nt":
            script = self.bin / f"{name}.py"
            script.write_text(body, encoding="utf-8")
            path = self.bin / f"{name}.cmd"
            path.write_text(f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n', encoding="utf-8")
            return path
        path = self.bin / name
        path.write_text("#!/usr/bin/env python3\n" + body, encoding="utf-8")
        path.chmod(path.stat().st_mode | 0o111)
        return path

    def profile_path(self) -> Path:
        if os.name == "nt":
            return self.documents / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
        return self.home / ".config" / "powershell" / "Microsoft.PowerShell_profile.ps1"

    def install_profile(self, module) -> None:
        arguments = ["--documents", str(self.documents)] if os.name == "nt" else ["--home", str(self.home)]
        self.assertEqual(module.main(arguments), 0)

    def active_launcher(self, host: str) -> Path:
        root = self.root / "active"
        script = root / "resources" / "machine" / "scripts" / f"{host}_terminal_launcher.py"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text(
            "import os, sys\n"
            "with open(os.environ['CALLS'], 'a', encoding='utf-8') as output:\n"
            "    output.write(('hooks ' if '--hooks' in sys.argv else 'refresh ') + ' '.join(sys.argv[1:]) + '\\n')\n",
            encoding="utf-8",
        )
        return root

    def run_bash(self, command: str) -> subprocess.CompletedProcess[str]:
        if os.name == "nt":
            self.skipTest("Bash adapter integration runs on Linux")
        if shutil.which("bash") is None:
            self.skipTest("Bash is unavailable")
        return subprocess.run(["bash", "--noprofile", "--norc", "-c", command], env=self.environment,
                              text=True, capture_output=True, check=False)

    def powershells(self) -> list[str]:
        names = ("pwsh", "powershell.exe") if os.name == "nt" else ("pwsh", "powershell")
        found = [shell for name in names if (shell := shutil.which(name))]
        if not found:
            self.skipTest("PowerShell is unavailable")
        return list(dict.fromkeys(found))

    def run_powershell(self, shell: str, command: str, mode: str = "Legacy") -> subprocess.CompletedProcess[str]:
        command = f"$PSNativeCommandArgumentPassing = '{mode}'; " + command
        return subprocess.run([shell, "-NoProfile", "-Command", command], env=self.environment,
                              text=True, capture_output=True, check=False)

    def active_argument_spy(self, host: str) -> Path:
        root = self.root / f"{host}-argument-spy"
        script = root / "resources" / "machine" / "scripts" / f"{host}_terminal_launcher.py"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text(
            "import json, os, sys\n"
            "with open(os.environ['ARGUMENTS'], 'w', encoding='utf-8') as output:\n"
            "    json.dump(sys.argv[1:], output, ensure_ascii=False)\n"
            "print('live launcher output')\n"
            "raise SystemExit(37)\n",
            encoding="utf-8",
        )
        return root

    def native_codex(self, shim: Path) -> Path:
        name = "codex.exe" if os.name == "nt" else "codex"
        native = shim.parent / "node_modules" / "@openai" / "codex" / "node_modules" / "@openai" / "codex-test" / "vendor" / "test" / "bin" / name
        native.parent.mkdir(parents=True, exist_ok=True)
        if native.is_file():
            return native
        if os.name != "nt":
            native.write_text(
                "#!/usr/bin/env python3\n"
                "import json, sys\n"
                "if sys.argv[1:] == ['plugin', 'list', '--json']:\n"
                " print(json.dumps({'installed': [{'pluginId': 'machine@base-agents', 'version': 'test', 'enabled': True}]}))\n",
                encoding="utf-8",
            )
            native.chmod(native.stat().st_mode | 0o111)
            return native
        source = self.root / "native_codex.cs"
        source.write_text(
            "using System; class Program { public static int Main(string[] args) { "
            "if (args.Length == 3 && args[0] == \"plugin\" && args[1] == \"list\" && args[2] == \"--json\") "
            "Console.Write(\"{\\\"installed\\\":[{\\\"pluginId\\\":\\\"machine@base-agents\\\",\\\"version\\\":\\\"test\\\",\\\"enabled\\\":true}]}\"); return 0; } }",
            encoding="utf-8",
        )
        compiler = shutil.which("powershell.exe")
        if compiler is None:
            self.skipTest("Windows PowerShell is required to compile the native Codex fixture")
        script = self.root / "compile_native.ps1"
        script.write_text(
            "$source = Get-Content -Raw -LiteralPath '" + str(source).replace("'", "''") + "'\n"
            "Add-Type -TypeDefinition $source -OutputAssembly '" + str(native).replace("'", "''") + "' -OutputType ConsoleApplication\n",
            encoding="utf-8",
        )
        compiled = subprocess.run([compiler, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
                                  text=True, capture_output=True, check=False)
        self.assertEqual(0, compiled.returncode, compiled.stderr)
        return native

    def assert_claude_wiring(self, run, command: str):
        self.calls.unlink(missing_ok=True)
        active = self.active_launcher("claude")
        cache = self.root / "claude-cache"
        cache.mkdir(exist_ok=True)
        (cache / "installed_plugins.json").write_text(json.dumps({"plugins": {"machine@base-agents": [{"scope": "user", "installPath": str(active)}]}}), encoding="utf-8")
        self.environment.update({"CLAUDE_CODE_PLUGIN_CACHE_DIR": str(cache), "CLAUDE_CONFIG_DIR": str(self.root / "claude-config")})
        self.executable("claude", "import os, sys\nopen(os.environ['CALLS'], 'a').write('claude ' + ' '.join(sys.argv[1:]) + '\\n')\n")
        self.install_profile(CLAUDE)

        completed = run(command)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        calls = self.calls.read_text(encoding="utf-8").splitlines()
        # The disposable active launcher is only a profile-delegation spy; command dispatch belongs
        # to the installed Python launcher and is exercised directly below.
        self.assertEqual(sum(line.startswith("refresh ") for line in calls), 3)

    def test_claude_bash_refresh_only_sessions_and_preserve_arguments(self):
        self.assert_claude_wiring(self.run_bash, f". {shlex.quote(str(self.home / '.bashrc'))}; claude plugin list; claude --resume session; claude")

    def test_claude_powershell_refresh_only_sessions_and_preserve_arguments(self):
        for shell in self.powershells():
            with self.subTest(shell=shell):
                self.assert_claude_wiring(lambda command: self.run_powershell(shell, command), f". '{self.profile_path()}'; claude plugin list; claude --resume session; claude")

    def assert_codex_wiring(self, run, command: str, expected_code: int):
        self.calls.unlink(missing_ok=True)
        active = self.active_launcher("codex")
        hooks = active / ".agents" / "machine" / "utility" / "hook-control" / "scripts" / "hook_control.py"
        hooks.parent.mkdir(parents=True)
        hooks.write_text("import os, sys\nopen(os.environ['CALLS'], 'a').write('hooks ' + ' '.join(sys.argv[1:]) + '\\n')\n", encoding="utf-8")
        self.environment["CODEX_HOME"] = str(self.root / "codex-home")
        shim = self.executable("codex", "import os, sys\nopen(os.environ['CALLS'], 'a').write('codex ' + ' '.join(sys.argv[1:]) + '\\n')\n")
        self.native_codex(shim)
        cache = Path(self.environment["CODEX_HOME"]) / "plugins" / "cache" / "base-agents" / "machine" / "test"
        cache.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(active, cache, dirs_exist_ok=True)
        self.install_profile(CODEX)

        completed = run(command)
        self.assertEqual(completed.returncode, expected_code, completed.stderr)
        calls = self.calls.read_text(encoding="utf-8").splitlines()
        self.assertEqual(sum(line.startswith("refresh ") for line in calls), 2)
        self.assertEqual(sum(line.startswith("hooks ") for line in calls), 1)
        self.assertEqual(sum(line.startswith("codex ") for line in calls), 0)

    def test_codex_bash_skips_plugin_recursion_and_keeps_codex_hooks(self):
        self.assert_codex_wiring(self.run_bash, f". {shlex.quote(str(self.home / '.bashrc'))}; codex plugin list; codex exec; codex-hooks status", 0)

    def test_codex_powershell_skips_plugin_recursion_and_keeps_codex_hooks(self):
        for shell in self.powershells():
            with self.subTest(shell=shell):
                self.assert_codex_wiring(lambda command: self.run_powershell(shell, command), f". '{self.profile_path()}'; codex plugin list; codex exec; codex-hooks status", 0)

    def test_powershell_payload_preserves_literal_arguments_for_each_host_and_mode(self):
        project = self.root / "project café"
        project.mkdir()
        for shadow in ("json.py", "subprocess.py"):
            (project / shadow).write_text("raise RuntimeError('project module was imported')\n", encoding="utf-8")
        literal = ['a"b', '', 'a b', 'café', 'C:\\path with space\\']
        modes = ("Legacy", "Standard")
        for host, module, hook in (("claude", CLAUDE, False), ("codex", CODEX, False), ("codex", CODEX, True)):
            arguments_path = self.root / f"{host}-{'hooks' if hook else 'cli'}-arguments.json"
            active = self.active_argument_spy(host)
            self.environment["ARGUMENTS"] = str(arguments_path)
            if host == "claude":
                cache = self.root / "claude-arguments-cache"
                cache.mkdir(exist_ok=True)
                (cache / "installed_plugins.json").write_text(json.dumps({"plugins": {
                    "machine@base-agents": [{"scope": "user", "installPath": str(active)}]
                }}), encoding="utf-8")
                self.environment["CLAUDE_CODE_PLUGIN_CACHE_DIR"] = str(cache)
                target = self.executable("claude", "raise SystemExit(88)\n")
            else:
                self.environment["CODEX_HOME"] = str(self.root / "codex-arguments-home")
                target = self.executable("codex", "raise SystemExit(88)\n")
                shim = target
                self.native_codex(shim)
                cache = Path(self.environment["CODEX_HOME"]) / "plugins" / "cache" / "base-agents" / "machine" / "test"
                cache.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(active, cache, dirs_exist_ok=True)
            self.install_profile(module)
            command_name = "codex-hooks" if hook else host
            quoted = " ".join("'" + value.replace("'", "''") + "'" for value in literal)
            command = f". '{self.profile_path()}'; Set-Location '{project}'; {command_name} {quoted}; exit $LASTEXITCODE"
            for shell in self.powershells():
                for mode in modes:
                    with self.subTest(host=host, hooks=hook, shell=shell, mode=mode):
                        arguments_path.unlink(missing_ok=True)
                        completed = self.run_powershell(shell, command, mode)
                        self.assertEqual(37, completed.returncode, completed.stderr)
                        self.assertEqual("live launcher output\n", completed.stdout)
                        expected = ["--project", str(project), "--target", str(target)]
                        if hook:
                            expected.append("--hooks")
                        expected.extend(["--", *literal])
                        self.assertEqual(expected, json.loads(arguments_path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
