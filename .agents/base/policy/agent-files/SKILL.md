---
name: agent-files
description: Keep AGENTS.md and CLAUDE.md paired in repositories that select Base, with one shared instruction source. Use when creating, editing, moving, renaming or deleting repository agent instruction files.
kind: policy
domain: behavior
---

# Pair agent instruction files

Owns the pairing of `AGENTS.md` and `CLAUDE.md` in repositories that explicitly select `base@tj-agents`.
Selecting Base adopts this generic pairing convention. Remote owner, account and employer identity do not
determine its scope. Base selection does not adopt Personal or authorize adding personal policy.

Apply the convention within the authorized target after reading its existing instructions. Repositories
that have not adopted Base keep their own layout; loading this skill elsewhere does not enroll them or
authorize changing their agent files.

When an authorized change creates, moves, renames or deletes one file, handle its sibling in the same
directory together with it. `AGENTS.md` owns the instructions; its sibling `CLAUDE.md` contains only:

```text
@AGENTS.md
```

If a pair in the authorized target is incomplete, repair it as part of that change. Preserve all distinct
owner-authored instructions from either file in `AGENTS.md` before replacing `CLAUDE.md` with the import.
Retain their scope and any host-specific qualifications; surface conflicting guidance instead of silently
choosing a new policy. Before delivery, check both directions within the authorized target. Report gaps
elsewhere without widening the change.

```text
example-org/tools selects Base; the task updates docs/CLAUDE.md:
Reconcile the docs/ pair, preserving its instructions; leave other directories alone.

A repository does not select Base; the task edits its existing CLAUDE.md:
Keep its own layout; this convention does not require adding AGENTS.md.

An employer repository selects Base; the task updates root agent instructions:
Pair the root files and preserve employer policy; do not select or inject Personal.
```
