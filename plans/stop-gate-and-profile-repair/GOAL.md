# Stop gate and profile repair

Bounded side workstream launched 2026-10-13 from the `sandbox-dotnet` Claude session (`fed1d447`), which keeps
its own goal and checkout. This successor owns only this goal.

## Authorization

- Standing standards-defect default in `engineering:session-guidance` § "Maintain the right source owner":
  implement, test, open the PR and merge in `tj-agents/core` once its gates pass.
- Tommy, 2026-10-13, explicitly: launch this one repair session, and fix the plugin naming in his profile.
- Limit: Tommy said launch no extra CLI sessions — this is the only one. Do not launch further sessions,
  schedulers or `claude -p` children.
- Not covered: Azure writes, edits to `tj-agents/dotnet`, other employer-repository edits, publishing elsewhere.
- Tommy, 2026-10-13: approved all 15 employer-local settings files in `MIGRATION_PREVIEW.md`;
  add the 45 equivalent C++ false flags while preserving all existing choices.

## Checkout

`C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-StopGateAndProfileRepair`, branch
`Fix/StopGateFailures` from verified parent `Docs/StopGateOwnership`
`cdd71edd394e5a8afdb4fe0c94fffa75e57eb79d` (PR #236), based on remote main `c95b899fc8119a37dfbde1b25d9e34bacbc3c265`.
The same foreground owner continues this goal across its sequential delivery slices.

- PR: not opened.

## Defects

### D1 — agents stop with unfinished, unblocked work

Tommy's rule, in his words: if you stop and there's nothing else to do, close the CLI; if you aren't finished,
don't stop. The only reasons to stay open are actively working, asking a question, or owning a background
wait. He had to ask "are we finished?" — that message is the failure.

- `engineering:session-guidance` lines 99–103: "Stay open while the final message asks the user something
  **or is an answer that exists only in the transcript**". The second clause lets any status report justify
  stopping idle.
- `base:goal-continuation` says keep working and that a gate on one action doesn't end ownership, but nothing
  enforces it. A documented blocker on one part (here, an infra hold) made stopping look legitimate while
  unblocked app work remained.
- Evidence: `sandbox-dotnet` session ended a turn on 2026-10-13 after pushing `c82102c`/`e16fd46`, with no
  entity, migration or database endpoint written, no question asked and no background wait owned.

### D2 — `continuation_stop.py` didn't block that stop

`C:\Users\TommySeery\source\repos\sandbox-dotnet\.agents\continuation\owner.json`: `state: waiting`,
`foreground: null`, `child: null`, no scheduler registered. `outcome()` should reach line 244 and block
("Register and enable the matching persistent-workflow scheduler"), yet the turn ended. Find out why (hook
deadline in `hook_dispatch.py`, receipt/session lookup, or D3's torn install). Even when it fires, its remedy
is "register a scheduler" — wrong when the user forbids extra sessions and unblocked work remains; the remedy
must be "continue the unblocked work, ask, or close".

### D3 — torn engineering plugin install: no Claude skills

`~/.claude/plugins/cache/base-agents/engineering/4090e7d23875`: 208 of the source's 331 files, `skills/`
absent (`.claude-plugin/plugin.json` points at `./skills/`). Source `4090e7d` has 61 Claude skills; the
previous cache `c91b60c955ad` had 61. Written 2026-10-13 00:00:27, around a PC crash. Every Claude session on
it lacks all `engineering:*` skills (`engineering:handoff` returns "Unknown skill"). `base` and `machine` caches
are complete. Reinstall it, and decide whether core should detect a torn package (for example a SessionStart
completeness check that reports it) so this can't silently strip a session again.

### D4 — profile half-migrated to the `tj-agents` marketplace

`~/.claude/settings.json` `enabledPlugins`:

- `dotnet@dotnet` and `react@react` name marketplaces that don't exist; the installed plugins are
  `dotnet@dotagents` and `react@react-agents`. Both are therefore off outside work repos.
- `base`/`engineering`/`machine@base-agents` and `cpp`/`msvc`/`win32@cpp-agents` are legacy; `nvim`/`rust`
  are already `@tj-agents`.
- `tj-agents` (`tj-agents/marketplace`) already serves all of them. Tommy expected this done long ago and
  called the per-repo names redundant.

Converge the profile on `<plugin>@tj-agents`, remove stale legacy marketplaces once nothing references them,
and fix whatever installer or migration in core should have done this so it doesn't recur. Local-scope
`dotnet@dotagents` installs under `infonetica\*` work repos exist; handle them deliberately, don't strand them.

## Out of scope, noted for Tommy

`dotnet:learning` (`tj-agents/dotnet`) defaults to learning mode with an empty `dotnet:knowledge`, treating
Tommy as a .NET beginner. He knows .NET well and said it needs updating at some point. Different repository,
not this goal.

## Completion

- D3: a new Claude session lists the `engineering:*` skills.
- D4: a new Claude session lists `dotnet:*` and `react:*`; `enabledPlugins` uses `@tj-agents` throughout; the
  migration owner is fixed.
- D1/D2: the rule text no longer lets a status report justify stopping, and the Stop gate blocks a turn that
  ends with unblocked authorized work and no question or owned wait — with tests.
- `MISTAKES.md` records the D1 mistake; PRs merged once checks and review pass.
- Report the outcome back to Tommy.

## Lane

Current phase: L4 specified Stop dispatcher and continuation-boundary implementation with focused
regressions. A bounded in-session worker owns runtime/test paths; parent owns goal and delivery.
Independent correctness/workflow review uses L4 after implementation.

## Delivery slices

1. Completed `Fix/StopGateAndProfileRepair`: D3/D4 package health, native cache recovery,
   pinned external sources and opt-in user-profile migration, with focused synthetic profile tests.
   Base: `4090e7d238754b3f1a37cd297142a698129cd3c8`; actual 1,002 substantive code/test lines. The final two-line overage remains atomic with migration safety and its regressions; splitting those would weaken the qualified change.
2. Separate `Docs/StopGateOwnership`: canonical continuation and session-close wording,
   retaining published four-field blocker and `Paused:` formats. Base: updated remote main after slice 1.
3. Current `Fix/StopGateFailures`: fail-closed Stop dispatch and blocker-boundary enforcement,
   with real missing-import, deadline and continuation regressions. Parent: PR #236 at `cdd71edd394e5a8afdb4fe0c94fffa75e57eb79d`.
   Expected fewer than 400 substantive code/test lines; review the child delta and validate the cumulative tree.
   The parent cannot merge automatically because `published-contract` is a recorded stop class. Proceeding
   as a stack completes authorized unblocked repair before the final concrete human delivery decision.
   Land bottom-up; retarget/reconcile the child after the parent lands.

Each slice requires independent review, Windows/Linux CI and its own guarded merge. No new CLI
sessions or schedulers are required; this foreground owner continues across the slices.

## Next Steps

The Stop runtime repair and its 54 focused tests pass, along with required generation and packaging.
Review the immutable child candidate, publish it against PR #236's branch and own exact-head CI.
Finish authorized preparation before the remaining concrete delivery and host-acceptance decisions.

Scope: whole plan through all remaining phases and terminal delivery.
Current slice: D2 Stop dispatcher/continuation enforcement, stacked on the human-gated ownership wording.
Remaining scope: parent/child delivery; fresh-host acceptance within Tommy's session limit.
Done when: all authorized repairs are verified and merged, with any genuine capability boundary recorded.

## Agent-host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/machine/scripts/claude_standards_sync.py; .agents/hooks/hook_dispatch.py; .agents/hooks/continuation_stop.py; canonical continuation contracts",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Verify enabled plugin payloads and pinned sources before launch; prevent incomplete active goals from stopping through failed gates.",
      "source": ".agents/machine/scripts/claude_standards_sync.py; .agents/hooks/continuation_stop.py; .agents/hooks/hook_dispatch.py",
      "mapping": "Machine launcher sync plus .agents/plugins/manifests/claude/engineering-hooks.json Stop dispatch and shared SessionStart contracts.",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "23 dispatcher and 31 continuation tests passed, including real missing-import failure, both host event spellings, deadline and blocker-boundary cases; generated-tree, harness and packaging checks passed. Fresh-host acceptance remains unobserved under the session limit."
      }
    },
    {
      "host": "codex",
      "behavior": "Use shared continuation and Stop recovery contracts while retaining the separate native Codex marketplace synchronization owner.",
      "source": ".agents/hooks/continuation_stop.py; .agents/hooks/hook_dispatch.py; .agents/base/policy/goal-continuation/SKILL.md",
      "mapping": ".agents/plugins/manifests/codex/engineering-hooks.json and generated authenticated hook snapshots; Claude profile migration has no Codex profile mutation.",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "23 dispatcher and 31 continuation tests passed, including real missing-import failure, both host event spellings, deadline and blocker-boundary cases; generated-tree, harness and packaging checks passed. Fresh-host acceptance remains unobserved under the session limit."
      }
    }
  ]
}
```

## Progress

- One Codex successor owns the promoted goal. No extra CLI sessions, schedulers or prompt children
  were launched. Bounded in-session workers preserve this single owner.
- Assessment complete: reuse native Claude commands and the existing sync owner, add bounded payload
  checks and opt-in alias migration; bootstrap remains the locked-profile digest owner. Preserve pinned
  subdirectory refs and existing project/local installations.
- D2 cause: the original Stop attachment lacked `workflow_route` and `worktree_cleanup_gate.py`.
  Dispatcher returned success with empty stdout after 1,584 ms. The incident was not a deadline overrun.
- Live D3/D4: eight healthy user packages are enabled at `@tj-agents`, with mapped legacy preferences
  absent. Engineering has 52 complete skills at published `v2.1.15`, rather than 61 at damaged main.
  Consolidated marketplace pins remain authoritative; no marketplace source repository was edited.
- Tommy approved all 15 employer-local files and 45 C++ false flags in `MIGRATION_PREVIEW.md`.
  Exactly those additions were verified against backups; all other values were preserved. Native user
  C++ migration returned zero, keeping scoped legacy installs/marketplaces while they remain referenced.
- Fresh-session loading and adoption of these source changes by installed pinned packages are unobserved
  under the explicit no-extra-session limit. Native registry/payload checks passed for all eight packages.
- D3/D4 source: PR #235 merged reviewed head `9690bff537e90f82c3c3a562c1ffa54a57c334e0` at
  `8b33980747476f9369c1b39497908226c2990b21`; exact-head Windows/Linux CI `38336373168` passed.
  All ten review findings were resolved. Causal main CI/regeneration `38337890284` passed.
- Parent PR #236: `cdd71edd394e5a8afdb4fe0c94fffa75e57eb79d`, independent native/contract/workflow
  review approved in `reviews/Docs-StopGateOwnership.md`; frozen reference checks had no errors/warnings.
  Exact-head CI `38339400959` is owned by the foreground monitor. The binder reserves the changed
  `contract/plan-checkpoint` path under the published-contract stop class; standing authority exempts
  only auth. This gates automatic parent delivery, not authorized child preparation.
- Child implementation: Stop nonzero exits and missing deadline verdicts fail closed, preserving sibling
  reasons/context; documented blockers reject trailing actionable tasks and unsupported budget/capability
  shortcuts. Four-field/Paused compatibility, completion, explicit controls and scheduler checks remain.
- Child verification: 23 dispatcher and 31 continuation tests passed, including real missing-import,
  deadline, both-host payload and boundary regressions. Catalog generation, generated-tree checks,
  three harness validators and skill packaging passed. No generated distribution output is committed.
- Harness extra roots must be mapped shipped resources; skill definitions are already covered by canonical
  scope roots. The runtime slice declares existing shared enforcement resources and keeps all schemas.
- Incident B008 is resolved by PR #235. B009 and M015 remain owned by this goal until runtime delivery
  and whole-goal acceptance. Their retired branch qualifiers were reconciled in this substantive slice.
