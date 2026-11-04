"""Workflow catch-up: live item states and stalled sessions."""

import importlib.util
import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "catch_up", ROOT / ".agents/workflow/utility/catch-up/scripts/catch_up.py"
)
assert SPEC is not None and SPEC.loader is not None
CATCH_UP = importlib.util.module_from_spec(SPEC)
sys.modules["catch_up"] = CATCH_UP
SPEC.loader.exec_module(CATCH_UP)

PR = "https://github.com/tj-agents/core/pull/551"
ISSUE = "https://github.com/tj-agents/personal/issues/49"
BRANCH = "tj-agents/template:Refactor/SubjectSkillLayout"


def graphql_response(text: str) -> dict[str, Any]:
    assert text.count("repository(") == 3
    return {
        "data": {
            "i0": {
                "pullRequest": {
                    "state": "MERGED",
                    "title": "Add catch-up",
                    "isDraft": False,
                    "mergedAt": "2026-11-03T12:00:00Z",
                    "reviewDecision": "APPROVED",
                    "headRefName": "Feature/CatchUp",
                }
            },
            "i1": {
                "issue": {
                    "state": "OPEN",
                    "title": "Approval command",
                    "stateReason": None,
                    "closedAt": None,
                }
            },
            "i2": {
                "ref": {"name": "Refactor/SubjectSkillLayout"},
                "pullRequests": {
                    "nodes": [
                        {
                            "url": "https://github.com/tj-agents/template/pull/56",
                            "number": 56,
                            "state": "OPEN",
                            "mergedAt": None,
                        }
                    ]
                },
            },
        }
    }


SESSIONS = {
    "SubjectSkillLayout": [
        {
            "host": "codex",
            "id": "01a187bc",
            "status": "closed",
            "activity": "2026-10-30T01:31:54Z",
            "matched_by": ["branch"],
            "work_item": {"status": "active", "title": "Subject layout"},
        },
        {
            "host": "claude",
            "id": "f8af11f2",
            "status": "closed",
            "activity": "2026-10-20T10:38:30Z",
            "matched_by": ["message"],
            "work_item": None,
        },
    ],
    "CatchUp": [
        {
            "host": "claude",
            "id": "36c6da7d",
            "status": "closed",
            "activity": "2026-11-03T12:00:00Z",
            "matched_by": ["branch"],
            "work_item": None,
        }
    ],
}


class CatchUpTests(unittest.TestCase):
    def report(self) -> dict[str, Any]:
        items = [
            CATCH_UP.parse("pr", PR),
            CATCH_UP.parse("issue", ISSUE),
            CATCH_UP.parse("branch", BRANCH),
        ]
        result: dict[str, Any] = CATCH_UP.report(
            items, [], graphql_response, lambda topic: SESSIONS.get(topic, [])
        )
        return result

    def test_items_report_live_state(self) -> None:
        states = {item["reference"]: item["state"] for item in self.report()["items"]}
        self.assertEqual(states, {PR: "MERGED", ISSUE: "OPEN", BRANCH: "OPEN"})

    def test_closed_owner_of_unmerged_branch_is_stalled(self) -> None:
        sessions = {session["id"]: session for session in self.report()["sessions"]}
        self.assertTrue(sessions["01a187bc"]["stalled"])
        self.assertEqual(sessions["01a187bc"]["reopen"], "agent:open codex:01a187bc")
        self.assertFalse(sessions["36c6da7d"]["stalled"])
        self.assertNotIn("reopen", sessions["36c6da7d"])

    def test_text_only_match_is_not_an_owner(self) -> None:
        sessions = {session["id"]: session for session in self.report()["sessions"]}
        self.assertFalse(sessions["f8af11f2"]["stalled"])

    def test_rejects_a_reference_of_the_wrong_kind(self) -> None:
        with self.assertRaisesRegex(ValueError, "pr reference"):
            CATCH_UP.parse("pr", ISSUE)


if __name__ == "__main__":
    unittest.main()
