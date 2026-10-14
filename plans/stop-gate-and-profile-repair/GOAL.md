# Stop gate and profile repair

Bounded side workstream launched 2026-10-13 from the `sandbox-dotnet` Claude session (`fed1d447`), which keeps
its own goal and checkout. This successor owns only this goal.

## Authorization

- Standing standards-defect default in `engineering:session-guidance` § "Maintain the right source owner":
  implement, test, open the PR and merge in `tj-agents/core` once its gates pass.
- Tommy, 2026-10-13, explicitly: launch this one repair session, and fix the plugin naming in his profile.
- Exception consumed: Tommy explicitly approved exactly one bounded fresh Claude acceptance session; it passed with zero subagents. No further sessions are authorized.
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

- PR: [#237](https://github.com/tj-agents/core/pull/237), reviewed head `7d6f49a0c50fa9b9aefc11055a48f8a4b616daf1`, retargeted to main after parent merge.

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

Current phase: L7 delivery mechanics owned by this foreground workflow parent. L4 implementation and
independent correctness/workflow review are complete; the fixing head is approved. No model switch
is claimed. This existing Codex process owns the remaining exact CI and goal closeout.

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

Complete. All three repair PRs are merged. Required Windows/Linux checks and causal regeneration passed. No authorized repair tasks remain. The original sandbox application goal remains with its original owner.

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
        "evidence": "23 dispatcher and 31 continuation tests passed, including real missing-import failure, both host event spellings, deadline and blocker-boundary cases; generated-tree, harness and packaging checks passed. The one approved Claude profile-loading acceptance passed; adoption of the new Stop source by installed pins remains unobserved."
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
        "evidence": "23 dispatcher and 31 continuation tests passed, including real missing-import failure, both host event spellings, deadline and blocker-boundary cases; generated-tree, harness and packaging checks passed. The one approved Claude profile-loading acceptance passed; adoption of the new Stop source by installed pins remains unobserved."
      }
    }
  ]
}
```

## Progress

- One Codex successor owns the promoted goal. Exactly one explicitly approved fresh Claude acceptance session ran; no scheduler or other extra CLI session was launched. Bounded in-session workers preserve this single owner.
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
- One explicitly approved fresh Claude session passed on 2026-10-13, listing engineering/dotnet/react
  skills; exit zero, one turn, zero subagents. Installed pinned packages remain separate from new source
  adoption. Native registry/payload checks passed for all eight packages.
- D3/D4 source: PR #235 merged reviewed head `9690bff537e90f82c3c3a562c1ffa54a57c334e0` at
  `8b33980747476f9369c1b39497908226c2990b21`; exact-head Windows/Linux CI `38336373168` passed.
  All ten review findings were resolved. Causal main CI/regeneration `38337890284` passed.
- Parent PR #236: `cdd71edd394e5a8afdb4fe0c94fffa75e57eb79d`, independent native/contract/workflow
  review approved in `reviews/Docs-StopGateOwnership.md`; frozen reference checks had no errors/warnings.
  Exact-head Windows/Linux CI `38339400959` passed. The binder reserves the changed
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

- Child review at `c4c268a` completed changes-requested with one deduplicated finding R1: require
  complete unique metadata for extended blocker/Paused forms; preserve the unextended four-field
  legacy blocker. The predicate/test repair passed 31 focused tests and independent incremental review at `7d6f49a`.

- Tommy approved ordinary foreground merge of PR #236 and exactly one bounded fresh Claude acceptance
  session. Parent merged `cdd71edd` at `19b91b83835ed15783133276b1628b7fa4cc81ba`; exact causal main
  CI `38398869624` is owned. Child PR #237 is retargeted to main; review approved at `7d6f49a`.
- Acceptance session `e5e8b649-7c99-44a0-aa40-9a63da2d7d16` listed three actual engineering, dotnet and
  react skill names each; completed in one turn with zero subagent requests/spawns. No further CLI
  sessions or scheduler are authorized. Evidence: Temp/stop-profile-acceptance-20261013/stdout.json.

- Child exact-head Windows/Linux CI `38398088850` passed; PR #237 is ready. Local continuation owner
  `db620ae4b3d3fd790f89a6b0` is claimed by existing Codex PID 21676, with zero launches and no scheduler.
  Parent causal main CI remains actively monitored; no unattended continuation is claimed.

## Final completion ? 2026-10-13

PR #236 causal run 38398869624 passed. PR #237 merged reviewed head 7d6f49a0c50fa9b9aefc11055a48f8a4b616daf1 as e1fe101a1acd217c360dc02bc734d2f4822ebdab. Its causal run 38401523019 completed successfully, including verify-windows, verify-linux and regenerate. B008, B009 and M015 are resolved for this source repair. The outcome was reported to Tommy. The repaired profile remains at published pins; new Stop runtime adoption by installed marketplace packages was not claimed.

```completion
{
  "outcome": "Profile naming and package recovery repaired; Stop enforcement and continuation contracts fixed; all three repair PRs merged and verified.",
  "acceptance": [
    {
      "id": "D3-D4",
      "criterion": "Fresh Claude loads engineering, dotnet and react skills; canonical user aliases are repaired.",
      "evidence": [
        {
          "source": "Temp/stop-profile-acceptance-20261013/stdout.json; MIGRATION_PREVIEW.md and backed-up profile verification",
          "result": "One fresh approved session exited zero, one turn, zero subagents and listed all three skill families. Eight canonical user packages healthy; all 45 approved local flags preserved scoped opt-outs."
        }
      ],
      "owner": "Root repair session",
      "next_action": "None; verified"
    },
    {
      "id": "D1-D2",
      "criterion": "Stop failures block and contracts require remaining authorized work to continue.",
      "evidence": [
        {
          "source": "PRs 236 and 237; reviews/Docs-StopGateOwnership.md; reviews/Fix-StopGateFailures.md; CI 38401523019",
          "result": "Independent reviews approved; 23 dispatcher and 31 continuation tests passed. Required and causal Windows/Linux CI and regeneration passed."
        }
      ],
      "owner": "Root repair session",
      "next_action": "None; verified"
    },
    {
      "id": "delivery",
      "criterion": "Incident records resolved, repairs merged and outcome reported.",
      "evidence": [
        {
          "source": "BUGS.md B008/B009; MISTAKES.md M015; GitHub PRs 235/236/237; user completion report",
          "result": "All three PRs are MERGED at their reviewed heads. No authorized repair work remains."
        }
      ],
      "owner": "Root repair session",
      "next_action": "None; verified"
    }
  ],
  "deliveries": [
    {
      "repository": "tj-agents/core",
      "pr": 235,
      "head": "9690bff537e90f82c3c3a562c1ffa54a57c334e0"
    },
    {
      "repository": "tj-agents/core",
      "pr": 236,
      "head": "cdd71edd394e5a8afdb4fe0c94fffa75e57eb79d"
    },
    {
      "repository": "tj-agents/core",
      "pr": 237,
      "head": "7d6f49a0c50fa9b9aefc11055a48f8a4b616daf1"
    }
  ],
  "open_tasks": []
}
```
