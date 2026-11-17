---
name: docs-review
description: Review documentation or agent-metadata-only changes in one pass for accuracy, contradictions, ownership, concision and followability. Use for docs, plans, skills or meta-only PRs.

kind: workflow
domain: process
---

# Documentation review

Owns one review pass over documentation and agent metadata: Markdown, `.agents/`, `.claude/`, `.codex/`,
plans, `docs/`, `AGENTS.md`, `CLAUDE.md` and `README*`. Resolve the candidate as `engineering:review`
Stage 1 does. If any changed path affects runtime, product code, a package manifest or lockfile, migrations
or CI test selection, route the whole candidate to `engineering:review`. A candidate whose surviving diff is
empty is exempt:

```bash
git diff --diff-filter=ACMRT --name-only "<base>..<head>"
# No output: deletions only, nothing to review. Any path: review it below.
```

Run the `review` Stage 3 native layer, then one pass covering:

- accuracy: paths, headings, names, commands, flags and behavior match the repository;
- contradiction: changed rules agree with sibling and local guidance;
- one rule, one home: a durable rule lives with its narrow owner and hubs only point to it;
- concision: `AGENTS.md`, `CLAUDE.md` and `SKILL.md` additions add a real constraint, not narration;
- dangling references: durable guidance never depends on a plan, ticket or scratch file; and
- followability: each instruction has one owner, action and pass condition.

Load the root and changed-path `AGENTS.md` files and the sibling skills a changed skill names. A convention
finding names its owning rule; accuracy and contradiction findings stand on repository evidence. The
repository's CI runs the example and reachability checkers; read their results rather than rerunning them.
The parent verifies, deduplicates and assigns severity, dropping preference-only rewrites and unchanged
pre-existing issues. Report findings, the reviewed range and the rules applied.
