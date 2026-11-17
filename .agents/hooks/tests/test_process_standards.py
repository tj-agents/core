import unittest
from pathlib import Path

from fixtures.lane_expectations import authored_skill


class ProcessStandardsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[3]

    def corpus(self):
        paths = [
            path
            for scope in ("base", "engineering", "workflow")
            for path in (self.root / ".agents" / scope).rglob("SKILL.md")
        ]
        return "\n".join(path.read_text(encoding="utf-8") for path in paths)

    def test_deprecated_checkpoint_ceremony_is_absent(self):
        corpus = self.corpus().lower()
        deprecated = (
            "checkpoint-transport protocol",
            "before any report or stop",
            "before every report",
            "before reporting plan-managed work",
            "first coherent checkpoint",
            "normal checkout as the one shared owner",
            "ledgers always stay in the normal checkout",
        )

        for phrase in deprecated:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, corpus)

    def test_plan_standard_owns_phase_gates_and_consumption_contracts(self):
        plans = " ".join(authored_skill("plans").read_text(encoding="utf-8").split())

        for phrase in (
            "every intermediate state builds and passes",
            "verification gate",
            "pins its consumption contract",
            "A plan holds unfinished work only",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, plans)
        for retired in ("verified pickup", "ownership release", "merge-docs", "roadmap"):
            with self.subTest(retired=retired):
                self.assertNotIn(retired, plans)

    def test_address_review_does_not_force_one_agent_context_per_finding(self):
        address = " ".join(authored_skill("address-review").read_text(encoding="utf-8").split())

        self.assertIn("Take one finding, or one tightly coupled group, at a time under a single writer", address)
        self.assertNotIn("own fresh agent context", address)
        self.assertNotIn("one finding per agent context", address)

    def test_address_review_serializes_every_fix(self):
        address = " ".join(authored_skill("address-review").read_text(encoding="utf-8").split())

        self.assertIn("Never run two writers at once, even on disjoint files", address)
        self.assertNotIn("concurrent fixes", address)

    def test_always_on_instructions_own_the_stage_pointer_rule(self):
        instructions = authored_skill("workflow:session").read_text(
            encoding="utf-8"
        )

        self.assertIn("## A link to another skill is a stage pointer, not a read", instructions)
        self.assertIn(
            "Load a referenced skill when its stage is actually entered, never because a document",
            instructions,
        )
        self.assertEqual(1, self.corpus().count("stage is actually entered"))

    def test_always_on_instructions_reconcile_known_problems_before_terminal_results(self):
        flat = " ".join(authored_skill("engineering:session").read_text(encoding="utf-8").split())

        self.assertIn(
            "Before returning a terminal result, check the work against the standards that governed it and "
            "reconcile every problem encountered: fixed, routed to an existing owner, or recorded through the "
            "selected profile",
            flat,
        )

    def test_callout_corrects_task_before_optional_standards_repair(self):
        def callout(skill):
            instructions = authored_skill(skill).read_text(encoding="utf-8")
            return " ".join(
                instructions.split("## When the user calls out a mistake", 1)[1].split("## ", 1)[0].split()
            )

        text = callout("workflow:session")
        self.assertTrue(text.startswith("Answer the direct question first"))
        self.assertIn("Audit the session for other mistakes only when reporting a terminal result", text)

    def test_sessions_message_each_other_only_for_blockers_or_awaited_results(self):
        session = " ".join(authored_skill("workflow:session").read_text(encoding="utf-8").split())

        self.assertIn(
            "Message another session only for a blocker it must act on or a final result it is waiting for",
            session,
        )

    def test_the_whole_requested_outcome_is_delivered_and_the_profile_decides_pr_count(self):
        run = " ".join(authored_skill("workflow:run").read_text(encoding="utf-8").split())
        session = " ".join(authored_skill("engineering:session").read_text(encoding="utf-8").split())

        self.assertIn("Deliver the whole requested outcome", run)
        self.assertIn("The selected profile, or the user, decides how many PRs the outcome uses", run)
        self.assertIn("Never split a cutover into broken intermediate states", run)
        self.assertIn("Phases, handoffs and briefs never narrow it, and a merged PR is not completion", session)

    def test_unattended_continuation_is_opt_in_and_routed_once(self):
        remote = authored_skill("remote-validation").read_text(encoding="utf-8")
        shared = (self.root / ".agents/workflow/workflow/continue/references/delivery.md").read_text(encoding="utf-8")
        workflow = authored_skill("workflow:continue").read_text(encoding="utf-8")
        claude = (self.root / ".claude/skills/workflow/continue/SKILL.md").read_text(encoding="utf-8")
        codex = (self.root / ".codex/skills/workflow/continue/SKILL.md").read_text(encoding="utf-8")
        delivery = (self.root / ".codex/runtime/continuation/README.md").read_text(encoding="utf-8")

        self.assertIn("`workflow:continue` owns the wait only when the user asks for unattended progress", " ".join(remote.split()))
        self.assertIn("It is the only route to the Codex CLI continuation runtime", " ".join(workflow.split()))
        self.assertIn("Keep one background monitor per binding", shared)
        self.assertIn("A merged PR returns to `workflow:run`", " ".join(shared.split()))
        self.assertIn("init --root ROOT --goal GOALPATH", delivery)
        self.assertIn("CONTINUATION_RESULT_PATH", delivery)
        self.assertIn("900-second child timeout", delivery)
        self.assertIn("fresh headless `codex exec` context", " ".join(delivery.split()))
        self.assertIn("delivery_continuation.py", delivery)
        self.assertIn("`/goal`", claude)
        self.assertIn("`/loop`", claude)
        self.assertNotIn("continuation_runtime.py", claude)
        self.assertNotIn("delivery_continuation.py", claude)
        self.assertIn("Scheduled interface", codex)
        self.assertNotIn("Claude uses", remote)
        self.assertNotIn("Codex Desktop uses", remote)
        self.assertNotEqual(claude, codex)
        for identity in ("merge", "merging"):
            with self.subTest(identity=identity):
                body = " ".join(authored_skill(identity).read_text(encoding="utf-8").split())
                self.assertIn(
                    "Load `workflow:continue` and its delivery reference only when the user asks for unattended progress",
                    body,
                )

    def test_merge_runs_on_the_reviewed_head_under_the_repository_rulesets(self):
        merge = authored_skill("merge").read_text(encoding="utf-8")
        merging = authored_skill("merging").read_text(encoding="utf-8")

        self.assertLess(len(merging.encode("utf-8")), 3072)
        for body in (merge, merging):
            with self.subTest(body=body[:40]):
                self.assertIn("--auto --squash --match-head-commit", body)
                self.assertIn("GitHub rulesets are the merge gate", " ".join(body.split()))
        self.assertIn("never retry or toggle a genuine failure", " ".join(merge.split()))
        self.assertIn("Never retry or toggle a genuine failure", merging)
        self.assertIn("`workflow:run` owns the user's authority", " ".join(merging.split()))
        corpus = " ".join(self.corpus().split())
        self.assertEqual(1, corpus.count("## Authority and acceptance"))
        for retired in ("delivery-authorization", "authorized_stop_classes", "auto_merge.py", "merge queue"):
            with self.subTest(retired=retired):
                self.assertNotIn(retired, corpus)

    def test_address_debt_picks_fast_in_the_current_or_child_repository(self):
        flat = " ".join(authored_skill("address-debt").read_text(encoding="utf-8").split())

        self.assertIn("Work in the current repository", flat)
        self.assertIn("survey their debt as one list; the picked item's repository then owns the run", flat)
        self.assertIn("List titles and severity in one pass", flat)
        self.assertIn("Take the first genuinely high-value, self-contained item", flat)
        self.assertIn("the selected profile decides how many PRs", flat)

    def test_handoff_is_one_self_contained_prompt_launched_once(self):
        handoff = " ".join(authored_skill("handoff").read_text(encoding="utf-8").split())

        self.assertIn("One self-contained prompt", handoff)
        self.assertIn("It never narrows the requested outcome", handoff)
        self.assertIn("Checkpoint the canonical goal, then stop writing owned paths", handoff)
        self.assertIn("invoke the launcher once", handoff)
        self.assertIn("Never keep two writers on one checkout", handoff)
        self.assertIn("A prepared prompt alone is not a handoff", handoff)
        for retired in ("transfer.py", "acknowledge", "receipt"):
            with self.subTest(retired=retired):
                self.assertNotIn(retired, handoff)

    def test_review_uses_the_selected_standards_and_counts_identical_trees(self):
        flat = " ".join(authored_skill("review").read_text(encoding="utf-8").split())

        self.assertIn("`.agents/plugins.json` selection define the standards", flat)
        self.assertIn("A head whose tree equals an already-reviewed head's tree counts as reviewed", flat)
        lifecycle = " ".join(authored_skill("review-lifecycle").read_text(encoding="utf-8").split())
        self.assertIn("A review is one native review of the full base and head SHAs and the diff between them", lifecycle)
        for retired in ("bundle", "descriptor", "watermark", "work order"):
            with self.subTest(retired=retired):
                self.assertNotIn(retired, lifecycle)

    def test_merge_cleanup_runs_the_proving_worktree_sweep(self):
        flat = " ".join(authored_skill("merge").read_text(encoding="utf-8").split())

        for required in (
            "scripts/worktree_sweep.py --repo <primary-checkout>",
            "once cleanup_proof.py proves its PR merged at exactly its head",
            "a worktree with an active launch, a dependent open PR or a refused proof is kept and named",
            "Never force a removal the sweep refused",
        ):
            with self.subTest(required=required):
                self.assertIn(required, flat)
        for retired in ("finish.py", "close.py", "machine:close", "worktrees.ps1", "worktree remove --force"):
            with self.subTest(retired=retired):
                self.assertNotIn(retired, flat)

    def test_handoff_transfers_active_directory_removal_after_predecessor_release(self):
        handoff = " ".join(authored_skill("handoff").read_text(encoding="utf-8").split())
        cleanup = " ".join(authored_skill("merging").read_text(encoding="utf-8").split())

        self.assertIn("put `engineering:merging`'s transferred checkout cleanup in the successor's next action", handoff)
        self.assertIn("the predecessor does not perform it after launch", handoff)
        self.assertIn("only after the predecessor has stopped using it, then verifies the path is gone", cleanup)
        self.assertIn("A command error or residual path is incomplete cleanup", cleanup)




if __name__ == "__main__":
    unittest.main()
