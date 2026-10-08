import importlib.util
import contextlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("agent_recovery", ROOT / ".agents/machine/scripts/agent_recovery.py")
RECOVERY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RECOVERY)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic recovery ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cwd = self.root / "checkout with spaces"
        self.cwd.mkdir()
        self.state = self.root / "state"
        self.env = mock.patch.dict("os.environ", {"AGENT_STATE_DIRECTORY": str(self.state)}, clear=False)
        self.env.start()
        self.addCleanup(self.env.stop)

    def write_codex(self, session="exact_id", source="cli"):
        path = self.root / "sessions/archive" / f"{session}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        events = [
            {"type": "session_meta", "payload": {"id": session, "cwd": str(self.cwd), "source": source}},
            {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "recover launch topic"}]}},
        ]
        path.write_text("\n".join(json.dumps(item) for item in events), encoding="utf-8")

    def write_claude(self, root, session="claude_id"):
        path = root / "project" / f"{session}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"type": "user", "sessionId": session, "cwd": str(self.cwd),
                                    "message": {"content": [{"type": "text", "text": "Claude recovery title"}]}}), encoding="utf-8")

    def test_search_reads_archive_and_filters_non_cli_helper(self):
        self.write_codex()
        results = RECOVERY.search(("codex",), topic="topic", roots={"codex": self.root / "sessions"})
        self.assertEqual(results[0]["id"], "exact_id")
        self.assertEqual(results[0]["status"], "unknown")
        self.write_codex("helper", "vscode")
        self.assertEqual([item["id"] for item in RECOVERY.search(("codex",), roots={"codex": self.root / "sessions"})], ["exact_id"])

    def test_search_uses_native_archives_titles_and_ids_before_counting(self):
        sessions = self.root / "sessions"
        sessions.mkdir()
        archive = self.root / "archived_sessions"
        original_root = self.root
        self.root = archive.parent
        self.write_codex("archived_id")
        source = archive / "archive" / "archived_id.jsonl"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text((original_root / "sessions/archive/archived_id.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
        (original_root / "sessions/archive/archived_id.jsonl").unlink()
        (self.root / "session_index.jsonl").write_text(json.dumps({"id": "archived_id", "thread_name": "Lost title"}), encoding="utf-8")
        self.assertEqual(RECOVERY.search(("codex",), topic="title", roots={"codex": sessions})[0]["id"], "archived_id")
        self.assertEqual(RECOVERY.search(("codex",), topic="archived_id", roots={"codex": sessions})[0]["title"], "Lost title")
        registry = RECOVERY._registry_root()
        registry.mkdir(parents=True)
        (registry / "archived_id.json").write_text(json.dumps({"session_id": "archived_id", "title": "Saved tab title"}), encoding="utf-8")
        self.assertEqual(RECOVERY.search(("codex",), topic="Lost title", roots={"codex": sessions})[0]["id"], "archived_id")
        self.assertEqual(RECOVERY.search(("codex",), topic="Saved tab title", roots={"codex": sessions})[0]["id"], "archived_id")
        with self.assertRaises(ValueError):
            RECOVERY.search(("codex",), roots={"codex": self.root / "missing"})
        with self.assertRaises(ValueError):
            RECOVERY.search(("codex",), count=0, roots={"codex": sessions})

    def test_live_and_pid_reuse_are_distinct(self):
        self.write_codex()
        item = RECOVERY.find("codex", "exact_id", {"codex": self.root / "sessions"})
        record = RECOVERY._registry_root() / "exact_id.json"
        record.parent.mkdir(parents=True)
        record.write_text(json.dumps({"pid": 7, "pid_started_at": 10, "host": "codex"}), encoding="utf-8")
        process = type("P", (), {"name": "codex", "started_at": 10})()
        self.assertEqual(RECOVERY.liveness(item, lambda _: process), "live")
        process.started_at = 20
        self.assertEqual(RECOVERY.liveness(item, lambda _: process), "closed")
        record.write_text(json.dumps({"pid": 7, "pid_started_at": "bad", "host": "codex"}), encoding="utf-8")
        self.assertEqual(RECOVERY.liveness(item, lambda _: process), "unknown")

    def test_rejects_flag_like_native_id_and_keeps_ambiguous_receipt(self):
        self.assertFalse(RECOVERY.SESSION_ID.fullmatch("-resume"))
        path = RECOVERY._claim("codex", "exact_id", "profile")
        RECOVERY._receipt_state(path, "codex", "exact_id", "profile", "ambiguous")
        with self.assertRaises(ValueError):
            RECOVERY._claim("codex", "exact_id", "profile")

    def test_receipt_waits_for_newer_closed_registration_before_reuse(self):
        registry = RECOVERY._registry_root() / "exact_id.json"
        registry.parent.mkdir(parents=True)
        registry.write_text(json.dumps({"pid": 7, "pid_started_at": 1, "host": "codex", "started_at": 1}), encoding="utf-8")
        receipt = RECOVERY._claim("codex", "exact_id", "profile")
        registry.write_text(json.dumps({"pid": 7, "pid_started_at": 1, "host": "codex", "started_at": 1}), encoding="utf-8")
        with self.assertRaises(ValueError):
            RECOVERY._claim("codex", "exact_id", "profile")
        created = json.loads(receipt.read_text(encoding="utf-8"))["created_at"]
        registry.write_text(json.dumps({"pid": 8, "pid_started_at": 2, "host": "codex", "started_at": created + 1}), encoding="utf-8")
        with mock.patch.object(RECOVERY, "liveness", return_value="closed"):
            self.assertTrue(RECOVERY._claim("codex", "exact_id", "profile").is_file())

    def test_two_processes_retire_one_completed_receipt_once(self):
        registry = RECOVERY._registry_root() / "race_id.json"
        registry.parent.mkdir(parents=True)
        registry.write_text(json.dumps({"pid": 7, "pid_started_at": 1, "host": "codex", "started_at": 1}), encoding="utf-8")
        receipt = RECOVERY._claim("codex", "race_id", "profile")
        created = json.loads(receipt.read_text(encoding="utf-8"))["created_at"]
        registry.write_text(json.dumps({"pid": 999999, "pid_started_at": 2, "host": "codex", "started_at": created + 1}), encoding="utf-8")
        code = "import importlib.util,sys; p=sys.argv[1]; s=importlib.util.spec_from_file_location('r',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m);\ntry: m._claim('codex','race_id','profile'); print('ok')\nexcept ValueError: print('blocked')"
        env = dict(os.environ)
        commands = [[sys.executable, "-c", code, str(ROOT / ".agents/machine/scripts/agent_recovery.py")] for _ in range(2)]
        results = [subprocess.Popen(command, stdout=subprocess.PIPE, text=True, env=env) for command in commands]
        output = [process.communicate(timeout=20)[0].strip() for process in results]
        self.assertEqual(sorted(output), ["blocked", "ok"])

    def test_open_uses_exact_resume_cwd_and_refuses_unknown_without_confirmation(self):
        self.write_codex()
        cli = mock.Mock()
        cli.resolve_tab_directory.side_effect = lambda value: Path(value)
        cli.resolve_codex_executable.return_value = ("native-codex", {})
        real_load = RECOVERY._load
        with mock.patch.object(RECOVERY, "_load", side_effect=lambda name: cli if name == "agent_cli" else real_load(name)), \
             mock.patch.object(RECOVERY, "_verify_codex_resume"), \
             mock.patch.object(RECOVERY, "_sync_codex"):
            with self.assertRaises(ValueError):
                RECOVERY.open_session("codex", "exact_id", roots={"codex": self.root / "sessions"})
            RECOVERY.open_session("codex", "exact_id", roots={"codex": self.root / "sessions"}, confirm_closed=True)
        cli.launch_tab.assert_called_once_with(self.cwd, "native-codex", mock.ANY,
                                                ["resume", "exact_id", "Continue the requested work."], clear=("TERM",),
                                                force={"CODEX_HOME": RECOVERY._profile("codex", self.root / "sessions")})

    def test_explicit_claude_profile_overrides_conflicting_environment_for_resume(self):
        profile = self.root / "alternate profile"
        projects = profile / "projects"
        self.write_claude(projects)
        cli = mock.Mock()
        cli.resolve_tab_directory.side_effect = lambda value: Path(value)
        seen = []
        cli.open_claude_tab.side_effect = lambda *args: seen.append(__import__("os").environ.get("CLAUDE_CONFIG_DIR"))
        real_load = RECOVERY._load
        with mock.patch.dict("os.environ", {"CLAUDE_CONFIG_DIR": "wrong profile"}, clear=False), \
             mock.patch.object(RECOVERY, "_load", side_effect=lambda name: cli if name == "agent_cli" else real_load(name)):
            RECOVERY.open_session("claude", "claude_id", roots={"claude": projects}, confirm_closed=True)
        self.assertEqual(seen, [RECOVERY._profile("claude", projects)])

    def test_packaged_resource_loads_peer_process_helper(self):
        path = ROOT / "plugins/machine/resources/machine/scripts/agent_recovery.py"
        if not path.is_file():
            self.skipTest("generated package has not been refreshed")
        spec = importlib.util.spec_from_file_location("packaged_agent_recovery", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(callable(module._load("register_session").build_process_lookup))

    def test_loader_caches_native_exception_identity(self):
        self.assertIs(RECOVERY._load("agent_cli").LaunchTimeout, RECOVERY._load("agent_cli").LaunchTimeout)

    def test_main_reports_native_launch_failure(self):
        cli = RECOVERY._load("agent_cli")
        with mock.patch.object(RECOVERY, "open_session", side_effect=cli.LaunchError("terminal unavailable")), \
             contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(RECOVERY.main(["open", "--host", "codex", "--id", "exact_id"]), 1)

    def test_main_reports_native_launch_timeout_as_three(self):
        cli = RECOVERY._load("agent_cli")
        with mock.patch.object(RECOVERY, "open_session", side_effect=cli.LaunchTimeout("unknown launch")), \
             contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(RECOVERY.main(["open", "--host", "codex", "--id", "exact_id"]), 3)

    def test_recover_reports_partial_launch_without_losing_timeout_exit(self):
        cli = RECOVERY._load("agent_cli")
        items = [{"host": "codex", "id": "first_id"}, {"host": "codex", "id": "second_id"}]
        output = io.StringIO()
        with mock.patch.object(RECOVERY, "search", return_value=items), \
             mock.patch.object(RECOVERY, "open_session", side_effect=[items[0], cli.LaunchTimeout("unknown second launch")]), \
             contextlib.redirect_stderr(output):
            self.assertEqual(RECOVERY.main(["recover", "--host", "codex", "--select", "codex:first_id", "--select", "codex:second_id"]), 3)
        self.assertIn("Already opened: codex:first_id", output.getvalue())

    def test_recover_rejects_duplicate_selection_before_launch(self):
        item = {"host": "codex", "id": "exact_id"}
        with mock.patch.object(RECOVERY, "search", return_value=[item]), \
             mock.patch.object(RECOVERY, "open_session") as opened, \
             contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(RECOVERY.main(["recover", "--host", "codex", "--select", "codex:exact_id", "--select", "codex:exact_id"]), 1)
        opened.assert_not_called()


if __name__ == "__main__":
    unittest.main()
