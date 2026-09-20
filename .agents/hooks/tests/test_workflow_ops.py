import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


OPERATIONS = Path(__file__).resolve().parents[2] / "workflows" / "workflow_ops.py"
SCENARIOS = Path(__file__).resolve().parent / "fixtures" / "workflow_efficiency_scenarios.json"


def load_operations():
    spec = importlib.util.spec_from_file_location("workflow_ops", OPERATIONS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ops = load_operations()


class RepositoryFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
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
        nested = ops.inspect_repository(self.root, "agent-workflows/runtime-001")
        self.assertEqual("inspect", nested["operation"])
        with self.assertRaisesRegex(ops.WorkflowOperationError, "escapes"):
            ops.inspect_repository(self.root, "../outside")


class InspectionAndSkillTests(RepositoryFixture):
    def test_inspection_consolidates_repository_identity(self):
        result = ops.inspect_repository(self.root, "run-1")
        self.assertEqual("example/workflow-fixture", result["repository"])
        self.assertEqual("Feature/Workflow-ops", result["branch"])
        self.assertEqual(self.git("rev-parse", "HEAD"), result["head"])
        self.assertEqual([], result["dirty_paths"])

    def test_skill_identity_loads_once_and_survives_context_recovery(self):
        lifecycle = "feature"
        first = ops.skill_identities(self.root, "run-1", lifecycle, [])
        second = ops.skill_identities(self.root, "run-1", lifecycle, [])
        self.assertEqual("load", first["skills"][0]["action"])
        self.assertEqual("cached", second["skills"][0]["action"])
        self.assertEqual(first["skills"][0]["sha256"], second["skills"][0]["sha256"])

    def test_changed_skill_identity_requires_a_new_load(self):
        lifecycle = "feature"
        ops.skill_identities(self.root, "run-1", lifecycle, [])
        path = self.root / ".agents" / "skills" / "feature" / "SKILL.md"
        path.write_text(path.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")
        changed = ops.skill_identities(self.root, "run-1", lifecycle, [])
        self.assertEqual("load", changed["skills"][0]["action"])


class ReviewTests(RepositoryFixture):
    def setUp(self):
        super().setUp()
        self.head = self.commit("src/mapping.txt", "candidate\n", "candidate")

    def test_small_candidate_gets_one_minimal_isolated_wave(self):
        result = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        self.assertEqual(1, result["waves"])
        self.assertEqual(["native-general"], result["lenses"])
        self.assertEqual(["src/mapping.txt"], result["paths"])
        self.assertNotIn("transcript", result["context"])
        self.assertLess(len(json.dumps(result["context"])), 4096)
        tree = Path(result["bundle"]["tree"])
        self.assertEqual("candidate\n", (tree / "src" / "mapping.txt").read_text(encoding="utf-8"))
        self.assertEqual(result["bundle"]["identity_sha256"], ops.sha256_file(Path(result["bundle"]["identity"])))

    def test_review_prepare_resolves_rules_with_the_packaged_router(self):
        route_table = self.root / ".agents" / "skill-routes.json"
        route_table.write_text(
            json.dumps({"routes": [{"path": "^src/", "skills": ["feature"]}]}),
            encoding="utf-8",
        )
        candidate_router = self.root / ".agents" / "hooks" / "skill_router.py"
        candidate_router.parent.mkdir(parents=True)
        candidate_router.write_text(
            'import json\nprint(json.dumps({"skills": {"shadowed": []}}))\n',
            encoding="utf-8",
        )
        self.git("add", ".agents/skill-routes.json", ".agents/hooks/skill_router.py")
        self.git("commit", "-q", "-m", "add routing")

        result = ops.review_prepare(self.root, "routed-review", "origin/main", "HEAD", False)

        self.assertEqual(["feature"], [rule["name"] for rule in result["rules"]])
        self.assertEqual(".agents/skills/feature/SKILL.md", result["rules"][0]["path"])

    def test_opted_in_review_fails_visibly_when_router_runtime_is_missing(self):
        (self.root / ".agents" / "skill-routes.json").write_text(
            json.dumps({"routes": [{"path": "^src/", "skills": ["feature"]}]}),
            encoding="utf-8",
        )
        original = ops.__file__
        ops.__file__ = str(self.root / "absent-package" / "workflows" / "workflow_ops.py")
        try:
            with self.assertRaisesRegex(ops.WorkflowOperationError, "has no skill_router.py"):
                ops.routed_skills(self.root, ["src/mapping.txt"])
        finally:
            ops.__file__ = original
    def test_tampered_review_artifact_is_rejected(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        Path(descriptor["bundle"]["patch"]).write_bytes(b"forged")
        with self.assertRaisesRegex(ops.WorkflowOperationError, "patch hash"):
            ops.review_reconcile(self.root, "run-1", descriptor["artifact"], "origin/main")

    def test_tampered_materialized_tree_is_rejected(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        tree_file = Path(descriptor["bundle"]["tree"]) / "src" / "mapping.txt"
        tree_file.write_text("forged\n", encoding="utf-8")
        with self.assertRaisesRegex(ops.WorkflowOperationError, "materialized review tree"):
            ops.review_reconcile(self.root, "run-1", descriptor["artifact"], "origin/main")

    def test_tampered_tree_archive_is_rejected(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        Path(descriptor["bundle"]["tree_archive"]).write_bytes(b"forged")
        with self.assertRaisesRegex(ops.WorkflowOperationError, "tree archive hash"):
            ops.review_reconcile(self.root, "run-1", descriptor["artifact"], "origin/main")

    def test_descriptor_outside_the_bound_run_is_rejected(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        copied = self.root / "descriptor.json"
        copied.write_text(Path(descriptor["artifact"]).read_text(encoding="utf-8"), encoding="utf-8")
        with self.assertRaisesRegex(ops.WorkflowOperationError, "outside"):
            ops.review_reconcile(self.root, "run-1", copied, "origin/main")

    def test_unrelated_base_movement_does_not_restart_source_review(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        descriptor_path = descriptor["artifact"]
        tree = self.git("rev-parse", f"{self.base}^{{tree}}")
        moved = self.git("commit-tree", tree, "-p", self.base, "-m", "unrelated empty base move")
        self.git("update-ref", "refs/remotes/origin/main", moved)
        result = ops.review_reconcile(self.root, "run-1", descriptor_path, "origin/main")
        self.assertTrue(result["base_moved"])
        self.assertTrue(result["exact_head"])
        self.assertFalse(result["review_required"])

    def test_head_movement_requires_incremental_review(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        self.commit("src/second.txt", "later\n", "later candidate")
        result = ops.review_reconcile(self.root, "run-1", descriptor["artifact"], "origin/main")
        self.assertTrue(result["review_required"])
        self.assertIn("candidate-head-changed", result["reasons"])

    def test_delivery_preflight_preserves_review_after_unrelated_base_movement(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        tree = self.git("rev-parse", f"{self.base}^{{tree}}")
        moved = self.git("commit-tree", tree, "-p", self.base, "-m", "unrelated empty base move")
        self.git("update-ref", "refs/remotes/origin/main", moved)
        result = ops.delivery_preflight(self.root, "run-1", descriptor["artifact"], "origin/main")
        self.assertTrue(result["ready"])
        self.assertEqual([], result["blockers"])

    def test_delivery_preflight_blocks_base_movement_before_review(self):
        tree = self.git("rev-parse", f"{self.base}^{{tree}}")
        moved = self.git("commit-tree", tree, "-p", self.base, "-m", "base move")
        self.git("update-ref", "refs/remotes/origin/main", moved)
        result = ops.delivery_preflight(self.root, "run-1", None, "origin/main")
        self.assertFalse(result["ready"])
        self.assertIn("base-ahead-before-final-review", result["blockers"])


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

    def head_or_base(self):
        return self.git("rev-parse", "HEAD")


class TelemetryTests(RepositoryFixture):
    def transcript(self):
        path = Path(self.temp.name) / "session.jsonl"
        records = [
            {
                "timestamp": "2026-09-09T10:00:00Z",
                "type": "token_usage_record",
                "payload": {
                    "turn_id": "turn-1",
                    "thread_token_usage": {
                        "input_tokens": 1000,
                        "cached_input_tokens": 800,
                        "output_tokens": 50,
                    },
                },
            },
            {
                "timestamp": "2026-09-09T10:00:01Z",
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "call_id": "call-1",
                    "name": "wait",
                    "arguments": "{}",
                },
            },
            {
                "timestamp": "2026-09-09T10:00:03Z",
                "type": "response_item",
                "payload": {
                    "type": "function_call_output",
                    "call_id": "call-1",
                },
            },
            {
                "timestamp": "2026-09-09T10:10:03Z",
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "call_id": "call-2",
                    "name": "exec",
                    "input": "Get-Content skill/SKILL.md",
                },
            },
            {
                "timestamp": "2026-09-09T10:10:04Z",
                "type": "token_usage_record",
                "payload": {
                    "turn_id": "turn-2",
                    "thread_token_usage": {
                        "input_tokens": 1500,
                        "cached_input_tokens": 1200,
                        "output_tokens": 75,
                    },
                },
            },
        ]
        path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")
        return path

    def test_transcript_metrics_separate_cached_usage_and_offline_time(self):
        metrics = ops.transcript_telemetry(self.transcript(), "codex", 300)
        self.assertEqual(2, metrics["model_turns"])
        self.assertEqual(2, metrics["tool_calls"])
        self.assertEqual(1, metrics["wait_poll_calls"])
        self.assertEqual(1, metrics["skill_load_calls"])
        self.assertEqual(300, metrics["uncached_input_tokens"])
        self.assertEqual(1200, metrics["cached_input_tokens"])
        self.assertEqual(75, metrics["output_tokens"])
        self.assertGreaterEqual(metrics["suspended_offline_seconds"], 600)

    def test_incident_scale_metrics_breach_soft_and_hard_budgets(self):
        metrics = {
            "model_turns": 468,
            "tool_calls": 439,
            "wait_poll_calls": 222,
            "uncached_input_tokens": 700000,
            "cached_input_tokens": 54300000,
            "output_tokens": 92000,
            "active_execution_seconds": 20000,
            "remote_waiting_seconds": 5269,
            "suspended_offline_seconds": 24720,
            "skill_load_calls": 28,
        }
        budget = json.loads((OPERATIONS.parent / "budgets.json").read_text(encoding="utf-8"))
        result = ops.budget_result(metrics, budget)
        self.assertFalse(result["allowed"])
        breached = {item["metric"] for item in result["breaches"]}
        self.assertIn("wait_poll_calls", breached)
        self.assertIn("cached_input_tokens", breached)
        self.assertIn("suspended_offline_seconds", breached)

    def test_codex_reasoning_items_and_nested_waits_are_counted(self):
        path = Path(self.temp.name) / "codex-session.jsonl"
        records = [
            {"type": "response_item", "payload": {"type": "reasoning"}},
            {"type": "response_item", "payload": {"type": "reasoning"}},
            {
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "call_id": "call-1",
                    "name": "exec",
                    "input": "await tools.write_stdin({session_id: 1});",
                },
            },
        ]
        path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")
        metrics = ops.transcript_telemetry(path, "codex", 300)
        self.assertEqual(2, metrics["model_turns"])
        self.assertEqual(1, metrics["wait_poll_calls"])


if __name__ == "__main__":
    unittest.main()
