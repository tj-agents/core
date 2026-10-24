# Standards currency, native messaging and host naming

Authorized by the 24 October 2026 handoff in `core-standards-messaging-handoff.txt`.
Owner: Codex session 01a16f6f-fa83-7c81-b911-3238508dd489.
Checkout: C:/Users/tommy/source/repos/tj-agents/core/.worktrees/Fix-StandardsMessaging.
Branch: Fix/StandardsMessaging. Baseline: 5a64d9bb.
Scope: investigate and repair demonstrated Core defects, validate, review and deliver.
Core's `.github/merge-policy.json` requires Tommy to merge. No Sandbox writes or messages.
Lane: L3 investigation/design; L4 specified implementation and review.

## Ownership and capability

PR 463 / Fix/AutomaticRefreshContinuation has a verified live native owner,
01a16f30-e5bf-75d1-8fe3-7e7c74e77f0a. Its source and checkout remain exclusively owned.
The historical followup-recovery goal describes PR 207; it does not establish a new writer lease.
One exact-owner coordination attempt timed out before sending, with no receipt. Do not retry,
resume that live owner or interpret this as release. Independent investigation continues here.

## Evidence and decisions

- Sandbox's original CLI transcript contains the stale digest warning as developer context at
  19:22:24 UTC, matching the earlier VS Code session's warning at 18:11:44 UTC.
- Installed `agents/concertable/local/standards-manifest.json` has exactly loaded digest
  a82665525f0517502a295a2ea7d5692d2af4c5742bfc6a0efa1d9501fc52875e.
  Both original session currency proofs record published digest
  9c278dacf4c10191c99df0d627b795a83ddb8ae17c55437718e48f70faf794ae,
  `session_status: stale`, `writes_allowed: false`, source `origin-main-authenticated`.
- The emitting owner is Concertable's `hooks/always_on_instructions.py`: `_standards_root` accepts
  any `.agents/skill-routes.json`, then `verify_session` compares that plugin's manifest against
  Concertable/agents main and injects `report`. Its write router consumes the session proof.
  This is a Concertable digest, not a digest of Core's selected packages.
- Sandbox's declared plugin selection excludes Concertable. A globally active legacy Concertable
  hook treats its unrelated routes as opt-in; it does not check this selection. This explains why
  the warning appeared there. The useful integrity gate need not be weakened to correct that scope.
- Core `startup_binding.main` checks required packages, then `launch_check`, then starts the native
  process; updates precede SessionStart on that path. `reload_plugins.selection` explicitly filters
  publishers to tj-agents. Its successful selected-package refresh cannot update this Concertable
  manifest. Historical launch-path use and exact publication timing are unproven; neither a
  Core publish-after-start race nor a Core startup-order defect explains the identified digest.
- The prior agent overlooked `machine:sync-plugins`' clear instruction to run refresh itself.
  That behavioral mistake needs no duplicate rule. Its later claim that a Core snapshot caused
  the warning was unsupported; the warning alone did not establish that source attribution.
- Current Core's Windows handoff launcher explicitly selects `--no-daemon` for Codex >=0.157;
  native 0.164 help says that bypasses even an existing shared server. Follow-up needs that server.
- Existing receipt safeguards and exact-owner recovery remain useful and must be preserved.
- Naming recommendation: Machine continues to own cross-host native operations. Target-specific
  suffixes distinguish destinations; creating Codex/Claude packages solely for prefixes is unjustified.
  No aliases or migration will be introduced without a demonstrated boundary benefit.

## Implemented bounded slice

Extend the existing Machine follow-up helper with `probe`. It shares the exact send preconditions,
returns `reachable` only for a loaded exact recipient with direct input and an unambiguous permitted
turn state, and performs no turn mutation, receipt reservation, thread load or recovery. An actual
send rechecks everything. The skill identifies Windows launch isolation, the absence of an independent
Claude messaging equivalent, and continued task ownership when transport is unavailable. Its no-send
advice no longer requires making the user paste a message.

This is a capability improvement and a recovery-guidance correction, not restoration of live transport.
No new daemon, replacement writer, user-profile change, consumer installation or Sandbox action occurred.

Machine remains the correct owning package: either host can operate either target. `codex:` and
`claude:` would be real plugin namespaces, not display aliases under the current generator. A future
approved split would require two selectable manifests/catalog/harness entries, both host adapters,
self-contained helpers/resources, marketplace registrations and migration of Workflow handoffs,
Machine recovery/open utilities, Engineering references and actual project selections. All known
callers and fresh host loading would have to cut over together; Personal forbids speculative aliases.
PR 455 already owns per-plugin generator name scoping; do not duplicate that implementation here.

## Verification and remaining limits

- 36 focused follow-up tests pass, including active/idle probes, wrong identities/directories,
  unloaded recipients, missing direct input, unsupported states, ambiguous turns, transport failure,
  no file/input side effects and revalidation after a successful observation.
- Native Codex 0.164 experimental schema generation retains the helper's direct-input, expected-turn,
  client-message-id and paginated-history APIs. This establishes protocol shape, not live delivery.
- The new source probe against the exact live Core owner returned unavailable after five seconds,
  without a receipt or input. The earlier authorized send attempt also created no receipt.
- Claude native CLI help has no independent-session message command; Core ships no equivalent.
  Same-conversation collaboration remains a different capability. No claim about all external APIs.
- Generated source/catalog/harness checks and PowerShell packaging checks pass. All 46 source-layout
  and harness-manifest tests pass. No consumer installation or Linux native host acceptance is claimed.
- Concertable scope correction requires authorization for its separate owning source. Core-only
  changes cannot truthfully claim that this stale warning is repaired. Resolver: Tommy authorizes
  that source investigation; acceptance: an unrelated selected project receives no Concertable
  context/gate, while an opted-in Concertable project retains manifest-integrity enforcement.

## Next Steps

1. Complete packaging validation and freeze the bounded helper/guidance candidate.
2. Run independent native review and exact-head Windows/Linux CI; open a concrete PR.
   Record the owner merge gate and unverified native entry points precisely.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/machine/utility/followup-codex/SKILL.md",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Assess exact Codex recipient reachability without creating a writer",
      "source": ".claude/skills/followup-codex/SKILL.md",
      "mapping": ".agents/plugins/sources.json machine adapter mapping",
      "verification": {"level": "source", "result": "passed", "evidence": "36 helper tests, 46 layout/harness tests and packaging checks; generated Claude helper included"}
    },
    {
      "host": "codex",
      "behavior": "Assess exact Codex recipient reachability without creating a writer",
      "source": ".codex/skills/followup-codex/SKILL.md",
      "mapping": ".agents/plugins/sources.json machine adapter mapping",
      "verification": {"level": "source", "result": "passed", "evidence": "36 helper tests, 46 layout/harness tests, packaging checks and native unavailable-probe observation"}
    }
  ]
}
```
