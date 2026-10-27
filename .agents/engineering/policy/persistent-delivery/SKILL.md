---
name: persistent-delivery
description: Shared safety and identity contract for a PR that must survive an agent turn and continue through exact-head validation, repair, review, and authorized delivery. Use when an authorized software delivery must continue across delayed checks; workflow:continue selects the supported native wake mechanism.

kind: policy
domain: process
---

# Persistent delivery contract

Owns software delivery identity, completion evidence and authorized decisions across wakes. Load
`workflow:continue` to establish supported host continuation. The Codex entry supplies its required durable
CLI transport; the shared policy does not start a scheduler or model turn.

A continuation goal may exist before a PR or delivery binding. Keep its repository, worktree, canonical
goal, completion condition and authorized actions in the existing goal record; add the exact PR/head/run
binding when a remote delivery stage exists. Missing merge authorization gates merge only. It does not
block authorized local work, exact-head repair, or review that can proceed before that gate.

## Completion record

Before reporting completion, maintain the canonical goal's fenced `completion` JSON with observed
acceptance evidence, every owned delivery PR identity, and every unresolved task required for the authorized
outcome with its owner and next action. The shared completion check refreshes every delivery PR and rejects completion unless the bound delivery is
recorded, merged at its full head, has no unchecked tasks, and the outcome evidence is present. A rejection
keeps the current owner and leaves the returned actions open.

Derive that boundary from the user's authorized outcome and verified delivery ownership. Preserve
independent work in optional `follow_up`, with its exact PR/head, responsible owner, next action and
`scope_evidence` identifying why it belongs to that separate delivery. The check returns this information
without waiting for it or refreshing its PR. It rejects overlap with an owned delivery or open task.
An external owner does not waive acceptance: when the requested outcome requires that work, keep the
unmet criterion in `acceptance` and its action in `open_tasks`. Do not add independent future work to the
current goal's acceptance merely to retain it. A successful completion check proceeds to the session's
`agent:close` decision; independent follow-up alone is no reason to keep the frontend open.

```text
User requests reviewed parser PRs; both are merged and verified.
Another owner retains a separate dashboard PR: record it in follow_up with that ownership evidence.
Result: the parser delivery may complete and enter agent:close.
User instead requests the working dashboard: its missing acceptance still blocks completion,
even when another owner is implementing it.
```

Before retiring recovery artifacts, reconcile and update any linked selected item through
[the shared recording contract](../../../workflow/resources/problem-records.md). Resolve it only after its own
acceptance is verified; the PR completion check alone does not close it. Preserve unresolved item
ownership and next action.

Run the same read-only check before a foreground terminal report:

Run the Python helpers with `python` on Windows or `python3` on Linux/macOS:

```bash
python -B <completion-check> --goal <absolute-goal> --root <absolute-worktree>
```

Resolve `<completion-check>` to `.agents/workflows/completion.py` in source or
`workflows/completion.py` in an installed engineering package.

The record has this shape; `follow_up` may be omitted when empty. Every string is nonempty, every head is a forty-character SHA, acceptance
and delivery records are unique, and empty evidence keeps its acceptance item open with an owner and next
action.

```completion
{
  "outcome": "The requested user-visible outcome.",
  "acceptance": [
    {
      "id": "criterion-id",
      "criterion": "The observable acceptance criterion.",
      "evidence": [
        {"source": "artifact or observation", "result": "concrete observed result"}
      ],
      "owner": "current execution owner",
      "next_action": "Resolve this criterion when evidence is absent."
    }
  ],
  "deliveries": [
    {"repository": "owner/repository", "pr": 123, "head": "0123456789abcdef0123456789abcdef01234567"}
  ],
  "open_tasks": [
    {
      "repository": "owner/repository",
      "pr": 123,
      "head": "0123456789abcdef0123456789abcdef01234567",
      "text": "Unchecked visible PR task.",
      "owner": "current execution owner",
      "next_action": "Complete the task and refresh the PR."
    }
  ],
  "follow_up": [
    {
      "repository": "owner/dashboard",
      "pr": 456,
      "head": "abcdef0123456789abcdef0123456789abcdef0123",
      "text": "Add the independently requested dashboard.",
      "owner": "dashboard delivery owner",
      "next_action": "Complete dashboard review under its existing goal.",
      "scope_evidence": "The user requested parser delivery here; the dashboard goal assigns PR456 to its existing owner."
    }
  ]
}
```

## Bind one delivery owner

Before creating or updating persistent work, capture one immutable delivery binding in the host task and in
the current durable handoff or plan state when one exists:

