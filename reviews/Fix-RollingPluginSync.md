# Code review — Fix/RollingPluginSync

**Review status:** `complete`
**Judgment:** `approved`
**Reviewed up to commit:** `81dce32ea5f69deb1947ed6136824f33b45132da` `(2026-10-16)`
**Security-reviewed up to commit:** `81dce32ea5f69deb1947ed6136824f33b45132da` `(2026-10-16)`

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
  "candidate_head": "81dce32ea5f69deb1947ed6136824f33b45132da",
  "shared_source": ".agents/machine/scripts/rolling_plugins.py and startup_binding.py; shared hooks and selection generator",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Refresh and verify selected publisher main trees before native startup; fail closed and preserve active hook isolation",
      "source": ".agents/machine/scripts/rolling_plugins.py; startup_binding.py; claude_terminal_profile.py",
      "mapping": "Canonical runtime is generated into plugins/machine/resources/machine/scripts with host-specific hooks and cache materialization",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Reviewed clean through 81dce32e. Exact-head Linux CI 38824122187 passes, including generation, source and shared-runtime suites. Final test contracts passed focused checks (8e7fe5cec3d927f9, a70a098143b25ded); POSIX inventory and Windows wiring passed (1a9f7d8da48a1899, 44e7afa6a1748ea2). Multi-source integration checks and earlier actual native two-generation adapter acceptance (4d722d0af34b3626) remain valid. Exact-head Windows CI also passes; integrated installed-session activation awaits user merge and main publication."
      }
    },
    {
      "host": "codex",
      "behavior": "Refresh and verify selected publisher main trees before native startup; fail closed and preserve active hook isolation",
      "source": ".agents/machine/scripts/rolling_plugins.py; startup_binding.py; codex_terminal_profile.py",
      "mapping": "Canonical runtime is generated into plugins/machine/resources/machine/scripts with host-specific hooks and cache materialization",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Reviewed clean through 81dce32e. Exact-head Linux CI 38824122187 passes, including generation, source and shared-runtime suites. Final test contracts passed focused checks (8e7fe5cec3d927f9, a70a098143b25ded); POSIX inventory and Windows wiring passed (1a9f7d8da48a1899, 44e7afa6a1748ea2). Multi-source integration checks and earlier actual native two-generation adapter acceptance (4d722d0af34b3626) remain valid. Exact-head Windows CI also passes; integrated installed-session activation awaits user merge and main publication."
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

## Review pass — 2026-10-15 — incremental

**Candidate base:** `1be576a46f5f07f4688418ae9ecb5c0bdca8b59b`
**Candidate head:** `38b148ab03189aa667ff1c3780bd3deb47f27f70`
**Candidate branch:** `Fix/RollingPluginSync`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:5c860af4e5a9ba56f45f35dad60e0cad674057ba0a8c33053db624fc17812804 (12 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\zvnSsFw8ZY6I_eujlpT34r\8FR3O_OaxSOTFXkTZMK9tj`
**Candidate bundle identity:** `sha256:9d3df3214430ee4724451b39bfd7bd7b4f018e13a280d8db422f69d883908853`
**Work-order path:** `reviews/Fix-RollingPluginSync.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

### Findings

No new findings. Native review completed in 337.227 seconds with no retained issue; artifact
`always-latest-plugins-native-review/artifacts/d66b4019383cd2f3-rolling-native-incremental-review.log`.
Parent workflow/cache security checks completed against the same frozen delta under the unavailable-model
fallback. The tier gate reported no applicable stack conventions. All prior finding text and first-pass
judgment are unchanged. Combined rolling runtime suite passed 22 cases (one platform skip) in
`6786223bd000197f-rolling-final-runtime-regression.log`.

## Review pass — 2026-10-16 — multi-marketplace integration

**Candidate base:** `38b148ab03189aa667ff1c3780bd3deb47f27f70`
**Candidate head:** `fd17db491c899925ab260ee6ba6d99c268f47bce`
**Candidate branch:** `Fix/RollingPluginSync`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:d817cca95d991b3b4e73c1dca310754a79d7c117e649454bacf5f4b172c57ed4` `(33 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\zvnSsFw8ZY6I_eujlpT34r\fn9WE6eA7XfLHQqDFg-RMR`
**Candidate bundle identity:** `sha256:0ae8609070be9be9a753d322e4e0a07eff36ea1b745148a1fc3acc4a13ea8296`
**Work-order path:** `reviews/Fix-RollingPluginSync.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Descriptor: `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\always-latest-plugins\review\7e7f5613a780ed77cb1d0a83160f913113ecd4bd21309246874f369d3a221b80\descriptor.json`.
Patch SHA-256: `e0db49a1145f2e2d525fa31624f2fe813b29e7bd68660c036e18bae672121ae0`.
Native review completed from the frozen detached checkout in 423.531 seconds. Parent workflow and
publisher-boundary review covered the immutable integration; no new finding is retained. The tier gate reports no
applicable stack and the router reports no rules or violations. Incoming generated paths are identical
to the newly integrated main and the generated-path guard passes.

Focused multi-source adoption, selection validation, host settings and permission convergence passed.
CI run 38822493978 reaches 1,162 source tests on Linux with six failures confined to the POSIX native
Codex fixture in terminal-profile wiring; this failure is outside the integration delta. The test double
creates its inventory under a Windows npm path while POSIX bootstrap calls the PATH executable directly.
The isolated fixture repair is being validated separately; this review candidate remains immutable.

Native evidence: `always-latest-plugins-native-review/artifacts/66fb6aa0da62dd49-rolling-native-marketplace-integration-review.log`.
The only native allegation concerned generated files inherited by merging PR #270. It is rejected:
`git diff origin/main..fd17db49 -- plugins` is empty and the exact-head generated-output guard passed
locally (`6118696b1a4f2779`) and in CI. The watermark delta includes main's generated publication; the
PR delta does not. No source or policy finding remains. The separate POSIX test-double fix is 7d5e3372,
with the emitted-inventory probe (1a9f7d8da48a1899) and Windows wiring regression (44e7afa6a1748ea2) passed.

## Review pass — 2026-10-16 — final test contracts

**Candidate base:** `fd17db491c899925ab260ee6ba6d99c268f47bce`
**Candidate head:** `81dce32ea5f69deb1947ed6136824f33b45132da`
**Candidate branch:** `Fix/RollingPluginSync`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:9db3061a2994ac49577dc4ae20296955a46cbff3c3e292e5ade89c812fedad6e` `(3 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\zvnSsFw8ZY6I_eujlpT34r\f1nUaunWYjsVvwCMjBVjV6`
**Candidate bundle identity:** `sha256:460f5014f18b6cd5926e7081437100b72b1de31063c4c2bea4dd16eaf7e0b17b`
**Work-order path:** `reviews/Fix-RollingPluginSync.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Descriptor: `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\always-latest-plugins\review\7f59d46ae9d6623b15bf008c8c156357acdd8b2b0de9e0bdea5e09711af3e70d\descriptor.json`.
Patch SHA-256: `76fe4bef42d8ab2b7b6d105f270fb3b56a521eda4a8da0961203bd83efbae8b7`.
Selected lenses: native-general, api-contract, workflow. The native reviewer consumes this range from a
clean detached checkout. Unsupported specialist model fallback remains with the parent over the same
immutable bundle. No routed rules or violations. The unused 7d5e3372-only preparation was superseded
before dispatch so all three test corrections receive one review.

CI 38823306085 passed all 1,162 Linux source tests, then ran 1,145 shared-runtime tests with two obsolete
expectations: a retired alias and a required manifest version. Those expectations were updated in 81dce32e;
both focused tests pass (8e7fe5cec3d927f9, a70a098143b25ded). The POSIX fixture probe and Windows wiring
regression passed before 7d5e3372. Exact-head full CI remains required.

### Final synthesis

No new findings. Native review completed in 331.268 seconds; artifact
`always-latest-plugins-native-review/artifacts/9ea90e4de2020635-rolling-native-final-test-review.log`.
Parent api-contract and workflow passes over the same frozen three-file delta are clean. The changes
preserve all existing host payload assertions, require versionless manifests and retire shipped aliases,
while putting the POSIX inventory at the executable bootstrap actually calls. Tier conventions remain
inapplicable (`c18d03c7cc325450-rolling-final-test-tier-rules.log`). No runtime or trust boundary changed.
All previous findings retain their original text, severity and disposition. Exact-head Linux and Windows CI are green in run 38824122187. Delivery preflight and host coverage pass;
PR #269 is ready for review with merge left to Tommy.

Final delivery: CI run 38824122187 passed guard, verify-windows and verify-linux at 81dce32e.
Authoritative PR-body validation passed; PR #269 is ready, open and has no auto-merge request.
