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

    def test_open_main_preserves_codex_task_recovery_authority_and_limits_file(self):
        self.write_codex()
        prompt = self.root / "recovery prompt é ' $().txt"
        content = "Observed follow-up blocker: proxy said 'unavailable'; $(retry) & <none>."
        content = "\n".join((
            content,
            "Canonical Goal: C:/private/GOAL.md",
            "Actual authorization: User authorized exact-owner recovery.",
            "Provenance: recorded user request.",
            "Authorized scope: inspect and reopen the exact owner.",
            "Limits: no settings changes.",
            "Holds: approval review remains a gate.",
            "Remaining gates: verify owner identity.",
        ))
        prompt.write_text(content, encoding="utf-8")
        original = prompt.read_bytes()
        cli = RECOVERY._load("agent_cli")
        with mock.patch.object(cli, "resolve_codex_executable", return_value=("native-codex", {})), \
             mock.patch.object(cli, "launch_tab") as launch, \
             mock.patch.object(RECOVERY, "_verify_codex_resume"), \
             mock.patch.object(RECOVERY, "_sync_codex"), \
             contextlib.redirect_stdout(io.StringIO()):
            code = RECOVERY.main([
                "open", "--host", "codex", "--id", "exact_id", "--confirm-closed",
                "--codex-history-root", str(self.root / "sessions"), "--prompt-path", str(prompt),
            ])
        self.assertEqual(0, code)
        arguments = launch.call_args.args[3]
        self.assertEqual("resume", arguments[0])
        self.assertEqual("exact_id", arguments[1])
        self.assertEqual(
            f"Read the file at {prompt.resolve()} and follow its instructions, working from the current directory.",
            arguments[2],
        )
        self.assertNotIn(content, arguments)
        self.assertEqual(original, prompt.read_bytes())

    def test_open_session_preserves_claude_task_recovery_authority_and_limits_file(self):
        profile = self.root / "alternate profile"
        projects = profile / "projects"
        self.write_claude(projects)
        prompt = self.root / "claude recovery authority.txt"
        content = """Host: claude
Native session ID: claude_id
Canonical Goal: C:/private/GOAL.md
Actual authorization: User authorized exact-owner recovery.
Provenance: recorded user request.
Authorized scope: inspect and reopen the exact owner.
Limits: no settings changes.
Holds: approval review remains a gate.
Remaining gates: verify owner identity.
Observed blocker: no send was attempted."""
        prompt.write_text(content, encoding="utf-8")
        original = prompt.read_bytes()
        cli = RECOVERY._load("agent_cli")
        with mock.patch.object(cli, "open_claude_tab") as launch:
            RECOVERY.open_session(
                "claude",
                "claude_id",
                prompt=None,
                roots={"claude": projects},
                confirm_closed=True,
                prompt_path=prompt,
                cli=cli,
            )
        arguments = launch.call_args.args[2]
        self.assertEqual("--resume", arguments[0])
        self.assertEqual("claude_id", arguments[1])
        self.assertEqual(
            f"Read the file at {prompt.resolve()} and follow its instructions, working from the current directory.",
            arguments[2],
        )
        self.assertNotIn(content, arguments)
        self.assertEqual(original, prompt.read_bytes())

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

    def test_sync_codex_loads_the_python_sync_module_on_windows(self):
        sync = mock.Mock()
        sync.SyncError = RECOVERY._load("codex_marketplace_sync").SyncError
        with mock.patch.object(RECOVERY.os, "name", "nt"), \
             mock.patch.object(RECOVERY, "_load", return_value=sync):
            RECOVERY._sync_codex("native-codex", self.cwd)
        sync.sync_codex_standards.assert_called_once_with("native-codex", self.cwd, out=mock.ANY)

    def test_sync_codex_swallows_a_sync_error_rather_than_raising(self):
        sync = RECOVERY._load("codex_marketplace_sync")
        with mock.patch.object(RECOVERY.os, "name", "nt"), \
             mock.patch.object(sync, "sync_codex_standards", side_effect=sync.SyncError("offline")), \
             mock.patch.object(RECOVERY, "_load", return_value=sync):
            RECOVERY._sync_codex("native-codex", self.cwd)

    def test_sync_codex_is_a_no_op_off_windows(self):
        with mock.patch.object(RECOVERY.os, "name", "posix"), \
             mock.patch.object(RECOVERY, "_load") as loader:
            RECOVERY._sync_codex("native-codex", self.cwd)
        loader.assert_not_called()

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

    def roots(self):
        claude = self.root / "claude projects"
        return claude, {"codex": self.root / "sessions", "claude": claude}

    def test_reopen_resolves_an_exact_id_in_either_host_without_a_host_argument(self):
        self.write_codex()
        claude, roots = self.roots()
        self.write_claude(claude)
        self.assertEqual("codex", RECOVERY.resolve_target("exact_id", roots=roots)["host"])
        self.assertEqual("claude", RECOVERY.resolve_target("claude_id", roots=roots)["host"])

    def test_reopen_resolves_a_topic_and_a_directory_across_hosts_and_refuses_ambiguity(self):
        self.write_codex()
        claude, roots = self.roots()
        self.write_claude(claude)
        self.assertEqual("claude_id", RECOVERY.resolve_target("Claude recovery title", roots=roots)["id"])
        with self.assertRaisesRegex(ValueError, "More than one session matched"):
            RECOVERY.resolve_target(str(self.cwd), roots=roots)
        self.assertIn(RECOVERY.resolve_target(str(self.cwd), roots=roots, pick_latest=True)["id"], {"exact_id", "claude_id"})
        with self.assertRaisesRegex(ValueError, "No Claude or Codex session matched"):
            RECOVERY.resolve_target("no such topic", roots=roots)

    def test_latest_prefers_a_live_match_over_a_newer_closed_one(self):
        found = [{"host": "claude", "id": "new", "status": "closed", "activity": "2", "cwd": str(self.cwd), "title": None, "preview": ""},
                 {"host": "codex", "id": "old", "status": "live", "activity": "1", "cwd": str(self.cwd), "title": None, "preview": ""}]
        with mock.patch.object(RECOVERY, "search", side_effect=lambda hosts, *_: [item for item in found if item["host"] in hosts]):
            self.assertEqual("old", RECOVERY.resolve_target("topic", pick_latest=True)["id"])

    def test_reopen_bare_word_is_a_topic_even_when_a_directory_has_that_name(self):
        self.write_codex()
        _, roots = self.roots()
        (self.root / "topic_dir_probe").mkdir()
        previous = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)
        with mock.patch.object(RECOVERY, "search", return_value=[]) as search:
            with self.assertRaises(ValueError):
                RECOVERY.resolve_target("topic_dir_probe", roots=roots)
        self.assertEqual(("topic_dir_probe", None), search.call_args.args[1:3])

    def test_reopen_closed_session_opens_in_its_own_host(self):
        self.write_codex()
        claude, roots = self.roots()
        self.write_claude(claude)
        focus = mock.Mock()
        with mock.patch.object(RECOVERY, "liveness", return_value="closed"), \
             mock.patch.object(RECOVERY, "open_session", return_value={"host": "claude", "id": "claude_id"}) as opened:
            result = RECOVERY.reopen("claude_id", roots=roots, focus=focus)
        self.assertEqual("opened", result["action"])
        self.assertEqual(("claude", "claude_id"), opened.call_args.args[:2])
        focus.assert_not_called()

    def test_reopen_live_session_focuses_its_tab_and_never_launches_a_second_writer(self):
        self.write_codex()
        _, roots = self.roots()
        focus = mock.Mock()
        with mock.patch.object(RECOVERY, "liveness", return_value="live"), \
             mock.patch.object(RECOVERY, "open_session") as opened:
            result = RECOVERY.reopen("exact_id", roots=roots, focus=focus)
        self.assertEqual("focused", result["action"])
        focus.assert_called_once_with("codex", "exact_id")
        opened.assert_not_called()

    def test_reopen_live_session_with_unfocusable_tab_fails_without_launching(self):
        self.write_codex()
        _, roots = self.roots()
        focus = mock.Mock(side_effect=ValueError("could not be focused"))
        with mock.patch.object(RECOVERY, "liveness", return_value="live"), \
             mock.patch.object(RECOVERY, "open_session") as opened:
            with self.assertRaisesRegex(ValueError, "could not be focused"):
                RECOVERY.reopen("exact_id", roots=roots, focus=focus)
        opened.assert_not_called()

    def test_reopen_unknown_session_is_still_refused_without_confirmation(self):
        self.write_codex()
        _, roots = self.roots()
        focus = mock.Mock()
        with self.assertRaisesRegex(ValueError, "conflicting or incomplete live identity"):
            RECOVERY.reopen("exact_id", roots=roots, focus=focus)
        focus.assert_not_called()

    def test_focus_session_runs_the_peer_cli_focus_and_reports_failure(self):
        done = subprocess.CompletedProcess([], 0, "", "")
        with mock.patch.object(RECOVERY.subprocess, "run", return_value=done) as run:
            RECOVERY.focus_session("codex", "exact_id")
        self.assertEqual(["--session", "exact_id", "--focus"], run.call_args.args[0][-3:])
        failed = subprocess.CompletedProcess([], 2, "", "close-tab: absent")
        with mock.patch.object(RECOVERY.subprocess, "run", return_value=failed):
            with self.assertRaisesRegex(ValueError, "absent"):
                RECOVERY.focus_session("codex", "exact_id")

    def test_reopen_main_requires_a_target(self):
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(1, RECOVERY.main(["reopen"]))
        self.assertIn("--target", err.getvalue())


if __name__ == "__main__":
    unittest.main()
