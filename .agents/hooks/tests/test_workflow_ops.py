import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path
from types import SimpleNamespace


OPERATIONS = Path(__file__).resolve().parents[2] / "workflows" / "workflow_ops.py"
SCENARIOS = Path(__file__).resolve().parent / "fixtures" / "workflow_efficiency_scenarios.json"


def load_operations():
    spec = importlib.util.spec_from_file_location("workflow_ops", OPERATIONS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ops = load_operations()


class WindowsSharingRetryTests(unittest.TestCase):
    def test_persistent_windows_denial_still_fails_at_the_existing_deadline(self):
        denied = PermissionError(13, "access denied")
        action = mock.Mock(side_effect=denied)
        with mock.patch.object(ops, "os", SimpleNamespace(name="nt")), \
                mock.patch.object(ops.time, "monotonic", side_effect=[0, 1, 2]), \
                mock.patch.object(ops.time, "sleep"), self.assertRaises(PermissionError) as raised:
            ops.retry_windows_sharing_violation(action)
        self.assertIs(denied, raised.exception)
        self.assertEqual(2, action.call_count)

    def test_non_windows_denial_is_not_retried(self):
        action = mock.Mock(side_effect=PermissionError(13, "access denied"))
        with mock.patch.object(ops, "os", SimpleNamespace(name="posix")), \
                mock.patch.object(ops.time, "sleep") as sleep, self.assertRaises(PermissionError):
            ops.retry_windows_sharing_violation(action)
        self.assertEqual(1, action.call_count)
        sleep.assert_not_called()


class RepositoryFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._baseline_temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls._baseline_temp.cleanup)
        baseline = RepositoryFixture()
        baseline.root = Path(cls._baseline_temp.name) / "repo"
        baseline._initialize_repository()
        cls._baseline_root = baseline.root
        cls._baseline_head = baseline.base

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        shutil.copytree(self._baseline_root, self.root)
        self.base = self._baseline_head

    def _initialize_repository(self):
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.root)], check=True)
        self.git("config", "user.email", "workflow@example.test")
        self.git("config", "user.name", "Workflow Fixture")
        self.git("remote", "add", "origin", "https://github.com/example/workflow-fixture.git")
        (self.root / ".agents" / "skills" / "feature").mkdir(parents=True)
        (self.root / ".agents" / "skills" / "feature" / "SKILL.md").write_text(
            "---\nname: feature\n---\n\n# Feature\n",
            encoding="utf-8",
        )
        (self.root / "src").mkdir()
        (self.root / "src" / "mapping.txt").write_text("baseline\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "baseline")
        self.base = self.git("rev-parse", "HEAD")
        self.git("update-ref", "refs/remotes/origin/main", self.base)
        self.git("switch", "-q", "-c", "Feature/Workflow-ops")

    def git(self, *arguments):
        return subprocess.run(
            ["git", *arguments],
            cwd=str(self.root),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    def commit(self, path, text, message):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        self.git("add", str(path))
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")


class CompactRunTests(RepositoryFixture):
    def test_process_output_decodes_utf8_even_with_non_ascii_text(self):
        result = ops.run_process(
            [sys.executable, "-c", "import sys; sys.stdout.buffer.write('café'.encode('utf-8'))"],
            self.root,
        )
        self.assertEqual("café", result.stdout)

    def test_success_returns_no_log_content_and_keeps_the_artifact(self):
        result = ops.compact_run(
            self.root,
            "run-1",
            "successful validation",
            [sys.executable, "-c", "print('large successful failure-path test detail\\n' * 100)"],
            8,
            20,
            4096,
        )
        self.assertEqual("succeeded", result["exit_state"])
        self.assertEqual([], result["summary"])
        self.assertEqual([], result["failing_items"])
        self.assertGreater(result["captured_lines"], 90)
        self.assertIn("large successful failure-path test detail", Path(result["artifact"]).read_text(encoding="utf-8"))
        scenario = json.loads(SCENARIOS.read_text(encoding="utf-8"))["bounded_log_output"]
        self.assertEqual(scenario["success_summary_bytes"], len(json.dumps(result["summary"]).encode("utf-8")) - 2)

    def test_failure_items_and_summary_are_bounded(self):
        result = ops.compact_run(
            self.root,
            "run-1",
            "failed validation",
            [sys.executable, "-c", "import sys; print('ERROR item-' + 'x' * 5000); sys.exit(3)"],
            2,
            1,
            128,
        )
        self.assertEqual("failed", result["exit_state"])
        self.assertEqual(3, result["exit_code"])
        self.assertEqual(1, len(result["failing_items"]))
        self.assertLessEqual(len(result["failing_items"][0].encode("utf-8")), 128)
        self.assertLessEqual(sum(len(line.encode("utf-8")) for line in result["summary"]), 128)

    def test_caller_cannot_raise_the_repository_output_caps(self):
        result = ops.compact_run(
            self.root,
            "run-1",
            "failed validation",
            [sys.executable, "-c", "import sys; print(('ERROR item ' + 'x' * 500 + '\\n') * 100); sys.exit(1)"],
            1000,
            1000,
            1000000,
        )
        self.assertLessEqual(len(result["failing_items"]), 20)
        self.assertLessEqual(sum(len(line.encode("utf-8")) for line in result["summary"]), 4096)

    def test_failure_summary_redacts_credentials(self):
        result = ops.compact_run(
            self.root,
            "run-1",
            "failed secret validation",
            [sys.executable, "-c", "import sys; print('ERROR token=abc123 password:open'); print('ERROR Authorization: Bearer bearer-value'); print('ERROR Authorization=Basic basic-value'); sys.exit(1)"],
            2,
            2,
            256,
        )
        returned = json.dumps({"summary": result["summary"], "failing_items": result["failing_items"]})
        self.assertNotIn("abc123", returned)
        self.assertNotIn("password:open", returned)
        self.assertNotIn("bearer-value", returned)
        self.assertNotIn("basic-value", returned)
        self.assertIn("[REDACTED]", returned)
        artifact = Path(result["artifact"]).read_text(encoding="utf-8")
        self.assertNotIn("abc123", artifact)
        self.assertNotIn("password:open", artifact)
        self.assertNotIn("bearer-value", artifact)
        self.assertNotIn("basic-value", artifact)

    def test_nested_run_ids_are_contained_and_parent_traversal_is_rejected(self):
        nested = ops.run_root(self.root, "agent-workflows/runtime-001")
        runs = (ops.state_root(self.root) / "runs").resolve()
        self.assertEqual(runs / "agent-workflows" / "runtime-001", nested)
        with self.assertRaisesRegex(ops.WorkflowOperationError, "escapes"):
            ops.run_root(self.root, "../outside")

    def test_run_id_rejects_an_alias_to_another_run_inside_the_state_root(self):
        runs = ops.state_root(self.root) / "runs"
        target = runs / "target"
        target.mkdir(parents=True)
        alias = runs / "alias"
        if sys.platform == "win32":
            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(alias), str(target)],
                capture_output=True, check=True,
            )
            self.addCleanup(alias.rmdir)
        else:
            alias.symlink_to(target, target_is_directory=True)
            self.addCleanup(alias.unlink)

        with self.assertRaisesRegex(ops.WorkflowOperationError, "redirected"):
            ops.run_root(self.root, "alias/nested")

    def test_run_id_rejects_a_redirected_workflow_state_root(self):
        state = ops.state_root(self.root)
        original_redirect = ops.is_redirect
        with mock.patch.object(
            ops, "is_redirect",
            side_effect=lambda path: Path(path) == state or original_redirect(path),
        ):
            with self.assertRaisesRegex(ops.WorkflowOperationError, "redirected"):
                ops.run_root(self.root, "run-1")


