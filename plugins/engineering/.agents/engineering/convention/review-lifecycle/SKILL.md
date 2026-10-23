---
name: review-lifecycle
description: Own the canonical per-branch review work order, its immutable candidate identity, in-progress and complete states, finding statuses, permitted remediation mutations, merge retention, and deletion after the branch lands. Use when producing, staging, incrementally extending, addressing, gating, or retiring a review artifact.

kind: convention
domain: process
---

# Review work-order contract

A review file is one branch's live work order, not an archive. Ordinary full, incremental, documentation
and combined reviews use an editable body in repository-private Git state. Resolve its absolute path with
`<engineering>/workflows/workflow_ops.py --root <checkout> --workflow-run-id <id> review-path`; never assemble a machine-local path.
Staged reviews use `review-path --durable`, retaining `reviews/<branch-slug>.md` with `/` replaced by `-`.
That operation promotes an existing private body without losing its findings. Existing durable work orders
remain canonical through their lifecycle. If the user names a path, resolve it and reject it unless it
equals the runtime's derived canonical path exactly. Selectors never create competing artifacts.

The strong parent finalizes an ordinary review with `review-record --descriptor <descriptor-path>
--work-order <canonical-work-order>` on the same workflow command. It verifies frozen-head completion and
host coverage, then atomically writes a Git-private receipt binding repository, checkout, branch, exact
head, descriptor identity and body hash. Editing the body invalidates that receipt until a reviewed pass
is completed again. All merge and delivery readers use the same resolver; invalid private evidence never
falls back to a committed or local durable file. Legacy durable evidence remains readable during migration.
Private proof requires the exact head; legacy review-only transport compatibility does not extend it.

The strong parent is the sole writer. Native review and fresh lenses return candidate evidence only. They
never edit the file, assign final severity, approve the change, or see one another's conclusions.

## Workflow preparation and completion

This evidence contract applies when a workflow needs a recorded review, including staged and incremental
passes. A standalone `review` returns its assessment without creating this state. An implementation owner
synchronizes once with its actual base before freezing; a review-only owner does not mutate the branch.
Use `python` on Windows or `python3` on Linux/macOS for these installed-package commands:

```bash
python <engineering>/workflows/workflow_ops.py --root <repository-root> --workflow-run-id <id> review-prepare --base <actual-base> --head HEAD --synchronize
```

Omit `--synchronize` for a review-only candidate. The helper returns the descriptor, binary patch, exact
path manifest and exported frozen tree. Preserve its immutable identities and use one concurrent wave
for independent native, specialist and security checks. Validate bounded `review-lens` results against
Workflow v2; an unavailable or invalid dispatch returns the same check to the parent after one focused
recovery. The parent verifies evidence, assigns severity and writes the one work order.

For an agent-surface candidate, add the moving coverage record defined by `workflow:plan-artifacts`, then run
`<engineering>/workflows/workflow_ops.py review-host-check --descriptor <descriptor-path>
--work-order <canonical-work-order>` with the same root and run id. Failure leaves the pass incomplete.

The descriptor's `security.first_path` requires security review. Its `trunk_first_path` also requires it
when the prior security marker is absent, unresolvable or followed by a sensitive change. Review
`<trunk_base>..<frozen-head>`, or `<frozen-base>..<frozen-head>` when no trunk base exists. Stamp the security
marker only after that evidence passes synthesis and the whole pass completes.

Set the current and active-pass judgments, complete status and exact frozen-head watermark only after
every required check completes. Run `review-record --descriptor <descriptor-path>
--work-order <canonical-work-order>` before removing the bundle. Failure keeps delivery blocked. Remove
the disposable bundle after completion, cancellation or terminal failure; an interrupted pass regenerates
it from its descriptor and reproduces its identity before resuming. Remediation remains `address-review`
followed by a fresh `incremental-review` pass under the calling workflow's authority.

## Immutable pass identity

Freeze every non-empty review pass before dispatching:

