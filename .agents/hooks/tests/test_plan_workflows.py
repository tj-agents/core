import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS = ROOT / ".agents" / "workflows"
FIXTURE = Path(__file__).parent / "fixtures" / "plan_workflow_scenarios.json"
sys.path.insert(0, str(WORKFLOWS))

from fixtures.lane_expectations import authored_skill, packaged_adapter
from workflow_runtime import (
    WorkflowContract,
    select_state_provider,
)
from fixtures.plan_authoring_harness import PlanAuthoringHarness
from fixtures.plan_workflow_harness import PlanWorkflowHarness


class PlanWorkflowAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.outcomes = {}
        for scenario in cls.fixture["scenarios"]:
            with PlanWorkflowHarness(
                WORKFLOWS,
                WorkflowContract,
                select_state_provider,
            ) as harness:
                cls.outcomes[scenario["id"]] = harness.run(scenario)
        cls.authoring_outcomes = {}
        for scenario in cls.fixture["authoring_scenarios"]:
            with PlanAuthoringHarness(
                WORKFLOWS,
                WorkflowContract,
                select_state_provider,
            ) as harness:
                cls.authoring_outcomes[scenario["id"]] = harness.run(scenario)

    def scenarios(self):
        return {scenario["id"]: scenario for scenario in self.fixture["scenarios"]}

    def run_scenario(self, scenario_id):
        return self.outcomes[scenario_id]

    def test_acceptance_matrix_covers_all_phase_four_recovery_paths(self):
        scenarios = self.scenarios()
        self.assertEqual(
            {
                "multi-phase-continuation",
                "phase-checkpoint-without-stop",
                "validation-failure-recovery",
                "fresh-context-transfer",
                "compatibility-entries",
                "blocker-return-path",
                "restart-recovery",
                "review-finding-recovery",
                "pr-slice-rollover",
                "trusted-continuation-resume",
                "contradicted-continuation-rereads",
            },
            set(scenarios),
        )
        self.assertEqual(
            {"complete", "continue", "transfer", "block"},
            {scenario["terminal"] for scenario in scenarios.values()},
        )
        for scenario in scenarios.values():
            self.assertEqual("plan-execution", scenario["workflow"])
            self.assertTrue(scenario["events"])

    def test_selection_contract_binds_cases_to_authored_catalogue_metadata(self):
        cases = {case["id"]: case for case in self.fixture["selection_cases"]}
        self.assertEqual(
            {
                "author-primary",
                "author-paraphrase",
                "author-design-reference",
                "execute-primary",
                "execute-paraphrase",
                "roadmap-compat",
                "resume-compat",
                "feature-neighbor",
                "review-neighbor",
            },
            set(cases),
        )
        self.assertEqual(
            ["plan-authoring", "plan-authoring", "plan-authoring"],
            [
                cases[name]["expected_skill"]
                for name in ("author-primary", "author-paraphrase", "author-design-reference")
            ],
        )
        self.assertEqual(
            ["plan-execution", "plan-execution"],
            [cases[name]["expected_skill"] for name in ("execute-primary", "execute-paraphrase")],
        )
        self.assertEqual("continue-roadmap", cases["roadmap-compat"]["expected_skill"])
        self.assertEqual("resume-plan", cases["resume-compat"]["expected_skill"])
        self.assertEqual("feature", cases["feature-neighbor"]["expected_skill"])
        self.assertEqual("review", cases["review-neighbor"]["expected_skill"])
        descriptions = {}
        for skill in {case["expected_skill"] for case in cases.values()}:
            body = authored_skill(skill).read_text(
                encoding="utf-8"
            )
            descriptions[skill] = next(
                line.removeprefix("description: ").strip()
                for line in body.splitlines()
                if line.startswith("description: ")
            )
        for case in cases.values():
            terms = [term.casefold() for term in case["description_terms"]]
            selected = descriptions[case["expected_skill"]].casefold()
            for term in terms:
                self.assertIn(term, selected, case["id"])
            for skill, description in descriptions.items():
                if skill == case["expected_skill"]:
                    continue
                self.assertFalse(
                    all(term in description.casefold() for term in terms),
                    f"{case['id']} also matches {skill}",
                )

    def test_plan_authoring_creates_graph_valid_artifacts_without_unauthorized_code(self):
        outcomes = self.authoring_outcomes
        self.assertEqual(
            {"planning-only-authoring", "author-then-execute"},
            set(outcomes),
        )
        for outcome in outcomes.values():
            self.assertEqual("plan-authoring", outcome["workflow"])
            self.assertEqual("Plan graph: 0 error(s), 0 warning(s)", outcome["plan_graph"])
            self.assertEqual(1, outcome["worktree_count"])
            self.assertTrue(outcome["changed_paths"])
            self.assertTrue(all(path.endswith(".md") for path in outcome["changed_paths"]))
            self.assertEqual(2, outcome["phase_gate_count"])
            self.assertFalse(outcome["plan_mentions_roadmap"])
            self.assertEqual(
                "webhooks/idempotent-processing",
                outcome["state"]["workflow_id"],
            )

    def test_authoring_authority_controls_identity_preserving_execution_entry(self):
        planning_only = self.authoring_outcomes["planning-only-authoring"]
        combined = self.authoring_outcomes["author-then-execute"]
        self.assertEqual("complete", planning_only["terminal"])
        self.assertFalse(planning_only["implementation_authorized"])
        self.assertIsNone(planning_only["transfer"])
        self.assertEqual("continue", combined["terminal"])
        self.assertTrue(combined["implementation_authorized"])
        self.assertEqual("continue", combined["transfer"]["transition"])
        self.assertEqual("plan-execution", combined["transfer"]["target_stage_id"])
        self.assertEqual(
            combined["state"]["workflow_id"],
            combined["execution_identity"],
        )

    def test_plan_skills_keep_one_canonical_body_and_thin_host_entries(self):
        for skill in (
            "plan-authoring",
            "plan-execution",
            "resume-plan",
            "continue-roadmap",
            "failing-tests",
        ):
            canonical = authored_skill(skill)
            plugin_canonical = ROOT / "plugins" / "engineering" / canonical.relative_to(ROOT)
            self.assertEqual(
                canonical.read_text(encoding="utf-8"),
                plugin_canonical.read_text(encoding="utf-8"),
            )
            for host, tree in (("claude", "skills"), ("codex", "codex-skills")):
                with self.subTest(skill=skill, host=host):
                    adapter = (ROOT / f".{host}" / "skills" / skill / "SKILL.md")
                    self.assertIn("canonical shared definition", adapter.read_text(encoding="utf-8"))
                    packaged = (
                        ROOT / "plugins" / "engineering" / tree / skill / "SKILL.md"
                    ).read_text(encoding="utf-8")
                    self.assertEqual(packaged_adapter(ROOT, skill, host), packaged)

    def test_trusted_continuation_resumes_without_reading_the_plan_corpus(self):
        outcome = self.run_scenario("trusted-continuation-resume")
        records = {entry["event"]: entry["record"] for entry in outcome["events"]}
        accepted = records["accept-continuation"]
        self.assertTrue(accepted["trusted"])
        self.assertEqual([], accepted["corpus_reads"])
        self.assertIn(
            "plans/runtime/RUNTIME_PROGRESS.md",
            accepted["corpus_reads_when_read"],
        )
        for field in ("workflow_id", "status", "owner", "artifacts"):
            self.assertEqual(
                accepted["corpus_state"][field],
                accepted["state"][field],
                field,
            )
        self.assertEqual(
            accepted["corpus_state"]["next_action"]["description"],
            accepted["state"]["next_action"]["description"],
        )
        self.assertEqual("continue", outcome["terminal"]["transition"])

    def test_contradicted_continuation_falls_back_to_the_plan_corpus(self):
        outcome = self.run_scenario("contradicted-continuation-rereads")
        records = {entry["event"]: entry["record"] for entry in outcome["events"]}
        contradicted = records["contradicted-continuation"]
        self.assertFalse(contradicted["trusted"])
        self.assertIn(
            "plans/runtime/RUNTIME_PROGRESS.md",
            contradicted["corpus_reads"],
        )
        self.assertEqual(
            "Feature/plan-acceptance",
            contradicted["state"]["owner"]["branch"],
        )

    def test_a_build_error_is_not_a_red_run(self):
        failing = authored_skill("failing-tests").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "A compiler, restore, or build error is not a red run and does not select this skill.",
            failing,
        )
        self.assertIn("**Neither is a compiler, restore, or generator error.**", failing)
        self.assertIn("diagnose/fix/rebuild loop", failing)
        execution = authored_skill("plan-execution").read_text(
            encoding="utf-8"
        )
        self.assertIn("once a test run itself comes back red", execution)

    def test_generic_unit_failure_stays_with_parent_or_repository_guidance(self):
        body = authored_skill("failing-tests").read_text(
            encoding="utf-8"
        )
        self.assertIn("| Unit | Use the repository's unit-test guidance", body)
        self.assertNotIn("| Unit or integration |", body)
        self.assertIn(
            "| In-process .NET integration using `WebApplicationFactory` |",
            body,
        )

    def test_scripted_scenarios_execute_to_typed_terminals(self):
        for scenario in self.fixture["scenarios"]:
            with self.subTest(scenario=scenario["id"]):
                outcome = self.run_scenario(scenario["id"])
                self.assertEqual(scenario["entry"], outcome["entry"])
                self.assertEqual("plan-execution", outcome["workflow"])
                self.assertEqual(
                    scenario["events"],
                    [entry["event"] for entry in outcome["events"]],
                )
                if scenario["terminal"] == "complete":
                    self.assertEqual("complete", outcome["terminal"]["status"])
                    self.assertEqual(
                        "complete", outcome["terminal"]["transition"]["transition"]
                    )
                elif scenario["terminal"] == "continue":
                    self.assertEqual("continue", outcome["terminal"]["transition"])
                elif scenario["terminal"] == "transfer":
                    self.assertEqual(
                        "transfer",
                        outcome["terminal"]["state"]["transition"]["transition"],
                    )
                    self.assertEqual("context-transfer", outcome["terminal"]["gate"]["gate_kind"])
                else:
                    self.assertEqual("block", outcome["terminal"]["transition"]["transition"])
                    self.assertEqual("dependency", outcome["terminal"]["gate"]["gate_kind"])

    def test_multi_phase_checkpoints_continue_before_terminal_completion(self):
        outcome = self.run_scenario("multi-phase-continuation")
        records = {entry["event"]: entry["record"] for entry in outcome["events"]}
        first = records["checkpoint-phase-one"]
        second = records["checkpoint-phase-two"]
        self.assertEqual("checkpoint", first["transition"]["transition"])
        self.assertEqual("active", first["state"]["status"])
        self.assertEqual("Implement phase two.", first["state"]["next_action"]["description"])
        self.assertEqual("checkpoint", second["transition"]["transition"])
        self.assertEqual("complete", second["state"]["status"])
        self.assertLess(
            self.scenarios()["multi-phase-continuation"]["events"].index("continue"),
            self.scenarios()["multi-phase-continuation"]["events"].index(
                "implement-phase-two"
            ),
        )

    def test_phase_checkpoint_is_material_but_not_a_stop(self):
        outcome = self.run_scenario("phase-checkpoint-without-stop")
        records = {entry["event"]: entry["record"] for entry in outcome["events"]}
        checkpoint = records["checkpoint-phase"]
        self.assertEqual("checkpoint", checkpoint["transition"]["transition"])
        self.assertEqual("active", checkpoint["state"]["status"])
        self.assertEqual("continue", records["continue"]["transition"])
        self.assertEqual("continue", outcome["terminal"]["transition"])

    def test_validation_failure_returns_to_parent_diagnosis_and_continues(self):
        scenario = self.scenarios()["validation-failure-recovery"]
        outcome = self.run_scenario(scenario["id"])
        records = {entry["event"]: entry["record"] for entry in outcome["events"]}
        self.assertEqual("retry", records["validation-failed"]["transition"])
        self.assertEqual("parent-diagnosis", records["validation-failed"]["target_stage_id"])
        self.assertLess(scenario["events"].index("parent-diagnosis"), scenario["events"].index("repair"))
        self.assertLess(scenario["events"].index("revalidate"), scenario["events"].index("checkpoint-repair"))
        self.assertEqual("continue", outcome["terminal"]["transition"])

    def test_deliberate_transfer_carries_checkpoint_identity_and_resume_condition(self):
        scenario = self.scenarios()["fresh-context-transfer"]
        outcome = self.run_scenario(scenario["id"])
        transfer = outcome["terminal"]
        self.assertEqual("transfer", transfer["state"]["next_action"]["kind"])
        self.assertEqual(scenario["resume_condition"], transfer["gate"]["resume_condition"])
        self.assertEqual(["plans/runtime/RUNTIME_PROGRESS.md"], transfer["gate"]["evidence"])
        self.assertEqual(transfer["state"], transfer["re_resolved"])
        self.assertEqual(
            "resume-from-checkpoint",
            transfer["state"]["transition"]["target_stage_id"],
        )
        self.assertEqual(
            scenario["resume_condition"],
            transfer["state"]["next_action"]["resume_condition"],
        )

    def test_compatibility_entries_have_one_semantic_owner_each(self):
        outcome = self.run_scenario("compatibility-entries")
        records = {entry["event"]: entry["record"] for entry in outcome["events"]}
        self.assertEqual(
            {"entry": "resume-plan", "owner": "plan-execution"},
            records["resume-plan-entry"],
        )
        self.assertEqual(
            {"entry": "continue-roadmap", "owner": "plan-authoring"},
            records["continue-roadmap-entry"],
        )

    def test_dependency_blocker_records_typed_gate_and_reciprocal_return(self):
        scenario = self.scenarios()["blocker-return-path"]
        outcome = self.run_scenario(scenario["id"])
        records = {entry["event"]: entry["record"] for entry in outcome["events"]}
        blocked = records["block"]
        returned = records["reciprocal-return"]
        self.assertEqual("blocked", blocked["status"])
        self.assertEqual(scenario["blocker"]["owner"], blocked["blocker"]["owner"])
        self.assertEqual(scenario["blocker"]["owner"], returned["return_path"])
        self.assertEqual("plans/runtime/RUNTIME_PROGRESS.md", returned["return_target"])
        self.assertEqual("Plan graph: 0 error(s), 0 warning(s)", returned["plan_graph"])

    def test_restart_re_resolves_the_same_portable_checkpoint(self):
        outcome = self.run_scenario("restart-recovery")
        records = {entry["event"]: entry["record"] for entry in outcome["events"]}
        checkpoint = records["checkpoint-restart"]["state"]
        restart = records["restart"]
        resolved = records["re-resolve"]
        self.assertEqual("repository", restart["provider_id"])
        self.assertEqual(checkpoint["owner"]["head"], restart["previous_head"])
        self.assertEqual(checkpoint["owner"], resolved["owner"])
        self.assertEqual(checkpoint["artifacts"], resolved["artifacts"])
        self.assertEqual(checkpoint["next_action"], resolved["next_action"])

    def test_review_finding_returns_through_address_and_incremental_review(self):
        scenario = self.scenarios()["review-finding-recovery"]
        outcome = self.run_scenario(scenario["id"])
        records = {entry["event"]: entry["record"] for entry in outcome["events"]}
        self.assertEqual("retry", records["review-finding"]["transition"])
        self.assertEqual("address-review", records["review-finding"]["target_stage_id"])
        repaired = records["checkpoint-review-repair"]["state"]["next_action"]["description"]
        self.assertIn("incremental review", repaired.casefold())
        self.assertLess(
            scenario["events"].index("address-review"),
            scenario["events"].index("incremental-review"),
        )
        self.assertEqual("continue", outcome["terminal"]["transition"])

    def test_merged_pr_slice_rolls_to_fresh_default_with_same_plan_identity(self):
        outcome = self.run_scenario("pr-slice-rollover")
        records = {entry["event"]: entry["record"] for entry in outcome["events"]}
        rollover = records["rollover-slice"]
        self.assertTrue(rollover["old_owner_closed"])
        self.assertEqual(rollover["main_head"], rollover["merge_base"])
        self.assertNotEqual(
            rollover["previous_owner"]["worktree"],
            rollover["state"]["owner"]["worktree"],
        )
        self.assertEqual(
            "Feature/plan-acceptance-slice-two",
            rollover["state"]["owner"]["branch"],
        )
        self.assertEqual(
            "runtime/plan-execution",
            rollover["state"]["workflow_id"],
        )
        self.assertEqual(
            "Implement the second PR slice from fresh default.",
            rollover["state"]["next_action"]["description"],
        )
        self.assertEqual("continue", rollover["transition"]["transition"])
        self.assertEqual("continue", outcome["terminal"]["transition"])


if __name__ == "__main__":
    unittest.main()
