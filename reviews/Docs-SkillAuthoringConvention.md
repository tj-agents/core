# Code review — Docs/SkillAuthoringConvention

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `4236f6f2a25bcf0ff2df5558a08dc64a05bc0fd3`  `(2026-10-10)`
**Judgment:** `changes-requested`

## Review pass — 2026-10-09 — full

**Candidate base:** `49c618c5204140629df7a78dd7f8e47a0bfe749f`
**Candidate head:** `4d63fe82046f99aebd87651c8f35a6f1355ec983`
**Candidate branch:** `Docs/SkillAuthoringConvention`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:150f88b807ff2652b7fe72bc65de176af224202b3fd519b3557107d4a89559a5` `(11 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/1YNaq4-UxodIoI1tf3dVbi/ITq8s8qMeeBeQFxq0E7EbQ`
**Candidate bundle identity:** `sha256:8e7232eb6aa01d2cb58847ac89c610a1fca7679e124a1c76f860a4421ab06875`
**Work-order path:** `reviews/Docs-SkillAuthoringConvention.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Synchronization: one pre-review synchronization against `origin/main` (behind 0). Routed rules:
`engineering:skill-authoring`. Lenses: native-general (Claude Code `code-review`, medium), workflow (parent). Security layer: not required (no
security path in the frozen or trunk range).

### Findings

- [x] **F1 — HIGH — native-general** — `.agents/skill-routes.json:1`
  Carrying a route table opts all of core into write-time routing. `skill_router.py` (`missing_routed_skills`)
  blocks every write in the repository, not only `SKILL.md`, while any routed skill is unresolved or
  plugin discovery fails, and `red_run_gate.has_jurisdiction` then gates every red test run in core. Until
  a release ships `engineering:skill-authoring`, and on any host whose discovery fails, every session in
  core stops writing. Fix: remove the route table and its test; keep discovery in the description and
  `AGENTS.md`, and record the decision in the goal.
  Fixed: route table and its test removed; the goal records why.
- [x] **F2 — LOW — native-general, workflow** — `.agents/engineering/convention/skill-authoring/SKILL.md:48`
  "The generator ... rejects two names that are equal once their hyphens are removed" holds only for core's
  generator; kit's check has its own folder-naming rules and no such check, so a kit-layout author could
  rely on a check that does not exist. Fix: attribute the hyphen check to core's generator and name
  `kit:check`'s naming rules for kit-layout repositories.
  Fixed: the hyphen check is attributed to core's generator, and kit's rules are said not to catch it.
- [x] **F3 — LOW — native-general** — `AGENTS.md:26`
  The new instruction names a skill that no installed release ships until the post-merge regeneration is
  installed, so `Skill(engineering:skill-authoring)` fails in the meantime. Fix: link the canonical
  definition path as `SKILL_KINDS.md` does.
  Fixed: `AGENTS.md` links the canonical definition.

Dropped after verification: alias-name collisions (hypothetical, no current alias clashes), route anchoring
and the route test's root (moot once F1 removes the table), and the `engineering:docs-and-debt` reference
(valid on `main`; #173 keeps that name as a routing entry and its owner is told to retarget it).

## Review pass — 2026-10-09 — incremental

**Candidate base:** `4d63fe82046f99aebd87651c8f35a6f1355ec983`
**Candidate head:** `33898c46c0585ce7f8d5ebcf31ca66906079a170`
**Candidate branch:** `Docs/SkillAuthoringConvention`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:37fefa4f557bbc4ca54f1600b62f66fed221762914e0fe0fe5b090dfb5a13042` `(6 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/Q-yMKrePaQWLa-Xc8_bweO/n9wzgnoPiAF_-ETcEFTFhb`
**Candidate bundle identity:** `sha256:8ea0ac0a6448fb62066774adc586cf04151a9330154db0d43c6410f433e81545`
**Work-order path:** `reviews/Docs-SkillAuthoringConvention.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Remediation of F1–F3. No routed rules (the route table is removed); security layer not required.

### Findings

- [wontfix] **F4 — MEDIUM — native-general** — `plans/skill-authoring-convention/GOAL.md:87`
  Removing the route table also removes the only automatic review-time trigger: `review-prepare` names
  routed skills only from a route table, so a review of a changed `SKILL.md` need not load the convention.
  Fix: a review-only route. Disposition: that is a router and workflow-runtime change outside this slice;
  recorded in `docs/workflows/TECH_DEBT.md` ("Review routing requires the write-time opt-in") with its
  resolution condition, and the goal links it.
- [x] **F5 — LOW — native-general** — `plans/skill-authoring-convention/GOAL.md:57`
  Completion step 3 still lists the route table as a discovery mechanism. Fix: point it at the Decisions.
  Fixed.
- [x] **F6 — LOW — native-general** — `plans/skill-authoring-convention/GOAL.md:119`
  Next Steps still points at a full review. Fix: point at the incremental pass and the PR. Fixed.
- [x] **F7 — LOW — native-general** — `plans/skill-authoring-convention/GOAL.md:107`
  Progress keeps pre-removal test counts and records no re-validation. Fix: record the re-run. Fixed.
- [x] **F8 — LOW — native-general** — `.agents/engineering/convention/skill-authoring/SKILL.md:50`
  The F2 fix asserts how kit's check behaves (an unowned claim about another repository) and leaves a
  kit-layout author no instruction to check within the repository. Fix: drop the kit claim and tell the
  author to check for a hyphen-only near miss wherever generation does not. Fixed.

## Review pass — 2026-10-09 — incremental

**Candidate base:** `33898c46c0585ce7f8d5ebcf31ca66906079a170`
**Candidate head:** `9c8168e9eca015e54ca1f8be73d0e5cc9f4f7597`
**Candidate branch:** `Docs/SkillAuthoringConvention`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:d74fc481d824915c190fa73044655de1c1c4d0cc5192c7864b4baddf48d16435` `(4 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/GYTEcEeUHOsjEMuMk7MGfk/hOPHXB-tZr2pFxAkDqIOnK`
**Candidate bundle identity:** `sha256:f7accff75597f2e4add7b8fa2a5f2510fc3b0931a985d86fdca94bf257586980`
**Work-order path:** `reviews/Docs-SkillAuthoringConvention.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Remediation of F4–F8. Security layer not required.

### Findings

- [x] **F9 — LOW — native-general** — `.agents/engineering/convention/skill-authoring/SKILL.md:68`
  "A kit-layout repository generates its host entry points instead" is still an unowned claim about kit.
  Fix: defer to the repository's layout owner. Fixed.
- [x] **F10 — LOW — native-general** — `.agents/engineering/convention/skill-authoring/SKILL.md:50`
  "Where generation does not" is ambiguous and limits the within-repository check to hyphen near misses,
  while the installed-plugin check need not include the repository being authored. Fix: one near-miss
  check over this repository's skills and every installed plugin. Fixed.
- [x] **F11 — LOW — native-general** — `plans/skill-authoring-convention/GOAL.md:109`
  No re-validation is recorded after `9c8168e` changed a shipped `SKILL.md`. Fix: re-run generation,
  catalog, harness, packaging and both suites and record it. Fixed (803 + 983 tests, every check green).

Dropped: the debt entry describing the opt-in it records (a debt entry must state its problem); the
unwrapped step-3 line and the unexplained test count were fixed in passing.

## Review pass — 2026-10-10 — incremental

**Candidate base:** `9c8168e9eca015e54ca1f8be73d0e5cc9f4f7597`
**Candidate head:** `244570bad7a8dc51c48fde3369225ac060ea9c6b`
**Candidate branch:** `Docs/SkillAuthoringConvention`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:6ec04f82f9d57ff5009efdd8882849797568b458c9e86959b282823b620dbd3e` `(3 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/s4pRz9qR4x3W_EJY_ht52c/Ir5lPrlGLFI9dH7c3l181S`
**Candidate bundle identity:** `sha256:e460f462a5b5ecfac78401ccb8de2012cdd89643089dd5c6fa16258423fc955f`
**Work-order path:** `reviews/Docs-SkillAuthoringConvention.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Remediation of F9–F11. Security layer not required.

### Findings

- [x] **F12 — LOW — native-general** — `.agents/engineering/convention/skill-authoring/SKILL.md:54`
  The rewritten naming paragraph was not rewrapped (151 characters). Fix: rewrap. Fixed.
- [x] **F13 — LOW — native-general** — `.agents/engineering/convention/skill-authoring/SKILL.md:54`
  "No generator sees other plugins" is wrong in core, whose generator pools base, engineering and machine.
  Fix: "Generation sees only this repository's plugins". Fixed.
- [x] **F14 — LOW — native-general** — `.agents/engineering/convention/skill-authoring/SKILL.md:50`
  "One hyphen away" is narrower than the hyphen-equality case core's generator checks. Fix: "differs only
  by hyphens". Fixed.
- [x] **F15 — LOW — native-general** — `.agents/engineering/convention/skill-authoring/SKILL.md:68`
  The layout-owner sentence repeats the pointer in the owner list. Fix: drop it. Fixed.

Dropped: the `kit:check` owner link (linking the owner is the rule), the debt entry's verified kit fact
(evidence, not a rule), and the plan's re-validation note (true; Next Steps records the pending review).
Re-validated: 803 + 983 tests, generation, tier payload, catalog, harness, packaging and reachability.

## Review pass — 2026-10-10 — incremental

**Candidate base:** `244570bad7a8dc51c48fde3369225ac060ea9c6b`
**Candidate head:** `2a4b65f436d81222680c23409d3347838618207a`
**Candidate branch:** `Docs/SkillAuthoringConvention`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:6ec04f82f9d57ff5009efdd8882849797568b458c9e86959b282823b620dbd3e` `(3 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/v3rYiTkyIOhoeQj6iSPJsi/xl4dqA3H1psXLoavbxDx9G`
**Candidate bundle identity:** `sha256:7db4909bbb8fcc71446d958d9ac57ef2ccbb400cffe2383f6330cb81533fa5a5`
**Work-order path:** `reviews/Docs-SkillAuthoringConvention.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Remediation of F12–F15. Security layer not required.

### Findings

- [x] **F16 — LOW — native-general** — `.agents/engineering/convention/skill-authoring/SKILL.md:66`
  Description parity is said to fail generation for every authored entry point, but entries listed in
  `extended_host_adapters` are compared on name, kind and domain only. Fix: scope the guarantee to plain
  entry points and tell authors to review an extension's description by hand. Fixed.
- [x] **F17 — LOW — native-general** — `.agents/engineering/convention/skill-authoring/SKILL.md:55`
  A near miss must be renamed while an exact clash with another publisher is allowed. Fix: choose a
  different name for either; qualification applies only where a clash already exists. Fixed.

Dropped: restoring the removed layout sentence (the owner list already covers it), the "only this
repository's plugins" bound (accurate), the 112-character line (a URL), and a duplicated plan note
(removed). Re-validated: 803 + 983 tests and every generation check.

## Review pass — 2026-10-10 — incremental

**Candidate base:** `2a4b65f436d81222680c23409d3347838618207a`
**Candidate head:** `1dd4c1629152038e2da0d16630d473ccdb436879`
**Candidate branch:** `Docs/SkillAuthoringConvention`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:6ec04f82f9d57ff5009efdd8882849797568b458c9e86959b282823b620dbd3e` `(3 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/7gOJuKgT5DaKS7lo_0Z2Tp/_jGm3h8eDJJkt7uYo0B3ig`
**Candidate bundle identity:** `sha256:1902c5dce1c7f227aded15883c739f6a6408deb20eac5e3bf0c061b5f7035dcf`
**Work-order path:** `reviews/Docs-SkillAuthoringConvention.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Remediation of F16–F17. Security layer not required.

### Findings

- [x] **F18 — LOW — native-general** — `.agents/engineering/convention/skill-authoring/SKILL.md:67`
  "Plain entry point" and "registered as a host extension" are undefined, so an author cannot tell which
  entry points generation checks. Fix: say "thin" and name `extended_host_adapters` in
  `.agents/plugins/sources.json`. Fixed.

Dropped: self-matches against this repository's installed copies (the check governs choosing a new
name), a later third-party clash (covered by "already shared"), and the split ledger line (tidied).
Re-validated: 803 + 983 tests and every generation check.

## Review pass — 2026-10-10 — incremental

**Candidate base:** `1dd4c1629152038e2da0d16630d473ccdb436879`
**Candidate head:** `975460a6fc4288a19c206c07bdd78194c82717ec`
**Candidate branch:** `Docs/SkillAuthoringConvention`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:6ec04f82f9d57ff5009efdd8882849797568b458c9e86959b282823b620dbd3e` `(3 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/o4qhwkab2bNUQXX-f68KOt/fRoP0dfumXfXJaLSU4P-pZ`
**Candidate bundle identity:** `sha256:2bea072d610a527aa550ca3279e2432365ef6561df58d97a747a57d6a1cf0e64`
**Work-order path:** `reviews/Docs-SkillAuthoringConvention.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Remediation of F18. Security layer not required.

### Findings

- [x] **F19 — LOW — native-general** — `.agents/engineering/convention/skill-authoring/SKILL.md:68`
  "Change ... every host entry point" contradicts the next sentence's exception for host extensions,
  and the paragraph names core-internal configuration in a generic convention ("thin" stays undefined).
  Fix: one generic rule (update every authored copy in the same commit) and defer which entry points
  repeat or rephrase the description, and what generation checks, to the layout owner. Fixed.

Re-validated: 803 + 983 tests and every generation check.

## Review pass — 2026-10-10 — incremental

**Candidate base:** `975460a6fc4288a19c206c07bdd78194c82717ec`
**Candidate head:** `c84ae5b8bcdc72ed43fb3d5ac2a58c06c07527b0`
**Candidate branch:** `Docs/SkillAuthoringConvention`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:6ec04f82f9d57ff5009efdd8882849797568b458c9e86959b282823b620dbd3e` `(3 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/3IIaht-Db6hLaXo-rAt51W/ANulOW8oydLTzbZbRrhpd2`
**Candidate bundle identity:** `sha256:09bff7468a6bed465bc9e96ea7d8339e181ac4826b8ec7065237c02ef9400d02`
**Work-order path:** `reviews/Docs-SkillAuthoringConvention.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Remediation of F19. Security layer not required.

### Findings

- [x] **F20 — LOW — native-general** — `.agents/engineering/convention/skill-authoring/SKILL.md:68`
  The convention defers description parity to the layout owner, but `SOURCE_LAYOUT.md` does not state
  it, and the hand review of a host-worded description is no longer said anywhere. Fix: state the parity
  rule and the `extended_host_adapters` exception, with its hand review, in `SOURCE_LAYOUT.md`, and have
  the convention say to update repeating entry points and review rewording ones. Fixed.

Re-validated: 803 + 983 tests and every generation check.

## Review pass — 2026-10-10 — incremental

**Candidate base:** `c84ae5b8bcdc72ed43fb3d5ac2a58c06c07527b0`
**Candidate head:** `4236f6f2a25bcf0ff2df5558a08dc64a05bc0fd3`
**Candidate branch:** `Docs/SkillAuthoringConvention`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:b58cac523513586fc80176dc1f1a0038ddd265540b6fdf6de8db990cc42f49b0` `(4 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/pIPNksfWCO1e-FnP1TYfAX/pAszdJXgov3KyFS51k1nVG`
**Candidate bundle identity:** `sha256:1445aae7aae854a932a4022a1db7b616178828e4446b0abb6535852894737674`
**Work-order path:** `reviews/Docs-SkillAuthoringConvention.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Remediation of F20. Security layer not required.

### Findings

- [x] **F21 — LOW — native-general** — `SOURCE_LAYOUT.md:34`
  The new parity paragraph enumerates generator checks incompletely ("checks only its name, kind, domain
  and single canonical reference" omits the roster and lane/model checks) and calls a per-skill list
  per-entry-point. Fix: state the rule and the exception per skill, and name `validate_adapters` as the
  enforcement instead of enumerating it. Fixed.

Dropped: a description-hash gate for extended adapters (an enhancement; the hand review is the stated
rule), the claimed conflict with "may add only host-specific metadata" (a host-worded description is
host-specific metadata), and the convention sentence the plugin debt entry already names for removal.
Re-validated: 803 + 983 tests and every generation check.
