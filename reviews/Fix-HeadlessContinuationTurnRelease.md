# Code review — Fix/HeadlessContinuationTurnRelease

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `in-progress`
**Reviewed up to commit:** `6b6e291f3c602f7b0b5740c23a8cd7632b0d161a`  `(2026-10-12)`
**Judgment:** `pending`

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/hooks/continuation_stop.py",
  "candidate_head": "6b6e291f3c602f7b0b5740c23a8cd7632b0d161a",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Stop releases a foreground turn whose lease is released while an identity-verified scheduled headless writer owns the goal; unproven or unverified writers still block",
      "source": ".agents/hooks/continuation_stop.py",
      "mapping": ".agents/plugins/manifests/claude/engineering-hooks.json Stop via hook_dispatch.py and .agents/plugins/sources.json",
      "verification": {"level": "source", "result": "passed", "evidence": "CI run 38317477446 verify-linux passed test_continuation_stop.py at 6b6e291f3c602f7b0b5740c23a8cd7632b0d161a and a local Windows run of its 7 headless tests passed, including the claude harness subtests over both Stop payload spellings"}
    },
    {
      "host": "codex",
      "behavior": "Stop releases a foreground turn whose lease is released while an identity-verified scheduled headless writer owns the goal; unproven or unverified writers still block",
      "source": ".agents/hooks/continuation_stop.py",
      "mapping": ".agents/plugins/manifests/codex/engineering-hooks.json Stop via hook_dispatch.py and .agents/plugins/sources.json",
      "verification": {"level": "source", "result": "passed", "evidence": "CI run 38317477446 verify-linux passed test_continuation_stop.py at 6b6e291f3c602f7b0b5740c23a8cd7632b0d161a and a local Windows run of its 7 headless tests passed, including the codex harness subtests over both Stop payload spellings"}
    }
  ]
}
```

## Review pass — 2026-10-12 — full

**Candidate base:** `c91b60c955ad4a3f0f7a9383fc20f1c4a6b58510`
**Candidate head:** `a6b12c630f23e93ab06a37e0ac6eefad4ddc429f`
**Candidate branch:** `Fix/HeadlessContinuationTurnRelease`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:d1e55fd1553a7699d5aad4bff6a380a67fd1b014267db9671977ffdb68856b59` `(4 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\848qAs5MSFjhIHEx1u4kJ5\gWrlWWvZ-ou6tHPnFUoGx5`
**Candidate bundle identity:** `sha256:839121adf352f133fd79c125dcf34351360f8121d1154dcbaed8e67db35e1261`
**Work-order path:** `reviews/Fix-HeadlessContinuationTurnRelease.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Descriptor: `.git/agent-workflow/runs/review-229/review/816ae5596bd9fa8bbab473e7154a06c79d57119bca0a60dda4c2ebaa62357140/descriptor.json`
(patch `sha256:3433c04a8d93f20ae154a7ec6b987829bdd895f07cf87202238f5f4d029cab7f`). Synchronization: none;
`origin/main` equals the candidate base.

Native layer: Claude Code built-in `code-review` (medium) over the frozen range. It returned one low
finding, retained as STOP1. Lens dispatched: `workflow`, which returned three low-confidence candidates in
`GOAL.md`, all dropped at synthesis. "Old line 239" cites the start of the blocking branch, which is
accurate. The asymmetric Claude mapping text is superseded by this review-stage coverage record, which
names both dispatch paths. `pending` in the plan-stage coverage record is that stage's required value.
Security layer not required (`first_path` and `trunk_first_path` null). Routed skills: none. Tier gate: no
stack tier conventions apply. The `CODE_CONVENTIONS.md` check found stdlib Python, no comments, and
cross-platform tests that passed on both CI platforms at the frozen head.

### Findings

- [x] **STOP1 — LOW — native-general** — `.agents/hooks/continuation_stop.py:250`
  A well-formed `child` record whose process has exited or been replaced gets "unverified headless writer;
  reconcile it". `continuation_runtime.launch` leaves `state=working` plus that record from the moment the
  supervisor exits until its checkpoint or failure save. A crashed wake leaves the same state, and the next
  scheduled wake recovers it. In both cases the correct direction is to wait for the receipt; the
  foreground cannot reconcile the owner. Fix: reserve the reconcile message for a malformed or
  unverifiable record or a non-`working` state, and give an exited or reused writer the wait message.
  Cover both in the tests.
  Fixed in `568db87`. `headless_writer_record` checks validity separately from liveness.
  `test_ended_headless_writer_waits_for_its_receipt` fails 2 subtests on a6b12c6 and passes after the fix.
  The focused `-k headless` run passed 6 tests on Windows.

## Review pass — 2026-10-12 — incremental

**Candidate base:** `a6b12c630f23e93ab06a37e0ac6eefad4ddc429f`
**Candidate head:** `568db8788deb7a08679477a836f601ebcb60b7eb`
**Candidate branch:** `Fix/HeadlessContinuationTurnRelease`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:b808cfe280f8dd62e2403073753d83ae60e6ecfb253899b1b160364f8291a5ea` `(3 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\a6Wuu6-82Ifb352bCHTnPL\WJfWRyCUPjL5WYexy2HEFo`
**Candidate bundle identity:** `sha256:892c1db881105cd6eb972b30224e07d7cf742ace319f7631bf24ed75488d8044`
**Work-order path:** `reviews/Fix-HeadlessContinuationTurnRelease.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Descriptor: `.git/agent-workflow/runs/review-229-inc1/review/5897d64720943e32f95987b1cb61c416859faea807222438404e08a17291ae58/descriptor.json`
(patch `sha256:5627bfbd526763281fa0de2d63fd9dc2ecc8e1c63028146e88a03a4e38b2c4de`). Remediation delta for STOP1.

Native layer: Claude Code built-in `code-review` (medium) over the frozen range. It returned one low
finding, retained as STOP2. Lens dispatched: `workflow`, with no findings. It verified that a wake meeting
a live foreground lease still records a `wake` event, and that both ended-writer subtests fail on
a6b12c6. Security layer not required. STOP1's original text, severity and pass judgment are unchanged
apart from its permitted status and disposition update.

### Findings

- [x] **STOP2 — LOW — native-general** — `.agents/hooks/continuation_stop.py:253`
  A well-formed writer that has ended, with no ready scheduler or observed wake, now gets "wait for its
  receipt". No supervisor or scheduled wake will produce that receipt: a manual wake, or a wake killed by
  a machine crash, leaves `working` plus a dead child. Fix: wait only when the writer is live or scheduled
  recovery is proven. Reconcile an ended writer that has neither, and test that combination.
  Fixed in `6b6e291`. Stop waits only for a live writer or one with scheduler and wake proof, and reconciles
  otherwise. `test_ended_headless_writer_without_scheduled_recovery_blocks_for_reconciliation` covers
  all three missing-proof combinations, and the focused `-k headless` run passed 7 tests on Windows.

## Review pass — 2026-10-12 — incremental

**Candidate base:** `568db8788deb7a08679477a836f601ebcb60b7eb`
**Candidate head:** `6b6e291f3c602f7b0b5740c23a8cd7632b0d161a`
**Candidate branch:** `Fix/HeadlessContinuationTurnRelease`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:b808cfe280f8dd62e2403073753d83ae60e6ecfb253899b1b160364f8291a5ea` `(3 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\7JpE8IDXmvwmvXSzEHk6PO\zY9r2NQXRQhKiJisONbmQ_`
**Candidate bundle identity:** `sha256:38dd3a8aff942f15a1c33af5be2fa2b2ddbd09e6bda8aa956df3b0ade8d94b98`
**Work-order path:** `reviews/Fix-HeadlessContinuationTurnRelease.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Descriptor: `.git/agent-workflow/runs/review-229-inc2/review/cd8f6bd8d41745084a8898ac38d6e643f92fff81826fbe0abd2720d9a4881354/descriptor.json`
(patch `sha256:46e1828172b7f816259cb1269e34e2ef476cb9987272c24c6c4a0a2427c89e52`). Remediation delta for STOP2.
Base movement c91b60c..7ac3aee (PR227 lanes debt docs and its regeneration) touches no candidate or routed path.

Native layer: Claude Code built-in `code-review` (medium) over the frozen range, with no findings. Lens
dispatched: `workflow`. It confirmed all four live/durable outcomes and the regression value of the new
test, and returned two B011 accuracy candidates, merged into DOC1. Security layer not required. STOP2's
original text, severity and pass judgment are unchanged apart from its permitted status and disposition
update.

### Findings

- [x] **DOC1 — LOW — workflow** — `BUGS.md:114`
  B011 is stale against the reviewed behavior. Its resolution condition says a missing scheduler or wake
  "still waits", but an ended writer missing that proof now gets a reconcile block. Its verification
  evidence cites 32 tests, but the file now has 34. Fix: state the live/ended split in the resolution
  condition and update the evidence to the current test count and review passes.
  Fixed in `0ebb95e`. The B011 resolution condition states the live and ended outcomes, and the evidence cites
  34 tests, the STOP1 and STOP2 regressions and CI run 38317477446.

## Review pass — 2026-10-12 — incremental

**Candidate base:** `6b6e291f3c602f7b0b5740c23a8cd7632b0d161a`
**Candidate head:** `0ebb95e072f183493fc286434da67dc4452e1c6e`
**Candidate branch:** `Fix/HeadlessContinuationTurnRelease`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:a1878267f0cd899b307c55d14ead838b0e865db19c049fefed469e0270b583e9` `(1 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\kEeGP4KlOwRf-_45sAM8H6\SqbgoMQ6Cjpn_OPQwTOKql`
**Candidate bundle identity:** `sha256:bc2ac005c70b3b5c9950932e7147785e14d0a145bd1525dfd43a74a0fd283e69`
**Work-order path:** `reviews/Fix-HeadlessContinuationTurnRelease.md`
**Work-order mode:** `append`
**Pass judgment:** `pending`

Descriptor: `.git/agent-workflow/runs/review-229-inc3/review/4aa6e0a0c43a0a3a67fce3d0c1338aaa52e79ea41a948433a5eb3cb982777a0e/descriptor.json`
(patch `sha256:8e05505a17f57fed2b91f71b6f08eb5bd780c34eb3b01f70c0f41a2efd1a92d3`). Remediation delta for DOC1.

### Findings

Pending parent synthesis.
