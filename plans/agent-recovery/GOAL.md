# Find and resume agent sessions after a crash

Authorization: Tommy explicitly requested search-codex, open-codex, search-claude, open-claude and recover-agents on 2026-10-08, then made this the new focus. Implement, test, review and deliver these shared machine capabilities through normal personal-repository gates. He continued the previous handoff in Sol; preserve it and do not reopen it.
Checkout: C:/Users/TommySeery/source/repos/tj-agents/core (completed goal promoted from Feature-AgentRecovery)
Branch: Feature/AgentRecovery
Integrated base: ab32149213bf30895f11d85f1bf73c0a09b25317; delivered head: 9a4162621e97da6a6e7610a2e92e143e799a3b6b
PR: https://github.com/tj-agents/core/pull/151 (merged)
Owner: current parent session coordinating one bounded L4 implementation worker. No Astra dispatch is needed for this specified utility work.
Canonical source: .agents/machine/utility for all five skill definitions. Both native hosts discover thin adapters. Shared helpers live in .agents/machine/scripts and ship through existing machine resources. open-claude already exists and must be reused.

Outcome: a user can find a lost top-level Codex/Claude conversation by topic, title, ID or checkout, see which work it concerns and whether it is live, then reopen that exact session in its native TUI with an instruction to continue. recover-agents coordinates the two search/open pairs for the relevant chosen scope without duplicating running agents or resuming helper/subagent sessions.

Implementation boundary: reuse history.py, agent_cli.py, register_session.py process identity helpers and existing supported startup sync. Do not create a second history database or a copy of the recovery vault, modify credentials, weaken permissions/hook trust or reopen unrelated historical work. PR137 owns the handoff-codex Python port: preserve its shared launch code and use narrow new callers around existing primitives.

Specified behavior:
- Search includes saved histories, archived Codex sessions where supported, and registry titles. Return bounded metadata with exact native session ID, host, original cwd, branch, activity, useful preview, profile and live/closed/unknown status; raw transcripts stay local. Validate IDs and exclude non-top-level/helper sessions. Search works after a crash; profiles are inputs, not copied secrets.
- open-codex uses existing native executable discovery and terminal launch primitives, verifies native resume arguments locally, supports exact resume and a continuation prompt/file. No npm shim or intermediate interactive shell. Existing open-claude gets only necessary shared resume/live safeguards.
- Resolve session identity and original cwd from history before resuming. Guard verified live sessions using PID plus start time and current-session identity. Unknown/conflicting liveness is reported and reconciled rather than silently creating a second writer. Serialize same-session launch requests and preserve an ambiguous terminal-launch result instead of blindly retrying.
- recover-agents first inventories the requested topic/checkout/scope across both hosts, groups candidates and exposes the search/open operations. It resumes only explicitly selected relevant sessions, carrying a concise continue-work instruction and the native session context. Do not guess unfinished status from a final response or open every historical session. For a user asking to recover relevant work, inspect available canonical goals/PR state and select the applicable sessions; ask only if identity is truly ambiguous.
- Define concise, discoverable shared skills; thin .codex/.claude adapters only reference canonical definitions. Generated plugins remain outside commits.

Delivery: one focused slice, target below roughly1000 substantive code/test lines, with a concrete size assessment if it grows. Meaningful synthetic tests cover profile/scope/topic matching, helper exclusion, stale/PID-reused and live records, exact resume argv/cwd, quoted paths, duplicate requests, ambiguous launch and missing history/session. Validate shipped package layouts and CLI help. No real private transcripts enter tests. Parent owns review/PR/CI/merge and goal updates; worker owns specified production/test changes only.

## Next Steps

1. Dispatch the bounded L4 implementation now. Record actual code/test progress here; avoid another design/monitor-only cycle.
2. Verify targeted tests, generated/harness checks and synthetic end-to-end search/resume behavior. Qualify actual history search read-only; launch a harmless native fixture only if needed and distinctly titled.
3. Commit the working capability, obtain fresh bounded review, open its focused PR, monitor exact-head CI and merge. Ship/install by the supported plugin update path and verify discovery in both hosts.
4. Record RESULT.md with implemented behavior, tests, PR/merge and observed native limits. Preserve the unrelated previous grant goal and Sol-owned handoff.

## Implementation checkpoint â€” 2026-10-08

The bounded L4 worker is implementing the shared helper and adapters. Elevated transport is working after one corrected invocation. Parent verified the unchanged shared primitives: 77 agent_cli tests (11 platform skips) and 19 history tests passed. The existing goal is bound to durable owner 7d77d5dd0479fc26a0cbc058; foreground owns it while implementation proceeds. Previous grant work remains preserved and released.


## Acceptance repair checkpoint

First candidate is not yet acceptable. It passed five narrow helper tests, but parent inspection found missing native sibling archive/title search, incorrect alternate-profile launch handling, a duplicate-launch race while SessionStart registration is delayed, and existing open-claude resume bypassing the shared guard. The same L4 writer is repairing these specified boundaries and adding meaningful regressions before commit. No PR or delivery claim has been made.

The missing shared recovery capability was identified by Tommy's lost-session callout. Selected engineering session-guidance supplies standing source-owner repair authority through tested/reviewed PR and merge in this repository. The requested usable machine recovery skills authorize supported local installation; no consuming repository selections or credentials are changed.


## Fixed candidate checkpoint

The shared helper and all five canonical skills now have both host entries. Protected exact Claude resumes reuse the shared guard; normal fresh/continue launch behavior remains covered. The parent confirmed and repaired five review findings, including native thread_name and tab-title matching, stable native exception identities, cross-process receipt retirement, selected-profile startup sync, and selection validation before side effects. Partial recovery keeps already-opened identities visible and preserves timeout exit3.

