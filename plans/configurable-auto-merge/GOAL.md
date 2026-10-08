# Configurable auto-merge

## Authorization

Tommy, 2026-10-08: design and implement a repository-declared, opt-in auto-merge setting for tj-agents/core; test, commit, push, and open a pull request. Merge only when the setting and existing delivery authority permit it.

## Outcome

Repositories can explicitly enable or disable agent-initiated auto-merge. When omitted, no auto-merge action occurs. When enabled, the delivery workflow may arm auto-merge only after its existing exact-head checks, independent review, and readiness decision pass; the necessary host permission is derived from that declaration. The setting must never grant merging by default or bypass existing stop classes and scoped authorization.

## Source context

- Existing merge authorization resolves to absent unless the user, a goal, or a scoped approval records it.
- PR #153 exposed that an explicit user approval cannot reach a disconnected live Codex session reliably.
- `harness_permissions_sync.py` already composes host permission grants from trusted installed marketplaces.

## Decisions

- This is a new feature slice, isolated at `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Feature-ConfigurableAutoMerge` on `Feature/ConfigurableAutoMerge`, based on `origin/main` `9561267`.
- The configuration’s exact schema and owner path remain to be designed, but it must be repository-declared, explicit, and default inert.
- The successor owns this workstream only. It must not modify PR #153 or the `Fix/HandoffRequestPhrasing` worktree.

## Completion

- A documented explicit enable/disable configuration is validated on both supported hosts.
- Omission has a regression test proving that it does not permit or arm auto-merge.
- Enabled behavior has coverage proving that it honors the existing readiness, review, authorization, and stop gates.
- Authored source, tests, and any required manifest/harness declarations are committed; a PR is open with validation evidence.

## Next Steps

Lane: L3 — the repository configuration boundary and host permission integration are unresolved but bounded.

1. Inspect the current merge authorization, delivery binding, harness permission sync, and repository configuration conventions; propose the smallest explicit schema and enforcement point.
2. Implement the approved-in-goal design with focused regressions for enable, disable, omission, and preserved merge gates.
3. Run affected and repository-required checks; commit, push, open a draft PR, and record the PR and evidence here.
