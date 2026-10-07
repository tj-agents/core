# Repository-owned plans, worktrees and TJ Agents adoption

Status: approved outcome, execution in progress, 2026-10-07. Codex pickup verified; allocator design under review. Producer and consumer acceptance remain.

## Authorization and ownership

Tommy approved the proposal on 2026-10-07: "yep ... other repos should read the core conventions and create
worktrees using the worktree script we have in core ... go ahead with this".
Authority covers completing this goal: design, implementation, tests, focused PRs and normal delivery,
Claude/Codex handoffs, project adoption and retirement of verified obsolete copies. Preserve work-repository
authority rules and real security/validation holds. Do not invent a new confirmation at a phase boundary.
The prior planning-only hold is lifted. The completed router fix is https://github.com/tj-agents/core/pull/126.

This proposal owns the new layout decisions. Existing machine/consumer adoption and old-checkout retirement
remain owned by plans/repo-declared-config/REPO_DECLARED_CONFIG_PLAN.md and its progress ledger.
After feedback, reconcile those owners and add only the genuinely new execution items; do not create a
second adoption ledger. Existing unfinished goals remain unfinished until their actual acceptance passes.

## Recommendation

Core owns the shared behavior and tools. Each project owns its plans and declares its selected capabilities.
Use the existing tj-agents/marketplace discovery catalog for the unified identity; source packages remain
owned by tj-agents/core and the individual stack/product repositories. Do not copy the core source tree
into every project.

Apply repository-owned plans and internal worktrees to all projects, including personal and work repos.
Preserve each work repository's existing commit, publishing and merge authority rules.

Recommended layout:

    source/repos/tj-agents/core/
        plans/repository-layout/REPOSITORY_LAYOUT_PROPOSAL.md
        .worktrees/<flattened-branch>/
        .agents/
        .claude/
        .codex/

    source/repos/<any-project>/
        plans/<goal>/<owned-artifact>.md
        .worktrees/<flattened-branch>/
        .agents/capabilities.lock.json
        .agents/catalog/catalog.json

Existing declared project plan conventions such as docs/plans remain valid; plans is the default when
none exists. During delivery, the active branch's checkout owns the current plan. Other Git checkouts
can contain their branch's normal copy, but must not become competing writers or authoritative ledgers.

## What is already true, and what is incomplete

- The GitHub source is already tj-agents/core. This session was started in an old base-agents worktree.
- README and release records deliberately retain base-agents as an installed marketplace identity.
  The foundation package is named base; that package boundary is separate from the old repository name.
- tj-agents/marketplace already exposes base, engineering, machine and the stack packages under the
  tj-agents marketplace. Its README requires explicit selection and disabling the old plugin before
  enabling its replacement, to avoid duplicate hooks.
- Core's open-worktree convention already calculates <common-repository-root>/.worktrees/<branch>.
  It also recognizes legacy sibling <repo>.worktrees directories. The main gap is inconsistent creation,
  existing locations and adoption, rather than an absent internal-worktree rule.
- Maintained-plan policy permits project plans; workboard still enumerates ~/.claude/plans separately.
  No inspected contract makes that external directory mandatory for project execution goals.
- The old checkout is not a disposable empty duplicate: it has other worktrees and unrelated local work.
  The canonical core checkout also has active work and both internal and sibling worktrees.
- The installed finisher passed its cleanup preflight but failed its five-second startup acknowledgement.
  It reported that nothing was closed. A late reaper was stopped when this new planning request arrived.
  PR #126 is merged; removal of its old checkout has not been observed.

## Approved decisions

1. Repository goals live in their owning repository, using its existing plan convention or plans/<goal>.
   Host scratch drafts may exist as ephemeral host state, but they cannot become the maintained execution
   source of truth. Promote an existing external project goal once, preserve its decisions/evidence,
   update all handoff/continuation references, and retire the former owner after verifying recovery.
   Truly non-repository tasks keep a goal in their own task directory.
2. Worktree creation always uses the common Git repository root, including when invoked from a linked
   checkout. Never allocate below the current linked worktree or create a new sibling <repo>.worktrees.
   Keep .worktrees ignored by Git. Retain legacy discovery while existing worktrees are migrated.
