# Code review — Fix/ReviewNativeCodeReview

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `9363122`  `(2026-10-01)`
**Judgment:** `approved`

## Review pass — 2026-10-01 — full

**Candidate base:** `bcfa25a4f8377d03442febac838cd8af4ef3ff68`
**Candidate head:** `49b980bbdaf69985d52cddecc69b0798874a4fea`
**Candidate branch:** `Fix/ReviewNativeCodeReview`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:ceda9d2780109dd6c887222b5775414c325355a18e7ba3bf03e7b678b6266290` `(38 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\review-pr74\review\6b4741d65a0b1f0206fe0801c5437e96320b47b3af7418ece0947c33137b8ca9`
**Candidate bundle identity:** `sha256:becb7c1404a433e2dcc4256249799af33f0d9851712a3c841cec41731d1f9045`
**Work-order path:** `reviews/Fix-ReviewNativeCodeReview.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

**Lens coverage:** the native layer was Claude Code's built-in `code-review` (`high 74`, 10 candidates).
The helper selected the `native-general`, `api-contract` and `workflow` lenses. One fresh `review-lens` ran the
workflow and api-contract concerns together (5 candidates). Security layer not required: no frozen path
matches the merge gate inventory. Tier conventions: no stack tier applies to core.

### Findings

- [x] **NR1 — HIGH — native** — `.agents/engineering/workflow/review/SKILL.md:101`
  Stage 3 skips `code-review` whenever the live target's head differs from the frozen head. After
  `review-prepare --synchronize` merges the base locally, the frozen head exists only locally, so a PR
  target never matches. The fallback then fires in exactly the implementation-workflow reviews this
  change targets. Fix: give the native reviewer the frozen range `<base>..<head>` as its target, which
  works locally for both hosts, and drop the head-equality precondition.
- [x] **NR2 — HIGH — native** — `.agents/engineering/workflow/review/SKILL.md:128`
  Stage 4 relies on the descriptor's `rules`, but `review_prepare` keeps only routed names that exist
  under `tree/.agents/skills/`. Plugin-owned routed skills (such as `dotnet:persistence`) and `DENY
  PATTERN HIT` evidence are silently lost in a repository with a route table. Fix: restore the explicit
  router step, run from `<engineering>/hooks/skill_router.py` against the frozen tree.
- [x] **NR3 — MEDIUM — native + workflow** — `.agents/hooks/tier_gate.py:300`
  `installed_declarations` compares the resolved cache root with the unresolved registry `installPath`.
  A junction, symlink or short-name spelling therefore yields `[]` and every tier vanishes, both for
  the gate and for `--conventions`. Fix: resolve both sides in `_key`.
- [x] **NR4 — MEDIUM — native** — `.agents/hooks/tier_gate.py:114`
  Stage 4 runs the gate from the agent shell, where no plugin-root variable is set, so `~/.claude` is
  read before `~/.codex` even in Codex. Fix: put the gate's own install cache (`__file__`'s fifth
  ancestor named `cache`) ahead of the home caches.
- [x] **NR5 — MEDIUM — native** — `.agents/engineering/workflow/incremental-review/SKILL.md:43`
  Claude's `code-review` took only `<PR|branch>`, so an incremental pass or a big-review stage reviewed
  the whole PR under a 10-finding cap, and the delta got little native coverage. Fix: the same frozen
  range target, plus ` -- <scoped paths>` for a bounded stage.
- [x] **NR6 — MEDIUM — native** — `.agents/workflows/workflow_ops.py:483`
  The security classification covers only the review range. The merge gate classifies the head's
  whole range against `origin/main`, so a stack child whose parent layer touched auth paths gets no
  security layer and is then blocked at merge. Fix: union the trunk range and exclude the branch's
  own work order, as the gate does.
- [x] **NR7 — LOW — native** — `.agents/hooks/tier_gate.py:293`
  Project-scoped registry entries count for every project. Fix: count a `projectPath` entry only
  inside its project, and pass the assessed project root to `declarations()`.
