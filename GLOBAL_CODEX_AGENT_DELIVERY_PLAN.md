# Deliver shared Codex agents once per profile

## Goal and authorization

Replace base-agents' stale per-repository Codex role provisioning with one supported profile-level
installation, while retaining Claude's plugin-native agent delivery. Tommy explicitly authorized the
durable cross-PC marketplace/installer repair, validation, delivery, local migration, and cleanup of
base-agents-owned repository copies. Do not remove unrelated user-defined agents or ask Tommy to copy
configuration between repositories manually.

This is a delivery-path correction, not a new lane implementation. The canonical role bodies, model
mapping, and host adapters already belong to base-agents and must remain authored once.

## Evidence and diagnosis

- `sandbox-hwid/.codex/agents/` contains ten untracked role files dated 2026-09-19. Their `workflow_*`
  names and bodies are stale relative to the installed base-agents release.
- `engineering@base-agents` already packages the canonical Codex TOML roles under `codex-agents/` and
  the canonical Claude roles under `agents/`.
- Claude loads the plugin `agents/` payload directly and no repository-local `.claude/agents` directory
  exists in `sandbox-hwid`.
- The authored Codex installer currently requires `-ProjectRoot` and copies generated roles into every
  `<repo>/.codex/agents`. The Workflow v2 support matrix and host manifest encode that project-scoped
  delivery as mandatory.
- The official OpenAI Codex subagent documentation now defines `~/.codex/agents/` for personal agents
  shared across repositories and `.codex/agents/` for project-scoped agents. Tommy's lane and workflow
  roles are personal cross-repository standards, so profile scope is the correct supported boundary.
- `C:\Users\tommy\.codex\agents` currently has no installed base-agents roles. Removing the project
  copies before the profile cut-over would temporarily remove those roles from Codex.
- The current workspace proves that the repository-local files are active: its advertised role names
  match the stale local `workflow_*` files rather than the current packaged role names.

Official reference: https://learn.chatgpt.com/docs/agent-configuration/subagents

## Required outcome

1. Inspect current `origin/main` installation, generated-source, package, capability-catalog, host
   acceptance, and uninstall/upgrade conventions before editing. Preserve `.agents/` as the canonical
   source and `plugins/*` as generated output.
2. Change Codex delivery so the canonical packaged roles install once into the resolved Codex profile's
   `agents/` directory (normally `~/.codex/agents`, with an explicit supported alternate profile path).
   Preview, apply, verify, upgrade, and uninstall/cleanup behavior must be deterministic and must preserve
   unrelated personal agents.
3. Remove the blanket base-agents requirement for generated `<repo>/.codex/agents`. Retain project-scoped
   custom agents as a supported Codex feature only when a project intentionally owns distinct roles; do
   not use that scope for Tommy's shared lane/workflow roster.
4. Keep Claude on plugin-native `agents/` delivery. Do not generate or install `.claude/agents` copies.
   Add regression coverage proving the two hosts deliberately use different delivery mechanisms while
   sharing canonical role bodies and semantic workflow contracts.
5. Provide a safe migration for known former base-agents-managed project files, including the stale
   `workflow-*.toml` names, without deleting unrelated repository agents. The migration must install and
   verify profile roles before removing managed project copies.
6. Update the support matrix, host delivery manifest, installer documentation, catalog/digests, generated
   packages, and focused tests. Run the full required validation and independent immutable review.
   The repair must also fix the machine-package closure exposed during this transfer: both the generated
   and installed 2.0.1 `handoff-codex` launcher omit the shared `agent-cli.ps1` dependency that the
   launcher resolves at runtime. Add packaging coverage that executes or resolves every launcher's shipped
   dependency from the generated package layout, not only the authored source tree.
7. Commit, push, open/update the PR, monitor CI, merge, refresh/install the delivered release on this PC,
   and verify a fresh Codex session in an arbitrary repository advertises the canonical roles without a
   local `.codex/agents` directory.
8. After that proof, remove only the ten stale base-agents-owned files from
   `C:\Users\tommy\source\repos\sandbox-hwid\.codex\agents`, remove the directory if empty, and record the
   migration in `sandbox-hwid/docs/next-session.md`. Then automatically hand ownership back to
   `sandbox-hwid` so its authorized canonical C++ structure refactor can continue.

## Acceptance criteria

- Canonical role definitions remain single-source in base-agents.
- Codex loads the shared roles from the user profile across repositories; consuming repositories no
  longer receive base-agents lane copies.
- Claude continues loading the corresponding plugin agents without repository-local copies.
- Install, verify, upgrade, cleanup, generation, and host-acceptance tests guard the cut-over.
- The release is merged and installed locally before stale project copies are removed.
- A fresh arbitrary-repository Codex session proves the roles remain available after cleanup.
- No unrelated agent definitions or dirty files in any checkout are changed.

## Progress

