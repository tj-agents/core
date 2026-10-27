---
name: solution-assessment
description: Assess existing capabilities and credible solutions once before choosing an implementation. Use when introducing a project, reusable tool, infrastructure capability, or general technical mechanism.
kind: policy
domain: behavior
---

# Assess a solution

When a new idea is introduced, first consult that same idea's recorded assessment before doing
research. If it is complete, carry its decision forward. Otherwise, once before choosing an
implementation, check repository capabilities and credible public solutions using current primary
sources, and inspect relevant implementations when behavior matters. Compare adoption, forking,
selective reuse, custom implementation, and keeping the current solution against the intended
outcome; choose the smallest suitable approach.

Solve deterministic work with deterministic code: a script, fixture or dummy process, never a model
session.

```text
Test the session-close watcher against `python -c "import time; time.sleep(600)"`, not a Claude session.
```

Record that the assessment is complete, its useful references, limitations, and rationale in the
existing task context or goal/decision artifact. Distinguish observed behavior from source inspection
and documentation claims. Small ideas need no new plan, configuration, database, or command just to
record the decision. Keep routine edits and application-specific business behavior proportionate;
assess a reusable technical component when selecting one.

Handoff, resume, compaction, implementation steps, branch changes, or rereading this rule carry the
completed assessment forward and never rerun it. Reopen it only at the user's explicit request.
This assessment grants no
authority to install, execute third-party code, replace a component, or publish changes; those actions
retain their existing gates.
