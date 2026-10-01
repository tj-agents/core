# Code review — Fix/SecurityReviewCheckoutScope

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `c5eea99`  `(2026-10-01)`
**Judgment:** `approved`

## Review pass — 2026-10-01 — full

**Candidate base:** `6d163f10b7c03aebf789ebdeb9bcab41dab0d3dd`
**Candidate head:** `a7696a820384336fd98472ad1b7dc8cadd9e9b45`
**Candidate branch:** `Fix/SecurityReviewCheckoutScope`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:4f338de02a0aad2810109049934db3d0fa5f7d732ab560bf1e565f4e0caabc3c` `(8 paths)`
**Work-order path:** `reviews/Fix-SecurityReviewCheckoutScope.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

**Lens coverage:** each pass's native layer was Claude Code's built-in `code-review`, given the frozen
range plus ` -- <authored paths>`. No security-sensitive path, and no tier conventions apply to core.

### Findings

- [x] **SR1 — MEDIUM — native** — `.agents/engineering/workflow/review/SKILL.md:178`
  Being at the frozen head is not enough for `security-review`, which diffs the working tree against
  `origin/HEAD`'s merge-base. Fix: use it only for a clean checkout at the frozen head, full scope, and
  a `trunk_base` equal to that merge-base. Resolved in `b7ee1d7`.
- [x] **SR2 — HIGH — parent** — `.agents/engineering/workflow/review/SKILL.md:93`
  The shared procedure named Claude's and Codex's reviewers, against AGENTS.md: host-only material
  belongs in `.claude/` or `.codex/` entry points. Fix: Stages 3 and 6 name no host and defer to
  `review`'s host entry point; `.claude/skills/review` names `code-review`/`security-review`,
  `.codex/skills/review` names `codex review --base`; review registered as an extended host adapter.
  Resolved in `709c36c`.
- [x] **SR3 — HIGH — native** — `.agents/plugins/sources.json:284`
  Registering `review` in `extended_host_adapters` broke the contract test that pinned the list.
  Fix: the test covers every registered adapter. Resolved in `74d2428`.
- [x] **SR4 — MEDIUM — parent** — `scripts/sync_plugin_packages.py`
  Nothing enforced the AGENTS.md placement rule. Fix: `host_only_terms` in `sources.json`, and
  generation fails when a shared skill Markdown file contains one. Resolved in `17d3122`, refined over
  two review rounds in `3d48595`, `e148adb` and `89741f1`: case per pattern, slash, formatted and
  linked spellings caught, and longer names, path segments and host-neutral prose allowed.

## Review pass — 2026-10-01 — incremental

**Candidate base:** `e148adb`
**Candidate head:** `89741f1`
**Candidate branch:** `Fix/SecurityReviewCheckoutScope`
**Candidate scope:** `all`
**Work-order path:** `reviews/Fix-SecurityReviewCheckoutScope.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

**Lens coverage:** the native layer was Claude Code's built-in `code-review` at `low`, run on the
pattern-only delta. It found nothing.

### Findings

None.

## Review pass — 2026-10-01 — incremental (base reconciliation)

**Candidate base:** `89741f1`
**Candidate head:** `c5eea99`
**Candidate branch:** `Fix/SecurityReviewCheckoutScope`
**Candidate scope:** `all`
**Work-order path:** `reviews/Fix-SecurityReviewCheckoutScope.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

**Lens coverage:** a parent review of the merge of `origin/main` (#77, Codex lanes moved to 6.1). The only
authored file both sides changed was `.codex/skills/review/SKILL.md`; it merged cleanly to the 6.1 model
plus this branch's Codex reviewer lines. The conflicts were only digest and generated files, which were
regenerated. The affected tests pass: review native layer, source layout, catalog, harness, workflow
contracts, review workflows and lane tables.

### Findings

None.
