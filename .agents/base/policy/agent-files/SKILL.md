---
name: agent-files
description: Keep AGENTS.md and CLAUDE.md paired within authorized instruction-file changes in projects adopting Base. Use when creating, moving, renaming or deleting an AGENTS.md or CLAUDE.md.
kind: policy
domain: behavior
---

# Pair agent instruction files

Owns the pairing of `AGENTS.md` and `CLAUDE.md` when a project adopts Base and the authorized work changes
its instruction files. Repository ownership does not establish adoption. Local-only plugin selection
preserves the owner's instruction files; installing Base does not authorize rewriting them or adding
Personal policy. Agent's [repository selection contract](https://github.com/tj-agents/agent/blob/main/.agents/agent/utility/plugins/SKILL.md#repository-selection)
owns adoption and configuration scope.

Create, move, rename or delete both files of a directory together. `AGENTS.md` owns the instructions; its
sibling `CLAUDE.md` contains only:

```text
@AGENTS.md
```

Within the authorized target, repair an incomplete pair in the current change, preserving distinct
owner-authored instructions and their scope in `AGENTS.md` first. Surface conflicting instructions rather
than choosing a new policy. Before delivery, check both directions within that target. A machine-local
profile file never supplies this rule.