Local validation: focused recovery/open-claude/history/agent-cli run exercised136 tests with12 platform skips; the final boundary regression exercised60 tests with1 skip. Generated package checks, installed resource loading, packaging and harness inventory passed. Read-only native search found this current top-level Codex session at its original cwd/profile with status live. No real historical agent was reopened, and the Sol-owned previous handoff was preserved.

Review limitation: native Spark is unsupported by this account; native fallback could not execute local reads. Automatic approval review rejected an artifact-fed external native review for source transmission. The permitted parent fallback and a fresh internal behavior lens supplied the review; five concrete findings were recorded in reviews/Feature-AgentRecovery.md and are undergoing final incremental verification. No external native source payload was sent by the rejected action.

Next action: commit the stable repair, freeze the delta, complete fresh incremental review, publish the focused PR and bind exact-head CI. Current source/test size remains one coherent search/resume capability below1000 substantive implementation/test lines; both host guards and their regression coverage remain atomic.

## Delivery checkpoint — PR151

The stable candidate is published at https://github.com/tj-agents/core/pull/151, head1b6557c8f15b9141694c356e6dc4358f4a849a37. Main was synchronized before the final fresh full-source review. Generated distribution files are excluded from the PR; source guard and published What/Why body check passed. Exact-head CI is owned by workflow monitor recovery-pr151 and durable owner7d77d5dd0479fc26a0cbc058. Final internal review, merge, post-merge regeneration and supported installed-host verification remain before completion. Native review rejection remains accurately recorded above.


## CI inventory correction

Run37786935860 on head1b6557c8f15b9141694c356e6dc4358f4a849a37 completed695 tests with12 skips and one failure: the historical exact skill count69 needed73 after four additions. The one-line correction is committed and pushed at beac6a19843ec9770d252fbf4c90dafdf8ec2a17. All19 affected source-layout tests passed locally. Its frozen incremental review is approved; run37791963848 owns the corrected exact-head CI wait. Local PowerShell command execution was delayed; the native Windows command shell is working.


## Integrated launcher checkpoint

The corrected beac6a1 head passed its full CI run37791963848. PR148 then changed shared agent_cli resolution and the catalog while validation ran. Main was integrated to keep recovery compatible; current published head is 9a4162621e97da6a6e7610a2e92e143e799a3b6b. Combined local137 tests passed with12 platform skips; generated/harness/source guards passed. Fresh frozen review is finishing; this integrated head still requires its own green CI before merge. Use shell cmd.exe with login:false and require_escalated for this checkout; for PowerShell scripts call powershell.exe or pwsh explicitly with -NoProfile.

Next: finish this frozen review, rebind exact-head CI, mark the authoritative PR CI task complete only after green, verify main currency, and merge through the required quoted pushd envelope using shell pwsh.exe. Follow only the regenerate job causally triggered by PR151 landing, use the supported Codex/Claude plugin update paths, verify all five installed skills/resources and read-only native search. Do not reopen the unrelated Sol-owned grant handoff. Complete acceptance evidence/RESULT.md, release this owner/scheduler and preserve the final goal in the primary checkout before retiring this feature checkout.


## Merged delivery checkpoint

PR151 merged at6c56b76f2103f7e4b6365b78921cc9f04375494f after exact-head CI run37798028254 passed. Current owner is following causal main regeneration run37801166276, then will update both installed plugins through supported native paths and inspect all five skill entries/resources. Installation remains pending.


## Completed delivery

PR151 is merged and supported plugin updates expose all five skills in both installed hosts. Actual resource imports, CLI help and read-only native history search passed. RESULT.md records evidence and review limits. No historical session was reopened.

```completion
{
  "outcome": "Both Codex and Claude can search and recover exact native sessions through five shared skills.",
  "acceptance": [
    {
      "id": "shared-source",
      "criterion": "All five skills have canonical shared definitions and thin entries for both hosts.",
      "evidence": [
        {
          "source": "PR151 head1b6557c8f15b9141694c356e6dc4358f4a849a37",
          "result": "Canonical .agents/machine/utility definitions and both host entries are committed."
        }
      ],
      "owner": "root",
      "next_action": ""
    },
    {
      "id": "validation",
      "criterion": "Focused recovery, concurrency, profile and package checks pass.",
      "evidence": [
        {
          "source": "https://github.com/tj-agents/core/actions/runs/37798028254",
          "result": "Whole exact-head CI passed; local integrated137 tests passed with12 platform skips, including protected resume and package resource checks."
        }
      ],
      "owner": "root",
      "next_action": ""
    },
    {
      "id": "delivery",
      "criterion": "PR151 reviewed and merged with exact-head CI green.",
      "evidence": [
        {
          "source": "https://github.com/tj-agents/core/pull/151",
          "result": "Merged at 6c56b76f2103f7e4b6365b78921cc9f04375494f; integrated head9a4162621e97da6a6e7610a2e92e143e799a3b6b approved and CI run37798028254 succeeded."
        }
      ],
      "owner": "root",
      "next_action": ""
    },
    {
      "id": "installed-hosts",
      "criterion": "The generated machine plugin exposes all five skills and helper in both installed hosts.",
      "evidence": [
        {
          "source": "plans/agent-recovery/RESULT.md installed package evidence",
          "result": "Supported plugin updates completed; all five skill files, packaged resource imports and CLI help verified in both installed hosts. Claude packaged helper found current top-level native Codex session with original cwd/profile and live status."
        }
      ],
      "owner": "root",
      "next_action": ""
    }
  ],
  "deliveries": [
    {
      "repository": "tj-agents/core",
      "pr": 151,
      "head": "9a4162621e97da6a6e7610a2e92e143e799a3b6b"
    }
  ],
  "open_tasks": []
}
```
