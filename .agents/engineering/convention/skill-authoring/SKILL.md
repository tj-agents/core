---
name: skill-authoring
description: Authoring an agent skill in a tj-agents plugin repository — whether to extend an existing owner or create a new skill, sizing and splitting by subject and consumption rather than by trigger or section count, choosing a name that collides with nothing on either host, writing the description as the selection trigger, what a skill folder may hold, choosing a clean rename or an explicitly required compatibility path, and which tests a skill owes. Use when creating, splitting, merging, renaming, retiring or reviewing a skill, or editing a skill's name or description.

kind: convention
domain: process
---

# Skill authoring

For creating, splitting, consolidating or renaming a skill, enter `template:new-skill` first.
That selected gate resolves the authoring brief and delegates to the current host's native creator.
This convention supplies selection, sizing and naming rules to that gate and to reviews.

A skill is loaded only when an agent selects it, and every installed skill's name and description is in
every session's listing. A skill therefore costs discovery before it delivers anything: one more entry to
scan, one more selection to get right or wrong. Author a skill so that an agent doing the work it governs
selects it, and an agent doing anything else passes it by.

This convention owns whether a skill needs to exist, its selection trigger, name, and size. `template:check`
owns required skill content and layout validation. Other owners supply the rest; follow their links rather
than restating them here:

- **Kind**: [`SKILL_KINDS.md`](https://github.com/tj-agents/core/blob/main/SKILL_KINDS.md).
- **Lane**, and whether the skill may declare one: `machine:lanes`.
- **Where the files live and what is generated**: the repository's layout owner —
  [`SOURCE_LAYOUT.md`](https://github.com/tj-agents/core/blob/main/SOURCE_LAYOUT.md) in core,
  `template:check` in a Template-layout repository.
- **Shipped scripts and resources**: [`PACKAGING.md`](https://github.com/tj-agents/core/blob/main/PACKAGING.md).
- **One rule, one home** and concrete examples for changed guidance: `engineering:docs`; validate the
  required skill content and layout with `template:check`.

```text
Changed rule: every skill description names its selection trigger
Construction: description: "Owns query composition. Use when building a reusable query."
Call site: the agent selects query-building when the task asks to compose a reusable query
```

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
duplicate within one plugin; core's generator also rejects two names in one plugin equal once their
hyphens are removed.

The same subject in another plugin's context keeps the same bare name, such as `workflow:session` and
`engineering:session`. Otherwise, before choosing a name, check this repository's skills and every
installed plugin on both hosts for the same bare name and for a near miss: a plural, a reordered phrase,
or a name that differs only by hyphens. No generator catches every near miss. Choose a different name for
an unrelated exact match or a near miss. Write the qualified `plugin:name` in every reference to a shared
bare name, because a bare name may select the other plugin's skill.

## Mirror a host's native command

When a host already provides a capability natively, name the skill exactly after that command and make it
one skill on both hosts with extended host adapters (`extended_host_adapters` in
`.agents/plugins/sources.json`). Each host's entry point uses its native mechanism; the shared definition
supplies an implementation only for a host that lacks one. Never give the same capability different names
or different update paths per host.

```text
Both hosts ship a native code reviewer.
Skill `review`: each host's entry point invokes its own native reviewer.
```

## Write the description as the selection trigger

The description is the only text an agent sees before choosing. State what the skill owns, then a
`Use when …` sentence naming the situations and the words an agent will be using when it needs the
skill. Include only triggers this skill owns; a trigger that belongs to another skill makes the two
compete, and the wrong one can win. A description that would match most tasks is too broad, and the
skill is probably too broad as well.

A description change is one change: in the same commit, update every host entry point that repeats the
canonical description and review every one that words it for its host. The repository's layout owner
says which entry points do which, and what generation checks.

## A skill folder holds only what ships

Generation copies every file beside a canonical `SKILL.md` into each package that contains the skill. Keep
plans, reviews, working notes and debt records out of a skill folder. Record a skill's debt with
the selected profile under [the recording contract](../../../workflow/resources/problem-records.md).

## Replace names cleanly

When the user directs a clean rename or says not to preserve old names, remove the old entry,
aliases and forwarding paths, and update in-scope authored callers and both host adapters in the same
delivery. Do not infer a compatibility requirement from the old name having been published.

Preserve an old interface only when the user or an applicable project contract explicitly requires
compatibility. Record that requirement and its removal condition in the owning plan or debt entry.
A required compatibility entry contains only links to its replacements; its description names the
replacements and removal condition without repeating their selection triggers.

## Tests

Generation checks front matter, names, kind folders, host entry points and packaging; a rule-only skill
needs nothing more. A skill that ships a script ships tests for it in the repository's suite. Add a
focused test for a machine-checkable invariant the skill relies on, such as a compatibility entry that
must keep linking its replacements. Do not add a test that only asserts a sentence exists.
