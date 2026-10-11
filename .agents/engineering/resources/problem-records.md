# Problem records

Bug, mistake, and debt records preserve an observed problem until its owning repair has objective
evidence. They make the next action explicit; they do not create authority to repair, publish, dispatch,
or schedule work.

## Record shape

Use one stable, kind-local identifier. Keep the identifier when details, priority, state, or repair links
change. The root defaults use `B001` for bugs and `M001` for mistakes; an existing typed register may use
its declared identifier syntax.

Every entry records:

- **Kind:** `bug`, `mistake`, or `debt`.
- **Observed/reported:** the date and concrete observation or direct evidence. Say whether the cause is
  confirmed or unknown; never infer one to complete a record.
- **Impact and priority:** the effect and a reason for its priority. `P0` is critical active harm, `P1`
  is high and urgent, `P2` is routine, and `P3` is low.
- **Source owner:** the component, repository, standards package, or team that owns the causal repair.
- **State:** `open`, `in-progress`, `blocked`, `deferred`, or `resolved`. A register may declare an
  equivalent historic status; `Addressed` means verified `resolved`.
- **Repair link:** the canonical record path, existing goal, session, issue, branch, or PR that owns
  correction, or `none` stated explicitly.
- **Next action:** one concrete action toward resolution.
- **Resolution condition:** an objective condition that proves the record can be resolved.
- **Verification evidence:** observed evidence for the current state and, when resolved, the condition.

For a `blocked` or `deferred` entry, also record the reason, `blocked_by` as `capability`, `dependency`,
`conflict`, or `capacity`, the resolver, and the observable resume condition. A `conflict` names the
other writer and the paths or record it owns. These fields keep an outstanding record actionable without
claiming that a document starts a job.

## Historical entries

Keep existing facts, identifiers, statuses, and learning history intact. New records use the complete
shape above. Before updating or addressing an older entry, reconcile the common fields from observed
evidence before proceeding. A missing cause or source owner remains explicitly `unknown`, with investigation
as the next action; never invent either field to modernize a record. Declared equivalent historic states
remain valid.

## Location and retention

Use a repository-declared problem owner or an existing shared typed register when one exists. Otherwise,
bugs default to the repository-root `BUGS.md`; mistakes default to root `MISTAKES.md`; debt remains in
the owning area's `TECH_DEBT.md` under `engineering:write-debt`. A shared register keeps the kind on
each entry and preserves these fields.

Retain bugs after resolution with their final status and verification evidence. Retain mistakes as learning
history. A linked mistake resolves only when its own prevention condition passes, even when a linked bug or
debt repair is resolved. Delete debt only after the whole entry is verified resolved. When separate owning
areas need separate fixes, each retains its own debt entry and links any shared upstream source repair.

## One causal repair

One causal repair has one canonical repair record. Related incident or debt entries keep their own records
and link to that repair; a link neither creates another repair owner nor starts another job. First reconcile
an existing owner, record, goal, session, or PR before writing a new record or dispatching work. Repeated
reports of the same observation add dated evidence to that record and may update impact or priority. Merge
records only when the shared cause is known. Distinct observations may link to one repair when the evidence
supports it. An unknown cause stays unknown and does not justify a guessed merge.

## Examples

### Capability blocker

`B014` is a `bug`, observed on 2026-10-11: `config-check` emits an invalid host command for a valid
configuration. Cause: confirmed command construction omits the required argument. Source owner:
`tools/config-check`. Impact: consumers cannot run the generated command; `P2` because no active harm is
observed. State: `blocked`; reason: the required host command is unavailable for focused verification;
`blocked_by: capability`; repair link: `BUGS.md#B014`; resolver: the environment owner; resume when the
command reports its supported version. Next action: add the focused command-construction case and run it
when the capability is available. Resolution condition: the repaired command passes the focused case and
the host command accepts it. Verification evidence: the generated invalid command and unavailable-command
result.

### Conflicting writer

`M008` is a `mistake`, observed on 2026-10-11: this session began a second standards correction after
`session-42` had already claimed it. Cause: confirmed duplicate-writer attempt. Source owner:
`engineering/session-guidance`. Impact: parallel edits could produce conflicting guidance; `P2`. State:
`blocked`; reason: `session-42` owns the causal correction; `blocked_by: conflict`; conflicting owner:
`session-42`; conflicting paths: `.agents/engineering/policy/session-guidance/SKILL.md` and
`MISTAKES.md`; repair link: `MISTAKES.md#M008` and `session-42`. Resolver: `session-42`'s owner. Resume
when that result is reconciled or it releases those paths. Next action: append this evidence to the
canonical incident and stop the duplicate writer. Resolution condition: the correction passes its causal
verification and a new task reconciles the existing owner before editing. Verification evidence: the
existing writer lease and attempted duplicate edit.

### Capacity deferral

`B015` is a `bug`, observed on 2026-10-11: a focused test demonstrates a routine formatting defect with
no active harm. Cause: confirmed formatter escapes one valid input. Source owner: `tools/formatter`.
Impact: affected generated text is malformed; `P3` because a documented workaround exists. State:
`deferred`; reason: all available writers are committed to higher-value work; `blocked_by: capacity`;
repair link: `BUGS.md#B015`; resolver: the delivery owner; resume when a writer has capacity. Next action:
schedule the formatter repair under its existing delivery owner. Resolution condition: the focused test
passes and the workaround is unnecessary. Verification evidence: the failing focused test. The record stays
open and does not create a second job.
