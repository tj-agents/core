"""The terminal bootstrap reinstalls a machine package whose launcher cannot reach the native CLI."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents" / "machine" / "scripts"


def module(name: str):
    spec = importlib.util.spec_from_file_location(f"bootstrap_repair_{name}", SCRIPTS / f"{name}.py")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


BOOTSTRAP = module("claude_terminal_profile").BOOTSTRAP

READY_THEN_FAIL = (
    "import os, sys\n"
    "open(os.environ['BASE_AGENTS_LAUNCH_STATE'], 'w', encoding='utf-8').write('ready')\n"
    "open(os.environ['CALLS'], 'a', encoding='utf-8').write('{label}\\n')\n"
    "raise SystemExit(1)\n"
)
STARTED_THEN_EXIT = (
    "import os, sys\n"
    "open(os.environ['BASE_AGENTS_LAUNCH_STATE'], 'w', encoding='utf-8').write('started')\n"
    "open(os.environ['CALLS'], 'a', encoding='utf-8').write('{label}\\n')\n"
    "raise SystemExit({code})\n"
)
SILENT_FAIL = (
    "import os\n"
    "open(os.environ['CALLS'], 'a', encoding='utf-8').write('{label}\\n')\n"
    "raise SystemExit(1)\n"
)


class TerminalBootstrapRepairTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="bootstrap repair ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.cache = self.root / "claude-cache"
        self.cache.mkdir()
        self.calls = self.root / "calls.txt"
        (self.cache / "known_marketplaces.json").write_text(json.dumps({
            "base-agents": {"source": "https://github.com/tj-agents/core.git"},
        }), encoding="utf-8")
        self.environment = os.environ.copy()
        self.environment.pop("BASE_AGENTS_LAUNCH_STATE", None)
        self.environment.update({
            "CALLS": str(self.calls),
            "CLAUDE_CONFIG_DIR": str(self.root / "claude-config"),
            "CLAUDE_CODE_PLUGIN_CACHE_DIR": str(self.cache),
            "REGISTRY": str(self.cache / "installed_plugins.json"),
        })

    def package(self, version: str, launcher: str | None) -> Path:
        package = self.cache / "base-agents" / "machine" / version
        (package / "catalog").mkdir(parents=True)
        (package / "catalog" / "catalog.json").write_text("{}", encoding="utf-8")
        if launcher is not None:
            script = package / "resources" / "machine" / "scripts" / "claude_terminal_launcher.py"
            script.parent.mkdir(parents=True)
            script.write_text(launcher, encoding="utf-8")
        return package

    def install(self, package: Path) -> None:
        (self.cache / "installed_plugins.json").write_text(json.dumps({"plugins": {
            "machine@base-agents": [{"scope": "user", "installPath": str(package)}],
        }}), encoding="utf-8")

    def native_claude(self, repaired: Path | None, update_code: int = 0) -> Path:
        body = (
            "import json, os, sys\n"
            "open(os.environ['CALLS'], 'a', encoding='utf-8').write('claude ' + ' '.join(sys.argv[1:]) + '\\n')\n"
            f"if sys.argv[1:3] == ['plugin', 'update'] and {str(repaired) if repaired else None!r}:\n"
            "    open(os.environ['REGISTRY'], 'w', encoding='utf-8').write(json.dumps({'plugins': {\n"
            f"        'machine@base-agents': [{{'scope': 'user', 'installPath': {str(repaired) if repaired else ''!r}}}],\n"
            "    }}))\n"
            f"raise SystemExit({update_code} if sys.argv[1:3] == ['plugin', 'update'] else 0)\n"
        )
        script = self.root / "native_claude.py"
        script.write_text(body, encoding="utf-8")
        if os.name == "nt":
            target = self.root / "claude.cmd"
            target.write_text(f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n', encoding="utf-8")
            return target
        target = self.root / "claude"
        target.write_text(f"#!/bin/sh\nexec '{sys.executable}' '{script}' \"$@\"\n", encoding="utf-8")
        target.chmod(0o755)
        return target

    def run_bootstrap(self, target: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-I", "-B", "-c", BOOTSTRAP, "claude", str(target), str(self.root), *arguments],
            env=self.environment, text=True, capture_output=True, check=False, timeout=120,
        )

    def calls_made(self) -> list[str]:
        return self.calls.read_text(encoding="utf-8").splitlines() if self.calls.exists() else []

    def test_a_launcher_that_fails_before_the_cli_is_reinstalled_and_retried_once(self):
        fixed = self.package("fixed", STARTED_THEN_EXIT.format(label="fixed", code=0))
        self.install(self.package("broken", READY_THEN_FAIL.format(label="broken")))

        completed = self.run_bootstrap(self.native_claude(fixed), "--resume", "x")

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual([
            "broken",
            "claude plugin marketplace update base-agents",
            "claude plugin update machine@base-agents",
            "fixed",
        ], self.calls_made())
        self.assertIn("reinstalling machine@base-agents", completed.stderr)

    def test_a_missing_launcher_is_reinstalled_before_the_first_launch(self):
        fixed = self.package("fixed", STARTED_THEN_EXIT.format(label="fixed", code=0))
        self.install(self.package("empty", None))

        completed = self.run_bootstrap(self.native_claude(fixed))

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual([
            "claude plugin marketplace update base-agents",
            "claude plugin update machine@base-agents",
            "fixed",
        ], self.calls_made())

    def test_a_session_that_reached_the_cli_keeps_its_exit_code_without_repair(self):
        self.install(self.package("healthy", STARTED_THEN_EXIT.format(label="healthy", code=3)))

        completed = self.run_bootstrap(self.native_claude(None))

        self.assertEqual(3, completed.returncode, completed.stderr)
        self.assertEqual(["healthy"], self.calls_made())

    def test_a_launcher_without_launch_state_is_never_relaunched(self):
        self.install(self.package("legacy", SILENT_FAIL.format(label="legacy")))

        completed = self.run_bootstrap(self.native_claude(None))

        self.assertEqual(1, completed.returncode, completed.stderr)
        self.assertEqual(["legacy"], self.calls_made())

    def test_a_failed_repair_keeps_the_original_failure_and_launches_once(self):
        self.install(self.package("broken", READY_THEN_FAIL.format(label="broken")))

        completed = self.run_bootstrap(self.native_claude(None, update_code=1))

        self.assertEqual(1, completed.returncode, completed.stderr)
        self.assertEqual([
            "broken",
            "claude plugin marketplace update base-agents",
            "claude plugin update machine@base-agents",
        ], self.calls_made())

    def test_a_repair_that_does_not_fix_the_launcher_is_not_retried_again(self):
        broken = self.package("broken", READY_THEN_FAIL.format(label="broken"))
        self.install(broken)

        completed = self.run_bootstrap(self.native_claude(broken))

        self.assertEqual(1, completed.returncode, completed.stderr)
        self.assertEqual(["broken", "claude plugin marketplace update base-agents",
                          "claude plugin update machine@base-agents", "broken"], self.calls_made())


class LaunchStateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="launch state ")
        self.addCleanup(temporary.cleanup)
        self.state = Path(temporary.name) / "state"
        self.state.write_text("", encoding="utf-8")
        self.launch_state = module("launch_state")
        previous = os.environ.get(self.launch_state.ENVIRONMENT)
        self.addCleanup(self.restore, previous)
        os.environ[self.launch_state.ENVIRONMENT] = str(self.state)

    def restore(self, previous):
        if previous is None:
            os.environ.pop(self.launch_state.ENVIRONMENT, None)
        else:
            os.environ[self.launch_state.ENVIRONMENT] = previous

    def test_started_is_recorded_and_not_inherited_by_the_native_cli(self):
        self.launch_state.ready()
        self.assertEqual("ready", self.state.read_text(encoding="utf-8"))
        self.launch_state.started()
        self.assertEqual("started", self.state.read_text(encoding="utf-8"))
        self.assertNotIn(self.launch_state.ENVIRONMENT, os.environ)

    def test_real_launchers_report_ready_before_importing_their_dependencies(self):
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                source = (SCRIPTS / f"{host}_terminal_launcher.py").read_text(encoding="utf-8")
                self.assertLess(source.index("launch_state.ready()"), source.index("from startup_binding import"))


if __name__ == "__main__":
    unittest.main()
