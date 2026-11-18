---
name: layout
description: Lay out a page people read so it can be scanned and revisited - a summary a reader can stop at, numbered sections, tables for parallel items, collapsible detail, diagrams for flows, and state kept distinct. Use when writing or restructuring a human-facing page such as a design page, Confluence page, project record, explainer or revision page.
kind: convention
domain: docs
---

# Page layout

A page people read is scanned before it is read. Structure carries the meaning; prose only joins it.
Medium-specific mechanics (Confluence panels and macros, artifact styling) belong to that medium's
skill, which applies this layout with its native pieces.

## Lead with what a reader can stop at

Open with a header table of the facts a reader checks first (status, owner or role, scope, date), then
an "In 30 seconds" list of three to five bullets. A reader who stops there has the point.

## Number the sections and separate them

One subject per numbered `##` section, a `---` rule between sections, and `### 2.1`-style subsections.
Numbers let a reader say "see 4.2" and let an index link to stable anchors.

## Put parallel items in a table

Items with the same shape (options, problems, decisions, risks, steps, owners) go in a table whose
headers name the comparison, such as `Problem | Effect | Fixed by` or `Choice | Chosen | Rejected because`.
Use bullets for short independent points. Break any paragraph longer than three lines.

## Hide what most readers skip

Put option detail, change logs and question-and-answer pairs in `<details>` blocks with the question or
topic as the summary. Keep the glossary as the last section.

## Draw flows

Draw any flow across three or more parts as a Mermaid diagram: `sequenceDiagram` for order over time,
`flowchart` for structure. One idea per diagram. Colour only through `classDef` with `fill`, `stroke`
and `color` set together so it reads in light and dark themes. Never draw ASCII art.

## Keep state distinct

Say whether each thing is proposed, agreed or shipped, with a date. Open questions are a task list with
an owner each. End with the sources and the date they were read.

```markdown
# Order service redesign

| | |
| --- | --- |
| **Status** | Agreed 21 Oct 2026, being built |
| **Owner** | Payments team |

### In 30 seconds

- Orders are keyed by one id across services.
- Events carry full state, so duplicates are harmless.

---

## 1. Why it changed

| # | Problem | Effect |
| --- | --- | --- |
| 1 | Two id maps | Duplicate orders |

---

## 2. Open questions

- [ ] Retention period for the event journal (owner: Ana)
```
