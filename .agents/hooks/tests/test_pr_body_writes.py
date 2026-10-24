import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
HOOKS = ROOT / ".agents/hooks"
sys.path.insert(0, str(HOOKS))
SPEC = importlib.util.spec_from_file_location("pr_write_gate", HOOKS / "delivery_binding_gate.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)
BODY = "## Why\nFresh clones missed the selection.\n\n## What\nDeclare the selected plugin.\n"


class PrWriteTests(unittest.TestCase):
    def invoke(self, tool, arguments):
        payload = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": arguments}
        with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), \
                patch.object(sys, "argv", ["gate", "--validate-body", "--pr-writes-only"]), \
                patch.object(sys, "stderr", io.StringIO()), \
                patch.object(gate, "authoritative_body") as authoritative:
            try:
                code = gate.main()
            except SystemExit as error:
                code = error.code
            authoritative.assert_not_called()
            return code

    def test_direct_connector_create_and_body_edit_require_both_sections(self):
        for prefix in ("mcp__codex_apps__github_", "mcp__github__", "mcp__plugin_github_github__", "github_"):
            for operation in ("create", "update"):
                tool = prefix + operation + "_pull_request"
                for invalid in ("Change with a reason but no labels", "## Why\nReason", "## What\nChange\n## Why\n<!-- empty -->"):
                    with self.subTest(tool=tool, body=invalid):
                        self.assertEqual(2, self.invoke(tool, {"body": invalid}))
                self.assertEqual(0, self.invoke(tool, {"body": BODY}))

    def test_missing_create_body_is_rejected_but_metadata_edits_and_reads_are_unaffected(self):
        self.assertEqual(2, self.invoke("mcp__codex_apps__github_create_pull_request", {}))
        self.assertEqual(0, self.invoke("mcp__codex_apps__github_update_pull_request", {"title": "New title"}))
        self.assertEqual(0, self.invoke("mcp__github__update_pull_request", {"body": None, "state": "closed"}))
        self.assertEqual(0, self.invoke("mcp__codex_apps__github_get_pr_info", {}))
        self.assertEqual(0, self.invoke("mcp__gitlab__create_pull_request", {"description": "Different provider"}))

    def test_pr_write_mode_does_not_change_merge_authorization(self):
        self.assertEqual(0, self.invoke("exec_command", {"cmd": "gh pr merge 42 --merge"}))
        self.assertEqual(0, self.invoke("exec_command", {"cmd": "gh pr merge 'unterminated"}))
        self.assertEqual(0, self.invoke("mcp__codex_apps__github_merge_pull_request", {}))
        self.assertEqual(2, self.invoke("exec_command", {"cmd": "gh pr merge 42; gh pr create --body 'unlabelled'"}))

    def test_local_preflight_rejects_the_original_unlabelled_description(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "PR body ü.md"
            for body, expected in (("Select Template. Fresh clones need it.", 1), (BODY, 0)):
                path.write_text(body, encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, "-B", str(ROOT / ".agents/workflows/pr_body.py"), "--body-file", str(path)],
                    capture_output=True, text=True, encoding="utf-8", timeout=10,
                )
                self.assertEqual(expected, result.returncode, result.stderr)
                self.assertEqual(expected == 0, json.loads(result.stdout)["valid"])

    def test_both_packaged_host_registrations_reject_bad_cli_and_connector_writes(self):
        with tempfile.TemporaryDirectory(prefix="PR gate with spaces ü ") as directory:
            root = Path(directory)
            package = root / "engineering"
            shutil.copytree(ROOT / "plugins/engineering", package)
            caller = root / "unrelated caller"
            caller.mkdir()
            body_path = caller / "body.md"
            for host, tool, field in (("claude", "PowerShell", "command"), ("codex", "exec_command", "cmd")):
                manifest = json.loads((ROOT / f".agents/plugins/manifests/{host}/engineering-hooks.json").read_text(encoding="utf-8"))
                registration = next(group for group in manifest["hooks"]["PreToolUse"]
                                    if "delivery_binding_gate.py" in json.dumps(group))
                self.assertIsNone(re.fullmatch(registration["matcher"], "mcp__gitlab__create_pull_request"))
                hook = registration["hooks"][0]
                commands = [hook["args"]] if host == "claude" else [shlex.split(hook[key])[1:] for key in ("command", "commandWindows")]
                for arguments in commands:
                    arguments = [value.replace("${CLAUDE_PLUGIN_ROOT}", str(package)).replace("${PLUGIN_ROOT}", str(package)) for value in arguments]
                    for connector in (False, True):
                        selected_tool = "mcp__codex_apps__github_create_pull_request" if connector else tool
                        self.assertIsNotNone(re.fullmatch(registration["matcher"], selected_tool))
                        for body, denied in (("Unlabelled change and reason", True), (BODY, False)):
                            body_path.write_text(body, encoding="utf-8")
                            tool_input = {"body": body} if connector else {field: "gh pr create --body-file body.md"}
                            payload = {"hook_event_name": "PreToolUse", "tool_name": selected_tool,
                                       "tool_input": tool_input, "cwd": str(caller), "turn_id": "fixture"}
                            result = subprocess.run(
                                [sys.executable, *arguments], input=json.dumps(payload), cwd=caller,
                                env=dict(os.environ, PLUGIN_ROOT=str(package), CLAUDE_PLUGIN_ROOT=str(package)),
                                capture_output=True, text=True, encoding="utf-8", timeout=20,
                            )
                            if result.stdout.strip():
                                output = json.loads(result.stdout).get("hookSpecificOutput", {})
                                actual = output.get("permissionDecision") == "deny"
                            else:
                                actual = result.returncode == 2
                            self.assertEqual(denied, actual, (host, arguments, result.stdout, result.stderr))
                            if not denied:
                                self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
