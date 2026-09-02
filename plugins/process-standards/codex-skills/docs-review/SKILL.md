---
name: docs-review
description: Apply the canonical isolated review workflow to a documentation or agent-metadata-only branch using accuracy, contradiction, ownership, concision, dangling-reference, and followability lenses. Use to review docs, plans, skills, or a meta-only PR; route mixed runtime/product/package/CI-selection diffs to review.
domain: process
---

# Documentation review mode

This is the documentation mode of the canonical `review` pipeline. It uses the same frozen candidate,
native/general layer, fresh read-only dispatches, result validation, parent synthesis, canonical work order,
status, watermark, and explicit review-and-fix authorization. Only the scope guard, loaded rules, and lenses
differ.

In scope: Markdown, agent metadata under `.agents/`, `.claude/`, and `.codex/`, plans, documentation,
`AGENTS.md`, `CLAUDE.md`, and `README*`. In an agent-standards source repository this also includes its
process hooks, deterministic workflow helpers/tests, and generated plugin mirrors when they cannot affect a
product build or runtime.

## Scope guard

Resolve and freeze the candidate exactly as `review` Stage 1. If any frozen path affects runtime, product
code, a published package manifest/lockfile, migrations, or CI test selection, stop and route the entire
mixed candidate to `review`.

A pure closeout whose net diff contains deletions only is exempt because no surviving content remains for
these lenses:

```bash
git diff --diff-filter=ACMRT --name-only "<base>..<head>"
```

Any surviving path makes this an ordinary docs review.

## Work order and native layer

Use the same `reviews/<branch-slug>.md` contract from `review-lifecycle`. The parent records status
`in-progress` and the frozen candidate before review. Run the native/general layer over that descriptor,
using the bounded `review-lens` fallback when the host has no callable native review.

## Rules

Load the root and changed-path `AGENTS.md` files, the plan floor and `plans` for plan artifacts,
`review-lifecycle` for work-order changes, `handoff` for transfer instructions, and sibling skills a
changed skill names. Use the route table when it covers the paths. Convention findings require an owning
rule; accuracy and contradiction findings stand on repository evidence.

## Documentation lenses

Dispatch only relevant fresh lenses, using the same immutable descriptor and concurrency rules as
`review`:

- accuracy: paths, headings, names, commands, flags, behavior, and configuration must match the repository;
- contradiction: changed rules must agree with sibling and local guidance;
- one-rule-one-home: durable rules belong to their narrow owner, with hubs remaining pointers;
- recurring-context concision: `AGENTS.md`, `CLAUDE.md`, agent playbooks, and `SKILL.md` additions must
  add a real constraint rather than narration or duplication;
- dangling references: durable guidance must not depend on disposable plans, phases, tickets, or scratch
  files; and
- followability: each instruction has an unambiguous owner, action, and pass condition.

When agent guidance changes, run
`python <candidate-bundle>/tree/.agents/hooks/docs_reachability.py --root <candidate-bundle>/tree`.
Execute the frozen exported tree's helper against that same tree, never against the live checkout, and
treat each error as accuracy evidence.

Fresh lenses do not see sibling conclusions or write the artifact. The parent verifies repository evidence,
deduplicates, assigns severity and stable IDs, and drops preference-only rewrites, unchanged pre-existing
issues, and findings below the effort-adjusted confidence bar. Retained findings name one concrete edit.

## Complete and report

The parent finalizes the canonical work order exactly as `review` Stage 7: one judgment, status
`complete`, and a watermark at the frozen head. Use IDs such as `ACC#`, `CON#`, `HOME#`, `CONC#`,
`DANG#`, and `INST#`.

If a plan owns the branch, the completed pass is one material review transition. Report range, finding
counts, canonical work order, and watermark. Remediation begins only under explicit combined authorization
and returns through `incremental-review`.
