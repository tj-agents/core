# Persistent work-item session registry

## Objective

Replace the current ad hoc worktree/progress-dump recovery practice with one Core-owned convention that records the active native Claude and Codex sessions for each work item. Every repository that injects the Core plans convention must receive the same guidance and templates. A user must be able to say "continue work item X" and recover the literal recorded native session through its correct `open-claude` or `open-codex` command, even after its worktree was safely removed following pushed delivery.

## User-authorized outcome

The durable plan layout is:

```text
plans/
  features/
    <feature>/
      README.md
      work-items/
        <work-item>/
          README.md
          ACTIVE_SESSIONS.md
```

`README.md` at feature level explains the feature and lists its work items. The work-item `README.md` owns purpose, scope, current delivery status, PRs, durable decisions, evidence and completion. `ACTIVE_SESSIONS.md` is the only short-lived live-session registry. It contains one row for every active or resumable native session; one work item usually has one row but may have several bounded, non-overlapping owners.

Use the term **session handle** for the durable host-qualified identifier, for example `claude:<native-session-id>` or `codex:<native-session-id>`. Do not call an opaque identifier a hash unless the host actually supplies a cryptographic hash. Each row must record the host, session handle, visible CLI/tab title when available, role, state, absolute worktree, branch, PR, exact HEAD, last verified timestamp, predecessor/successor relationship where relevant, and the exact safe resume command. The resume command must select the recorded host/session and not merely open a new generic CLI. Remove the row when that session's work is terminal; retain delivery/history in the work-item README.

The existing "progress dump" is retired completely after its responsibilities have been migrated and every consumer/reader is updated. Its exact canonical paths, readers and generated/package representations are not yet confirmed: discover them from source and record the migration map before deleting anything. Do not delete a similarly named plan, goal, session runtime artifact or user-authored progress evidence merely because it resembles the old dump.

## Why this work exists

Core currently has many registered worktrees and partial local CLI liveness data, but no authoritative relation between a work item, the exact native agent/session that owns it, its PR/head, and safe cleanup. Once a session disappears, a worktree may remain solely because nobody can determine its owner or whether its work was pushed. Existing `.agents/continuation` owner/receipt files are runtime coordination state, not a durable cross-repository inventory. They can be stale or inaccessible and must not become the new registry.

The immediate evidence was a controller-association session on `Fix/ControllerGoalAssociation`: the source Stop repair was committed but the installed cache was stale, the historic transfer receipt named an absent successor while still reporting active, and the owner lock was stale. These facts must be carried as a problem example, not copied into the general convention as the normal workflow.

## Scope and boundaries

- Core owns the portable convention, templates, skill/workflow changes, generated host adoption, validation and release.
- The convention applies to Core and every repository that injects the Core marketplace/plan convention. Design consumer adoption so it is explicit, versioned and migratable; do not silently rewrite unrelated repositories or their plans.
- Separate durable guidance from product/runtime changes. Follow `engineering:git-branching`: global always-loaded guidance must land as its own focused docs/convention slice; templates, generators, runtime discovery and migration tooling belong in later focused slices if needed.
- Read `engineering:skill-authoring` before adding, splitting, renaming or retiring skills. The likely need is a plan/work-item convention, not a new skill by default; prove a new skill is necessary before creating one.
- Read existing plan-artifact, plans, plan-authoring, plan-checkpoint, handoff, open-claude, open-codex, recover-agents and peer-cli contracts before design. Reuse their host-native session recovery behavior; do not invent a new agent database if a durable Markdown registry plus existing recovery commands is enough.
- All shipped behavior must work on Windows and Linux. Do not patch installed plugin caches, disable hooks, add arbitrary local profile state, or commit generated `plugins/*` or catalog output.
- Do not modify the live controller-association PR #209 or its checkout. This work has its own branch, goal and review.

## Required design decisions

1. Define the canonical path grammar and determine whether `features/` is required for every plan or is the new preferred structure with a documented legacy bridge.
2. Define the complete `ACTIVE_SESSIONS.md` schema and lifecycle, including multiple concurrent bounded agents, handoffs, resume, stale/unknown sessions, finished/deleted worktrees, and when entries are removed versus retained in README history.
3. Specify how host-qualified handles and exact resume commands are produced and validated using existing `open-claude`, `open-codex`, `recover-agents` and `peer-cli` capabilities. A resume command must not produce a duplicate writer.
4. Identify every existing progress-dump source, reader, template, test, hook, generated artifact and consumer convention. Produce an explicit migration/deletion map before removal.
5. Define consumer rollout: which Core package/template changes propagate automatically, what repositories must opt in or migrate, what compatibility period (if any) is justified, and how adoption is verified without an unsafe sweeping edit.
6. Decide whether Termboard consumes this Markdown convention as its durable source of truth, mirrors it, or supersedes it. Preserve a simple non-Termboard workflow; Termboard is not a prerequisite for the convention.

