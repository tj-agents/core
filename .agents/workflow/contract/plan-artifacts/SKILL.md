---
name: plan-artifacts
description: Keep one canonical Markdown plan or goal for substantive work, with current progress and recovery evidence. Use when creating, revising, recovering or reporting a substantive plan.
kind: contract
domain: process
---

# Maintained plan artifacts

Owns where a plan lives and what it keeps current. Quick answers and one-step work need no plan.

- Write an actual Markdown plan before presenting substantive planning as ready.
- Its location follows the selected profile. Without a profile rule, keep it machine-local in the host's
  plans or scratch directory and commit nothing. A standalone task keeps its goal in its task directory.
- Keep one canonical file. Apply corrections to it directly; read a named existing plan before changing
  it; resolve ambiguous ownership before creating another. The `templates/PLAN.md` beside this skill is a
  starting point, not a required format.
- Give its absolute path as a clickable link whenever creating, revising or resuming it.
- Keep authorized scope apart from proposed steps, and keep progress, actual verification, unresolved
  decisions and remaining work current. Checkpoint a material milestone, a changed blocker or owner, a
  deliberate transfer, or a context ending with state that cannot be reconstructed. Never claim
  unobserved work or passed tests.
- Before resuming, read the plan and reconcile it with available evidence.
- When the owner stays, record no route or lane decision.

```text
Profile sets no plan location; the user asks for a plan of a cache migration.
Write: <host plans directory>/cache-migration.md; return its absolute link; commit nothing.
Resume: read it, reconcile progress with Git, continue from its Next Steps.
```
