import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plan_handoff_stop import (
    branch_ledgers,
    evaluate,
    expected_handoff,
    expected_pointer,
    next_steps,
    transcript_ledgers,
)


class PlanHandoffStopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "Concertable.worktrees" / "Feature" / "launch_example"
        self.root.mkdir(parents=True)
        self.root = self.root.resolve()
        self.ledger = self.root / "plans" / "launch" / "EXAMPLE_PROGRESS.md"
        self.plan = self.root / "plans" / "launch" / "EXAMPLE_PLAN.md"
        self.plan.parent.mkdir(parents=True)
        self.plan.write_text("# Plan\n", encoding="utf-8")
        self.roadmap = self.root / "plans" / "launch" / "LAUNCH_ROADMAP.md"
        self.roadmap.write_text(
            "# Roadmap\n\n- [ ] **Example** `launch/example`\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def write_ledger(self, next_steps, worktree=None):
        declared_worktree = worktree or self.root
        self.ledger.write_text(
            "\n".join(
                [
                    "# Progress",
                    "",
                    "- Plan: `plans/launch/EXAMPLE_PLAN.md`",
                    "- Roadmap: `plans/launch/LAUNCH_ROADMAP.md`",
                    "- Roadmap item: `launch/example`",
                    f"- Worktree: `{declared_worktree}`",
                    "- Branch: `Feature/launch_example`",
                    "",
                    "## Next Steps",
                    "",
                    next_steps,
                    "Scope: current slice only; full plan remains incomplete.",
                    "Current slice: complete the next action above.",
                    "Remaining scope: delivery and closeout remain.",
                    "Done when: this fixture step is green; the full plan remains open.",
                    "",
                    "## Completed work",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def write_ledger_without_next_steps(self):
        self.ledger.write_text(
            "\n".join(
                [
                    "# Progress",
                    "",
                    "- Plan: `plans/launch/EXAMPLE_PLAN.md`",
                    "- Roadmap: `plans/launch/LAUNCH_ROADMAP.md`",
                    "- Roadmap item: `launch/example`",
                    f"- Worktree: `{self.root}`",
                    "- Branch: `Feature/launch_example`",
                    "",
                    "## Completed work",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def write_plan_pair(self, root, next_steps, worktree, branch="Feature/launch_example"):
        ledger = root / "plans" / "launch" / "EXAMPLE_PROGRESS.md"
        plan = root / "plans" / "launch" / "EXAMPLE_PLAN.md"
        plan.parent.mkdir(parents=True, exist_ok=True)
        plan.write_text("# Plan\n", encoding="utf-8")
        roadmap = root / "plans" / "launch" / "LAUNCH_ROADMAP.md"
        roadmap.write_text(
            "# Roadmap\n\n- [ ] **Example** `launch/example`\n",
            encoding="utf-8",
        )
        ledger.write_text(
            "\n".join(
                [
                    "# Progress",
                    "",
                    "- Plan: `plans/launch/EXAMPLE_PLAN.md`",
                    "- Roadmap: `plans/launch/LAUNCH_ROADMAP.md`",
                    "- Roadmap item: `launch/example`",
                    f"- Worktree: `{worktree}`",
                    f"- Branch: `{branch}`",
                    "",
                    "## Next Steps",
                    "",
                    next_steps,
                    "Scope: current slice only; full plan remains incomplete.",
                    "Current slice: complete the next action above.",
                    "Remaining scope: delivery and closeout remain.",
                    "Done when: this fixture step is green; the full plan remains open.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return ledger.resolve()

    def input_with_codex_transcript(self, message):
        transcript = self.root / "transcript.jsonl"
        records = [
            {"type": "response_item", "payload": {"type": "message", "role": "user", "content": []}},
            {
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "name": "exec",
                    "input": (
                        'const patch = "*** Begin Patch\\n*** Update File: '
                        'plans\\launch\\EXAMPLE_PROGRESS.md\\n*** End Patch"; '
                        'await tools.apply_patch(patch); const options = {workdir: "'
                        + str(self.root)
                        + '"};'
                    ),
                },
            },
        ]
        transcript.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")
        return {
            "cwd": str(Path(self.temp.name) / "unrelated-main-checkout"),
            "transcript_path": str(transcript),
            "last_assistant_message": message,
        }

    def input_with_claude_transcript(self, message):
        transcript = self.root / "claude-transcript.jsonl"
        records = [
            {"type": "user", "message": {"role": "user", "content": "Continue the plan."}},
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "name": "Edit",
                            "input": {"file_path": str(self.ledger)},
                        }
                    ],
                },
            },
        ]
        transcript.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")
        return {
            "cwd": str(self.root),
            "transcript_path": str(transcript),
            "last_assistant_message": message,
        }

    def pointer(self):
        return (
            f"cd {self.root}\n"
            f"Read @{self.plan.resolve().as_posix()} and @{self.ledger.resolve().as_posix()} "
            "and do what its `## Next Steps` says."
        )

    def handoff(self):
        return expected_handoff(
            self.ledger.resolve(),
            self.pointer(),
            next_steps(self.ledger.read_text(encoding="utf-8")),
        )

    def input_without_ledger_reference(self, message):
        transcript = self.root / "unrelated-transcript.jsonl"
        record = {"type": "response_item", "payload": {"type": "message", "role": "user"}}
        transcript.write_text(json.dumps(record), encoding="utf-8")
        return {
            "cwd": str(self.root),
            "transcript_path": str(transcript),
            "last_assistant_message": message,
        }

    def input_with_codex_tool_output(self, message):
        transcript = self.root / "tool-output-transcript.jsonl"
        records = [
            {
                "type": "response_item",
                "payload": {"type": "message", "role": "user", "content": "Explain the result."},
            },
            {
                "type": "custom_tool_call_output",
                "payload": {
                    "type": "custom_tool_call_output",
                    "output": f"Read {self.ledger} from workdir: '{self.root}'",
                },
            },
        ]
        transcript.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")
        return {
            "cwd": str(self.root),
            "transcript_path": str(transcript),
            "last_assistant_message": message,
        }

    def input_with_injected_hook_prompt(self, message):
        transcript = self.root / "hook-prompt-transcript.jsonl"
        records = [
            {
                "type": "response_item",
                "payload": {"type": "message", "role": "user", "content": "Why was that emitted?"},
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": (
                        '<hook_prompt hook_run_id="stop:3:hooks.json">HANDOFF: '
                        f"Read @{self.ledger}</hook_prompt>"
                    ),
                },
            },
        ]
        transcript.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")
        return {
            "cwd": str(self.root),
            "transcript_path": str(transcript),
            "last_assistant_message": message,
        }

    def assertBlocked(self, result):
        self.assertEqual("block", result["decision"])
        return result["reason"]

    def test_active_plan_allows_same_context_continuation_without_handoff(self):
        self.write_ledger("Run the repository code-review workflow, then open the PR.")
        result = evaluate(
            self.input_with_codex_transcript(
                "Implementation is complete and committed. Continuing with Phase 2 here."
            )
        )
        self.assertEqual({}, result)

    def test_explicit_fresh_context_requires_handoff(self):
        self.write_ledger("Run the repository code-review workflow, then open the PR.")
        result = evaluate(
            self.input_with_codex_transcript("Continue this work in a fresh context.")
        )
        self.assertIn(self.pointer(), self.assertBlocked(result))

    def test_explanatory_context_language_does_not_select_transfer(self):
        self.write_ledger("Run the repository code-review workflow, then open the PR.")
        result = evaluate(
            self.input_with_codex_transcript(
                "A fresh context is only useful when earlier reasoning is no longer relevant."
            )
        )
        self.assertEqual({}, result)

    def test_allows_explained_handoff_at_end(self):
        self.write_ledger("Run the repository code-review workflow, then open the PR.")
        result = evaluate(self.input_with_codex_transcript(f"Ready.\n\n{self.handoff()}"))
        self.assertEqual({}, result)

    def test_bare_pointer_is_rejected(self):
        self.write_ledger("Run the repository code-review workflow, then open the PR.")
        result = evaluate(
            self.input_with_codex_transcript(f"Ready.\n\n```text\n{self.pointer()}\n```")
        )
        self.assertIn("explained continuation", self.assertBlocked(result))

    def test_pointer_followed_by_prose_is_rejected(self):
        self.write_ledger("Run the repository code-review workflow, then open the PR.")
        result = evaluate(
            self.input_with_codex_transcript(f"{self.handoff()}\n\nLet me know.")
        )
        self.assertIn("placed prose after it", self.assertBlocked(result))

    def test_generated_repair_handoff_passes_on_retry(self):
        self.write_ledger("Run the repository code-review workflow, then open the PR.")
        first = evaluate(
            self.input_with_codex_transcript("Continue this work in a fresh context.")
        )
        retry = self.input_with_codex_transcript(f"Ready.\n\n{self.handoff()}")
        retry["stop_hook_active"] = True

        self.assertEqual("block", first["decision"])
        self.assertEqual({}, evaluate(retry))

    def test_retry_guard_prevents_recursive_block(self):
        self.write_ledger("Run the repository code-review workflow, then open the PR.")
        retry = self.input_with_codex_transcript(
            "Continue this work in a fresh context, but the pointer is still missing."
        )
        retry["stop_hook_active"] = True

        result = evaluate(retry)

        self.assertNotIn("decision", result)
        self.assertIn("prevent a recursive Stop-hook loop", result["systemMessage"])

    def test_claude_transcript_also_allows_same_context_continuation(self):
        self.write_ledger("Run the repository code-review workflow, then open the PR.")
        result = evaluate(self.input_with_claude_transcript("Implementation is complete."))
        self.assertEqual({}, result)

    def test_paused_plan_is_silent(self):
        self.write_ledger("Paused: awaiting Tommy's go-ahead on the launch copy before publishing.")
        result = evaluate(self.input_with_codex_transcript("Copy is ready; waiting on you."))
        self.assertEqual({}, result)

    def test_terminal_plan_is_silent(self):
        self.write_ledger("Complete")
        result = evaluate(self.input_with_codex_transcript("Everything is complete."))
        self.assertEqual({}, result)

    def test_well_formed_blocker_requires_exact_report(self):
        blocker = (
            "Blocked: PR #123 has not merged.\n"
            "Blocked by: GitHub PR #123.\n"
            "Unblock action: The PR #123 owner must follow it to a terminal merge.\n"
            "Resume when: GitHub reports PR #123 merged."
        )
        self.write_ledger(blocker)
        result = evaluate(self.input_with_codex_transcript(blocker))
        self.assertEqual({}, result)

        missing = evaluate(self.input_with_codex_transcript("Still blocked on PR #123."))
        self.assertIn("report these exact lines", self.assertBlocked(missing))

    def test_malformed_blocker_is_blocked(self):
        self.write_ledger("Waiting for PR #123 to merge; its owner will surface this plan when ready.")
        result = evaluate(self.input_with_codex_transcript("Waiting for PR #123."))
        self.assertIn("Blocked by:", self.assertBlocked(result))

    def test_missing_next_steps_is_blocked(self):
        self.write_ledger_without_next_steps()
        result = evaluate(self.input_with_codex_transcript("Everything is complete."))
        self.assertIn("`## Next Steps`", self.assertBlocked(result))

    def test_invalid_plan_graph_is_blocked(self):
        self.write_ledger("Open the PR.")
        self.roadmap.write_text("# Roadmap\n", encoding="utf-8")
        result = evaluate(self.input_with_codex_transcript("Implementation is complete."))
        message = self.assertBlocked(result)
        self.assertIn("PLAN GRAPH", message)
        self.assertNotIn(self.pointer(), message)

    def test_missing_worktree_uses_open_worktree_opener(self):
        missing = self.root.parent / "launch_not_created"
        self.write_ledger("Implement the plan.", worktree=missing)
        result = evaluate(
            self.input_with_codex_transcript("Continue the plan in a fresh context.")
        )
        self.assertIn("/open-worktree Feature/launch_example", self.assertBlocked(result))

    @patch("plan_handoff_stop.git_branch", return_value="Feature/launch_example")
    def test_branch_discovery_reads_the_owning_worktree(self, _git_branch):
        ledger = self.write_plan_pair(self.root, "Open the PR.", self.root)

        self.assertEqual({ledger}, branch_ledgers(self.root))

    def test_relative_transcript_reference_resolves_in_owning_worktree(self):
        ledger = self.write_plan_pair(self.root, "Open the PR.", self.root)
        data = self.input_with_codex_transcript("Continue in a fresh context.")
        records = [
            json.loads(line)
            for line in Path(data["transcript_path"]).read_text(encoding="utf-8").splitlines()
        ]

        self.assertEqual({ledger}, transcript_ledgers(records, self.root))

    def test_mixed_blocked_and_active_returns_complete_repair(self):
        blocked = self.root / "plans" / "launch" / "OWNER_PROGRESS.md"
        blocked_plan = blocked.with_name("OWNER_PLAN.md")
        active = self.root / "plans" / "launch" / "DEPENDENT_PROGRESS.md"
        active_plan = active.with_name("DEPENDENT_PLAN.md")
        blocked_plan.write_text("# Plan\n", encoding="utf-8")
        active_plan.write_text("# Plan\n", encoding="utf-8")
        blocker = (
            "Blocked: The package is not published.\n"
            "Blocked by: package owner.\n"
            "Unblock action: Publish and verify the package.\n"
            "Resume when: The production feed restores it."
        )
        blocked.write_text(
            "- Plan: `plans/launch/OWNER_PLAN.md`\n"
            "- Roadmap: `plans/launch/LAUNCH_ROADMAP.md`\n"
            "- Roadmap item: `launch/example`\n"
            f"- Worktree: `{self.root}`\n\n## Next Steps\n\n{blocker}\n"
            "Scope: current slice only; full plan remains incomplete.\n"
            "Current slice: wait for package publication.\n"
            "Remaining scope: dependent delivery and closeout remain.\n"
            "Done when: the package is published; the full plan remains open.\n",
            encoding="utf-8",
        )
        active.write_text(
            "- Plan: `plans/launch/DEPENDENT_PLAN.md`\n"
            "- Roadmap: `plans/launch/LAUNCH_ROADMAP.md`\n"
            "- Roadmap item: `launch/example`\n"
            f"- Worktree: `{self.root}`\n\n## Next Steps\n\nOpen the dependent PR.\n"
            "Scope: current slice only; full plan remains incomplete.\n"
            "Current slice: open the dependent PR.\n"
            "Remaining scope: delivery and closeout remain.\n"
            "Done when: this fixture step is green; the full plan remains open.\n",
            encoding="utf-8",
        )
        active_pointer = (
            f"cd {self.root}\n"
            f"Read @{active_plan.resolve().as_posix()} and "
            f"@{active.resolve().as_posix()} and do what its `## Next Steps` says."
        )
        transcript = self.root / "mixed-handoff-transcript.jsonl"
        records = [
            {
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "name": "exec",
                    "input": (
                        'const patch = "*** Begin Patch\\n*** Update File: '
                        'plans/launch/OWNER_PROGRESS.md\\n*** Update File: '
                        'plans/launch/DEPENDENT_PROGRESS.md\\n*** End Patch"; '
                        f'const options = {{workdir: "{self.root}"}};'
                    ),
                },
            }
        ]
        transcript.write_text(
            "\n".join(json.dumps(record) for record in records),
            encoding="utf-8",
        )
        result = evaluate(
            {
                "cwd": str(self.root),
                "transcript_path": str(transcript),
                "last_assistant_message": "Continue active work in a fresh context.",
            }
        )
        message = self.assertBlocked(result)
        self.assertIn(active_pointer, message)
        self.assertIn("Blocked: The package is not published.", message)

    def test_patch_claims_targets_without_claiming_referenced_dependency_ledgers(self):
        typed_result = self.root / "plans" / "typed-result"
        unions = self.root / "plans" / "dotnet-11"
        owner = typed_result / "REUNION_INTEGRATION_PROGRESS.md"
        b2b = typed_result / "B2B_PROGRESS.md"
        workflow_unions = unions / "B2B_WORKFLOW_UNIONS_PROGRESS.md"
        for ledger in (owner, b2b, workflow_unions):
            ledger.parent.mkdir(parents=True, exist_ok=True)
            ledger.with_name(ledger.name.replace("_PROGRESS.md", "_PLAN.md")).write_text(
                "# Plan\n", encoding="utf-8"
            )
        typed_roadmap = typed_result / "TYPED_RESULT_ROADMAP.md"
        typed_roadmap.write_text(
            "- [ ] **Integration** `typed-result/integration`\n"
            "- [ ] **B2B** `typed-result/b2b`\n",
            encoding="utf-8",
        )
        dotnet_roadmap = unions / "DOTNET_ROADMAP.md"
        dotnet_roadmap.write_text(
            "- [ ] **Unions** `dotnet-11/unions`\n",
            encoding="utf-8",
        )
        owner.write_text(
            "- Plan: `plans/typed-result/REUNION_INTEGRATION_PLAN.md`\n"
            "- Roadmap: `plans/typed-result/TYPED_RESULT_ROADMAP.md`\n"
            "- Roadmap item: `typed-result/integration`\n\n"
            "## Next Steps\n\nCreate the integration worktree.\n"
            "Scope: current slice only; full plan remains incomplete.\n"
            "Current slice: create the integration worktree.\n"
            "Remaining scope: delivery and closeout remain.\n"
            "Done when: this fixture step is green; the full plan remains open.\n\n"
            "## Downstream handoffs\n\n- `plans/typed-result/B2B_PROGRESS.md`\n",
            encoding="utf-8",
        )
        b2b_steps = (
            "Blocked: ReUnion platform sync has not merged.\n"
            "Blocked by: plans/typed-result/REUNION_INTEGRATION_PROGRESS.md.\n"
            "Unblock action: The owner at `plans/typed-result/REUNION_INTEGRATION_PROGRESS.md` "
            "must merge it.\n"
            "Resume when: Main contains the ReUnion platform pin."
        )
        b2b.write_text(
            "- Plan: `plans/typed-result/B2B_PLAN.md`\n"
            "- Roadmap: `plans/typed-result/TYPED_RESULT_ROADMAP.md`\n"
            "- Roadmap item: `typed-result/b2b`\n\n"
            f"## Next Steps\n\n{b2b_steps}\n"
            "Scope: current slice only; full plan remains incomplete.\n"
            "Current slice: wait for the platform sync.\n"
            "Remaining scope: B2B delivery and closeout remain.\n"
            "Done when: the platform pin lands; the full plan remains open.\n\n"
            "## Downstream handoffs\n\n- `plans/dotnet-11/B2B_WORKFLOW_UNIONS_PROGRESS.md`\n",
            encoding="utf-8",
        )
        union_steps = (
            "Blocked: B2B delivery is not terminal.\n"
            "Blocked by: plans/typed-result/B2B_PROGRESS.md.\n"
            "Unblock action: The owner at `plans/typed-result/B2B_PROGRESS.md` must finish it.\n"
            "Resume when: Main contains the B2B work."
        )
        workflow_unions.write_text(
            "- Plan: `plans/dotnet-11/B2B_WORKFLOW_UNIONS_PLAN.md`\n"
            "- Roadmap: `plans/dotnet-11/DOTNET_ROADMAP.md`\n"
            "- Roadmap item: `dotnet-11/unions`\n\n"
            f"## Next Steps\n\n{union_steps}\n"
            "Scope: current slice only; full plan remains incomplete.\n"
            "Current slice: wait for B2B delivery.\n"
            "Remaining scope: workflow-union delivery and closeout remain.\n"
            "Done when: B2B is delivered; the full plan remains open.\n",
            encoding="utf-8",
        )
        transcript = self.root / "dependency-chain-transcript.jsonl"
        records = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": "Create the workflow-unions plan.",
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "name": "exec",
                    "input": (
                        'const patch = "*** Begin Patch\\n*** Update File: '
                        'plans/typed-result/B2B_PROGRESS.md\\n'
                        '+Unblock action: The owner at '
                        '`plans/typed-result/REUNION_INTEGRATION_PROGRESS.md` must merge it.\\n'
                        '*** End Patch"; const options = {workdir: "'
                        + str(self.root)
                        + '"};'
                    ),
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "name": "exec",
                    "input": (
                        'const patch = "*** Begin Patch\\n*** Update File: '
                        'plans/dotnet-11/B2B_WORKFLOW_UNIONS_PROGRESS.md\\n'
                        '+Unblock action: The owner at `plans/typed-result/B2B_PROGRESS.md` '
                        'must finish it.\\n*** End Patch"; const options = {workdir: "'
                        + str(self.root)
                        + '"};'
                    ),
                },
            },
        ]
        transcript.write_text(
            "\n".join(json.dumps(record) for record in records),
            encoding="utf-8",
        )
        claimed = transcript_ledgers(records, self.root)
        self.assertEqual({b2b.resolve(), workflow_unions.resolve()}, claimed)

        result = evaluate(
            {
                "cwd": str(self.root),
                "transcript_path": str(transcript),
                "last_assistant_message": f"{union_steps}\n\n{b2b_steps}",
            }
        )
        self.assertEqual({}, result)

    def test_relative_reference_resolves_only_against_its_tool_workdir(self):
        alternate_root = (Path(self.temp.name) / "unrelated-main-checkout").resolve()
        alternate_ledger = self.write_plan_pair(
            alternate_root,
            "Open the alternate PR.",
            alternate_root,
        )
        self.write_ledger("Open the owner PR.")
        records = [
            {
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "name": "exec",
                    "input": (
                        'const patch = "*** Begin Patch\\n*** Update File: '
                        'plans\\launch\\EXAMPLE_PROGRESS.md\\n*** End Patch"; '
                        'await tools.apply_patch(patch); const options = {workdir: "'
                        + str(self.root)
                        + '"};'
                    ),
                },
            }
        ]
        self.assertEqual(
            {self.ledger.resolve()},
            transcript_ledgers(records, alternate_root),
        )
        self.assertNotIn(alternate_ledger, transcript_ledgers(records, alternate_root))

    def test_cross_worktree_mutation_does_not_claim_foreign_ledger(self):
        foreign_root = (Path(self.temp.name) / "foreign-worktree").resolve()
        foreign_ledger = self.write_plan_pair(
            foreign_root,
            "Open the foreign PR.",
            foreign_root,
            branch="Feature/foreign",
        )
        records = [
            {
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "name": "exec",
                    "input": (
                        f'const patch = "*** Begin Patch\\n*** Update File: {foreign_ledger}'
                        '\\n*** End Patch"; await tools.apply_patch(patch);'
                    ),
                },
            }
        ]

        self.assertEqual(set(), transcript_ledgers(records, self.root))

    def test_structured_tool_workdir_resolves_relative_reference(self):
        self.write_ledger("Open the owner PR.")
        records = [
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "name": "write_file",
                    "arguments": {
                        "path": "plans/launch/EXAMPLE_PROGRESS.md",
                        "workdir": str(self.root),
                    },
                },
            }
        ]
        unrelated = Path(self.temp.name) / "unrelated-main-checkout"
        self.assertEqual({self.ledger.resolve()}, transcript_ledgers(records, unrelated))

    def test_absolute_reference_is_not_resolved_again_as_relative(self):
        alternate_root = (Path(self.temp.name) / "unrelated-main-checkout").resolve()
        self.write_plan_pair(alternate_root, "Open the alternate PR.", alternate_root)
        self.write_ledger("Open the owner PR.")
        records = [
            {
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "name": "exec",
                    "input": (
                        f'const patch = "*** Begin Patch\\n*** Update File: {self.ledger}'
                        '\\n*** End Patch"; await tools.apply_patch(patch); '
                        f'const options = {{workdir: "{self.root}"}};'
                    ),
                },
            }
        ]
        self.assertEqual({self.ledger.resolve()}, transcript_ledgers(records, alternate_root))

    def test_owner_copy_wins_over_stale_worktree_copy(self):
        self.write_ledger("Open the owner PR.")
        stale_root = (Path(self.temp.name) / "stale-checkout").resolve()
        self.write_plan_pair(
            stale_root,
            "Open the stale PR.",
            stale_root / "missing-owner",
        )
        transcript = self.root / "duplicate-transcript.jsonl"
        record = {
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [
                    {"type": "input_text", "text": str(stale_root / "plans" / "launch" / "EXAMPLE_PROGRESS.md")},
                    {"type": "input_text", "text": str(self.ledger)},
                ],
            },
        }
        transcript.write_text(json.dumps(record), encoding="utf-8")
        result = evaluate(
            {
                "cwd": str(self.root),
                "transcript_path": str(transcript),
                "last_assistant_message": "Continue this work in a fresh context.",
            }
        )
        message = self.assertBlocked(result)
        self.assertIn(self.pointer(), message)
        self.assertNotIn("missing-owner", message)

    def test_duplicate_logical_ledgers_emit_one_pointer(self):
        missing_owner = Path(self.temp.name) / "missing-owner"
        first = self.write_plan_pair(
            (Path(self.temp.name) / "copy-one").resolve(),
            "Open the PR.",
            missing_owner,
        )
        second = self.write_plan_pair(
            (Path(self.temp.name) / "copy-two").resolve(),
            "Open the PR.",
            missing_owner,
        )
        transcript = self.root / "logical-duplicate-transcript.jsonl"
        records = [
            {
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "name": "exec",
                    "input": (
                        f'const patch = "*** Begin Patch\\n*** Update File: {path}'
                        '\\n*** End Patch"; await tools.apply_patch(patch); '
                        f'const options = {{workdir: "{path.parents[2]}"}};'
                    ),
                },
            }
            for path in (first, second)
        ]
        transcript.write_text(
            "\n".join(json.dumps(record) for record in records),
            encoding="utf-8",
        )
        result = evaluate(
            {
                "cwd": str(self.root),
                "transcript_path": str(transcript),
                "last_assistant_message": "Continue this work in a fresh context.",
            }
        )
        message = self.assertBlocked(result)
        self.assertEqual(1, message.count("/open-worktree Feature/launch_example"))

    def test_unrelated_turn_in_plan_worktree_needs_no_handoff(self):
        self.write_ledger("Run the repository code-review workflow, then open the PR.")
        with patch("plan_handoff_stop.branch_ledgers", return_value={self.ledger}) as fallback:
            result = evaluate(self.input_without_ledger_reference("The answer is 42."))
        self.assertEqual({}, result)
        fallback.assert_not_called()

    def test_tool_output_does_not_claim_ledger_for_session(self):
        self.write_ledger("Run the repository code-review workflow, then open the PR.")
        result = evaluate(self.input_with_codex_tool_output("The output mentions another plan."))
        self.assertEqual({}, result)

    def test_injected_hook_prompt_does_not_claim_ledger_for_session(self):
        self.write_ledger("Run the repository code-review workflow, then open the PR.")
        result = evaluate(self.input_with_injected_hook_prompt("That pointer was unrelated."))
        self.assertEqual({}, result)


if __name__ == "__main__":
    unittest.main()
