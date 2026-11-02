# Work and problem records

Agent attaches verified native/session references through the canonical Agent Store. The source
repository's selected policy owns recording and progress authority; its selected provider owns remote
content, native types and tracker operations. Core never installs or selects either on a repository's
behalf.

## Repository selection

Identify the affected system, intended outcome and responsible source repository before choosing a
tracker root. The observation's checkout is evidence of where it occurred, not of who owns its cause.
Use that source repository's selection below. If ownership or scope is unclear, ask what system and
outcome the user means before making a remote record; retain facts and continue independent work.
Preserve employer evidence boundaries throughout source and destination selection.

Selecting `personal@tj-agents`, with the `tj-agents` marketplace at `tj-agents/marketplace`, in the source
repository's `.agents/plugins.json` selects Personal's work-item policy and `github:work-item` as its
provider. Any explicit provider is selected by a committed `.problem-records.json` naming its
qualified read operation, for example `{"schema_version":1,"provider":"infonetica:work-item"}`; it takes
precedence. Both are read from the primary checkout, the first non-bare entry of `git worktree list
--porcelain`, resolved from any worktree or subdirectory; a feature worktree's copy never overrides it.
Read the selection before any tracker operation. Selection requires repository authorization; installing
Core never adopts a provider. Load the source's applicable recording policy separately from its
provider operation. Importing those instructions for a source item does not adopt the source's complete
profile for the observing repository or change the active task's policy.
For Personal, load only its resolved `rules/resources/work-items.md` resource for this decision; do not
load its clean-cut, implementation or planning rules into an unrelated observing task.
The resolver may read that bounded policy from the native installed Personal payload even when the
observing project disables Personal. It does not activate that profile; executable provider operations
still require enabled native discovery.

## Incidental problems

When a bug, mistake or deliberate debt is noticed or reported during item A, preserve A's goal and next
action. Reconcile the affected source, existing record and repair owner, then invoke the selected
provider's qualified creation operation for a new item B when source policy and user authority permit. A
local Markdown entry is not a tracker operation. Keep unsent facts with A while recording is blocked,
pending or declined; continue unaffected authorized work.

Reporting, recording, repair authority, priority and handoff are separate decisions. A question,
frustration or bug callout alone leaves A active. Recording does not dispatch ordinary backlog work.
A source-specific standing instruction may separately authorize a bounded repair handoff. Apply it
only to its eligible source item, preserve A's goal and owner, and reconcile B's existing owner before
any launch. For tj-agents source defects, `template:self-repair` owns that decision. Honor an explicit
request to fix, reprioritize or hand off B; retain A's remaining work and ownership unless the user
replaces or transfers it.

Correct defects required for A's existing acceptance condition within A's authorization. Establish that
relationship with evidence before changing source. An issue number or severity alone establishes no
dependency. If A cannot safely proceed, explain the concrete blocker, resolver and decision needed;
continue independent authorized work without silently replacing A with a separate repair goal.

```text
A: add report export. B: an unrelated terminal-close bug is reported.
Apply the source's recording policy for B; continue report export.
"Why did the terminal stay open?" asks for an answer; apply that decision without starting B.
The export's existing acceptance check fails because its CSV writer corrupts quoted fields:
correct that defect within A, citing the failing export check.
"Fix the terminal bug first": retain A's next action, then reconcile B's owner and enter its repair.
```

