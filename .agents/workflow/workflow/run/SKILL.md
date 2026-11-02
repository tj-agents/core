---
name: run
description: Own authorized sustained or multiphase work through its actual acceptance condition. Use when work continues across phases, commits, reviews, or context changes.
kind: workflow
domain: process
---

# Run an authorized goal

Own the whole authorized goal through actual acceptance and authorized delivery. Reconcile user scope with
agent-authored slice limits, read one existing canonical goal, use `workflow:plan-artifacts` for recovery, keep
one next action, and continue independent authorized work across commits and pull requests. Direct short
requests remain their selected operation without a ceremonial plan.
For a side problem or user callout, apply
[Workflow's incidental-problems decision](../../resources/problem-records.md#incidental-problems)
before changing this goal's next action.

Read `agent:lanes` for bounded phase capability. The parent retains design, acceptance, diagnosis, and
severity. Delegate only specified implementation or independent evidence under exact disjoint leases, and
reconcile Git before reusing failed or cancelled leases.

For repository ownership, invoke `agent:recover` through native discovery and its published
`work-item-sessions.md` contract. Reconcile stored execution and owner state with actual native observation.
Claim the same execution only after verifying exact native identity and a permitted predecessor. Do not use
age-based takeover. Standalone work keeps its existing task goal and does not invent Git, provider, or SQLite
identity.

For software, load `engineering:plans` for technical delivery slicing and select `engineering:feature`,
`engineering:bugfix`, or the supplied selected technical operation for a bounded slice. A profile may supply an
`address-*` operation; Workflow uses that selection without depending on a profile or tracker. Those operations
return evidence to this owner. `engineering:review` remains the source review owner. Route an unmet
acceptance condition to an available suitable execution environment. A local OS or missing runtime alone is not
a blocker: within existing authority, assess supported provisioning that makes validation repeatable before
declaring a capability missing or asking the user for a machine. When a selected discipline supplies that path,
use it while retaining its authentication, trust, and authority constraints; independent authorized work
continues.

For a deferred command or condition, invoke `agent:listen` before parking or moving to
independent work. It owns deterministic background waiting and the native result notification.

## Terminal acceptance and frontend release

At the real end of an authorized goal, this workflow owns one terminal acceptance checkpoint. Prepare a
candidate receipt from the current goal, exact artifacts and digests, delivery evidence, known ownership,
children, waits, and cleanup disposition. The Store's one mutable `work_item` field is session evidence,
not the aggregate of responsibilities; an unknown responsibility inventory refuses automatic release.

Run the bounded deterministic checks against that candidate. Current generic completion criteria are
semantic, so they require one read-only native audit for every new candidate. Reserve that audit before
starting a same-session background child. Start the child only when the reservation response has outer
`dispatch_allowed: true`; a false value means reuse or reconcile the existing slot. Record its native
identity before treating it as in flight. After observing an existing child for an unknown reservation, bind
it with the reconciled path; never silently retry a spawn. The child returns findings or acceptance evidence;
it cannot release a frontend, retire a goal, remove a checkout, or transfer ownership.

An accepted receipt remains reusable while its candidate inputs remain unchanged. Agent rechecks that same
receipt against the current frontend and then arms a separately generated release request. A `pending`
cleanup disposition needs a separately acknowledged live cleanup worker bound to the exact session,
obligation, and target before that arm; a bare pending disposition refuses release. A new prompt cancels an
armed release before interpretation but does not invalidate unchanged acceptance evidence. A persistent
keep-open policy prevents release until revoked. An incomplete user dismissal preserves the goal with a
dismissal intent; refresh uses a restart intent and preserves the same conversation and owner.
Ordinary Stop only records activity and may acknowledge an already armed request. It never asks a model to
decide completion, blocks a reply, or starts a session.

Use the Core receipt CLI from the selected package root (`python3` on Linux/macOS). It snapshots the goal,
responsibility aggregate, declared evidence, and later audit result outside the checkout. Keep the returned
absolute receipt path and reservation id as evidence; do not recreate either when resuming the same candidate.

```text
python -B <core-runtime>/completion.py prepare --goal <goal> --aggregate <responsibilities.json> --owner-host codex --owner-session-id <session> --root <checkout>
python -B <core-runtime>/completion.py reserve-audit --receipt <receipt>
python -B <core-runtime>/completion.py bind-audit --receipt <receipt> --reservation-id <reservation> --native-child-id <child>
python -B <core-runtime>/completion.py record-audit --receipt <receipt> --reservation-id <reservation> --result <child-result.json>
python -B <core-runtime>/completion.py recheck --receipt <receipt>

python -B <agent-runtime>/close_lifecycle.py prepare --host codex --session-id <session> --profile <profile> --intent task-completion --receipt <receipt>
python -B <agent-runtime>/close_lifecycle.py recheck --host codex --session-id <session> --profile <profile> --release-generation <generation>
python -B <agent-runtime>/close_lifecycle.py arm --host codex --session-id <session> --profile <profile> --release-generation <generation>
python -B <agent-runtime>/close_lifecycle.py policy --host codex --session-id <session> --profile <profile> --action keep-open --reason <reason>
python -B <agent-runtime>/close_lifecycle.py dismiss --host codex --session-id <session> --profile <profile> --receipt <receipt> --reason <reason>
```

The child result contains `candidate_id`, `reservation_id`, `native_child_id`, `sources_sha256`,
`state` (`passed` or `failed`), and `findings`. Store that result outside the checkout. A reconciled bind
adds `--reconciled` only after observing the same native child for an unknown reservation.

Use `policy --action keep-open|revoke` for the persistent release policy. `dismiss` records an explicit
incomplete user dismissal. Refresh restart prepares, rechecks, and arms its own release generation without a
completion receipt.

Cleanup is a separate result: `unnecessary`, `retained`, `pending`, or `verified`. `engineering:merge`
owns an exact targeted checkout removal after release. A pending or refused cleanup remains durable and does
not turn into success because a host exited.

```text
Candidate: deterministic checks establish delivery and all known responsibilities.
Audit: reserve the candidate; only `dispatch_allowed: true` permits one same-session child. Reuse a completed audit for the same candidate.
Release: recheck the unchanged receipt, then arm the attributable frontend only.
```

Use only a supported host continuation. Do not claim unattended execution before the selected native or
host-specific continuation is established and its wake observed. `workflow:continue` selects and establishes
the next supported wake for this goal. Foreground execution remains valid without unattended capability.
After exhausting independent
authorized work, persist the exact blocker, resolver, unblock action, and observable resume condition.

Report terminal work as its actual outcome, validation evidence, and remaining durable state. A local commit,
pushed branch, open pull request, phase, or context boundary is not terminal while authorized work remains.

```text
Goal: deliver the approved migration.
Current slice: ask engineering:feature to add the bounded parser change and return tests.
Deferred result: give the bounded watcher command to agent:listen before parking.
Next action: consume its completion result, then continue the same goal.

During the migration, the user reports an unrelated terminal defect without requesting a repair.
Apply Workflow's incidental-problems decision; record through the selected create operation.
Keep the migration's next action and continue it.
```
