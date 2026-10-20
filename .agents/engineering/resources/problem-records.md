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

## Unselected repositories

Without a declaration, the problem registers the repository declares or already keeps, such as root
`BUGS.md`, root `MISTAKES.md` and owning-area `TECH_DEBT.md` files, remain its record owner. Record, list,
update and address entries there in the primary checkout, outside skill folders, feature worktrees and
plans, and publish them through `engineering:merge-docs` when authorized. Keep each register's stable
identifiers and format. An entry states its kind, observed evidence, confirmed or unknown cause, impact and
priority, source owner, state, repair link, next action, resolution condition and verification evidence.
Retain resolved bugs and mistakes with that evidence; delete a debt entry once verified resolved unless its
register declares other retention. Core never starts a register in a repository that keeps none; recording
there blocks as for an unavailable provider.

Plans, review artifacts, and roadmaps retain design and recovery evidence and link canonical record
identities; they are not a live queue. Preserve existing records and history. Repository and employer
policy controls where evidence may go; never redirect employer-owned facts to a personal provider.
