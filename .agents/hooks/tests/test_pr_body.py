import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "workflows"))
import workflow_ops as ops
from pr_body import unchecked_tasks, validate_pr_body


BODY = "## What\nChange.\n## Why\nReason.\n"


class BodyTests(unittest.TestCase):
    def test_unchecked_tasks_ignores_hidden_examples(self):
        body = "- [ ] live\n> - [ ] quote\n```md\n- [ ] fenced\n```\n<!-- - [ ] hidden -->\n    - [ ] indented"
        self.assertEqual(["live"], unchecked_tasks(body))

    def test_unchecked_tasks_includes_nested_list_tasks(self):
        body = "- Acceptance\n\n    - [ ] nested task\nParagraph.\n    - [ ] standalone code"
        self.assertEqual(["nested task"], unchecked_tasks(body))

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
    def test_packaged_workflow_ops_exposes_pr_body_check(self):
        root = Path(__file__).resolve().parents[3]
        package = root / "plugins/engineering"
        completed = subprocess.run(
            [sys.executable, "-B", str(package / "workflows/workflow_ops.py"), "--help"],
            capture_output=True, text=True, check=True)
        self.assertIn("pr-body-check", completed.stdout)


if __name__ == "__main__":
    unittest.main()
