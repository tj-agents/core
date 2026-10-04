# Code review — Fix/DefectHandoffDefault

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `ac6ae88221ba87bfd23676b1490be5a046251575`  `(2026-10-04)`
**Judgment:** `approved`

## Review pass — 2026-10-04 — docs

**Candidate base:** `06480cfbdf376fac825e4b0581f3b4b6a8e0f5a2`
**Candidate head:** `ce82032084b320f0101e12db3ca050a6c88801b0`
**Candidate branch:** `Fix/DefectHandoffDefault`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:23eb7bec86e71c0948352501eb82086e1b0cd9da6ba6174e99561ae0b6c5eb70` `(12 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\docs-review-defect-handoff-default\review\85654ace753484b18788dfadf1760179fc4e5822520a093fe7700f29eda772b5`
**Candidate bundle identity:** `sha256:eda4104d220b03c2b32f2f8343d19764cd1a6c5e5b64198395ad4709c7bfb095`
**Work-order path:** `reviews/Fix-DefectHandoffDefault.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Native layer: Claude Code built-in `code-review` skill over the frozen range. Lenses dispatched:
accuracy, contradiction, one-rule-one-home, concision, followability. Security layer not required
(`first_path` and `trunk_first_path` both null). Routed skills: none returned by review-prepare.
Tier gate: no stack tier conventions apply. Frozen-tree `docs_reachability.py`: 0 errors, 0 warnings.
Accuracy lens: no findings (all skill references resolve; test assertion matches the new sentence).

Dropped at synthesis: defining "standards package" inline (would embed a plugin roster in a generic
always-loaded contract; the term is established corpus vocabulary in `base:plan-artifacts` and
PACKAGING.md); relocating the rule to `base:plan-artifacts` (the rule's action is launching
`engineering:handoff`, so it lives where that capability exists — a session without engineering
correctly falls back to record-and-report); the diagnose/Diagnose verb repetition (classification
followed by directive, intentional).

### Findings

- [x] **INST1 — HIGH — followability** — `.agents/engineering/contract/session-guidance/SKILL.md:61`
  Two conflicting authority sources: "whatever authority the current task carries" reads as inheriting
  (and capping to) the task's own authority, while the next sentence grants "this standing
  authorization" unconditionally; handoff's trigger simultaneously calls the authorization "separate".
  Three lenses hit this root (followability, concision splice, cross-file mismatch with handoff).
  Fix: drop the parenthetical; write "without asking, even when the current task itself grants no
  implementation authority" and open the next sentence "This rule is the standing authorization: it
  covers…" so the rule itself is the single stated source.
- [x] **CON1 — MEDIUM — contradiction** — `.agents/engineering/contract/session-guidance/SKILL.md:11`
  The unchanged preamble "They do not grant implementation, publication or installation authority"
  directly contradicts the new standing authorization below it; a session citing the preamble has
  textual grounds to refuse the handoff — the original incident's failure mode. Fix: append "beyond
  the standing standards-defect default below".
- [x] **CON2 — MEDIUM — contradiction** — `.agents/base/contract/plan-artifacts/SKILL.md:38`
  "Neither a ready plan nor this contract authorizes publication, installation, or other actions
  outside that request" still lets a planning-only session refuse the standards-defect handoff — one
  of the exact misreads the plan diagnosed. Fix: extend to "outside that request or another standing
  authorization".
- [x] **INST2 — MEDIUM — followability** — `.agents/engineering/contract/session-guidance/SKILL.md:60`
  "record it" has no destination and collides with the same section's no-second-ledger rule: a session
  may write a debt entry for a defect the handoff's goal already records. Fix: drop "record it"; name
  the side workstream's goal as the record ("whose goal records the defect").
- [x] **INST3 — MEDIUM — followability** — `.agents/engineering/contract/session-guidance/SKILL.md:62`
  "merging through the standards repository's gates" does not decide whether the merge completes or
  stops at enqueue, and sits in tension with "publishing outside that repository" since the merge is
  the publish event for consumers. Fix: "merging once that repository's own gates pass".
- [x] **INST4 — MEDIUM — followability** — `.agents/engineering/contract/session-guidance/SKILL.md:63`
  "installing into another scope" does not decide whether the originating consumer repository counts;
  a session could auto-install the fixed package back into the active repo. Fix: "including the
  originating repository's".
- [x] **INST5 — LOW — native** — `.agents/engineering/contract/session-guidance/SKILL.md:61`
  "without asking" carries no carve-out for explicit user limits, contradicting "Honor user limits"
  in the same file and handoff's "Respect explicit user limits". Fix: close the gated list with
  "and explicit user limits still hold".
- [x] **INST6 — LOW — native** — `.agents/engineering/contract/session-guidance/SKILL.md:58`
  The launch is unconditional even when the session is already working in the standards repository on
  that very standard, where handoff forbids offloading an inseparable step. Fix: scope the exception
  with "outside the current goal".
- [x] **CONC1 — LOW — concision** — `.agents/engineering/workflow/handoff/SKILL.md:17`
  "standing like `engineering:session-guidance`'s standards-defect default" breaks parallelism with
  "granted by the user" and forces a re-read. Fix: "or standing, as with
  `engineering:session-guidance`'s standards-defect default".
- [x] **CONC2 — LOW — concision** — `.agents/engineering/workflow/plan-execution/SKILL.md:100`
  "with its own user-granted or standing authorization" restates the authorization taxonomy that
  handoff now owns, and uses "standing" without pointing at its owner. Fix: "with its own
  authorization", leaving the taxonomy to `engineering:handoff`.

### Disposition — 2026-10-04

All ten findings fixed in one coupled remediation (the same rule stated across four files). The
session-guidance paragraph was rewritten once to resolve INST1–INST6 and align with CON1's preamble
fix; CON2 extended `base:plan-artifacts`' authorization sentence; CONC1/CONC2 landed as proposed.
Validation: `sync-generated.ps1 -Check` green after regeneration; `test_process_standards.py` (19),
`test_plan_workflows.py` (19), `test_workflow_contracts.py` (62), `tests/test_plan_artifacts.py` (4)
all OK; no test pins the amended preamble or plan-artifacts sentences. Incremental review of the
remediation delta follows in the next pass.

## Review pass — 2026-10-04 — incremental

**Candidate base:** `ce82032084b320f0101e12db3ca050a6c88801b0`
**Candidate head:** `e58a505a5339f35fb49f73de25fe807b7dcdc9ef`
**Candidate branch:** `Fix/DefectHandoffDefault`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:b8995f44aca4f34cccbfa3870b3cd253ab64bf7c1a37cac40407ecab3a531c08` `(17 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\docs-review-defect-handoff-default\review\db2579ac7b4f8fbb0724078cee341d6f82d6cd7178a6405bf765dd7abcb3103c`
**Candidate bundle identity:** `sha256:74192a5498f8453f890ee8a3f797183ff553d8be2e249cbcfcfbc8f675ee01d5`
**Work-order path:** `reviews/Fix-DefectHandoffDefault.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Native layer: Claude Code built-in `code-review` skill over the delta. Lenses: contradiction,
concision. Security layer not required (`first_path` and `trunk_first_path` both null).

Dropped at synthesis: removing "below" from the preamble (navigational, earns its place); reverting
"as with" to "like" in handoff (re-litigates the prior pass's accepted CONC1); "another" → "a" in
plan-artifacts (low-confidence preference); the preamble-overclaim reading (the lens itself resolved
it as non-contradictory).

### Findings (incremental)

- [x] **INC1 — MEDIUM — contradiction** — `.agents/base/contract/goal-continuation/SKILL.md:26`
  The delta gave plan-artifacts a standing-authorization carve-out but left goal-continuation — the
  continuation owner session-guidance names for exactly this outlive-the-session fix work — flatly
  stating continuation "does not authorize … merging", reading as a revocation of the standing merge
  grant. Fix: "It adds no authority for installation, publication, merging, broader scope, or a new
  external action" — continuation adds nothing; standing grants survive.
- [x] **INC2 — MEDIUM — accuracy/native** — `.agents/engineering/contract/session-guidance/SKILL.md:64`
  "the originating repository's" can be read as the standards repo (where the fix originates),
  inverting which install the gate covers. Fix: "(the consuming repository included)", pairing with
  "consumed standards package".
- [x] **INC3 — MEDIUM — concision** — `.agents/engineering/contract/session-guidance/SKILL.md:58`
  "…or its source repository, outside the current goal, is the exception" attaches the qualifier to
  the repository instead of the defect (native layer found the same). Fix: front the adverbial —
  "Outside the current goal, a defect in …".
- [x] **INC4 — MEDIUM — concision** — `.agents/engineering/contract/session-guidance/SKILL.md:60`
  "bounded side-workstream mode, whose goal records the defect" attaches "whose" to "mode". Fix:
  "(the side workstream's goal records the defect)".
- [x] **INC5 — LOW — concision** — `.agents/engineering/contract/session-guidance/SKILL.md:64`
  Double-"and" list boundary ("…stay gated, and explicit user limits still hold") reads as a fourth
  list item. Fix: parenthesize the scope clause and split with a semicolon. Folded editorial tightening
  from the same lens: "regardless of the current task's own authority", drop "own" from "repository's
  own gates".
- [x] **INC6 — LOW — native** — `.agents/engineering/contract/session-guidance/SKILL.md:11`
  Preamble line exceeded the file's ~100-column wrap. Fix: rewrapped.

### Disposition — 2026-10-04 (incremental)

All six fixed in one coupled wording round before the remediation commit; concision's proposed INC3
wording ("even when it falls outside the current goal") was rejected as inverting the qualifier's
semantics — the fronted adverbial keeps the current-goal exclusion. Validation:
`sync-generated.ps1 -Check` green after regeneration; `tests/test_goal_continuation.py` (4) and
`test_process_standards.py` (19) OK; no test pins the changed sentences. A final incremental pass
over the fixing commit follows.

## Review pass — 2026-10-04 — incremental (2)

**Candidate base:** `e58a505a5339f35fb49f73de25fe807b7dcdc9ef`
**Candidate head:** `ac6ae88221ba87bfd23676b1490be5a046251575`
**Candidate branch:** `Fix/DefectHandoffDefault`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:a0acff6dd52bb04895c0da3e5bc9bf7ef8bd95760d3144e59ae010e5368281ee` `(13 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\docs-review-defect-handoff-default\review\10f318266ebed5d35764238ee62a1ac91ca03676c5940d016b77c7ffadf08493`
**Candidate bundle identity:** `sha256:5d53f4fb824db083c82de9decf28ac6e45b3377c244e6c106f8d171cd7e41bc9`
**Work-order path:** `reviews/Fix-DefectHandoffDefault.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Native layer: Claude Code built-in `code-review` skill over the delta. Lens: contradiction.
Security layer not required (`first_path` and `trunk_first_path` both null).

### Findings (incremental 2)

No findings. The native layer verified the rewritten sentences keep their antecedents and the
generated copies byte-match the authored sources; the contradiction lens checked every reworded
element against session-guidance's own body, handoff's bounded side-workstream section,
plan-artifacts, the rest of goal-continuation, and docs-and-debt, and found the
goal-continuation/session-guidance merge juxtaposition compatible (continuation preserves the
standing grant; it does not manufacture authority).
