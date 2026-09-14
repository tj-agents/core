import unittest
from pathlib import Path


class ProcessStandardsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[3]

    def corpus(self):
        paths = list((self.root / "standards").rglob("*.md"))
        paths.extend((self.root / ".agents" / "skills").glob("*/SKILL.md"))
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
        checkpoint = (self.root / ".agents" / "skills" / "plan-checkpoint" / "SKILL.md").read_text(
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
        staged = (self.root / ".agents" / "skills" / "big-review" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("## rules manifest", staged.lower())
        self.assertIn("the canonical work order is the resume contract", staged.lower())
        self.assertNotRegex(staged.lower(), r"plan checkpoint[^\n]{0,120}(?:each|every) stage")

    def test_address_review_does_not_force_one_agent_context_per_finding(self):
        address = (self.root / ".agents/skills/address-review/SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Take one open finding or one tightly coupled group", address)
        self.assertNotIn("own fresh agent context", address)
        self.assertNotIn("Spawn exactly one fresh agent context", address)
        self.assertNotIn("one finding per agent context", address)

    def test_address_review_serializes_every_fix(self):
        address = (self.root / ".agents/skills/address-review/SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Never overlap\nwriters", address)
        self.assertIn("one exclusive writer", address)
        self.assertIn("even for disjoint files", address)
        self.assertNotIn("Serial by default", address)
        self.assertNotIn("concurrent fixes", address)

    def test_floor_owns_the_stage_pointer_rule_and_no_skill_restates_it(self):
        floor = (self.root / "standards" / "process" / "FLOOR.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("## A link to another skill is a stage pointer, not a read", floor)
        self.assertIn(
            "Load a referenced skill when its stage is actually entered, never because a document",
            floor,
        )
        self.assertEqual(1, self.corpus().count("stage is actually entered"))

    def test_plan_execution_reads_the_plan_corpus_only_when_it_changes_a_decision(self):
        body = (self.root / ".agents/skills/plan-execution/SKILL.md").read_text(
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
            "Do not re-read the plan, the ledger, `plans`, or `plan-checkpoint`", flat
        )
        self.assertNotIn("Read the repository instructions, [`plans`]", body)

    def test_harness_specific_persistent_continuation_is_routed(self):
        remote = (self.root / ".agents/skills/remote-validation/SKILL.md").read_text(
            encoding="utf-8"
        )
        shared = (self.root / ".agents/skills/persistent-delivery/SKILL.md").read_text(
            encoding="utf-8"
        )
        claude = (
            self.root / ".claude/workflow-skills/persistent-workflow/SKILL.md"
        ).read_text(encoding="utf-8")
        codex = (
            self.root / ".codex/workflow-skills/persistent-workflow/SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertIn("persistent-workflow skill", remote)
        self.assertIn("persistent-delivery", remote)
        self.assertIn("one persistent owner for a PR/head pair", shared)
        self.assertIn("/goal", claude)
        self.assertIn("Desktop scheduled tasks", claude)
        self.assertIn("Dynamic Workflows", claude)
        self.assertIn(
            "Scheduled Task attached to this owning Codex/ChatGPT Desktop conversation",
            codex,
        )
        self.assertNotIn("Claude uses", remote)
        self.assertNotIn("Codex Desktop uses", remote)
        for skill in ("e2e-debug", "e2e-api-debug", "e2e-ui-debug", "integration-debug"):
            with self.subTest(skill=skill):
                self.assertIn(skill, shared)
        self.assertIn("clear context", shared)
        self.assertNotEqual(claude, codex)

        merge = (self.root / ".agents/skills/merge/SKILL.md").read_text(encoding="utf-8")
        merging = (self.root / ".agents/skills/merging/SKILL.md").read_text(encoding="utf-8")
        for body in (merge, merging):
            with self.subTest(policy="merge-debug-dispatch"):
                self.assertIn("immediately dispatch one fresh", body)
                self.assertIn("foreground fallback", body)
        self.assertIn("exact run head", merging)
        self.assertIn("bound PR source head", merging)

    def test_techdebt_isolates_before_survey_and_picks_fast(self):
        body = (self.root / ".agents/skills/techdebt/SKILL.md").read_text(encoding="utf-8")
        flat = " ".join(body.split())

        self.assertIn("Isolate — before reading a single `TECH_DEBT.md`", flat)
        self.assertIn("*before* any survey or investigation", flat)
        self.assertIn("Pick the item(s) fast", flat)
        self.assertIn("do not read each entry in full", flat)
        self.assertIn("the bundling test below is applied after that pick", flat)
        self.assertNotIn("Survey every `TECH_DEBT.md` in the repo, then choose", flat)

    def test_plan_execution_resumes_into_owned_partial_work(self):
        body = (self.root / ".agents/skills/plan-execution/SKILL.md").read_text(
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

    def test_review_rechecks_routed_rules_instead_of_citing_an_earlier_read(self):
        body = (self.root / ".agents/skills/review/SKILL.md").read_text(encoding="utf-8")
        flat = " ".join(body.split())

        self.assertIn(
            "Having invoked a skill earlier in the session — including while writing the "
            "diff now under review — is not evidence its rules were applied",
            flat,
        )
        self.assertIn("Re-open each routed skill here", flat)

    def test_merge_docs_keeps_an_existing_isolated_branch(self):
        body = (self.root / ".agents/skills/merge-docs/SKILL.md").read_text(
            encoding="utf-8"
        )
        flat = " ".join(body.split())

        self.assertIn(
            "do not create a second branch solely to change the type prefix to `Docs`", flat
        )


class SkillPayloadTests(unittest.TestCase):
    """A skill's payload is its folder, not only its SKILL.md.

    The generator's prune pass removes anything under a generated root it did not just author, so a
    sibling file the generator forgets to emit is not merely absent from the shipped copy - it is deleted
    from it. `handoff-claude` and `handoff-codex` each invoke a launcher script beside their SKILL.md, and
    a plugin cannot reference a file outside its own root, so an unshipped script is a skill whose one
    documented instruction cannot be followed.
    """

    GENERATED_ROOTS = (
        ".claude/skills",
        "plugins/process-standards/skills",
        "plugins/process-standards/codex-skills",
    )

    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[3]
        cls.authored = cls.root / ".agents" / "skills"

    def siblings(self):
        for skill in sorted(p for p in self.authored.iterdir() if p.is_dir()):
            for path in sorted(skill.rglob("*")):
                if path.is_file() and path.name != "SKILL.md":
                    yield skill.name, path.relative_to(skill).as_posix(), path

    def test_every_authored_sibling_ships_verbatim_in_every_generated_copy(self):
        found = 0
        for skill, relative, source in self.siblings():
            found += 1
            expected = source.read_text(encoding="utf-8").replace("\r\n", "\n")
            for generated_root in self.GENERATED_ROOTS:
                copy = self.root / generated_root / skill / relative
                with self.subTest(skill=skill, file=relative, root=generated_root):
                    self.assertTrue(copy.is_file(), f"{copy} was never generated")
                    self.assertEqual(
                        expected, copy.read_text(encoding="utf-8").replace("\r\n", "\n")
                    )
        self.assertTrue(found, "no skill ships a sibling file; this contract is untested")

    def test_both_handoff_launchers_ship_their_script(self):
        for skill, script in (
            ("handoff-claude", "scripts/launch-claude.ps1"),
            ("handoff-codex", "scripts/launch-codex.ps1"),
        ):
            with self.subTest(skill=skill):
                self.assertTrue((self.authored / skill / script).is_file())
                for generated_root in self.GENERATED_ROOTS:
                    self.assertTrue((self.root / generated_root / skill / script).is_file())

    def test_the_codex_launcher_ranks_by_version_and_refuses_a_stale_build(self):
        """Ranking the cached payloads by LastWriteTime picked a 0.151.0-alpha.7.1 desktop runtime over
        the 0.154.0 npm build, and gpt-6-astra does not exist in that alpha at all."""
        launcher = (
            self.authored / "handoff-codex" / "scripts" / "launch-codex.ps1"
        ).read_text(encoding="utf-8")

        self.assertIn("function Compare-CodexVersion", launcher)
        self.assertIn("$MinimumVersion = '0.154.0'", launcher)
        self.assertNotIn("Sort-Object LastWriteTime", launcher)


if __name__ == "__main__":
    unittest.main()
