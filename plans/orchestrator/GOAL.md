# Orchestrator (core#435)

## Outcome

One orchestrator session runs long sequential work across agents. It writes each worker's prompt,
waits as long as the work takes, and starts each piece the moment its dependencies finish. It adopts
existing sessions, keeps one queue of decisions only Tommy can make, executes the merges he approves,
watches CI with a script, and closes each worker once its work is merged and nothing is left in it.
Requirements: [core#435](https://github.com/tj-agents/core/issues/435) and its three comments.

Acceptance (from #435): a dependency file of three workers where C depends on A and B. `status` reports
each worker's work, state and blocker. C launches automatically once A and B finish. A merge gate appears
as `here: say "merge #N"` and is never sent to a peer as an instruction. A merged, clean, idle worker is
closed and its worktree removed without a prompt.

## Placement and dependency on the Workflow plan

The [Workflow/Agent Store boundaries](https://github.com/tj-agents/docs/pull/20) put lifecycle, handoff and
status in Workflow, native observation and host operations in Machine, and recorded state in Agent Store.
Dispatching dependent work is lifecycle, so the orchestrator is a new `workflow:orchestrate` skill:
a session-driven loop, not a background scheduler, and not a second handoff (it calls Machine's launchers
for bounded side workstreams). No orchestration exists today (searched `.agents`, `docs`, `tests`, `plans`).

The `workflow` package reached main with #354. The rest of the stack (#355, #356; Codex `01a16053`) stays
with its owner, and this branch never edits their branches. Both register Workflow skills in `catalog.json`
and `harness/workflow.json`, so this branch merges main after #355 lands and resolves that overlap. Docs#20's
decision gains one line naming `orchestrate`, and its "no scheduler" wording stays true.

Reused as-is, no edits (the stack changes launchers, `register_session.py`, `agent_recovery.py`):

| Need | Existing piece |
| --- | --- |
| Launch a worker in a tab | `machine:handoff-claude` / `handoff-codex` launchers (`--title`, `--lane`, status file with `child_pid`) |
| Bind launch → session | registry `sessions.pid` == status file `child_pid` |
| Recorded state, idle signal | Agent Store registry: `turn_state`, `ended_at`, `successor` (relaunch follows the chain) |
| Liveness, close tab | `machine:peer-cli` `close` (pid + start-time verified, exact tab) |
| Message a Codex worker | `machine:followup-codex` |
| Message a Claude worker | `SendMessage` (model action the script emits) |
| Worktree removal proof | `engineering:merge` `cleanup_proof.py` + `worktree_sweep.py` |
| Merge method | the repository's own: core runs `gh pr merge <n> --merge --auto` |

## Design

`orchestrate.py` (Python 3.9+, stdlib) owns all bookkeeping. The model writes prompts, judges worker output,
answers what it can, and relays the decision queue. It runs only these commands:

- `init <file> --name N` and `configure` (Machine script paths found by discovery, re-checked every tick).
- `add` a worker: id, title (the tab and peer name, per #358), repo, branch, host
  `claude|codex|subagent`, lane, prompt file, `depends_on`, `done_when` `merged|pushed|reported`.
- `adopt` an existing session by handle or tab title, and optionally its PR.
- `tick`: collect state from the registry, GitHub (`gh pr view` state, head, checks, review) and git
  (dirty, unpushed). Then close out finished workers and dispatch unblocked ones. Each dispatch gets its own
  worktree from `origin/<default>`, then a launch, a Codex follow-up, or an emitted action for the model
  (SendMessage, or Agent for subagents). Finally print the table and the decision queue. Every derived fact is
  recomputed from these sources each tick; the file holds only intent, bindings and answers.
- `wait`: block until a material change (a worker goes idle or ends, a PR merges, checks finish, a timeout).
  The model starts it with `run_in_background`, so its exit wakes the session. Local registry reads happen
  every few seconds; GitHub reads happen at most once a minute, and only for PRs not yet merged.
- `ask` / `answer`: the decision queue. Each entry names the tab, the question and the exact reply. A merge
  approval binds to the PR's head SHA, so a new push invalidates it.
- `merge`: only with a recorded approval for that exact head. It uses the repository's normal method, then
  the next `wait` watches the result.
- `mark <worker> reported|failed`: model judgement for `done_when: reported` work.

Close-out (automatic in `tick`): PR merged, tree clean, nothing unpushed, `turn_state` idle, no open
decision for the worker, and `cleanup_proof` `removable`. It then runs `peer-cli close --force`, followed by
the sweep. Anything else stays open with its reason shown.

The state file defaults to `~/.agents-state/orchestrations/<name>.json`, written atomically under a lock.
A restarted orchestrator runs `tick` and continues.

## Slices

1. **Runtime + tests**: `orchestrate.py` and the unittest suite. The tests use a temp registry, a fake
   launcher (dummy process), fake `gh`/`git` fixtures and a fake peer-cli. They cover #435's acceptance
   scenario, the head-bound merge gate, close-out refusals and a restart from the file.
2. **Skill**: `workflow:orchestrate` canonical SKILL.md, both host entry points, the catalog, harness
   permissions for the scripts, and a SOURCE_LAYOUT/README mention. Also add the Docs#20 line.
3. **Live acceptance**: drive one real three-worker run (Windows) with dummy-process workers. Linux runs
   the suite in CI. Native activation follows the stack's S3 gate.

## Progress

- 23 Oct: Tommy chose `workflow:` and asked to merge the stack. Its owner (Codex `01a16053`) was already
  landing it with his authorization (#352, #353, #354 merged by 09:40 UTC), so this session did not race it.
  Its follow-up endpoint was unavailable, so the boundary check was never delivered.
- #354 put the Workflow package on main, so this branch is based on main, not stacked on #355.
- Slice 1 committed (`908ebdd4`): runtime, Agent Store `sessions()`, `peer-cli list --json`, 12 tests.
- Slice 2 committed (`294af0f6`, `1a4d979d`, `88091ea1`): skill, entry points, catalog, harness, merge
  failure handling, `peer-cli --id`. PR [#439](https://github.com/tj-agents/core/pull/439) is open.
- The review standards resolver fails with "Selected marketplaces provide conflicting plugin namespaces",
  so injected-standards scope is unresolved. CODE_CONVENTIONS.md was applied directly.
- Docs#20 is still open and owned by `01a16053`. Its `orchestrate` line waits for that PR to merge.

- Review of `23da17c6..88091ea1`. Native `code-review high` found 10 findings and the security lens found 5.
  Fixed: worker self-approval and reconfiguration (privileged commands now require the orchestrator
  identity from `peer-cli self`), unquoted worker text, merge-queue false drop (`mergeQueueEntry`),
  squash/rebase close-out, a stale PR on a reused branch, relaunch inheriting reports, branchless merged
  subagents, a single sweep, empty-rollup green, and the PowerShell-hostile report command. Rejected:
  reusing `workflow_ops.parse_status_checks`, because Workflow must not depend on the Engineering runtime.

## Next Steps

Commit the review fixes, run incremental review on the delta, push. Merge
main after #355 and resolve the catalog/harness overlap. Run a live three-worker acceptance with real tabs
when Tommy picks the work. Merge #439 after Tommy says "merge #439".
