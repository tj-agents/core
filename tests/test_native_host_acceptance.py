import hashlib
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
OBSERVER = Path(__file__).resolve().parents[1] / "scripts" / "native_startup_observer.py"
specification = importlib.util.spec_from_file_location("native_host_acceptance", SCRIPT)
NATIVE = importlib.util.module_from_spec(specification)
specification.loader.exec_module(NATIVE)


class NativeHostAcceptanceTests(unittest.TestCase):
    def test_observer_imports_the_nested_installed_startup_binding(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / 'state'
            binding = state / 'bin' / '.agents' / 'agent' / 'runtime' / 'startup_binding.py'
            binding.parent.mkdir(parents=True)
            binding.write_text('', encoding='utf-8')
            result = subprocess.run([sys.executable, '-B', str(OBSERVER), '--help'], capture_output=True,
                                    text=True, encoding='utf-8', env={**os.environ,
                                                                       'AGENT_STATE_DIRECTORY': str(state)})
        self.assertEqual(0, result.returncode, result.stderr)

    def test_an_early_failure_cannot_reuse_a_previous_failed_observer_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            evidence = Path(temporary)
            receipt = evidence / 'codex-startup-observer.json'
            receipt.write_text(json.dumps({'state': 'failed', 'error':
                'workflow@tj-agents native-required-hook-failure-probe'}), encoding='utf-8')
            operation = mock.Mock(side_effect=NATIVE.AcceptanceError('installation failed before launch'))
            with self.assertRaisesRegex(NATIVE.AcceptanceError, 'no valid receipt'):
                NATIVE.require_failure_probe('codex', evidence, operation)
            self.assertFalse(receipt.exists())

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.state = self.root / "state"

    def receipt(self):
        path = self.state / "cli-sessions" / "session.json"
        path.parent.mkdir(parents=True)
        value = {
            "host": "codex", "session_id": "session", "cwd": str(self.project),
            "pid": 42, "pid_started_at": 100.0,
        }
        path.write_text(json.dumps(value), encoding="utf-8")
        return value

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
        contract = package / ".agents" / "base" / "policy" / "task-routing" / "SKILL.md"
        contract.parent.mkdir(parents=True)
        contract.write_text("task routing", encoding="utf-8")
        transcript = self.root / "session.jsonl"
        digest = hashlib.sha256(b"task routing").hexdigest()
        transcript.write_text(
            json.dumps({"type": "response_item", "payload": {"content": f"base:task-routing {digest}"}}) + "\n"
            + json.dumps({"type": "event_msg", "payload": {"type": "task_complete", "error": {"message": "401 Unauthorized"}}}) + "\n",
            encoding="utf-8",
        )
        NATIVE.require_failed_turn(transcript, package, 0.1)
        transcript.write_text(json.dumps({"type": "event_msg", "payload": {"type": "task_complete", "error": None}}) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(NATIVE.AcceptanceError, "Base context"):
            NATIVE.require_failed_turn(transcript, package, 0.1)

    def test_transcript_waits_for_initial_appearance(self):
        package = self.root / "base"
        contract = package / ".agents" / "base" / "policy" / "task-routing" / "SKILL.md"
        contract.parent.mkdir(parents=True)
        contract.write_text("task routing", encoding="utf-8")
        digest = hashlib.sha256(b"task routing").hexdigest()
        entries = [
            {"type": "response_item", "payload": {"content": f"base:task-routing {digest}"}},
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