- repository owner/name and PR URL/number;
- absolute worktree and branch that own the change;
- current remote head SHA;
- every pending check ID and run ID with its full head SHA;
- review work-order path, execution order, and completed reviewed-SHA watermark;
- explicit merge authorization: absent, `--auto` authorized, or a narrower recorded instruction; and
- the explicit completion condition.

When the current PR is one stage of a longer plan-managed delivery, also bind one workflow handoff:
workflow ID, repository-relative plan or ledger state artifact, and the exact next stage to resume after this
PR merges. The workflow handoff preserves the broader goal across successive delivery owners; it never
weakens the exact PR/head/run identity active at any moment.

There is exactly one persistent owner for a PR/head pair. Reuse and update that owner when the binding is the
same. A new head created by this owner replaces its binding. A head changed by somebody else, a changed PR,
or a different worktree ends ownership and surfaces a human decision; never silently follow it.

Resolve authority from the repository's recorded standing instruction, the user authorization kept in
the owning goal record (`engineering:merging` owns that goal-wide scope), or an observed user approval
for this exact PR. The source command below, or packaged `workflows/workflow_ops.py`, is the single writer of
the binding artifact. Run this helper with `python` on Windows or `python3` on Linux/macOS:

```text
python -B .agents/workflows/workflow_ops.py --root ROOT --workflow-run-id ID delivery-bind --pr NUMBER [--approval-record PATH]
```

The optional approval record has exactly these fields. Replace the illustrative values with the actual
owning checkout identity, permitted merge mode, user's wording and observed message provenance:

```json
{
  "repository": "example/test",
  "pr_number": 42,
  "worktree": "C:\\source\\test",
  "branch": "feature",
  "mode": "merge",
  "instruction": "Merge PR 42 when checks and review pass",
  "source": "User message in SESSION at TIMESTAMP"
}
```

`worktree` must match the binder's normalized absolute checkout root, and `branch` must match both the
checkout and remote PR. `mode` is `merge` or `auto`, according to the actual approval; an authorization
naming no mode records `auto`, because unattended completion is what it requests. A goal file's bare
existence never invents merge authority; the user's recorded authorization of the goal does, for the
goal's own PRs (`engineering:merging`) — write it as this record, with its wording and provenance, for
each PR the goal creates. Invalid explicit input fails before any standing-authority fallback. Without a
standing instruction, goal authorization, or matching scoped approval, authority remains `absent` and
merge requires a user decision.

The binder reads authoritative forge state and resolves `.agents/delivery-authorization.json`, when
present, against the current changed paths and labels. The authorization table itself always stops.
With `standing_authorization` set to `auto` or `merge`, its optional `authorized_stop_classes` list may
name each of `ci-workflow`, `migration`, `auth`, `money` and `published-contract` at most once. Repository
stop paths and its hold label still apply; without a table, `human-gate` is the hold label. A scoped
approval cannot add exemptions or bypass a stop. **Re-run the binder on every rebind:** a repaired head
may add a stop path or hold.

The auto-merge preference comes from `.agents/settings.json` in the actual checkout, at
`configuration.core.auto_merge`, separately from delivery authority. An absent file or an omitted
`configuration`, `core` or `auto_merge` disables auto-merge, and malformed settings fail closed. The
settings file itself is always a non-exemptible stop. After the normal green exact-head, independent-review and merge-authorization decision, invoke only
the packaged guarded command:

```text
python -B workflows/auto_merge.py --root ROOT
```

It reloads fresh settings and authority, the complete remote diff and labels, live PR readiness, exact local and
remote branch/head/worktree identity, and the canonical review and security evidence before executing its
fixed GitHub command. Do not run `gh pr merge --auto` directly; the delivery hook directs it to this wrapper.

The artifact retains matching approval wording and provenance as `scoped_approval` across wakes and
supported repairs to the same PR, worktree and branch. Each rebind refreshes the remote head, checks and
review evidence and reevaluates the stops. A stopped head retains the approval record but resolves
`absent`; it does not authorize unattended merge. A wake or same-PR repair never requires another approval
solely because the repository lacks a standing table. The record cannot carry into another repository,
PR, worktree or branch. If ordinary merge is approved and GitHub auto-merge is unavailable, wait for
terminal checks and current-head review, then perform the authorized ordinary merge. End the binding with
`delivery-release --reason <terminal>`.

That command writes the binding to `.agents/persistent-workflow-binding.json` at the owning worktree root — repo
owner/name, PR number and URL, branch, absolute worktree, full head SHA, the exact check and run IDs, and
the completion condition. It is per-worktree runtime state, gitignored, and is the discoverable form of the
binding a hook can read. Update it on every rebind to a new head, and delete it on any terminal (merge,
closure, supersession, external head replacement, a human gate). Do not arm an unattended auto-merge without
a continuation that owns the wait.

