# Code review — Fix/ReviewNativeCodeReview

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `49b980b`  `(2026-10-01)`
**Judgment:** `changes-requested`

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

- [ ] **NR1 — HIGH — native** — `.agents/engineering/workflow/review/SKILL.md:101`
  Stage 3 skips `code-review` whenever the live target's head differs from the frozen head. After
  `review-prepare --synchronize` merges the base locally, the frozen head exists only locally, so a PR
  target never matches. The fallback then fires in exactly the implementation-workflow reviews this
  change targets. Fix: give the native reviewer the frozen range `<base>..<head>` as its target, which
  works locally for both hosts, and drop the head-equality precondition.
- [ ] **NR2 — HIGH — native** — `.agents/engineering/workflow/review/SKILL.md:128`
  Stage 4 relies on the descriptor's `rules`, but `review_prepare` keeps only routed names that exist
  under `tree/.agents/skills/`. Plugin-owned routed skills (such as `dotnet:persistence`) and `DENY
  PATTERN HIT` evidence are silently lost in a repository with a route table. Fix: restore the explicit
  router step, run from `<engineering>/hooks/skill_router.py` against the frozen tree.
- [ ] **NR3 — MEDIUM — native + workflow** — `.agents/hooks/tier_gate.py:300`
  `installed_declarations` compares the resolved cache root with the unresolved registry `installPath`.
  A junction, symlink or short-name spelling therefore yields `[]` and every tier vanishes, both for
  the gate and for `--conventions`. Fix: resolve both sides in `_key`.
- [ ] **NR4 — MEDIUM — native** — `.agents/hooks/tier_gate.py:114`
  Stage 4 runs the gate from the agent shell, where no plugin-root variable is set, so `~/.claude` is
  read before `~/.codex` even in Codex. Fix: put the gate's own install cache (`__file__`'s fifth
  ancestor named `cache`) ahead of the home caches.
- [ ] **NR5 — MEDIUM — native** — `.agents/engineering/workflow/incremental-review/SKILL.md:43`
  Claude's `code-review` took only `<PR|branch>`, so an incremental pass or a big-review stage reviewed
  the whole PR under a 10-finding cap, and the delta got little native coverage. Fix: the same frozen
  range target, plus ` -- <scoped paths>` for a bounded stage.
- [ ] **NR6 — MEDIUM — native** — `.agents/workflows/workflow_ops.py:483`
  The security classification covers only the review range. The merge gate classifies the head's
  whole range against `origin/main`, so a stack child whose parent layer touched auth paths gets no
  security layer and is then blocked at merge. Fix: union the trunk range and exclude the branch's
  own work order, as the gate does.
- [ ] **NR7 — LOW — native** — `.agents/hooks/tier_gate.py:293`
  Project-scoped registry entries count for every project. Fix: count a `projectPath` entry only
  inside its project, and pass the assessed project root to `declarations()`.
- [ ] **NR8 — LOW — native** — `tests/test_review_native_layer.py:732`
  The Stage 4 acceptance test reads the developer's real caches and passes on the no-tier message.
  Fix: give it an isolated home and config with a registry-installed and a stale tier, and assert the
  installed convention path.
- [ ] **NR9 — LOW — workflow** — `.agents/engineering/workflow/review/SKILL.md:3`
  The `review` description and the `docs-review` intro still say "native/general", which contradicts
  the renamed Stage 3. The guard test misses both. Fix: reword them in canonical and both host
  descriptions, and assert no `native/general` remains.
- [ ] **NR10 — LOW — workflow** — `.agents/machine/scripts/prune_plugin_cache.py:592`
  `--notice` help still says only "Throttled", although it now also prints an unthrottled
  superseded-session line. Fix: reword the help.

Verified and dismissed during synthesis. A stale-session notice wired only in machine can't see an
engineering-only update: all three packages update together from one marketplace commit, and a process
predating this release can't run new code, which no notice can change. The `merge_review_gate` import
reconfigures stdout to UTF-8, which is what `workflow_ops` emits anyway. Big-review's per-area
`security: yes/no` manifest line is derived per area by the parent, not from the candidate-level field.
