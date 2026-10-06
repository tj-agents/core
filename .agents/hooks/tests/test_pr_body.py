import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "workflows"))
import delivery_binding_gate as gate
import workflow_ops as ops
from pr_body import validate_pr_body


BODY = "## What\nChange.\n## Why\nReason.\n"


class BodyTests(unittest.TestCase):
    def test_supported_formats_and_order(self):
        for body in (BODY, "\ufeff" + BODY, "## WHY\nReason\n# wHaT\nChange",
                     "**What:** Change.\n\n**Why:** Reason.",
                     "**Why:**\nReason\n\n**What:**\nChange\n\nGenerated with Codex"):
            with self.subTest(body=body):
                self.assertTrue(validate_pr_body(body)["valid"])

    def test_hidden_and_empty_content_never_fills_sections(self):
        for content in ("", "<!-- prose -->", "```\nprose\n```", "    prose", " \tprose",
                        "> prose", "---\n- [ ]\n***", "1.\n2. [ ]", "Generated with Codex",
                        "Co-authored-by: Codex <codex@example.com>"):
            with self.subTest(content=content):
                self.assertEqual(["Empty What section"],
                                 validate_pr_body(f"## What\n{content}\n## Why\nReason")["errors"])
        for body in ("<!-- ## What\nChange -->\n## Why\nReason",
                     "```md\n## What\nChange\n```\n## Why\nReason",
                     "```md\n```text\n## What\nChange\n```\n## Why\nReason",
                     "> ## What\n> Change\n## Why\nReason"):
            self.assertEqual(["Missing What section"], validate_pr_body(body)["errors"])

    def test_next_section_ends_content(self):
        self.assertTrue(validate_pr_body("## What\n**Replace cache keys**\n## Why\nReason")["valid"])
        self.assertEqual(["Empty What section"],
                         validate_pr_body("## What\n## Notes\nChange\n## Why\nReason")["errors"])
        self.assertEqual(["Empty Why section"],
                         validate_pr_body("**Why:**\n**What:** Change")["errors"])
        self.assertFalse(validate_pr_body(None)["valid"])


