# Repo-declared agent configuration — progress

- Plan: `plans/repo-declared-config/REPO_DECLARED_CONFIG_PLAN.md`
- Roadmap: `plans/repo-declared-config/REPO_DECLARED_CONFIG_ROADMAP.md`
- Roadmap item: `repo-declared-config/migrate-agent-state`
- Worktree: `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-RepoDeclaredPluginIsolation`
- Branch: `Fix/RepoDeclaredPluginIsolation`
- Base: `a0fe999b3f2efc7380b87b1b6e9e25fbbd554f54` (fetched `origin/main`)
- PR: not opened for this continuation
- Dependency/package gates: real consumer acceptance before deleting machine state
- Last reconciled: 2026-09-29; two implementation candidates checkpointed for Sol continuation
- Transfer selection: `machine:handoff-codex`, lane L3 (`gpt-6-sol`, high); lower-cost ownership of the
  remaining migration and review judgments under Tommy's explicit model preference

## Authorization and ownership

Tommy resumed the whole migration on September 29 and requested lower-cost execution. Core retains
this goal; specified implementation is delegated to Sol. Existing authorization covers implementation,
validation, PRs and normal merge paths across the authorized consumers. The original session requires
domain-selected capabilities to bring in core transitively, with no manually maintained machine plugin
configuration. The September 27 manifest/config work on main is reusable infrastructure; its explicit
core selections do not by themselves prove this session's transitive or fresh-start acceptance.

Both bounded implementation workers have released their leases. The current parent is preparing one
full-goal continuation on Sol in this exact core worktree; successful launcher submission releases the
parent's writing ownership. The successor must acknowledge ownership here before edits. Do not launch
a second owner because acknowledgement is slow. This transfer carries both candidates and the whole
migration, rather than stopping the task at its local checkpoints.

