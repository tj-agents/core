# Code review — Fix/ContinuationProbeGate

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `6c5acc9bad2064703ad4741ba8cb446dc3606a4e`  `(2026-10-12)`
**Judgment:** `changes-requested`

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/workflows/continuation_runtime.py",
  "candidate_head": "6c5acc9bad2064703ad4741ba8cb446dc3606a4e",
  "hosts": [
    {
      "host": "claude",
      "behavior": "A Git failure or stale live foreground lease never produces an ungated blocked continuation owner, and failed runtime commands are not reported as owner state.",
      "source": ".agents/workflows/continuation_runtime.py",
      "mapping": "Shared continuation runtime and Stop hook shipped through engineering harness sources for both hosts.",
      "verification": {"level": "source", "result": "passed", "evidence": "test_fresh_and_stale_foreground, test_git_failure_keeps_foreground_owner_and_reports_command_failure and test_stale_live_foreground_wake_leaves_a_continuable_owner pass against the shared runtime and Stop hook."}
    },
    {
      "host": "codex",
      "behavior": "A Git failure or stale live foreground lease never produces an ungated blocked continuation owner, and failed runtime commands are not reported as owner state.",
      "source": ".agents/workflows/continuation_runtime.py",
      "mapping": "Shared continuation runtime and Stop hook shipped through engineering harness sources for both hosts.",
      "verification": {"level": "source", "result": "passed", "evidence": "The same shared-source regressions run against a Codex-harness owner fixture; the GIT_DIR exit-128 case reproduces the observed sandbox heartbeat failure and passes."}
    }
  ]
}
```

## Review pass — 2026-10-12 — full

**Candidate base:** `c91b60c955ad4a3f0f7a9383fc20f1c4a6b58510`
**Candidate head:** `6c5acc9bad2064703ad4741ba8cb446dc3606a4e`
**Candidate branch:** `Fix/ContinuationProbeGate`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:64b11b95653af2358a7befb323331e6ce39ad51f7573baab6a3db292051ca0ee` `(6 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\S-U-31QGSFbZeosUAaqi2q\4vOTG0q5MdJofmp6Gqmp9C`
**Candidate bundle identity:** `sha256:8be5ed70cd63a0eb7a9c9d66c7dd8e445d0b764e481aeabd116618c89d8f2559`
**Work-order path:** `reviews/Fix-ContinuationProbeGate.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Native layer: Claude Code built-in `code-review` skill (medium) over the frozen range. Lens dispatched:
`workflow` (`review-lens`). Security layer not required (`first_path` and `trunk_first_path` both null).
Routed skills: none returned by review-prepare.

Dropped at synthesis: "a stale live lease never escalates" — the deadline check precedes the lease branch,
so the owner still reaches the typed `continuation-budget-exhausted` gate; the owning session's Stop still
demands continue-or-yield; and the replaced `blocked` result was the false gate itself, which also made the
adapter unregister the scheduler. `alive()` treating an unreadable identity as live is unchanged behavior.
The adapter's own `{"state":"blocked"}` failure output is on unchanged lines; it was fixed in `c183651`
and is covered by the next pass.

### Findings

- [x] **CAT1 — HIGH — native** — `.agents/catalog/catalog.json:209`
  The committed `base-agents/engineering` digest is generated output; `check_generated_paths.py --base
  c91b60c` exits 1 on it, and the file was rewritten whole as CRLF because `update_catalog_digests.py`
  writes platform newlines. Fix: restore the catalog from the base and write it with LF. Resolved in
  `ab9cdda`; the guard now reports no generated paths.
- [x] **RUN1 — LOW — native, workflow** — `.agents/workflows/continuation_runtime.py:617`
  For `--owner` calls the heartbeat/yield check compares the owner's recorded checkout with the root read
  from that same record, so it verifies nothing. Fix: also require `.git` at the recorded root, without
  running Git. Resolved in `ab9cdda` with `test_heartbeat_requires_the_recorded_checkout_root`.
