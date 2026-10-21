---
name: list-work
description: List selected work items and supporting plans in the current repository group, including their state and next action. Use when Tommy asks what work is open, which plans remain, what is active, or to list work about a subject.

kind: utility
domain: process
---

# List work

Read [repository selection](../../resources/problem-records.md#repository-selection) first. When a
provider is selected, load its qualified skill and use its list/read commands scoped by the requested
filter, limit, kind and state. Include tracker-only items with no local plan. The provider owns live item
state.

Run the shipped script from the skill directory for plans. The optional arguments are filter, limit, and
scope; `all` includes other repository groups.

On Windows:

```text
python -B "<skill-directory>\scripts\list-work.py" "<filter>" [limit] [scope]
```

On Linux or macOS:

```text
python3 -B "<skill-directory>/scripts/list-work.py" "<filter>" [limit] [scope]
```

Report the rows as printed, newest first. Keep out-of-scope and text-only matches as counts unless the
caller selected `all`. Blank state means the plan has no explicit checkbox or completion state. A selected
repository's plans show `supporting`: they are design and recovery context, never its live queue. Report
`skipped` repositories whose selection could not be read; an invalid selection in the current repository
stops the script.
