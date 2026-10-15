# Code review — Fix/RollingPluginSync

**Review status:** `complete`
**Judgment:** `changes-requested`
**Reviewed up to commit:** `1be576a46f5f07f4688418ae9ecb5c0bdca8b59b` `(2026-10-15)`
**Security-reviewed up to commit:** `1be576a46f5f07f4688418ae9ecb5c0bdca8b59b` `(2026-10-15)`

## Review pass — 2026-10-15 — full

**Candidate base:** `f2dd95cae5aef351017eea4d7ce3dc39a9fcae76`
**Candidate head:** `1be576a46f5f07f4688418ae9ecb5c0bdca8b59b`
**Candidate branch:** `Fix/RollingPluginSync`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:cfac483ab5230be35f21498ba3d9e32930138d4d7d1e5e14764d9ea5c972b827` `(82 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\zvnSsFw8ZY6I_eujlpT34r\larU2JrqoKyq2ddBh_PtSv`
**Candidate bundle identity:** `sha256:bf8748e5e07423a7121485d0acf675b52be113a65792d3af43d3f7a235598a30`
**Work-order path:** `reviews/Fix-RollingPluginSync.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Descriptor: `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\always-latest-plugins\review\95aad4d89aeaa0acaad9d74187f3ed4af824bdadc46e1c39edcca123116a5fa1\descriptor.json`.
Patch SHA-256: `c8f250edcd76b30e58d22e3ff4275fe310f4adf76700c8fcfb7d2c46a68b8cc7`.
Selected lenses: native-general, security, workflow. One independent wave.
Routed rules: none; no route violations. Frozen repository guidance and tier conventions still apply.
Main was fetched and merged once in `af100167` before this frozen candidate. The preparation helper's
unrelated expired-review garbage collection was skipped in a temporary wrapper after it repeatedly
scanned 381 historical descriptors; candidate construction and validation used the shipped helper unchanged.

### Findings

Native review completed from the clean detached checkout at the frozen head. Security and workflow
review-lens dispatches failed before starting because gpt-5.3-codex-spark is unsupported by the account;
those bounded checks returned to the parent over the same frozen bundle.

- [x] **R1 — HIGH — workflow** — `.agents/machine/scripts/rolling_plugins.py:265`
  `effective.update()` replaces an entire `enabledPlugins` mapping when a later source mentions one
  plugin. Claude merges these maps by plugin ID, so a user-enabled package omitted by project settings
  can still load natively without entering the refresh set, and earlier explicit disables can disappear.
  Merge selection and marketplace maps by key while preserving native precedence and pass only the
  necessary launch overrides rather than flattening unrelated settings into a CLI-precedence blob.
  Evidence: frozen `claude_settings`/`_prepare`; official Claude plugin-loading reference, "Find where
  a plugin is enabled", checked 2026-10-15. Confidence high.

- [x] **R2 — HIGH — security** — `.agents/machine/scripts/rolling_plugins.py:559`
  `_write_tree` creates and removes paths before checking their ancestors; its deletion bound is the
  same potentially redirected `destination.parent`. A junction/symlink in a staging ancestor can
  redirect replacement/deletion into another directory before the later `_verified_tree` rejects it.
  Reject redirected ancestors before any cache mutation, including checkout/lock/staging paths, and
  validate marketplace/plugin identity components before composing cache destinations. Add a sentinel
  regression proving an outside directory stays byte-identical. Confidence high.

- [x] **R3 — HIGH — workflow** — `.agents/machine/scripts/startup_binding.py:88`
  Both permission-helper candidates miss the shipped `.agents/machine/utility/plugin-selection` path
  when the coordinator runs from `resources/machine/scripts`. Every selected packaged session fails
  before launch. Include the package's canonical `.agents` location and exercise both helper lookups
  from a disposable packaged layout. Confidence high; generated-path existence probe confirmed both
  current candidates absent and the canonical helper present.

- [x] **R4 — MEDIUM — security** — `.agents/machine/scripts/rolling_plugins.py:353`
  `_completed` spawns a child before asking the shared deadline for its remaining budget. An expired
  deadline raises outside the timeout handler, leaving the child alive after preflight releases its
  lock. Check the budget before spawning and terminate the child on any post-spawn exception.
  Evidence: frozen function orders Popen before deadline.remaining and catches only TimeoutExpired.
  Confidence high.

### Synthesis and evidence

Independent native-general review completed successfully in 743.559 seconds; artifact
`always-latest-plugins-native-review/artifacts/889b22a419d011b6-rolling-native-review.log`.
Its proposed snapshot-helper finding was rejected: for package/resources/machine/scripts,
`HERE.parents[2]` is the package root, and a direct generated-package import successfully loaded
package/hooks/codex_hook_snapshot.py. Inspecting the adjacent permission lookup instead established R3.
Parent security and workflow passes completed against the frozen bundle after the unsupported-model
fallback. No additional finding is retained beyond R1–R4. Exact-head CI failed on stale launch fixtures
and fixture Git identity; the focused fixture repairs remain a delivery gate alongside these findings.

```agent-host-coverage
{
  "schema_version": 1,
  "candidate_head": "1be576a46f5f07f4688418ae9ecb5c0bdca8b59b",
  "shared_source": ".agents/machine/scripts/rolling_plugins.py and startup_binding.py; shared hooks and selection generator",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Refresh and verify selected publisher main trees before native startup; fail closed and preserve active hook isolation",
      "source": ".agents/machine/scripts/rolling_plugins.py; startup_binding.py; claude_terminal_profile.py",
      "mapping": "Canonical runtime is generated into plugins/machine/resources/machine/scripts with host-specific hooks and cache materialization",
      "verification": {
        "level": "source",
        "result": "limited",
        "evidence": "Native disposable adapter acceptance 4d722d0af34b3626 passed two generations for both hosts. Source startup and convergence tests were reviewed. Full packaged launch is blocked by R3; CI 38810619930 has failing fixtures."
      },
      "exception": {
        "constraint_evidence": "No installed integrated-launch acceptance is claimed; publication and activation await user merge. R1\u2013R4 and CI repairs must complete first.",
        "supported_other_host_outcome": "Both hosts passed native disposable payload replacement and deletion; both remain subject to the same packaged permission-helper defect."
      }
    },
    {
      "host": "codex",
      "behavior": "Refresh and verify selected publisher main trees before native startup; fail closed and preserve active hook isolation",
      "source": ".agents/machine/scripts/rolling_plugins.py; startup_binding.py; codex_terminal_profile.py",
      "mapping": "Canonical runtime is generated into plugins/machine/resources/machine/scripts with host-specific hooks and cache materialization",
      "verification": {
        "level": "source",
        "result": "limited",
        "evidence": "Native disposable adapter acceptance 4d722d0af34b3626 passed two generations for both hosts. Source startup and convergence tests were reviewed. Full packaged launch is blocked by R3; CI 38810619930 has failing fixtures."
      },
      "exception": {
        "constraint_evidence": "No installed integrated-launch acceptance is claimed; publication and activation await user merge. R1\u2013R4 and CI repairs must complete first.",
        "supported_other_host_outcome": "Both hosts passed native disposable payload replacement and deletion; both remain subject to the same packaged permission-helper defect."
      }
    }
  ]
}
```

R1 fix evidence: identity-wise merge preserves source precedence and explicit disables; launch overrides
retain supplied CLI fields without elevating unrelated file settings. Four Claude cases passed in
`b436dc9b65110cd1-rolling-claude-selection-review-fix.log`.

R2 fix evidence: cache writes/deletes, locks, checkouts and promotions reject linked or reparse
ancestors before mutation. Identity components and publisher URL segments are validated before paths
are composed. Windows junction sentinel, lock, checkout and traversal cases passed in
`380524bbd0cec6b3-rolling-cache-boundary-review-fix.log` (four boundary tests).

R3 fix evidence: packaged permission lookup includes the canonical `.agents` directory. Eight startup
binding cases passed, including both helper imports from a disposable packaged layout, in
`024ca2385dff225c-rolling-packaged-coordinator-review-fix.log`.

R4 fix evidence: an expired budget prevents spawn; any post-spawn exception terminates the child.
Both expiry regressions passed in `165396aa4b823c64-rolling-deadline-review-fix.log`.
