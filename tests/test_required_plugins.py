from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / ".agents/machine/scripts"
sys.path.insert(0, str(SCRIPTS))
import required_plugins as required


class RequiredPluginsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="required standards ")
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name) / "project with spaces"
        (self.project / ".agents").mkdir(parents=True)
        self.selection = self.project / ".agents/plugins.json"
        self.profile = Path(self.temporary.name) / "profile"
        self.environment = mock.patch.dict(os.environ, {"CODEX_HOME": str(self.profile)})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def select(self, *identities):
        self.selection.write_text(json.dumps({"schema_version": 1, "plugins": list(identities)}), encoding="utf-8")

    def entry(self, host, identity="arbitrary-stack@arbitrary-publisher", **values):
        name, marketplace = identity.split("@")
        root = self.profile / "plugins/cache" / marketplace / name / "version"
        root.mkdir(parents=True, exist_ok=True)
        if host == "codex":
            entry = {"name": name, "marketplaceName": marketplace, "version": "version", "enabled": True}
        else:
            entry = {"id": identity, "installPath": str(root), "enabled": True}
        return {**entry, **values}

    def check(self, host, entries, status=0):
        data = {"installed": entries} if host == "codex" else entries
        response = subprocess.CompletedProcess([], status, json.dumps(data), "broken marketplace manifest" if status else "")
        with mock.patch.object(required.subprocess, "run", return_value=response) as run:
            result = required.check(self.project, host, "native-cli")
            self.assertEqual(self.project, run.call_args.kwargs["cwd"])
            self.assertLess(run.call_args.kwargs["timeout"], 7)
            return result

    def test_unselected_repository_does_not_query_or_require_a_host(self):
        with mock.patch.object(required.subprocess, "run") as run:
            self.assertIsNone(required.check(self.project, "codex"))
        run.assert_not_called()

    def test_every_selected_plugin_is_required_for_both_hosts(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.select("arbitrary-stack@arbitrary-publisher", "second-stack@another-publisher")
                entries = [self.entry(host)]
                with self.assertRaisesRegex(required.RequiredPluginsError, "second-stack@another-publisher"):
                    self.check(host, entries)
                entries.append(self.entry(host, "second-stack@another-publisher"))
                self.assertEqual(2, len(self.check(host, entries)))

    def test_disabled_broken_wrong_project_and_missing_payload_are_not_active(self):
        for host in ("codex", "claude"):
            for values in ({"enabled": False}, {"installed": False}, {"error": "bad manifest"}, {"errors": ["bad skill"]},
                           {"scope": "project"},
                           {"scope": "project", "projectPath": str(self.project / "other")}):
                with self.subTest(host=host, values=values):
                    self.select("arbitrary-stack@arbitrary-publisher")
                    with self.assertRaises(required.RequiredPluginsError):
                        self.check(host, [self.entry(host, **values)])
        self.select("absent@publisher")
        with self.assertRaises(required.RequiredPluginsError):
            self.check("codex", [{"name": "absent", "marketplaceName": "publisher", "version": "missing", "enabled": True}])

    def test_broken_inventory_is_a_failure_even_when_another_host_has_cached_files(self):
        self.select("arbitrary-stack@arbitrary-publisher")
        self.entry("claude")
        with self.assertRaisesRegex(required.RequiredPluginsError, "broken marketplace manifest"):
            self.check("codex", [], status=1)

    def test_unreadable_invalid_and_unsupported_selections_fail(self):
        for content in ("{", "[]", '{"schema_version": 99, "plugins": ["x@y"]}', '{"schema_version": 1, "plugins": []}'):
            with self.subTest(content=content):
                self.selection.write_text(content, encoding="utf-8")
                with self.assertRaises(required.RequiredPluginsError):
                    required.check(self.project, "codex")

    def test_invalid_inventory_and_timeout_fail(self):
        self.select("arbitrary-stack@arbitrary-publisher")
        for response in (subprocess.CompletedProcess([], 0, "not JSON", ""),
                         subprocess.CompletedProcess([], 0, "{}", "")):
            with mock.patch.object(required.subprocess, "run", return_value=response):
                with self.assertRaises(required.RequiredPluginsError):
                    required.check(self.project, "codex", "native-cli")
        with mock.patch.object(required.subprocess, "run", side_effect=subprocess.TimeoutExpired("native-cli", 3)):
            with self.assertRaises(required.RequiredPluginsError):
                required.check(self.project, "codex", "native-cli")

    def test_subdirectories_use_their_own_repository_selection(self):
        self.select("arbitrary-stack@arbitrary-publisher")
        self.assertEqual(self.project, required.project_root(self.project / "src/deep"))
        nested = self.project / "nested"
        (nested / ".git").mkdir(parents=True)
        self.assertEqual(nested, required.project_root(nested / "src"))

    def test_maintenance_remains_available_but_agent_and_review_commands_require_standards(self):
        for host in ("codex", "claude"):
            for arguments in (["plugin", "add", "x@y"], ["--help"], ["doctor"]):
                with mock.patch.object(required, "check") as check:
                    required.check_launch(self.project, host, "native-cli", arguments)
                    check.assert_not_called()
            for arguments in ([], ["exec", "write code"], ["review"], ["-m", "plugin", "write code"]):
                with mock.patch.object(required, "check") as check:
                    required.check_launch(self.project, host, "native-cli", arguments)
                    check.assert_called_once()

    def test_explicit_directory_override_is_the_checked_project(self):
        with mock.patch.object(required, "check") as check:
            required.check_launch(self.project, "codex", "native-cli", ["--cd", "another", "exec", "work"])
            check.assert_called_once_with(self.project / "another", "codex", "native-cli")


if __name__ == "__main__":
    unittest.main()