3. Prefer tj-agents/marketplace for discovery and new host installation. Keep base, engineering and
   machine as meaningful package names. Migrate installed base-agents identities explicitly, rather
   than inventing a second new marketplace called core.
4. Projects commit their capability lock, selected owners' release records and generated host settings.
   Bootstrap resolves and verifies the required core closure explicitly. Adding a marketplace alone
   does not prove package installation, dependency inheritance or active hooks in either host.
5. Retire only old checkouts proven redundant or deliberately superseded. Distinct projects survive.
   Reconcile dirty work, local-only commits, branch/worktree registrations, active sessions and references
   before moving or deleting a checkout. After migration is authorized, routine verified cleanup proceeds
   automatically; do not add another blanket confirmation step.

## Source ownership

- .agents/base/policy/plan-artifacts: common repository-goal storage and recovery contract.
- .agents/engineering/convention/plans and workflow/plan-authoring: selected engineering lifecycle.
- .agents/engineering/operation/open-worktree: allocation and reuse contract.
- .agents/engineering/utility/workboard: plan discovery, including legacy external goals.
- .agents/machine/utility/handoff-claude and handoff-codex: native launch adapters and exact target checks.
- .agents/machine/utility/peer-cli/scripts/finish.ps1 and finish_reaper.ps1: acknowledged closeout.
- .agents/machine/utility/bootstrap-capabilities: project declaration, dependency closure and adoption.
- .agents/plugins/manifests and sources.json: authored package/harness ownership.
- tj-agents/marketplace: aggregate discovery identities and package mapping.
- tj-agents/kit: new repository scaffolding, so fresh repos begin with the same defaults.

Shared instructions remain authored once under .agents. Host adapters contain host differences only.
Generated plugins output remains outside authored PRs.

## Delivery and handoff sequence

Claude policy and Codex execution-owner handoffs are being prepared in the isolated checkouts below.
Every executor gets the owned artifact, exact source/checkout, authority, acceptance and dependencies.
Independent contexts may prepare disjoint work in parallel; dependent delivery remains sequential.

| Slice | Proposed owner | Deliverable and gate |
| --- | --- | --- |
| A: shared contract | Claude, core | Confirm storage/defaults and migration interfaces; update shared plan/allocation contracts and affected discovery guidance. Test project goals, existing conventions, active-branch ownership and standalone tasks. |
| B: allocation and closeout | Codex, core | Reuse and unify current allocation paths; audit launchers and side-worktree creation. Repair late-reaper/startup failure behavior without a dangling cleanup process. Verify Windows native hosts, exact target ownership, delayed acknowledgement, shared claims and failures. |
| C: marketplace adoption | Claude, marketplace plus kit in separate PRs | Reuse the tj-agents aggregate; reconcile it with core's exact release/catalog ownership and bootstrap. Make new scaffolds declare core closure; test clean installs and transition from legacy identities with no duplicate hooks. |
| D: project and machine convergence | Codex migration owner; Claude acceptance owner | Extend the existing repo-declared-config workstream. Inventory every project and known machine; migrate plans, worktrees and declarations in small batches, validating both hosts before retiring old state. |

A establishes interfaces before B. C can inspect its independent repository during B, but consumer rollout
requires the exact released producer artifacts from B and C. D follows their successful native acceptance.
Use one writer per artifact/checkout; separate hosts do not justify competing ledgers.

For each slice: select the applicable lane, keep the change reviewable, run focused regression checks,
review the exact candidate and deliver through that repository's own CI/merge rules. Source generation
alone does not establish installed-host adoption.

## Migration details that must be resolved before execution readiness

- Enumerate exact goal owners and external-plan references before moving any goal. Rebind continuation
  and handoff state through supported APIs; verify a fresh host resumes the same goal and next action.
- Enumerate every worktree creation caller. Fix bypasses rather than introducing a second allocator.
  Move registered worktrees through Git's supported operation where possible; never use raw folder
  moves with stale Git metadata. Quiesce the affected session, preserve dirty work, update references,
  and prove launch/cleanup from the new location before retiring the old location.
- Keep project plan ownership relative to the active Git branch. Commit recovery artifacts before a
  fresh execution handoff when they must be visible in that checkout; do not rely on a machine-local copy.
