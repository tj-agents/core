import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "native_host_acceptance.py"
specification = importlib.util.spec_from_file_location("native_host_acceptance", SCRIPT)
NATIVE = importlib.util.module_from_spec(specification)
specification.loader.exec_module(NATIVE)


class NativeHostAcceptanceTests(unittest.TestCase):
    def test_codex_requires_a_matching_native_hook_completion(self):
        source = Path("base/hooks/codex.json").resolve()
        run = {"id": "current", "eventName": "sessionStart", "source": "plugin",
               "sourcePath": str(source), "status": "completed", "entries": []}
        messages = [{"method": "hook/started", "params": {"run": run}},
                    {"method": "hook/completed", "params": {"run": run}}]
        self.assertEqual(run, NATIVE.require_codex_hook(messages, source))
        for invalid in ([], messages[1:], messages + messages[1:]):
            with self.assertRaises(NATIVE.AcceptanceError):
                NATIVE.require_codex_hook(invalid, source)
        with self.assertRaises(NATIVE.AcceptanceError):
            NATIVE.require_codex_hook(messages, source.parent / "different.json")
        with self.assertRaises(NATIVE.AcceptanceError):
            NATIVE.require_codex_hook(messages, source, "probe")
        run.update(status="failed", entries=[{"kind": "error", "text": "hook exited with code 1"}])
        self.assertEqual(run, NATIVE.require_codex_hook(messages, source, "probe"))

    def test_claude_requires_a_current_native_hook_response(self):
        run = {"type": "system", "subtype": "hook_response", "hook_event": "SessionStart",
               "hook_id": "current", "exit_code": 0, "stderr": ""}
        started = {"type": "system", "subtype": "hook_started", "hook_event": "SessionStart", "hook_id": "current"}
        messages = [started, run]
        self.assertEqual(run, NATIVE.require_claude_hook(messages))
        for invalid in ([], [run], messages + [run]):
            with self.assertRaises(NATIVE.AcceptanceError):
                NATIVE.require_claude_hook(invalid)
        with self.assertRaises(NATIVE.AcceptanceError):
            NATIVE.require_claude_hook(messages, "probe")
        run.update(exit_code=1, stderr="probe")
        self.assertEqual(run, NATIVE.require_claude_hook(messages, "probe"))
        with self.assertRaises(NATIVE.AcceptanceError):
            NATIVE.require_claude_hook(messages, "another failure")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
    def test_fixture_selects_required_packages_without_personal(self):
        NATIVE.write_fixture(self.project)
        value = json.loads((self.project / ".agents" / "plugins.json").read_text(encoding="utf-8"))
        self.assertEqual(list(NATIVE.IDENTITIES), value["plugins"])
        self.assertNotIn("personal@tj-agents", value["plugins"])

    def test_claude_plugin_inventory_requires_listed_enabled_identities(self):
        completed = SimpleNamespace(stdout=json.dumps([
            {"id": identity, "enabled": True} for identity in NATIVE.IDENTITIES
        ]))
        NATIVE.require_plugins(NATIVE.claude_plugin_inventory(completed))
        completed = SimpleNamespace(stdout=json.dumps({"installed": []}))
        with self.assertRaisesRegex(NATIVE.AcceptanceError, "did not return a list"):
            NATIVE.claude_plugin_inventory(completed)

    def test_plugin_discovery_requires_enabled_installed_identities(self):
        inventory = {"installed": [
            {"pluginId": identity, "installed": True, "enabled": True}
            for identity in NATIVE.IDENTITIES
        ]}
        NATIVE.require_plugins(inventory)
        inventory["installed"][-1]["enabled"] = False
        with self.assertRaisesRegex(NATIVE.AcceptanceError, "engineering@tj-agents"):
            NATIVE.require_plugins(inventory)

    def test_transcript_requires_base_context_and_unauthenticated_completion(self):
        package = self.root / "base"
        contract = package / "tier.json"
        contract.parent.mkdir(parents=True)
        contract.write_text(json.dumps({"tier": "base", "applies": "always", "session_context": "Use the clipboard."}), encoding="utf-8")
        transcript = self.root / "session.jsonl"
        transcript.write_text(
            json.dumps({"type": "response_item", "payload": {"content": "Tier gate - which standards apply in this project\nUbiquitous, always applies: base, engineering, workflow.\nUse the clipboard."}}) + "\n"
            + json.dumps({"type": "event_msg", "payload": {"type": "task_complete", "error": {"message": "401 Unauthorized"}}}) + "\n",
            encoding="utf-8",
        )
        NATIVE.require_failed_turn(transcript, package, 0.1)
        transcript.write_text(json.dumps({"type": "event_msg", "payload": {"type": "task_complete", "error": None}}) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(NATIVE.AcceptanceError, "Base context"):
            NATIVE.require_failed_turn(transcript, package, 0.1)

    def test_base_without_session_context_accepts_an_empty_hook_result(self):
        package = self.root / "base"
        package.mkdir()
        (package / "tier.json").write_text(json.dumps({"tier": "base", "applies": "always"}), encoding="utf-8")
        NATIVE.require_base_evidence("", package, "native hook")

    def test_transcript_waits_for_initial_appearance(self):
        package = self.root / "base"
        contract = package / "tier.json"
        contract.parent.mkdir(parents=True)
        contract.write_text(json.dumps({"tier": "base", "applies": "always", "session_context": "Use the clipboard."}), encoding="utf-8")
        entries = [
            {"type": "response_item", "payload": {"content": "Tier gate - which standards apply in this project\nUbiquitous, always applies: base, engineering, workflow.\nUse the clipboard."}},
            {"type": "event_msg", "payload": {"type": "task_complete", "error": {"message": "401 Unauthorized"}}},
        ]
        with mock.patch.object(NATIVE, "transcript_entries", side_effect=[None, entries]):
            NATIVE.require_failed_turn(self.root / "session.jsonl", package, 0.2)

    def test_claude_initialize_requires_qualified_command_inventory(self):
        NATIVE.require_claude_discovery({"commands": [
            {"name": "workflow:run"}, {"name": "engineering:commit"},
        ]})
        with self.assertRaisesRegex(NATIVE.AcceptanceError, "workflow:run"):
            NATIVE.require_claude_discovery({"commands": [{"name": "run"}, {"name": "engineering:commit"}]})

    def test_discovery_rejects_substrings_without_exact_skill_names(self):
        with self.assertRaisesRegex(NATIVE.AcceptanceError, "workflow skill"):
            NATIVE.require_discovery({"description": "workflow run engineering commit"}, "native")
        with self.assertRaisesRegex(NATIVE.AcceptanceError, "workflow skill"):
            NATIVE.require_discovery({"commands": [{"name": "run"}, {"name": "commit"}]}, "native")
        NATIVE.require_discovery({"commands": [
            {"name": "run", "pluginId": "workflow@tj-agents"},
            {"name": "commit", "path": "/cache/plugins/engineering/skills/commit/SKILL.md"},
        ]}, "native")

    def test_restarted_startup_hooks_require_trusted_current_hashes(self):
        hooks = {"data": [{"hooks": [
            {"pluginId": "base@tj-agents", "source": "plugin", "enabled": True, "key": "base", "trustStatus": "trusted", "currentHash": "sha256:base", "trustedHash": "sha256:base"},
        ]}]}
        trusted = {
            "base": {"trusted_hash": "sha256:base"},
        }
        NATIVE.require_startup_hooks(hooks, trusted=True, trusted_hashes=trusted)
        trusted["base"]["trusted_hash"] = "sha256:stale"
        with self.assertRaisesRegex(NATIVE.AcceptanceError, "did not trust"):
            NATIVE.require_startup_hooks(hooks, trusted=True, trusted_hashes=trusted)

    def test_isolated_environment_precedes_direct_native_directories(self):
        codex = self.root / "codex" / "codex"
        claude = self.root / "claude" / "claude"
        codex.parent.mkdir()
        claude.parent.mkdir()
        codex.write_text("", encoding="utf-8")
        claude.write_text("", encoding="utf-8")
        temporary = self.root / "temporary"
        environment = NATIVE.isolated_environment(temporary, codex, claude, 'http://127.0.0.1:1/v1')
        self.assertEqual([str(codex.resolve().parent), str(claude.resolve().parent)], environment["PATH"].split(__import__("os").pathsep)[:2])
        self.assertEqual(Path(environment["HOME"]), self.root / "temporary" / "home")
        self.assertEqual(Path(environment["USERPROFILE"]), self.root / "temporary" / "home")
        self.assertTrue(Path(environment["CODEX_HOME"]).is_dir())
        self.assertTrue(Path(environment["CLAUDE_CONFIG_DIR"]).is_dir())
        self.assertTrue(Path(environment["AGENT_STATE_DIRECTORY"]).is_dir())
        config = (Path(environment["CODEX_HOME"]) / "config.toml").read_text(encoding="utf-8")
        self.assertIn('cli_auth_credentials_store = "file"', config)
        self.assertIn('hooks = true', config)



if __name__ == "__main__":
    unittest.main()
