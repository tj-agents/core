# Code review — Fix/GoalWideMergeApproval

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `7da0ed7827705dee3873bc44046130e4a1ab97e2`  `(2026-10-06)`
**Judgment:** `changes-requested`

## Review pass — 2026-10-06 — docs

**Candidate base:** `fb365abb8478a87eb8f0129312c839b05debbc0a`
**Candidate head:** `7da0ed7827705dee3873bc44046130e4a1ab97e2`
**Candidate branch:** `Fix/GoalWideMergeApproval`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:7d9f0d580d73cca333c592456a7ff41b7dfc83dfd49fded05d2cea2828952a48` `(9 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\goal-wide-merge-approval-review\review\beca2ac994d1971aa78a6a259b1f5ba8faa0d42e437447602080752da95e0006`
**Candidate bundle identity:** `sha256:bc5c630a397f67c88f5a54c3b6a416728e42fae3d815b319b08e0c6e87c8737e`
**Work-order path:** `reviews/Fix-GoalWideMergeApproval.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Native layer: built-in `code-review` skill (high) over the frozen range. Fresh lens: documentation
(accuracy, contradiction, one-rule-one-home, concision, dangling references, followability).
Mechanical: `docs_reachability.py` on the bundle tree — 0 errors; tier gate — no stack tier applies.
Parent verified the lens's uncovered siblings (committing, remote-validation, git-branching,
merge-docs, session-guidance) by direct grep of their merge-authorization lines: all consistent.

### Findings

- [x] **GW1 — MEDIUM — followability** — `.agents/engineering/policy/persistent-delivery/SKILL.md:67`
  The binder paragraph tells the agent to write the goal authorization as the approval record but gives
  no rule for the required `mode` when the goal authorization names none; `scoped_approval()` rejects
  anything but `merge`/`auto`, so the agent must guess between arming unattended auto-merge and blocking
  delivery. Fix: state that a goal authorization naming no mode records `auto` — unattended completion
  is what a goal authorization requests; stop classes and holds still gate.
- [x] **GW2 — MEDIUM — test-coverage** — `.agents/hooks/tests/test_process_standards.py:214`
  The referrer loop asserts only that the token `engineering:merging` appears somewhere in each referrer,
  which `merge/SKILL.md` satisfied three times before this change — reverting any pointer leaves the test
  green. Fix: assert each referrer's specific pointer sentence.
- [x] **GW3 — LOW — contradiction** — `.agents/engineering/policy/merging/SKILL.md:15`
  "survives … successive delivery bindings" reads against persistent-delivery's unchanged rule that the
  record cannot carry into another PR; the authority survives, the record is rewritten. Fix: add the
  re-record clause so the mechanics are stated where the rule lives.
- [x] **GW4 — LOW — accuracy** — `.agents/engineering/policy/merging/SKILL.md:17`
  The directive to read "explicit authorization" anywhere as this rule quotes a phrase this same patch
  removed from the corpus (verified: only the test's negative assertion still carries it) and over-rewrites
  legitimate narrower constructs (an observed exact-PR approval remains a valid authority source). Fix:
  replace with "no delivery standard adds a per-PR approval requirement on top of it"; update the test
  phrase.
- [x] **GW5 — LOW — followability** — `.agents/engineering/policy/persistent-delivery/SKILL.md:41`
  "the owning goal's recorded user authorization" names no concrete artifact, unlike the other two
  sources (standing table file, approval-record schema). Fix: point at the owning goal record, which the
  same document already names as keeping the goal's authorized actions.
- [x] **GW6 — LOW — contradiction** — `plans/external-goal-continuation/EXTERNAL_GOAL_CONTINUATION.md:81`
  The live plan artifact still mandates the overturned sentence ("a goal file's existence or
  implementation approval never invents merge authority"). Fix: reconcile that clause to the new rule.
  Deliberately not added to the corpus test: plans legitimately quote defective wording when recording
  defects, so a phrase sweep over `plans/**` would misfire.
- [x] **GW7 — LOW — concision** — `.agents/base/policy/goal-continuation/SKILL.md:27`
  The rewrap left "applicable existing gate;" as an orphan fragment line in an always-loaded policy.
  Fix: rewrap the paragraph.
- [x] **GW8 — LOW — followability** — `.agents/engineering/convention/plans/SKILL.md:78`
  The appended pointer sentence is bolted onto the typed-gate paragraph with no stated relation (same
  shape in plan-execution). Fix: fold the pointer into the continue-to-merged sentence it qualifies.

Disposition: all eight fixed in one remediation commit. GW1: binder records `auto` when a goal
authorization names no mode. GW2: referrer loop now pins each pointer sentence and the mode default.
GW3: merging states the per-PR binding re-record is mechanics, not a fresh approval. GW4: dead-quote
directive replaced with "no delivery standard adds a per-PR approval requirement"; test phrase updated.
GW5: binder points at the owning goal record. GW6: plan clause reconciled to the new rule. GW7: paragraph
rewrapped. GW8: pointers folded into the sentences they qualify. Validation: test_process_standards
21/21, test_goal_continuation + test_plan_artifacts 8/8.
