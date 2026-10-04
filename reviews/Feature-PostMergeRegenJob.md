# Code review — Feature/PostMergeRegenJob

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `3ea80014cb5efd60c547eed377b55d8c342711ba`  `(2026-10-04)`
**Security-reviewed up to commit:** `3ea80014cb5efd60c547eed377b55d8c342711ba`  `(2026-10-04)`
**Judgment:** `approved`

## Review pass — 2026-10-04 — full

**Candidate base:** `c21cdaf617672e3c8377a60899d0bea24d6b7b91`
**Candidate head:** `d3e4e8eaa70c7fadcd3ef6c895e1c8240c383f48`
**Candidate branch:** `Feature/PostMergeRegenJob`
**Candidate scope:** `all`
**Candidate path-set:** `(7 paths)` — descriptor `27f2c3852de93470b03fb933faa6b5f67886a40dda5d1aba761adab912e4da04`
**Candidate bundle:** `removed after completion`
**Candidate bundle identity:** `sha256:8aa27576ce7603dd2b78be72a897710d93688fb8a901729305ea4802412981f5`
**Work-order path:** `reviews/Feature-PostMergeRegenJob.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

### Findings

- [x] **NAT1 — HIGH — native-general** — `.github/workflows/ci.yml` (regenerate verify step)
  GitHub pwsh steps propagate only the last command's exit code; intermediate failures of
  `sync-generated.ps1 -Check`, tier payload or digest checks were masked whenever the final command
  passed, so a broken regeneration could push to main — and GITHUB_TOKEN pushes trigger no workflows,
  so nothing would re-check it. Fixed: every multi-command step sets `$ErrorActionPreference = 'Stop'`
  plus `$PSNativeCommandUseErrorActionPreference = $true` and explicitly checks ps1 exit codes.
- [x] **NAT2 — MEDIUM — native-general** — `.github/workflows/ci.yml` (commit-and-push step)
  A rejected `git push origin HEAD:main` was masked by the trailing digest check resetting
  `$LASTEXITCODE`, leaving main silently stale. Fixed by NAT1's error preference (the push now throws)
  and by replacing the `git diff --cached --quiet` probe with a non-failing `--name-only` capture.
- [x] **NAT3 — LOW — native-general** — `scripts/check_generated_paths.py`
  The guard read `generated_roots` from the PR's own `sources.json`, so a PR editing that file could
  exempt its own generated paths. Fixed: roots are read from the merge base via `git show`.
- [x] **NAT4 — LOW — native-general** — `.github/workflows/ci.yml` (commit-and-push step)
  The committed-digest HEAD check ran after `git push`, detecting a broken regeneration only once
  live. Fixed: it now runs between `git commit` and `git push`.

Native layer: Claude Code `code-review` (medium) over the frozen range — the four findings above, all
fixed on this branch. Security layer: `.github/workflows/ci.yml` is a classified security path
(`first_path` set), so the host security review ran over the trunk range — no findings above the
confidence bar: the `contents: write` regenerate job is confined to push-to-main events executing
main's own code with no pull_request-event bridge to its token; `github.base_ref` is
collaborator-controlled only (and was moved from template interpolation to `env:` as hardening); the
guard script's subprocess calls use list arguments with no shell. Guard verified locally in both
directions (clean branch exit 0; a range containing `plugins/**` exit 1 with the offending list).

## Review pass — 2026-10-04 — incremental

**Candidate base:** `d3e4e8eaa70c7fadcd3ef6c895e1c8240c383f48`
**Candidate head:** `3ea80014cb5efd60c547eed377b55d8c342711ba`
**Candidate branch:** `Feature/PostMergeRegenJob`
**Candidate scope:** `.github/workflows/ci.yml, scripts/check_generated_paths.py`
**Work-order path:** `reviews/Feature-PostMergeRegenJob.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

### Findings

No findings: the delta is the NAT1–NAT4 fixes and the `env:` hardening described above, re-verified by
the local guard runs and yaml parse; the PR's own CI run exercises the new guard and verify jobs
directly.
