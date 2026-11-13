---
name: committing
description: Commit each verified chunk of authorized work without asking, never stage ignored files, and push only a stable candidate. Use whenever a chunk of work goes green or before pushing.

kind: contract
domain: process
---

# Committing and pushing

Owns commit cadence, staging safety, commit messages and push cadence.

## Commit verified work without asking

When work is authorized and a discrete chunk passes its targeted checks, commit it. Do not leave finished work
uncommitted "for review": review runs off commits, uncommitted work is lost to a checkout or restore, and a later
`git add -A` sweeps it into an unrelated change. Work that belongs to another PR is committed on that PR's
branch.

## Never stage what Git ignores

Never `git add -f`, or otherwise stage, a path covered by `.gitignore` or `.git/info/exclude`. If an ignored
file genuinely belongs in a commit, ask first.

```text
$ git check-ignore -v .claude/settings.local.json
.git/info/exclude:16:/.claude/settings.local.json	.claude/settings.local.json
```

That output means the file stays unstaged.

## Messages and attribution

The diff shows what changed; the commit message carries why. Attribution lines follow the harness's
instructions. A PR body needs only Why and What; `engineering:open-pr` writes it.

## Push a stable candidate

Commit at every natural boundary; push only a stable candidate that needs remote validation, a real handoff or
a published checkpoint. Batch related fixes into one push, and never push bookkeeping alone.
