# Code review — Feature/LaneLadderExpansion

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `f2132095cdb3f76046ea81bcc9047d257b8b3d22`  `(2026-09-24)`
**Judgment:** `approved`

## Review pass — 2026-09-24 — full

**Candidate base:** `f6932c7ceed87b20d68dca4574b015d50fe96725`
**Candidate head:** `82781781d1437e4223d5a5cc3f9c0525710b5136`
**Candidate branch:** `Feature/LaneLadderExpansion`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:dcd1fcf700600023d907886dc9b500ddd7e8243b63514bd7f3f71f58a7c15cff` `(115 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\base-agents\.git\agent-workflow\runs\lane-ladder-review\review\72e0fd76f5dba1056c21329d6376450a8545c9d23c8bf7037918e24e193c3597`
**Candidate bundle identity:** `sha256:d8957133a9fbaec0418507f2ff4371fa200b52e05b40ab1ff0f10785df286c6e`
**Work-order path:** `reviews/Feature-LaneLadderExpansion.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

**Rules routed:** none — `review-prepare` reports an empty routed-rule set for the 115 frozen paths.

**Lens coverage:** helper-selected `native-general`, `security`, `api-contract`, `workflow`; dispatched in
one wave as four read-only `review-lens` contexts over the frozen bundle. The security layer ran as part
of that wave and returned no finding.

### Findings

- [x] **LL1 — LOW — native-general + api-contract + workflow** — `.agents/lanes/claude.json:15`
  Claude L1's `why` read "frontier family at the coding default setting" — `xhigh` is not the table's
  "default setting" (that phrase is reserved for `high`, see L3), the term "coding default" exists nowhere
  else in the repo, and the paired Codex L1 uses the correct convention. Three lenses flagged it
  independently. Fixed: reworded to "frontier family at the setting above `high`." matching the Codex
  entry and the table's own vocabulary; mirrors regenerated.

- [x] **LL2 — LOW — workflow** — `.agents/engineering/contract/lanes/SKILL.md:100`
  "Not level" point 2 claimed L6 "stays on each harness's small current-generation family" — false for
  Claude, whose L6 prices the workhorse (`sonnet`), not the small family (`haiku`); only the Codex half
  was true. Fixed: reworded to say L6 stops the drop one family early — Claude's workhorse at its lowest
  setting, Codex's small current-generation family.

- [x] **LL3 — LOW — workflow** — `.agents/engineering/contract/lanes/SKILL.md:46-58`
  The four questions never mention input size, yet input size is the only stated differentiator between
  L6 and L7, so two identical answers could land on either rung. Fixed: one sentence appended to the
  paragraph below the questions naming the floor-only extra axis — clerical work is L7 only while its
  input fits the cheapest rung.

### Verified and dismissed during synthesis

- `.codex/agent-delivery.json` `project_managed_agent_sha256` carrying no `lane-l6/l7` entries and stale
  `lane-l1..l5` digests is not a defect: `install-workflow-agents.ps1:250-263` always computes live
  digests from the current source files and treats the JSON map as an additive historical fallback for
  pre-existing on-disk copies, which brand-new files cannot have. Confirmed by the parent against the
  installer source and independently by two lenses.
- Frontier spend guard holds as a pair on both hosts: L1 prices `claude-fable-5`/`gpt-6-astra` @ `xhigh`,
  frontier the same models @ `max`, and `test_the_frontier_tier_sits_above_the_ladder_and_no_rung_can_reach_it`
  asserts any rung sharing the frontier model sits strictly below its effort. No generated agent or
  adapter prices the frontier pair.
- Every renumbered consumer keeps its price: all 27 authored `lane:` declarations (54 with plugin mirrors)
  resolve to the same model+effort as before the shift; the six repriced `.codex` adapters (`commit`,
  `commit-all`, `push`, `pull`, `sync-checkout`, `open-worktree` → `gpt-5.5`) match the new L7; the
  untouched workflow host stage pins still match the remapped `STAGE_LANES`.
- `materialize_tree`'s unlink-before-write introduces no TOCTOU or symlink hazard: the path is a repo-private
  digest-derived bundle location, the tar path-escape guard and `filter="data"` extraction are unchanged,
  and a historical review (`reviews/Chore-WorkboardSkillTests.md:96`) independently documents the EINVAL
  truncation bug it fixes.
- Launchers add no injection surface: lane/model/effort values flow from the repo's own tables into
  argument arrays and array-splat invocation, never through a shell; `ValidateSet` widening only narrows
  the enum before that.
- No stale old-ladder vocabulary anywhere in the frozen tree (`L1..L5` ranges, "no family below luna",
  L5-as-cheapest, L3-as-ordinary); required literal lane-table location strings survive; the lanes skill
  description is byte-identical across canonical and both host adapters; both handoff rung tables match
  the canonical summaries verbatim in all mirrors.
- `resolve.py` docstring examples truthful against the new tables; `--lanes` iterates only `lanes`, so the
  Claude frontier's new `effort` key changes no consumer (`launch-claude.ps1` reads only `.Model`).
- Catalog digests updated consistently in both locations for the two changed packages; shipped tables and
  launcher scripts byte-identical across all authored and packaged copies at the frozen head.
- No secrets, tokens, or machine-identifying content in the changed or generated files.

### Out of scope, unchanged disposition

- `test_merge_review_gate.CanonicalEnvelopeShellTests` fails the same two bash-discovery tests only under
  a PATH lacking git's `bin/bash.exe` (reproduced: passes under PowerShell on this machine); predates this
  branch, which touches no file it covers. The entry recorded in `reviews/Fix-PluginCacheReconcile.md`
  keeps its resolution condition.

## Review pass — 2026-09-24 — incremental

**Candidate base:** `82781781d1437e4223d5a5cc3f9c0525710b5136`
**Candidate head:** `f2132095cdb3f76046ea81bcc9047d257b8b3d22` *(remediation of LL1–LL3)*
**Candidate branch:** `Feature/LaneLadderExpansion`
**Candidate scope:** `all`
**Work-order path:** `reviews/Feature-LaneLadderExpansion.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Delta: the Claude L1 `why` reworded to the tables' effort vocabulary, the not-level point 2 corrected for
Claude's L6 family, the floor-only input-size sentence added below the four questions, regenerated catalog
digests and the three table/contract mirrors, and the retirement of the merged PR #33's spent work order.
No new finding.

Checked in this pass:

- The reworded L1 `why` is byte-identical in phrasing convention to Codex L1 and consistent with L2/L3;
  "coding default" no longer appears anywhere in the tree.
- The corrected not-level point 2 is true against both tables (Claude L6 `sonnet-5@low`, Codex L6
  `luna@low`, floors `haiku-4-5` / `gpt-5.5@low`), and the new four-questions sentence agrees with the L6
  and L7 summaries without contradicting the re-route guidance.
- `test_lane_tables.py` green at this head (22 passed, 725 subtests); `sync-generated.ps1 -Check` 0 changed.

The out-of-scope disposition recorded in the full pass is unchanged; this delta touches no file it covers.