The separate model-control/harness-injection and missed-handoff investigation was launched on Sol in
`Docs/ModelSwitchHandoffInvestigation`. It owns only
`core/.worktrees/Docs-ModelSwitchHandoffInvestigation/plans/harness-model-control/INVESTIGATION.md`.
It does not replace or block this migration. Existing `Fix/CodexStandardsSync` (PR #60) and Claude
startup work keep their own scopes. Do not modify their worktrees or duplicate those implementations.

## Current state

PR #48 merged the core-owned harness manifests, owner-only catalog, host-config generator and first
machine verifier. PR #59 supplied live Codex hook snapshots; PR #64 records Claude launcher acceptance.
The latest local immutable core release tag is v2.1.15; current source describes the 2.1.16 candidate.
Do not claim source/package installation proves repository adoption or release publication.

The earlier independent audit remains on `Feature/Repo-Declared-Config` at `9f16181`; it was not shipped.
It supplies useful strict parsing, nested Codex profile and repository override coverage missing from
main's `verify_machine.py`. Preserve those behaviors by improving the existing verifier when that slice
is reached, rather than adding a second checker. The old worktree has no active writer.

No normal profiles or consumer configuration have been changed by this continuation. User-scope plugin
settings and agent copies remain until replacement acceptance. Other machines have not been reverified.
The older checkout under `C:\Users\tommy` and its dirty legacy `base-agents` checkout must not be retired
until their work is preserved. Product-specific global environment text also remains a cleanup item.

## Active delivery map

1. **Concertable hook scope:** branch `Fix/PluginScopeIsolation`, worktree
   `C:\Users\TommySeery\source\repos\Concertable\agents\.worktrees\Fix-PluginScopeIsolation`, base
   `eae6cc643c2b902b91b1321e12cd84b79c69784d`. Local checkpoint
   `3bcb5273bd97b18deaa4d0b23bd1fa264c866d79` contains the shared selector, packaged dispatcher, both host
   manifests, direct startup/delivery guards and tests. Its worker lease is released.
   The unrelated Concertable `Fix/StandardsCurrencyAutoRefresh` checkout is untouched.
   Root cause, mechanism and the measured split assessment are in the plan's immediate scope-isolation
   section. The commit has 22 total files, 440 additions and 176 deletions; about 363 changed lines belong
   to 12 authored code/test/manifest files. Generated mirrors and the owning debt entry make up the rest.
2. **Core role delivery:** read-only evidence/proof in this core worktree. Verify supported generic native
   subagent dispatch with packaged role instructions before implementing an adapter or deleting agents.
   The earlier isolated Codex exec proof worked without profile/repository agent files; this is role
   transport evidence only. Preserve source ownership in core; do not add a consumer provisioning script.
3. **Machine verifier:** strengthen the existing packaged verifier in this core worktree while native
   role acceptance is gated. The plan's machine-verifier continuation defines strict parsing, named
   profiles, redacted structured findings and explicit repository override checks. This remains a
   read-only diagnostic; it grants no cleanup acceptance and introduces no second audit entry point.
   The Sol implementation and parent-requested corrections are complete and its lease is released.
   The candidate preserves the old API, reports unreadable/malformed inputs without values, retains
   named-profile setting paths and distinguishes local Git origins from remote package subpaths.
   Approximately 450 substantive code/test lines across two files, plus usage docs and generated data,
   remain one diagnostic concern below the normal split threshold. Core's generated hook-command changes
   were separately checked to contain only updated package digests.
4. **Consumer declarations and cleanup:** follow after the selected delivery mechanism is tested and
   released. C++ consumers share the `ThomasSeery/cpp` Git repository. Domain standards source is at
   `C:\Users\TommySeery\source\repos\cpp-agents` (remote `tj-agents/cpp`), not an absent tj-agents/cpp path.
   Concertable's registry owns its 13 consumers; `Concertable/concertable` was absent locally on the last
   inventory. Keep all listed consumer adoption and other-machine verification outstanding.

## Host evidence and design boundaries

Codex 0.157 proved per-run model/effort/developer-role instructions work without copied role files, but
repository plugin enablement alone left a fixture uninstalled and its skill unavailable after native
thread startup. Claude dependency installation wrote the dependency into project settings; removing it
left dependency-unsatisfied. Detailed evidence remains at the old audit worktree's
`plans/repo-declared-config/HOST_EVIDENCE.md`; do not repeat those failed native-only assumptions.

The installed native CLI is now 0.158.0. Its plugin-add help still has no project-scope install option.
Its built-in `default` and `explorer` roles need no external role file, but native spawning inherits the
parent's sandbox and exposes no per-child sandbox override. The current support matrix promises enforced
read-only readers; prompt-delivered role text in a workspace-write parent does not satisfy that promise.
The earlier per-run `codex exec --sandbox read-only` proof remains the applicable transport evidence.
Extend the existing core HostRuntime contract rather than declaring prompt-only delivery equivalent.
Native registration of named roles is not an added requirement; actual role behavior and scoped loading
are. Initial cold-start materialization, hook trust and native session acceptance must be reported
separately from generated configuration or fixture success.

The new isolated 0.158 native-child probe did not launch. Automatic approval review rejected copying the
existing Codex login into a temporary profile, citing sensitive-data exposure. The fixture value was
synthetic; no credential was to be returned. The auth copy and trace are confirmed absent. Evidence is in
`C:\Users\TOMMYS~1\AppData\Local\Temp\codex-native-role-bccb980456804523ae71bee74ab319ac\evidence.txt`.
An explicit approval question is pending; do not retry that action without its answer. Concertable scope
isolation and source-level adapter work remain independent of this probe gate.

## Verification and reviews

Concertable: 7 scope tests, 22 rule tests, 11 instruction tests, 16 manifest integration tests and all
3 Codex tests passed. Every one of its 16 Claude and 7 Codex handlers uses the dispatcher. The full
shared suite ran 810 tests with 2 failures and 9 skips. Both failures reproduced on a frozen archive of
the unchanged base: the capability-selection preview fixture compares Windows short and long paths,
and its repository-validation fixture resolves a PowerShell shim that cannot start `dotnet`.
`TECH_DEBT.md` in that candidate owns the exact failures and resolution condition. Do not rerun the
whole Windows suite without a new reason or weaken those assertions; exact-head Linux PR CI must pass.
Generated check reports 265 current files, diff whitespace checks pass, and all AGENTS/CLAUDE pairs match.

Core: the final verifier suite ran 12 tests successfully with one Windows directory-link privilege skip;
the mocked reparse-point test passed. Harness-manifest, catalog-digest and generated-output drift checks
passed after the final fix. The package sync check also passed during implementation. No normal-profile
audit, cleanup, independent candidate review, PR CI or native consumer acceptance has been completed by
this continuation. The older audit's 200-test result does not validate this candidate.

Both candidates still need final-review synchronization, frozen independent review, PRs and their normal
delivery gates. No completed review watermark exists. The account previously rejected Spark, so use the
declared Sol review fallback without repeating that known failed model launch. GitHub ruleset discovery
for Concertable/agents returned the account-tier HTTP 403; use its available normal GitHub merge path
after review and CI, never an admin bypass. No existing open PR owns either candidate branch.

## Next Steps

Scope: continue the whole migration on Sol, beginning with review and delivery of the two implementation
checkpoints. Current slices are Concertable hook isolation and core machine verification; the separate
native-role approval gate does not block their review, source corrections or publication.
Remaining scope: transitive declarations, shared duplicate retirement, generator adoption, self-heal,
strict verifier coverage, plugin-write guards, profile cleanup and all consumer/machine acceptance.
Done when: declared domain capabilities load their required shared core behavior in both hosts, unrelated
repositories receive no Concertable behavior, normal profiles contain no own behavioral configuration,
and the plan's live-session and migration acceptance checks pass.

1. Acknowledge sole ownership of this plan and both listed delivery worktrees. The predecessor and its
   implementation workers have released writing after the one successful launcher submission. The
   `Docs/ModelSwitchHandoffInvestigation` session remains a different owner of its narrow investigation.
2. Resolve each candidate's local HEAD and clean source state. Core's substantive checkpoint includes
   this ledger; Concertable's exact head is recorded above. Load the review lifecycle at its current
   stage, synchronize each candidate with its actual base once immediately before final review, and
   freeze its descriptor. Revalidate only changed scope after any relevant base movement or repair.
   Use fresh read-only Sol review contexts, including the path-selected workflow lens, and validate
   their Workflow-v2 evidence. Do not treat implementation-worker output as independent approval.
3. Open one PR per repository through plain Git/gh, monitor exact-head CI, resolve candidate-caused
   failures, and deliver under the already-authorized normal merge path. Current primary checkouts
   contain unrelated work: core's primary is stale/dirty and Concertable's primary is on
   `Fix/StandardsCurrencyAutoRefresh` ahead of main. Preserve those checkouts and other worktrees.
   Honor real cleanup/ownership gates and keep delivery state truthful; no force removal or admin merge.
4. Continue core's packaged role transport, transitive domain declarations, duplicate retirement and
   consumer adoption under this same plan. The built-in-child probe is unaccepted and its temporary
   login-copy approval remains unanswered in the predecessor conversation; do not interpret elapsed
   time or this handoff as permission to retry. Source-level adapter work and noncredential fixtures
   can continue. Retain the full cold-start, self-heal and per-machine acceptance requirements.

Do not stop at a local commit, this safety fix, an open PR or a fresh context. No user-scope settings or
agent files may be deleted before their replacement acceptance passes. Complete only at the original
outcome; otherwise keep the precise external gate and remaining authorized work with this owner.
