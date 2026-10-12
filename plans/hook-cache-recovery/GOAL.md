# Installed Stop-hook recovery

## Objective

Determine and implement the supported Core delivery/recovery path for a stale installed engineering Stop hook that falsely blocks a valid continuation binding with `binding-head-changed`. Deliver the repair as an isolated Core change; do not modify the controller-association PR #209, its continuation owner, or installed plugin-cache files by hand.

## Evidence

On 2026-10-12, the controller-association checkout at `Fix/ControllerGoalAssociation` was at `e7df895d41a2faaab73743f98978b08212a99bc0`, matching both its continuation owner and `.agents/persistent-workflow-binding.json`. The source hook now reads `remote_head_sha`, but the installed cache `base-agents/engineering/2.1.16/hooks/continuation_stop.py` still reads `binding.get("head")` after normalization, which guarantees the false failure.

The source correction alone does not update a running or stale installed plugin package. The supported recovery must preserve hook trust and package integrity, work on Windows and Linux, and prevent future sessions from being trapped by the obsolete cache.

## Scope

- Diagnose the supported installation, refresh, versioning and host-reload path.
- Make the minimal canonical-source change(s), tests and release/delivery wiring needed to recover safely.
- Record the precise user action, if any, required to update an already-running host.
- Do not patch `C:\Users\TommySeery\.codex\plugins\cache` directly, disable hooks, rewrite PR #209 runtime state, or delete locks/receipts as a workaround.

## Authorization

This is the bounded standards-defect side workstream required by `engineering:session-guidance`. Normal Core implementation, tests, PR and merge are authorized; profile installation, destructive cleanup and bypassing host trust remain gated.

## Handoff lane

Lane: L3. The fault is clear, but the supported deployment/recovery behavior and host cache/trust boundaries require an open investigation.

## Completion

- A supported remedy is implemented and validated on Windows and Linux where Core owns the behavior.
- The canonical source has regression coverage for the faulty normalization path and recovery path.
- Documentation distinguishes source repair from installed-cache recovery and gives a safe, exact operator action.
- No workaround mutates an installed cache or continuation state by hand.

## Diagnosis (2026-10-12, Claude, lane L3)

The installed cache is not stale. `~/.codex/plugins/cache/base-agents/engineering/2.1.16/hooks/continuation_stop.py`
is byte-identical (after CRLF normalization) to `plugins/engineering/hooks/continuation_stop.py` on `origin/main`
(`73824c0`), blob `fa71510`. The `remote_head_sha` correction exists only in PR #209's unmerged commit `70643fa`;
the defect was never released. The main-line test mocked `binding_from_artifact` with a `head` key, so the real
normalization (`delivery_runtime.ARTIFACT_ALIASES` maps `head` to `remote_head_sha`) was never exercised.

Delivery path, observed:

- Post-merge `regenerate` commits `plugins/engineering` to main. The Codex version stays `2.1.16`, but the
  supported refresh (`codex` terminal wrapper or `handoff-codex` → `codex_marketplace_sync.sync_codex_standards`:
  `plugin marketplace upgrade`, `plugin add <id>` per enabled plugin, then tj-agents hook trust) re-caches same-version
  content. Evidence: cached `hooks/delivery_binding_gate.py`, `hooks/hook_runtime.py`, `workflows/repository_configuration.py`,
  `session-context.py`, `hooks/codex.json` and `harness.json` each match the post-change side of their latest regenerate commit
  (`cbe9726` … `3b41211`). No version bump is required.
- The Codex hook definition embeds the package `sha256-tree-v1` digest, so any package change is a changed hook
  definition. The wrapper re-trusts tj-agents hooks after verifying the package; a bare `codex` needs `/hooks` review.
- Claude caches per commit (`~/.claude/plugins/cache/base-agents/engineering/<sha12>`); the `claude` wrapper,
  `open-claude`, `handoff-claude` and session recovery run `claude_standards_sync.py` before loading.
- A running session cannot pick up the repair on either host: Codex runs its integrity-checked `PLUGIN_DATA`
  snapshot; Claude keeps its loaded `CLAUDE_PLUGIN_ROOT`. This is the trust boundary and must not be bypassed.
- A running session is not trapped: `continuation_stop.outcome` returns no block when the session's latest prompt
  is a direct control (`pause`/`stop`/`cancel`, per `workflow_route.DIRECT_CONTROL`), and `workflow_route` records
  that receipt on UserPromptSubmit on both hosts.

## Remedy

1. Release the one-line source repair independently of PR #209: apply `70643fa`'s `continuation_stop.py` and test
   hunks verbatim, so #209 merges cleanly over them, plus a regression test that drives `binding_active` through the
   real `continuation_runtime`/`delivery_runtime` normalization with matching and divergent heads.
2. Document in `README.md` that a hook repair reaches a host only after merge + regenerate and a new refreshed
   session, and the exact operator action for an already-running session.
3. No cache patch, version bump, hook disable or continuation-state edit.

Operator action for an already-running blocked session (after the repair is on main): send `stop` (or `pause`) as
the whole prompt to end the turn, close it, and start a new session through the `codex`/`claude` wrapper,
`handoff-codex` or `handoff-claude`. Without the wrapper: Codex `codex plugin marketplace upgrade`, then
`codex plugin add engineering@base-agents`, then trust the changed hook in `/hooks`; Claude `/plugin marketplace update`
then `/plugin update engineering@base-agents` before starting the new session.

PR #209 note (not edited here): its `BUGS.md` adds B004 twice; its owner should de-duplicate it and link this repair.

```agent-host-coverage
{"schema_version":1,"shared_source":".agents/hooks/continuation_stop.py","hosts":[{"host":"claude","behavior":"Stop accepts a delivery binding whose remote_head_sha matches HEAD and rejects a divergent head.","source":".agents/hooks/continuation_stop.py","mapping":"Shared hook shipped as plugins/engineering/hooks/continuation_stop.py and wired in .agents/plugins/manifests/claude/engineering-hooks.json Stop dispatch.","verification":{"level":"planned","result":"pending","evidence":"test_continuation_stop.py real-normalization regression on Windows and Linux CI."}},{"host":"codex","behavior":"Stop accepts a delivery binding whose remote_head_sha matches HEAD and rejects a divergent head.","source":".agents/hooks/continuation_stop.py","mapping":"Same shipped hook wired in .agents/plugins/manifests/codex/engineering-hooks.json Stop dispatch through the snapshot loader.","verification":{"level":"planned","result":"pending","evidence":"test_continuation_stop.py real-normalization regression on Windows and Linux CI."}}]}
```

## Verification

- `test_binding_active_reads_the_head_through_real_artifact_normalization` errors with `binding-head-changed`
  against the unrepaired hook and passes with the repair.
- `python -B -m unittest discover -s .agents/hooks/tests -p test_continuation_stop.py`: 30 tests OK (Windows).
- `sync-generated.ps1 -Check` (529 files, 0 changed after local regenerate, output left uncommitted),
  `sync_harness_manifests.py --check` and the `host_coverage.py --stage plan` validator pass.

## Next Steps

1. Review, push, open PR, merge under the Authorization above; Linux evidence comes from `verify-linux` CI.

- Scope: only installed Stop-hook cache recovery.
- Current slice: delivery of the implemented remedy.
- Remaining scope: review and delivery.
- Done when: an obsolete installed hook cannot indefinitely trap a valid session after the source repair is released and the documented supported recovery action is taken.
