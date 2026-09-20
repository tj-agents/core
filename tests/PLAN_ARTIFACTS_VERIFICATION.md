# Plan-artifacts P1 verification

Candidate: Codex package 1.2.0; Claude retains commit-based refresh. Source baseline
`c3572f85163f581a645c0f43d67df6b3563ffa82`; implementation is on `Feature/PlanArtifacts`.
This is verification evidence, not a second migration plan. The workspace-level
`AGENT_ECOSYSTEM_MIGRATION_PLAN.md` remains the progress owner.

## Observed results (2026-09-19, Windows)

- Generator and `-Check`: 183 current files, 55 skills, distinct Claude and Codex trees.
- `python -B -m unittest discover -s tests -p test_plan_artifacts.py -v`: four passing tests covering
  both packaged roots, resource closure, identical canonical bodies, startup/resume/compact/clear
  fixtures, an unrelated directory with spaces, actual Git Bash command execution, no adapter file
  mutations, absent/malformed/invalid-UTF-8 contract diagnostics, and digest-marked fallback generation.
- `tests/skill-packaging.tests.ps1` and `tests/handoff-launchers.tests.ps1`: pass.
- Initial PR CI exposed a test assertion comparing a Windows short temp-path alias with the helper's
  resolved long path. The assertion now resolves the expected path; the focused suite passes locally.
  Exact-head CI verifies the runner-specific case. No helper behavior or test was disabled.
- Claude Code 2.1.278 ordinary plugin validation: pass with the existing missing-version warning.
  Strict validation: exit 1 for that warning, also observed on the unmodified baseline. A disposable
  control copy with only `version: 1.2.0` added passes strict validation. The shipped Claude manifest
  deliberately stays versionless under the existing refresh policy; no release-policy migration occurred.
- Codex CLI 0.155.1 native local-marketplace registration and installation into a fresh disposable
  CODEX_HOME: pass; native installer reports base@base-agents 1.2.0, enabled. No other plugin was installed.
- Claude loaded the copied base package with `--plugin-dir` and an isolated CLAUDE_CONFIG_DIR. Its
  actual SessionStart hook event reports exit 0, success, and the canonical contract in additionalContext.
- The user explicitly approved sending generated base context and synthetic prompts to OpenAI and
  Anthropic after the automatic approval reviewer blocked the initial networked retry. Authorized
  probes used disposable profiles, temporary private authentication copies, and only the base plugin.
- Codex native context delivery is observed in a developer message containing the contract and source
  SHA-256, before the model reads any skill. Hooks ran with the CLI's invocation-only trust override
  for the reviewed local package. Persisted trust was not established and no instruction fallback was
  installed. Normal-profile enablement/trust and desktop behavior remain separate adoption checks.
- The initial Codex fixture could not write: a fresh Windows profile defaulted to read-only, the Store
  PowerShell executable failed in the restricted-token sandbox, and the temporary directory was
  inaccessible to that token. The successful fixture uses a standalone directory under the workspace
  parent, `windows.sandbox = "unelevated"`, one writable workspace, and a process PATH excluding
  WindowsApps so the system PowerShell is selected. Sandbox restrictions remained enabled throughout;
  normal settings, shell profiles, and Windows security configuration were not changed.
- The generic skill-creator validator rejects the repository's established top-level `kind` and `domain`
  metadata. The repository generator accepts and validates this metadata; the upstream validator was not
  changed and its result is not reported as a pass.

## Observed behavioral probes

Claude Code 2.1.278 (default Sonnet 5) and Codex CLI 0.155.1 (default GPT-6 Astra) were invoked with
synthetic household book-tracker requests, without model overrides. The standalone working directories
had spaces in their paths, no Git repository, and no roadmap/provider. Only the existing-owner case
supplied local AGENTS.md/CLAUDE.md and ROADMAP NOTES.md. File contents and final responses were inspected,
not merely hook output or expected-word matching.

| Case | Claude | Codex | Evidence inspected |
|---|---|---|---|
| New plan | Pass | Pass | Useful Markdown plan, sequence and acceptance checks; absolute link resolves |
| Correction | Pass | Pass | Same canonical file; JSON replaces CSV; duplicate ISBNs reject before saving; matching criteria |
| Resume | Pass | Pass | Sample review recorded accurately; implementation/tests still pending; next action and remaining work |
| Planning-only | Pass | Pass | No application implementation, install, publication, or invented test result |
| Quick task | Pass | Pass | Response is 42; working directory stays empty |
| Spaces | Pass | Pass | Actual paths and response links resolve in directories containing spaces |
| Existing owner | Pass | Pass | ROADMAP NOTES.md updated with keyboard navigation/check; local instructions unchanged |

Both hosts also passed fresh-session recovery from the saved artifact. Each host retained one canonical
plan, recorded the reported sample review without inventing executed tests, and preserved the existing
owner case's local instruction content unchanged. Quick-task directories remained empty.

Claude's initial probes revealed two link failures. Its first fresh-session response omitted its link,
and its first existing-owner response used a relative link. This observed failure led to a narrow
contract clarification: every create/revise/resume response, including a fresh-session
summary, must provide an absolute clickable path. Both failed cases were rerun with the regenerated
contract and passed; every Claude plan-response link was checked against the actual existing file.
The Codex successful fixture started with that clarified contract.

