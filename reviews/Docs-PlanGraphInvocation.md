# Code review — Docs/PlanGraphInvocation

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `589c2c90fc20814dc037673af9870b65a6201028`  `(2026-10-07)`
**Judgment:** `approved`

## Review pass — 2026-10-07 — docs

**Candidate base:** `61d4920477a313528f855babd2e4ee4ccdf3d8f6`
**Candidate head:** `589c2c90fc20814dc037673af9870b65a6201028`
**Candidate branch:** `Docs/PlanGraphInvocation`
**Candidate scope:** `all`
**Candidate path-set:** `.agents/engineering/convention/plans/SKILL.md, .agents/engineering/workflow/plan-authoring/SKILL.md, .agents/engineering/workflow/plan-execution/SKILL.md` `(3 paths)`
**Work-order path:** `reviews/Docs-PlanGraphInvocation.md`
**Work-order mode:** `new`
**Pass judgment:** `approved`

Scope guard: all three changed paths are `.agents/` SKILL.md authored guidance with no runtime, package,
schema, or CI-selection impact — docs-review scope confirmed.

Accuracy lens: `python -B .agents/hooks/plan_graph.py --help` confirms the script accepts only `--root`
and `--json`; `--plan` is not a recognized argument and the previous text's invocation exited 2.
`python -B .agents/hooks/plan_graph.py --root .` was run against the live tree and returns `0 error(s)`
(exit 0), confirming the corrected invocation is accurate. `.agents/hooks/plan_graph.py`'s own module
docstring states "Product-specific pre-launch policy and its --plan CLI remain in the Concertable
adapter" — confirming the Concertable-specific sentences in `plans/SKILL.md` and
`plan-execution/SKILL.md` were misattributing a product-specific flag to this shared script; the fix
separates the claim rather than silently dropping the Concertable guard's existence.

Contradiction lens: no sibling or local guidance conflicts with the corrected command text.

Dangling-reference lens: none of the three edits introduce a reference to a disposable plan, ticket, or
scratch file.

Followability lens: each corrected instruction names one concrete, verified command with no ambiguity
about which script it targets.

Frozen-tree `docs_reachability.py --root .`: 0 errors, 0 warnings.

### Findings

None.