class InspectionTests(RepositoryFixture):
    def test_inspection_consolidates_repository_identity(self):
        result = ops.inspect_repository(self.root)
        self.assertEqual("example/workflow-fixture", result["repository"])
        self.assertEqual("Feature/Workflow-ops", result["branch"])
        self.assertEqual(self.git("rev-parse", "HEAD"), result["head"])
        self.assertEqual([], result["dirty_paths"])

    def test_inspection_preserves_modified_and_renamed_paths_with_spaces(self):
        path = self.root / ".agents" / "skills" / "feature" / "SKILL.md"
        path.write_text("# Changed guidance\n", encoding="utf-8")
        self.git("mv", "src/mapping.txt", "src/renamed mapping.txt")
        result = ops.inspect_repository(self.root)
        self.assertCountEqual(
            [".agents/skills/feature/SKILL.md", "src/renamed mapping.txt", "src/mapping.txt"],
            result["dirty_paths"],
        )


class DeliveryPreflightTests(RepositoryFixture):
    def setUp(self):
        super().setUp()
        self.url = "https://github.com/example/workflow-fixture/pull/12"
        self.pr = {"number": 12, "url": self.url, "headRefName": "Feature/Workflow-ops",
                   "headRefOid": self.base, "baseRefName": "main", "state": "OPEN",
                   "isCrossRepository": False, "mergeStateStatus": "BLOCKED"}
        self.branch_prs = []
        self.forge_commands = []
        original = ops.run_process

        def run(arguments, root, **kwargs):
            if arguments[0] != "gh":
                return original(arguments, root, **kwargs)
            self.forge_commands.append(arguments)
            payload = self.pr if arguments[2] == "view" else self.branch_prs
            return subprocess.CompletedProcess(arguments, 0, json.dumps(payload), "")

        patcher = mock.patch.object(ops, "run_process", side_effect=run)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_branch_without_a_pull_request_is_ready_to_create_one(self):
        result = ops.delivery_preflight(self.root)
        self.assertEqual({"pr_url": None, "action": "create"}, result["ownership"])
        self.assertTrue(result["ready"])
        self.assertEqual([], result["warnings"])
        self.assertEqual("list", self.forge_commands[0][2])

    def test_branch_name_outside_the_convention_only_warns(self):
        self.git("switch", "-q", "-c", "unconventional-branch")
        result = ops.delivery_preflight(self.root)
        self.assertEqual(["branch-name"], result["warnings"])
        self.assertEqual([], result["blockers"])
        self.assertTrue(result["ready"])

    def test_default_branch_is_blocked_without_a_forge_lookup(self):
        self.git("switch", "-q", "main")
        result = ops.delivery_preflight(self.root)
        self.assertIn("default-branch", result["blockers"])
        self.assertFalse(result["ready"])
        self.assertEqual([], self.forge_commands)

    def test_open_pull_request_for_this_branch_is_updated(self):
        self.branch_prs = [self.pr]
        result = ops.delivery_preflight(self.root)
        self.assertEqual("update", result["ownership"]["action"])
        self.assertEqual(self.url, result["ownership"]["pr_url"])
        self.assertTrue(result["ready"])

    def test_base_currency_blocks_only_when_github_reports_behind(self):
        cases = (("BEHIND", ["base-update-required"]), ("BLOCKED", []), ("DIRTY", ["merge-conflict"]))
        for merge_state, blockers in cases:
            with self.subTest(merge_state=merge_state):
                self.pr["mergeStateStatus"] = merge_state
                self.branch_prs = [self.pr]
                self.assertEqual(blockers, ops.delivery_preflight(self.root)["blockers"])

    def test_pull_request_for_another_branch_must_be_integrated(self):
        self.pr["headRefName"] = "Feature/Delivery"
        result = ops.delivery_preflight(self.root, self.url)
        self.assertEqual("integrate", result["ownership"]["action"])
        self.assertEqual("Feature/Delivery", result["ownership"]["branch"])
        self.assertIn("delivery-integrate", result["blockers"])
        self.assertEqual("view", self.forge_commands[0][2])

    def test_closed_or_fork_pull_request_is_reconciled_instead_of_replaced(self):
        for changes in ({"state": "MERGED"}, {"isCrossRepository": True}):
            with self.subTest(changes=changes):
                self.pr.update(changes)
                result = ops.delivery_preflight(self.root, self.url)
                self.assertEqual("reconcile-review", result["ownership"]["action"])
                self.assertIn("delivery-reconcile-review", result["blockers"])

    def test_foreign_repository_pull_request_is_rejected_before_forge_access(self):
        with self.assertRaisesRegex(ops.WorkflowOperationError, "this repository"):
            ops.delivery_preflight(self.root, "https://github.com/another/repo/pull/12")
        self.assertEqual([], self.forge_commands)

    def test_forge_failure_is_not_an_empty_branch_lookup(self):
        original = ops.run_process

        def unavailable(arguments, root, **kwargs):
            if arguments[0] == "gh":
                raise ops.WorkflowOperationError("forge unavailable")
            return original(arguments, root, **kwargs)

        with mock.patch.object(ops, "run_process", side_effect=unavailable):
            with self.assertRaisesRegex(ops.WorkflowOperationError, "forge unavailable"):
                ops.delivery_preflight(self.root)

    def test_uncommitted_code_blocks_but_documentation_does_not(self):
        notes = self.root / "plans" / "notes"
        notes.mkdir(parents=True)
        (notes / "WORK PLAN.md").write_text("# Separate notes\n", encoding="utf-8")
        result = ops.delivery_preflight(self.root)
        self.assertTrue(result["ready"])
        self.assertEqual(["plans/notes/WORK PLAN.md"], result["documentation_dirty_paths"])
        (notes / "script.py").write_text("print('unfinished')\n", encoding="utf-8")
        result = ops.delivery_preflight(self.root)
        self.assertIn("uncommitted-code", result["blockers"])
        self.assertEqual(["plans/notes/script.py"], result["code_dirty_paths"])

    def test_cli_returns_a_blocked_exit(self):
        self.pr["headRefName"] = "Feature/Delivery"
        with mock.patch.object(ops, "emit") as emit:
            code = ops.main(["--root", str(self.root), "--workflow-run-id", "cli", "delivery-preflight",
                             "--pr-url", self.url])
        self.assertEqual(1, code)
        self.assertEqual("integrate", emit.call_args.args[0]["ownership"]["action"])


