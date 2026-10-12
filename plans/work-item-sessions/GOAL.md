# Persistent work-item session registry

## Objective

Replace the current ad hoc worktree/progress-dump recovery practice with one Core-owned convention that records the active native Claude and Codex sessions for each work item. Every repository that injects the Core plans convention must receive the same guidance and templates. A user must be able to say "continue work item X" and recover the literal recorded native session through its correct `open-claude` or `open-codex` command, even after its worktree was safely removed following pushed delivery.

## User-authorized outcome

The durable plan layout is:

```text
plans/
  features/
    <feature>/
      README.md
      work-items/
        <work-item>/
          README.md
          ACTIVE_SESSIONS.md
```

`README.md` at feature level explains the feature and lists its work items. The work-item `README.md` owns purpose, scope, current delivery status, PRs, durable decisions, evidence and completion. `ACTIVE_SESSIONS.md` is the only short-lived live-session registry. It contains one row for every active or resumable native session; one work item usually has one row but may have several bounded, non-overlapping owners.

Use the term **session handle** for the durable host-qualified identifier, for example `claude:<native-session-id>` or `codex:<native-session-id>`. Do not call an opaque identifier a hash unless the host actually supplies a cryptographic hash. Each row must record the host, session handle, visible CLI/tab title when available, role, state, absolute worktree, branch, PR, exact HEAD, last verified timestamp, predecessor/successor relationship where relevant, and the exact safe resume command. The resume command must select the recorded host/session and not merely open a new generic CLI. Remove the row when that session's work is terminal; retain delivery/history in the work-item README.

The existing "progress dump" is retired completely after its responsibilities have been migrated and every consumer/reader is updated. Its exact canonical paths, readers and generated/package representations are not yet confirmed: discover them from source and record the migration map before deleting anything. Do not delete a similarly named plan, goal, session runtime artifact or user-authored progress evidence merely because it resembles the old dump.

## Why this work exists

Core currently has many registered worktrees and partial local CLI liveness data, but no authoritative relation between a work item, the exact native agent/session that owns it, its PR/head, and safe cleanup. Once a session disappears, a worktree may remain solely because nobody can determine its owner or whether its work was pushed. Existing `.agents/continuation` owner/receipt files are runtime coordination state, not a durable cross-repository inventory. They can be stale or inaccessible and must not become the new registry.

The immediate evidence was a controller-association session on `Fix/ControllerGoalAssociation`: the source Stop repair was committed but the installed cache was stale, the historic transfer receipt named an absent successor while still reporting active, and the owner lock was stale. These facts must be carried as a problem example, not copied into the general convention as the normal workflow.

## Scope and boundaries

- Core owns the portable convention, templates, skill/workflow changes, generated host adoption, validation and release.
- The convention applies to Core and every repository that injects the Core marketplace/plan convention. Design consumer adoption so it is explicit, versioned and migratable; do not silently rewrite unrelated repositories or their plans.
- Separate durable guidance from product/runtime changes. Follow `engineering:git-branching`: global always-loaded guidance must land as its own focused docs/convention slice; templates, generators, runtime discovery and migration tooling belong in later focused slices if needed.
- Read `engineering:skill-authoring` before adding, splitting, renaming or retiring skills. The likely need is a plan/work-item convention, not a new skill by default; prove a new skill is necessary before creating one.
- Read existing plan-artifact, plans, plan-authoring, plan-checkpoint, handoff, open-claude, open-codex, recover-agents and peer-cli contracts before design. Reuse their host-native session recovery behavior; do not invent a new agent database if a durable Markdown registry plus existing recovery commands is enough.
- All shipped behavior must work on Windows and Linux. Do not patch installed plugin caches, disable hooks, add arbitrary local profile state, or commit generated `plugins/*` or catalog output.
- Do not modify the live controller-association PR #209 or its checkout. This work has its own branch, goal and review.

## Required design decisions

1. Define the canonical path grammar and determine whether `features/` is required for every plan or is the new preferred structure with a documented legacy bridge.
2. Define the complete `ACTIVE_SESSIONS.md` schema and lifecycle, including multiple concurrent bounded agents, handoffs, resume, stale/unknown sessions, finished/deleted worktrees, and when entries are removed versus retained in README history.
3. Specify how host-qualified handles and exact resume commands are produced and validated using existing `open-claude`, `open-codex`, `recover-agents` and `peer-cli` capabilities. A resume command must not produce a duplicate writer.
4. Identify every existing progress-dump source, reader, template, test, hook, generated artifact and consumer convention. Produce an explicit migration/deletion map before removal.
5. Define consumer rollout: which Core package/template changes propagate automatically, what repositories must opt in or migrate, what compatibility period (if any) is justified, and how adoption is verified without an unsafe sweeping edit.
6. Decide whether Termboard consumes this Markdown convention as its durable source of truth, mirrors it, or supersedes it. Preserve a simple non-Termboard workflow; Termboard is not a prerequisite for the convention.

## Acceptance criteria

- A fresh Core plan can create one feature, one work item, a work-item README and `ACTIVE_SESSIONS.md` using the documented convention.
- A work item can record one Claude and one Codex session with exact host-qualified handles and resume commands; a bounded multi-agent work item remains unambiguous.
- A closed session is removed from `ACTIVE_SESSIONS.md`; its worktree may be safely deleted once Git/PR evidence is durable, while the work-item README preserves its delivery outcome.
- A stale or unknown session is reported as stale/unknown and does not authorize deletion, reopening or a second writer by inference.
- Existing handoff/recovery/peer tooling has a documented path from an entry to the correct host command, with tests where Core owns the behavior.
- The exact legacy progress dump and all of its readers are migrated or removed with no dangling source/generated references.
- Core’s generated host/package adoption is updated from canonical source and all affected Windows/Linux tests, source-layout checks and package-generation gates pass.
- The rollout is split into reviewable PR-sized slices, with independent review and normal delivery for each. Consumer migration is tracked rather than claimed complete before evidence exists.

## Authorized delivery

Tommy explicitly authorized this Core-wide convention and migration on 2026-10-12, including normal implementation, testing, review, PRs and merge after repository gates pass. This does not authorize destructive cleanup of existing worktrees, deleting user data, profile installation, bypassing hooks/checks, or bulk edits to consumer repositories without the reviewed migration plan and their normal ownership gates.

## First actions

1. Read this goal, repository instructions, current plan conventions and the directly relevant Core skill/workflow sources.
2. Inventory the actual progress dump and every reader before proposing deletion.
3. Write the canonical convention and phased migration plan in this goal, including exact source paths and a PR-slice map.
4. Implement only the first reviewable Core source slice after the design is recorded and sized; hand off later consumer migration or Termboard integration only with their own canonical goals.

## Handoff lane

Lane: L3. This is an open cross-repository convention and migration design with unresolved ownership, compatibility and recovery choices. Tommy explicitly selected Claude for this non-frontier handoff.
