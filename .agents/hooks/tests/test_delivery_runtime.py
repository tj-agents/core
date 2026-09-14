import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS = ROOT / ".agents" / "workflows"
sys.path.insert(0, str(WORKFLOWS))
from delivery_runtime import DeliveryContractViolation, PersistentDeliveryRouter


HEAD = "a" * 40
REPAIR_HEAD = "b" * 40
SUCCESSOR_HEAD = "c" * 40


class PersistentDeliveryRouterTests(unittest.TestCase):
    def setUp(self):
        self.router = PersistentDeliveryRouter()
        self.binding = {
            "repository": "tomjseery/base-agents",
            "pr_url": "https://github.com/tomjseery/base-agents/pull/70",
            "pr_number": 70,
            "worktree": r"C:\source\agent-standards.worktrees\Feature-delivery",
            "branch": "Feature/Delivery",
            "remote_head_sha": HEAD,
            "pending_evidence": [
                {"check_id": "check-11", "run_id": "run-22", "head_sha": HEAD}
            ],
            "review": {
                "work_order": "reviews/Feature-Delivery.md",
                "work_order_order": ["native-general", "test-impact"],
                "reviewed_sha": None,
            },
            "merge_authorization": {"mode": "absent", "instruction": None},
            "completion_condition": "PR is merged or reaches a human decision",
        }

    def observation(self, **overrides):
        observation = {
            "pr_number": 70,
            "remote_head_sha": HEAD,
            "state": "open",
            "state_token": "state-2",
            "checks_conclusion": "pending",
            "review_judgment": "pending",
            "reviewed_sha": None,
        }
        observation.update(overrides)
        return observation

    def test_binding_rejects_check_evidence_from_another_head(self):
        self.binding["pending_evidence"][0]["head_sha"] = REPAIR_HEAD

        with self.assertRaisesRegex(DeliveryContractViolation, "another head"):
            self.router.validate_binding(self.binding)

    def test_binding_rejects_a_pr_url_for_another_repository_or_number(self):
        self.binding["pr_url"] = "https://github.com/tomjseery/other/pull/70"

        with self.assertRaisesRegex(DeliveryContractViolation, "PR URL"):
            self.router.validate_binding(self.binding)

    def test_one_continuation_is_created_updated_and_never_duplicated(self):
        created = self.router.continuation_operation(self.binding, [])
        self.assertEqual("create", created["operation"])

        existing = [{"task_id": "task-1", "owner_key": created["owner_key"]}]
        updated = self.router.continuation_operation(self.binding, existing)
        self.assertEqual("update", updated["operation"])
        self.assertEqual("task-1", updated["task_id"])

        with self.assertRaisesRegex(DeliveryContractViolation, "more than one"):
            self.router.continuation_operation(self.binding, existing * 2)

    def test_owner_repair_rebinds_the_same_delivery_to_new_exact_runs(self):
        updated = self.router.rebind_after_owner_push(
            self.binding,
            REPAIR_HEAD,
            [{"check_id": "check-33", "run_id": "run-44", "head_sha": REPAIR_HEAD}],
            owner_push=True,
        )

        self.assertEqual(REPAIR_HEAD, updated["remote_head_sha"])
        self.assertIsNone(updated["review"]["reviewed_sha"])
        self.assertEqual(self.router.owner_key(self.binding), self.router.owner_key(updated))
        self.assertNotEqual(self.router.binding_key(self.binding), self.router.binding_key(updated))

    def test_workflow_owner_survives_an_explicit_successor_rebind(self):
        self.binding["workflow_handoff"] = {
            "workflow_id": "package-upgrade-plan",
            "state_artifact": "plans/package-upgrade.md",
            "next_stage": "plan-execution",
        }
        successor = {
            **self.binding,
            "pr_url": "https://github.com/tomjseery/base-agents/pull/71",
            "pr_number": 71,
            "worktree": r"C:\source\agent-standards.worktrees\Feature-plan-execution",
            "branch": "Feature/Plan-execution",
            "remote_head_sha": SUCCESSOR_HEAD,
            "pending_evidence": [
                {
                    "check_id": "check-71",
                    "run_id": "run-71",
                    "head_sha": SUCCESSOR_HEAD,
                }
            ],
        }

        rebound = self.router.rebind_to_successor(
            self.binding,
            successor,
            parent_transfer=True,
        )

        self.assertEqual(
            self.router.owner_key(self.binding),
            self.router.owner_key(rebound),
        )
        self.assertNotEqual(
            self.router.binding_key(self.binding),
            self.router.binding_key(rebound),
        )
        self.assertEqual(
            "reviews/Feature-Plan-execution.md",
            rebound["review"]["work_order"],
        )
        self.assertIsNone(rebound["review"]["reviewed_sha"])
        self.assertEqual(
            {"mode": "absent", "instruction": None},
            rebound["merge_authorization"],
        )

    def test_successor_rebind_does_not_inherit_predecessor_review_or_authorization(self):
        self.binding["workflow_handoff"] = {
            "workflow_id": "package-upgrade-plan",
            "state_artifact": "plans/package-upgrade.md",
            "next_stage": "plan-execution",
        }
        self.binding["review"]["reviewed_sha"] = HEAD
        self.binding["merge_authorization"] = {
            "mode": "merge",
            "instruction": "Merge only the package upgrade PR.",
        }
        successor = {
            **self.binding,
            "pr_url": "https://github.com/tomjseery/base-agents/pull/71",
            "pr_number": 71,
            "branch": "Feature/Plan-execution",
            "remote_head_sha": SUCCESSOR_HEAD,
            "pending_evidence": [
                {
                    "check_id": "check-71",
                    "run_id": "run-71",
                    "head_sha": SUCCESSOR_HEAD,
                }
            ],
        }

        rebound = self.router.rebind_to_successor(
            self.binding,
            successor,
            parent_transfer=True,
        )

        self.assertIsNone(rebound["review"]["reviewed_sha"])
        self.assertNotEqual(
            self.binding["review"]["work_order"],
            rebound["review"]["work_order"],
        )
        self.assertEqual(
            {"mode": "absent", "instruction": None},
            rebound["merge_authorization"],
        )

    def test_successor_authorization_must_bind_the_exact_successor(self):
        self.binding["workflow_handoff"] = {
            "workflow_id": "package-upgrade-plan",
            "state_artifact": "plans/package-upgrade.md",
            "next_stage": "plan-execution",
        }
        successor = {
            **self.binding,
            "pr_url": "https://github.com/tomjseery/base-agents/pull/71",
            "pr_number": 71,
            "branch": "Feature/Plan-execution",
            "remote_head_sha": SUCCESSOR_HEAD,
            "pending_evidence": [
                {
                    "check_id": "check-71",
                    "run_id": "run-71",
                    "head_sha": SUCCESSOR_HEAD,
                }
            ],
        }
        authorization = {
            "repository": successor["repository"],
            "pr_number": successor["pr_number"],
            "branch": successor["branch"],
            "remote_head_sha": successor["remote_head_sha"],
            "mode": "merge",
            "instruction": "Merge this exact successor PR when its own gates pass.",
        }

        rebound = self.router.rebind_to_successor(
            self.binding,
            successor,
            parent_transfer=True,
            successor_authorization=authorization,
        )
        self.assertEqual("merge", rebound["merge_authorization"]["mode"])

        authorization["remote_head_sha"] = HEAD
        with self.assertRaisesRegex(DeliveryContractViolation, "exact successor"):
            self.router.rebind_to_successor(
                self.binding,
                successor,
                parent_transfer=True,
                successor_authorization=authorization,
            )

    def test_successor_rebind_rejects_an_external_or_unowned_transfer(self):
        self.binding["workflow_handoff"] = {
            "workflow_id": "package-upgrade-plan",
            "state_artifact": "plans/package-upgrade.md",
            "next_stage": "plan-execution",
        }
        successor = {
            **self.binding,
            "pr_url": "https://github.com/tomjseery/base-agents/pull/71",
            "pr_number": 71,
            "remote_head_sha": SUCCESSOR_HEAD,
            "pending_evidence": [
                {
                    "check_id": "check-71",
                    "run_id": "run-71",
                    "head_sha": SUCCESSOR_HEAD,
                }
            ],
        }

        with self.assertRaisesRegex(DeliveryContractViolation, "only the parent"):
            self.router.rebind_to_successor(
                self.binding,
                successor,
                parent_transfer=False,
            )
        successor["workflow_handoff"] = {
            **successor["workflow_handoff"],
            "workflow_id": "another-plan",
        }
        with self.assertRaisesRegex(DeliveryContractViolation, "another workflow"):
            self.router.rebind_to_successor(
                self.binding,
                successor,
                parent_transfer=True,
            )

    def test_workflow_handoff_rejects_a_windows_absolute_state_artifact(self):
        self.binding["workflow_handoff"] = {
            "workflow_id": "package-upgrade-plan",
            "state_artifact": r"C:\plans\package-upgrade.md",
            "next_stage": "plan-execution",
        }

        with self.assertRaisesRegex(DeliveryContractViolation, "repository-relative"):
            self.router.validate_binding(self.binding)

    def test_workflow_handoff_rejects_windows_drive_and_root_relative_artifacts(self):
        for state_artifact in (r"C:plans\package-upgrade.md", r"\plans\package-upgrade.md"):
            with self.subTest(state_artifact=state_artifact):
                self.binding["workflow_handoff"] = {
                    "workflow_id": "package-upgrade-plan",
                    "state_artifact": state_artifact,
                    "next_stage": "plan-execution",
                }

                with self.assertRaisesRegex(DeliveryContractViolation, "repository-relative"):
                    self.router.validate_binding(self.binding)

    def test_structured_owner_keys_do_not_collide_on_delimiter_text(self):
        first = copy.deepcopy(self.binding)
        second = copy.deepcopy(self.binding)
        first["branch"] = "Feature/a|b"
        second["branch"] = "Feature/a"
        second["worktree"] = f"{second['worktree']}|b"

        self.assertNotEqual(self.router.owner_key(first), self.router.owner_key(second))

    def test_external_head_replacement_stops_and_removes_continuation(self):
        decision = self.router.decide(
            self.binding,
            self.observation(remote_head_sha=REPAIR_HEAD),
        )

        self.assertEqual("human-gate", decision["kind"])
        self.assertEqual("external-head-replacement", decision["terminal"])
        self.assertTrue(decision["remove_continuation"])

    def test_unchanged_state_does_nothing(self):
        self.binding["last_state_token"] = "state-2"

        decision = self.router.decide(self.binding, self.observation())

        self.assertEqual("noop", decision["kind"])
        self.assertFalse(decision["remove_continuation"])

    def test_each_remote_test_tier_routes_to_a_fresh_debug_context(self):
        expected = {
            "unit": "failing-tests",
            "integration": "integration-debug",
            "e2e-api": "e2e-api-debug",
            "e2e-ui": "e2e-ui-debug",
            "e2e-both": "e2e-debug",
            "e2e-ui-regression": "e2e-ui-debug",
        }
        for tier, skill in expected.items():
            with self.subTest(tier=tier):
                decision = self.router.decide(
                    self.binding,
                    self.observation(
                        checks_conclusion="failure",
                        failure_tier=tier,
                        failure_signature=f"{tier} failed at assertion 12",
                        failed_evidence=self.binding["pending_evidence"][0],
                    ),
                )
                self.assertEqual("dispatch", decision["kind"])
                self.assertEqual("implementation", decision["semantic_stage"])
                self.assertEqual(skill, decision["skill"])
                self.assertTrue(decision["fresh_context"])
                self.assertIn("Check ID: check-11", decision["prompt"])
                self.assertIn("Run ID: run-22", decision["prompt"])
                self.assertIn(HEAD, decision["prompt"])
                self.assertIn("Do not merge", decision["prompt"])

    def test_merge_group_failure_binds_both_run_head_and_pr_source_head(self):
        merge_group_head = "c" * 40
        evidence = {
            "check_id": "check-merge-11",
            "run_id": "run-merge-22",
            "head_sha": merge_group_head,
            "event": "merge_group",
            "pr_head_sha": HEAD,
        }
        self.binding["pending_evidence"] = [evidence]

        decision = self.router.decide(
            self.binding,
            self.observation(
                checks_conclusion="failure",
                failure_tier="e2e-both",
                failure_signature="merge queue E2E assertion failed",
                failed_evidence=evidence,
            ),
        )

        self.assertEqual("e2e-debug", decision["skill"])
        self.assertIn(f"Run head: {merge_group_head}", decision["prompt"])
        self.assertIn(f"Bound PR source head: {HEAD}", decision["prompt"])

        evidence["pr_head_sha"] = REPAIR_HEAD
        with self.assertRaisesRegex(DeliveryContractViolation, "another PR head"):
            self.router.validate_binding(self.binding)

    def test_green_head_routes_to_independent_review(self):
        decision = self.router.decide(
            self.binding,
            self.observation(checks_conclusion="success"),
        )

        self.assertEqual("review", decision["semantic_stage"])
        self.assertEqual("review", decision["skill"])
        self.assertTrue(decision["fresh_context"])

    def test_review_findings_route_to_serial_remediation(self):
        decision = self.router.decide(
            self.binding,
            self.observation(
                checks_conclusion="success",
                review_judgment="findings",
                reviewed_sha=HEAD,
            ),
        )

        self.assertEqual("implementation", decision["semantic_stage"])
        self.assertEqual("address-review", decision["skill"])
        self.assertFalse(decision["fresh_context"])

    def test_review_evidence_from_another_head_is_rejected(self):
        with self.assertRaisesRegex(DeliveryContractViolation, "review evidence"):
            self.router.decide(
                self.binding,
                self.observation(
                    checks_conclusion="success",
                    review_judgment="findings",
                    reviewed_sha=REPAIR_HEAD,
                ),
            )

    def test_completed_review_requires_a_current_head_watermark(self):
        for judgment in ("clean", "findings"):
            with self.subTest(judgment=judgment):
                with self.assertRaisesRegex(DeliveryContractViolation, "reviewed head"):
                    self.router.decide(
                        self.binding,
                        self.observation(
                            checks_conclusion="success",
                            review_judgment=judgment,
                        ),
                    )

    def test_unknown_review_judgment_is_rejected(self):
        with self.assertRaisesRegex(DeliveryContractViolation, "unknown review judgment"):
            self.router.decide(
                self.binding,
                self.observation(
                    checks_conclusion="success",
                    review_judgment="approved-ish",
                ),
            )

    def test_pending_review_cannot_merge_with_a_watermark(self):
        self.binding["merge_authorization"] = {
            "mode": "merge",
            "instruction": "The user explicitly authorized merge.",
        }

        with self.assertRaisesRegex(DeliveryContractViolation, "pending review"):
            self.router.decide(
                self.binding,
                self.observation(
                    checks_conclusion="success",
                    review_judgment="pending",
                    reviewed_sha=HEAD,
                ),
            )

    def test_unauthorized_merge_stops_and_removes_continuation(self):
        decision = self.router.decide(
            self.binding,
            self.observation(
                checks_conclusion="success",
                review_judgment="clean",
                reviewed_sha=HEAD,
            ),
        )

        self.assertEqual("human-gate", decision["kind"])
        self.assertEqual("merge-authorization", decision["terminal"])
        self.assertTrue(decision["remove_continuation"])

    def test_authorized_current_head_may_enter_merge(self):
        self.binding["merge_authorization"] = {
            "mode": "auto",
            "instruction": "The user explicitly authorized auto-merge.",
        }

        decision = self.router.decide(
            self.binding,
            self.observation(
                checks_conclusion="success",
                review_judgment="clean",
                reviewed_sha=HEAD,
            ),
        )

        self.assertEqual("merge", decision["kind"])
        self.assertEqual("review", decision["semantic_stage"])
        self.assertEqual("auto", decision["authorization"]["mode"])

    def test_every_pr_terminal_removes_the_continuation(self):
        for state in ("merged", "closed", "superseded"):
            with self.subTest(state=state):
                decision = self.router.decide(
                    self.binding,
                    self.observation(state=state),
                )
                self.assertEqual("cleanup", decision["kind"])
                self.assertTrue(decision["remove_continuation"])

    def test_intermediate_plan_merge_transfers_without_removing_continuation(self):
        self.binding["workflow_handoff"] = {
            "workflow_id": "package-upgrade-plan",
            "state_artifact": "plans/package-upgrade.md",
            "next_stage": "plan-execution",
        }

        decision = self.router.decide(
            self.binding,
            self.observation(state="merged"),
        )

        self.assertEqual("transfer", decision["kind"])
        self.assertEqual("implementation", decision["semantic_stage"])
        self.assertEqual("plan-execution", decision["skill"])
        self.assertTrue(decision["close_delivery_binding"])
        self.assertFalse(decision["remove_continuation"])

    def test_intermediate_merge_with_an_external_head_stops_the_continuation(self):
        self.binding["workflow_handoff"] = {
            "workflow_id": "package-upgrade-plan",
            "state_artifact": "plans/package-upgrade.md",
            "next_stage": "plan-execution",
        }

        decision = self.router.decide(
            self.binding,
            self.observation(state="merged", remote_head_sha=REPAIR_HEAD),
        )

        self.assertEqual("human-gate", decision["kind"])
        self.assertEqual("external-head-replacement", decision["terminal"])
        self.assertTrue(decision["remove_continuation"])

    def test_external_head_replacement_wins_over_replacement_review_evidence(self):
        decision = self.router.decide(
            self.binding,
            self.observation(
                remote_head_sha=REPAIR_HEAD,
                review_judgment="clean",
                reviewed_sha=REPAIR_HEAD,
            ),
        )

        self.assertEqual("human-gate", decision["kind"])
        self.assertEqual("external-head-replacement", decision["terminal"])
        self.assertTrue(decision["remove_continuation"])

    def test_external_pr_replacement_wins_over_inconsistent_review_evidence(self):
        decision = self.router.decide(
            self.binding,
            self.observation(
                pr_number=71,
                review_judgment="clean",
                reviewed_sha=REPAIR_HEAD,
            ),
        )

        self.assertEqual("cleanup", decision["kind"])
        self.assertEqual("superseded", decision["terminal"])
        self.assertTrue(decision["remove_continuation"])


if __name__ == "__main__":
    unittest.main()