## Acceptance criteria

- A fresh Core plan can create one feature, one work item, a work-item README and `ACTIVE_SESSIONS.md` using the documented convention.
- A work item can record one Claude and one Codex session with exact host-qualified handles and resume commands; a bounded multi-agent work item remains unambiguous.
- A closed session is removed from `ACTIVE_SESSIONS.md`; its worktree may be safely deleted once Git/PR evidence is durable, while the work-item README preserves its delivery outcome.
- A stale or unknown session is reported as stale/unknown and does not authorize deletion, reopening or a second writer by inference.
- Existing handoff/recovery/peer tooling has a documented path from an entry to the correct host command, with tests where Core owns the behavior.
- The exact legacy progress dump and all of its readers are migrated or removed with no dangling source/generated references.
- Core’s generated host/package adoption is updated from canonical source and all affected Windows/Linux tests, source-layout checks and package-generation gates pass.
- The rollout is split into reviewable PR-sized slices, with independent review and normal delivery for each. Consumer migration is tracked rather than claimed complete before evidence exists.

## Authorized delivery

Tommy explicitly authorized this Core-wide convention and migration on 2026-10-12, including normal implementation, testing, review, PRs and merge after repository gates pass. This does not authorize destructive cleanup of existing worktrees, deleting user data, profile installation, bypassing hooks/checks, or bulk edits to consumer repositories without the reviewed migration plan and their normal ownership gates.

## Handoff lane

Lane: L3. This is an open cross-repository convention and migration design with unresolved ownership, compatibility and recovery choices. Tommy explicitly selected Claude for this non-frontier handoff.

## Investigation evidence (2026-10-12)

### The progress dump is the `<NAME>_PROGRESS.md` ledger

Identified from the user's own words, not by name resemblance:

- Originating Codex session `codex:01a12aa7-5b58-7312-9400-ef710762147f` (Fix-ControllerGoalAssociation), lines 7203–7230: the work-item/`ACTIVE_SESSIONS.md` proposal, then "that way we can finally delete the progress dump also, that can FULLY GET REMOVED NOW".
- Claude session `claude:a2bcd5c4-bf6d-4087-95e3-d7ba7f711875` (Concertable pipeline, 2026-09-23): "for now we just have the plan and progress dump" and "workboard ... should be used to make plans easier to track and eventually remove the progress dump".
- `~/.claude/plans/agent-workboard/PLAN_TRACKING_AND_THE_PROGRESS_DUMP.md` records the diagnosis: state is inferred from prose, progress accretes, and nothing distinguishes plan classes. Resolution condition: state is a field, progress is no longer an append-only plan section.

The dump is therefore the engineering progress ledger defined by `engineering:plans` ("A progress ledger (`<NAME>_PROGRESS.md`)") and templated by `engineering:plan-checkpoint`. `GOAL.md` (base default), `.agents/continuation/*` runtime state and `cli-session-recovery/` vault data are not the dump and are not deletion targets.

### Ledger responsibilities and readers (source, excluding generated `plugins/`)

