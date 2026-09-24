# Code review — Feature/HandoffModelSelection

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `880b8e4`  `(2026-09-24)`
**Judgment:** `approved`

## Review pass — 2026-09-24 — full

**Candidate base:** `ff9dc07dad0fb7a19ae3411ea5e0cc49a5ae03af`
**Candidate head:** `2fe16d6ade90ccdef358265ff6ace635c5469f1d`
**Candidate branch:** `Feature/HandoffModelSelection`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:2dd13088005d490561c973a28b2c12a2eeaea76c82d858df5f95ec9627b0b242` `(31 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\base-agents\.git\agent-workflow\runs\review-pr-33\review\b99e9023d6eb83231fe8f265f73f964e21a45b6fce46fd5f8f8e9c2700eae3d5`
**Candidate bundle identity:** `sha256:3e188b6c1bd3a5f4f51927c893b49a68c853548a87231d3f73bac7628d0fbced`
**Work-order path:** `reviews/Feature-HandoffModelSelection.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

**Rules routed:** none — `review-prepare` reports an empty routed-rule set for the 31 frozen paths.

**Lens coverage:** helper-selected `native-general`, `api-contract`, `workflow`; dispatched in one wave as
three read-only `review-lens` contexts over the frozen bundle. Security layer not owed: no frozen path
matches the merge gate's generic security patterns and the repository declares no `.agents/merge-gate.json`
inventory.

### Findings

- [x] **HM1 — MEDIUM — workflow + native-general** — `.agents/machine/handoff-claude/SKILL.md:72`,
  `.agents/machine/handoff-codex/SKILL.md:58`
  The rewritten Model selection prose makes `-Lane`/`-Frontier` the caller-facing mechanism, but the
  section tail still said "Add `-Model '<model-id>'` only when a model was resolved as above" — a
  leftover from the pre-branch text where the caller resolved a raw id externally. A skim-reader landing
  on the imperative tail would invent a model id or skip lane selection, exactly what the section above
  forbids. The codex doc also omitted that `-ReasoningEffort` is the one flag `-Frontier` still accepts
  (winning over the tier's own effort), a nuance stated only in a script comment.
  Fixed: both tails now offer `-Lane`/`-Frontier` first and `-Model` for a user-named id, and the codex
  frontier paragraph states the `-ReasoningEffort` exception.

- [x] **HM2 — LOW — workflow** — `.agents/machine/handoff-claude/SKILL.md:53`,
  `.agents/machine/handoff-codex/SKILL.md:39`
  The L2 row dropped "at the top of the ladder" from the table summary it copies, while L1 kept it —
  reading the launcher table alone, L2 lost its capability signal and could be underweighted against L1.
  Fixed: clause restored verbatim in both files.

- [x] **HM3 — LOW — native-general** — `tests/handoff-launchers.tests.ps1`
  The codex `-Lane` + explicit `-Model` path (lane fills only the effort half) was exercised nowhere,
  though the Claude equivalent was. Fixed: a test now asserts the explicit model passes through, the lane
  model does not, and the lane's effort fills the missing half.

- [x] **HM4 — LOW — native-general** — `tests/handoff-launchers.tests.ps1`
  The unknown-lane rejection test only reached `[ValidateSet]`, never `Resolve-AgentLaneModel`'s own
  table-lookup guard, so a broken guard would pass unnoticed. Fixed: the comment now claims the parameter
  surface, and a direct call into the shipped `agent-cli.ps1` asserts the resolver rejects a lane its
  table does not price.

- [x] **HM5 — LOW — native-general** — `.agents/hooks/tests/test_lane_tables.py`
  The machine-plugin delivery test asserted parity for 2 of the 4 files the `resources/lanes` mapping
  ships. Fixed: extended to all four, matching its engineering-plugin sibling.

- [x] **HM6 — LOW — workflow** — `.agents/engineering/contract/lanes/SKILL.md:63`
  "Where a lane is applied" enumerated three surfaces while `engineering:handoff` now instructs a fourth
  (a lane passed to a handoff launcher at dispatch time). Fixed: a fourth bullet names the launcher
  surface and restates that the caller judges, the launcher prices.

### Verified and dismissed during synthesis

- The relative hop `..\..\lanes\<host>.json` in `Resolve-AgentLaneModel` resolves correctly from both
  locations the library is dot-sourced from: authored `.agents/machine/scripts` → `.agents/lanes`, and
  packaged `resources/machine/scripts` → `resources/lanes` (independently confirmed by two lenses and by
  the packaged-tree launcher tests actually resolving through it).
- No stale `L0`–`L3` vocabulary, `model-lanes.json` reference, or "dumb transport / no resolver ships"
  text anywhere in the frozen tree, including host adapters, CAPABILITIES.md, INDEX.md and catalog text.
- The new top-level `frontier` key is invisible to every `table["lanes"]` consumer: `resolve.py`, the
  generator, `lane_expectations.py`, workflow host stage pins and the generated lane agents.
- `FAMILY_ORDER` change (`claude-fable-5` for the stale `claude-fable-5-1`, `gpt-6-astra` added) stays
  coherent with every consumer; the frontier-above-the-ladder test holds on both hosts.
- Frontier guard wording is consistent at every mention (both handoff SKILL.mds, lanes contract, both
  tables' `why` fields, launcher comments); nothing permits inferring authorization from difficulty.
- Regex escaping in the launcher tests is correct where model ids carry literal dots.
- Generated `plugins/**` copies are byte-identical to authored sources at the frozen head.

### Out of scope, unchanged disposition

- `test_merge_review_gate.CanonicalEnvelopeShellTests` fails the same two bash-discovery tests on this
  machine and passes on CI; reproduced on the main checkout, predates this branch, which touches no file
  it covers. The entry recorded in `reviews/Fix-PluginCacheReconcile.md` keeps its resolution condition.

## Review pass — 2026-09-24 — incremental

**Candidate base:** `2fe16d6ade90ccdef358265ff6ace635c5469f1d`
**Candidate head:** `880b8e4` *(remediation of HM1–HM6 plus this work order)*
**Candidate branch:** `Feature/HandoffModelSelection`
**Candidate scope:** `all`
**Work-order path:** `reviews/Feature-HandoffModelSelection.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Delta: the two handoff SKILL.md tails and L2 rows, the codex frontier `-ReasoningEffort` sentence, the
lanes contract's fourth application bullet, the two launcher-test additions, the widened machine parity
tuple, regenerated catalog digests and generated mirrors, and this work order. No new finding.

Checked in this pass:

- Both tails now read coherently under the section that precedes them: `-Lane`/`-Frontier` first,
  `-Model` reserved for a user-named id, defaults unchanged. No model name entered either document.
- The new codex `-Lane`+`-Model` test asserts all three halves of the documented contract (explicit model
  through, lane model absent, lane effort filled); the resolver-guard test dot-sources the *packaged*
  `agent-cli.ps1` and hits the table-lookup throw that `[ValidateSet]` shielded before.
- `handoff-launchers.tests.ps1`, `test_lane_tables.py`, `skill-packaging.tests.ps1` green at this head;
  `sync-generated.ps1 -Check` 0 changed.

The out-of-scope disposition recorded in the full pass is unchanged; this delta touches no file it covers.
