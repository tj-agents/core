# Prepared work-repository plugin migrations

All 16 migrations are prepared in isolated sparse worktrees. Canonical adoption and drift checks pass.
Claude and Codex settings agree with each selection, use portable sources, and enable Claude marketplace auto-update.
Existing distinct Claude instructions are preserved in sibling AGENTS.md files; CLAUDE.md becomes the shared-source pointer.

Tommy explicitly approved committing and publishing this exact set on 2026-10-20 ("yep lets go"). All 16 migrations are committed. Twelve draft PRs were confirmed by the publication batch; reverse-proxy PR #83 was subsequently confirmed after the create request timed out. Auth-config and infra-shiboleth-idp are archived and rejected pushes. Preaward-app has an intact migration commit but a local branch-name case mismatch; its publication reconciliation was interrupted when local tools stopped returning output. Reconcile GitHub before retrying publication.


| Repository | Existing stacks | Instruction pairs repaired | Prepared worktree |
|---|---|---:|---|
| infra-shiboleth-idp | shared/work profile | 0 | `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Migrate-Work-infra-shiboleth-idp` |
| standards-docs | shared/work profile | 0 | `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Migrate-Work-standards-docs` |
| zanzibar-poc | dotnet | 0 | `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Migrate-Work-zanzibar-poc` |

Original consumer checkouts and their local settings are untouched. After publisher/consumer merges and native acceptance, remove superseded local declarations and audit actual callers before removing user marketplaces. Tommy merges; this session has no merge authority.


Claude isolated acceptance: the initial authenticated headless session did not install declared plugins. Native marketplace and project-scope plugin installation then succeeded in disposable profile `ca-tq7_1ujl`. A second fresh session was started after removing its native-created user declaration keys, but its result is unconfirmed because local tools stopped returning output. Credential use was explicitly approved; the token is held only in memory and the test scans its disposable profile for exact token bytes before reporting. Do not claim this acceptance passed until `claude-installed-acceptance.json.tmp` and native inventory are inspected. Interactive acceptance could not start because the execution environment rejected its PTY.

An independent session owns later core changes on this delivery branch. Its HEAD advanced from reviewed `19bb7b20a4027791f836a0d94f40a37d6d1ac70c` to `e90aa2af8f50e0e25dee82fb78ec81efd987be49`, with additional uncommitted edits including the refresh-cli retirement. Do not stage, overwrite or revert those changes. Consumer acceptance and review tooling use the immutable runtime exported from `19bb7b20` at `C:/Users/TommySeery/AppData/Local/Temp/ra-1z3e80xo`.
