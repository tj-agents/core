# Code review — Fix/LaneOneReservedForCriticalDesign

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `9959be4d224fd68e0afbd09546f56b76a070e9bf`  `(2026-09-27)`
**Judgment:** `changes-requested`

## Review pass — 2026-09-27 — all

**Candidate base:** `a7925eadfd7007e6923d1dbf4e13414ebfb9d648`
**Candidate head:** `9959be4d224fd68e0afbd09546f56b76a070e9bf`
**Candidate branch:** `Fix/LaneOneReservedForCriticalDesign`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:fc15ac418492632b9506653b676913300e6610d39f696731dca44a3b7805112e` `(37 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\lane-l1-review-1\review\90f2c7d2a22f9fd48d386b5236101942d15d35c0af14c9bc74cd6a6cbd6642d6`
**Candidate bundle identity:** `sha256:6fd1bb8c90f9e94655732f6837c66c9520e11680a2339de4c1c7e44c22d701e3`
**Work-order path:** `reviews/Fix-LaneOneReservedForCriticalDesign.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

### Findings

- [x] **REV-001 — MEDIUM — correctness** — `.agents/machine/handoff-claude/scripts/launch-claude.ps1:60`
  The L1 authorization check lives only inside `Resolve-AgentLaneModel`, and both launchers skip that call
  when the caller already supplied the selection: Claude on `-Lane L1 -Model <id>`, Codex on
  `-Lane L1 -Model <id> -ReasoningEffort <e>` (`launch-codex.ps1:157`). Such a call launches with no
  `-UserAuthorizedLane`, contradicting both handoff skills' "the launcher throws without it". Resolve the
  lane whenever `-Lane` is present and use its values only for the halves the caller left out, and add a
  test that `-Lane L1` beside an explicit `-Model` (and `-ReasoningEffort` for Codex) still throws.

Lenses: native-general, api-contract, workflow. Security layer not required: no path matches the generic
or repository `security_paths` inventory.
