# Work and problem records

Core owns agent execution tracking and reusable engineering workflows. The selected profile owns remote
work-item content, native types, tracker operations and record policy. Core never installs or selects a
profile on a repository's behalf.

## Repository selection

A committed `.problem-records.json` in the source repository's primary checkout selects the profile's
qualified read operation, for example `{"schema_version":1,"provider":"personal:work-item"}`.
The primary checkout is the first non-bare entry of `git worktree list --porcelain`, resolved from any
worktree or subdirectory; a feature worktree's copy never overrides it. Read the declaration before any
tracker operation. Selection requires repository authorization; installing Core never adopts a provider.

## Selected profile operations

| Operation | Explicit personal scope | Selected Infonetica employer scope |
| --- | --- | --- |
| Read, list or view an existing item | `personal:work-item` | `infonetica:work-item` |
| Record a new item | `personal:create-work-item` | `infonetica:create-work-item` |
| Reconcile and carry out existing work | `personal:address-work-item` | `infonetica:address-work-item` |

A session lists only the skills of the project it started in. When the needed operation is not listed,
run `python -B <engineering plugin root>/hooks/problem_records.py --root <repository> --operation
create|read|address --harness claude|codex`, the root being two directories above a loaded engineering
skill's base directory, and follow the printed `skill`. A failure, including a directory outside any
repository, blocks the operation.

Use only the selected profile's qualified operation. It owns deterministic scripts, factual validation,
request reconciliation, remote persistence, native type mapping, retention and verified closure. It also
owns when recording is permitted and any required user decision. Selecting a provider, observing a
problem or authorizing a repair does not itself authorize creating a remote item. Apply the selected
profile's decision before creation; keep personal recording autonomy with the personal profile.

While a recording decision is pending or declined, retain relevant facts in the existing authorized task
and continue unaffected work. Do not create a substitute item, switch providers or treat withheld
recording consent as permission to publish elsewhere. Preserve
the request's intent: a software defect, observed agent/process mistake, deliberate debt, feature, story
or concrete task. The profile maps that intent to its actual tracker types; Core does not impose a shared
remote schema. Recording never starts implementation. An explicit addressing request reuses the item's
existing repair, feature or plan owner and the applicable engineering lifecycle.

A read returns persisted details without creating an agent execution. When work begins, use Machine's
shared session registry to associate the profile-verified qualified external reference with the existing
execution and its agent sessions. Keep ownership, execution status and resume IDs in the original SQLite
store; keep backlog content and acceptance evidence in the profile's remote tracker.

An invalid declaration or a missing, unavailable or offline profile blocks the record operation. Retain
unsent facts in the active task or goal with the resolver and observable resume condition. Do not install
another profile, redirect employer evidence, create a Markdown register or select a different backend.

## Repositories without a provider

Without a valid declaration, tracker operations block. Retain unsent facts in the active task or goal with
the resolver and observable resume condition. Existing `BUGS.md`, `MISTAKES.md` and `TECH_DEBT.md` files
remain historical evidence that may be read and linked; do not update them as an active backlog.

Plans, review artifacts and roadmaps retain design and recovery evidence and link canonical record
identities. Preserve existing remote identities and history. Repository and employer policy controls
where evidence may go; employer-owned facts stay within the selected employer provider.

```text
The primary checkout selects personal:work-item. A new defect uses personal:create-work-item with bug
intent; a repeated observation updates its existing GitHub identity. An explicit repair request uses
personal:address-work-item and keeps the existing repair owner. Reading the item creates no execution.
An employer profile requires a creation decision: retain the observation in the current task until that
decision is supplied; selecting the profile does not satisfy it.
```
