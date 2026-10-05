---
name: guide
description: Content rules for a repository guide that designs the app with its reader and explains the code they are learning — product and system design chapters as inline-SVG diagrams the guide owns, code excerpts only from code that exists, the fewest sentences that carry each point, no restating of plans, process, standards or the knowledge record, and no quizzes, glossaries, tables or callouts unless asked. Use when designing an app's product or system design in its guide, or when writing, updating or reviewing a learning repository's guide chapters.

kind: convention
domain: process
---

# Design the app, then explain its code

A guide does two jobs for its reader: hold the design they code the app from, and explain the code they
have written. Every sentence passes one test: does the reader need it to code from this design or to
read this code?

- A design chapter shows the product design (what the app does for its user: commands, screens, flows)
  and the system design (components, boundaries, data model, key flows) as diagrams with the fewest
  words. It precedes the code on purpose: the reader codes from it.
- The guide owns the design. Plans keep sequencing, status and milestones and link to the chapters;
  changing the design means changing the chapter.
- A diagram is inline SVG styled with the page's theme variables, so it renders offline, in both themes
  and as a published artifact.
- A code excerpt quotes only code that exists at the current revision — the build fails otherwise. A
  design chapter describes what will exist but never quotes invented code; when a milestone adds code,
  add its code chapters then.
- When code changes, update the chapters and diagrams that quote or describe it in the same change.
- Give each point the fewest sentences that carry it: what the design or code does and means now. No
  history, no rationale for the choice made, no rejected alternatives.
- Never restate what another file owns: the plan, the roadmap, the learning process, the agreed
  standards, the knowledge record.
- No quizzes, glossaries, comparison tables, callout boxes, reading lists or other apparatus unless the
  reader asks for them.
- A comparison with a language the reader knows is one inline phrase, used only when it is the fastest
  route to the point.

The guide lives in `guide/` at the repository root and builds with its vendored builder;
`engineering:guide-build` owns the scaffold, the build and the excerpt mechanics.
