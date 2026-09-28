# Tier declarations

Every standards plugin ships a `tier.json` at its payload root. `base`, `engineering`, and
`machine` apply to every project. A stack plugin declares `stack-present` and the markers that
identify its stack. The base package's `hooks/tier_gate.py` reads installed declarations at
SessionStart and blocks use of a stack skill when its stack is absent.

The declaration format is defined by [tier.schema.json](../schemas/tier.schema.json). `detect.files` names
repository-relative paths, `detect.globs` matches filenames at any depth, and `detect.content`
matches a pattern inside files selected by a glob. Any match makes the stack present. Use a
marker intrinsic to the stack, such as a project file. `owner_repository` allows a standards
authoring repository to use its own skills without ordinary project markers.

The gate gets plugin and marketplace identity from the installed path. It exposes
`AGENTS_TIER_OVERRIDE=<tier>[,<tier>]` for a single session when detection is wrong. Correct a
bad declaration in its owning stack repository. Host skill listings can still show blocked
skills; the PreToolUse gate prevents their application.
