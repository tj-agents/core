---
name: agent-files
description: Keep AGENTS.md and CLAUDE.md paired in every repository, with one shared instruction source. Use when creating, moving, renaming or deleting an AGENTS.md or CLAUDE.md.
kind: policy
domain: behavior
---

# Pair agent instruction files

Owns the pairing of `AGENTS.md` and `CLAUDE.md` in repositories whose GitHub owner is listed in
`repo-owners.json`. Any other repository keeps its own layout; edit its agent files only when the work
requires it, and never add personal conventions or settings to them.

Create, move, rename or delete both files of a directory together. `AGENTS.md` owns the instructions; its
sibling `CLAUDE.md` contains only:

```text
@AGENTS.md
```

If either file exists without the other, repair the pair in the current change, moving any distinct
instructions from an existing `CLAUDE.md` into `AGENTS.md` first. Before delivery, check both directions
across the changed repository. A machine-local profile file never supplies this rule.
