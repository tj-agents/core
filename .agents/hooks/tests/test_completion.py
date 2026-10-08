import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "workflows"))
from completion import CompletionError, completion_check, visible_tasks


HEAD = "a" * 40


def goal(acceptance=None, deliveries=None, open_tasks=None, extra=""):
    document = {
        "outcome": "The requested user-visible outcome is observed.",
        "acceptance": acceptance if acceptance is not None else [
            {"id": "verified", "criterion": "The runtime gate rejects unsupported completion.",
             "evidence": [{"source": "focused test", "result": "passed"}],
             "owner": "delivery owner", "next_action": "None."},
        ],
        "deliveries": deliveries if deliveries is not None else [
            {"repository": "example/test", "pr": 42, "head": HEAD},
        ],
        "open_tasks": open_tasks if open_tasks is not None else [],
    }
    return f"# Goal\n\n{extra}\n```completion\n{json.dumps(document)}\n```\n"


class CompletionTests(unittest.TestCase):
    def write_goal(self, content):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "GOAL.md"
        path.write_text(content, encoding="utf-8")
        return path

    def test_complete_requires_fresh_merged_bound_delivery(self):
        path = self.write_goal(goal())
        requested = []

        def forge(delivery, root):
            requested.append((delivery, root))
            return {"number": 42, "headRefOid": HEAD, "state": "MERGED", "body": "## What\nChange\n## Why\nReason"}

        result = completion_check(path, {"repository": "example/test", "pr": 42, "head": HEAD}, path.parent, forge)
        self.assertTrue(result["ready"])
        self.assertEqual([({"repository": "example/test", "pr": 42, "head": HEAD}, path.parent)], requested)

    def test_rejects_bound_delivery_omitted_from_goal(self):
        path = self.write_goal(goal(deliveries=[]))
        result = completion_check(path, {"repository": "example/test", "pr": 42, "head": HEAD}, path.parent, lambda *_: {})
        self.assertFalse(result["ready"])
        self.assertIn("bound delivery is absent from completion deliveries", result["blockers"])

    def test_checks_every_delivery_and_unchecked_remote_tasks(self):
        second = "b" * 40
        path = self.write_goal(goal(deliveries=[
            {"repository": "example/test", "pr": 42, "head": HEAD},
            {"repository": "example/test", "pr": 43, "head": second},
        ]))
        requested = []

        def forge(delivery, _):
            requested.append(delivery["pr"])
            return {"number": delivery["pr"], "headRefOid": delivery["head"], "state": "MERGED",
                    "body": "## What\nChange\n## Why\nReason\n- [ ] Acceptance still pending" if delivery["pr"] == 43 else ""}

        result = completion_check(path, None, path.parent, forge)
        self.assertEqual([42, 43], requested)
        self.assertIn("delivery PR #43 has unchecked task: Acceptance still pending", result["blockers"])
        self.assertIn("delivery PR #43 unchecked task lacks owner: Acceptance still pending", result["blockers"])
        self.assertEqual("Acceptance still pending", result["open_tasks"][-1]["text"])
        self.assertIsNone(result["open_tasks"][-1]["owner"])

    def test_open_task_requires_matching_owned_identity(self):
        open_tasks = [{"repository": "example/test", "pr": 42, "head": HEAD, "text": "Acceptance still pending",
                       "owner": "delivery owner", "next_action": "Finish acceptance."}]
        path = self.write_goal(goal(open_tasks=open_tasks))
        result = completion_check(
            path,
            None,
            path.parent,
            lambda *_: {"number": 42, "headRefOid": HEAD, "state": "MERGED",
                        "body": "- [ ] Acceptance still pending"},
        )
        self.assertFalse(result["ready"])
        self.assertNotIn("unchecked task lacks owner", "\n".join(result["blockers"]))
        self.assertEqual(open_tasks, result["open_tasks"])

    def test_unreadable_remote_body_blocks_completion(self):
        path = self.write_goal(goal())
        result = completion_check(
            path,
            None,
            path.parent,
            lambda *_: {"number": 42, "headRefOid": HEAD, "state": "MERGED", "body": None},
        )
        self.assertIn("delivery PR #42 body is unreadable", result["blockers"])

    def test_pending_acceptance_requires_owned_action(self):
        acceptance = [{"id": "verified", "criterion": "A result is observed.", "evidence": [],
                       "owner": "", "next_action": ""}]
        path = self.write_goal(goal(acceptance=acceptance))
        with self.assertRaisesRegex(CompletionError, "owner and next_action"):
            completion_check(path, None, path.parent, lambda *_: {})

    def test_visible_tasks_excludes_examples_and_quotes(self):
        content = "- [ ] live task\n> - [ ] quoted\n```md\n- [ ] fenced\n```\n<!-- - [ ] hidden -->\n    - [ ] indented"
        self.assertEqual(["live task"], visible_tasks(content))

    def test_visible_tasks_includes_nested_list_tasks(self):
        self.assertEqual(["nested task"], visible_tasks("- Acceptance\n\n    - [ ] nested task"))

    def test_ignores_completion_examples_inside_fences_and_comments(self):
        fake = "````markdown\n```completion\n{}\n```\n````\n<!-- ```completion\n{}\n``` -->\n".format("{}", "{}")
        path = self.write_goal(fake + goal())
        result = completion_check(
            path,
            None,
            path.parent,
            lambda *_: {"number": 42, "headRefOid": HEAD, "state": "MERGED", "body": ""},
        )
        self.assertTrue(result["ready"])

    def test_generated_package_reports_owned_missing_evidence(self):
        path = self.write_goal(goal(acceptance=[
            {"id": "verified", "criterion": "A result is observed.", "evidence": [],
             "owner": "fixture owner", "next_action": "Run the focused check."},
        ], deliveries=[]))
        package = Path(__file__).resolve().parents[3] / "plugins/engineering/workflows/completion.py"
        completed = subprocess.run(
            [sys.executable, "-B", str(package), "--goal", str(path), "--root", str(path.parent)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(1, completed.returncode)
        result = json.loads(completed.stdout)
        self.assertFalse(result["ready"])
        self.assertEqual("fixture owner", result["open_tasks"][0]["owner"])


if __name__ == "__main__":
    unittest.main()