| Responsibility | Owner today | Source |
|---|---|---|
| Structural graph: `Plan:`/`Roadmap:`/`Roadmap item:` headers, one-roadmap-item-per-plan, blocker 4-field schema, `## Downstream handoffs` reciprocity, terminal-with-undispatched-handoff, 4 scope lines, review-before-merge, 200-line/16 KB budget | `plan_graph.py` | `.agents/hooks/plan_graph.py:26-347` |
| Stop-hook transfer gate: claimed-ledger discovery, worktree/branch ownership, owner-copy dedupe, exact pointer and `Why:` line, blocker verbatim report | `plan_handoff_stop.py` | `.agents/hooks/plan_handoff_stop.py:24-526`; wired `.agents/plugins/manifests/claude/engineering-hooks.json:108`, `.agents/plugins/harness/engineering.json:111` |
| Workflow v2 repository provider: resolve plan/roadmap/worktree/branch, `## Next Steps` kind (`Paused:`/`Blocked:`/`Transfer:`/`Complete:`), `## Reviews`, decisions, `PR:` → `artifacts.pull_request`, `artifacts.ledger` | `workflow_runtime.py` | `.agents/workflows/workflow_runtime.py:541-787` |
| Repository inspection and delivery ownership (`progress_ledgers`, `delivery-preflight --ledger`) | `workflow_ops.py` | `.agents/workflows/workflow_ops.py:417,430,1657-1745,2213,2276` |
| Contract | Workflow v2 | `.agents/workflows/contract/v2/state.schema.json:43-48` (`artifacts.ledger` required), `examples/state.example.json:16`, `gates.md:35`, `.agents/workflows/providers/repository.md:4-18` |
| Convention text | skills | `engineering:plans` (definition, lifecycle, close-out), `plan-checkpoint` (template, budget, compaction), `handoff-format` (pointer), and ledger create/update text in `plan-authoring`, `plan-execution`, `feature`, `update-roadmap`, `merge`, `handoff`, `commit`, `committing`, `open-pr`, `stack`, `git-branching`, `resume-plan`, `pr-preflight`, `open-worktree` |
| Tests/fixtures | hooks tests | `test_plan_graph.py` (22), `test_plan_handoff_stop.py` (30), `test_plan_handoff_ownership.py` (10), `test_workflow_contracts.py:1806-2001`, `test_workflow_ops.py:939-1077`, `test_plan_workflows.py`, `test_task_workflows.py:235`, `test_hook_runtime.py`, `test_process_standards.py`, fixtures `plan_progress.template`, `provider_progress.template`, `plan_workflow_harness.py`, `plan_authoring_harness.py`, `task_workflow_harness.py`, `*_scenarios.json` |
| Live Core ledgers | plans | `plans/conditional-skill-routes/CONDITIONAL_SKILL_ROUTES_PROGRESS.md`, `plans/merge-worktree-cleanup/MERGE_WORKTREE_CLEANUP_PROGRESS.md`, `plans/repo-declared-config/REPO_DECLARED_CONFIG_PROGRESS.md` (214 lines, over budget) |

Generated copies exist in 59 tracked `plugins/` files; they are regenerated by CI after each source change and are never edited here.

### Native session tooling to reuse

- Exact guarded resume: `.agents/machine/scripts/agent_recovery.py open --host claude|codex --id <id>` (`open_session`, :292). It resumes in the recorded cwd and profile, refuses a verified `live` session ("refusing to create a duplicate writer"), refuses `unknown` without `--confirm-closed`, and claims a cross-process launch receipt. `machine:open-claude --resume` and `machine:open-codex` both delegate to it.
- Liveness: `agent_recovery.liveness` (:53) over the SessionStart registry `~/.agents-state/cli-sessions/<id>.json` written by `register_session.py` (pid + start time; `live`/`closed`/`unknown`).
- Current session id: `CLAUDE_CODE_SESSION_ID` (Claude) and `CODEX_THREAD_ID` (Codex) (`agent_recovery.py:55`).
- Unguarded resume strings (`history.py` `claude --resume <id>` / `codex resume <id>`, handoff launchers, the Windows-only vault) must not be recorded as the registry's resume command.
- Handoff launchers do not report the successor's id; `transfer.py acknowledge --successor` takes free text. The successor must record its own row.
- `.agents/continuation/` (`owner.json`, lock, receipts) is gitignored, pid-bound and worktree-bound runtime state with no native session id. It stays runtime coordination, not the registry.

### Termboard

`termboard/plans/ROADMAP.md`: a Rust learning project; milestone 1 not started; milestone 5 is "reopen each card's native session with its resume command". `tj-agents/docs/plans/agentic-delivery/ROADMAP.md:27-37`: do not make Termboard a prerequisite; until it exists, peer-cli and exact native resume identity are the lookup path.

## Proposed design

### D1 Layout and path grammar

```text
plans/features/<feature>/README.md
plans/features/<feature>/work-items/<work-item>/README.md
plans/features/<feature>/work-items/<work-item>/ACTIVE_SESSIONS.md   (only while a session is recorded)
plans/features/<feature>/work-items/<work-item>/<SUPPORTING>.md       (optional design/research docs)
```

`<feature>` and `<work-item>` are lowercase kebab-case. The work-item key is `<feature>/<work-item>`, derived from the path; it replaces the `Roadmap item:` header.

