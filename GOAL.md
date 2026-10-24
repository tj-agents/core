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
CI, independent review and delivery remain. Item #473 exists; its helper reported incomplete board
placement because the GitHub POST failed, so board placement has not been claimed.

PR: not opened
Next action: commit the verified authored sources, review the immutable candidate and open the draft PR.

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
      "verification": {"level": "planned", "result": "pending", "evidence": "focused tests and Windows/Linux native CI acceptance"}
    },
    {
      "host": "codex",
      "behavior": "discovers generated payloads and verifies snapshots using the new self-exclusion",
      "source": ".agents/plugins/manifests/codex/machine.json",
      "mapping": "plugins/machine/.codex-plugin/plugin.json, hooks/codex.json and packages.json",
      "verification": {"level": "planned", "result": "pending", "evidence": "focused snapshot tests and Windows/Linux native CI acceptance"}
    }
  ]
}
```
