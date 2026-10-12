# Authenticate the native session's continuation controller

## Outcome and ownership

Implement reciprocal association between a native agent session and its canonical continuation controller so Stop evaluates the actual parent goal when the native event checkout differs. A sparse route receipt or a same-executable PID check cannot establish ownership. Preserve the existing parent lease across bounded side work and require existing release and verified successor pickup for full-goal transfer.

This is the Core-owned implementation plan for the accepted design in the [immutable shared design at Docs commit 0d74933ff0889251f6228c96d81b7553ed95a736](https://github.com/tj-agents/docs/blob/0d74933ff0889251f6228c96d81b7553ed95a736/plans/tj-agents-auto-merge/PLAN.md#selected-parent-continuation-prevention). That section contains the deciding mechanisms and detailed source examples. This Goal records executable scope and acceptance; it does not replace the shared design.

Authorized scope is these seven Core source paths plus this Goal:

- `.agents/workflows/continuation_runtime.py`
- `.agents/hooks/continuation_stop.py`
- `.agents/hooks/tests/test_continuation_runtime.py`
- `.agents/hooks/tests/test_continuation_stop.py`
- `.agents/engineering/workflow/persistent-workflow/SKILL.md`
- `.agents/plugins/harness/engineering.json`
- `tests/test_harness_manifests.py`

The existing shipped harness manifest and its inventory test are included because the skill introduces an `associate-session` command requiring an exact declaration for both hosts. Add only that operation's permission declaration and inventory coverage; retain the existing manifest and packaging. Do not add a helper module, new manifest or another source path. Do not edit owner state by hand, scan for an owner, introduce a daemon, transport, cache, configuration/authorization schema, native `/cd` interface or Linux scheduler adapter. The shared Docs parent remains owned by `/root`; a completed source slice never closes it.

## Authority and execution lifecycle

The authorized rollout requires every agent fix to cover Claude and Codex. This change delivers shared source behavior and equivalent wiring coverage in both native Stop payloads; it does not authorize installing or activating a normal profile, changing billing, credentials, repository protection or visibility, bypassing checks, or adopting another owner's PR.

The heartbeat source phase is terminally reconciled: PR187 merged at `3f07d82322f8fcbfea24158fb0e4aebc1ae05366`, full causal main CI `38092630867` passed, generated commit `b4e6f1020b4c1edcfea8e21d6dae2ba5ebdb8a5e` names the exact parent, and native SID `01a12745-ab05-7d12-8a0c-0d6bfc04ee41` declared heartbeat complete at `2026-10-10T23:31:10.778Z`, explicitly including post-merge regeneration and green CI. This is source-phase closeout, not lease-expiry inference; the old native checkout remains preserved and unadopted, and its stale Goal is not edited. A fresh isolated association writer is therefore eligible.

Before implementation writes, acknowledge transfer with the installed helper `C:/Users/TommySeery/.codex/plugins/cache/base-agents/engineering/2.1.16/.agents/engineering/workflow/handoff/scripts/transfer.py`, using receipt `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-ControllerGoalAssociation/.agents/continuation/controller-association-transfer.json`; read the attempt ID from that receipt and use the exact native SID as successor. First inspect instructions, verify checkout identity and missing association, record nonempty evidence under `.agents/continuation`, then advance the helper. The receipt proves transfer ownership; it is not native enforcement or authorization. The parent prepares, begins and submits the handoff and observes the five-minute pickup window; do not launch a duplicate. If the supported escalated execution path reports a genuine capability gate, record it without retrying a launcher.

Use a fresh meaningful L4 implementation lane for this shared ownership change. Keep the atomic implementation estimate at or below 1,000 changed code, tests and Goal lines (expected about 950); measure it before review. Obtain an exact frozen independent review and required Windows and Linux CI before normal merge. Publish generated output causally after merge and clean only this owned checkout safely. `/root` retains the parent rollout. No normal-profile installation is in scope.

## Contract

Add `associate-session --owner CANONICAL_OWNER --token EXISTING_FOREGROUND_TOKEN --session-id HOST_SESSION_ID --session-cwd NATIVE_EVENT_CWD` to the existing shared continuation runtime. Require the canonical owner/root lock, working state, exact live foreground token, known live PID creation identity and no competing child. Preserve goal, authority, lease and limits. Register one controller per resolved native cwd/session; exact repeat is idempotent, conflicting tuples cannot be forced. Store the lookup locator at `<native-cwd>/.agents/continuation/sessions/<sha256(session-id)>.json` and reciprocal optional owner `session_association`, bound to owner ID/path, repo/worktree/branch/goal, PID/creation identity and SHA-256 token generation. Never expose the raw token. Lock index then owner; write and read back both records before success. Partial publication is failure, preserves the lease and permits same-token/tuple reconciliation. A locator alone carries no authority.

Stop may use the controller only after reciprocal identity and the genuine nearest native CLI PID/creation identity and session boundary are proven. Validate the mutable controller lease and recheck generation at decision time. The controller supplies owner, binding, completion and scheduler checks; retain native cwd/session for user controls. Authentic but invalid controller state gates reconciliation. Stale or unproven pointers preserve local behavior without foreign-owner mutation. Yield/checkpoint marks the association released atomically with foreground release; a new claim invalidates its generation. Bounded side handoff preserves the parent association. Full transfer uses existing release/claim and distinct verified successor pickup. Waiting requires actual foreground/child release, a matching enabled scheduler action and an observed owner-matching wake. Existing pause/cancel controls and supervised-child nonce/result checks remain scoped to the selected owner. Same-user filesystem/hook trust is the boundary; do not claim protection against a user able to rewrite both records.

## Acceptance matrix

All cases use disposable owners and native directories. A rejection leaves owner, lease and foreign state unchanged unless the expected result explicitly requires reconciliation.

| ID | Scenario | Expected result |
|---|---|---|
| P1 | Native root A has unrelated blocked/no-foreground owner; B owns the valid associated parent; route has only `routed_at`. | Stop selects B, blocks premature completion, leaves both owners unchanged. |
| P2 | P1 with missing, malformed non-authoritative or unrelated read-only receipt. | Association still selects B; no route obligation is required. |
| P3 | Bounded side handoff; repeated Stop including `stop_hook_active`; child succeeds or fails pickup. | B's parent claim survives and remains actionable; side progress never completes B. |
| P4 | Register the same valid tuple twice with current token. | Idempotent; token, identity and budget remain unchanged. |
| P5 | Authenticated yield to waiting, no child, current-platform scheduler receipt matches the owner and canonical root, its existing platform verifier confirms it is enabled, and an owner-matching wake is observed. | Stop permits ending on either supported platform only after the existing backend and wake predicates pass. Native Linux acceptance remains limited until verified with an accessible Linux user manager. |
| P6 | Associated complete owner with valid completion versus missing/open-task evidence. | Permit only verified full completion; rejected checkpoint/Stop preserves unfinished ownership. |
| P7 | Genuine blocker and explicit direct Pause/Cancel/Stop, then Status and explicit Resume. | Honor controls and retained suspension; resume enforcement without synthetic completion or foreign mutation. |
| P8 | External absolute goal, same-cwd owner, no association. | Existing supported lifecycle is unchanged. |
| N1 | No association, including fresh local execution and ordinary read-only session. | Preserve local Stop; never search remotely. |
| N2 | Missing reciprocal; forged owner/path/session/cwd/generation; copied pointer in another session. | No foreign adoption or mutation; local fallback. |
| N3 | Wrong token, missing foreground, unknown/dead identity, wrong state or competing child at registration. | Registration fails without changing owner, foreground, goal or index authority. |
| N4 | Unrelated/reused/inaccessible PID identity, nearer foreign CLI, nested same-host or mixed-host session. | No inherited adoption; report unsupported identity proof as a capability limit. |
| N5 | Old index after yield/new claim, recreated owner ID or conflicting registration. | Old generation cannot reach new writer; conflict is explicit, never transfer. |
| N6 | Copied/aliased owner, nested non-Git root, traversal, symlink/junction redirect or path variants. | Require canonical path and true worktree root; normalize Windows while retaining Linux case sensitivity. |
| N7 | Authentic association but changed controller repo/branch/head/binding, missing goal or malformed state. | Reconcile the proven controller; do not fall back to unrelated local owner. |
| N8 | No foreground, missing/deleted lease, held foreground despite scheduler or headless writing child. | Stop blocks; absent lease alone is not release proof. |
| N9 | Released waiting owner with stale/disabled/wrong scheduler or missing/foreign wake. | Stop blocks until existing scheduler and wake gates are met. |
| N10 | Waiting on Linux with a Windows ScheduledTasks receipt, or on Windows with a Linux systemd receipt. | The existing platform dispatcher rejects the mismatched receipt and Stop remains gated. A matching, current-platform receipt follows its existing verifier; add no adapter. |
| N11 | Pause/cancel text is quoted, in task output, another session/cwd, or absent from sparse receipt. | No suspension from indirect text; explicit current-user control retains precedence. |
| N12 | Child nonce/result/owner triple matches or conflicts; side child copies locator/environment. | Existing child exception applies only to selected owner; parent cannot be released/completed through child data. |
| N13 | Concurrent registrations, partial writes/readback failure, eviction or replacement between reads. | No false success, unauthorized target or lease loss; explicit failure and bounded generation reevaluation. |
| N14 | Same native session/cwd after full transfer with old index and successor claim. | Old association is invalid; no predecessor enforcement of successor or inferred transfer completion. |

## Next Steps

A fresh L4 implementation successor owns this side slice because shared ownership and hook ancestry need code-level judgment. Before deliverable writes, acknowledge transfer with the receipt helper and exact session identity above. First verify the checkout identity, inspect the missing association in the current runtime/Stop APIs, and record nonempty source evidence under `.agents/continuation`; then initialize and claim the supported continuation for this side Goal with finite defaults and the native process identity. Register and observe a supported wake before claiming unattended ownership. Do not create or change the Root global owner. Implement the seven-path atomic slice, including the exact installed-relative `python -B ${PLUGIN_ROOT}/workflows/continuation_runtime.py associate-session` declaration for both hosts and its inventory test; run focused Windows and Linux tests plus generation, obtain frozen independent review and both required CI checks, merge normally, publish generated output causally, complete the source Goal through the supported completion JSON/check path, and safely clean only this owned checkout. Reassess the actual size before growing past 1,000 substantive lines; preserve the atomic ownership and permission boundary. The parent prepares/begins/submits and observes the five-minute pickup; no duplicate launch. Handoff, acknowledgement, commit or merge alone does not complete the Goal.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/workflows/continuation_runtime.py and .agents/hooks/continuation_stop.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Authenticate reciprocal native-session/controller ownership before existing Stop completion and lease checks.",
      "source": ".agents/hooks/continuation_stop.py",
      "mapping": "`.agents/plugins/manifests/claude/engineering-hooks.json` wires the Stop entry; `.agents/plugins/harness/engineering.json` declares the shared hook for both hosts and `.agents/plugins/sources.json` maps it to `hooks/continuation_stop.py`. Verify the actual payload and ancestry in isolated acceptance.",
      "verification": {"level": "source", "result": "limited", "evidence": "Design accepted; implementation and host payload verification are pending. Source fixtures cannot establish native activation."},
      "exception": {"constraint_evidence": "Association source is pending. Core1bb supports Windows ScheduledTasks and Linux systemd user-manager receipts; Linux native waiting on a reachable manager and profile activation remain unverified.", "supported_other_host_outcome": "Both hosts use the shared Stop hook and platform dispatcher; neither has native association acceptance or profile activation evidence."}
    },
    {
      "host": "codex",
      "behavior": "Authenticate reciprocal native-session/controller ownership before existing Stop completion and lease checks.",
      "source": ".agents/hooks/continuation_stop.py",
      "mapping": "`.agents/plugins/manifests/codex/engineering-hooks.json` wires the Stop entry; `.agents/plugins/harness/engineering.json` declares the shared hook for both hosts and `.agents/plugins/sources.json` maps it to `hooks/continuation_stop.py`. Verify the actual payload and ancestry in isolated acceptance.",
      "verification": {"level": "source", "result": "limited", "evidence": "Design accepted; implementation and host payload verification are pending. Source fixtures cannot establish native activation."},
      "exception": {"constraint_evidence": "Association source is pending. Core1bb supports Windows ScheduledTasks and Linux systemd user-manager receipts; Linux native waiting on a reachable manager and profile activation remain unverified.", "supported_other_host_outcome": "Both hosts use the shared Stop hook and platform dispatcher; neither has native association acceptance or profile activation evidence."}
    }
  ]
}
```
## Verification and limits

Use meaningful disposable Windows and Linux tests with spaces and non-ASCII paths. Cover all 22 cases, concurrent registration, stale/forged/copied reciprocals, partial-write races, path redirection, PID reuse, foreign-owner isolation, both Claude and Codex native Stop payloads, repeated callbacks after successful and failed side pickup, and positive completion/pause/release controls. Check actual Stop payloads on both hosts. Separately verify real hook ancestry in disposable isolated acceptance; same-executable ancestry does not prove mixed-host isolation. Core commit `1bb1c130b2d1762bce07b599bb0fbb7e311c6749` includes existing Windows ScheduledTasks and Linux systemd user-manager receipt verification. Linux registration requires a reachable `systemctl --user` manager; the user timer runs only while that manager runs. Injected tests and source CI do not prove that a real Linux user manager is accessible or accepts the native waiting path, so Linux native acceptance remains limited until verified on an accessible Linux host. Source tests do not establish host activation or normal-profile enforcement.

## Execution readiness

Verdict: ready
Execution authorization: implementation
Transfer: required
Receipt: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-ControllerGoalAssociation/.agents/continuation/controller-association-transfer.json

Readiness authorizes this source boundary, including the mandatory existing-manifest declaration and inventory test. It does not claim implementation, installed-profile activation or native acceptance.

## Current checkpoint

Status: the authorized source slice is committed at `168b87d8607bbc756ce2c9ff37faa251d729a877`, with checkpoint `a38eaf6c1a134b2f91c3e49452247093a58f8215`. The continuation runtime now provides a bounded, evidence-backed reconciliation path for a lease-free `owner-head-changed` owner; the recovered owner was reconciled without changing its ID or limits. Focused continuation runtime and harness-manifest validation passed after catalog synchronization and local generation.

CI recovery: exact-head CI `38189764005` failed on both Windows and Linux because the new narrow `continuation_runtime.py associate-session *` declaration was rejected by the shared harness validator as though it granted every script argument. The manifest then became unusable and both auto-merge permission tests failed. Persistent delivery authorizes exact-head repair; the recovery adds only `.agents/machine/utility/bootstrap-capabilities/scripts/harness_permissions.py` and its existing focused inventory test. The validator now accepts exactly one literal subcommand plus its arguments, rejects option-style or wildcard subcommands, and checks both Bash and PowerShell declarations. The continuation reconciler also now accepts a blocked stale-head owner regardless of its stale reason, while still requiring the exact identity rebind and no foreground or child writer. Focused permission-sync, association declaration, continuation runtime and Stop tests pass. Generated catalog/package refresh is validation-only and remains uncommitted.

Stop recovery: the valid delivery artifact stores its exact bound SHA as `remote_head_sha`, while the normalized binding used by `continuation_stop.binding_active` was incorrectly checked for `head`. That produced the false `binding-head-changed` gate despite both values being `93803964be31d8283fe2f9e79ef12ad02ed3f9e2`. The hook now checks `remote_head_sha`; focused Stop coverage proves both the matching case and a real SHA mismatch. B004 records the causal defect and links this repair.

Continuation recovery: the active owner then reached its finite deadline while the goal was still incomplete and the user explicitly renewed the work. The runtime had no guarded way to preserve that owner while recording a new finite budget. It now provides `renew`, which is available only to a blocked `continuation-budget-exhausted` owner with no foreground or child writer, requires a nonempty reason, next action and 1–24 hour deadline, and preserves owner identity and recorded limits. B005 records this causal defect and the focused runtime coverage proves both renewal and duplicate-renewal rejection.

Next action: commit the exact-head CI, Stop-binding and continuation-budget recoveries; refresh the delivery binding and reconcile/renew the exact owner; then obtain a fresh frozen incremental review and rerun exact-head Windows/Linux CI before normal delivery steps.