- full base SHA and full head SHA;
- target branch and candidate scope, recorded as `all` or the exact bounded path or region;
- the exact sorted changed-path set, represented by its SHA-256 digest and file count; encode each path as
  UTF-8, join paths with one NUL byte, and do not add a trailing NUL; and
- the SHA-256 of the binary base-to-head patch, routed technical-rule identity hashes, selected lens set,
  and the single pre-review synchronization record when implementation owns the review; and
- the canonical work-order path and whether the pass is new or appended.

Before review dispatch, materialize a disposable candidate bundle outside the working tree. It contains an
exported frozen-head tree, the exact binary full-index base-to-head patch, the exact NUL-delimited path
manifest used for the path-set digest, and a canonical UTF-8 identity manifest. The identity manifest records
the pass descriptor, frozen tree object ID, and SHA-256 hashes of the patch and path manifest; its own
SHA-256 is the candidate-bundle identity. Record the bundle path and identity as immutable artifacts.

Derive every diff, native review, security review, routed rule set, guidance read, lens dispatch, and final
marker from the descriptor and materialized bundle. Do not substitute a later live `HEAD` or working-tree
file. If the branch moves, finish or cancel the frozen pass and review the later delta incrementally.

Movement of the remote base alone does not invalidate this source review. Run
`<engineering>/workflows/workflow_ops.py review-reconcile`, with `<engineering>` as `review` defines it,
against the stored descriptor. A changed candidate head requires incremental review; a base-only change
requires another source review only when it touches a candidate path or a routed rule body. Merge-group
validation remains the authoritative combined-tree check against the current base.

Record the descriptor in the pass section:

```markdown
**Candidate base:** `<full-base-sha>`
**Candidate head:** `<full-head-sha>`
**Candidate branch:** `<branch>`
**Candidate scope:** `all|<exact-bounded-scope>`
**Candidate path-set:** `sha256:<digest>` `(<N> paths)`
**Candidate bundle:** `<absolute-disposable-directory>`
**Candidate bundle identity:** `sha256:<digest>`
**Work-order path:** `<resolved-canonical-path>`
**Work-order mode:** `new|append`
```

The parent validates the materialized bundle when it creates it. Read-only hosts consume the exported tree,
patch, and manifest without requiring Git access or recomputing identities from the live checkout. On
interruption, regenerate the bundle from the recorded descriptor and require the same bundle identity before
resuming. Remove the disposable bundle after pass completion, cancellation, or failed dispatch cleanup.

The moving top-level completion marker is separate:

```markdown
**Reviewed up to commit:** `<full-completed-head-sha>`  `(<ISO date>)`
```

Keep exactly one top-level `Review status` and current `Judgment`; do not repeat either inside pass sections.
Each pass instead has one `Pass judgment`. Set the top-level fields and the active pass to `in-progress`,
`pending`, and `pending` before expensive review work. A first pass has no
`Reviewed up to commit:` marker until it completes. An incremental pass retains the prior completed marker
while its new pass is in progress. On successful parent synthesis, set the status to `complete` and move the
single top-level marker to the frozen candidate head. Set the current and active-pass judgments to
`approved` or `changes-requested`. A completed pass judgment is immutable; a later pass may change only the
top-level current judgment and its own pass judgment.

## Canonical shape

```markdown
# Code review — <branch>

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `in-progress|complete`
**Reviewed up to commit:** `<full-completed-head-sha>`  `(<ISO date>)`
**Judgment:** `pending|approved|changes-requested`

## Review pass — <ISO date> — <full|incremental|docs|staged:area>

**Candidate base:** `<full-base-sha>`
**Candidate head:** `<full-head-sha>`
**Candidate branch:** `<branch>`
**Candidate scope:** `all|<exact-bounded-scope>`
**Candidate path-set:** `sha256:<digest>` `(<N> paths)`
**Candidate bundle:** `<absolute-disposable-directory>`
**Candidate bundle identity:** `sha256:<digest>`
**Work-order path:** `<resolved-canonical-path>`
**Work-order mode:** `new|append`
**Pass judgment:** `pending|approved|changes-requested`

### Findings

- [ ] **<ID> — <SEVERITY> — <lens>** — `file_path:line`
  <verified defect and concrete fix>
```

