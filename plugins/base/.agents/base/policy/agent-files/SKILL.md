---
name: agent-files
description: Keep AGENTS.md and CLAUDE.md paired in every repository, with one shared instruction source.
kind: policy
domain: behavior
---

# Pair agent instruction files

Whenever you create, move, rename, or delete an `AGENTS.md` or `CLAUDE.md`, handle both files in that
directory together. `AGENTS.md` owns the instructions. Its sibling `CLAUDE.md` contains only:

```text
@AGENTS.md
```

Claude then loads the same instructions. If either file exists without the other, repair the pair as part of
the current change. Move any distinct instructions from an existing `CLAUDE.md` into `AGENTS.md` before
replacing it with the pointer.

Before delivery, check both directions across the changed repository: every `AGENTS.md` has its sibling
`CLAUDE.md`, and every `CLAUDE.md` has its sibling `AGENTS.md` with the exact pointer content. Do not rely
on a machine-local profile file to supply this repository rule.