class HookTests(unittest.TestCase):
    def run_gate(self, command, *, codex=False, pre=True, cwd=None, workdir=None):
        payload = {"tool_name": "exec_command" if codex else "PowerShell",
                   "tool_input": {"cmd" if codex else "command": command},
                   "cwd": cwd or ".", "tool_response": "https://github.com/example/test/pull/42"}
        if codex:
            payload["turn_id"] = "fixture"
        if workdir is not None:
            payload["tool_input"]["workdir"] = workdir
        with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), \
             patch.object(sys, "argv", ["gate", "--validate-body"] if pre else ["gate"]), \
             patch.object(sys, "stderr", io.StringIO()):
            try:
                return gate.main()
            except SystemExit as error:
                return error.code

    def test_create_edit_and_literal_body_for_both_hosts(self):
        for codex in (False, True):
            for operation in ("create", "new", "edit 42"):
                with self.subTest(codex=codex, operation=operation):
                    self.assertEqual(2, self.run_gate(f"gh pr {operation} --body 'empty'", codex=codex))
                    self.assertEqual(0, self.run_gate(f"gh pr {operation} -b '{BODY}'", codex=codex))
            self.assertEqual(2, self.run_gate("gh pr create --fill", codex=codex))
            self.assertEqual(2, self.run_gate('gh pr create --body "$body"', codex=codex))
            self.assertEqual(2, self.run_gate("gh pr create -F -", codex=codex))
            self.assertEqual(2, self.run_gate("gh pr create -F missing-file", codex=codex))
            self.assertEqual(2, self.run_gate("echo before && gh pr create -F body.md", codex=codex))
            for command in ("gh pr create --body '--help'", "gh pr edit 42 --editor",
                            "echo done; gh pr create --body 'empty'",
                            "cd x; gh pr create --body 'empty'",
                            "echo done\ngh pr create --body 'empty'",
                            "gh pr create --body 'unterminated"):
                self.assertEqual(2, self.run_gate(command, codex=codex))
            self.assertEqual(0, self.run_gate(f"gh pr create --body='{BODY}'", codex=codex))

    def test_body_file_and_unaffected_operations(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "body.md").write_text(BODY, encoding="utf-8")
            self.assertEqual(0, self.run_gate("gh pr create --body-file body.md", cwd=directory))
        for command in ("gh pr view 42", "gh pr create --help", "gh pr edit 42 --title 'Title'",
                        "echo 'gh pr create --body missing'", "gh pr edit 42 --add-label ready",
                        "gh pr merge 42 --disable-auto"):
            self.assertEqual(0, self.run_gate(command))

    def test_merge_always_checks_current_remote_body(self):
        with tempfile.TemporaryDirectory() as directory:
            command = f'pushd "{directory}" && gh pr merge 42 --squash --auto'
            with patch.object(gate, "authoritative_body") as check:
                self.assertEqual(0, self.run_gate(command, codex=True))
                check.assert_called_once_with(Path(directory).resolve(), "42", None)
                check.side_effect = ValueError("Empty Why section")
                self.assertEqual(2, self.run_gate(command, codex=True))
        with patch.object(gate, "authoritative_body") as check:
            self.assertEqual(0, self.run_gate("gh pr merge 42 --repo other/repo --squash"))
            self.assertEqual("other/repo", check.call_args.args[2])
            self.assertEqual(0, self.run_gate("gh pr merge --match-head-commit abc123 42 --squash"))
            self.assertEqual("42", check.call_args.args[1])
        self.assertEqual(2, self.run_gate("gh pr merge 42 --squash", codex=True))

    def test_body_edit_keeps_binding_and_fetches_even_same_head(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".agents/persistent-workflow-binding.json"
            path.parent.mkdir()
            path.write_text('{"pr":42,"head":"same"}')
            original = path.read_bytes()
            with patch.object(gate, "authoritative_body") as check, patch.object(gate, "bind") as bind:
                self.assertEqual(0, self.run_gate(f"gh pr edit 42 -b '{BODY}'", pre=False, cwd=directory))
                check.assert_called_once()
                bind.assert_not_called()
                check.side_effect = ValueError("Empty Why section")
                self.assertEqual(2, self.run_gate(f"gh pr edit 42 -b '{BODY}'", pre=False, cwd=directory))
            self.assertEqual(original, path.read_bytes())

    def test_create_fetches_returned_url_without_binding_opt_in(self):
        with patch.object(gate, "authoritative_body") as check, patch.object(gate, "find_config", return_value=None):
            self.assertEqual(0, self.run_gate(f"gh pr create -b '{BODY}'", pre=False))
            self.assertEqual("https://github.com/example/test/pull/42", check.call_args.args[1])
            check.side_effect = ValueError("Missing Why section")
            self.assertEqual(2, self.run_gate(f"gh pr create -b '{BODY}'", pre=False))

    def test_attached_short_body_flags_are_checked_before_and_after_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "valid.md").write_text(BODY, encoding="utf-8")
            (root / "invalid.md").write_text("empty", encoding="utf-8")
            for codex in (False, True):
                for flag in ("-bempty", "-Finvalid.md"):
                    for operation in ("create", "edit 42"):
                        self.assertEqual(2, self.run_gate(f"gh pr {operation} {flag}",
                                                        cwd=directory, codex=codex))
                    with patch.object(gate, "authoritative_body", side_effect=ValueError("Missing Why section")) as check:
                        self.assertEqual(2, self.run_gate(f"gh pr edit 42 {flag}",
                                                        cwd=directory, codex=codex, pre=False))
                        check.assert_called_once_with(root.resolve(), "42", None)
                for flag in (f"-b'{BODY}'", "-Fvalid.md"):
                    self.assertEqual(0, self.run_gate(f"gh pr edit 42 {flag}", cwd=directory, codex=codex))

    def test_merge_flags_use_merge_option_semantics(self):
        for flags in ("-m", "-r", "-s", "-a", "-m -a", "-r -d", "-t 'subject' -b 'commit body'",
                      "-A author@example.com --match-head-commit abc123"):
            with self.subTest(flags=flags), patch.object(gate, "authoritative_body") as check:
                self.assertEqual(0, self.run_gate(f"gh pr merge {flags} 42"))
                self.assertEqual("42", check.call_args.args[1])
                check.side_effect = ValueError("Missing Why section")
                self.assertEqual(2, self.run_gate(f"gh pr merge 42 {flags}"))
        with tempfile.TemporaryDirectory() as directory:
            for flags in ("-m", "-r", "-s -d"):
                with patch.object(gate, "authoritative_body") as check:
                    command = f'pushd "{directory}" && gh pr merge 42 {flags}'
                    self.assertEqual(0, self.run_gate(command, codex=True))
                    check.assert_called_once_with(Path(directory).resolve(), "42", None)

    def test_windows_executable_spellings_are_gated(self):
        for executable in ("gh.exe", "GH", "GH.EXE", "Gh.Exe"):
            for codex in (False, True):
                for operation in ("create", "edit 42"):
                    self.assertEqual(2, self.run_gate(f"{executable} pr {operation} -bempty", codex=codex))
                self.assertEqual(2, self.run_gate(f"{executable} pr create --body 'unterminated", codex=codex))
                self.assertEqual(0, self.run_gate(f"echo '{executable} pr create -bempty'", codex=codex))
                self.assertEqual(0, self.run_gate(f"{executable} pr create --help", codex=codex))
            with patch.object(gate, "authoritative_body") as check:
                self.assertEqual(0, self.run_gate(f"{executable} pr merge 42 -m"))
                check.assert_called_once()
                check.reset_mock()
                self.assertEqual(2, self.run_gate(f"{executable} pr merge 42 -m", codex=True))
                check.assert_not_called()
            with tempfile.TemporaryDirectory() as directory, patch.object(gate, "authoritative_body") as check:
                checkout = Path(directory) / "GH.EXE pr merge -m folder"
                checkout.mkdir()
                command = f'pushd "{checkout}" && {executable} pr merge 42 --squash --auto'
                self.assertEqual(0, self.run_gate(command, codex=True))
                check.assert_called_once_with(checkout.resolve(), "42", None)
                self.assertEqual(2, self.run_gate(command + " && echo done", codex=True))
            with patch.object(gate, "authoritative_body", side_effect=ValueError("Empty Why section")) as check:
                self.assertEqual(2, self.run_gate(f"{executable} pr edit 42 -bempty", pre=False))
                check.assert_called_once()

    def test_body_files_use_invocation_workdir_before_session_cwd(self):
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory) / "session"
            invocation = Path(directory) / "invocation"
            session.mkdir()
            invocation.mkdir()
            for codex in (False, True):
                for session_body, invocation_body, expected in ((BODY, "empty", 2), ("empty", BODY, 0)):
                    (session / "body.md").write_text(session_body, encoding="utf-8")
                    (invocation / "body.md").write_text(invocation_body, encoding="utf-8")
                    for operation in ("create", "edit 42"):
                        self.assertEqual(expected, self.run_gate(f"gh pr {operation} -Fbody.md", codex=codex,
                                                                cwd=str(session), workdir=str(invocation)))
                with patch.object(gate, "authoritative_body") as check:
                    self.assertEqual(0, self.run_gate("gh pr edit 42 -Fbody.md", pre=False,
                                                    cwd=str(session), workdir=str(invocation), codex=codex))
                    check.assert_called_once_with(invocation.resolve(), "42", None)