- Resolve aggregate-marketplace identity versus immutable release IDs, digests and project locks.
  The current aggregate advertises main while core project adoption pins releases; adding the aggregate
  must not silently convert an existing project to a moving release or activate duplicate packages.
- Inventory legacy source clones separately from installed host caches. Native plugin management owns
  cache transitions. Preserve immutable releases and historical compatibility records that consumers need.
- Preserve supported runtime state, transcripts and credentials outside Git. Moving plans into projects
  does not mean moving session secrets or machine receipts into tracked project files.
- Define resumable per-project migration receipts and rollback. A failed cutover leaves its former
  working owner intact and reports the specific failed acceptance; it cannot mark the fleet complete.

These are design work for the approved execution plan. This draft specifies outcomes and proposed
boundaries, not final implementation snippets or an execution-ready mechanism.

## Acceptance

- Every in-scope project uses a repository-owned maintained goal, with no active external duplicate.
- All new worktrees are allocated under their common repository's .worktrees, from either host and
  whether launch begins in the primary or a linked checkout.
- Existing misplaced worktrees and obsolete flat clones are migrated or have a concrete outstanding owner;
  an exception is never silently counted as convergence.
- Clean and existing consumers explicitly receive the required core packages through the chosen catalog,
  with exact source ownership/release verification and no duplicated skills or hooks.
- Claude and Codex fresh-session tests prove plan pickup, worktree launch and routine merged cleanup.
- Old checkouts are retired only after preserved work and migrated references are verified.
- The existing adoption goal stays open until all selected projects/machines pass, and core's source
  changes are not reported as the whole migration.
- Routine authorized delivery and proof-verified cleanup finish automatically. A concrete validation or
  authority gate is reported accurately, without an invented human continuation question.

## Current evidence and review state

Inspected shared plan, authoring, checkpoint and worktree contracts; read canonical core instructions,
README, current plan inventory, repo-declared configuration plan/progress and worktree registrations.
Read the existing aggregate marketplace and kit READMEs. Read-only evidence explorers confirmed source
ownership, explicit package closure, allocation defaults, host launch constraints and affected test areas.
The approved outcome is authorized. Concrete helper design is the successor's first phase; implementation readiness must be established before code writes.

## Execution ownership and evidence

- Full-goal successor: native Codex in Feature/RepositoryOwnedLayout.
- Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-RepositoryOwnedLayout
- Fresh base: origin/main 61d4920477a313528f855babd2e4ee4ccdf3d8f6, fetched 2026-10-07.
- Launch lane: L1 because the first phase resolves the remaining helper/packaging mechanisms.
  Re-select and apply L4 for implementation; delivery does not raise a lane.
- Claude side slice: Docs/RepoOwnedPlanConventions in core/.worktrees/Docs-RepoOwnedPlanConventions.
  Its only goal is plans/repository-layout/PLAN_POLICY.md in that checkout. It owns common plan policy,
  planning discovery guidance and associated focused regression/docs evidence; it cannot rewrite this goal.
- Parent handoff is a continuation of approved design into execution, not a claim that every mechanism
  already has a reviewed implementation design. The Codex successor owns the design and full outcome,
  and applies critical readiness before its own substantial-design implementation transfer when needed.
- Pickup evidence: .agents/continuation/layout-pickup.json in this checkout, written by the successor,
  with harness, session identity, branch, head, first_action and timestamp. Never infer pickup from launch.
- Codex session `01a11794-26f3-7fb2-accb-0df87faa5180` acknowledged pickup at head
  `a2a15a5ea3f3b9bf36b51d6d6c3a34106372068a`. Its receipt is the path above.
- Continuation owner `323cc6bbb879a40c0682dbf1` is initialized in `.agents/continuation/owner.json`.
  The foreground lease binds verified Codex PID 46660. Windows task
  `AgentStandards-Continuation-a156e0a2dcaa8334638e3580ba591621403fba42def006d35051c62f1d8fa943`
  is registered at a 20-minute interval. An observed wake retained the foreground owner and launched
  no child. Heartbeat during foreground work; checkpoint and yield before a scheduled takeover.
- Do not retire this active goal checkout at the first PR merge; carry the same logical goal through
  successor slices and preserve recovery artifacts before worktree cleanup.

## Confirmed helper gap and existing work ownership