- 2026-09-21: Confirmed the repository-local lane/workflow files are untracked and redundant with the
  base-agents ownership model, but currently provide this session's Codex role discovery.
- 2026-09-21: Confirmed the installed engineering 2.0.1 package contains canonical Codex and Claude role
  payloads; only Codex is routed through the project-scoped installer.
- 2026-09-21: Confirmed official Codex documentation supports profile-scoped personal agents under
  `~/.codex/agents/`.
- 2026-09-21: Created this isolated worktree and branch `Fix/Global-Codex-Agent-Delivery` from current
  `origin/main` at `b62a8ed` without touching the dirty base-agents main checkout.
- 2026-09-21: The first installed 2.0.1 handoff submission failed before launching a successor because
  `.agents/machine/utility/scripts/agent-cli.ps1` was absent from both the installed and generated machine
  package. The authored worktree contains that dependency. No duplicate successor was started; this owner
  retained control and added the package-closure defect to the same authorized repair.
- 2026-09-21: Replaced the repository-scoped Codex installer contract with deterministic profile preview,
  apply, verify, uninstall, and ordered project migration. The installer resolves `-CodexHome`, then
  `CODEX_HOME`, then `~/.codex`, verifies profile hashes before cleanup, and preserves unrelated profile and
  project agents.
- 2026-09-21: Updated the host runtime and support matrix so Codex probes profile roles plus intentional
  project roles while Claude continues loading its plugin `agents/` payload. Added focused regressions for
  the host divergence, profile discovery from an arbitrary repository, stale-name migration, reparse safety,
  drift repair, cleanup, and generated launcher dependency closure.
- 2026-09-21: Confirmed current `origin/main` and the installed 2.1.0 package already contain the shared
  `agent-cli.ps1` resource; strengthened the generated-layout test so every shipped consumer is discovered
  and resolved. The package-closure defect recorded against installed 2.0.1 is therefore repaired in the
  current release baseline and guarded by this candidate.
- 2026-09-21: Full local validation is green: generated output is current, 42 general Python tests pass,
  547 hook/workflow tests pass with 8 platform skips, and the CLI recovery, skill packaging, and generated
  launcher PowerShell suites pass.
- 2026-09-21: Reconciled first with `origin/main` at `c67cef3` / release 2.1.1, including its portable
  package-digest implementation. Before review, `origin/main` published the UTF-8 bootstrap repair as
  release 2.1.2. Reconciled that baseline too and advanced this changed package set to immutable release
  2.1.3. The 44-test general suite, delivery-focused workflow tests, catalog/generation gates, CLI recovery,
  packaging, and launcher suites pass; the immediately prior combined candidate also passed all 547
  hook/workflow tests with 8 platform skips.
- 2026-09-21: Cancelled the first immutable review pass after its workflow lens proved the review helper's
  `path_digest` did not hash the emitted NUL-delimited path manifest as the lifecycle contract requires. The
  same pass identified installer ownership, legacy CLI, and ancestor-reparse gaps. Corrected the helper and
  added literal manifest-digest coverage; replaced filename-only ownership with a profile ownership manifest
  plus shipped historical project-content digests; retained deprecated `-ProjectRoot` as a safe migration
  alias; and made every existing ancestor component reparse-protected. Focused workflow-helper and six
  installer safety regressions pass. A new full review must be frozen only after full validation and commit.
- 2026-09-21: The replacement full review at `00db7c7` retained one medium installer-recovery finding: an
  interrupted apply could copy roles before durable ownership was recorded. Added a pre-mutation pending
  ownership journal, same-directory staged replacement, exact-digest recovery, and a regression covering
  recovery, later upgrade, and uninstall. All 19 workflow-generation tests and package gates pass. The clean
  incremental pass now approves the fixing head `ce94efa` with every finding resolved.
- 2026-09-21: PR #20's first exact-head CI run passed generation, catalog, committed-package, recovery,
  packaging, launcher, and general source tests, then failed one Windows-only installer-test assertion. The
  assertion coupled ordering evidence to an exact rendered temporary path even though the operations ran.
  Replace it with semantic `ADD`-before-`REMOVE` action ordering, review and push that fix, then return the
  same PR to exact-head CI.
- 2026-09-21: the next exact-head run proved that the same Windows short-path alias can also affect the
  environment-derived preview assertion. The installer again completed; replace the remaining absolute
  path-string assertion with a semantic `ADD` suffix check, rerun the focused receipts, and review the fix.

## Next Steps

Once the remaining CI portability fix receives its incremental watermark, push it to PR #20 and deliver the approved
2.1.3 candidate through CI/merge. Refresh the installed release, install and
verify the profile roles, prove an arbitrary repository advertises them without local copies, then migrate
only the ten known base-agents files from `sandbox-hwid`, record the migration there, and automatically hand
ownership back to its authorized refactor.
