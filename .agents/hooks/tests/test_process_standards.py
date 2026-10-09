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
            for scope in ("base", "engineering", "machine")
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
        checkpoint = authored_skill("plan-checkpoint").read_text(
            encoding="utf-8"
        )

        for phrase in (
            "material implementation milestone",
            "genuine blocker",
            "a full review completes",
            "delivery, merge, publication, or final closeout crosses a terminal boundary",
            "current context is ending with partial state",
            "A plan-managed push has one leg",
            "Never create or push an\nobservation-only",
            "200 lines",
            "16,000 UTF-8 bytes",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, checkpoint)

    def test_staged_review_uses_its_own_resume_contract(self):
        staged = authored_skill("big-review").read_text(
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
        instructions = authored_skill("session-guidance").read_text(
            encoding="utf-8"
        )

        self.assertIn("## A link to another skill is a stage pointer, not a read", instructions)
        self.assertIn(
            "Load a referenced skill when its stage is actually entered, never because a document",
            instructions,
        )
        self.assertEqual(1, self.corpus().count("stage is actually entered"))

    def test_always_on_instructions_reconcile_known_problems_before_terminal_results(self):
        instructions = authored_skill("session-guidance").read_text(
            encoding="utf-8"
        )
        flat = " ".join(instructions.split())

        self.assertIn(
            "Before committing or returning a terminal result, check the work against the "
            "standards that governed it and reconcile every problem encountered: it is fixed, "
            "handed off, or already has the owning debt entry, landed or landing with this change",
            flat,
        )

    def test_a_standards_defect_hands_off_in_the_same_turn(self):
        instructions = authored_skill("session-guidance").read_text(
            encoding="utf-8"
        )
        flat = " ".join(instructions.split())

        for phrase in (
            "A defect in a consumed standards package or its source repository is the exception: "
            "a stale or broken standard",
            "and so is a standard that caused or failed to prevent a mistake",
            "in the same turn, after answering the user's direct question and before the current task resumes, without asking",
            "announcing a later or separate fix instead of launching is a violation",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, flat)

    def test_callout_checks_standards_before_an_apology(self):
        instructions = authored_skill("session-guidance").read_text(encoding="utf-8")
        section = " ".join(
            instructions.split("## When the user calls out a mistake", 1)[1].split("## ", 1)[0].split()
        )

        self.assertTrue(section.startswith("When the user calls out a mistake, before apologizing"))
        self.assertLess(section.index("before apologizing"), section.index("An apology"))
        self.assertLess(section.index("Answer the user's direct question first"), section.index("If it did, launch"))
        for phrase in (
            "missing, ambiguous, contradictory, mispriced or unenforced",
            "every consumed `tj-agents` plugin on both hosts",
            "`engineering:handoff` in bounded side-workstream mode in the same turn",
            "SendFeedback draft or local memory does not substitute",
            "Existing user limits and scope gates still apply",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, section)

    def test_plan_execution_reads_the_plan_corpus_only_when_it_changes_a_decision(self):
        body = authored_skill("plan-execution").read_text(
            encoding="utf-8"
        )
        flat = " ".join(body.split())

        self.assertIn(
            "in exactly three cases: selecting ownership for the first time in this "
            "context, evidence that is missing or self-contradictory, and writing or "
            "reconciling a material checkpoint",
            flat,
        )
        self.assertIn(
            "### Resume a preserved continuation without re-reading the corpus", body
        )
        self.assertIn(
            "trustworthy when it names all five of the plan identity, the absolute "
            "worktree, the branch, the current state, and the single next action",
            flat,
        )
        self.assertIn("it does not relax the worktree identity check", flat)
        self.assertIn(
            "Do not re-read the plan, the ledger, `plans` or `plan-checkpoint`",
            flat,
        )
        self.assertNotIn("Read the repository instructions, [`plans`]", body)

    def test_harness_specific_persistent_continuation_is_routed(self):
        remote = authored_skill("remote-validation").read_text(
            encoding="utf-8"
        )
        shared = authored_skill("persistent-delivery").read_text(
            encoding="utf-8"
        )
        workflow = authored_skill("persistent-workflow").read_text(encoding="utf-8")
        claude = (
            self.root / ".claude/skills/persistent-workflow/SKILL.md"
        ).read_text(encoding="utf-8")
        codex = (
            self.root / ".codex/skills/persistent-workflow/SKILL.md"
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
        self.assertIn("delivery-continuation.ps1", codex)
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
                "plan-execution",
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
                "plan-execution",
                "default-branch state (`engineering:merging` owns the goal-wide "
                "merge-authorization scope)",
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

    def test_techdebt_uses_mode_specific_isolation_and_picks_fast(self):
        body = authored_skill("techdebt").read_text(encoding="utf-8")
        flat = " ".join(body.split())

        self.assertIn("Single-repo mode:** survey the repository", flat)
        self.assertIn("Select or reuse an available checkout under `engineering:git-branching`", flat)
        self.assertIn("Polyrepo-root mode:** run Step 2's survey across every child repo", flat)
        self.assertIn("Once the primary item is selected, its child repo owns this run", flat)
        self.assertIn("Pick the item(s) fast", flat)
        self.assertIn("do not read each entry in full", flat)
        self.assertIn("the bundling test below is applied after that pick", flat)
        self.assertNotIn("Survey every `TECH_DEBT.md` in the repo, then choose", flat)

    def test_plan_execution_resumes_into_owned_partial_work(self):
        body = authored_skill("plan-execution").read_text(
            encoding="utf-8"
        )
        flat = " ".join(body.split())

        self.assertIn(
            "A restored worktree that is dirty is not by itself a reason to stop", flat
        )
        self.assertIn("that is partial implementation to resume", flat)
        self.assertIn(
            "Stop only when the dirty state is conflicting, unexplained, unowned, or unsafe",
            flat,
        )

    def test_ownership_or_repository_change_selects_a_real_handoff(self):
        plans = " ".join(authored_skill("plans").read_text(encoding="utf-8").split())
        execution = " ".join(
            authored_skill("plan-execution").read_text(encoding="utf-8").split()
        )
        formatting = " ".join(
            authored_skill("handoff-format").read_text(encoding="utf-8").split()
        )

        self.assertIn("changes owner, repository, worktree, PR, or logical workstream", plans)
        self.assertIn("execute the `handoff` workflow", plans)
        self.assertIn("a pointer in the response alone does not transfer ownership", plans)
        self.assertIn("execute `engineering:handoff`", execution)
        self.assertIn("invokes one selected launcher before this context releases ownership", execution)
        self.assertIn("It does not select or perform a transfer", formatting)
        self.assertIn("`engineering:handoff` performs the selected transfer", formatting)

    def test_planning_to_execution_uses_scale_and_context(self):
        lanes = " ".join(authored_skill("lanes").read_text(encoding="utf-8").split())
        plans = " ".join(authored_skill("plans").read_text(encoding="utf-8").split())
        execution = " ".join(
            authored_skill("plan-execution").read_text(encoding="utf-8").split()
        )
        self.assertIn("Lane selection does not itself transfer task ownership", lanes)
        self.assertIn("For Codex, the parent normally continues in the same checkout", lanes)
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
        self.assertIn("Do not transfer merely because a phase or commit completed", execution)
        self.assertIn("A massive plan whose substantial design phase", execution)

        for host in ("codex", "claude"):
            with self.subTest(host=host):
                launcher = (
                    self.root / f".agents/machine/utility/handoff-{host}/SKILL.md"
                ).read_text(encoding="utf-8")
                flat_launcher = " ".join(launcher.split())
                self.assertIn("After a small or medium plan", flat_launcher)
                self.assertIn("planning alone does not call for this launcher", flat_launcher)
                self.assertIn("After a massive plan", flat_launcher)
                self.assertIn("normally transfers execution to one fresh harness", flat_launcher)
                self.assertIn("even in the same checkout", flat_launcher)
                self.assertNotIn("Split a job that designs and then delivers", launcher)

    def test_plan_artifacts_always_reach_merged_default_branch(self):
        plans = authored_skill("plans").read_text(encoding="utf-8")
        authoring = authored_skill("plan-authoring").read_text(
            encoding="utf-8"
        )
        execution = authored_skill("plan-execution").read_text(
            encoding="utf-8"
        )

        self.assertIn("## Planning artifacts always land", plans)
        self.assertIn("## Roadmap → plan → progress", plans)
        self.assertIn("## Implementation examples and their standards", plans)
        self.assertIn(
            "planning-only or meta-only slice lands through `merge-docs`",
            " ".join(plans.split()),
        )
        self.assertIn("Location alone never makes a restriction stale", plans)
        for live_gate in (
            "explicit current user limitation",
            "recorded repository authorization",
            "named PR/head security or validation hold",
            "merge hold",
            "repository stop class",
        ):
            with self.subTest(live_gate=live_gate):
                self.assertIn(live_gate, " ".join(plans.split()))
        self.assertIn("land through `merge-docs`", " ".join(authoring.split()))
        self.assertIn(
            "Planning-only work carries standing authorization",
            " ".join(authoring.split()),
        )
        self.assertIn(
            "A live delivery restriction overrides that standing authorization",
            " ".join(authoring.split()),
        )
        for live_gate in (
            "explicit current user limitation",
            "repository authorization",
            "security or validation hold",
            "merge hold",
            "stop class",
        ):
            with self.subTest(authoring_live_gate=live_gate):
                self.assertIn(live_gate, " ".join(authoring.split()))
        self.assertIn(
            "only after the design artifact and any owning ledger are merged to the default branch",
            " ".join(authoring.split()),
        )
        self.assertIn(
            "Planning-artifact publication remains part of the authorized plan lifecycle",
            " ".join(execution.split()),
        )
        self.assertIn(
            "Deliver a meta-only slice through `engineering:merge-docs`; "
            "deliver any slice containing runtime, product, package, schema, deployment, "
            "or test-selection changes through `engineering:merge`",
            " ".join(execution.split()),
        )
        self.assertNotIn("delivering each completed slice through [`merge`]", execution)
        self.assertIn("including a planning-only slice", " ".join(execution.split()))

    def test_review_rechecks_routed_rules_instead_of_citing_an_earlier_read(self):
        body = authored_skill("review").read_text(encoding="utf-8")
        flat = " ".join(body.split())

        self.assertIn("Read only identities returned as `load`", flat)
        self.assertIn("an unchanged identity returned as `cached`", flat)
        self.assertIn("changed or missing hash requires a new body read", flat)

    def test_merge_docs_keeps_an_existing_isolated_branch(self):
        body = authored_skill("merge-docs").read_text(
            encoding="utf-8"
        )
        flat = " ".join(body.split())

        self.assertIn(
            "do not create a second branch solely to change the type prefix to `Docs`", flat
        )

    def test_merge_requires_safe_cleanup_when_the_repository_helper_is_absent(self):
        body = authored_skill("merge").read_text(encoding="utf-8")
        cleanup = body.split(
            "### 5. Return to a clean base and retire any isolated checkout",
            maxsplit=1,
        )[1].split("### 6. Follow the publish", maxsplit=1)[0]
        flat = " ".join(cleanup.split())

        for required in (
            "Join-Path <primary-checkout> 'scripts/worktrees.ps1'",
            "Test-Path -LiteralPath $worktreeHelper -PathType Leaf",
            "If that exact primary-checkout helper path is absent, do not skip cleanup",
            "cleanup_proof.py",
            "a dirty tree",
            "a merge commit absent from `origin/<default>`",
            "a still-open PR for the head",
            "`preserve:` stops cleanup",
            "worktree remove -- <target-worktree>",
            "branch -d <branch>",
            "proof covers exactly this head, so delete it with",
            "branch -D <branch>",
            "Step 5 is a blocking post-merge gate",
            "Only the `finish.ps1` path may enter Step 6 first",
            "never remove that path",
        ):
            with self.subTest(required=required):
                self.assertIn(required, flat)

        self.assertNotIn("worktree remove --force", cleanup)

    def test_merge_retargets_the_host_before_active_worktree_removal(self):
        body = authored_skill("merge").read_text(encoding="utf-8")
        cleanup = body.split(
            "### 5. Return to a clean base and retire any isolated checkout",
            maxsplit=1,
        )[1].split("### 6. Follow the publish", maxsplit=1)[0]
        flat = " ".join(cleanup.split())

        for required in (
            "Compare the recorded target checkout in the delivery binding with the resolved primary checkout",
            "When the target is the primary checkout, or the session is already attached to the primary checkout, do not retarget or hand off",
            "continue cleanup and branch deletion in the current session",
            "Only when the recorded target is a linked worktree, the host is attached to that target, and the target differs from the primary checkout",
            "the session closes itself as the delivery's final action, after Step 6",
            'no arguments and no leading `&`, because the harness allow rule matches only this string',
            'powershell.exe -NoProfile -ExecutionPolicy Bypass -File <machine:peer-cli skill-directory>/scripts/finish.ps1',
            "detaches a reaper that removes the worktree and branch once this session exits",
            "closes this session's CLI and tab",
            "Only when `finish.ps1` is unavailable or its preflight fails",
            "shell `cd`, or `git -C` does not retarget Codex or Claude",
            "invoke `/cd <primary-checkout>` there",
            "invoke the unqualified `handoff` workflow once with the primary checkout",
            "The successor is the sole cleanup owner",
            "requires the physical target path to be absent",
            "Do not make the user choose between these paths",
        ):
            with self.subTest(required=required):
                self.assertIn(required, flat)

        self.assertLess(cleanup.index("finish.ps1"), cleanup.index("$worktreeHelper"))
        self.assertLess(
            cleanup.index("finish.ps1"),
            cleanup.index("worktree remove -- <target-worktree>"),
        )

    def test_cd_and_handoff_transfer_active_directory_removal_to_the_successor(self):
        cd = " ".join(authored_skill("cd").read_text(encoding="utf-8").split())
        handoff = " ".join(
            authored_skill("handoff").read_text(encoding="utf-8").split()
        )

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
        self.assertIn(
            "put that exact operation and its final filesystem verification in the "
            "successor's `## Next Steps`",
            handoff,
        )
        self.assertIn(
            "The predecessor must not perform the operation after launch", handoff
        )
        self.assertIn("a command error or residual path as incomplete", handoff)


if __name__ == "__main__":
    unittest.main()