## Route every wake through the shared decision contract

The parent remains the workflow owner. It owns the plan, durable delivery state, stage transitions, exact
binding, authorization, and final terminal decision. A host wake reads authoritative forge state once and
passes the binding and observation through `workflows/delivery_runtime.py`. Reject a PR, check, run, review,
or merge observation from another head.

An exact-head failure selects its test tier before repair:

| Evidence | Fresh-context procedure |
|---|---|
| Unit | `failing-tests` |
| In-process integration | `integration-debug` |
| Service E2E | `e2e-api-debug` |
| Browser E2E | `e2e-ui-debug` |
| Both E2E tiers | `e2e-debug` |

Dispatch one clear context through the host's agent API with the selected skill,
repository/PR/worktree/branch, full bound SHA, exact
check and run IDs with their head SHA, and the failure signature. The debug context reads the remote log
first, reproduces only the failing scope, applies the tier procedure, runs focused validation, and returns
structured repair evidence to the parent. It does not create another monitor, select follow-on scope, or
merge. This dispatch is not a keyboard macro, `/clear`, pasted prompt, or new top-level conversation. The
parent validates the result, accepts one stable repair, commits and pushes it, then updates the existing
continuation to the new SHA and exact pending runs. It never creates a second continuation during that rebind.

A green exact head enters independent `review` or `incremental-review`. A host with a declared model
fallback keeps the same semantic stage, frozen SHA, role boundary, and fresh-context requirement, and records
both the primary and selected model. Exhausting a protected-stage route is a human decision. Actionable current-head findings
enter `address-review` and return through a new current-head watermark. Only a green, independently reviewed
head may enter `merge`, and only under the recorded authorization.

## Transfer an intermediate merge

The runtime owner is bound to one worktree and branch, and permits head repair within that identity.
It cannot rebind itself to a successor PR or another checkout. When a slice PR merges, complete its
recorded delivery condition, release its binding, checkpoint its runtime owner and remove its scheduled
task. Preserve that owner's receipts and results. Before reusing the same checkout, archive its terminal
`.agents/continuation/` directory, including `owner.json`, receipts and results, outside the tracked tree;
the next initialization needs the canonical owner path available. Remove the old scheduler before
archiving its receipt. Completing the slice owner does not complete the broader canonical goal.

With a workflow handoff, the foreground parent resumes the recorded stage through `workflow:run` and
reconciles the next slice's existing branch, worktree and PR, including its actual base and head. Create
those only when absent. After retiring the old owner, initialize and claim the next worktree's canonical
owner against the same goal, then register its continuation when needed. Keep one active writer. The
repository, workflow ID and state artifact remain identical; automatic supervisor transfer across
worktrees is outside the runtime's supported transition.

The successor is a new delivery binding with its own checks, review watermark, and merge authorization.
A completed PR's binding never carries over; the successor re-resolves authority from the same recorded
sources, and the goal's authorization covers each PR the goal itself creates (`engineering:merging`). The
workflow owner may implement, validate, push, open, and review that successor without intervention when
those actions are already in scope, and stops at its merge gate only when no recorded goal, standing, or
scoped authority covers it.

An unchanged authoritative state produces no report, mutation, replacement continuation, or model-driven
work. Host mechanics decide how a later transition wakes the owner; shared policy never claims that a shell
process, hook, or ordinary model turn provides persistence.

## Authorization and terminals

Persistent delivery may implement, test, commit, push, diagnose exact-head CI, and obtain the required review.
It must not merge, enable auto-merge, approve, deploy, delete, or widen scope without the recorded authority.
An authorized auto-merge request awaiting GitHub's required review stays `waiting`, with its binding and
scheduled owner intact. The user approves in GitHub; approval alone requires no agent turn. A merge
observation wakes the same owner to finish the authorized post-merge steps. Report the approval link once;
do not ask the user to announce approval. A rejected review, changed head, explicit hold or missing task
authorization retains its existing repair or human-gate behavior.

A merge authorization never covers publishing: releasing to a package feed stays an explicit human call
whatever the standing instruction says about merging.
The ordinary review/merge skills remain authoritative. Keep one monitor and one read per wake. Launch
`.agents/workflows/workflow_ops.py monitor` for the exact binding; it persists state across disconnects and
wakes the owner only for a material transition or terminal result.

Stop and remove the slice's host task when the bound PR merges, closes, is superseded, or reaches a genuine human,
authorization, external-head, model-availability, or product-capability decision. A closed continuation is
never replaced merely to report why it stopped. Record the final PR/head/result and next decision in the
normal handoff or plan artifact when one owns the work. The host task prompt itself carries the full binding
so the owning conversation can resume after application restart without the user restating the task.
