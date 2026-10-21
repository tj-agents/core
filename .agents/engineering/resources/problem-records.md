# Work and problem records

Core consumes canonical work-item identities and owns no recording backend. Route every recording,
listing and addressing operation by the repository's selection.

## Repository selection

A committed `.problem-records.json` in the source repository's primary checkout selects a provider:
`{"schema_version":1,"provider":"plugin:utility"}`. The primary checkout is the first non-bare entry of
`git worktree list --porcelain`, resolved from any worktree or subdirectory; a feature worktree's copy
never overrides it. Read the declaration before recording, listing or addressing work. Selection requires
repository authorization: installing Core or Work Items never adopts a provider.

## Selected repositories

Load the qualified Work Items writer that matches the request:

| Request | Writer |
| --- | --- |
| Untyped recording request | `work-items:write-issue` |
| Faulty software behavior | `work-items:write-bug` |
| Observed agent or process error | `work-items:write-mistake` |
| Deliberate shortcut or deferred compromise | `work-items:write-debt` |
| New or changed behavior | `work-items:write-feature` |
| Concrete work with a completion condition | `work-items:write-task` |

The Work Items package owns provider admission, reconciliation, facts, persistence, retention, and
verified closure. An invalid declaration or a missing, unavailable or offline provider blocks the
operation: retain unsent facts in the active task or goal with the resolver and observable resume
condition. Do not create a Markdown register or select a different backend.

## Repositories without a provider

Without a valid declaration, recording, updating and addressing work items block. Retain unsent facts in
the active task or goal with the resolver and observable resume condition. Existing Markdown registers,
including `BUGS.md`, `MISTAKES.md` and `TECH_DEBT.md`, remain historical evidence: they may be read and
linked, but they are not an active backend and must not be updated or used to create a parallel backlog.

Plans, review artifacts, and roadmaps retain design and recovery evidence and link canonical record
identities; they are not a live queue. Preserve existing records and history. Repository and employer
policy controls where evidence may go; never redirect employer-owned facts to a personal provider.
