import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS = ROOT / ".agents" / "workflows"
sys.path.insert(0, str(WORKFLOWS))
from delivery_runtime import DeliveryContractViolation, PersistentDeliveryRouter, binding_from_artifact


HEAD = "a" * 40
REPAIR_HEAD = "b" * 40


class PersistentDeliveryRouterTests(unittest.TestCase):
    def setUp(self):
        self.router = PersistentDeliveryRouter()
        self.binding = {
            "repository": "Concertable/agents",
            "pr_url": "https://github.com/Concertable/agents/pull/70",
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

    def test_binding_rejects_check_evidence_from_another_head(self):
        self.binding["pending_evidence"][0]["head_sha"] = REPAIR_HEAD

        with self.assertRaisesRegex(DeliveryContractViolation, "another head"):
            self.router.validate_binding(self.binding)

    def test_binding_rejects_a_pr_url_for_another_repository_or_number(self):
        self.binding["pr_url"] = "https://github.com/Concertable/other/pull/70"

        with self.assertRaisesRegex(DeliveryContractViolation, "PR URL"):
            self.router.validate_binding(self.binding)

    def test_workflow_handoff_rejects_a_windows_absolute_state_artifact(self):
        self.binding["workflow_handoff"] = {
            "workflow_id": "package-upgrade-plan",
            "state_artifact": r"C:\plans\package-upgrade.md",
            "next_stage": "workflow:run",
        }

        with self.assertRaisesRegex(DeliveryContractViolation, "repository-relative"):
            self.router.validate_binding(self.binding)

    def test_workflow_handoff_rejects_windows_drive_and_root_relative_artifacts(self):
        for state_artifact in (r"C:plans\package-upgrade.md", r"\plans\package-upgrade.md"):
            with self.subTest(state_artifact=state_artifact):
                self.binding["workflow_handoff"] = {
                    "workflow_id": "package-upgrade-plan",
                    "state_artifact": state_artifact,
                    "next_stage": "workflow:run",
                }

                with self.assertRaisesRegex(DeliveryContractViolation, "repository-relative"):
                    self.router.validate_binding(self.binding)

    def test_artifact_aliases_round_trip_to_a_valid_binding(self):
        artifact = {
            "repo": self.binding["repository"], "pr": self.binding["pr_number"],
            "pr_url": self.binding["pr_url"], "branch": self.binding["branch"],
            "worktree": self.binding["worktree"], "head": self.binding["remote_head_sha"],
            **{key: self.binding[key] for key in (
                "pending_evidence", "review", "merge_authorization", "completion_condition")},
        }

        self.assertEqual(self.binding, self.router.validate_binding(binding_from_artifact(artifact)))


if __name__ == "__main__":
    unittest.main()
