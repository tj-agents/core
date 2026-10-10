# Code review — Fix/HarnessPermissionsVersionFlake

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `be1d55a5c6e0fd06c8e4385c72e2441048c215e7`  `(2026-10-10)`
**Judgment:** `changes-requested`

## Review pass — 2026-10-10 — full

**Candidate base:** `29827dfcfd81e7d59c75d9bf179c90e4d15dbdc8`
**Candidate head:** `ca25bc1c0bb0eecbce04dae9956a326839bacce0`
**Candidate branch:** `Fix/HarnessPermissionsVersionFlake`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:8f1ee152fb0e02fce1f03689d18ab54cc407a16535875cb04f53335885f96751` `(1 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/GJ8cf971mCQlsteEq2s0Dp/6rRfIMHs5wE13LaGbmQdFm`
**Candidate bundle identity:** `sha256:7e6a81395582e2ba277d1d1d29343be23516a49eec90f34039f7c8e4bdf3c6f0`
**Work-order path:** `reviews/Fix-HarnessPermissionsVersionFlake.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Synchronization: one pre-review synchronization against `origin/main` (behind 0). Routed rules: none.
Security layer: not required.

### Findings

- [x] **F1 — MEDIUM — native-general** — `tests/test_harness_permissions_sync.py:202`
  The rewritten checks match only the forward-slash spelling, but the sync writes forward-slash and
  backslash entries, so a stale backslash `v1` entry or a missing backslash `v2` entry would pass. Fix:
  compare against `harness_permissions.render_claude_allow`'s exact entries for each version. Fixed.
- [x] **F2 — LOW — native-general** — `tests/test_harness_permissions_sync.py:131`
  The precondition in `test_stale_owned_entries_are_removed` used a prefix match that `.../v10` would also
  satisfy, and differed from the other test. Fix: the same exact rendered-entry comparison. Fixed.

## Review pass — 2026-10-10 — incremental

**Candidate base:** `ca25bc1c0bb0eecbce04dae9956a326839bacce0`
**Candidate head:** `9512032b9f42397a800339a81999485590269a1e`
**Candidate branch:** `Fix/HarnessPermissionsVersionFlake`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:de8f60fd0969faf2f102169d8fe562e495f28e5ce1a9c6ffd986e92d3fa7e998` `(2 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/EiPrpERJg2GaqK3Lxd9eFj/x9GJ1rpnmkrYK-UdxA3VSe`
**Candidate bundle identity:** `sha256:37ba3e50b4b197afa3f23e8d30ea2d350d7642b30c0ffd09e081372c1a27942c`
**Work-order path:** `reviews/Fix-HarnessPermissionsVersionFlake.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Remediation of F1–F2. Security layer not required.

### Findings

- [x] **F3 — MEDIUM — native-general** — `tests/test_harness_permissions_sync.py:203`
  The F1 fix took its expected entries from `render_claude_allow`, the renderer under test, so a renderer
  regression could not fail it; the subset and intersection checks also missed leftover or extra entries,
  and the installs still hard-coded the template the constant duplicated. Fix: build both spellings
  independently in `cleanup_entries`, assert exact equality, and install `[CLEANUP]`. Fixed.

Dropped: the in-progress work-order state and its `/tmp` bundle path (both prescribed by the review
contract), and the Codex rules substring check (unchanged pre-existing lines outside this change).

## Review pass — 2026-10-10 — incremental

**Candidate base:** `9512032b9f42397a800339a81999485590269a1e`
**Candidate head:** `be1d55a5c6e0fd06c8e4385c72e2441048c215e7`
**Candidate branch:** `Fix/HarnessPermissionsVersionFlake`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:de8f60fd0969faf2f102169d8fe562e495f28e5ce1a9c6ffd986e92d3fa7e998` `(2 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/kqJu_SZVg5nspaz77Qe2yx/wqa2DbIuXTXvj0Bdv0lPMJ`
**Candidate bundle identity:** `sha256:6bbd2a35a19583ba06d07d036968c70afcf0e0f47101ee8448d0d9e4bf838fe5`
**Work-order path:** `reviews/Fix-HarnessPermissionsVersionFlake.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Remediation of F3. Security layer not required.

### Findings

- [x] **F4 — LOW — native-general** — `tests/test_harness_permissions_sync.py:214`
  F3 adopted `CLEANUP` in two installs only; ten other calls still hard-coded the template, so F3's
  disposition overstated the fix. Fix: every install uses `[CLEANUP]`. Fixed.
- [x] **F5 — LOW — native-general** — `tests/test_harness_permissions_sync.py:208`
  The comment still described a substring check. Fix: say exact equality proves the v1 entries are gone.
  Fixed.

Dropped: the helper's separator logic mirroring `path_spellings` (the file's established oracle, as in
`test_both_separator_spellings_are_rendered`) and its single-template scope (named for `CLEANUP`).
