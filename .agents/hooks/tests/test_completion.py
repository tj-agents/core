import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "workflows"))
from completion import (CompletionError, bind_terminal_audit, completion_check, prepare_terminal_acceptance,
                        receipt_lock, record_terminal_audit, recheck_terminal_acceptance,
                        reserve_terminal_audit, retire_terminal_goal, visible_tasks)


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
    def setUp(self):
        state = tempfile.TemporaryDirectory()
        self.addCleanup(state.cleanup)
        environment = mock.patch.dict(os.environ, {'AGENT_STATE_DIRECTORY': state.name})
        environment.start()
        self.addCleanup(environment.stop)

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

    def terminal_files(self, aggregate=None):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        goal_path = root / "GOAL.md"
        goal_path.write_text(goal(deliveries=[]), encoding="utf-8")
        aggregate_path = root / "aggregate.json"
        aggregate_path.write_text(json.dumps(aggregate if aggregate is not None else {
            "known": True,
            "owned": [],
            "responsibilities": [],
            "children": [],
            "waits": [],
        }), encoding="utf-8")
        artifact = root / "evidence.txt"
        artifact.write_text("passed\n", encoding="utf-8")
        return root, goal_path, aggregate_path, artifact

    def test_terminal_acceptance_requires_a_bound_passing_audit_then_rechecks(self):
        root, goal_path, aggregate_path, artifact = self.terminal_files()
        with tempfile.TemporaryDirectory() as state, mock.patch.dict(os.environ, {"AGENT_STATE_DIRECTORY": state}):
            receipt_path, receipt = prepare_terminal_acceptance(
                goal_path, aggregate_path, {"host": "codex", "session_id": "s1"}, root, [artifact], None)
            self.assertEqual("candidate", receipt["state"])
            self.assertEqual("required", receipt["audit"]["state"])
            self.assertEqual(3, len(receipt["sources"]))
            reserved, _dispatch = reserve_terminal_audit(receipt_path)
            bound = bind_terminal_audit(receipt_path, reserved["audit"]["reservation_id"], "native-1")
            result = root / "audit.json"
            result.write_text(json.dumps({
                "candidate_id": bound["candidate_id"], "state": "passed", "findings": [],
                "reservation_id": bound["audit"]["reservation_id"],
                "native_child_id": bound["audit"]["native_child_id"],
                "sources_sha256": bound["audit"]["sources_sha256"],
            }), encoding="utf-8")
            recorded = record_terminal_audit(receipt_path, bound["audit"]["reservation_id"], result)
            self.assertEqual("passed", recorded["audit"]["state"])
            accepted = recheck_terminal_acceptance(receipt_path)
            accepted_again = recheck_terminal_acceptance(receipt_path)
            reused, dispatch = reserve_terminal_audit(receipt_path)
            self.assertEqual('accepted', accepted_again['state'])
            self.assertEqual(bound['audit']['reservation_id'], reused['audit']['reservation_id'])
            self.assertFalse(dispatch)
        self.assertEqual("accepted", accepted["state"])
        self.assertEqual("passed", accepted["audit"]["state"])

    def test_terminal_acceptance_rejects_changed_sources_after_audit(self):
        root, goal_path, aggregate_path, artifact = self.terminal_files()
        with tempfile.TemporaryDirectory() as state, mock.patch.dict(os.environ, {"AGENT_STATE_DIRECTORY": state}):
            receipt_path, _receipt = prepare_terminal_acceptance(
                goal_path, aggregate_path, {"host": "codex", "session_id": "s1"}, root, [artifact], None)
            reserved, _dispatch = reserve_terminal_audit(receipt_path)
            bound = bind_terminal_audit(receipt_path, reserved["audit"]["reservation_id"], "native-1")
            result = root / "audit.json"
            result.write_text(json.dumps({
                "candidate_id": bound["candidate_id"], "state": "passed", "findings": [],
                "reservation_id": bound["audit"]["reservation_id"],
                "native_child_id": bound["audit"]["native_child_id"],
                "sources_sha256": bound["audit"]["sources_sha256"],
            }), encoding="utf-8")
            record_terminal_audit(receipt_path, bound["audit"]["reservation_id"], result)
            artifact.write_text("changed\n", encoding="utf-8")
            rechecked = recheck_terminal_acceptance(receipt_path)
        self.assertEqual("candidate", rechecked["state"])
        self.assertEqual("failed", rechecked["audit"]["state"])
        self.assertIn("frozen terminal acceptance sources changed", rechecked["deterministic"]["blockers"])

    def test_terminal_acceptance_fails_closed_for_unknown_aggregate_or_unbound_reservation(self):
        root, goal_path, aggregate_path, artifact = self.terminal_files({
            "known": False,
            "owned": [],
            "responsibilities": [],
            "children": [],
            "waits": [],
        })
        with tempfile.TemporaryDirectory() as state, mock.patch.dict(os.environ, {"AGENT_STATE_DIRECTORY": state}):
            receipt_path, receipt = prepare_terminal_acceptance(
                goal_path, aggregate_path, {"host": "codex", "session_id": "s1"}, root, [artifact], None)
            self.assertIn("aggregate responsibility inventory is unknown", receipt["deterministic"]["blockers"])
            with self.assertRaisesRegex(CompletionError, "deterministic blockers"):
                reserve_terminal_audit(receipt_path)
        self.assertEqual("required", receipt["audit"]["state"])

    def test_terminal_acceptance_marks_an_unbound_audit_reservation_unknown(self):
        root, goal_path, aggregate_path, artifact = self.terminal_files()
        with tempfile.TemporaryDirectory() as state, mock.patch.dict(os.environ, {"AGENT_STATE_DIRECTORY": state}):
            receipt_path, _receipt = prepare_terminal_acceptance(
                goal_path, aggregate_path, {"host": "codex", "session_id": "s1"}, root, [artifact], None)
            reserved, _dispatch = reserve_terminal_audit(receipt_path)
            rechecked = recheck_terminal_acceptance(receipt_path)
            with self.assertRaises(CompletionError):
                bind_terminal_audit(receipt_path, reserved['audit']['reservation_id'], 'native-1')
            bound = bind_terminal_audit(receipt_path, reserved['audit']['reservation_id'],
                                        'native-1', reconciled=True)
            self.assertEqual('bound', bound['audit']['state'])
        self.assertEqual("reserved", reserved["audit"]["state"])
        self.assertEqual("unknown", rechecked["audit"]["state"])
        self.assertIn("native audit reservation has no bound child", rechecked["deterministic"]["blockers"])

    def test_only_the_first_reservation_can_dispatch_a_native_audit(self):
        root, goal_path, aggregate_path, artifact = self.terminal_files()
        with tempfile.TemporaryDirectory() as state, mock.patch.dict(os.environ, {'AGENT_STATE_DIRECTORY': state}):
            path, _ = prepare_terminal_acceptance(goal_path, aggregate_path,
                                                  {'host': 'codex', 'session_id': 's1'}, root, [artifact])
            first, dispatch_first = reserve_terminal_audit(path)
            repeated, dispatch_again = reserve_terminal_audit(path)
        self.assertTrue(dispatch_first)
        self.assertFalse(dispatch_again)
        self.assertEqual(first['audit']['reservation_id'], repeated['audit']['reservation_id'])

    def test_a_concurrent_receipt_writer_cannot_reserve_an_audit(self):
        root, goal_path, aggregate_path, artifact = self.terminal_files()
        with tempfile.TemporaryDirectory() as state, mock.patch.dict(os.environ, {'AGENT_STATE_DIRECTORY': state}):
            path, _ = prepare_terminal_acceptance(goal_path, aggregate_path,
                                                  {'host': 'codex', 'session_id': 's1'}, root, [artifact])
            with receipt_lock(path):
                with self.assertRaisesRegex(CompletionError, 'another terminal receipt operation'):
                    reserve_terminal_audit(path)
            _, dispatch = reserve_terminal_audit(path)
            self.assertTrue(dispatch)

    def test_retired_goal_reuses_the_accepted_audit_and_preserves_evidence(self):
        root, goal_path, aggregate_path, artifact = self.terminal_files()
        with tempfile.TemporaryDirectory() as state, mock.patch.dict(os.environ, {'AGENT_STATE_DIRECTORY': state}):
            path, _ = prepare_terminal_acceptance(goal_path, aggregate_path,
                                                  {'host': 'codex', 'session_id': 's1'}, root, [artifact])
            with self.assertRaisesRegex(CompletionError, 'only an accepted goal'):
                retire_terminal_goal(path)
            reserved, _ = reserve_terminal_audit(path)
            bound = bind_terminal_audit(path, reserved['audit']['reservation_id'], 'native-1')
            result = root / 'audit.json'
            result.write_text(json.dumps({
                'candidate_id': bound['candidate_id'], 'reservation_id': bound['audit']['reservation_id'],
                'native_child_id': 'native-1', 'sources_sha256': bound['audit']['sources_sha256'],
                'state': 'passed', 'findings': [],
            }), encoding='utf-8')
            record_terminal_audit(path, bound['audit']['reservation_id'], result)
            accepted = recheck_terminal_acceptance(path)
            retired = retire_terminal_goal(path)
            self.assertTrue(goal_path.exists())
            self.assertTrue(retired['checkpoint']['retired_goal'])
            for snapshot in retired['checkpoint']['sources']:
                self.assertFalse(Path(snapshot['path']).is_relative_to(root))
                self.assertTrue(Path(snapshot['path']).is_file())
            goal_path.unlink()
            result.unlink()
            rechecked = recheck_terminal_acceptance(path)
            self.assertEqual('accepted', rechecked['state'])
            self.assertEqual(accepted['audit'], rechecked['audit'])
            self.assertFalse(reserve_terminal_audit(path)[1])
            Path(retired['checkpoint']['sources'][0]['path']).write_text('changed', encoding='utf-8')
            self.assertEqual('candidate', recheck_terminal_acceptance(path)['state'])

    def test_audit_from_another_native_child_cannot_accept_the_candidate(self):
        root, goal_path, aggregate_path, artifact = self.terminal_files()
        with tempfile.TemporaryDirectory() as state, mock.patch.dict(os.environ, {'AGENT_STATE_DIRECTORY': state}):
            path, _ = prepare_terminal_acceptance(goal_path, aggregate_path,
                                                  {'host': 'codex', 'session_id': 's1'}, root, [artifact])
            reserved, _ = reserve_terminal_audit(path)
            bound = bind_terminal_audit(path, reserved['audit']['reservation_id'], 'native-1')
            result = root / 'audit.json'
            result.write_text(json.dumps({'candidate_id': bound['candidate_id'],
                                         'reservation_id': bound['audit']['reservation_id'],
                                         'native_child_id': 'other-native-child',
                                         'sources_sha256': bound['audit']['sources_sha256'],
                                         'state': 'passed', 'findings': []}), encoding='utf-8')
            with self.assertRaisesRegex(CompletionError, 'reserved child'):
                record_terminal_audit(path, bound['audit']['reservation_id'], result)
            self.assertEqual('candidate', recheck_terminal_acceptance(path)['state'])

    def test_terminal_acceptance_keeps_cleanup_separate_from_acceptance(self):
        root, goal_path, aggregate_path, artifact = self.terminal_files()
        with tempfile.TemporaryDirectory() as state, mock.patch.dict(os.environ, {"AGENT_STATE_DIRECTORY": state}):
            obligations = Path(state) / "merge-cleanup" / "targeted-obligations"
            obligations.mkdir(parents=True)
            obligations.joinpath("pending.json").write_text(json.dumps({
                "kind": "targeted-cleanup", "obligation_id": "cleanup-1", "state": "pending",
                "owner": {"host": "codex", "session_id": "s1"}, "worktree": str(root),
            }), encoding="utf-8")
            cleanup = obligations / "pending.json"
            receipt_path, _receipt = prepare_terminal_acceptance(
                goal_path, aggregate_path, {"host": "codex", "session_id": "s1"}, root, [artifact], None, cleanup)
            reserved, _dispatch = reserve_terminal_audit(receipt_path)
            bound = bind_terminal_audit(receipt_path, reserved["audit"]["reservation_id"], "native-1")
            result = root / "audit.json"
            result.write_text(json.dumps({
                "candidate_id": bound["candidate_id"], "state": "passed", "findings": [],
                "reservation_id": bound["audit"]["reservation_id"],
                "native_child_id": bound["audit"]["native_child_id"],
                "sources_sha256": bound["audit"]["sources_sha256"],
            }), encoding="utf-8")
            record_terminal_audit(receipt_path, bound["audit"]["reservation_id"], result)
            accepted = recheck_terminal_acceptance(receipt_path)
        self.assertEqual("accepted", accepted["state"])
        self.assertEqual("pending", accepted["cleanup"]["state"])


if __name__ == "__main__":
    unittest.main()