Feature, story, task and untyped recording requests use the selected provider's creation operation.
Source policy supplies recording authority; the provider maps intent to native type.
[Repository selection](#repository-selection) never grants permission to start implementation.

## Work progress

At authorized work start, resolve the affected source and its selected recording policy and provider.
Apply that policy's recording decision to the current work; do not infer automatic recording from a
provider's installation. Reconcile the canonical item before creating one and bind it to the existing
execution rather than starting another lifecycle.

When source policy requires automatic maintenance, use its selected provider to persist factual
progress at material changes: starting work, blocking or resuming, handing off, entering review, and
verified acceptance. Keep the same item, goal and owner. Record evidence first and verify the remote
issue and board transitions; board state alone proves neither ownership nor completion. Resolve the
actual board options rather than inventing states. Preserve the exact operation and request identity
after an uncertain or partial response and reconcile the existing item before retrying.

```text
The current feature already has an item and owner. Review begins: update that item's factual progress
and its supported board state, then read the result back. No second execution or issue is created.
The PR opens but acceptance is pending: keep the item open; an open PR does not establish completion.
```

## Selected provider operations

| Operation | Explicit personal scope | Selected Infonetica employer scope |
| --- | --- | --- |
| Read, list or view an existing item | `github:work-item` | `infonetica:work-item` |
| Record a new item | `github:create-work-item` | `infonetica:create-work-item` |
| Reconcile and carry out existing work | `github:address-work-item` | `infonetica:address-work-item` |

A session lists only the skills of the project it started in. When the needed operation is not listed,
run `python -B <hooks>/problem_records.py --root <repository> --operation create|read|address --harness
claude|codex` (`python3` on Linux/macOS) and load the resolved source policy and printed operation
`skill`. `<hooks>` is the installed engineering plugin's `hooks` directory, beside the `skills`
directory that holds its skill base directories,
or `.agents/hooks` in a Core checkout. A failure, including a directory outside any repository, blocks the operation.

Use only the selected provider's qualified operation. It owns deterministic scripts, factual validation,
request reconciliation, remote persistence, native type mapping, retention and verified closure.
The source policy owns when recording and automatic progress updates are
permitted, including any required user decision. Selecting a provider, observing a problem or
authorizing a repair does not itself authorize creating a remote item. Apply the source policy's
decision before creation; keep personal recording and board-maintenance autonomy with Personal.
Verify remote issue and board state before reporting progress as persisted.

While a recording decision is pending or declined, retain relevant facts in the existing authorized task
and continue unaffected work. Do not create a substitute item, switch providers or treat withheld
recording consent as permission to publish elsewhere. Preserve
the request's intent: a software defect, observed agent/process mistake, deliberate debt, feature, story
or concrete task. The provider maps that intent to its actual tracker types; Core does not impose a shared
remote schema. Recording never starts implementation. An explicit addressing request reuses the item's
existing repair, feature or plan owner and the applicable engineering lifecycle.

A read returns persisted details without creating an agent execution. When work begins, use Agent's
shared session registry to associate the provider-verified qualified external reference with the existing
execution and its agent sessions. Keep ownership, execution status and resume IDs in the original SQLite
store; keep backlog content and acceptance evidence in the provider's remote tracker.

An invalid declaration, unavailable source policy or missing or offline provider blocks the record operation. Retain
unsent facts in the active task or goal with the resolver and observable resume condition. Do not install
another profile or provider, redirect employer evidence, create a Markdown register or select a different backend.

## Repositories without a provider

Without a valid selection, tracker operations block. Retain unsent facts in the active task or goal with
the resolver and observable resume condition. Markdown registers (`BUGS.md`, `MISTAKES.md`, `TECH_DEBT.md`)
are retired; never create or update one.

Plans, review artifacts and roadmaps retain design and recovery evidence and link canonical record
identities. Preserve existing remote identities and history. Repository and employer policy controls
where evidence may go; employer-owned facts stay within the selected employer provider.

```text
The primary checkout selects github:work-item under Personal policy. A new defect uses
github:create-work-item with bug intent; a repeated observation updates its existing GitHub identity.
An explicit repair request uses
github:address-work-item and keeps the existing repair owner. Reading the item creates no execution.
A shared Workflow recording failure observed during CLI work belongs to Core's selected tracker,
after verifying Core owns that policy. Reconcile an existing CLI issue and its history before deciding
whether to transfer it; do not create a second issue merely to change repositories.
An employer profile requires a creation decision: retain the observation in the current task until that
decision is supplied; selecting the profile does not satisfy it.
An employer task demonstrates a reusable Core hook defect. Resolve Core as the affected source and
load its selected recording policy and GitHub operation. Record independently supported source facts;
keep employer evidence within the employer task. Template self-repair selects eligible source-side
follow-through while the employer task keeps its goal and owner.
A personal project's ordinary debt uses the same GitHub mechanics under its own policy. Recording it
and updating its board state do not start its implementation.
```