The current shell/worktrees.ps1 is an existing-worktree picker, not a creator. Core's open-worktree
currently creates through inline Git commands and names a repository-vendored scripts/worktrees.ps1.
PR https://github.com/tj-agents/core/pull/101 owns that audit helper on Fix/FreshWorktreeAudit at
core/.worktrees/Fix-FreshWorktreeAudit (head 2fd7eade30273d5efa6f11e7b424871083e12cc3).
It implements audit only; it does not create, close or retire and is not plugin-shipped.
Do not recreate its audit repairs or overwrite its active owner. Resolve its actual session/PR ownership
and use its authoritative review for corrections to that slice.

The user's consumption contract is explicit: consumer repos read installed core conventions and invoke
one shipped core worktree helper, without vendoring a new copy or requiring a manually located core clone.
The helper must create beneath the common Git repository root from either a primary or linked checkout,
fetch the actual base, validate branch/path identity and preserve refusal/ownership checks.
Use Git's supported worktree operations. Packaging, dependencies and harness declarations ship atomically.
Do not add an allocator to each launcher independently or teach consumers inline creation as the normal path.
Settle the exact CLI/module owner from current source and the audit PR before implementation, write concrete
examples in this goal, and obtain design review. No additional user decision is needed for routine mechanisms.

## Native launch repair evidence