- [x] **NR8 — LOW — native** — `tests/test_review_native_layer.py:732`
  The Stage 4 acceptance test reads the developer's real caches and passes on the no-tier message.
  Fix: give it an isolated home and config with a registry-installed and a stale tier, and assert the
  installed convention path.
- [x] **NR9 — LOW — workflow** — `.agents/engineering/workflow/review/SKILL.md:3`
  The `review` description and the `docs-review` intro still say "native/general", which contradicts
  the renamed Stage 3. The guard test misses both. Fix: reword them in canonical and both host
  descriptions, and assert no `native/general` remains.
- [x] **NR10 — LOW — workflow** — `.agents/machine/scripts/prune_plugin_cache.py:592`
  `--notice` help still says only "Throttled", although it now also prints an unthrottled
  superseded-session line. Fix: reword the help.

  **Resolved** NR1–NR10 in `1624018`; each fix is the one named on its finding.

Verified and dismissed during synthesis. A stale-session notice wired only in machine can't see an
engineering-only update: all three packages update together from one marketplace commit, and a process
predating this release can't run new code, which no notice can change. The `merge_review_gate` import
reconfigures stdout to UTF-8, which is what `workflow_ops` emits anyway. Big-review's per-area
`security: yes/no` manifest line is derived per area by the parent, not from the candidate-level field.

## Review pass — 2026-10-01 — incremental

