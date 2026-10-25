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
            for scope in ("base", "engineering", "machine", "workflow")
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

    def test_checkpoint_standard_owns_material_transitions_and_single_push(self):
        checkpoint = " ".join(authored_skill("plans").read_text(encoding="utf-8").split())

        for phrase in (
            "material implementation milestone",
            "genuine blocker or ownership handoff",
            "completed full review or important finding",
            "terminal delivery transition",
            "unsafe context ending",
            "pushes once",
            "Do not create observation-only",
            "200 lines",
            "16,000 UTF-8 bytes",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, checkpoint)

    def test_staged_review_uses_its_own_resume_contract(self):
        staged = authored_skill("staged-review").read_text(
            encoding="utf-8"
        )

        self.assertIn("## rules manifest", staged.lower())
        self.assertIn("the canonical work order is the resume contract", staged.lower())
        self.assertNotRegex(staged.lower(), r"plan checkpoint[^\n]{0,120}(?:each|every) stage")

    def test_address_review_does_not_force_one_agent_context_per_finding(self):
        address = authored_skill("address-review").read_text(
            encoding="utf-8"
        )

        self.assertIn("Take one open finding or one tightly coupled group", address)
        self.assertNotIn("own fresh agent context", address)
        self.assertNotIn("Spawn exactly one fresh agent context", address)
        self.assertNotIn("one finding per agent context", address)

    def test_address_review_serializes_every_fix(self):
        address = authored_skill("address-review").read_text(
            encoding="utf-8"
        )

        self.assertIn("Never overlap\nwriters", address)
        self.assertIn("one exclusive writer", address)
        self.assertIn("even for disjoint files", address)
        self.assertNotIn("Serial by default", address)
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
        instructions = authored_skill("engineering:session").read_text(
            encoding="utf-8"
        )
        flat = " ".join(instructions.split())

        self.assertIn(
            "Before committing or returning a terminal result, check the work against the "
            "standards that governed it and reconcile every problem encountered: it is fixed, "
            "routed to an existing owner, recorded when authorized, or retained in the active task "
            "pending the profile's recording decision.",
            flat,
        )

    def test_standards_repair_requires_internal_source_authority(self):
        instructions = authored_skill("engineering:session").read_text(
            encoding="utf-8"
        )
        flat = " ".join(instructions.split())

        for phrase in (
            "A defect in a consumed agent standard or tool is diagnosed at its source",
            "Use `engineering:self-repair` to establish causal evidence and whether its internal repair authority applies",
            "outside automatic scope, explain the proposed repair and continue unaffected authorized work",
            "That workflow owns the repair authorization and delivery procedure",
            "explicit user limits still hold",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, flat)

        self_repair = " ".join(authored_skill("self-repair").read_text(encoding="utf-8").split())
        for phrase in (
            "Its owning source is an explicitly authorized `tj-agents` standards or tooling repository",
            "Both the originating task and the source repository have explicitly adopted personal scope",
            "`tj-agents/infonetica` is employer tooling and remains outside automatic repair",
            "Conclude with no standards change when no reusable source defect is established",
            "Reconcile that owner and contribute the evidence without creating a duplicate writer",
            "Fix the standard or tool in the current session",
            "Hand the repair off only when the user asks",
            "For an eligible automatic repair, standing authorization covers implementation, tests, review, pull "
            "request, merge and publication in that source repository once its gates pass",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self_repair)

    def test_callout_corrects_task_before_optional_standards_repair(self):
        def callout(skill):
            instructions = authored_skill(skill).read_text(encoding="utf-8")
            return " ".join(
                instructions.split("## When the user calls out a mistake", 1)[1].split("## ", 1)[0].split()
            )

        self.assertTrue(callout("workflow:session").startswith("Answer the direct question first"))
        section = callout("engineering:session")
        for phrase in (
            "`engineering:self-repair`",
            "source ownership, causal evidence and repair eligibility",
            "the automatic-repair boundary and the no-source-change outcome",
            "Existing user limits and scope gates still apply",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, section)

        self_repair = " ".join(authored_skill("self-repair").read_text(encoding="utf-8").split())
        for phrase in (
            "a demonstrated defect in a reusable agent standard, skill, route, hook or lifecycle tool",
            "An employer task does not grant automatic repair authority",
            "monitoring-only",
            "Monitoring does not grant delivery authority",
            "never authorizes taking over an unrelated pending delivery",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self_repair)

    def test_harness_specific_persistent_continuation_is_routed(self):
        remote = authored_skill("remote-validation").read_text(
            encoding="utf-8"
        )
        shared = authored_skill("persistent-delivery").read_text(
            encoding="utf-8"
        )
        workflow = authored_skill("persistent-workflow").read_text(encoding="utf-8")
        claude = (
            self.root / ".claude/skills/engineering/persistent-workflow/SKILL.md"
        ).read_text(encoding="utf-8")
        codex = (
            self.root / ".codex/skills/engineering/persistent-workflow/SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertIn("persistent-workflow skill", remote)
        self.assertIn("persistent-delivery", remote)
        self.assertIn("one persistent owner for a PR/head pair", shared)
        self.assertIn("init --root ROOT --goal GOALPATH", workflow)
        self.assertIn("CONTINUATION_RESULT_PATH", workflow)
        self.assertIn("900-second child timeout", workflow)
        self.assertIn("Missing merge authorization gates merge only", shared)
        self.assertIn("Claude `/goal`, `/loop`, monitors, channels", claude)
        self.assertIn("fresh `claude -p` context", claude)
        self.assertIn(
            "Scheduled Task attached to the owning Codex conversation",
            codex,
        )
        self.assertIn("fresh headless `codex exec` context", codex)
        self.assertIn("delivery_continuation.py", codex)
        self.assertNotIn("Claude uses", remote)
        self.assertNotIn("Codex Desktop uses", remote)
        for skill in ("e2e-debug", "e2e-api-debug", "e2e-ui-debug", "integration-debug"):
            with self.subTest(skill=skill):
                self.assertIn(skill, shared)
        self.assertNotEqual(claude, codex)

        merge = authored_skill("merge").read_text(encoding="utf-8")
        merging = authored_skill("merging").read_text(encoding="utf-8")
        for body in (merge, merging):
            with self.subTest(policy="merge-debug-dispatch"):
                self.assertIn("immediately dispatch one fresh", body)
                self.assertIn("foreground fallback", body)
        self.assertIn("exact run head", merging)
        self.assertIn("bound PR source head", merging)

    def test_merge_authorization_is_goal_scoped_with_one_owner(self):
        merging = authored_skill("merging").read_text(encoding="utf-8")
        flat_merging = " ".join(merging.split())
        corpus = " ".join(self.corpus().split())

        self.assertIn("## What authorizes a merge", merging)
        self.assertIn("Merge authorization is scoped to the goal, not the PR", flat_merging)
        self.assertIn(
            "merge authorization for every PR that goal itself creates", flat_merging
        )
        self.assertIn("no per-PR re-approval", flat_merging)
        self.assertIn(
            "no delivery standard adds a per-PR approval requirement", flat_merging
        )
        self.assertEqual(
            1, corpus.count("Merge authorization is scoped to the goal, not the PR")
        )

        bodies = {
            name: " ".join(authored_skill(name).read_text(encoding="utf-8").split())
            for name in (
                "persistent-delivery",
                "merge",
                "plans",
                "feature",
                "bugfix",
            )
        }
        self.assertIn(
            "an authorization naming no mode records `auto`",
            bodies["persistent-delivery"],
        )
        for referrer, pointer in (
            (
                "persistent-delivery",
                "the owning goal record (`engineering:merging` owns that goal-wide scope)",
            ),
            (
                "merge",
                "re-resolves merge authorization from the goal's recorded "
                "authorization (`engineering:merging`)",
            ),
            (
                "plans",
                "default-branch state (`engineering:merging` owns the goal-wide "
                "merge-authorization scope)",
            ),
            (
                "feature",
                "covers delivery (`engineering:merging` owns that goal-wide scope)",
            ),
            (
                "bugfix",
                "covers delivery (`engineering:merging` owns that goal-wide scope)",
            ),
        ):
            with self.subTest(referrer=referrer):
                self.assertIn(pointer, bodies[referrer])

        for per_pr_reading in (
            "implementation approval never invents merge authority",
            "reaches merge only under explicit authorization",
            "never silently authorizes the successor",
            "merge authorization into the successor",
            "adds no authority for installation, publication, merging",
        ):
            with self.subTest(per_pr_reading=per_pr_reading):
                self.assertNotIn(per_pr_reading, corpus)

    def test_address_debt_uses_mode_specific_isolation_and_picks_fast(self):
        body = authored_skill("address-debt").read_text(encoding="utf-8")
        flat = " ".join(body.split())

        self.assertIn("Single-repo mode:** survey the repository", flat)
        self.assertIn("Select or reuse an available checkout under `engineering:branching`", flat)
        self.assertIn("Polyrepo-root mode:** run Step 2's survey across every child repo", flat)
        self.assertIn("Once the primary item is selected, its child repo owns this run", flat)
        self.assertIn("Pick the item(s) fast", flat)
        self.assertIn("do not read each entry in full", flat)
        self.assertIn("the bundling test below is applied after that pick", flat)
        self.assertNotIn("Survey every `TECH_DEBT.md` in the repo, then choose", flat)

    def test_ownership_or_repository_change_selects_a_real_handoff(self):
        plans = " ".join(authored_skill("plans").read_text(encoding="utf-8").split())
        handoff = " ".join(
            authored_skill("handoff").read_text(encoding="utf-8").split()
        )

        self.assertIn("changes owner, repository, worktree, PR, or logical workstream", plans)
        self.assertIn("execute the `handoff` workflow", plans)
        self.assertIn("a pointer in the response alone does not transfer ownership", plans)
        self.assertIn("It prepares the exact `workflow:handoff` pointer", plans)
        self.assertIn("Stop owned-path writes before invoking the launcher", handoff)
        self.assertIn("Preparing a pointer alone does not complete a handoff", handoff)
    def test_planning_to_execution_uses_scale_and_context(self):
        lanes = " ".join(authored_skill("lanes").read_text(encoding="utf-8").split())
        plans = " ".join(authored_skill("plans").read_text(encoding="utf-8").split())
        execution = plans
        self.assertIn("Lane selection never transfers task ownership", lanes)
        self.assertIn("On either host the parent does its own work in the same checkout", lanes)
        self.assertIn("explicit path and responsibility ownership", lanes)
        self.assertIn("A small follow-up can stay with the parent", lanes)
        self.assertIn("If delegation is unavailable", lanes)
        self.assertIn("Continue in the current context by default for small and medium plans", plans)
        self.assertIn("The parent retains ownership", plans)
        self.assertIn("massive plan whose design was a substantial phase", plans)
        self.assertIn("normally hand execution to one fresh harness", plans)
        self.assertIn("even when the checkout stays the same", plans)
        self.assertIn("Judge plans between these cases", plans)
        self.assertIn("plan length alone is not a mechanical threshold", plans)
        self.assertIn("changes owner, repository, worktree, PR, or logical workstream", plans)
        self.assertIn("Do not select a handoff as routine phase-ending ceremony", execution)
        self.assertIn("a massive plan has completed substantial design", execution)

        for host in ("codex", "claude"):
            with self.subTest(host=host):
                launcher = (
                    self.root / f".agents/machine/utility/handoff-{host}/SKILL.md"
                ).read_text(encoding="utf-8")
                flat_launcher = " ".join(launcher.split())
                self.assertNotIn("After a small or medium plan", flat_launcher)
                self.assertNotIn("After a massive plan", flat_launcher)
                self.assertNotIn("engineering:plans", launcher)
                self.assertNotIn("Split a job that designs and then delivers", launcher)

    def test_side_handoff_submission_keeps_the_parent_executing(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                launcher = (
                    self.root / f".agents/machine/utility/handoff-{host}/SKILL.md"
                ).read_text(encoding="utf-8")
                flat_launcher = " ".join(launcher.split())
                self.assertIn("bounded side-workstream handoff", flat_launcher)
                self.assertIn("retain the originating goal and foreground writer lease", flat_launcher)
                self.assertIn("continue its next action in the same turn", flat_launcher)
                self.assertIn("does not satisfy the originating goal's completion condition", flat_launcher)
                self.assertIn("Accept an already authorized prepared dispatch", flat_launcher)
                self.assertIn("The caller owns the checkpoint, release and pickup rules", flat_launcher)
                self.assertIn("successful submission is not pickup", flat_launcher)
                self.assertNotIn("engineering:handoff", launcher)
                self.assertNotIn("the handoff happened. Report it and stop.", launcher)

    def test_plan_artifacts_always_reach_merged_default_branch(self):
        plans = authored_skill("plans").read_text(encoding="utf-8")
        flat = " ".join(plans.split())

        self.assertIn("## Planning artifacts always land", plans)
        self.assertIn("## Roadmap → plan → progress", plans)
        self.assertIn("## Implementation examples and their standards", plans)
        self.assertIn("planning-only or meta-only slice lands through `merge-docs`", flat)
        self.assertIn("Location alone never makes a restriction stale", plans)
        for live_gate in (
            "explicit current user limitation",
            "recorded repository authorization",
            "named PR/head security or validation hold",
            "merge hold",
            "repository stop class",
        ):
            with self.subTest(live_gate=live_gate):
                self.assertIn(live_gate, flat)
        self.assertIn("Planning-only work is terminal only when its", flat)
        self.assertIn("implementation are terminal only when that delivery PR merges", flat)

    def test_review_keeps_injected_scope_and_rechecks_rule_identities(self):
        body = authored_skill("review").read_text(encoding="utf-8")
        flat = " ".join(body.split())

        self.assertIn("reads `.agents/plugins.json`", flat)
        self.assertIn("only when its recorded hash is unchanged", flat)
        self.assertIn("changed or missing hash requires a new body read", flat)

    def test_merge_docs_keeps_an_existing_isolated_branch(self):
        body = authored_skill("merge-docs").read_text(
            encoding="utf-8"
        )
        flat = " ".join(body.split())

        self.assertIn(
            "do not create a second branch solely to change the type prefix to `Docs`", flat
        )

    def test_merge_cleanup_runs_the_proving_worktree_sweep(self):
        body = authored_skill("merge").read_text(encoding="utf-8")
        cleanup = body.split(
            "### 5. Return to a clean base and retire any isolated checkout",
            maxsplit=1,
        )[1].split("### 6. Follow the publish", maxsplit=1)[0]
        flat = " ".join(cleanup.split())

        for required in (
            "never remove that path",
            "scripts/worktree_sweep.py --repo <primary-checkout>",
            "`cleanup_proof.py` proves its PR merged at exactly its head",
            "archiving any leftovers under `<state>/merge-cleanup/set-aside/` first",
            "while a registered session still works inside it",
            "while an open PR is based on its branch",
            "removed by the sweep that runs once the session closes",
            "never force a removal",
        ):
            with self.subTest(required=required):
                self.assertIn(required, flat)

        for retired in ("finish.py", "close.py", "machine:close", "worktrees.ps1", "worktree remove --force"):
            with self.subTest(retired=retired):
                self.assertNotIn(retired, cleanup)

    def test_cd_and_handoff_transfer_active_directory_removal_to_the_successor(self):
        cd = " ".join(authored_skill("cd").read_text(encoding="utf-8").split())
        handoff = " ".join(authored_skill("handoff").read_text(encoding="utf-8").split())
        cleanup = " ".join(authored_skill("merging").read_text(encoding="utf-8").split())

        self.assertIn("Retarget the host **before** any helper or native command", cd)
        self.assertIn(
            "the successor the sole owner of the removal and final filesystem verification",
            cd,
        )
        self.assertIn(
            "the original stops repository-scoped work; a completed delivery closes its own session "
            "through `engineering:merge` Step 5's `finish`; only when that is unavailable does the "
            "`handoff` successor own the removal, closing the predecessor through `machine:peer-cli`",
            cd,
        )
        self.assertIn("follow `engineering:merging` under Transferred checkout cleanup", handoff)
        self.assertIn(
            "Put the exact operation and final filesystem verification in the successor's `## Next Steps`",
            handoff,
        )
        self.assertIn("The predecessor must not perform it after launch", handoff)
        self.assertIn("a command error or residual path as incomplete", cleanup)




if __name__ == "__main__":
    unittest.main()
