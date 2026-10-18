"""Coordinator identity and recovery run through the shared shell bootstrap on both platforms."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "canonical_coordinator_profile", ROOT / ".agents/machine/scripts/claude_terminal_profile.py"
)
PROFILE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROFILE)


class CanonicalCoordinatorTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="coordinator recovery ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.bootstrap = self.root / "bootstrap.py"
        self.bootstrap.write_text(PROFILE.BOOTSTRAP, encoding="utf-8")
        self.home = self.root / "home"
        self.addCleanup(mock.patch.stopall)
        mock.patch.dict(os.environ, {"CODEX_HOME": str(self.home)}).start()

    def run_bootstrap(self, arguments, responses):
        with mock.patch.object(sys, "argv", [str(self.bootstrap), *arguments]), \
                mock.patch("subprocess.run", side_effect=responses) as native:
            with self.assertRaises(SystemExit) as stopped:
                runpy.run_path(str(self.bootstrap), run_name="__main__")
        return stopped.exception.code, native

    def test_plugin_repair_does_not_require_or_inventory_a_coordinator(self):
        arguments = ["plugin", "add", "machine@tj-agents", "--json"]
        status, native = self.run_bootstrap(
            ["codex", "native-codex", str(self.root), *arguments],
            [subprocess.CompletedProcess([], 37)],
        )
        self.assertEqual(37, status)
        native.assert_called_once_with(["native-codex", *arguments])

    def test_probe_does_not_perform_the_requested_plugin_mutation(self):
        status, native = self.run_bootstrap(
            ["--probe", "codex", "native-codex", str(self.root), "plugin", "remove", "anything"], []
        )
        self.assertEqual(0, status)
        native.assert_not_called()

    def test_current_coordinator_is_selected_and_original_arguments_survive(self):
        package = self.home / "plugins/cache/tj-agents/machine/local"
        (package / "catalog").mkdir(parents=True)
        (package / "catalog/catalog.json").write_text("{}", encoding="utf-8")
        launcher = package / "resources/machine/scripts/codex_terminal_launcher.py"
        launcher.parent.mkdir(parents=True)
        launcher.touch()
        inventory = {"installed": [{
            "pluginId": "machine@tj-agents", "marketplaceName": "tj-agents", "name": "machine",
            "version": "local", "enabled": True,
            "marketplaceSource": {"sourceType": "git", "source": "https://github.com/tj-agents/marketplace.git"},
        }]}
        status, native = self.run_bootstrap(
            ["codex", "native-codex", str(self.root), "resume", "a session"],
            [subprocess.CompletedProcess([], 0, json.dumps(inventory)), subprocess.CompletedProcess([], 19)],
        )
        self.assertEqual(19, status)
        self.assertEqual(native.call_args.args[0], [
            sys.executable, "-I", "-B", str(launcher), "--project", str(self.root),
            "--target", "native-codex", "--", "resume", "a session",
        ])

    def test_old_identity_cannot_be_selected_and_failure_names_working_repair(self):
        inventory = {"installed": [{
            "pluginId": "machine@base-agents", "marketplaceName": "base-agents", "name": "machine",
            "version": "local", "enabled": True,
            "marketplaceSource": {"sourceType": "git", "source": "https://github.com/tomjseery/base-agents.git"},
        }]}
        with mock.patch("sys.stderr") as errors:
            status, native = self.run_bootstrap(
                ["codex", "native-codex", str(self.root)],
                [subprocess.CompletedProcess([], 0, json.dumps(inventory))],
            )
        self.assertEqual(125, status)
        self.assertEqual(1, native.call_count)
        self.assertIn("codex plugin add machine@tj-agents", "".join(call.args[0] for call in errors.write.call_args_list))


if __name__ == "__main__":
    unittest.main()
