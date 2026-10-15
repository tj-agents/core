---
name: list-work
description: List plans in the current repository group, including their state and next action. Use when Tommy asks what work is open, which plans remain, what is active, or to list work about a subject.

kind: utility
domain: process
---

# List work

Run the shipped script from the skill directory. The optional arguments are filter, limit, and scope;
`all` includes other repository groups.

On Windows:

```text
python -B "<skill-directory>\scripts\list-work.py" "<filter>" [limit] [scope]
```

On Linux or macOS:

```text
python3 -B "<skill-directory>/scripts/list-work.py" "<filter>" [limit] [scope]
```

Report the rows as printed, newest first. Keep out-of-scope and text-only matches as counts unless the
caller selected `all`. Blank state means the plan has no explicit checkbox or completion state.