The first Codex launch definitively failed before its terminal invocation: automatic hook trust rejected
engineering@base-agents because installed package_files included three generated workflows/__pycache__/*.pyc
files absent from committed source. Exact comparison at source revision 61d4920477a313528f855babd2e4ee4ccdf3d8f6
found no missing or changed authored files. Base and machine packages also matched. The predecessor removed
only those three proved derived files after validating every absolute target stayed inside its exact cache.
No hook check, permission setting or source verification was bypassed. A retry of this definite pre-launch
failure is safe; no Codex successor existed from that attempt.
Resolve the standards-source defect as a focused slice: normal runtime imports must not poison an installed
package's integrity on the next native handoff. Preserve the strict authored-byte comparison; do not simply
ignore arbitrary executable extra files. Tests must exercise runtime import followed by native trust proof.
This source repair belongs to the full-goal owner, separate from Claude's plan-policy paths.

## Allocator mechanism and first delivery boundary

The first producer slice adds creation to the installed `engineering:open-worktree` capability.
There is no existing creator to extract: `shell/worktrees.ps1` selects existing trees, while PR #101's
`scripts/worktrees.ps1` implements audit only. Preserve #101's audit ownership and tests. Its observed
head is `2fd7eade30273d5efa6f11e7b424871083e12cc3`, base `Feature/SecretRefreshGrant`, state open,
verify failed and guard cancelled. Its diagnostics are not a delivered allocator dependency.

Author the helper at `.agents/engineering/operation/open-worktree/scripts/worktrees.py`.
Python 3.9+ and Git are its only external prerequisites. Existing skill-resource generation ships the
same source beside both host entries and in the package's canonical skill directory; consumers call
their installed skill path. No consumer script, machine-local resolver, core checkout, shell profile,
cross-plugin import or host-specific allocator is required.

The interface is synchronous, emits one JSON result on stdout, sends failures to stderr and returns
nonzero on refusal. A successful result includes `repository`, `worktree`, `branch`, `head`,
`base_ref`, `base_head` and `created`. The helper never launches or closes a host, removes a worktree,
resets a branch, stages files, commits, or chooses a delivery slice. Callers retain task/session ownership.

Paths and refs are strings, SHAs are full hexadecimal commit IDs, and `created` is boolean. It means
this call created the worktree, so every successful `create` returns `true`, including restoration.
`base_ref` and `base_head` always name the verified source ref and commit used for this checkout;
neither is nullable. New creation uses the fetched remote base, local restoration uses its local
branch ref, and remote-only restoration uses its fetched remote branch ref. `head` equals `base_head`.

```json
{"repository":"C:/repos/example","worktree":"C:/repos/example/.worktrees/Feature-Example","branch":"Feature/Example","head":"1111111111111111111111111111111111111111","base_ref":"refs/remotes/origin/main","base_head":"1111111111111111111111111111111111111111","created":true}
{"repository":"C:/repos/example","worktree":"C:/repos/example/.worktrees/Fix-Existing","branch":"Fix/Existing","head":"2222222222222222222222222222222222222222","base_ref":"refs/heads/Fix/Existing","base_head":"2222222222222222222222222222222222222222","created":true}
{"repository":"C:/repos/example","worktree":"C:/repos/example/.worktrees/Fix-Existing","branch":"Fix/Existing","head":"3333333333333333333333333333333333333333","base_ref":"refs/remotes/origin/Fix/Existing","base_head":"3333333333333333333333333333333333333333","created":true}
```

```powershell
python -B '<installed-open-worktree-directory>/scripts/worktrees.py' create --repository . --branch Feature/Example
python -B '<installed-open-worktree-directory>/scripts/worktrees.py' create --repository . --branch Feature/Child --base Feature/Parent --expected-base <full-fetched-parent-sha>
python -B '<installed-open-worktree-directory>/scripts/worktrees.py' create --repository . --branch Fix/Existing --existing --expected-head <full-branch-sha>
```

`--remote` defaults to `origin`. A new branch uses the remote's advertised default branch unless
`--base` supplies its exact branch name. Bases are always fetched remote branches; a local-only stack
parent must be published through its already-authorized owning workflow first. `--expected-base`
binds a reviewed parent and fails on disagreement. `--existing` explicitly attaches an unregistered
local branch, or creates its matching local tracking branch from the remote; `--expected-head` is
mandatory and must match. Refuse an already registered branch and report its exact checkout for the
caller to reconcile ownership. Ordinary task resumption reads that checkout without allocating another.
Reject `--existing` combined with `--base` or `--expected-base`, and reject `--expected-head` without
`--existing`. Ref names and configured remote names are validated before constructing refspecs.

Resolve paths from Git, independent of the caller's linked checkout:

```python
common = Path(git(caller, 'rev-parse', '--path-format=absolute', '--git-common-dir')).resolve()
repository = common.parent
caller_root = Path(git(caller, 'rev-parse', '--show-toplevel')).resolve()
caller_git = Path(git(caller, 'rev-parse', '--absolute-git-dir')).resolve()
if caller_git == common:
    if caller_root != repository or not (caller_root / '.git').is_dir():
        raise Refusal('Separately relocated primary Git directories are unsupported')
elif caller_git.parent != common / 'worktrees':
    raise Refusal('The caller is not a conventional linked worktree')
elif Path((caller_git / 'gitdir').read_text().strip()).resolve() != caller_root / '.git':
    raise Refusal('Linked worktree registration does not match the caller')
if common.name != '.git' or git(repository, 'rev-parse', '--is-bare-repository') != 'false':
    raise Refusal('An ordinary non-bare repository with its common .git directory is required')
if Path(git(repository, 'rev-parse', '--path-format=absolute', '--git-common-dir')).resolve() != common:
    raise Refusal('Common repository identity does not match')
if git(repository, 'rev-parse', '--is-inside-work-tree') != 'true':
    raise Refusal('The common directory parent is not the primary worktree')
if Path(git(repository, 'rev-parse', '--show-toplevel')).resolve() != repository:
    raise Refusal('Separately relocated Git directories are unsupported')
target = repository / '.worktrees' / branch.replace('/', '-')
```

The caller identity check must precede probing the common directory's parent: Git can infer that
parent as a worktree even when a relocated primary lives elsewhere. Require the caller's resolved
top-level path and Git directory to agree with its worktree registration. For a linked caller, verify
both directions of its `.git` pointer and administrative `gitdir` file. Git does not retain enough
metadata to distinguish every separately relocated primary through a linked caller; that layout is
outside this helper's supported contract, and these checks do not claim universal detection of it.

Every Git subprocess receives an environment with inherited repository selectors removed: `GIT_DIR`,
`GIT_WORK_TREE`, `GIT_COMMON_DIR`, `GIT_INDEX_FILE`, `GIT_OBJECT_DIRECTORY`,
`GIT_ALTERNATE_OBJECT_DIRECTORIES`, `GIT_CEILING_DIRECTORIES`, and `GIT_DISCOVERY_ACROSS_FILESYSTEM`.
This follows the existing `worktree_cleanup_gate.py` boundary. Preserve normal authentication settings.

Reject invalid Git branch names, non-capitalized type prefixes, option-like arguments, case variants
of any existing local/remote branch, and existing target paths, including empty directories. Inspect
all registered worktrees before creating anything; branch and path comparisons use case-folded normalized
absolute identities on Windows. Refuse a registered target even if its directory is missing. Reject
`.worktrees` symlinks/junctions/reparse points and require the resolved target parent to remain beneath
the common root. Bare or separately relocated Git-directory layouts are explicit unsupported cases.

Read the selected remote's branch advertisement with `ls-remote --symref <remote> HEAD refs/heads/*`.
Use its symbolic HEAD branch when no base was supplied; an explicit base selects that exact advertised
head. Include the advertised branch names in collision checks, even if the clone's configured fetch
mapping excludes them. Fetch the selected base explicitly and compare its commit with the advertisement:

```python
source_ref = 'refs/heads/' + selected_branch
base_ref = 'refs/remotes/' + remote + '/' + selected_branch
git(repository, 'fetch', '--prune', remote, '+' + source_ref + ':' + base_ref)
base_head = git(repository, 'rev-parse', '--verify', base_ref + '^{commit}')
if base_head != advertised_heads[source_ref]:
    raise Refusal('The selected remote branch changed; inspect and retry')
```

This overrides a narrowed configured fetch mapping for the selected source. Never silently fall back
to local main or the caller's branch after network/base failure. Pin add to the verified full SHA:

```python
git(repository, 'worktree', 'add', '--no-track', '-b', branch, str(target), base_head)
```

For an existing local branch use `worktree add <target> <branch>` after its expected-head check.
Refresh the selected remote with `fetch --prune` first, but derive its result exclusively from the local
ref and required expected HEAD. For remote-only restoration use the explicit fetch mechanism above
with the restored branch as `selected_branch`, verify expected HEAD, create from that SHA, then set
the matching remote tracking ref. Re-read all selected local refs inside the allocation lock before add.
Use argument arrays and bounded subprocess timeouts, never a shell-built command. Serialize creation
per common repository using an exclusive `.git/agent-worktree-allocation.lock`; its JSON records the
PID, branch and target. Release only the lock this invocation acquired. An existing lock refuses and
requires ownership reconciliation; no age-based stealing. Git's own branch/path refusal still applies.

Ensure `/.worktrees/` is ignored via common `.git/info/exclude` without touching tracked `.gitignore`.
Preserve existing exclude content and verify Git ignores the target before adding it. Refuse if any
tracked path lives beneath `.worktrees`, or if a negating rule prevents ignore. After Git succeeds,
verify its registration, branch, HEAD, common directory and clean status. On any failure preserve
partial Git/path evidence and report it; do not roll back by force-deleting a branch or directory.

Expected slice: helper plus focused tests, packaging test and engineering harness declaration,
approximately 500–800 substantive lines in five files. No launcher, audit, reaper, migration or
marketplace changes belong in this PR. The parent owns design and the goal; one L4 worker owns these
specified implementation paths. The helper's new invocation permissions are declared in the engineering
harness using the existing `${PLUGIN_ROOT}` patterns, constrained to `python -B <helper> create`.
No new hook or plugin dependency is introduced. Generated output is refreshed only for validation.

Its follow-on guidance slice replaces open-worktree's inline allocation examples with this shipped
interface after producer delivery, updates the wrapper references as needed, and preserves legacy audit
discovery. It uses its own Docs branch; Claude's plan-policy paths remain disjoint. Until both producer
and guidance land, consumer rollout remains pending. The integrity repair, cleanup reliability,
aggregate/kit and adoption remain subsequent independently measured slices of this same goal.

Verification: temporary bare remote plus ordinary clone, invocation from primary and linked checkout,
non-main remote default, fetched base advancing beyond stale local main, exact stack-parent mismatch,
local/remote restoration with expected SHA, registered branch refusal, flattened/case path collisions,
dirty caller preservation, tracked or negated `.worktrees` exclusion, symlink/junction escape, fetch
failure, narrowed fetch mappings with a stale explicit base, separately relocated `.git` directories,
hostile inherited Git selectors, stale allocation lock and partial-add failure preservation. Execute both generated host-local
copies outside the author checkout against fixture consumers. Check harness manifests, package generation
and the normal source suite. Native Claude/Codex adoption remains a later explicit acceptance gate.

Implementation-path standards read: root AGENTS.md, README.md, SOURCE_LAYOUT.md, PACKAGING.md,
`engineering:git-branching`, `engineering:open-worktree`, `engineering:plans` and `engineering:lanes`.
The router found no local route table for the helper/test/manifest paths; no stack tier applies.
Existing Python unittest and package-resource patterns in `tests/test_source_layout.py` govern tests.

## Execution readiness

Allocator verdict: full and delta design reviews completed; the caller-identity correction awaits its
focused recheck. A real-Git fixture passes for primary and linked checkouts and refuses a relocated primary.
The examples and refusal behavior above resolve
the first producer slice; they do not declare the remaining fleet migration mechanism ready.
Execution authorization: implementation and normal goal delivery, as recorded under Authorization.
Transfer: not required for this bounded helper refinement. This session is already the full-goal
successor; retain it and dispatch one specified L4 implementation worker after design review.
Native and independent read-only review covered the frozen design at `fe7ddc8`; native delta review
covered `0df530e`. Retained corrections define output semantics, explicit refspec freshness and
caller-root verification. The delta review's missing-adoption-checkpoint claim was rejected: the committed
ledger already contains its self-contained Next Steps. Review work orders remain local; this goal records
the durable outcome. Next action: recheck the caller-identity correction, then dispatch the producer
implementation at L4. Broader acceptance remains unchanged.

## Next Steps

Scope: whole goal through all remaining slices and terminal delivery.
Current slice: finish the shared helper design and begin the core producer changes; Claude owns the
independent plan-policy slice.
Remaining scope: producer delivery, cleanup reliability, marketplace/kit adoption, every project and known
machine migration, both-host acceptance, and verified retirement of obsolete flat checkouts.
Done when: every acceptance criterion above passes and all resulting authorized PRs/adoption/cleanup gates
are terminal; source-only changes or one merged PR do not complete this goal.

1. Read the goal and exact Git checkout, then record pickup in .agents/continuation/layout-pickup.json,
   including the first observed action and current branch/head. Use your distinct session identity.
   Load plan-execution and the current canonical lanes; keep one full-goal owner.
2. Read Claude's PLAN_POLICY.md from its exact checkout; it is an independent bounded writer. Establish
   its launch/pickup evidence without creating another policy agent. Preserve its ownership and receive
   its reviewed PR into the normal sequential delivery map. You are not alone in this codebase:
   never revert others' edits and adapt your implementation around their disjoint ownership.
3. Reconcile the existing repo-declared-config plan/progress with its actual active owner and branch,
   and read PR #101's worktree/authoritative review state. Audit allocation callers and packaging.
   Resolve the shipped helper interface/examples and reviewable slices in this same goal. The parent
   read current core README/AGENTS, canonical plan/branching/handoff contracts and marketplace/kit READMEs.
4. Apply readiness/design review, route specified implementation to L4 workers or supported host controls,
   implement and test the shared script and adapters, and deliver focused PRs through required review/CI.
   Keep common durable guidance on the Claude Docs branch or a separate guidance slice.
5. Continue cleanup-reliability and marketplace/kit work in their own reviewable slices. Use actual Claude
   handoffs for aggregate/scaffold work and Claude host acceptance, not only Codex subagents. Do not
   launch speculative duplicate successors or overlap writers.
6. Extend the existing adoption owner for project/machine batches and goal/reference migrations. Before
   deletion, preserve dirty work, local-only history and active sessions and prove replacement ownership.
   The old base-agents primary has unrelated shell/cr.ps1 work and other registered worktrees; it is not
   disposable. Keep distinct project repositories. Update this same goal at material transitions.
7. Persist and monitor any exact-head delayed CI through the supported continuation runtime. On true gates,
   keep independent authorized work moving and record owner/unblock action/resume evidence. Routine
   commit, push, PR creation, merge and verified cleanup use the authorization above without re-asking.

The originating session stops all owned-path writes before launching this successor. It remains a
read-only pickup observer and does not perform cleanup or migration after launch. Do not close the
originating session or its old worktree while it is still reporting pickup; release/cleanup belongs to
a later verified transition. No former planning-only or feedback-pending sentence grants a live hold.
