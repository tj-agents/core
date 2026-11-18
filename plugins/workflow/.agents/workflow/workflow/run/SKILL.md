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

## Authority and acceptance

The user's authorization defines the whole goal. An instruction to implement, execute, or deliver it
covers its necessary reviewable slices and the PRs those slices create. An agent-selected phase, PR, or
procedural limit does not narrow that authority. A goal file records authority; its existence does not
invent it.

When the user names a replacement or cutover, carry that scope through acceptance; an agent cannot retain
the former public capability by reclassifying it as policy, transport, or another discovery name.

Preserve an explicit user hold, design approval requested for separately proposed work, and every repository
guard for the relevant action. The selected procedures retain their own
capability and credential gates. Engineering owns the technical review, CI, stop paths, labels, and merge
checks that apply to a PR. A required human GitHub approval is a waiting dependency, not a handoff or a
new task: retain the exact binding, resume this same owner when it is observed, and do not ask the user to
announce it.

When a software slice has source, required review, and exact-head CI ready, record it ready and continue
to the selected Engineering merge procedure under this goal's existing authority. A CI event alone grants
no authority. Terminal reporting requires the authorized outcome's observed acceptance, including any
authorized publication, update, or installation; a source commit, pushed branch, or merged PR alone is
not completion.

```text
User: "Implement and ship the parser migration."
Agent: chooses two PR-sized slices and records their review and CI evidence.
First PR: its required GitHub approval is pending, so workflow:continue retains the same goal and binding.
Approval observed: workflow:run resumes engineering:merge without a new user prompt.
Completion: report only after the requested migration and its authorized package update are observed.
```

Read `agent:lanes` for bounded phase capability. The parent retains design, acceptance, diagnosis, and
severity. Delegate only specified implementation or independent evidence under exact disjoint leases, and
reconcile Git before reusing failed or cancelled leases.

For repository ownership, invoke `agent:recover` through native discovery and its published
`work-item-sessions.md` contract. Reconcile stored execution and owner state with actual native observation.
Claim the same execution only after verifying exact native identity and a permitted predecessor. Do not use
age-based takeover. Standalone work keeps its existing task goal and does not invent Git, provider, or SQLite
identity.

Before implementing a goal that introduces a reusable tool, capability or technical mechanism, apply
`base:solution-assessment` unless that idea already has a completed one.
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