class MonitorTests(RepositoryFixture):
    def observer(self, values):
        remaining = iter(values)
        last = values[-1]

        def observe(_root, _identity):
            nonlocal last
            last = next(remaining, last)
            return last

        return observe

    def test_monitor_persists_exact_identity_and_emits_only_after_transition(self):
        observer = self.observer(
            [
                {"state": "in_progress", "conclusion": None},
                {"state": "in_progress", "conclusion": None},
                {"state": "completed", "conclusion": "success"},
            ]
        )
        result = ops.monitor_remote(
            self.root,
            "run-1",
            "run",
            "42",
            "HEAD",
            "ci",
            1,
            0.001,
            2,
            observer,
        )
        self.assertEqual("terminal", result["transition"])
        self.assertEqual(3, result["queries"])
        self.assertEqual(self.head_or_base(), result["identity"]["head"])
        state = json.loads(Path(result["state_artifact"]).read_text(encoding="utf-8"))
        self.assertEqual("example/workflow-fixture", state["identity"]["repository"])
        self.assertEqual("42", state["identity"]["target_id"])

    def test_monitor_reconnects_to_the_same_identity(self):
        observer = self.observer(
            [
                {"state": "in_progress", "conclusion": None},
                {"state": "queued", "conclusion": None},
            ]
        )
        first = ops.monitor_remote(self.root, "run-1", "run", "42", "HEAD", "ci", 1, 0.001, 2, observer)
        second = ops.monitor_remote(self.root, "run-1", "run", "42", "HEAD", "ci", 1, 0.001, 2, observer)
        self.assertFalse(first["reconnected"])
        self.assertTrue(second["reconnected"])
        self.assertEqual(first["monitor_id"], second["monitor_id"])

    def test_a_second_live_monitor_for_the_same_identity_is_refused(self):
        identity = ops.remote_identity(self.root, "run", "42", "HEAD", "ci", 1)
        monitor_id = ops.digest(identity)
        lock = ops.state_root(self.root) / "monitors" / f"{monitor_id}.lock"
        observer = self.observer([{"state": "completed", "conclusion": "success"}])
        with ops.MonitorLease(lock):
            with self.assertRaisesRegex(ops.WorkflowOperationError, "another process"):
                ops.monitor_remote(self.root, "run-1", "run", "42", "HEAD", "ci", 1, 0.001, 2, observer)

    def test_completed_run_is_observed_after_disconnect_and_suspension(self):
        scenario = json.loads(SCENARIOS.read_text(encoding="utf-8"))
        observations = scenario["completed_run_while_disconnected"]
        first_observer = self.observer(observations["before_disconnect"])
        first = ops.monitor_remote(self.root, "run-1", "run", "42", "HEAD", "ci", 1, 0.001, 2, first_observer)
        state_path = Path(first["state_artifact"])
        state = json.loads(state_path.read_text(encoding="utf-8"))
        suspension = scenario["machine_suspension"]
        state["last_observed_at"] -= suspension["elapsed_seconds"]
        ops.atomic_json(state_path, state)
        second_observer = self.observer(observations["after_reconnect"])
        second = ops.monitor_remote(
            self.root,
            "run-1",
            "run",
            "42",
            "HEAD",
            "ci",
            1,
            suspension["poll_seconds"],
            2,
            second_observer,
        )
        self.assertTrue(second["reconnected"])
        self.assertTrue(second["terminal"])
        self.assertEqual("success", second["observation"]["conclusion"])
        self.assertGreaterEqual(second["timing"]["suspended_offline_seconds"], suspension["minimum_offline_seconds"])

    def test_completed_run_emits_on_its_first_observation(self):
        result = ops.monitor_remote(
            self.root, "run-1", "run", "42", "HEAD", "ci", 1, 0.001, 2,
            self.observer([{"state": "completed", "conclusion": "success"}]),
        )
        self.assertTrue(result["terminal"])
        self.assertEqual(1, result["queries"])

    def ready_pr(self, **changes):
        value = {
            "state": "open", "merge_state": "blocked", "auto_merge": False,
            "review_decision": "review_required", "check_count": 2,
            "pending_items": [], "failing_items": [], "merge_group_failures": [],
        }
        value.update(changes)
        return value

    def test_initial_green_pr_emits_once_before_human_review(self):
        result = ops.monitor_remote(
            self.root, "run-1", "pr", "42", "HEAD", None, None, 0.001, 0.2,
            self.observer([self.ready_pr()]),
        )
        self.assertEqual("material-transition", result["transition"])
        self.assertFalse(result["terminal"])
        self.assertEqual(1, result["queries"])
        state = json.loads(Path(result["state_artifact"]).read_text(encoding="utf-8"))
        self.assertEqual(result["observation"], state["last_observation"])

    def test_reconnect_does_not_repeat_initial_green_pr_notification(self):
        ready = self.ready_pr()
        first = ops.monitor_remote(
            self.root, "run-1", "pr", "42", "HEAD", None, None, 0.001, 0.2,
            self.observer([ready]),
        )
        second = ops.monitor_remote(
            self.root, "run-1", "pr", "42", "HEAD", None, None, 0.001, 2,
            self.observer([ready, ready, self.ready_pr(state="merged")]),
        )
        self.assertEqual("material-transition", first["transition"])
        self.assertEqual(first["monitor_id"], second["monitor_id"])
        self.assertTrue(second["reconnected"])
        self.assertEqual("merged", second["observation"]["state"])
        self.assertEqual(4, second["queries"])

    def test_empty_or_pending_checks_do_not_emit_initial_readiness(self):
        for changes in ({"check_count": 0}, {"pending_items": ["windows"]}):
            with self.subTest(changes=changes):
                target = "43" if changes.get("check_count") == 0 else "44"
                result = ops.monitor_remote(
                    self.root, "run-1", "pr", target, "HEAD", None, None, 0.001, 2,
                    self.observer([self.ready_pr(**changes), self.ready_pr(state="merged")]),
                )
                self.assertEqual("merged", result["observation"]["state"])
                self.assertEqual(2, result["queries"])

    def test_pr_observer_retains_nonempty_check_evidence(self):
        identity = ops.remote_identity(self.root, "pr", "42", "HEAD", None, None)
        pr = {
            "headRefOid": identity["head"], "state": "OPEN", "mergeStateStatus": "BLOCKED",
            "reviewDecision": "REVIEW_REQUIRED", "autoMergeRequest": None,
            "statusCheckRollup": [{"name": "ci", "status": "COMPLETED", "conclusion": "SUCCESS"}],
        }
        queue = {"data": {"repository": {"pullRequest": {"mergeQueueEntry": None}}}}
        responses = [subprocess.CompletedProcess([], 0, json.dumps(value), "") for value in (pr, queue, [])]
        with mock.patch.object(ops, "run_process", side_effect=responses):
            observed = ops.forge_observation(self.root, identity)
        self.assertEqual(1, observed["check_count"])

    def head_or_base(self):
        return self.git("rev-parse", "HEAD")


if __name__ == "__main__":
    unittest.main()
