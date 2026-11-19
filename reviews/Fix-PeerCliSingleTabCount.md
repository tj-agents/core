# Code review — Fix/PeerCliSingleTabCount

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `cce4503d4f6f670c2e5c410cb5c0e42156345211`  `(2026-10-07)`
**Judgment:** `approved`

## Review pass — 2026-10-07 — full

**Candidate base:** `f5317135b3c5c7dc6e55ac8c248978a91b4f1603`
**Candidate head:** `bb2ca32ad2c4c2f6362297a13a0844adfd6bc81e`
**Candidate branch:** `Fix/PeerCliSingleTabCount`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:d3eb6ed7d344b7949afc08d734a7993e983609306a82e7459f63aaec55956a6d` `(3 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\kD88M0ox5ha9p3zLNY05fX\Ob2hlHnd7vpJ6zz5GwIdBA`
**Candidate bundle identity:** `sha256:7675e3676fed6fcb957ce543aac3da67324d4e3d6bd201c9734bace14b488880`
**Work-order path:** `reviews/Fix-PeerCliSingleTabCount.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

### Findings

- [x] **F1 — LOW — native-general** — `tests/close-tab.tests.ps1:21`
  Design-narration comment explaining the rationale for dot-sourcing with `-List` violated the global
  zero-comment rule. Removed; the existing `peer-cli.tests.ps1` precedent for the same dot-source
  pattern carries no comment either.
- [x] **F2 — LOW — native-general** — `tests/test_close_tab.py:25`
  Design-narration comment contrasting PS5.1 vs PS7 Count/Length behavior violated the same rule.
  Removed.
- [wontfix] **F3 — LOW — native-general** — `tests/close-tab.tests.ps1:21`
  Dot-sourcing the full `close-tab.ps1` via `-List` runs real UI Automation enumeration
  (`Get-TerminalTabs`) as a side effect of loading test functions. Pre-existing pattern already used
  by `tests/peer-cli.tests.ps1` for the same script; not introduced or worsened by this branch, and
  `-List` short-circuits before any tab is touched. Out of scope for this bounded fix.

## Review pass — 2026-10-07 — incremental

**Candidate base:** `bb2ca32ad2c4c2f6362297a13a0844adfd6bc81e`
**Candidate head:** `cce4503d4f6f670c2e5c410cb5c0e42156345211`
**Candidate branch:** `Fix/PeerCliSingleTabCount`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:d3eb6ed7d344b7949afc08d734a7993e983609306a82e7459f63aaec55956a6d` `(3 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\kD88M0ox5ha9p3zLNY05fX\wFFE-en9XYME6zdjyUajXW`
**Candidate bundle identity:** `sha256:b2da5a13406027eaaf94d0d0ae9af6674d9b760176238b6a0f39352f19db1c1e`
**Work-order path:** `reviews/Fix-PeerCliSingleTabCount.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

### Findings

No new findings. F1 and F2 are fixed by this commit; F3 remains `wontfix` as recorded above. The
collection-shape fix in `close-tab.ps1` (the `@()`-wrapped conditional extracted into
`Resolve-TabMatches`) and the zero/single/multiple/wildcard regression coverage are unchanged and
correct under both PowerShell hosts.
