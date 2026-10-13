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
`Docs/StopGateOwnership` from remote main `c95b899fc8119a37dfbde1b25d9e34bacbc3c265`.
The same foreground owner continues this goal across its sequential delivery slices.

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

Current phase: L5 mechanical guidance implementation; the exact ownership, blocker and session-close
wording is resolved. Bounded in-session worker applies it; parent owns goal, verification and transitions.
Review reselects L4 for ordinary correctness and workflow judgment.

## Delivery slices

1. Completed `Fix/StopGateAndProfileRepair`: D3/D4 package health, native cache recovery,
   pinned external sources and opt-in user-profile migration, with focused synthetic profile tests.
   Base: `4090e7d238754b3f1a37cd297142a698129cd3c8`; actual 1,002 substantive code/test lines. The final two-line overage remains atomic with migration safety and its regressions; splitting those would weaken the qualified change.
2. Separate `Docs/StopGateOwnership`: canonical continuation and session-close wording,
   retaining published four-field blocker and `Paused:` formats. Base: updated remote main after slice 1.
3. Separate `Fix/StopGateFailures`: fail-closed Stop dispatch and blocker-boundary enforcement,
   with real missing-import, deadline and continuation regressions. Base: updated main after slice 2.

Each slice requires independent review, Windows/Linux CI and its own guarded merge. No new CLI
sessions or schedulers are required; this foreground owner continues across the slices.

## Next Steps

Ownership wording and supported harness declarations are implemented and packaging checks pass.
Review the immutable candidate, deliver this slice, then implement the Stop runtime slice.

Scope: whole plan through all remaining phases and terminal delivery.
Current slice: D1 canonical continuation, blocker and session-close wording.
Remaining scope: D2 Stop dispatcher/continuation enforcement; fresh-host acceptance within Tommy's session limit.
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
        "level": "planned",
        "result": "pending",
        "evidence": "Synthetic native-plugin fixtures, missing-import Stop reproduction, continuation boundary tests and payload inspection; fresh CLI acceptance restricted by the explicit no-additional-session instruction."
      }
    },
    {
      "host": "codex",
      "behavior": "Use shared continuation and Stop recovery contracts while retaining the separate native Codex marketplace synchronization owner.",
      "source": ".agents/hooks/continuation_stop.py; .agents/hooks/hook_dispatch.py; .agents/base/policy/goal-continuation/SKILL.md",
      "mapping": ".agents/plugins/manifests/codex/engineering-hooks.json and generated authenticated hook snapshots; Claude profile migration has no Codex profile mutation.",
      "verification": {
        "level": "planned",
        "result": "pending",
        "evidence": "Shared dispatcher/continuation regression tests with both host payload spellings and existing Codex synchronization consumer tests."
      }
    }
  ]
}
```

## Progress

- Pickup: this Codex successor owns the promoted goal in the named checkout. No further CLI sessions,
  schedulers or prompt children have been launched; bounded in-session workers preserve one goal owner.
- Assessment complete: reuse native Claude commands and the existing sync owner, adding bounded
  payload checks and opt-in alias migration. Bootstrap remains the locked-profile digest owner.
  Native CLI help and official plugin documentation establish scope/install semantics; preserve subdir refs.
- D2 cause: original Stop attachment lacked `workflow_route` and `worktree_cleanup_gate.py`.
  Dispatcher returned success without a block after 1,584 ms; this incident was not a deadline overrun.
- Live D3/D4 repair: base/engineering/machine/cpp/msvc/win32/dotnet/react user packages are healthy
  and enabled at `@tj-agents`; all mapped legacy user preference aliases are absent. Engineering has
  52 complete skills at the consolidated catalog's published `v2.1.15`, rather than 61 at damaged main.
  Consolidated marketplace pins remain authoritative; no marketplace source repository was edited.
- Tommy approved all 15 files and 45 C++ false flags in `MIGRATION_PREVIEW.md`. They were applied
  and independently compared with byte backups: exactly those additions, all other values preserved.
  Native user C++ migration then returned zero; project/local legacy installs and their marketplaces
  remain while scoped references require them. Unrelated profile choices were preserved.
- Fresh-session loading is unobserved under the explicit no-extra-session limit. Native registry and
  declared-payload checks passed for all eight repaired packages; do not claim source changes are adopted
  by the currently pinned installed packages or that a new host session accepted them.
- D3/D4 source delivery: PR #235 merged reviewed head `9690bff537e90f82c3c3a562c1ffa54a57c334e0`
  at `8b33980747476f9369c1b39497908226c2990b21`; exact-head CI `38336373168` passed Windows/Linux.
  Independent native, migration and workflow review approved; all ten findings resolved. Review evidence
  is archived outside the checkout after retirement of the merged branch. No additional CLI was launched.
- Main consequence `38337890284` is owned by the foreground monitor at its exact merge commit.
  Regeneration is the repository's only publication consequence; no external marketplace is published here.
- Validation: original 27 sync, 13 repair and 36 Codex consumer tests passed; focused migration/authentication,
  scope and race checks passed. The final alias-removal regression was reproduced red, then four checks
  passed after correction. Generated/harness/packaging checks passed; full Windows/Linux CI passed.
- Current source slice: `Docs/StopGateOwnership` uses the updated remote base and this same goal owner.
  Preserve four published blocker fields and `Paused:`; exhaust all unblocked authorized work before
  either form can describe the remaining whole goal. Harness declarations identify shipped Stop resources;
  extra skill-file roots were rejected because the mandatory canonical scope roots already ship skills.
- Ownership validation: catalog generation, both-host generated-tree checks, three harness manifests
  and `skill-packaging.tests.ps1` passed. Generated distribution output is excluded from this commit.