class OperationTests(unittest.TestCase):
    def test_read_only_command_does_not_create_runtime_artifacts(self):
        result = {"validation": {"valid": True}, "exit_state": "passed"}
        with patch.object(ops, "repository_root", return_value=Path(".")), \
             patch.object(ops, "run_root") as runtime, \
             patch.object(ops, "pr_body_check", return_value=result) as check, \
             patch.object(ops, "emit"):
            self.assertEqual(0, ops.main(["--workflow-run-id", "fixture", "pr-body-check",
                                          "--pr", "42", "--repo", "other/repo"]))
            runtime.assert_not_called()
            check.assert_called_once_with(Path("."), "42", "other/repo")

    def test_authoritative_request_includes_body_and_correct_target(self):
        value = {"number": 42, "url": "https://github.com/other/repo/pull/42",
                 "headRefOid": "a" * 40, "body": BODY}
        with patch.object(ops, "run_process") as process:
            process.return_value.stdout = json.dumps(value)
            result = ops.pr_body_check(Path("."), value["url"], "other/repo")
            args = process.call_args.args[0]
            self.assertIn("body", args[args.index("--json") + 1].split(","))
            self.assertIn(value["url"], args)
            self.assertEqual(["--repo", "other/repo"], args[-2:])
            self.assertTrue(result["validation"]["valid"])
            value["body"] = "## What\nChange"
            process.return_value.stdout = json.dumps(value)
            self.assertEqual("failed", ops.pr_body_check(Path("."), "42")["exit_state"])

    def test_invalid_remote_body_does_not_mutate_existing_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ops.delivery_runtime.BINDING_FILE
            path.parent.mkdir()
            path.write_text('{"pr":42,"head":"same"}')
            original = path.read_bytes()
            for value in ({"body": "## What\nChange"}, {"body": None}, {}):
                with patch.object(ops, "pull_request_state", return_value=value):
                    with self.assertRaises(ops.WorkflowOperationError):
                        ops.delivery_bind(Path(directory), "fixture", 42, "merged", None)
                self.assertEqual(original, path.read_bytes())


class PackageTests(unittest.TestCase):
    def test_generated_hook_import_and_windows_argument_forwarding(self):
        root = Path(__file__).resolve().parents[3]
        package = root / "plugins/engineering"
        payload = {"tool_name": "exec_command", "turn_id": "fixture",
                   "tool_input": {"cmd": "gh pr create --body 'empty'"}}
        completed = subprocess.run(
            [sys.executable, "-B", str(package / "hooks/pre_tool_use_adapter.py"),
             str(package / "hooks/delivery_binding_gate.py"), "--validate-body"],
            input=json.dumps(payload), capture_output=True, text=True, check=True)
        result = json.loads(completed.stdout)
        self.assertEqual("deny", result["hookSpecificOutput"]["permissionDecision"])
        self.assertIn("Missing What section", result["hookSpecificOutput"]["permissionDecisionReason"])
        completed = subprocess.run(
            [sys.executable, "-B", str(package / "workflows/workflow_ops.py"), "--help"],
            capture_output=True, text=True, check=True)
        self.assertIn("pr-body-check", completed.stdout)


if __name__ == "__main__":
    unittest.main()
