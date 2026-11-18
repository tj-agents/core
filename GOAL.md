# Generate package records

Canonical item: https://github.com/tj-agents/core/issues/473

## Authority and ownership

Tommy authorized implementation, a PR and delivery to merge on October 24, 2026 through the supplied
handoff. Work from `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Refactor-GeneratedPackages`
on `Refactor/GeneratedPackages`. The repository requires Tommy's review approval; request `tomjseery`,
enable guarded auto-merge and never use an admin bypass. Report `Approve <PR URL>` first when approval
is the remaining gate. The prior scratch handoff is promoted into this goal.

## Assessment and delivery slice

Assessment complete: reuse Core's existing deterministic generator, skill discovery, host manifests,
harness declarations and tree hashing. No new technical component or dependency is needed.
The existing catalog duplicates those inputs; runtime tool requirements and platforms move into
`sources.json`. External plugin prerequisites retain their separate existing declaration.

One atomic source/schema/caller cutover targets `main`, based on
`41b2473946b4c64c813d176db3f910173677377b`. Splitting producer generation from schema, snapshot,
CI and test consumers would leave broken intermediate entry points or require prohibited aliases.
Implementation uses L4 capability for the specified transformation and local testable decisions;
bounded read-only evidence and independent review are delegated. No additional executable owner.
Repository conventions: `CODE_CONVENTIONS.md`, `SOURCE_LAYOUT.md`, `PACKAGING.md`, the root and harness
`AGENTS.md`, `workflow:run`, `engineering:feature`, `engineering:remote-validation` and `machine:lanes`.

## Acceptance

- Generate complete `plugins/packages.json` and identical Machine-root `packages.json` in the same pass
  as payloads; missing/stale generated files never prevent generation.
- Remove the authored record, retired digest updater and all Core-path consumers. Move schemas into
  `.agents/schemas/`; keep schema bytes covered by Machine's digest and only exclude `packages.json`.
- Preserve the unrelated central marketplace catalog, native trust and publisher identity controls.
- Run affected tests as one bounded command, removing inherited Git-config injection variables first.
  Full Windows/Linux tests and native host acceptance run in CI.
- Commit authored sources only, review the immutable candidate, open a PR, request Tommy's approval,
  enable guarded auto-merge and verify main's regeneration publishes the package records after merge.

## Current state

Implementation is complete locally. The affected 118-test run exposed two renamed-fixture expectations;
those two cases and the expanded six-test generation module passed after correction. Four snapshot
subcases skipped because Windows symbolic-link creation is unavailable. Generation and its check,
harness validation, tier payloads, packaging, source/shipped schema validation and agent-file pairs pass.
The plan-graph command reports six structural errors in two untouched ledgers; an exported original
HEAD reproduces the identical six errors. No graph errors were introduced by this change.

Renaming audit: remaining `catalog` uses refer to the central marketplace/host marketplace manifests,
Machine's persisted marketplace event state and their tests, plus workflow stage catalogue metadata;
none refer to the retired Core package record. These uses keep their independent contracts.

The current diff is one atomic cutover. The large deletion is the former 1,360-line derived record;
schema moves and preservation of Machine's existing mixed line endings keep review focused.
Independent full source/security review and incremental native review passed at exact head
`02aa08a2817ce3348bc274b8157c06d0a0d67467`. The CI command-count assertion was corrected
from 18 to 16 after removal of the two retired digest commands; all three permission tests pass.
Replacement CI is run 40139419177. Windows/Linux full source/package and shared-runtime tests passed; both-platform
native startup/discovery acceptance passed. All checks including ci-required are green. Delivery remains. Item #473 exists; its helper reported incomplete board
placement because the GitHub POST failed, so board placement has not been claimed.

PR: https://github.com/tj-agents/core/pull/475
Head: `02aa08a2817ce3348bc274b8157c06d0a0d67467`
Review: Git-private canonical work order and exact-head receipt, resolved by workflow_ops.py review-path.
PR is ready for review and tomjseery review was requested. All authored code is pushed.
Next action: Tommy approves and manually merges PR #475 under the repository CI-workflow stop;
then resume the post-merge publication acceptance from this goal.

