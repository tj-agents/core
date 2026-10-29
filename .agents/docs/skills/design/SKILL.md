---
name: design
description: The shape of an approach or design page for a change - header, In 30 seconds, contents, background and plan diagrams, the problem, Rule | Why, decisions with their options, what could go wrong, running it, open questions, delivery, glossary, change log and what was not verified. Use when writing, restructuring or reviewing an approach, design, spike or options page in any medium.
kind: standard
domain: docs
---

# Design page

Owns the sections of an approach page and what each carries. Load `docs:layout` for page conventions and
`docs:diagram` for every diagram; the medium's skill, such as `work:confluence`, supplies its native pieces.

## Place it and follow its space

Put it under the page of the feature or area it changes. Search that space for its own conventions, such as
an options-page template, a status vocabulary or a diagram standard, and follow them by link.

## Shape

1. Header table: work item, status, owner, reviewer, last updated.
2. "In 30 seconds": problem, fix, done when. A lead who reads only this knows what and why.
3. Contents, two levels.
4. Background: how it works today, as a diagram, with every moving part a newcomer meets and why it exists.
5. The problem: what breaks without the change; why the obvious shortcut fails, collapsed.
6. The plan: a diagram of the mechanism, then a `Rule | Why` table.
7. Decisions, each decided or undecided. Each choice's options collapse into `Option | Verdict | Why`
   (chosen, rejected, dropped), then what was given up.
8. What could go wrong: `# | Risk | What we do about it | Status` (covered, partly, open, check, manual,
   to do, unknown, accepted). Cover load on consumers, alerting, unknown subscribers, readiness of
   dependents, re-runs and partial failure, and writes that destroy good data. This catches what code
   review misses.
9. Running it: prerequisites as a task list, steps per environment or tenant, order, rollback.
10. Open questions as a task list, each with an owner.
11. Delivery: `Change | What it does | State`.
12. Glossary and change log, each collapsed. Every change to the approach gets a dated line.
13. A closing italic line saying what was not verified and when the code was read.

```text
# Order id unification          header: AB-123 | Proposed | Payments | Ana | 2 Nov 2026
In 30 seconds                   problem, fix, done when
1. Background                   sequenceDiagram of today
2. The problem                  shortcut, collapsed
3. The plan                     sequenceDiagram after + Rule | Why
4. Decisions                    Option | Verdict | Why, collapsed
5. What could go wrong          risk table with statuses
...
_Not verified: production row counts. Code read 2 Nov 2026._
```

## Readability

Plain words; jargon goes in the glossary. Every moving part, rule and decision carries its why.
