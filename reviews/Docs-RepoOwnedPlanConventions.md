# Code review — Docs/RepoOwnedPlanConventions

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `19f01b7bcfaff27a8131dad874d8aa3eba80977b`  `(2026-10-07)`
**Judgment:** `approved`

## Review pass — 2026-10-07 — docs

**Candidate base:** `61d4920477a313528f855babd2e4ee4ccdf3d8f6`
**Candidate head:** `19f01b7bcfaff27a8131dad874d8aa3eba80977b`
**Candidate branch:** `Docs/RepoOwnedPlanConventions`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:d32e297df5e77b2700939ed2a4b43aad153dce5ab8220e936ea32debcac05114` `(2 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\lqM2zNM9yS1PwVZvEBnVyU\ZKB9xGZ7Z4CEh171higkzE`
**Candidate bundle identity:** `sha256:8364207666a9fe83080204127c185c59a659ad7e7e3783221ffc15318e27ffff`
**Work-order path:** `reviews/Docs-RepoOwnedPlanConventions.md`
**Work-order mode:** `new`
**Pass judgment:** `approved`

Native layer: Claude Code built-in `code-review` skill (low effort) over the frozen range. No code,
runtime logic, or conditions to evaluate — documentation/policy prose and a new plan file only.
Security layer not required (`first_path` and `trunk_first_path` both null). Routed skills: none.
Frozen-tree `docs_reachability.py`: 0 errors, 0 warnings.

Lenses applied over the frozen patch: accuracy (new `plans/<goal>/` and "active delivery branch's
checkout owns current planning state" wording matches established corpus terms in
`engineering:convention/plans` and the repo's own `plans/<epic>/` layout); contradiction (no conflict
with the unchanged surrounding paragraphs in `base:plan-artifacts`, or with `engineering:convention/plans`,
`workflow/plan-authoring`, or `utility/workboard`, all of which were inspected and already match this
contract); one-rule-one-home (the host-scratch-promotion rule belongs in `base:plan-artifacts` because it
is the common contract that must hold even without the richer engineering lifecycle selected; no
duplication introduced elsewhere); recurring-context concision (every added clause states a new decision
from the authorizing proposal, not narration); dangling references (the new text names a generic
convention, not this branch's own disposable plan file); followability (clear actor/action/pass condition
in each added clause).

### Findings

No findings.

### Disposition — 2026-10-07

Approved with no findings. `tests/test_plan_artifacts.py` (4) passes against the regenerated contract;
`scripts/sync_harness_manifests.py --check` confirms no harness-manifest update is required for this
unchanged delivery mechanism.
