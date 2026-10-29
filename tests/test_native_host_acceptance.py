import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
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

    def test_fixture_selects_required_packages_without_personal(self):
        NATIVE.write_fixture(self.project)
        value = json.loads(
            (self.project / ".agents" / "plugins.json").read_text(encoding="utf-8")
        )
        self.assertEqual(list(NATIVE.IDENTITIES), value["plugins"])
        self.assertNotIn("personal@tj-agents", value["plugins"])

    def test_claude_plugin_inventory_requires_listed_enabled_identities(self):
        completed = SimpleNamespace(
            stdout=json.dumps(
                [{"id": identity, "enabled": True} for identity in NATIVE.IDENTITIES]
            )
        )
        NATIVE.require_plugins(NATIVE.claude_plugin_inventory(completed))
        completed = SimpleNamespace(stdout=json.dumps({"installed": []}))
        with self.assertRaisesRegex(NATIVE.AcceptanceError, "did not return a list"):
            NATIVE.claude_plugin_inventory(completed)

    def test_plugin_discovery_requires_enabled_installed_identities(self):
        inventory = {
            "installed": [
                {"pluginId": identity, "installed": True, "enabled": True}
                for identity in NATIVE.IDENTITIES
            ]
        }
        NATIVE.require_plugins(inventory)
        inventory["installed"][-1]["enabled"] = False
        with self.assertRaisesRegex(NATIVE.AcceptanceError, "engineering@tj-agents"):
            NATIVE.require_plugins(inventory)

    def test_claude_initialize_requires_qualified_command_inventory(self):
        NATIVE.require_claude_discovery(
            {"commands": [{"name": "workflow:run"}, {"name": "engineering:commit"}]}
        )
        with self.assertRaisesRegex(NATIVE.AcceptanceError, "workflow:run"):
            NATIVE.require_claude_discovery(
                {"commands": [{"name": "run"}, {"name": "engineering:commit"}]}
            )

    def test_discovery_rejects_substrings_without_exact_skill_names(self):
        with self.assertRaisesRegex(NATIVE.AcceptanceError, "workflow skill"):
            NATIVE.require_discovery(
                {"description": "workflow run engineering commit"}, "native"
            )
        with self.assertRaisesRegex(NATIVE.AcceptanceError, "workflow skill"):
            NATIVE.require_discovery(
                {"commands": [{"name": "run"}, {"name": "commit"}]}, "native"
            )
        NATIVE.require_discovery(
            {
                "commands": [
                    {"name": "run", "pluginId": "workflow@tj-agents"},
                    {
                        "name": "commit",
                        "path": "/cache/plugins/engineering/skills/commit/SKILL.md",
                    },
                ]
            },
            "native",
        )

    def test_restarted_startup_hooks_require_trusted_current_hashes(self):
        hooks = {
            "data": [
                {
                    "hooks": [
                        {
                            "pluginId": "base@tj-agents",
                            "source": "plugin",
                            "enabled": True,
                            "key": "base",
                            "trustStatus": "trusted",
                            "currentHash": "sha256:base",
                            "trustedHash": "sha256:base",
                        }
                    ]
                }
            ]
        }
        trusted = {"base": {"trusted_hash": "sha256:base"}}
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
        environment = NATIVE.isolated_environment(
            temporary, codex, claude, "http://127.0.0.1:1/v1"
        )
        self.assertEqual(
            [str(codex.resolve().parent), str(claude.resolve().parent)],
            environment["PATH"].split(os.pathsep)[:2],
        )
        self.assertEqual(Path(environment["HOME"]), self.root / "temporary" / "home")
        self.assertEqual(
            Path(environment["USERPROFILE"]), self.root / "temporary" / "home"
        )
        self.assertTrue(Path(environment["CODEX_HOME"]).is_dir())
        self.assertTrue(Path(environment["CLAUDE_CONFIG_DIR"]).is_dir())
        self.assertTrue(Path(environment["AGENT_STATE_DIRECTORY"]).is_dir())
        config = (Path(environment["CODEX_HOME"]) / "config.toml").read_text(
            encoding="utf-8"
        )
        self.assertTrue('cli_auth_credentials_store = "file"' in config)
        self.assertTrue("hooks = true" in config)

    def codex_completion(self):
        package = self.root / "installed Base"
        roots = [SimpleNamespace(identity="base@tj-agents", root=package)]
        event = {
            "method": "hook/completed",
            "params": {
                "threadId": "current-session",
                "run": {
                    "eventName": "sessionStart",
                    "source": "plugin",
                    "sourcePath": str(package / "hooks" / "codex.json"),
                    "status": "completed",
                    "entries": [],
                },
            },
        }
        return (roots, event)

    def test_codex_native_completion_allows_empty_context(self):
        codex_completion = self.codex_completion()
        roots, event = codex_completion
        self.assertEqual(
            NATIVE.require_codex_startup([event], roots, "current-session"),
            event["params"]["run"],
        )

    def test_codex_native_completion_rejects_uncorrelated_events(self):
        for location, key, value in [
            ("event", "method", "hook/started"),
            ("params", "threadId", "old-session"),
            ("run", "source", "config"),
            ("run", "eventName", "preToolUse"),
            ("run", "sourcePath", "/other/base/hooks/codex.json"),
            ("run", "sourcePath", None),
        ]:
            with self.subTest(location=location, key=key, value=value):
                codex_completion = self.codex_completion()
                roots, event = codex_completion
                target = {
                    "event": event,
                    "params": event["params"],
                    "run": event["params"]["run"],
                }[location]
                target[key] = value
                with self.assertRaisesRegex(
                    NATIVE.AcceptanceError, "no native SessionStart completion"
                ):
                    NATIVE.require_codex_startup([event], roots, "current-session")

    def test_codex_native_completion_rejects_unsuccessful_status(self):
        for status in ["failed", "blocked", "running", None]:
            with self.subTest(status=status):
                codex_completion = self.codex_completion()
                roots, event = codex_completion
                event["params"]["run"]["status"] = status
                with self.assertRaises(NATIVE.RequiredHookError):
                    NATIVE.require_codex_startup([event], roots, "current-session")

    def test_codex_requires_native_completion_even_when_401_is_present(self):
        codex_completion = self.codex_completion()
        roots, _ = codex_completion
        transcript = self.root / "session.jsonl"
        transcript.write_text(
            json.dumps(
                {
                    "type": "event_msg",
                    "payload": {
                        "type": "task_complete",
                        "error": {"message": "401 Unauthorized"},
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        NATIVE.require_failed_turn(transcript, 0.1)
        with self.assertRaisesRegex(
            NATIVE.AcceptanceError, "no native SessionStart completion"
        ):
            NATIVE.require_codex_startup([], roots, "current-session")

    def test_turn_requires_unauthenticated_completion(self):
        for error in [None, {"message": "500 Internal Server Error"}]:
            with self.subTest(error=error):
                transcript = self.root / "session.jsonl"
                transcript.write_text(
                    json.dumps(
                        {
                            "type": "event_msg",
                            "payload": {"type": "task_complete", "error": error},
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(
                    NATIVE.AcceptanceError, "expected unauthenticated 401"
                ):
                    NATIVE.require_failed_turn(transcript, 0.1)

    def test_turn_waits_for_initial_transcript_appearance(self):
        entries = [
            {
                "payload": {
                    "type": "task_complete",
                    "error": {"message": "401 Unauthorized"},
                }
            }
        ]
        with mock.patch.object(
            NATIVE, "transcript_entries", side_effect=[None, entries]
        ):
            self.assertEqual(
                entries, NATIVE.require_failed_turn(self.root / "session.jsonl", 0.2)
            )

    def claude_completion(self):
        common = {
            "type": "system",
            "hook_id": "hook",
            "session_id": "session",
            "hook_event": "SessionStart",
            "hook_name": "SessionStart:startup",
        }
        return [
            {**common, "subtype": "hook_started"},
            {
                **common,
                "subtype": "hook_response",
                "outcome": "success",
                "exit_code": 0,
                "output": "",
            },
        ]

    def test_claude_native_completion_allows_empty_context(self):
        claude_completion = self.claude_completion()
        self.assertEqual(
            NATIVE.require_claude_startup(claude_completion), claude_completion[1]
        )

    def test_claude_native_completion_requires_matching_start(self):
        for key, value in [
            ("hook_id", "other"),
            ("session_id", "old"),
            ("hook_event", "Stop"),
            ("hook_name", "SessionStart:resume"),
            ("subtype", "hook_started"),
        ]:
            with self.subTest(key=key, value=value):
                claude_completion = self.claude_completion()
                claude_completion[1][key] = value
                with self.assertRaisesRegex(
                    NATIVE.AcceptanceError, "no native SessionStart completion"
                ):
                    NATIVE.require_claude_startup(claude_completion)

    def test_claude_native_completion_rejects_hook_failure(self):
        for outcome, exit_code in [("error", 1), ("success", 1), ("error", 0)]:
            with self.subTest(outcome=outcome, exit_code=exit_code):
                claude_completion = self.claude_completion()
                claude_completion[1].update(outcome=outcome, exit_code=exit_code)
                with self.assertRaises(NATIVE.RequiredHookError):
                    NATIVE.require_claude_startup(claude_completion)

    def test_failure_probe_requires_current_native_failed_completion(self):

        def early_failure():
            raise NATIVE.AcceptanceError("installation failed before launch")

        with self.assertRaisesRegex(
            NATIVE.AcceptanceError, "installation failed before launch"
        ):
            NATIVE.require_failure_probe("codex", early_failure)

    def test_failure_probe_rejects_wrong_host_or_blocked_completion(self):
        for host, status in [("claude", "failed"), ("codex", "blocked")]:
            with self.subTest(host=host, status=status):

                def fail(host=host, status=status):
                    raise NATIVE.RequiredHookError(host, {"status": status})

                with self.assertRaisesRegex(NATIVE.AcceptanceError, "different reason"):
                    NATIVE.require_failure_probe("codex", fail)

    def test_failure_probe_accepts_current_failed_completion(self):
        codex_completion = self.codex_completion()
        roots, event = codex_completion
        event["params"]["run"]["status"] = "failed"
        result = NATIVE.require_failure_probe(
            "codex",
            lambda: NATIVE.require_codex_startup([event], roots, "current-session"),
        )
        self.assertEqual(result, event["params"]["run"])

    def test_failure_probe_rejects_success(self):
        with self.assertRaisesRegex(
            NATIVE.AcceptanceError, "accepted a deliberately failed"
        ):
            NATIVE.require_failure_probe("codex", lambda: None)


if __name__ == "__main__":
    unittest.main()
