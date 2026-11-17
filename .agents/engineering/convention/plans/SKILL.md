---
name: plans
description: Shape of an implementation plan: phases that each end green, a verification gate per phase and a consumption contract for every consumable capability. Use when writing or executing a plan.

kind: convention
domain: process
---

# Plans

Owns what an implementation plan contains. Where it lives and how it is tracked is the selected profile's
choice; `workflow:plan-artifacts` owns the common maintained-plan contract.

- A plan breaks work too big for one commit into phases. Each phase states what it changes, why, and its
  verification gate, and every intermediate state builds and passes.
- A phase that ships a capability something else consumes pins its consumption contract: who calls it and the
  exact shape it returns. The consumer may come later; the output contract may not.
- Where prose leaves an implementation choice open, show the deciding code in the target file, written to the
  standards that govern that path.
- A plan holds unfinished work only. Delete it when its work is complete; Git history is the archive.

```text
Phase 2: export report rows.
Gate: `uv run pytest -q tests/test_export.py` and the CLI build pass.
Consumption contract: `report export` writes `report.csv` (UTF-8, header row) and prints its path; the
dashboard download in phase 4 reads that file.
```