Final contract SHA-256 (UTF-8 with LF normalization):
`646b2d968a0462efbff14970e2779880c2e0a8e58eb1d682a9bb4f1b9de99fd7`.

## Default execution and continuity probes

The user subsequently required default workflow selection for long-term work and continuous ownership
through delivery and automated context transfer. The common contract and `plan-execution` trigger now
state that behavior explicitly. Agent-authored phase limits cannot override the user's request. The
execution skill also supports standalone work without inventing an engineering runtime or extra ledger.

The synthetic task asks for three consistent lending-club documents without naming a skill. An existing
GOAL.md contains an agent-authored phase-1 stopping point explicitly identified as not a user restriction.
Both hosts completed all three deliverables; both planning-only controls created only a plan.

Codex's first continuity run loaded plan-artifacts and plan-execution, repaired the stale scope, updated
GOAL.md, and linked it in the final response. A fresh Codex rerun with the final contract also
loaded the execution skill before editing and completed the same ownership checks. Claude's first run completed the documents but left GOAL.md
stale; its fixture also lacked the native Skill tool. A second run exposed Skill and kept GOAL.md current,
but still did not load the workflow. A third fresh run with the final trigger and explicit skill-loading
instruction again skipped the workflow and left GOAL.md stale, despite a successful hook event carrying
the exact current contract. These Claude outcomes are failures of automatic workflow ownership, not passes.

That P1 instruction layer was not a deterministic enforcement mechanism. P2 now supplies a packaged
UserPromptSubmit router from canonical .agents/hooks/workflow_route.py. It selects the full
engineering:plan-execution body for active-goal or explicit multi-phase execution prompts and stays silent
for planning-only and quick tasks. Focused source and relocated-package tests cover positive selection,
negative applicability, completed goals, event filtering, source digest/body identity, and missing-contract
failure.

On 2026-09-20 Claude Code 2.1.278 reported the successful UserPromptSubmit event carrying the complete
canonical contract on event line 6, before the first write on line 26, then completed all three documents and
reconciled GOAL.md. Codex CLI 0.155.1 completed the same full-goal fixture. Because Codex's JSON stream does
not expose successful hook stdout, one isolated transparent wrapper recorded the installed plugin hook's
input and forwarded output unchanged: event UserPromptSubmit, exit 0, empty stderr, selected-workflow
header, full body, and source digest 778a85477e65fe9a84b6416f35d61a7b2847f3705fa696600e77babdc11866ed.
The wrapper was removed immediately; the restored installed router SHA-256 matched generated output
e7fcde742cb7ae9d1f60d2993a666ff0251192f96f76a6b5bda3499635ba9927.

This closes automatic workflow routing and canonical progress ownership for the two CLI hosts. Persisted
Codex hook trust, desktop behavior, and Linux behavior remain later adoption checks.

Live unqualified handoff acceptance also passes on both CLI hosts. The packaged Codex and Claude launchers
each started exactly one successor in `base-agents/.worktrees/Test-P2-Handoff-Acceptance`, an in-repository
worktree at implementation commit `5c5e07874b4bfee41ce1238743edbcde98f2c261`. Each successor read the
same two-line pointer, created `ACK.md`, reconciled `GOAL.md` to `Status: complete`, and changed no tracked
repository files. Codex ran as CLI 0.155.1 with Astra/high and invocation-only hook-trust bypass; Claude ran
as Code 2.1.278 with its configured default and without permission bypass.

All probes terminated and their temporary authentication copies were removed. Their synthetic
plan files and private session evidence remain available for review; none of those raw profiles/logs
are part of this commit. The original P1 artifact cases passed locally; P2 still owns independent review and delivery.

Native Claude startup and resume hook events both report success. Native Codex context injection is
observed as described above. Adapter fixtures cover startup/resume/compact/clear; no actual forced
compaction, Linux run, desktop integration, or persistent trust adoption is claimed. The generated
fallback's body and source digest were tested, but no user instruction file was modified to activate it.

The strict Claude missing-version warning remains the documented baseline exception. It was not hidden
by changing the existing refresh/release policy. P2 review and delivery, P3-P7, publication, and
normal-profile adoption remain delivery slices of the same authorized goal.

## Reproduction and interface sources

Run from the implementation checkout:

```text
pwsh -NoProfile -File .agents/sync-generated.ps1 -Check
python -B -m unittest discover -s tests -p test_plan_artifacts.py -v
pwsh -NoProfile -File tests/skill-packaging.tests.ps1
pwsh -NoProfile -File tests/handoff-launchers.tests.ps1
claude plugin validate --strict ./plugins/base
```

The last command has the baseline warning described above. Source packaging and resource validation
must pass independently of host/model availability. Do not change the release policy solely to hide it.

[OpenAI plugin hooks](https://developers.openai.com/plugins/build/plugins) documents the compatibility
CLAUDE_PLUGIN_ROOT variable and explicit legacy manifest hook paths.
[Claude hooks](https://code.claude.com/docs/en/hooks) documents SessionStart additionalContext and
shell execution. Installed CLI help was checked for profile, local-plugin, and hook-trust options.

[OpenAI Windows sandbox documentation](https://developers.openai.com/docs/windows/windows-sandbox)
explains the native elevated and restricted-token fallback modes. The disposable fixture's mode and
PATH adjustment above are verification-environment choices, not changes to plugin behavior.