Use one status vocabulary:

- `[ ]` open;
- `[~]` remediation or staged coverage in progress;
- `[x]` resolved; and
- `[wontfix]` a conscious final disposition whose reason and any required debt entry are recorded.

Do not introduce a second deferred status. Any postponed work is `[wontfix]` here and must use
the selected profile to record debt in the same stroke, linking its record and objective resolution
condition under [the recording contract](../../../workflow/resources/problem-records.md). Keep
review evidence in the work order; ordinary findings do not each require a tracker record.

Use one severity vocabulary. `CRITICAL` is an immediately exploitable security, data-loss, or catastrophic
availability defect; `HIGH` is a likely correctness, security, or boundary failure with material impact;
`MEDIUM` is a concrete defect with limited impact or reach; and `LOW` is a concrete rule violation or
regression with small impact. Every retained severity is actionable; confidence and uncertainty stay
separate from severity.

Append every later pass with the same `## Review pass` heading shape and a nested `### Findings` section.
Finding IDs remain unique across the whole file. A pass with no findings states that explicitly below its
heading rather than creating another top-level findings section.

Staged reviews add `## Coverage`, `## Rules manifest`, `## Cross-area notes`, and this exact state to the
same artifact:

```markdown
## Parent finalization

**Cross-area notes status:** `pending|complete`
**Parent summary status:** `pending|complete`

<parent summary, written when status becomes complete>
```

Keep exactly one top-level field of each kind. Create both as `pending` on the first staged pass and reset
them to `pending` when a later staged wave begins. Cross-area notes use `[ ]`, `[~]`, and `[x]` and
their status becomes `complete` only when every note is terminal. Coverage entries use the same vocabulary;
the work-order status remains `in-progress` until every area and note is complete. If every area is `[x]`
but cross-area notes status, parent summary status, judgments, status, or a required watermark are
incomplete, the pass is in the explicit `parent-finalization` resume state rather than complete.

## Permitted mutations

- The review parent creates pass identity, records verified findings, deduplicates, assigns severity, writes
  the final judgment, and stamps completion.
- `incremental-review` appends a pass and moves the marker only after that pass completes.
- `address-review` may change a finding's status and append disposition or fix evidence. It must not rewrite
  the frozen candidate identity, original finding text, original severity, or any completed pass judgment.
- The merge gate resolves canonical private proof or the existing durable file. It requires a completed status when the field is present, a
  current marker, no `[ ]` or `[~]` item, and a current security marker when applicable.

## Addressing findings

Fix the fixable part immediately. If one finding contains a clear fix and a genuinely blocked remainder,
split them: land the clear fix and carry only the blocked remainder to its durable owner. An already committed
phase, a later test opportunity, low severity, or latency is not a reason to postpone a reversible fix.

Findings stay on the reviewed branch when that branch caused, exposed, worsened, or made the fix necessary.
Move one only when repository evidence proves it pre-existed on the base, the reviewed change neither exposes
nor worsens it, and its repair is independent.

## Retention and deletion

Keep the work order and private receipt, including a clean no-find review, through merge because they are
the local merge gate's evidence. On interruption, resolve that same body and receipt; retain the immutable
descriptor and regenerate its bundle only when review work must resume. Missing proof never implies approval.
They are spent only after the branch merges or is deliberately retired and every finding is terminal. Then
remove the private body and receipt or untracked durable file. Delete a tracked artifact in the next
substantive or final closeout commit; never create a review-only cleanup commit or publish ordinary proof.

An artifact with open findings or incomplete staged coverage remains live. A review is never kept as a
permanent record after its branch is terminal; Git, the PR, durable debt, and the merged changes own history.
