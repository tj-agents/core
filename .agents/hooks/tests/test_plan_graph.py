import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plan_graph import (
    LEDGER_MAX_BYTES,
    LEDGER_MAX_LINES,
    is_paused,
    ledger_errors,
    next_steps,
    plan_path,
    repository_report,
)


SCENARIOS = Path(__file__).resolve().parent / "fixtures" / "workflow_efficiency_scenarios.json"


class PlanGraphTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.epic = self.root / "plans" / "epic"
        self.epic.mkdir(parents=True)
        self.plan = self.epic / "SHARED_PLAN.md"
        self.plan.write_text("# Plan\n", encoding="utf-8")
        self.roadmap = self.epic / "EPIC_ROADMAP.md"
        self.roadmap.write_text(
            "# Roadmap\n\n- [ ] **Build the graph** `epic/graph`\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def write_ledger(self, name="WORKTREE_A_PROGRESS.md", next_steps="Open the PR.", extra=""):
        ledger = self.epic / name
        ledger.write_text(
            "\n".join(
                [
                    "# Progress",
                    "",
                    "- Plan: `plans/epic/SHARED_PLAN.md`",
                    "- Roadmap: `plans/epic/EPIC_ROADMAP.md`",
                    "- Roadmap item: `epic/graph`",
                    f"- Worktree: `{self.root}`",
                    "- Branch: `Feature/epic_graph`",
                    "",
                    "## Next Steps",
                    "",
                    next_steps,
                    "Scope: current slice only; full plan remains incomplete.",
                    "Current slice: complete the next action above.",
                    "Remaining scope: later phases and terminal delivery remain.",
                    "Done when: this slice is green; the full plan remains open.",
                    "",
                    extra,
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return ledger

    def test_declared_plan_is_authoritative_for_differently_named_ledger(self):
        ledger = self.write_ledger()

        self.assertEqual(self.plan, plan_path(ledger))
        self.assertEqual([], ledger_errors(ledger))

    def test_unselected_plan_does_not_block_unrelated_repository_work(self):
        self.plan.write_text(
            "# Plan\n\nRetain the legacy reader through a compatibility window.\n",
            encoding="utf-8",
        )

        self.assertEqual([], repository_report(self.root)["errors"])

    def test_roadmap_item_must_have_a_stable_checklist_marker(self):
        ledger = self.write_ledger()
        self.roadmap.write_text("Roadmap prose mentions `epic/graph`.\n", encoding="utf-8")

        errors = ledger_errors(ledger)

        self.assertEqual(1, len(errors))
        self.assertIn("roadmap item marker", errors[0])

    def test_roadmap_item_accepts_a_status_table_row(self):
        ledger = self.write_ledger()
        self.roadmap.write_text(
            "| Status | Key | Item |\n"
            "|---|---|---|\n"
            "| [ ] | `epic/graph` | Build the graph |\n",
            encoding="utf-8",
        )

        self.assertEqual([], ledger_errors(ledger))

    def test_roadmap_item_key_must_match_the_epic(self):
        ledger = self.write_ledger()
        ledger.write_text(
            ledger.read_text(encoding="utf-8").replace("epic/graph", "other/graph"),
            encoding="utf-8",
        )

        errors = ledger_errors(ledger)

        self.assertEqual(1, len(errors))
        self.assertIn("must match `epic/<slug>`", errors[0])

    def test_missing_reciprocal_owner_handoff_is_rejected(self):
        owner = self.write_ledger("OWNER_PROGRESS.md")
        waiting = self.write_ledger(
            "WAITING_PROGRESS.md",
            "Blocked: The owner has not published.\n"
            "Blocked by: plans/epic/OWNER_PROGRESS.md.\n"
            "Unblock action: Publish the owner package.\n"
            "Resume when: The package restores from the feed.",
        )

        errors = ledger_errors(waiting, live_owners=False)

        self.assertTrue(owner.is_file())
        self.assertEqual(1, len(errors))
        self.assertIn("must list plans/epic/WAITING_PROGRESS.md", errors[0])

    def test_reciprocal_owner_handoff_registers_the_wait(self):
        self.write_ledger(
            "OWNER_PROGRESS.md",
            extra="## Downstream handoffs\n\n- `plans/epic/WAITING_PROGRESS.md`",
        )
        waiting = self.write_ledger(
            "WAITING_PROGRESS.md",
            "Blocked: The owner has not published.\n"
            "Blocked by: plans/epic/OWNER_PROGRESS.md.\n"
            "Unblock action: Publish the owner package.\n"
            "Resume when: The package restores from the feed.",
        )

        self.assertEqual([], ledger_errors(waiting, live_owners=False))

    def test_one_roadmap_item_cannot_have_multiple_plan_owners(self):
        self.write_ledger()
        second_plan = self.epic / "SECOND_PLAN.md"
        second_plan.write_text("# Second\n", encoding="utf-8")
        second = self.write_ledger("SECOND_PROGRESS.md")
        second.write_text(
            second.read_text(encoding="utf-8").replace("SHARED_PLAN.md", "SECOND_PLAN.md"),
            encoding="utf-8",
        )

        report = repository_report(self.root)

        self.assertEqual(1, len(report["errors"]))
        self.assertIn("multiple plan owners", report["errors"][0])

    def test_non_plan_owner_does_not_require_reciprocal_ledger(self):
        ledger = self.write_ledger(
            next_steps=(
                "Blocked: Production credentials are unavailable.\n"
                "Blocked by: Tommy.\n"
                "Unblock action: Tommy supplies the production credentials.\n"
                "Resume when: The credentials authenticate successfully."
            )
        )

        self.assertEqual([], ledger_errors(ledger))

    def test_terminal_owner_cannot_retain_pending_handoff(self):
        ledger = self.write_ledger(
            next_steps="Complete.",
            extra="## Downstream handoffs\n\n- `plans/epic/WAITING_PROGRESS.md`",
        )

        errors = ledger_errors(ledger)

        self.assertEqual(1, len(errors))
        self.assertIn("terminal ledger still has undispatched", errors[0])

    def test_paused_state_is_recognized_and_valid(self):
        ledger = self.write_ledger(
            next_steps="Paused: awaiting Tommy's go-ahead on the launch copy before publishing."
        )

        self.assertTrue(is_paused(next_steps(ledger.read_text(encoding="utf-8"))))
        self.assertEqual([], ledger_errors(ledger))

    def test_active_and_blocked_states_are_not_paused(self):
        self.assertFalse(is_paused("Open the PR."))
        self.assertFalse(
            is_paused(
                "Blocked: PR #1 has not merged.\n"
                "Blocked by: GitHub PR #1.\n"
                "Unblock action: The owner merges it.\n"
                "Resume when: GitHub reports it merged."
            )
        )

    def test_merge_before_review_is_flagged(self):
        ledger = self.write_ledger(
            next_steps="1. Open the PR.\n2. `/merge` with full E2E, then follow the platform-sync PR."
        )

        errors = ledger_errors(ledger)

        self.assertEqual(1, len(errors))
        self.assertIn("pre-merge gate", errors[0])

    def test_review_sequenced_before_merge_passes(self):
        ledger = self.write_ledger(
            next_steps="1. Run `/review`; address findings.\n2. `/merge` on go-ahead, then platform-sync."
        )

        self.assertEqual([], ledger_errors(ledger))

    def test_merge_with_recorded_review_passes(self):
        ledger = self.write_ledger(
            next_steps="Merge on Tommy's go-ahead, then follow the platform-sync PR to green.",
            extra="## Reviews\n\n- Reviewed `abc1234..def5678`, no open findings.",
        )

        self.assertEqual([], ledger_errors(ledger))

    def test_merge_origin_main_is_a_branch_sync_not_a_pr_merge(self):
        ledger = self.write_ledger(
            next_steps="Merge origin/main, rebuild the affected projects to 0 errors, then push."
        )

        self.assertEqual([], ledger_errors(ledger))

    def test_merge_with_watermark_review_evidence_passes(self):
        ledger = self.write_ledger(
            next_steps="After CI is green, re-enqueue with full-e2e; merge only after the queue E2E passes.",
            extra="- Review and security watermark: `abc1234`; no open findings.",
        )

        self.assertEqual([], ledger_errors(ledger))

    def test_paused_awaiting_merge_without_review_is_flagged(self):
        ledger = self.write_ledger(
            next_steps="Paused: awaiting Tommy — say `merge 42` to release the merge."
        )

        errors = ledger_errors(ledger)

        self.assertEqual(1, len(errors))
        self.assertIn("pre-merge gate", errors[0])

    def test_blocker_mentioning_owner_merge_is_not_gated(self):
        ledger = self.write_ledger(
            next_steps=(
                "Blocked: the owner package is not on the feed.\n"
                "Blocked by: plans/epic/OWNER_PROGRESS.md.\n"
                "Unblock action: the owner at `plans/epic/OWNER_PROGRESS.md` must merge it.\n"
                "Resume when: the feed restores the package."
            ),
        )
        owner = self.write_ledger(
            "OWNER_PROGRESS.md",
            extra="## Downstream handoffs\n\n- `plans/epic/WORKTREE_A_PROGRESS.md`",
        )

        errors = ledger_errors(ledger, live_owners=False)

        self.assertTrue(owner.is_file())
        self.assertNotIn("pre-merge gate", " ".join(errors))

    def test_legacy_graph_metadata_is_rejected(self):
        legacy_plan = self.epic / "LEGACY_PLAN.md"
        legacy_plan.write_text("# Legacy\n", encoding="utf-8")
        legacy = self.epic / "LEGACY_PROGRESS.md"
        legacy.write_text("## Next Steps\n\nOpen the PR.\n", encoding="utf-8")

        report = repository_report(self.root)

        self.assertEqual(3, len(report["errors"]))
        self.assertEqual([], report["warnings"])

    def test_phase_only_scope_exposes_that_the_full_plan_remains_incomplete(self):
        scenario = json.loads(SCENARIOS.read_text(encoding="utf-8"))["phase_only_execution"]
        ledger = self.write_ledger(next_steps=scenario["current_slice"])
        body = next_steps(ledger.read_text(encoding="utf-8"))
        self.assertIn("full plan remains incomplete", body)
        self.assertIn("Remaining scope:", body)
        self.assertIn("Done when:", body)
        self.assertEqual([], ledger_errors(ledger))

    def test_oversized_ledger_emits_compaction_warning(self):
        self.write_ledger(extra="\n".join(f"- evidence {index}" for index in range(LEDGER_MAX_LINES)))

        report = repository_report(self.root)

        self.assertEqual([], report["errors"])
        self.assertEqual(1, len(report["warnings"]))
        self.assertIn("compact the current snapshot", report["warnings"][0])
        self.assertIn(f"{LEDGER_MAX_LINES}-line/{LEDGER_MAX_BYTES}-byte", report["warnings"][0])

    def test_compact_ledger_stays_below_continuation_budget(self):
        self.write_ledger(extra="## Evidence\n\n- PR #123 at `abc1234`; targeted checks green.")

        report = repository_report(self.root)

        self.assertEqual([], report["warnings"])


if __name__ == "__main__":
    unittest.main()
