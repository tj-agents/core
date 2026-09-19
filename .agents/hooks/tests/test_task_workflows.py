import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS = ROOT / ".agents" / "workflows"
FIXTURE = Path(__file__).parent / "fixtures" / "task_workflow_scenarios.json"
sys.path.insert(0, str(WORKFLOWS))

from host_runtime import HostAdapterRegistry, WriterLeaseRegistry
from workflow_runtime import (
    ContractViolation,
    WorkflowContract,
    select_state_provider,
)
from fixtures.lane_expectations import authored_skill, packaged_adapter
from fixtures.task_workflow_harness import TaskWorkflowHarness


class TaskWorkflowAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.contract = WorkflowContract(WORKFLOWS, repository_root=ROOT)
        cls.capabilities = cls.contract.capabilities["delegable_capabilities"]

    def scenarios(self):
        return {scenario["id"]: scenario for scenario in self.fixture["scenarios"]}

    def harness(self, host, deck="bare-cli"):
        return TaskWorkflowHarness(
            ROOT,
            WORKFLOWS,
            host,
            HostAdapterRegistry,
            WriterLeaseRegistry,
            ContractViolation,
            select_state_provider,
            deck,
        )

    def test_acceptance_matrix_covers_phase_three_paths_and_terminals(self):
        scenarios = self.scenarios()
        self.assertEqual(
            {
                "feature-short-path",
                "small-obvious-bug",
                "complex-bug",
                "failure-recovery",
                "writer-serialization",
                "feature-durable-promotion",
                "human-gate",
            },
            set(scenarios),
        )
        self.assertEqual(["codex", "claude"], self.fixture["hosts"])
        self.assertEqual("feature", scenarios["feature-short-path"]["expected_workflow"])
        self.assertEqual("bugfix", scenarios["small-obvious-bug"]["expected_workflow"])
        self.assertEqual([], scenarios["feature-short-path"]["dispatches"])
        self.assertEqual([], scenarios["small-obvious-bug"]["dispatches"])
        self.assertEqual([], scenarios["feature-short-path"]["durable_artifacts"])
        self.assertEqual([], scenarios["small-obvious-bug"]["durable_artifacts"])
        self.assertEqual("coordinated", scenarios["writer-serialization"]["path"])
        self.assertNotEqual([], scenarios["feature-durable-promotion"]["durable_artifacts"])
        self.assertNotIn("complete", scenarios["human-gate"]["events"])

    def test_selection_matrix_covers_positive_paraphrases_and_neighboring_owners(self):
        cases = {case["id"]: case for case in self.fixture["selection_cases"]}
        self.assertEqual(
            {
                "feature-primary",
                "feature-paraphrase",
                "bug-primary",
                "bug-paraphrase",
                "planning-only",
                "active-plan",
                "review-only",
                "named-e2e",
                "red-test",
            },
            set(cases),
        )
        self.assertEqual(
            ["feature", "feature"],
            [cases[name]["expected_skill"] for name in ("feature-primary", "feature-paraphrase")],
        )
        self.assertEqual(
            ["bugfix", "bugfix"],
            [cases[name]["expected_skill"] for name in ("bug-primary", "bug-paraphrase")],
        )
        self.assertEqual(
            {"plan-authoring", "plan-execution", "review", "e2e-ui-debug", "failing-tests"},
            {
                cases[name]["expected_skill"]
                for name in ("planning-only", "active-plan", "review-only", "named-e2e", "red-test")
            },
        )
        self.assertEqual(len(cases), len({case["request"] for case in cases.values()}))

    def test_task_skills_keep_one_canonical_body_and_thin_host_entries(self):
        for skill in ("feature", "bugfix"):
            canonical = authored_skill(skill)
            plugin_canonical = ROOT / "plugins" / "engineering" / canonical.relative_to(ROOT)
            self.assertEqual(
                canonical.read_text(encoding="utf-8"),
                plugin_canonical.read_text(encoding="utf-8"),
            )
            for host, tree in (("claude", "skills"), ("codex", "codex-skills")):
                with self.subTest(skill=skill, host=host):
                    packaged = (
                        ROOT / "plugins" / "engineering" / tree / skill / "SKILL.md"
                    ).read_text(encoding="utf-8")
                    self.assertEqual(packaged_adapter(ROOT, skill, host), packaged)

    def test_scripted_lifecycles_execute_to_typed_terminals_on_both_hosts(self):
        for scenario in self.fixture["scenarios"]:
            for host in self.fixture["hosts"]:
                with self.subTest(scenario=scenario["id"], host=host):
                    outcome = self.harness(host).run(scenario)
                    self.assertEqual(scenario["expected_workflow"], outcome["workflow"])
                    self.assertEqual(
                        scenario["events"],
                        [entry["event"] for entry in outcome["events"]],
                    )
                    if scenario["terminal"]["kind"] == "human-gate":
                        self.assertEqual("human", outcome["terminal"]["gate_kind"])
                        self.assertEqual("open", outcome["terminal"]["status"])
                    else:
                        self.assertEqual("complete", outcome["terminal"]["transition"])

    def test_lifecycle_sequences_preserve_parent_decisions_and_candidate_review_order(self):
        scenarios = self.scenarios()
        required = {
            "feature-short-path": [
                "discover",
                "parent-architecture",
                "implement",
                "focused-validate",
                "commit-candidate",
                "review",
                "validate",
                "complete",
            ],
            "small-obvious-bug": [
                "reproduce",
                "classify-quick",
                "parent-diagnosis",
                "implement",
                "regression",
                "focused-validate",
                "commit-candidate",
                "review",
                "validate",
                "complete",
            ],
            "complex-bug": [
                "reduce-logs",
                "classify-investigation",
                "parallel-readers",
                "competing-hypotheses",
                "parent-diagnosis",
                "implement",
                "regression",
                "focused-validate",
                "commit-candidate",
                "review",
                "validate",
                "complete",
            ],
            "failure-recovery": [
                "classify-investigation",
                "reader-invalid",
                "parent-fallback",
                "parent-diagnosis",
                "implement",
                "regression",
                "focused-validate",
                "commit-candidate",
                "review",
                "validate",
                "complete",
            ],
        }
        for scenario_id, events in required.items():
            with self.subTest(scenario=scenario_id):
                self.assertEqual(events, scenarios[scenario_id]["events"])

    def test_complex_bug_readers_overlap_before_parent_diagnosis(self):
        scenario = self.scenarios()["complex-bug"]
        self.assertEqual(
            ["log-analyst", "evidence-explorer", "test-impact-analyst"],
            scenario["dispatches"],
        )
        outcome = self.harness("codex").run(scenario)
        parallel = next(
            entry["record"] for entry in outcome["events"] if entry["event"] == "parallel-readers"
        )
        self.assertEqual(3, parallel["active"])
        self.assertLess(
            scenario["events"].index("competing-hypotheses"),
            scenario["events"].index("parent-diagnosis"),
        )

    def test_invalid_result_falls_back_to_parent_before_diagnosis(self):
        scenario = self.scenarios()["failure-recovery"]
        outcome = self.harness("claude").run(scenario)
        fallback = next(
            entry["record"] for entry in outcome["events"] if entry["event"] == "parent-fallback"
        )
        self.assertEqual("invalid-result", fallback["reason_code"])
        self.assertEqual("fallback", fallback["parent_transition"])
        self.assertLess(
            scenario["events"].index("parent-fallback"),
            scenario["events"].index("parent-diagnosis"),
        )

    def test_writer_leases_serialize_a_coordinated_non_short_path(self):
        scenario = self.scenarios()["writer-serialization"]
        outcome = self.harness("codex").run(scenario)
        rejected = next(
            entry["record"] for entry in outcome["events"] if entry["event"] == "writer-two-rejected"
        )
        self.assertIn("another writer lease", rejected["detail"])
        self.assertEqual("coordinated", scenario["path"])

    def test_durable_promotion_validates_repository_state(self):
        scenario = self.scenarios()["feature-durable-promotion"]
        outcome = self.harness("claude").run(scenario)
        records = {entry["event"]: entry["record"] for entry in outcome["events"]}
        self.assertEqual("available", records["repository-probe"]["status"])
        self.assertEqual("repository", records["repository-probe"]["provider_id"])
        self.assertEqual("repository", records["checkpoint"]["provider_id"])
        self.assertEqual(scenario["durable_artifacts"][1], records["checkpoint"]["artifacts"]["ledger"])

    def test_durable_promotion_rejects_mismatched_state_provider_intent(self):
        scenario = json.loads(json.dumps(self.scenarios()["feature-durable-promotion"]))
        scenario["state_provider"] = "external"
        with self.assertRaisesRegex(AssertionError, "expected external state"):
            self.harness("claude").run(scenario)

    def test_kandev_and_bare_cli_produce_the_same_workflow_records(self):
        scenario = self.scenarios()["feature-durable-promotion"]
        bare = self.harness("claude", "bare-cli").run(scenario)
        managed = self.harness("claude", "kandev").run(scenario)
        bare_events = json.loads(json.dumps(bare["events"]))
        managed_events = json.loads(json.dumps(managed["events"]))
        for events in (bare_events, managed_events):
            checkpoint = next(entry["record"] for entry in events if entry["event"] == "checkpoint")
            checkpoint.pop("owner")
        self.assertEqual("bare-cli", bare["deck"])
        self.assertEqual("kandev", managed["deck"])
        self.assertEqual(bare["workflow"], managed["workflow"])
        self.assertEqual(bare_events, managed_events)
        self.assertEqual(bare["terminal"], managed["terminal"])


if __name__ == "__main__":
    unittest.main()