- Feature `README.md` replaces `<EPIC>_ROADMAP.md`: purpose, then one checklist line per work item with a link, its `Status:` and its delivery PRs.
- Work-item `README.md` replaces both `<NAME>_PLAN.md` and `<NAME>_PROGRESS.md` (and base's `plans/<goal>/GOAL.md`). Header fields: `Status:` (`proposed`/`active`/`blocked`/`paused`/`delivery-gated`/`done`, a field, never inferred), `Branch:`, `PR:`, `Worktree:`. Sections: outcome and scope, authorization, design (or links to supporting docs), delivery slices as a checklist with PR links, current state, verification, `## Reviews`, decisions, `## Next Steps` (unchanged semantics: blocker/paused/transfer forms and the four scope lines). Delivery history is the checked slice list; no chronological log.
- The 200-line/16 KB budget applies to the work-item README. Large design moves to a supporting doc in the same folder.
- `features/` is required for every new repository plan once the convention slice lands. Existing `_PLAN`/`_PROGRESS`/`_ROADMAP` and `plans/<goal>/GOAL.md` are read during a bridge until their migration slice; nothing new is created in those shapes. Standalone non-repository tasks are unchanged.

### D2 `ACTIVE_SESSIONS.md` schema and lifecycle

One section per recorded native session. The heading is its **session handle**, `<host>:<native-session-id>`:

```markdown
# Active sessions

## codex:01a12aa7-5b58-7312-9400-ef710762147f
- Role: owner
- State: active
- Machine: <hostname>
- Profile: default
- Title: <visible CLI/tab title, or none>
- Worktree: <absolute path>
- Branch: <branch>
- PR: <URL, or not opened>
- Head: <40-hex commit>
- Predecessor: <handle, or none>
- Successor: <handle, or none>
- Verified: <UTC ISO-8601>
- Resume: `machine:open-codex --id 01a12aa7-5b58-7312-9400-ef710762147f`
```

- `Role:` is `owner` (at most one per work item: the delivery-branch writer) or `bounded: <scope>` for a concurrent agent whose scope and writable paths are disjoint from every other row.
- Stored `State:` is `active` or `handing-off`. Liveness is never stored.
- `Resume:` is the guarded skill invocation, never a raw `claude --resume`/`codex resume`: `machine:open-claude --resume <id>` or `machine:open-codex --id <id>`, plus `--claude-history-root`/`--codex-history-root <profile>/…` when `Profile:` is not `default`.
- Record: a session adds its own row when it takes ownership (plan-execution pickup, handoff acknowledgement, or a bounded lease), using `CLAUDE_CODE_SESSION_ID`/`CODEX_THREAD_ID` and Git for the other fields. Refresh `Head:`/`PR:`/`Verified:` only at material checkpoints, in the same substantive commit as the README; never an observation-only commit.
- Handoff: the predecessor sets `State: handing-off` before launch. On acknowledgement the successor adds its row with `Predecessor:` and removes the predecessor's row in its first checkpoint.
- Remove a row when that session's work is terminal (work item done or bounded scope delivered), in the commit that records the outcome in the README. Delete the file when its last row goes; absence means no recorded session.
- Read-time status (computed, never written): `live`/`closed`/`unknown` from `agent_recovery.liveness` on the recorded machine; `foreign` when `Machine:` differs from the current machine; `stale` when the worktree is missing or its branch/HEAD differs from the row. `unknown`, `stale` and `foreign` authorize nothing: no resume, no new writer, no worktree deletion, until reconciled (session search evidence or the user's explicit confirmation).
- A worktree is deletable only when no row in any checkout names it and its branch head is on the remote with the PR recorded in the README; peer-cli `finish.py`'s existing claimant and cleanup-proof gates still apply.

### D3 Resume path

`machine:recover-agents` gains a "continue work item" entry rather than a new skill: read the work item's `ACTIVE_SESSIONS.md`; with exactly one `owner` row, run its `Resume:`; with several rows, list them and require an explicit handle; with no rows, start a new owner from the README's `## Next Steps` through `engineering:plan-execution`. `agent_recovery.open_session` already refuses a live or unknown session, so a recorded resume cannot create a duplicate writer. A small helper, `work_item_sessions.py` beside `agent_recovery.py`, parses and validates the file, reports read-time status, finds the work item that names a given worktree, and prints the guarded command.

### D4 Migration and deletion map for the progress dump

Ordered so guidance never points at behavior that does not exist:

1. Engineering runtime accepts a work-item README wherever it accepts a ledger (`plan_graph.py`, `plan_handoff_stop.py`, `workflow_runtime.py` provider, `workflow_ops.py`), plus feature README as roadmap. Ledgers still read.
2. Convention switch: `base:plan-artifacts`, `engineering:plans`, `plan-checkpoint` template, `handoff-format` pointer (`Read @<work-item README> and do what its ## Next Steps says`), and every skill listed in the readers table; templates for both READMEs and `ACTIVE_SESSIONS.md`.
3. Core's own `plans/` migrated: the three live ledgers and each live `plans/<goal>/GOAL.md` become work items; terminal leftovers are identified individually with evidence before any deletion.
4. Removal: ledger parsing, `_PROGRESS`/`_PLAN`/`_ROADMAP` patterns, fixtures and tests replaced; rename grep gate `_PROGRESS|progress ledger` returns zero outside an explicit allowlist. Workflow v2 `artifacts.ledger` needs a contract decision at this step (additive field vs v3) because host pins live under the contract version.

### D5 Consumer rollout

Steps 1–2 and 4 ship to every consumer through the marketplace automatically. Consumer `plans/` content is never rewritten from Core. Each consumer migrates under its own goal and gates; the bridge in step 1 keeps legacy ledgers working until step 4, and step 4 does not merge until every recorded consumer migration has landed. `plan_graph.py` reports legacy artifact counts so adoption is measurable per repository. Work repositories decide whether machine-local paths and session ids belong in their tracked plans.

### D6 Termboard

This Markdown registry is the interim. Termboard (SQLite) supersedes it: once Termboard covers the daily loop, `ACTIVE_SESSIONS.md` and the work-item session convention stop being used and are retired under their own goal. Keep the interim tooling minimal accordingly. Nothing in Core waits on Termboard.

### S2 runtime dual-read specification

A work-item README is `plans/features/<f>/work-items/<w>/README.md`; it is both plan and ledger. Ledger handling stays unchanged until S5.

- `workflow_runtime.py` `RepositoryStateProvider.resolve`: when the path is a work-item README, require headers `Status`, `Worktree`, `Branch`; `artifacts.plan` and `artifacts.ledger` are the README, `artifacts.roadmap` is `plans/features/<f>/README.md` (must exist), `workflow_id` is `<f>/<w>`, decisions come from `## Decisions`. Next Steps, `PR:`, `## Reviews` and worktree/branch checks reuse the existing code. The v2 schema is unchanged.
- `plan_graph.py`: `repository_report` also checks every work-item README: `Status:` in the D1 set; the feature README holds exactly one checklist line containing `` `<f>/<w>` ``; the existing Next Steps scope, blocker, review-gate and terminal-handoff checks; `Blocked by:` and `## Downstream handoffs` may name a work-item README; the 200-line/16 KB budget; `Status: done` requires `Complete:` Next Steps and no `ACTIVE_SESSIONS.md`.
- `plan_handoff_stop.py`: recognise work-item README paths wherever it recognises `_PROGRESS.md`; the pointer becomes `Read @<absolute README> and do what its `## Next Steps` says.`; the `Why:` line names the README.
- `workflow_ops.py`: `inspect_repository` adds `work_items`; `delivery-preflight --ledger` accepts a work-item README.
- Tests mirror each existing ledger case with a work-item fixture.

## Delivery slices

| Slice | Content | Route | Depends on |
|---|---|---|---|
| S1 | `ACTIVE_SESSIONS.md` schema doc and template under machine resources; `work_item_sessions.py` (`validate`, `status`, `find --worktree`, `resume` via `open_session`, `record`/`remove` for the current session); `recover-agents` "continue work item" text; Windows/Linux tests | `merge` | none |
| S2 | Engineering runtime dual-read (D4 step 1) with tests | `merge` | none |
| S3 | Convention switch (D4 step 2), own docs slice | `merge-docs` unless a test-selection path is touched | S1, S2 |
| S4 | Core `plans/` migration (D4 step 3) | `merge-docs` | S3 |
| S5 | Ledger removal and contract decision (D4 step 4) | `merge` | S4 and recorded consumer migrations |
| S6+ | One goal per consumer repository | that repository | S3 |

## Decisions (Tommy, 2026-10-12)

1. Done work items keep their README (Status `done`, delivery slices) until the whole feature is terminal; then the feature folder is deleted. Git is the archive.
2. `ACTIVE_SESSIONS.md` uses one `## <handle>` section per session with `- Field:` lines.
3. Runtime first: S1, S2, then the S3 convention switch.
4. Termboard supersedes the Markdown registry once it covers the daily loop (D6).
5. After the 2026-10-12 crash: the session registry is a local hook-written SQLite store, not `ACTIVE_SESSIONS.md` ("fine for now"); cloud sync is the long-term vision, not part of this work. See the redesign section.
6. The registry is one central local database, `~/.agents-state/sessions.db`, written by hooks. It holds session state and work-item status, so status never lives in a branch's Markdown: no `ACTIVE_SESSIONS.md`, and no `Status:` field in work-item READMEs, which keep only purpose, design and decisions. SQLite, not Postgres or SQL Server: no server process, and each machine works on separate work. Cloud sync is a later step behind the same storage module.

```agent-host-coverage
{"schema_version":1,"shared_source":".agents/machine/scripts/work_item_sessions.py","hosts":[{"host":"claude","behavior":"Record, report and resume the exact Claude session recorded for a work item through the guarded open-claude path.","source":".agents/machine/scripts/work_item_sessions.py","mapping":"Machine package resources consumed by machine:recover-agents and machine:open-claude --resume.","verification":{"level":"planned","result":"pending","evidence":"S1 unit tests for parse, validation, status and resume delegation with a Claude row and CLAUDE_CODE_SESSION_ID."}},{"host":"codex","behavior":"Record, report and resume the exact Codex session recorded for a work item through the guarded open-codex path.","source":".agents/machine/scripts/work_item_sessions.py","mapping":"Machine package resources consumed by machine:recover-agents and machine:open-codex.","verification":{"level":"planned","result":"pending","evidence":"S1 unit tests for parse, validation, status and resume delegation with a Codex row and CODEX_THREAD_ID."}}]}
```

## Redesign: hook-written SQLite session store (approved 2026-10-12)

Trigger: a PC crash killed ~20 sessions. The registry (`~/.agents-state/cli-sessions/*.json`, 381 entries) records start only, so every session now reads `closed` and finished work is indistinguishable from interrupted work. Tommy rejected a Markdown session registry and asked for a database, with a cloud DB and Termboard as the long-term vision.

- Store: `~/.agents-state/sessions.db`, SQLite in WAL mode via stdlib `sqlite3` (Windows and Linux, no dependency), behind one storage module so cloud sync can replace the backend later. Replaces `ACTIVE_SESSIONS.md` in S1; the work-item README layout (D1) stays as the human documentation.
- Work-item status lives in the same database (decision 6). D1's `Status:` header and S2's `Status:` checks are superseded; where the delivery fields and `## Next Steps` live is re-specified before S2 starts.
- One `sessions` row per `host:session_id`, never deleted: machine, cwd, branch, work item (resolved from the branch against `plans/features/*/work-items/*/README.md` `Branch:`, or set by an explicit `claim`), PR, title, pid and pid start time, `started_at`, `last_activity_at`, `turn_state` (`working`/`awaiting_input`), `ended_at`, `end_reason` (`finished`/`closed`/`handed_off`), successor.
- Written by hooks, not agents: SessionStart upserts (extends `register_session.py`), UserPromptSubmit sets `working`, Stop sets `awaiting_input` and refreshes branch/work item, Claude SessionEnd sets `ended_at`; `finish.py`, `close.py` and handoff set the end reason. Codex has no SessionEnd hook here (manifests: SessionStart, UserPromptSubmit, Stop, PreToolUse), so a hand-closed Codex tab reads as interrupted: a harmless false positive.
- Tommy's two flags: not finished = `ended_at IS NULL`; worked on right now = `turn_state = 'working'` and the recorded pid alive. Liveness is computed at read time, never trusted from storage.
- Recovery: `recover-agents --interrupted` selects `ended_at IS NULL` rows whose pid is dead, groups them by work item with their last turn state, and reopens them through `agent_recovery.open_session`, verifying each resumed session re-registered before reporting success.
- Not cloud now: a native session id resumes only on the machine holding its transcript, every hook would gain a network call and a secret, and work-item state already syncs through Git and GitHub. Termboard (milestone 1 uses rusqlite, milestone 5 is native recover) adopts or imports this schema; libSQL/Turso embedded replicas are the sync path if cross-machine visibility is wanted before then.
- Defect folded in: `agent_recovery.py recover --select` marked `claude:c27c07bf` `launched` at 21:34 while the session never re-registered (registry pid unchanged); launch success must require a fresh SessionStart registration.

### S1 rework specification

Observed 2026-10-12: `claude --resume <id>` keeps the native id (this session re-registered as `c27c07bf` with a new pid), so a resumed session is detectable by a fresh `started_at` on the same id.

- `.agents/machine/scripts/session_store.py` (new, stdlib only): the single storage module. `~/.agents-state/sessions.db` (honouring `AGENT_STATE_DIRECTORY`), WAL, `busy_timeout` 5000 ms, `PRAGMA user_version = 1`. Tables:
  - `sessions(handle PK '<host>:<id>', host, session_id, machine, profile, title, cwd, repo, branch, head, work_item → work_items.key, role ('owner' | 'bounded: <scope>'), pid, pid_started_at, started_at, last_activity_at, turn_state ('working'|'awaiting_input'), ended_at, end_reason ('finished'|'closed'|'handed_off'), predecessor, successor)`. Rows are never deleted.
  - `work_items(key PK '<repo>:<feature>/<item>', repo, feature, item, status ('proposed'|'active'|'blocked'|'paused'|'delivery-gated'|'done'), branch, pr, updated_at)`.
  - `repo` is the `origin` remote as lowercase host plus path, Azure DevOps SSH and HTTPS unified (review R15), else the absolute `git-common-dir`.
- Hook entry `session_store.py hook <session-start|prompt|stop|session-end> --host claude|codex` reads the hook payload from stdin and always exits 0 within its budget. SessionStart is called from `register_session.py` after its existing JSON registry write (that registry stays; `agent_recovery.liveness` reads it). SessionStart upserts and clears `ended_at`/`end_reason`, because a resumed session is alive again. UserPromptSubmit sets `working`. Stop sets `awaiting_input` and refreshes cwd/branch/head. Claude SessionEnd sets `ended_at` and keeps an earlier reason, else `closed`. Start and Stop attach an unset work item when exactly one non-`done` work item in the same repo records the current branch.
- Wiring: Claude `machine-hooks.json` gains UserPromptSubmit, Stop and SessionEnd. Codex gains UserPromptSubmit and Stop; it has no SessionEnd, so a hand-closed Codex tab reads as interrupted.
- `work_item_sessions.py` is rewritten over the store, and all `ACTIVE_SESSIONS.md` code is removed. Commands:
  - `claim <feature>/<item> --host H [--role] [--predecessor]` creates the item (`active`, current branch) when absent and enforces one live owner. A predecessor's ownership transfers with `handed_off` and `successor` set.
  - `status <feature>/<item>` and `find --worktree` are read-only.
  - `resume` picks the single not-ended owner, refuses foreign/stale/live, and goes through `open_session`.
  - `interrupted [--resume HANDLE…]` lists not-ended rows whose pid is dead, grouped by work item with the last turn state, and resumes only listed handles.
  - `end --reason` and `item <feature>/<item> --status [--pr]` record session ends and work-item status.
- `finish.py` and `close.py` record `finished`/`closed` for their own session before closing it, best-effort.
- `agent_recovery.open_session` reports success only after the resumed session registers again (`started_at` after the launch). Otherwise the receipt is `ambiguous` and the CLI exits 3, never retried.
- `work-item-sessions.md` and the `recover-agents` text describe the store, `claim`, `status`/`resume` and `interrupted`. The Codex auto-approve rule covers `status`, `find`, `interrupted` and `resume`. Catalog `digest` values are never committed.

## Current progress

- 2026-10-12, Claude session `claude:c27c07bf-a274-466a-a10e-10ef96f36841`: investigation complete; design, migration map and slices recorded above.
- S1 implemented in this commit: `.agents/machine/scripts/work_item_sessions.py`, `tests/test_work_item_sessions.py` (24 tests), `.agents/machine/resources/work-item-sessions.md`, the `recover-agents` "Continue a work item" section, machine harness permissions (Codex scoped to `status`/`resume`), sources mapping and catalog digest. Windows: `test_work_item_sessions`, `test_agent_recovery`, `test_harness_manifests`, `test_catalog_digests`, `test_harness_permissions_sync`, `test_open_claude` — 115 passed, 1 pre-existing symlink skip; `sync-generated.ps1 -Check` passes after a throwaway regeneration (`plugins/` restored). Linux, review and PR outstanding.
- Persistent-workflow owner initialized and claimed; scheduler registration was denied by the permission classifier as unauthorized persistence, so the owner is checkpointed `blocked` (`host-capability-or-permission-unavailable`). Foreground work continues.
- Review: `reviews/Feature-WorkItemSessions.md`, approved at `d03b34d` after R1–R8 were fixed (one HIGH: committed rows became permanently stale). PR [#228](https://github.com/tj-agents/core/pull/228) opened as a draft at `07c6777`; `b4c89fe` restored the generated machine catalog digest the `guard` job rejects. That digest commit is not yet covered by the review watermark. The ACTIVE_SESSIONS store is now superseded by decision 6.
- Side workstream: a standards defect in `.agents/hooks/worktree_placement_gate.py` (heredoc lines that fail `shlex` are classed as invalid worktree creations) is recorded with replay evidence in `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-WorktreeGateHeredocFalsePositive\plans\worktree-gate-heredoc-false-positive\GOAL.md`. Its Codex launch was denied by the permission classifier over `--bypass-hook-trust`.
- 2026-10-12 ~21:27: the PC crashed (resource exhaustion: Python "can't start new thread", Git Bash fork failures) and interrupted this session. Recovery session `claude:cec3b609-c328-4482-b813-3c35719a8032` recorded the SQLite redesign in `ffb9a62`; Tommy approved it (decisions 5 and 6).
- 2026-10-13, after a second crash: the S1 store rework is committed in `b131203`, with catalog line endings and digests restored in `46592c5`. It contains `session_store.py`, the hook wiring, `work_item_sessions.py` over the store, finish/close end reasons, docs and tests. Resume registration verification is not duplicated here: PR [#233](https://github.com/tj-agents/core/pull/233) (`Fix/RecoveryClaudeProfile`) owns it in `agent_recovery.py`. Windows checks run so far: session, finish, peer-cli, register, hook-contract, launch-budget, harness, catalog, recovery and open-claude suites; throwaway regeneration with `sync-generated -Check` and catalog `--check` passes.
- The continuation Stop hook falsely reports `binding-head-changed` whenever a delivery binding exists: it reads the binding head from `head`, while the artifact stores it as `remote_head_sha`. That fix is owned by PR [#230](https://github.com/tj-agents/core/pull/230).

- 2026-10-13: review rounds over the store found R9–R40 (`reviews/Feature-WorkItemSessions.md`); every finding is fixed with regression tests except R14 (wontfix by design) and two rejected with recorded reasons. Fix commits `3df8655`, `6c4ed07`, `b43e091`. Key outcomes: the packaged SessionStart loader finds `session_store.py`; at most one owner row per work item (partial unique index plus one `BEGIN IMMEDIATE` transaction in `session_store.claim_work_item`); only `closed` rows resume; finish/close record their end before spawning the observer and reopen it on refusal. The work order's watermark is `6c4ed07` with no open findings; `b43e091` is pushed and bound to PR #228 but not yet reviewed.
- Local verification at `b43e091` (worker report, Windows): store and CLI tests 87 OK; peer-cli, hook, harness, catalog, recovery and open-claude suites 164 OK (1 pre-existing skip); `test_codex_windows_hook_commands` OK; `sync_harness_manifests.py --check` passes. `test_finish_entrypoint_removes_verified_disposable_worktree_after_host_exit` is a load flake that also fails on `main` (BUGS.md B008). CI passed on `67b45a8`; later heads are unobserved.
- Installed `engineering@base-agents` `4090e7d23875` is truncated (no `skills/`, `workflows/`, `schemas/`); run workflow helpers from this checkout's `.agents/workflows/`. The Claude Stop hook falsely reports `binding-head-changed` until PR #230 merges.
- 2026-10-13: Tommy asked for a Codex handoff to finish this. Claude session `claude:c27c07bf-a274-466a-a10e-10ef96f36841` released ownership after this checkpoint; its continuation owner (`.agents/continuation/owner.json`, harness `claude`) is checkpointed `blocked` and should be re-initialized by the Codex owner with `--harness codex`, after moving the old `owner.json`/`events.jsonl` outside the tree.

## Next Steps

Lane: L4 (ordinary review, CI repair and delivery); re-route to L3 before the S2 design proposal. Effective `auto_approve_design` is false (no `design` key in `.agents/settings.json`).

1. Re-initialize and claim the continuation owner for Codex (see Current progress), then run `engineering:incremental-review` over `6c4ed07..b43e091` (medium effort is enough: the last high-effort passes produced only low-severity edge cases), using `.agents/workflows/workflow_ops.py` from this checkout. Fix any finding through `engineering:address-review`; record dispositions only in `reviews/Feature-WorkItemSessions.md`.
2. Confirm exact-head Windows/Linux CI on PR [#228](https://github.com/tj-agents/core/pull/228); repair failures under `engineering:failing-tests` (never commit `plugins/` or catalog `digest` changes; keep files LF). Mark the PR ready and deliver through `engineering:merge` (standing auto-merge authorization). Do not duplicate PR #233's resume-registration change.
3. After merge, propose where `## Next Steps` and delivery fields live now that work-item READMEs carry no status (decision 6) and wait for Tommy's decision, then start S2 from the updated `origin/main`.

- Scope: whole plan through all remaining phases and terminal delivery.
- Current slice: S1 session store (SQLite), hooks and interrupted-session recovery.
- Remaining scope: S2–S5 in Core; consumer migrations under their own goals.
- Done when: the progress ledger is removed from Core with no dangling references, and every recorded consumer migration has landed.
