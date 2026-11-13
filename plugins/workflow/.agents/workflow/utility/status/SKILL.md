---
name: status
description: Read selected work items and supporting plans with execution state and next actions. Use when asking what work is open, which plans remain, what is active, or a named subject's status.
kind: utility
domain: process
---

# Status

Owns reporting open work items and supporting plans; it changes nothing.

Read [repository selection](../../resources/problem-records.md#repository-selection) first. When a
provider is selected, load its qualified skill and use its list/read commands scoped by the requested
filter, limit, kind and state. Include tracker-only items with no local plan. The provider owns live item
state.

Run the shipped script from the skill directory for plans. The optional arguments are filter, limit, and
scope; `all` includes other repository groups.

On Windows:

```text
python -B "<skill-directory>\scripts\status.py" "payments"
```

On Linux or macOS:

```text
python3 -B "<skill-directory>/scripts/status.py" "payments"
```

Report the rows as printed, newest first. Keep out-of-scope and text-only matches as counts unless the
caller selected `all`. Blank state means the plan has no explicit checkbox or completion state. A work-item
README's state and kind come from `tj item resolve` on its `- Work item:` reference; `Done` items are hidden
and an unresolved reference shows `unknown` with its reason. A selected repository's plans show
`supporting`: they are design and recovery context, never its live queue. Report `skipped` repositories
whose selection could not be read; an invalid selection in the current repository stops the script.
