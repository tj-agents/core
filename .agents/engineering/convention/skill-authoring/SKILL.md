---
name: skill-authoring
description: Authoring an agent skill in a tj-agents plugin repository — whether to extend an existing owner or create a new skill, sizing and splitting by subject and consumption rather than by trigger or section count, choosing a name that collides with nothing on either host, writing the description as the selection trigger, what a skill folder may hold, keeping a published name working through a compatibility entry, and which tests a skill owes. Use when creating, splitting, merging, renaming, retiring or reviewing a skill, or editing a skill's name or description.

kind: convention
domain: process
---

# Skill authoring

A skill is loaded only when an agent selects it, and every installed skill's name and description is in
every session's listing. A skill therefore costs discovery before it delivers anything: one more entry to
scan, one more selection to get right or wrong. Author a skill so that an agent doing the work it governs
selects it, and an agent doing anything else passes it by.

This convention owns how a skill is shaped and named. Other owners supply the rest; follow their links
rather than restating them here:

- **Kind**: [`SKILL_KINDS.md`](https://github.com/tj-agents/core/blob/main/SKILL_KINDS.md).
- **Lane**, and whether the skill may declare one: `engineering:lanes`.
- **Where the files live and what is generated**: the repository's layout owner —
  [`SOURCE_LAYOUT.md`](https://github.com/tj-agents/core/blob/main/SOURCE_LAYOUT.md) in core,
  `kit:check` in a kit-layout repository.
- **Shipped scripts and resources**: [`PACKAGING.md`](https://github.com/tj-agents/core/blob/main/PACKAGING.md).
- **One rule, one home** for the prose inside a skill: `engineering:docs-and-debt`.

## Extend an owner before creating a skill

Look the subject up first: the repository's catalog or capability index, then the skills installed on
both hosts. When a rule is consulted by the same task that already loads an existing skill, it belongs
in that skill, even if the existing name does not mention it. A new skill is justified only by a subject
that a task loads on its own.

## Size a skill by subject and consumption

One skill owns one subject that a reader loads as a unit. Split only when both halves are independently
consumed: a recurring task loads one without the other, and loading the other would cost it real
context or mislead it. A rule a few paragraphs long that sits beside its neighbour stays there, even if a
task occasionally needs it alone; reading an unused section costs less than an extra skill to discover
and select. Never split by trigger count, section count or file length.

Merge two skills when every task that loads one also loads the other. Keep supporting examples, guards
and checklists with the skill they support.

## Name the subject the reader is thinking of

A public name is a lowercase hyphenated word or phrase naming the subject an agent has in mind when it
needs the skill, not the mechanism inside it. Generation enforces the syntax and rejects an exact
duplicate within the repository; core's generator also rejects two names equal once their hyphens are
removed.

Before choosing a name, check this repository's skills and every installed plugin on both hosts for the
same bare name and for a near miss: a plural, a reordered phrase, or a name one hyphen away. No generator
sees other plugins, and none catches every near miss. Choose a different name for a near miss. When a bare name is shared with another publisher, write
the qualified `plugin:name` in every reference to it, because a bare name may select the other plugin's
skill.

## Write the description as the selection trigger

The description is the only text an agent sees before choosing. State what the skill owns, then a
`Use when …` sentence naming the situations and the words an agent will be using when it needs the
skill. Include only triggers this skill owns; a trigger that belongs to another skill makes the two
compete, and the wrong one can win. A description that would match most tasks is too broad, and the
skill is probably too broad as well.

Where host entry points are authored, as in core, they carry the canonical description verbatim and
generation fails when a copy differs: change the canonical description and every host entry point in the
same commit. The repository's layout owner says whether its entry points are authored or generated.

## A skill folder holds only what ships

Generation copies every file beside a canonical `SKILL.md` into each package that contains the skill.
Keep plans, reviews, working notes and debt records out of a skill folder. Record a skill's debt in the
`TECH_DEBT.md` of the area that owns it, outside every skill folder.

## Keep a published name working

A released skill name is a public interface: plans, route tables, other skills and habits name it.
Rename, split or retire it only with a compatibility path that stays until a recorded removal date:

- **One-to-one rename or move**: an alias from the old name to the new one in the repository's
  compatibility record.
- **Split, or a rename an alias cannot express**: keep the old name as a thin compatibility entry whose
  body contains only links to its replacements. Its description says that it is a compatibility entry,
  names the replacements and gives the removal date. It does not repeat the replacements' trigger words,
  so a session matching on the task selects a replacement directly instead of the stub.
- **Removal**: a debt entry in the owning area with the date and an objective condition, such as no
  repository's route table or instructions on its default branch still naming the old skill.

## Tests

Generation checks front matter, names, kind folders, host entry points and packaging; a rule-only skill
needs nothing more. A skill that ships a script ships tests for it in the repository's suite. Add a
focused test for a machine-checkable invariant the skill relies on, such as a compatibility entry that
must keep linking its replacements. Do not add a test that only asserts a sentence exists.