The delivery binder reevaluated the supplied goal authorization and stopped merge authorization at
`ci-workflow` for `.github/workflows/ci.yml`. The repository authorizes only the `auth` stop class.
Do not modify policy or bypass this stop. Guarded auto-merge cannot be armed under the current policy.
After manual merge, the outstanding acceptance is the causally linked main regeneration run publishing
`plugins/packages.json`; retain issue #473 until that is verified.

Continuation was initialized, claimed, scheduled and an actual wake observed, with no competing child.
The guarded command refused the green ready PR with `current authorization does not permit merge`.
Terminal authorization handoff: checkpoint blocked and remove its scheduled task and delivery binding
under persistent-delivery. No unattended post-merge owner remains; the goal and review proof remain.
Do not claim merge or generated-main publication has occurred.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": "scripts/sync_plugin_packages.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "discovers generated self-contained package payloads and package records",
      "source": ".agents/plugins/manifests/claude/machine.json",
      "mapping": "plugins/machine/.claude-plugin/plugin.json and packages.json",
      "verification": {
        "level": "installed",
        "result": "passed",
        "evidence": "Run 40139419177 at 02aa08a2817ce3348bc274b8157c06d0a0d67467: native host startup and discovery acceptance passed on Windows and Linux. Local focused generation, packaging and snapshot checks also passed."
      }
    },
    {
      "host": "codex",
      "behavior": "discovers generated payloads and verifies snapshots using the new self-exclusion",
      "source": ".agents/plugins/manifests/codex/machine.json",
      "mapping": "plugins/machine/.codex-plugin/plugin.json, hooks/codex.json and packages.json",
      "verification": {
        "level": "installed",
        "result": "passed",
        "evidence": "Run 40139419177 at 02aa08a2817ce3348bc274b8157c06d0a0d67467: native host startup and discovery acceptance passed on Windows and Linux. Local focused generation, packaging and snapshot checks also passed."
      }
    }
  ]
}
```

```completion
{
  "outcome": "Package-record generation implemented and pushed; delivery remains gated by repository CI-workflow policy and owner review.",
  "acceptance": [
    {
      "id": "generation",
      "criterion": "Deterministic complete package records generated with payloads, all source consumers migrated, retired catalog/updater removed.",
      "evidence": [
        {
          "source": "02aa08a2817ce3348bc274b8157c06d0a0d67467 plus local focused validation and canonical review receipt",
          "result": "passed"
        }
      ],
      "owner": "Codex",
      "next_action": "Retain reviewed exact head."
    },
    {
      "id": "native-ci",
      "criterion": "Windows/Linux full tests and native host acceptance pass at the delivery head.",
      "evidence": [
        {
          "source": "https://github.com/tj-agents/core/actions/runs/40139419177 at 02aa08a2817ce3348bc274b8157c06d0a0d67467",
          "result": "All checks passed: Windows/Linux source/package and runtime tests plus fresh native startup/discovery acceptance; ci-required success."
        }
      ],
      "owner": "Codex",
      "next_action": "Retain observed exact-head CI evidence."
    },
    {
      "id": "publication",
      "criterion": "PR merged and causally linked regeneration publishes plugins/packages.json on main.",
      "evidence": [],
      "owner": "Tommy at repository merge-policy gate, then resumed delivery owner",
      "next_action": "Approve/reconcile CI-workflow stop and merge PR 475; verify linked main regeneration before closing issue 473."
    }
  ],
  "deliveries": [
    {
      "repository": "tj-agents/core",
      "pr": 475,
      "head": "02aa08a2817ce3348bc274b8157c06d0a0d67467"
    }
  ],
  "open_tasks": [
    {
      "repository": "tj-agents/core",
      "pr": 475,
      "head": "02aa08a2817ce3348bc274b8157c06d0a0d67467",
      "text": "Merge-policy decision and post-merge publication acceptance",
      "owner": "Tommy then resumed delivery owner",
      "next_action": "Review PR 475; after merge verify the exact resulting regeneration run and plugins/packages.json on main."
    }
  ]
}
```
