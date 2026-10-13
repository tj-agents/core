# Stop gate and profile repair

Bounded side workstream launched 2026-10-13 from the `sandbox-dotnet` Claude session (`fed1d447`), which keeps
its own goal and checkout. This successor owns only this goal.

## Authorization

- Standing standards-defect default in `engineering:session-guidance` § "Maintain the right source owner":
  implement, test, open the PR and merge in `tj-agents/core` once its gates pass.
- Tommy, 2026-10-13, explicitly: launch this one repair session, and fix the plugin naming in his profile.
- Limit: Tommy said launch no extra CLI sessions — this is the only one. Do not launch further sessions,
  schedulers or `claude -p` children.
- Not covered: Azure writes, edits to `tj-agents/dotnet` or employer repositories, publishing elsewhere.

## Checkout

`C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-StopGateAndProfileRepair`, branch
`Fix/StopGateAndProfileRepair` from `origin/main` `4090e7d`. Split into PR-sized slices under
`engineering:git-branching` if the defects don't belong in one diff.

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

L3: open investigation (D2) and bounded design (D1 enforcement) with unresolved alternatives.

## Delivery slices

1. Current `Fix/StopGateAndProfileRepair`: D3/D4 package health, native cache recovery,
   pinned external sources and opt-in user-profile migration, with focused synthetic profile tests.
   Base: `4090e7d238754b3f1a37cd297142a698129cd3c8`; expected fewer than 1,000 code/test lines.
2. Separate `Docs/StopGateOwnership`: canonical continuation and session-close wording,
   retaining published four-field blocker and `Paused:` formats. Base: updated remote main after slice 1.
3. Separate `Fix/StopGateFailures`: fail-closed Stop dispatch and blocker-boundary enforcement,
   with real missing-import, deadline and continuation regressions. Base: updated main after slice 2.

Each slice requires independent review, Windows/Linux CI and its own guarded merge. No new CLI
sessions or schedulers are required; this foreground owner continues across the slices.

## Next Steps

Finish and verify the profile repair candidate, apply its authorized user-profile migrations,
then commit, independently review and deliver the current slice before starting its successor.
Scoped C++ preference writes remain pending Tommy's answer to `MIGRATION_PREVIEW.md`.

Scope: whole-plan.
Current slice: D3/D4 normal-profile package checks, pinned sources and user alias migration.
Remaining scope: D1 canonical stop ownership wording; D2 dispatcher and continuation enforcement;
scoped C++ decision; installed-host acceptance within the no-additional-session limit.
Done when: all authorized repairs are verified and merged, with any genuine scope or capability
boundary recorded against the same goal.
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

- 2026-10-13: goal written and launched by the `sandbox-dotnet` session.
- 2026-10-13: Codex successor acknowledged pickup in the named checkout. D3 verified:
  the registered engineering cache has no `skills/` directory. D4 verified: user settings enable
  nonexistent `dotnet@dotnet` and `react@react` identities; scoped legacy installs remain registered.
  Investigation uses L3 for unresolved stop-gate and migration behavior. No further CLI sessions,
  schedulers or prompt children will be launched; bounded in-session workers retain this goal owner.
- D2 cause confirmed from the original Stop attachment: `continuation_stop.py` and
  `callout_repair_gate.py` could not import the missing `workflow_route`; `worktree_cleanup_gate.py`
  was missing. The dispatcher returned success and no blocking verdict. The original duration was
  1,584 ms, ruling out its deadline as this incident's cause.
- D3 recovery: native `engineering@tj-agents` install succeeded with 52 complete skills at the
  consolidated catalog's published `v2.1.15` pin. The damaged main install expected 61. Native
  user installs for base/machine/C++/.NET/React also succeeded. Fresh session loading cannot be
  claimed without violating the no-additional-CLI-session limit; verify native registry and payload
  now, retain fresh-session acceptance as a capability limit.
- D4 scope: work-repository local settings disable the legacy C++ identities. New unified C++
  identities were disabled immediately to preserve those choices. The exact proposed equivalents
  are in `MIGRATION_PREVIEW.md`; scoped writes await Tommy's answer. Legacy marketplaces remain
  while project/local records reference them. Source migration must preserve explicit disabled
  choices and defer aliases whose scoped overrides cannot be safely preserved.
- Assessment complete: reuse native Claude plugin commands and existing sync owner; add bounded
  package checks and opt-in alias migration rather than a second installer. Existing bootstrap
  remains the full digest verifier for locked profiles. Official Claude plugin docs and the local
  CLI help confirm plugin scope/native install semantics. Preserve each git-subdir source ref.
- Implementation phase selected L4: specified sync/integrity changes with synthetic regression
  coverage; bounded in-session worker owns only sync code and its fixtures/tests.
- Profile checkpoint: 27 synchronization tests and plugin packaging passed. Authorized user aliases
  for base/machine/.NET/React migrated through the tested source helper; engineering was already
  repaired. All five canonical user packages passed declared-payload checks. The C++ aliases remain
  deliberately deferred pending the 15 scoped settings equivalents; unrelated settings and registry
  scopes were preserved. No fresh host session was launched.
