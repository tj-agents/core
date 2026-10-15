"""Actual Bash and PowerShell execution of terminal profile adapters in disposable homes."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import stat
import sys
import tempfile
import unittest
from unittest import mock


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
        self.root = Path(self.temporary.name).resolve()
        self.home = self.root / "home"
        self.documents = self.root / "Documents"
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.calls = self.root / "calls.txt"
        self.environment = os.environ.copy()
        self.environment.update({"HOME": str(self.home), "PATH": f"{self.bin}{os.pathsep}{self.environment['PATH']}", "CALLS": str(self.calls),
                                 "CLAUDE_CONFIG_DIR": str(self.root / "claude-config"),
                                 "CLAUDE_CODE_PLUGIN_CACHE_DIR": str(self.root / "missing-claude-cache")})

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
        catalog = root / "catalog"
        catalog.mkdir(exist_ok=True)
        (catalog / "catalog.json").write_text("{}", encoding="utf-8")
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
        catalog = root / "catalog"
        catalog.mkdir(exist_ok=True)
        (catalog / "catalog.json").write_text("{}", encoding="utf-8")
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
        native = shim if os.name != "nt" else shim.parent / "node_modules" / "@openai" / "codex" / "node_modules" / "@openai" / "codex-test" / "vendor" / "test" / "bin" / name
        native.parent.mkdir(parents=True, exist_ok=True)
        if os.name != "nt":
            native.write_text(
                "#!/usr/bin/env python3\n"
                "import json, sys\n"
                "if sys.argv[1:] == ['plugin', 'list', '--json']:\n"
                " print(json.dumps({'installed': [{'pluginId': 'machine@base-agents', 'version': 'test', 'enabled': True, 'marketplaceName': 'base-agents', 'name': 'machine', 'marketplaceSource': {'sourceType': 'git', 'source': 'https://github.com/tj-agents/core.git'}}]}))\n",
                encoding="utf-8",
            )
            native.chmod(native.stat().st_mode | 0o111)
            return native
        if native.is_file():
            return native
        source = self.root / "native_codex.cs"
        source.write_text(
            "using System; class Program { public static int Main(string[] args) { "
            "if (args.Length == 3 && args[0] == \"plugin\" && args[1] == \"list\" && args[2] == \"--json\") "
            "Console.Write(\"{\\\"installed\\\":[{\\\"pluginId\\\":\\\"machine@base-agents\\\",\\\"version\\\":\\\"test\\\",\\\"enabled\\\":true,\\\"marketplaceName\\\":\\\"base-agents\\\",\\\"name\\\":\\\"machine\\\",\\\"marketplaceSource\\\":{\\\"sourceType\\\":\\\"git\\\",\\\"source\\\":\\\"https://github.com/tj-agents/core.git\\\"}}]}\"); return 0; } }",
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

    def claude_package(self, cache: Path, active: Path, version: str) -> Path:
        package = cache / "base-agents" / "machine" / version
        package.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(active, package, dirs_exist_ok=True)
        catalog = package / "catalog"
        catalog.mkdir(exist_ok=True)
        (catalog / "catalog.json").write_text("{}", encoding="utf-8")
        return package

    def configure_claude_coordinator(self, cache: Path, package: Path) -> None:
        cache.mkdir(exist_ok=True)
        (cache / "known_marketplaces.json").write_text(json.dumps({
            "base-agents": {"source": "https://github.com/tj-agents/core.git"},
        }), encoding="utf-8")
        (cache / "installed_plugins.json").write_text(json.dumps({"plugins": {
            "machine@base-agents": [{"scope": "user", "installPath": str(package)}],
        }}), encoding="utf-8")

    def versioned_python(self, name: str, version: tuple[int, int], label: str) -> Path:
        if os.name == "nt":
            script = self.bin / f"{name}.py"
            script.write_text(
                "import os, sys\n"
                "code = next((value for value in sys.argv[1:] if 'version_info' in value), '')\n"
                f"version = {version!r}\n"
                "if code:\n"
                "    required = (3, 11) if '(3, 11)' in code else (3, 9)\n"
                "    raise SystemExit(0 if version >= required else 1)\n"
                "with open(os.environ['INTERPRETERS'], 'a', encoding='utf-8') as output:\n"
                f"    output.write({label!r} + '\\n')\n"
                "os.execv(sys.executable, [sys.executable, *sys.argv[1:]])\n",
                encoding="utf-8",
            )
            path = self.bin / f"{name}.cmd"
            path.write_text(f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n', encoding="utf-8")
            return path
        path = self.bin / name
        path.write_text(
            "#!/bin/sh\n"
            "case \"$*\" in\n"
            f"  *'(3, 11)'*) exit {0 if version >= (3, 11) else 1} ;;\n"
            f"  *'(3, 9)'*) exit {0 if version >= (3, 9) else 1} ;;\n"
            "esac\n"
            f"printf '%s\\n' '{label}' >> \"$INTERPRETERS\"\n"
            f"exec {shlex.quote(sys.executable)} \"$@\"\n",
            encoding="utf-8",
        )
        path.chmod(path.stat().st_mode | 0o111)
        return path

    def codex_interpreter_fixture(self) -> tuple[Path, Path]:
        active = self.root / "codex-interpreter-active"
        launcher = active / "resources" / "machine" / "scripts" / "codex_terminal_launcher.py"
        launcher.parent.mkdir(parents=True)
        launcher.write_text(
            "import os, sys\n"
            "with open(os.environ['CALLS'], 'a', encoding='utf-8') as output:\n"
            "    output.write(('hooks' if '--hooks' in sys.argv else 'refresh') + '\\n')\n",
            encoding="utf-8",
        )
        catalog = active / "catalog"
        catalog.mkdir(exist_ok=True)
        (catalog / "catalog.json").write_text("{}", encoding="utf-8")
        target = self.executable("codex", "raise SystemExit(88)\n")
        if os.name == "nt":
            self.native_codex(target)
        else:
            native = self.bin / "node_modules" / "@openai" / "codex" / "node_modules" / "@openai" / "codex-test" / "vendor" / "test" / "bin" / "codex"
            native.parent.mkdir(parents=True)
            native.write_text("#!/bin/sh\nprintf '%s\\n' '{\"installed\":[{\"pluginId\":\"machine@base-agents\",\"version\":\"test\",\"enabled\":true,\"marketplaceName\":\"base-agents\",\"name\":\"machine\",\"marketplaceSource\":{\"sourceType\":\"git\",\"source\":\"https://github.com/tj-agents/core.git\"}}]}'\n", encoding="utf-8")
            native.chmod(native.stat().st_mode | 0o111)
        codex_home = self.root / "codex-interpreter-home"
        cache = codex_home / "plugins" / "cache" / "base-agents" / "machine" / "test"
        cache.parent.mkdir(parents=True)
        shutil.copytree(active, cache)
        return codex_home, active

    def assert_claude_wiring(self, run, command: str):
        self.calls.unlink(missing_ok=True)
        active = self.active_launcher("claude")
        cache = self.root / "claude-cache"
        package = self.claude_package(cache, active, "test")
        self.configure_claude_coordinator(cache, package)
        self.environment.update({"CLAUDE_CODE_PLUGIN_CACHE_DIR": str(cache), "CLAUDE_CONFIG_DIR": str(self.root / "claude-config")})
        self.executable("claude", "import os, sys\nopen(os.environ['CALLS'], 'a').write('claude ' + ' '.join(sys.argv[1:]) + '\\n')\n")
        self.install_profile(CLAUDE)

        completed = run(command)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        calls = self.calls.read_text(encoding="utf-8").splitlines()
        # The disposable active launcher is only a profile-delegation spy; command dispatch belongs
        # to the installed Python launcher and is exercised directly below.
        self.assertEqual(sum(line.startswith("refresh ") for line in calls), 3)

    @unittest.skipIf(os.name == "nt", "POSIX profile modes are verified on Linux")
    def test_install_and_refresh_preserve_private_profile_permissions(self):
        prior_umask = os.umask(0o022)
        try:
            for module in (CLAUDE, CODEX):
                with self.subTest(profile=module.__name__):
                    path = self.root / (module.__name__ + ".bashrc")
                    path.write_text("private=value\n", encoding="utf-8")
                    path.chmod(0o600)
                    self.assertTrue(module.ensure(path, module.BASH_BLOCK))
                    self.assertEqual(0o600, stat.S_IMODE(path.stat().st_mode))
                    refreshed = module.BASH_BLOCK.replace(module.END, "# refreshed\n" + module.END)
                    self.assertTrue(module.ensure(path, refreshed))
                    self.assertEqual(0o600, stat.S_IMODE(path.stat().st_mode))
                    self.assertTrue(path.read_text(encoding="utf-8").startswith("private=value\n"))
        finally:
            os.umask(prior_umask)
        self.assertEqual([], list(self.root.glob(".*.tmp")))

    def test_failed_profile_replacement_keeps_original_and_removes_temporary_file(self):
        for module in (CLAUDE, CODEX):
            with self.subTest(profile=module.__name__):
                path = self.root / (module.__name__ + ".bashrc")
                path.write_bytes(b"original\n")
                with mock.patch.object(CLAUDE.os, "replace", side_effect=OSError("blocked")):
                    with self.assertRaisesRegex(OSError, "blocked"):
                        module.ensure(path, module.BASH_BLOCK)
                self.assertEqual(b"original\n", path.read_bytes())
                self.assertEqual([], list(self.root.glob(".*.tmp")))

    def test_claude_bash_refresh_only_sessions_and_preserve_arguments(self):
        self.assert_claude_wiring(self.run_bash, f". {shlex.quote(str(self.home / '.bashrc'))}; claude plugin list; claude --resume session; claude")

    def test_claude_powershell_refresh_only_sessions_and_preserve_arguments(self):
        for shell in self.powershells():
            with self.subTest(shell=shell):
                self.assert_claude_wiring(lambda command: self.run_powershell(shell, command), f". '{self.profile_path()}'; claude plugin list; claude --resume session; claude")

    def test_claude_powershell_fails_closed_when_its_registry_cannot_be_read(self):
        self.executable("claude", "print('fallback')\n")
        self.install_profile(CLAUDE)
        for shell in self.powershells():
            with self.subTest(shell=shell):
                completed = self.run_powershell(shell, f". '{self.profile_path()}'; claude; exit $LASTEXITCODE")
                self.assertNotEqual(0, completed.returncode)
                self.assertNotIn("fallback", completed.stdout)
                self.assertIn("registry could not be read", completed.stderr)

    def test_claude_powershell_fails_closed_without_a_usable_python(self):
        self.executable("claude", "print('fallback')\n")
        self.install_profile(CLAUDE)
        override = (
            "function Get-Command { param($Name, [switch]$All, $CommandType, $ErrorAction) "
            "if ($Name -in @('python', 'python3', 'py')) { return }; "
            "Microsoft.PowerShell.Core\\Get-Command @PSBoundParameters }; "
        )
        for shell in self.powershells():
            with self.subTest(shell=shell):
                completed = self.run_powershell(shell, override + f". '{self.profile_path()}'; $result = claude; if ($result -eq 125) {{ exit 125 }}; exit 1")
                self.assertEqual(125, completed.returncode, completed.stderr)
                self.assertNotIn("fallback", completed.stdout)
                self.assertIn("no usable Python", completed.stderr)

    def test_claude_powershell_preserves_a_real_cli_exit_125_without_a_second_launch(self):
        active = self.root / "exit-status-active"
        launcher = active / "resources" / "machine" / "scripts" / "claude_terminal_launcher.py"
        launcher.parent.mkdir(parents=True)
        launcher.write_text(
            "import os\n"
            "with open(os.environ['CALLS'], 'a', encoding='utf-8') as output:\n"
            "    output.write('refresh\\n')\n"
            "raise SystemExit(125)\n",
            encoding="utf-8",
        )
        cache = self.root / "exit-status-cache"
        package = self.claude_package(cache, active, "test")
        self.configure_claude_coordinator(cache, package)
        self.environment["CLAUDE_CODE_PLUGIN_CACHE_DIR"] = str(cache)
        self.executable("claude", "import os\nopen(os.environ['CALLS'], 'a').write('cli\\n')\n")
        self.install_profile(CLAUDE)
        for shell in self.powershells():
            with self.subTest(shell=shell):
                self.calls.unlink(missing_ok=True)
                completed = self.run_powershell(shell, f". '{self.profile_path()}'; claude; exit $LASTEXITCODE")
                self.assertEqual(125, completed.returncode, completed.stderr)
                self.assertEqual("refresh\n", self.calls.read_text(encoding="utf-8"))

    def test_claude_powershell_reads_the_active_package_on_each_invocation(self):
        self.executable("claude", "raise SystemExit(99)\n")
        cache = self.root / "active-package-cache"
        cache.mkdir()
        packages = []
        for label in ("first", "second"):
            package = self.root / label
            launcher = package / "resources" / "machine" / "scripts" / "claude_terminal_launcher.py"
            launcher.parent.mkdir(parents=True)
            launcher.write_text(
                "import os\n"
                "with open(os.environ['CALLS'], 'a', encoding='utf-8') as output:\n"
                f"    output.write('{label}\\n')\n",
                encoding="utf-8",
            )
            packages.append(package)
        first = self.claude_package(cache, packages[0], "first")
        second_package = self.claude_package(cache, packages[1], "second")
        self.configure_claude_coordinator(cache, first)
        registry = cache / "installed_plugins.json"
        second = cache / "second.json"
        registry.write_text(json.dumps({"plugins": {
            "machine@base-agents": [{"scope": "user", "installPath": str(first)}],
        }}), encoding="utf-8")
        second.write_text(json.dumps({"plugins": {
            "machine@base-agents": [{"scope": "user", "installPath": str(second_package)}],
        }}), encoding="utf-8")
        self.environment["CLAUDE_CODE_PLUGIN_CACHE_DIR"] = str(cache)
        self.install_profile(CLAUDE)
        for shell in self.powershells():
            with self.subTest(shell=shell):
                self.calls.unlink(missing_ok=True)
                registry.write_text(json.dumps({"plugins": {
                    "machine@base-agents": [{"scope": "user", "installPath": str(first)}],
                }}), encoding="utf-8")
                command = (
                    f". '{self.profile_path()}'; claude; "
                    f"Copy-Item -LiteralPath '{second}' -Destination '{registry}' -Force; "
                    "claude; exit $LASTEXITCODE"
                )
                completed = self.run_powershell(shell, command)
                self.assertEqual(0, completed.returncode, completed.stderr)
                self.assertEqual("first\nsecond\n", self.calls.read_text(encoding="utf-8"))

    def assert_codex_wiring(self, run, command: str, expected_code: int):
        self.calls.unlink(missing_ok=True)
        active = self.active_launcher("codex")
        hooks = active / ".agents" / "machine" / "utility" / "hook-control" / "scripts" / "hook_control.py"
        hooks.parent.mkdir(parents=True, exist_ok=True)
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

    def test_powershell_skips_windows_store_aliases_before_usable_python(self):
        active = self.active_argument_spy("claude")
        arguments = self.root / "arguments.json"
        cache = self.root / "alias-cache"
        package = self.claude_package(cache, active, "test")
        self.configure_claude_coordinator(cache, package)
        self.environment.update(CLAUDE_CODE_PLUGIN_CACHE_DIR=str(cache), ARGUMENTS=str(arguments), OS="Windows_NT")
        self.executable("claude", "raise SystemExit(88)\n")
        stub = r"C:\Users\test\WindowsApps\python.exe"
        interpreter = str(sys.executable).replace("'", "''")
        override = (
            "function Get-Command { param($Name, [switch]$All, $CommandType, $ErrorAction) "
            "if ($Name -eq 'python') { "
            "[pscustomobject]@{ Source = '" + stub + "' }; "
            "[pscustomobject]@{ Source = '" + interpreter + "' }; return }; "
            "if ($Name -in @('python3', 'py')) { return }; "
            "Microsoft.PowerShell.Core\\Get-Command @PSBoundParameters }; "
        )
        for module in (CLAUDE, CODEX):
            profile_path = self.root / (module.__name__ + ".ps1")
            profile_path.write_text(module.POWERSHELL_BLOCK, encoding="utf-8")
            for shell in self.powershells():
                with self.subTest(profile=module.__name__, shell=shell):
                    command = override + f". '{profile_path}'; if (-not $baseAgentsPython) {{ throw 'usable Python missed' }}; "
                    if module is CODEX:
                        command += "if (-not $baseAgentsCodexHooksPython) { throw 'usable hook Python missed' }; "
                    command += "if ($baseAgentsPython.Path -ne '" + interpreter + "') { throw 'wrong interpreter' }; exit 0"
                    completed = self.run_powershell(shell, command)
                    self.assertEqual(0, completed.returncode, completed.stderr)
                    self.assertEqual("", completed.stderr)

    def test_codex_hooks_selects_python_311_without_changing_refresh_selection(self):
        codex_home, _active = self.codex_interpreter_fixture()
        first_name, second_name = ("python", "python3") if os.name == "nt" else ("python3", "python")
        self.versioned_python(first_name, (3, 9), "python39")
        self.versioned_python(second_name, (3, 11), "python311")
        interpreters = self.root / "interpreters.txt"
        codex_bash = self.root / "codex-profile.sh"
        claude_bash = self.root / "claude-profile.sh"
        codex_powershell = self.root / "codex-profile.ps1"
        claude_powershell = self.root / "claude-profile.ps1"
        codex_bash.write_text(CODEX.BASH_BLOCK, encoding="utf-8")
        claude_bash.write_text(CLAUDE.BASH_BLOCK, encoding="utf-8")
        codex_powershell.write_text(CODEX.POWERSHELL_BLOCK, encoding="utf-8")
        claude_powershell.write_text(CLAUDE.POWERSHELL_BLOCK, encoding="utf-8")
        environment = dict(self.environment, PATH=str(self.bin), CODEX_HOME=str(codex_home), INTERPRETERS=str(interpreters))
        bash_orders = ((codex_bash, claude_bash), (claude_bash, codex_bash))
        if os.name != "nt":
            for first, second in bash_orders:
                with self.subTest(shell="bash", order=(first.name, second.name)):
                    self.calls.unlink(missing_ok=True)
                    interpreters.unlink(missing_ok=True)
                    completed = subprocess.run(
                        ["/bin/bash", "--noprofile", "--norc", "-c", f". {shlex.quote(str(first))}; . {shlex.quote(str(second))}; _base_agents_bootstrap='import sys; sys.exit(0)'; codex plugin list; codex-hooks status"],
                        env=environment, text=True, encoding="utf-8", capture_output=True, check=False,
                    )
                    self.assertEqual(0, completed.returncode, completed.stderr)
                    self.assertEqual(["python39", "python39", "python311"], interpreters.read_text(encoding="utf-8").splitlines())
        powershell_orders = ((codex_powershell, claude_powershell), (claude_powershell, codex_powershell))
        for shell in self.powershells():
            for first, second in powershell_orders:
                with self.subTest(shell=shell, order=(first.name, second.name)):
                    self.calls.unlink(missing_ok=True)
                    interpreters.unlink(missing_ok=True)
                    command = f"$PSNativeCommandArgumentPassing = 'Legacy'; . '{first}'; . '{second}'; $baseAgentsBootstrap = 'import sys; sys.exit(0)'; codex plugin list; codex-hooks status; exit $LASTEXITCODE"
                    completed = subprocess.run([shell, "-NoProfile", "-Command", command], env=environment,
                                               text=True, encoding="utf-8", capture_output=True, check=False)
                    self.assertEqual(0, completed.returncode, completed.stderr)
                    self.assertEqual(["python39", "python39", "python311", "python311"], interpreters.read_text(encoding="utf-8").splitlines())

    def test_codex_hooks_requires_python_311_without_running_hook_control(self):
        codex_home, _active = self.codex_interpreter_fixture()
        first_name = "python" if os.name == "nt" else "python3"
        self.versioned_python(first_name, (3, 9), "python39")
        bash_profile = self.root / "codex-profile.sh"
        powershell_profile = self.root / "codex-profile.ps1"
        bash_profile.write_text(CODEX.BASH_BLOCK, encoding="utf-8")
        powershell_profile.write_text(CODEX.POWERSHELL_BLOCK, encoding="utf-8")
        environment = dict(self.environment, PATH=str(self.bin), CODEX_HOME=str(codex_home), INTERPRETERS=str(self.root / "interpreters.txt"))
        if os.name != "nt":
            bash = subprocess.run(
                ["/bin/bash", "--noprofile", "--norc", "-c", f". {shlex.quote(str(bash_profile))}; codex-hooks status"],
                env=environment, text=True, encoding="utf-8", capture_output=True, check=False,
            )
            self.assertEqual(1, bash.returncode)
            self.assertIn("requires Python 3.11", bash.stderr)
            self.assertFalse((codex_home / "config.toml").exists())
        for shell in self.powershells():
            with self.subTest(shell=shell):
                command = f"$PSNativeCommandArgumentPassing = 'Legacy'; . '{powershell_profile}'; codex-hooks status; exit $LASTEXITCODE"
                completed = subprocess.run([shell, "-NoProfile", "-Command", command], env=environment,
                                           text=True, encoding="utf-8", capture_output=True, check=False)
                self.assertEqual(1, completed.returncode)
                self.assertIn("requires Python 3.11", completed.stderr)
                self.assertFalse((codex_home / "config.toml").exists())

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
                package = self.claude_package(cache, active, "test")
                self.configure_claude_coordinator(cache, package)
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
