import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "workflows"))
from completion import CompletionError, completion_check, visible_tasks


HEAD = "a" * 40


def goal(acceptance=None, deliveries=None, open_tasks=None, extra="", follow_up=None):
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
    if follow_up is not None:
        document["follow_up"] = follow_up
    return f"# Goal\n\n{extra}\n```completion\n{json.dumps(document)}\n```\n"


class CompletionTests(unittest.TestCase):
    def write_goal(self, content):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "GOAL.md"
        path.write_text(content, encoding="utf-8")
        return path

    def publisher_follow_up(self):
        return [
            {"repository": "example/agent", "pr": 20, "head": "b" * 40,
             "text": "Adopt publisher actions.", "owner": "publisher delivery owner",
             "next_action": "Finish the separately owned publisher review.",
             "scope_evidence": "User authorized this session to deliver refresh PRs 27 and 28; PR20 has an existing publisher owner."},
            {"repository": "example/actions", "pr": 34, "head": "c" * 40,
             "text": "Publish update hints.", "owner": "publisher delivery owner",
             "next_action": "Land shared publisher actions.",
             "scope_evidence": "Publisher owner's existing goal retains the independent PR34 delivery."},
        ]

    def test_completed_refresh_stack_keeps_publisher_follow_up_without_blocking_close(self):
        deliveries = [{"repository": "example/agent", "pr": number, "head": HEAD} for number in (27, 28)]
        follow_up = self.publisher_follow_up()
        path = self.write_goal(goal(deliveries=deliveries, follow_up=follow_up))
        requested = []

        def forge(delivery, _):
            requested.append(delivery)
            return {"number": delivery["pr"], "headRefOid": HEAD, "state": "MERGED", "body": ""}

        result = completion_check(path, deliveries[-1], path.parent, forge)
        self.assertTrue(result["report_ready"])
        self.assertTrue(result["ready"])
        self.assertEqual([], result["blockers"])
        self.assertEqual([], result["open_tasks"])
        self.assertEqual(follow_up, result["follow_up"])
        self.assertEqual(deliveries, requested)

    def test_external_owner_does_not_waive_required_acceptance(self):
        path = self.write_goal(goal(acceptance=[
            {"id": "live", "criterion": "Live notifications are observed.", "evidence": [],
             "owner": "publisher delivery owner", "next_action": "Verify live consumption."},
        ], deliveries=[], follow_up=self.publisher_follow_up()))
        result = completion_check(path, root=path.parent)
        self.assertFalse(result["report_ready"])
        self.assertFalse(result["ready"])
        self.assertIn("acceptance live lacks evidence", result["blockers"])

    def test_open_task_blocks_even_when_its_owner_is_external(self):
        task = {key: value for key, value in self.publisher_follow_up()[0].items() if key != "scope_evidence"}
        path = self.write_goal(goal(deliveries=[], open_tasks=[task]))
        result = completion_check(path, root=path.parent)
        self.assertFalse(result["ready"])
        self.assertEqual([task], result["open_tasks"])

    def test_follow_up_cannot_reclassify_an_owned_pr_even_at_another_head(self):
        task = self.publisher_follow_up()[0]
        owned = {"repository": task["repository"], "pr": task["pr"], "head": HEAD}
        for deliveries, open_tasks in (([owned], []), ([], [{**owned, "text": "Finish delivery.",
                                                             "owner": "this session", "next_action": "Finish."}])):
            with self.subTest(deliveries=deliveries):
                path = self.write_goal(goal(deliveries=deliveries, open_tasks=open_tasks, follow_up=[task]))
                with self.assertRaisesRegex(CompletionError, "cannot include an owned delivery or open task"):
                    completion_check(path, root=path.parent)

    def test_follow_up_requires_scope_and_owner_evidence(self):
        for field in ("scope_evidence", "owner", "next_action"):
            with self.subTest(field=field):
                task = {**self.publisher_follow_up()[0], field: " "}
                path = self.write_goal(goal(deliveries=[], follow_up=[task]))
                with self.assertRaisesRegex(CompletionError, "follow_up task requires"):
                    completion_check(path, root=path.parent)

    def test_repository_casing_cannot_disguise_follow_up_overlap(self):
        task = {**self.publisher_follow_up()[0], "repository": "EXAMPLE/AGENT"}
        owned = {"repository": "example/agent", "pr": task["pr"], "head": HEAD}
        for deliveries, open_tasks in (([owned], []), ([], [{**owned, "text": "Finish delivery.",
                                                             "owner": "this session", "next_action": "Finish."}])):
            with self.subTest(deliveries=deliveries):
                path = self.write_goal(goal(deliveries=deliveries, open_tasks=open_tasks, follow_up=[task]))
                with self.assertRaisesRegex(CompletionError, "cannot include an owned delivery or open task"):
                    completion_check(path, root=path.parent)

    def test_bound_repository_casing_matches_canonical_delivery_identity(self):
        path = self.write_goal(goal())
        result = completion_check(
            path, {"repository": "EXAMPLE/TEST", "pr": 42, "head": HEAD}, path.parent,
            lambda *_: {"number": 42, "headRefOid": HEAD, "state": "MERGED", "body": ""},
        )
        self.assertTrue(result["ready"])

    def test_generated_package_retains_follow_up_and_allows_completed_exit(self):
        follow_up = self.publisher_follow_up()
        path = self.write_goal(goal(deliveries=[], follow_up=follow_up))
        package = Path(__file__).resolve().parents[3] / "plugins/engineering/workflows/completion.py"
        completed = subprocess.run(
            [sys.executable, "-B", str(package), "--goal", str(path), "--root", str(path.parent)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        self.assertTrue(result["ready"])
        self.assertEqual(follow_up, result["follow_up"])

    def test_complete_requires_fresh_merged_bound_delivery(self):
        path = self.write_goal(goal())
        requested = []

        def forge(delivery, root):
            requested.append((delivery, root))
            return {"number": 42, "headRefOid": HEAD, "state": "MERGED", "body": "## What\nChange\n## Why\nReason"}

        result = completion_check(path, {"repository": "example/test", "pr": 42, "head": HEAD}, path.parent, forge)
        self.assertTrue(result["ready"])
        self.assertEqual([({"repository": "example/test", "pr": 42, "head": HEAD}, path.parent)], requested)
        self.assertEqual("unobserved", result["cleanup_status"])
        self.assertEqual([], result["pending_cleanup"])

    def test_pending_cleanup_preserves_report_readiness_and_blocks_cli_exit(self):
        path = self.write_goal(goal(deliveries=[]))
        state = tempfile.TemporaryDirectory()
        self.addCleanup(state.cleanup)
        obligations = Path(state.name) / "merge-cleanup" / "obligations"
        obligations.mkdir(parents=True)
        obligations.joinpath("own.json").write_text(json.dumps({
            "worktree": str(path.parent),
            "session_id": "s1",
            "session_exit_required": True,
            "checkout_retained": True,
            "disposition": {"status": "pending", "reason": "keep-open"},
        }), encoding="utf-8")
        obligations.joinpath("other.json").write_text(json.dumps({
            "worktree": str(Path(state.name) / "other-worktree"),
            "session_id": "s2",
            "session_exit_required": True,
        }), encoding="utf-8")
        with mock.patch.dict(os.environ, {"AGENT_STATE_DIRECTORY": state.name}):
            result = completion_check(path, None, path.parent, lambda *_: {
                "number": 42, "headRefOid": HEAD, "state": "MERGED", "body": "",
            })
            completed = subprocess.run(
                [sys.executable, "-B", str(Path(__file__).resolve().parents[2] / "workflows/completion.py"),
                 "--goal", str(path), "--root", str(path.parent)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertTrue(result["report_ready"])
        self.assertFalse(result["ready"])
        self.assertIn("cleanup remains pending", result["blockers"])
        self.assertEqual("pending", result["cleanup_status"])
        self.assertEqual([{
            "worktree": str(path.parent.resolve()),
            "session_id": "s1",
            "kind": "keep-open",
            "reason": "keep-open",
        }], result["pending_cleanup"])
        self.assertEqual(1, completed.returncode)
        self.assertTrue(json.loads(completed.stdout)["report_ready"])
        self.assertFalse(json.loads(completed.stdout)["ready"])

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

    def test_acceptance_failure_sets_both_readiness_values_false(self):
        path = self.write_goal(goal(acceptance=[
            {"id": "verified", "criterion": "A result is observed.", "evidence": [],
             "owner": "fixture owner", "next_action": "Run the focused check."},
        ], deliveries=[]))
        result = completion_check(path, None, path.parent, lambda *_: {})
        self.assertFalse(result["report_ready"])
        self.assertFalse(result["ready"])

    def test_malformed_goal_reports_both_readiness_values_false(self):
        path = self.write_goal("# Goal\n")
        completed = subprocess.run(
            [sys.executable, "-B", str(Path(__file__).resolve().parents[2] / "workflows/completion.py"),
             "--goal", str(path), "--root", str(path.parent)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(2, completed.returncode)
        result = json.loads(completed.stdout)
        self.assertFalse(result["report_ready"])
        self.assertFalse(result["ready"])

    def test_visible_tasks_excludes_examples_and_quotes(self):
        content = "- [ ] live task\n> - [ ] quoted\n```md\n- [ ] fenced\n```\n<!-- - [ ] hidden -->\n    - [ ] indented"
        self.assertEqual(["live task"], visible_tasks(content))

    def test_unchecked_marker_whitespace_blocks_completion(self):
        path = self.write_goal(goal())
        for body in ("- [ ]\tVerify deployment", "- [ ]"):
            with self.subTest(body=body):
                result = completion_check(path, None, path.parent, lambda *_: {
                    "number": 42, "headRefOid": HEAD, "state": "MERGED", "body": body,
                })
                self.assertFalse(result["ready"])
                self.assertEqual(1, len(result["open_tasks"]))

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