**Candidate base:** `49b980bbdaf69985d52cddecc69b0798874a4fea`
**Candidate head:** `162401871c1a4a6a1ee2a81bced9653dad1d3bf6`
**Candidate branch:** `Fix/ReviewNativeCodeReview`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:63c98f65e726fe023370cd19f24c0d5d148033735d4e3ee70d1c0f7bbe9b83e6` `(33 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\review-pr74-inc1\review\44f54f551e38bfad5478a36c357eed1f03d635bfa16e68d10d4e0d9c4d53a8d1`
**Candidate bundle identity:** `sha256:d376146c7bcbbbdbe16e8db1946d881db2f441571328f7afc7de45e0d921fdc8`
**Work-order path:** `reviews/Fix-ReviewNativeCodeReview.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

**Lens coverage:** the native layer was Claude Code's built-in `code-review`, run against the commit range
`49b980b..1624018` as its target. It reviewed exactly that delta, which confirms that a range target works.
It returned 10 candidates. The helper-selected `workflow` lens was covered by the native pass and parent
synthesis over the same delta. No new path is security-sensitive.

### Findings

- [x] **NR11 — MEDIUM — native** — `.agents/workflows/workflow_ops.py:379`
  The classification excluded the branch's own work order, but the gate's first sensitivity check
  (`touches_security(changed_against_main(head))`) counts it. A branch named for auth work would be
  told it needs no security layer and then blocked at merge. Fix: classify exactly what the gate
  classifies, with no exclusion.
- [x] **NR12 — MEDIUM — native** — `.agents/workflows/workflow_ops.py:358`
  Merging the trunk range into one `required` flag let a security marker certify paths that the frozen
  scope never reviewed. Fix: report `first_path` (frozen paths) and `trunk_first_path` (gate range)
  separately. Stage 6 runs on `first_path`, or on `trunk_first_path` in a new work order, and covers
  the head's range against the trunk.
- [x] **NR13 — MEDIUM — native** — `.agents/engineering/workflow/review/SKILL.md:133`
  NR2's prose router call passed every path through argv, which overflows on Windows and drops `-`
  prefixed paths, and it duplicated the helper's own router call. Fix at the cause: `review-prepare`
  keeps every routed name (`routed_skills`, plugin-owned included) and the deny hits
  (`route_violations`), and Stage 4 reads those.
- [x] **NR14 — LOW — native** — `.agents/hooks/tier_gate.py:167`
  Between a user-scope and a project-scope install, the newer mtime won. Fix: an install scoped to the
  assessed project replaces the user-scope install.
- [x] **NR15 — LOW — native** — `.agents/hooks/tier_gate.py:133`
  `_key` resolved every path on every PreToolUse call. Fix: compare cheaply first, and resolve only
  the project once and the ancestors that fail the cheap match.
- [x] **NR16 — LOW — native** — `.agents/workflows/workflow_ops.py:379`
  The work-order slug was rebuilt from `git branch --show-current`, which is wrong on a detached HEAD.
  The docstring also narrated the design. Fix: both are removed along with NR11's exclusion.
- [x] **NR17 — LOW — native** — `.agents/engineering/workflow/review/SKILL.md:97`
  ` -- <scoped paths>` is not a documented `code-review` target form. Fix: verify it on the next pass,
  and fall back to the range alone, with parent path filtering, if it is not honoured.

  **Resolved** NR11–NR16 in `ca107f2`. NR17 was verified in the next pass: given
  `<range> -- <paths>`, `code-review` ran `git diff <range> -- <paths>` and every finding cited a scoped path.

## Review pass — 2026-10-01 — incremental

**Candidate base:** `162401871c1a4a6a1ee2a81bced9653dad1d3bf6`
**Candidate head:** `ca107f25271175db546ac69d06f13fe3f3473357`
**Candidate branch:** `Fix/ReviewNativeCodeReview`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:c5fd3e79db8e6f9c7dec52668920ee7e3b90ff7a89ea6f970fbb62eb11b55c1b` `(19 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\review-pr74-inc2\review\e667eff61e891991e131d0216a0cb318279bfa8d526a24b18d3cf33c5a4b000f`
**Candidate bundle identity:** `sha256:493cc671d4c5e718d2ddd7c4d27444e7caaf2279e7aaa084afa83c88986899e9`
**Work-order path:** `reviews/Fix-ReviewNativeCodeReview.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

**Lens coverage:** the native layer was Claude Code's built-in `code-review`, given the range plus
` -- <authored paths>`. It returned 10 candidates. No security-sensitive path.

### Findings

- [x] **NR18 — MEDIUM — native** — `.agents/engineering/workflow/review/SKILL.md:176`
  Stage 6's `<trunk-merge-base>` was never frozen. Fix: the descriptor's `security.trunk_base`
  records it, and Stage 6 reviews `<trunk_base>..<frozen-head>`.
- [x] **NR19 — MEDIUM — native** — `.agents/engineering/workflow/review/SKILL.md:175`
  The trunk-range layer ran only for a `new` work order, so an appended pass on a branch with no
  security marker skipped it and was then blocked at merge. Fix: run it whenever `trunk_first_path` is
  set and the work order has no `Security-reviewed up to commit:` marker.
- [x] **NR20 — LOW — native** — `.agents/hooks/tier_gate.py:178`
  A matching project install with no `tier.json` discarded the user install, so the tier vanished.
  The outer/inner project choice was also decided by mtime. Fix: rank each install by scope
  specificity (user lowest) and let the best valid declaration win.
- [x] **NR21 — LOW — native** — `.agents/hooks/tier_gate.py:162`
  The cache key was unresolved for explicit `roots`. Fix: resolve the root once per cache.
- [x] **NR22 — LOW — native** — `.agents/workflows/workflow_ops.py:626`
  `load_descriptor` did not re-verify `routed_skills`/`route_violations`. Fix: compare them from one
  `route_findings` call.
- [x] **NR23 — LOW — native** — `.agents/hooks/tests/test_workflow_ops.py:236`
  The deny-hit test asserted only truthiness. Fix: assert the exact `[path, reason]` evidence.
  The security helper closure was also simplified.

  **Resolved** NR18–NR23 in the remediation commit after `ca107f2`.

Dismissed: paths with leading or trailing whitespace or embedded newlines lose exactness through the
router's stdin contract. That is pathological in practice and predates this change, since the reconcile
path uses the same contract. A legacy repo router returning the list form can't report deny hits; the
packaged router always ships and returns the dict form.

## Review pass — 2026-10-01 — incremental

**Candidate base:** `ca107f25271175db546ac69d06f13fe3f3473357`
**Candidate head:** `1d8eff77e5849aba12201975ffe4d58321b743ac`
**Candidate branch:** `Fix/ReviewNativeCodeReview`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:c5fd3e79db8e6f9c7dec52668920ee7e3b90ff7a89ea6f970fbb62eb11b55c1b` `(19 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\review-pr74-inc3\review\2e197fde1736995bbd2c8862e935a932ee680c52a81436c89b3a3084813d54ae`
**Candidate bundle identity:** `sha256:dd6b6b3f78fe1fcc30b018b97b9e13c159156480ddf8e12fd885d2c5ee435a42`
**Work-order path:** `reviews/Fix-ReviewNativeCodeReview.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

**Lens coverage:** the native layer was Claude Code's built-in `code-review` at `medium`, given the range
plus ` -- <authored paths>`. It returned 2 findings and confirmed the tier ranking, routing re-check and
pattern fallback. No security-sensitive path.

### Findings

- [x] **NR24 — MEDIUM — native** — `.agents/engineering/workflow/review/SKILL.md:175`
  The trunk-range layer skipped a branch whose security marker exists but is stale, and the gate blocks
  on exactly that (`security_no_longer_covered`). Fix: run it when the marker is missing or a
  security-sensitive path changed between it and the frozen head.
- [x] **NR25 — LOW — native** — `.agents/engineering/workflow/review/SKILL.md:176`
  With no resolvable trunk, `trunk_base` is null and the range is `None..<head>`. Fix: fall back to
  `<frozen-base>..<frozen-head>`.

  **Resolved** NR24–NR25 in the remediation commit after `1d8eff7`.

## Review pass — 2026-10-01 — incremental

**Candidate base:** `1d8eff77e5849aba12201975ffe4d58321b743ac`
**Candidate head:** `6d1ef4081dd3be2ed7af13e3d77afff7fd68dbb2`
**Candidate branch:** `Fix/ReviewNativeCodeReview`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:0c7a70aaf22bbdc30c3facc1a33b6e519b8836533721ae2235124b80814d84cf` `(8 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\review-pr74-inc4\review\2f72ef68089a1f595044999769eb61e8b5d4bc6d6656f263c5d7d090cf6e45d0`
**Candidate bundle identity:** `sha256:e935814f198adc19b4ad1d2fac41d4eee2fdbe8ad7164a10d693b5890caaf83c`
**Work-order path:** `reviews/Fix-ReviewNativeCodeReview.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

**Lens coverage:** the native layer was Claude Code's built-in `code-review` at `medium`, given the range
plus ` -- .agents/engineering/workflow/review/SKILL.md`. It returned 1 finding. No security-sensitive path.

### Findings

- [x] **NR26 — LOW — native** — `.agents/engineering/workflow/review/SKILL.md:176`
  An unresolvable marker (rebased away) is treated as stale by the gate, but the trigger did not cover
  it. Fix: run the layer when the marker is missing, unresolvable, or followed by a sensitive change.

  **Resolved** NR26 in the remediation commit after `6d1ef40`.

## Review pass — 2026-10-01 — incremental

**Candidate base:** `6d1ef4081dd3be2ed7af13e3d77afff7fd68dbb2`
**Candidate head:** `93631227833d1fa8fecd85e9d401a2c5b509e513`
**Candidate branch:** `Fix/ReviewNativeCodeReview`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:0c7a70aaf22bbdc30c3facc1a33b6e519b8836533721ae2235124b80814d84cf` `(8 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\review-pr74-inc5\review\3bea53fa62b96d90c67506b1162ea7f02bc2765a8b939725ded674191eccddfd`
**Candidate bundle identity:** `sha256:044008db9c246da1f7d2106144cfcb79c27f95a5276c9fbaa86e0c9394e2d9c7`
**Work-order path:** `reviews/Fix-ReviewNativeCodeReview.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

**Lens coverage:** the native layer was Claude Code's built-in `code-review` at `low`, given the range
plus ` -- .agents/engineering/workflow/review/SKILL.md`. It found nothing. No security-sensitive path.

### Findings

None.
