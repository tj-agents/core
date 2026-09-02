---
name: docs-and-debt
description: Keeping a repository's guidance corpus honest — one rule with exactly one owning document that everywhere else links to rather than restates, a doc living at the lowest node that fully contains its concern, a topic index mapping topic to owner, every instruction file reachable from something that actually loads it and checked by a hook, one line plus a diagnostic id where a machine can enforce the rule instead of prose re-arguing it, never naming violation sites in a rule doc because the citations rot, tech debt recorded in the file owning the problem and deleted when fixed, and throwaway working markdown kept in the repo then deleted once it has served its purpose. Use when writing or editing any guidance doc, adding a rule, finding the same rule in two places, logging tech debt, or creating a scratch analysis or handoff note.
domain: process
---

# Docs and tech debt

## One rule, one home

**Exactly one file owns a rule.** Everywhere else links to it and never restates it. **A second copy is a bug,
not emphasis** — two copies drift the day one changes, and the drift is invisible because both read as
maintained.

- **A doc lives at the lowest node that fully contains its concern.** Single-component → that component's own
  folder, thin, inheriting upward and never restating. Cross-component or orchestration → the root. Create one
  only where genuinely specific content exists.
- **Keep a topic index** mapping topic → owning doc, and look a topic up there *before* writing a rule down.
  Without an index, discovery depends on happening through the right file, and duplicates accumulate silently.
- **Generic rules and project specifics never straddle a file.** A generic rule states the shape; the
  consumer's own docs hold its concrete roster. That separation is what lets the generic half be extracted and
  shared.
- **A doc is either imported or summarized, never both.** An import already loads the body, so a summary
  beside it is the second copy.
- **Never name violation sites in a rule doc.** They get fixed and the citation rots — silently, because
  nothing checks it. Violations belong in the tech-debt file that owns them.
- **Never cite a transient artifact** — a plan filename, a phase number, a ticket — from a durable doc. The
  reference is engineered to dangle.
- **Check the code before writing the rule down.** Rules that teach what the codebase has already moved past
  read exactly as maintained as correct ones.

### Define-once is an authoring rule; delivery may still have to copy

**Where a rule is *authored* once, but the mechanism that delivers it cannot reach across a boundary, the copy
is unavoidable — so generate it and check it.** A packaged plugin, a vendored hook, a published npm or NuGet
payload all copy their contents on install and cannot reference a file outside their own root. Believing
otherwise is what produces a shipped artifact pointing at a path that exists only on the author's machine.

The rule that follows: **one authored source, every copy generated, and a check that fails when a copy drifts
from it.** A hand-maintained second copy is the bug this whole section is about; a *generated* second copy is
just delivery. If you cannot generate it, you cannot honestly claim one home.

### Over-generalising loses the rule; it does not portabilise it

Only the **product's own** identifiers make a doc unportable. A framework type, a third-party library, an
analyzer diagnostic ID — those name no product and belong in the generic rule.

Stripping them out is not neutral, it is destructive:

- a reader cannot grep for *"a reset tool"*, and will not find the library it means;
- a build gate, hook or lint rule cannot match on *"a host factory"*, so the rule silently drops from
  enforceable to advisory;
- most importantly, sometimes **the concrete name *is* the rule** — where the presence of one specific type is
  what classifies a file into one tier or another, replacing it with a paraphrase deletes the criterion while
  the prose still reads complete.

Write the type name. Reserve the paraphrase for the product's own vocabulary.

### Enforcement moves with the rule it enforces

A hook, gate, check or lint rule is part of its rule's home. When a rule moves to another file or another
repository, its enforcement moves too. Left behind, the two drift with **nothing watching** — the standard says
one thing and the gate enforces the older thing, and both look maintained.

### An open question is content — a move must carry it

An explicitly-flagged unresolved decision ("open call — settle this and replace this paragraph") is worth more
than most prose, and it is the first thing lost in a relocation because it reads like scaffolding. **An
unresolved decision nobody can see is one nobody will ever resolve.** Carry it, or resolve it deliberately;
never let it evaporate.

## Make it machine-checked wherever you can

- **If an analyzer, linter, or formatter can enforce it, the doc gets one line and the diagnostic id.** Prose
  is for rules a tool cannot express. Before writing a style rule, check whether config can hold it.
- **Every instruction file must be reachable** — by plain link or import, followed transitively — from
  something that actually loads it. A doc reachable from nothing is loaded nowhere, which is how a convention
  goes unread until a shipped feature violates it. Check it with a hook, and fail a guidance doc that links a
  file which does not exist.
- Keep a rule's statement short: statement, anti-pattern, one example. Headings that are imperative rule
  statements ("Repositories inherit the module base") beat topic labels ("Repositories").

## Sort a rule by the cost of missing it, not by topic

A load-on-demand skill applies only when it is invoked, so it is safe **only** for rules the task itself will
summon. **A rule whose violation is silent and costly stays in the always-loaded instructions** — that is the
row to respect, and getting it wrong is worse than having no skill at all.

| Rule | Home |
|---|---|
| Generic, consulted while doing the work | a shared load-on-demand skill |
| Project-specific and expensive to miss silently | that repo's always-loaded instructions |
| Cross-project and always applicable | your global agent instructions |

## Tech debt

Record tech debt in the `TECH_DEBT.md` belonging to the area that **owns the problem**; if that area has none,
create it there rather than adding the entry to a broader parent. **Once the debt is addressed, delete the
entire entry** — a resolved entry retained as an archive is just another stale doc.

A shortcut is acceptable only where it is genuinely, provably the right call — and then it is *logged* with the
reasoning, never left silent.

## Throwaway working markdown

Ad-hoc markdown — an investigation prompt, a scratch analysis, a handoff note for another tool or agent — goes
**in the repository**, never in a temp or scratchpad directory. A scratchpad is invisible to the human and to
other tools operating on the repo, so a doc written there is effectively lost.

These are working docs, not an archive: **delete the file once it has served its purpose** — the handoff
happened, the question was answered, the analysis landed in code. Don't let throwaway markdown accumulate.
