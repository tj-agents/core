# Code review — Fix/OwnerStateWindowsRace

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `638411d921aa98b6fe69346cd26c05879f97d0ac`  `(2026-10-10)`
**Judgment:** `changes-requested`

## Review pass — 2026-10-10 — full

**Candidate base:** `b4b576fa6a999fd43031e8c49aefaf32aa3a7d05`
**Candidate head:** `638411d921aa98b6fe69346cd26c05879f97d0ac`
**Candidate branch:** `Fix/OwnerStateWindowsRace`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:591f7fb061c9810cf8e48886a6136a00c388e9be86ae14c79035491a6dd61ac7` `(6 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/Y6W7lxSd4beZnQO7PtColE/kUZctkTqZJi_OWSl_DaWFH`
**Candidate bundle identity:** `sha256:35a23c0ca1a6b56136cfb9f6320b73ba1faffaa099389624b19c4dfdb7a8e5f5`
**Work-order path:** `reviews/Fix-OwnerStateWindowsRace.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

### Findings

- [x] **F1 — MEDIUM — workflow** — `.agents/machine/utility/hook-control/scripts/hook_control.py:378`
  `restore` removes the hook-control snapshot with `sidecar.unlink()` while `status` can read that same file outside `ExclusiveLock`; Windows can reject the deletion with a sharing violation. Retry the snapshot deletions with the same Windows sharing-violation policy and cover restoration under an open snapshot reader.
  Resolved by retrying both snapshot removals and the Windows-pinned open-reader restoration regression; `tests/test_hook_control.py` passed on Linux (Windows cases skipped by platform).
- [x] **F2 — MEDIUM — native-general** — `.agents/hooks/tests/test_continuation_runtime.py:250`
  The open-reader contention test proves replace retries, but its read runs before replacement can proceed and therefore does not exercise a sharing violation from the read itself. Inject one `PermissionError` with Windows sharing-violation code 32 before a successful read and assert the read retries; apply the equivalent proof to the hook-control snapshot reader.
  Resolved by injecting one Windows sharing violation into each read path before success; both focused suites passed on Linux, and the complete proof runs in the Windows-pinned cases.
