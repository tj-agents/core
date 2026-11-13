---
name: docs
description: Keep guidance docs honest: one owning document per rule, linked not restated, machine-checked where possible, examples where a label is ambiguous. Use when writing guidance or working markdown.

kind: convention
domain: process
---

# Docs

Owns where a rule lives, how guidance is written and checked, and the lifetime of working markdown.

## Describe the intended behavior

State the responsibility a standard assigns, the evidence that selects it and the normal lifecycle, so a reader
can act on a case the author has not seen. Repair an unclear boundary in its existing owner; incident details
belong in tests, a commit message or a debt record. Reserve hard prohibitions for material invariants and state
their reason.

## One rule, one home

Exactly one file owns a rule; everywhere else links to it. A second hand-maintained copy is a bug.

- A doc lives at the lowest node that fully contains its concern. Keep a topic index mapping topic to owner and
  check it before writing a rule.
- A generic rule states the shape; the consumer's own docs hold its concrete roster.
- A doc is either imported or summarized, never both.
- Never cite violation sites or transient artifacts (a plan file, a phase, a ticket) from a durable doc; record
  violations as debt through the selected profile.
- Check the code before writing a rule down.
- Where delivery must copy a rule across a package boundary, generate every copy from one source and fail a
  check when a copy drifts.
- Write third-party type, library and diagnostic names; paraphrase only the product's own vocabulary.
- A hook or check moves with the rule it enforces, and an open question moves with its section.

## Make it machine-checked wherever you can

If an analyzer, linter or formatter can enforce a rule, the doc gets one line and the diagnostic ID. Every
instruction file is reachable by link or import from something that loads it, and a guidance doc never links
a missing file. Give a concrete example where a label could mean several things; `template:check` also
requires one fenced example in each authored skill body. Review a guidance change once through `docs-review`;
its mechanical checkers run in CI.

```bash
python -B "<template:check skill-directory>/scripts/check_examples.py" --root . --base origin/main
```

## Sort a rule by the cost of missing it

| Rule | Home |
|---|---|
| Generic, consulted while doing the work | a shared load-on-demand skill |
| Project-specific and expensive to miss silently | that repository's always-loaded instructions |
| Cross-project and always applicable | global agent instructions |

## Working markdown

Scratch analyses, investigation prompts and handoff notes go where the selected profile puts them. Delete each
once it has served its purpose.
