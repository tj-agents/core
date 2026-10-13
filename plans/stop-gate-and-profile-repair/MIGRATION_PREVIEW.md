# Scoped preference migration preview

The handoff excludes edits to employer repositories. Completing the user C++ naming migration
requires preserving the existing project opt-outs in the following local settings files.

For each file, keep the existing values and add these equivalent keys under `enabledPlugins`:
`cpp@tj-agents: false`, `msvc@tj-agents: false`, `win32@tj-agents: false`.
No code, tracked settings, permissions or other preferences change.

Files:
