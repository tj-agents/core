import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ci_change_classifier import classify_validation, may_cancel_prior_validation


class CiChangeClassifierTests(unittest.TestCase):
    def test_metadata_only_tip_reuses_green_executable_validation(self):
        result = classify_validation(
            "pull_request",
            "synchronize",
            ["plans/launch/EXAMPLE_PROGRESS.md", "reviews/EXAMPLE.md"],
            "tree-a",
            "tree-a",
            "success",
        )

        self.assertEqual("metadata-only", result)

    def test_metadata_only_tip_does_not_supersede_live_executable_validation(self):
        result = classify_validation(
            "pull_request",
            "synchronize",
            ["plans/launch/EXAMPLE_PROGRESS.md"],
            "tree-a",
            "tree-a",
            "in_progress",
        )

        self.assertEqual("metadata-only", result)

    def test_code_and_metadata_require_full_validation(self):
        result = classify_validation(
            "pull_request",
            "synchronize",
            ["src/Service.cs", "plans/launch/EXAMPLE_PROGRESS.md"],
            "tree-a",
            "tree-b",
            "success",
        )

        self.assertEqual("full", result)

    def test_unknown_comparison_requires_full_validation(self):
        result = classify_validation(
            "pull_request",
            "synchronize",
            ["plans/launch/EXAMPLE_PROGRESS.md"],
            None,
            "tree-a",
            "success",
        )

        self.assertEqual("full", result)

    def test_unvalidated_previous_head_requires_full_validation(self):
        result = classify_validation(
            "pull_request",
            "synchronize",
            ["plans/launch/EXAMPLE_PROGRESS.md"],
            "tree-a",
            "tree-a",
            "failure",
        )

        self.assertEqual("full", result)

    def test_merge_group_always_requires_full_validation(self):
        result = classify_validation(
            "merge_group",
            "checks_requested",
            ["plans/launch/EXAMPLE_PROGRESS.md"],
            "tree-a",
            "tree-a",
            "success",
        )

        self.assertEqual("full", result)

    def test_pull_request_open_requires_full_validation(self):
        result = classify_validation(
            "pull_request",
            "opened",
            ["plans/launch/EXAMPLE_PROGRESS.md"],
            "tree-a",
            "tree-a",
            "success",
        )

        self.assertEqual("full", result)

    def test_push_event_requires_full_validation(self):
        result = classify_validation(
            "push",
            None,
            ["plans/launch/EXAMPLE_PROGRESS.md"],
            "tree-a",
            "tree-a",
            "success",
        )

        self.assertEqual("full", result)

    def test_metadata_classification_cannot_cancel_live_executable_validation(self):
        self.assertFalse(may_cancel_prior_validation("metadata-only"))

    def test_executable_classification_may_supersede_an_older_candidate(self):
        self.assertTrue(may_cancel_prior_validation("full"))


if __name__ == "__main__":
    unittest.main()
