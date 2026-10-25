import hashlib
import importlib.util
import json
import sqlite3
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "native_host_acceptance.py"
specification = importlib.util.spec_from_file_location("native_host_acceptance", SCRIPT)
NATIVE = importlib.util.module_from_spec(specification)
specification.loader.exec_module(NATIVE)


class NativeHostAcceptanceTests(unittest.TestCase):
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

    def test_missing_or_malformed_receipt_fails_closed(self):
        store = SimpleNamespace(connect=lambda path: None, get_session=lambda connection, handle: None)
        register = SimpleNamespace(build_process_lookup=lambda: lambda pid: None)
        with self.assertRaisesRegex(NATIVE.AcceptanceError, "missing or malformed codex receipt"):
            NATIVE.require_receipt(self.state, store, register, "codex", "session", self.project, 1)
        receipt = self.state / "cli-sessions" / "session.json"
        receipt.parent.mkdir(parents=True)
        receipt.write_text("not-json", encoding="utf-8")
        with self.assertRaisesRegex(NATIVE.AcceptanceError, "missing or malformed codex receipt"):
            NATIVE.require_receipt(self.state, store, register, "codex", "session", self.project, 1)

    def test_receipt_uses_explicit_isolated_store_and_host_descendant(self):
        value = self.receipt()
        connection = SimpleNamespace(close=lambda: None)
        connected = []
        store = SimpleNamespace(
            connect=lambda path: connected.append(path) or connection,
            get_session=lambda current, handle: dict(value),
        )
        processes = {
            42: SimpleNamespace(pid=42, ppid=7, name="codex.exe", started_at=100.0),
            7: SimpleNamespace(pid=7, ppid=1, name="shell.exe", started_at=99.0),
        }
        register = SimpleNamespace(build_process_lookup=lambda: processes.get)
        NATIVE.require_receipt(self.state, store, register, "codex", "session", self.project, 7)
        self.assertEqual([self.state / "sessions.db"], connected)
        with self.assertRaisesRegex(NATIVE.AcceptanceError, "not descended"):
            NATIVE.require_receipt(self.state, store, register, "codex", "session", self.project, 99)

    def test_locked_agent_store_fails_closed(self):
        self.receipt()
        store = SimpleNamespace(connect=lambda path: (_ for _ in ()).throw(sqlite3.OperationalError("locked")))
        processes = {
            42: SimpleNamespace(pid=42, ppid=7, name="codex.exe", started_at=100.0),
            7: SimpleNamespace(pid=7, ppid=1, name="shell.exe", started_at=99.0),
        }
        register = SimpleNamespace(build_process_lookup=lambda: processes.get)
        with self.assertRaisesRegex(NATIVE.AcceptanceError, "Agent Store is unavailable"):
            NATIVE.require_receipt(self.state, store, register, "codex", "session", self.project, 7)

    def test_receipt_and_agent_store_must_match(self):
        value = self.receipt()
        connection = SimpleNamespace(close=lambda: None)
        store = SimpleNamespace(
            connect=lambda path: connection,
            get_session=lambda current, handle: {**value, "cwd": "wrong"},
        )
        processes = {
            42: SimpleNamespace(pid=42, ppid=7, name="codex.exe", started_at=100.0),
            7: SimpleNamespace(pid=7, ppid=1, name="shell.exe", started_at=99.0),
        }
        register = SimpleNamespace(build_process_lookup=lambda: processes.get)
        with self.assertRaisesRegex(NATIVE.AcceptanceError, "Agent Store row does not match"):
            NATIVE.require_receipt(self.state, store, register, "codex", "session", self.project, 7)

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
            {"pluginId": "machine@tj-agents", "source": "plugin", "enabled": True, "key": "machine", "trustStatus": "trusted", "currentHash": "sha256:machine", "trustedHash": "sha256:machine"},
        ]}]}
        trusted = {
            "base": {"trusted_hash": "sha256:base"},
            "machine": {"trusted_hash": "sha256:machine"},
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
