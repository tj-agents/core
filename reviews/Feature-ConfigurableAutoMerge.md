# Configurable auto-merge review

**Review status:** `complete`
**Reviewed up to commit:** `fef2e8ef87ed105555f692d59eec82a28f917b6e` `(2026-10-11)`
**Security-reviewed up to commit:** `fef2e8ef87ed105555f692d59eec82a28f917b6e`
**Judgment:** `approved`

## Review pass — 2026-10-10 — current-main recovery

**Candidate base:** `b4e6f1020b4c1edcfea8e21d6dae2ba5ebdb8a5e`
**Candidate head:** `6f35f036272ef3de9a54389c93eb5fae58791d2a`
**Candidate branch:** `Feature/ConfigurableAutoMerge`
**Candidate scope:** `all`
**Work-order path:** `reviews/Feature-ConfigurableAutoMerge.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

The candidate was rebased onto current main and revalidated. The native Codex reviewer launched but did not produce a terminal result, so the required fallback reviewed the bounded guarded-merge, authorization, trusted package provenance, Claude/Codex permission-refresh, and security-sensitive paths directly. Focused guarded-merge, binding, delivery-runtime, permission-sync, source-layout, catalog, generated-output, packaging, and both-host synchronization checks passed.

### Findings

No findings. The guarded command remains the only auto-merge permission granted, requires an explicit strict-boolean repository declaration, and rechecks exact-head identity, readiness, authorization, stop paths, labels, and review evidence before invoking GitHub. The heartbeat base update was reconciled without source conflicts; its continuation metadata changes do not alter the feature's merge guard, authorization resolution, trusted package provenance, or host permission paths. The user-authorized configuration delta explicitly enables guarded auto-merge and exempts only the `auth` stop class; the authorization-table stop remains non-exemptible, so this bootstrap PR still requires its recorded manual merge after green checks.

## Incremental review — 2026-10-11 — CI expectation repair

**Candidate head:** `fef2e8ef87ed105555f692d59eec82a28f917b6e`
**Pass judgment:** `approved`

The two failing PR-body assertions were updated from direct `--auto` invocations to the equivalent manual merge invocation. This preserves the feature invariant that direct `--auto` is denied and only the guarded wrapper can enable auto-merge. The focused PR-body suite and the full shared-runtime hook suite passed. No findings.
