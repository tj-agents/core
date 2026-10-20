# Repository-declared plugin configuration progress

Status: core and sandbox PRs are green, independently reviewed and ready for Tommy. Remaining rollout is blocked by the explicit authorization and external conditions below.
Owner: current Codex session.
Branch: Feature/RepoDeclaredPlugins
Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-RepoDeclaredPlugins
Base: 85e3a0d35d07c2f2e1fee780be421aa80cd3e75d (includes Tommy-merged #320)
Head: 19bb7b20a4027791f836a0d94f40a37d6d1ac70c
Core PR: tj-agents/core#321 (ready for review, all required checks green at final head)
Sandbox PR: tomjseery/sandbox-dotnet#2 (055b118706c0aaeff1d91355fce50a4b2aeeba43; green, independently reviewed and ready)
Merge authority: Tommy only. This session has merged nothing. The handoff overrides the repository's
standing auto-merge policy for this goal; no delivery binding or merge watcher is armed.

Assessment complete: reuse native project settings and the existing plugin-selection generator and updater.
Template, Concertable's migrated consumer mains, winwrap and sandbox-hwid already use the unified marketplace.
No new skill, hook or installer. One-time automatic update setup remains in setup.ps1.

Delivered core behavior: native handoff/open/recovery without rolling refresh or trust/config convergence;
SessionStart receipt and late cancellation retained; packaged refresh-cli entry point with native fast default
and optional full verification; scheduled updater reads native effective configuration for exact saved trusted
projects, bootstraps marketplace snapshots and follows external publisher revisions. Native Codex installation
writes derived user enabled entries automatically; repository selection is authored, trust and caches are native.

Verification:
- Focused Windows startup, agent-cli, handoff-Claude/Codex, open-Claude and recovery suites passed.
- Final remediation: updater 24 tests and refresh 11 tests pass; regenerated package freshness passes.
- Exact prior head c09822e0: complete Windows and Linux CI passed, run 39345573105.
- Final head 19bb7b20: both platform jobs and ci-required in run 39397986405 passed.
  Initial native review's three medium findings are fixed
  with regression coverage: cached-catalog selection omission, retired publisher blocking metadata repair,
  and effective Claude local scope. Independent full and incremental workflow lenses returned no findings.
  Native incremental review returned no findings; canonical review is approved at full final head, with
  host-coverage validation and Git-private proof recorded. Delivery preflight is green at that exact head.
- Fresh real Windows Codex 0.163.0-alpha.1 profile at AppData/Local/Temp/pa-4b11ksfg: initial user config
  contained exact project trust only, and the project declared the published unified marketplace and base.
  Updater installed it. After removing the native-created user enabled entry, a fresh app-server loaded all
  five base skills from project declarations. Real verify-only inventory/revision/package-byte checks passed.
  Final code read native effective config, updated, then reported current on a second pass.
- Real Windows Claude 2.1.282 handoff returned verified SessionStart receipt at
  C:/Users/TommySeery/AppData/Local/Temp/tj-agents-handoff-cg3y2ah2/status.json. This uses normal auth and
  existing user declarations; it does not establish isolated profile acceptance. The same exact closed test
  session was resumed through agent_recovery (native history written) and open-claude. All three temporary
  tabs were closed through verified peer-cli identities; session 2c19642d-794e-44d2-a243-77573de3a7de.
- Real Windows Codex handoff correctly failed its SessionStart ACK deadline. Native hooks/list reports
  base/machine SessionStart trustStatus=modified. No trust bypass or silent trust rewrite was performed.
  Receipt: C:/Users/TommySeery/AppData/Local/Temp/tj-agents-handoff-2y1kits6/status.json.

Consumer migration: sandbox-dotnet has portable generated selection plus both native settings. Sixteen
Infonetica consumers are prepared in isolated sparse worktrees; all adoption/check operations and host
selection agreement checks pass, and distinct existing Claude instructions are preserved in sibling AGENTS.
See [WORK_CONSUMER_MIGRATIONS.md](WORK_CONSUMER_MIGRATIONS.md) for exact scope and paths. No work commits,
pushes or PRs were made. Original consumer checkouts and the original core checkout are preserved.

External conditions and exact resume actions:
- Work publication: automatic approval review rejected bulk work commits because the Infonetica commit
  gate requires explicit go-ahead for the concrete set. Tommy authorizes commit/push/PR for the 16 prepared
  migrations; then commit each reviewed scope, perform independent review, push and open dependent PRs.
- Infonetica publisher: tj-agents/infonetica#8 supplies native Codex metadata absent from current main.
  Retried run 37936207023 fails before starting due failed GitHub payments/spending limit. Publisher/account
  owner resolves billing and Tommy merges when ready; no billing change or merge was attempted here.
- Isolated Claude acceptance: automatic review rejected reading the OAuth access token into an isolated
  child's environment without explicit credential-use authority. No token was read/copied. Tommy can
  authorize memory-only use for this bounded test, or provide an already authenticated isolated profile.
- Native Codex handoff: native approval of the changed installed hook definitions is required before
  expecting SessionStart ACK. Fresh skill loading and source tests do not establish hook acceptance.
- Linux native acceptance: requires installed native hosts and fresh trusted repository-only sessions,
  plus real handoff/open/recovery. Linux source CI is separate evidence.
- Fallback cleanup: stale actual local callers still reference legacy registries. Keep user wiring until
  consumer merges, actual caller reconciliation and native acceptance; preserve unrelated settings/caches.

Final review: canonical Git-private work order at
C:/Users/TommySeery/source/repos/tj-agents/core/.git/agent-workflow/reviews/a6eed2852352e5f3becc57dd003a1fac80d5b30f2442d6c23c618c16a695088e/work-order.md
is approved with watermark 19bb7b20a4027791f836a0d94f40a37d6d1ac70c. Review host coverage and
private proof pass; disposable bundles are removed. PR body validation and delivery preflight pass.
Instruction file checks pass both directions (core three pairs; sandbox one pair). No authored code is
uncommitted or unpushed; generated output is excluded from the PR.

Next action requires Tommy's bounded approval: (1) commit, push and open PRs for the sixteen prepared
work migrations in WORK_CONSUMER_MIGRATIONS.md; (2) read the existing Claude OAuth token only into memory
and pass it to the isolated acceptance child, with no credential logging or file copy. Automatic approval
review rejected both proposed actions for missing explicit work-commit/credential-use authority.
After approval, continue those two workstreams and their independent review/CI; publisher availability,
native Codex hook consent, actual local-caller reconciliation and Linux native acceptance remain as above.
Keep both ready PRs open for Tommy to merge. No automatic merge binding is armed.
