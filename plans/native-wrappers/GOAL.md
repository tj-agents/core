# Core native wrappers

Owns the approved Core D6, D7 and D11 cutover from the [shared native-duplicates plan](https://github.com/tj-agents/docs/blob/main/plans/native-duplicates/NATIVE_DUPLICATES_PLAN.md).

```text
Claude delivery wait -> native goal and scheduling -> shared delivery evidence.
Codex durable CLI wait -> Codex runtime -> the same shared delivery evidence.
```

Authority: the parent approved this bounded implementation at main
`f847d301722ceb383f43c628d3ae99af82225b5e`. No commit, publication, installation,
live scheduling or session operation belongs to this writer lease. Protected Core #512
owns routing, hook and workflow-ops changes; those files remain outside this cutover.

- [x] Move the durable CLI supervisor and scheduler into Codex runtime, with exact package-local resolution and host rejection.
- [x] Keep native-first continuation and delivery invariants shared; put executable custom continuation instructions in the Codex entry.
- [x] Retire the five approved redundant selectors and their host/roster entries.
- [x] Correct Codex security-review availability without changing review evidence or routing.
- [x] Require a concrete workflow, policy or missing host capability before retaining a wrapper; native command naming alone does not justify a skill.
- [x] Regenerate locally and run focused runtime, packaging and guidance checks.

Acceptance requires relocated source and installed fixtures, no Claude custom continuation
entry, rejection of outer-runtime fallback, preserved delivery evidence and finite Codex
owner limits. Fresh native host and Windows/Linux scheduling acceptance remains a parent
delivery gate. Existing Claude registrations have not been migrated; their exact owners
must be reconciled before deployment can claim completion.

## Progress

October 27, 2026: implemented the approved source cutover. The supervisor and scheduler now
live under Codex runtime; the adapter is authored only beside the Codex entry. Exact source and
installed roots require local markers and shared resources. Initialization, owner load and child
execution reject other hosts. The five approved selector definitions, host entries and publication
roster entries are removed. Shared completion, binding and review evidence implementations are unchanged.

Focused verification:

- Adapter: 46 tests passed, six platform skips (the runner's platform predicates retain their existing behavior).
- Review adapter: 11 tests passed. Process standards: 19 tests passed.
- Supervisor: all 42 tests passed after correcting the outdated successful-exit expectation for fail-closed host rejection.
- Source and complete installed-package bytecode fixture passed, including required markers,
  lane resources and the relocated Codex runtime.
- Generator Check: 446 package files, zero drift. Plugin digest Check: zero drift.
  Harness manifest, tier payload, host coverage and canonical guidance example checks passed.
- Broader workflow contracts: 77 tests ran with two failures, 19 errors and three skips; observed
  failures were inherited Git configuration (`missing config value GIT_CONFIG_VALUE_1`) during local
  Git setup or verifier execution. The writer used two child-process diagnostic probes to confirm inherited Git configuration causality; no repository credential or test-isolation changes were made. The changed bytecode test passed independently.

Declared external runtime exports were staged locally for generation (Agent `4fad2409dd872ff7cf69bcc7e7b6f5952ab9f128`,
CLI `a312194a0aa32dbf2599cc2a98f7c4deffed72a1`). Their generated dependency bytes differ from prior tracked
output and therefore regenerate package hook fingerprints and digests; authored hooks remain untouched.
No commit, publication, installation, live scheduling or host-session action was performed.

Parent full-suite checkpoint: repository suite ran 431 tests (four failures, 61 Git128 errors, 14 skips); hooks ran 620 (three failures, 170 Git128 errors, seven skips). The stale 62-skill count was corrected to 57; all 23 source-layout tests then passed. All ten unchanged pre-tool adapter tests and the unchanged hook-timeout test passed in isolation after their load-sensitive full-suite failures. Existing Windows environment-mock restoration loses an empty inherited Git config value; source code and credential controls were not changed to hide that limitation. Exact-head clean Windows/Linux CI remains required.

Remaining parent gates: review the source diff, observe exact-head clean CI,
complete native-host/Windows/Linux acceptance, and reconcile exact existing Claude external registrations
before claiming an installed migration. Protected Core #512 remains outside this source diff.

October 27 user correction: remove Agent's redundant memory wrapper and repair this repository's
`engineering:skill-authoring` rule that encouraged mirroring every native command. The retained review
and continuation skills own frozen delivery evidence and durable CLI requirements, respectively.
Their value audit does not justify a separate wrapper for native memory controls. The earlier source
candidate passed full Windows/Linux CI at `bf287c19d3dcfb00abd6ed9bc314421d344ad38c`; this guidance
correction requires incremental review and its own exact-head checks.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/workflow/workflow/continue/SKILL.md",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Native goal and scheduling preserve shared delivery identity and authority.",
      "source": ".claude/skills/workflow/continue/SKILL.md",
      "mapping": "workflow/skills/continue",
      "verification": {"level": "source", "result": "passed", "evidence": "Focused guidance and package isolation checks; fresh host acceptance remains a delivery gate."}
    },
    {
      "host": "codex",
      "behavior": "Native goal and exposed scheduling use a Codex-only adapter for required durable CLI wakes.",
      "source": ".codex/skills/workflow/continue/SKILL.md",
      "mapping": "workflow/codex-skills/continue; engineering/codex-skills/persistent-delivery and .codex/runtime/continuation",
      "verification": {"level": "source", "result": "passed", "evidence": "Focused adapter, supervisor and source/package bytecode checks; fresh host acceptance remains a delivery gate."}
    }
  ]
}
```

October 27 naming correction: the user requested a Workflow namespace for continuation. The public
identity is now `workflow:continue`; `workflow:run` retains the goal and `workflow:resume` reconstructs
context. PR completion evidence moves into existing `engineering:persistent-delivery`; its Codex entry
retains the durable CLI instructions and adapter. The supervisor, scheduler, binding filename and live
registrations retain their identities. There is no old skill alias. This completes the same continuation
cutover in Core #517: canonical definition, both host entries, caller guidance and package assertions
change atomically. Splitting the rename would leave a missing skill or competing owners. Native runtime
behavior is unchanged; focused adapter, completion, packaging and process checks plus fresh frozen review
and exact-head Windows/Linux CI qualify the new candidate. The only delivery-hook change updates two
diagnostic skill references; routing, permission and gate logic remain outside this correction.
