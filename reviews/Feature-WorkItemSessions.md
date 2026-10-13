# Code review — Feature/WorkItemSessions

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `ba74c9c932e200a049c92c7a3488930c52a12d57`  `(2026-10-13)`
**Judgment:** `approved`

## Review pass — 2026-10-12 — full

**Candidate base:** `c91b60c955ad4a3f0f7a9383fc20f1c4a6b58510`
**Candidate head:** `afa69fa55a938cde389e56d171db21fac8877660`
**Candidate branch:** `Feature/WorkItemSessions`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:5ce45e3415d8bf786db4b56fd8d0dfd107e22173051442035cf4dd0201f51df8` `(8 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\LVFP5jDNUJ7t4db8Ve9L_W\ok9rHq73XwWAmDRQ0gETxL`
**Candidate bundle identity:** `sha256:801a0add80f2d8c1de8ba3ca3ec72c8c75f7384ddfd7ccf4751c6514b3e19e50`
**Work-order path:** `reviews/Feature-WorkItemSessions.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Native layer: Claude Code `code-review` skill (medium). Lens: `workflow` (`review-lens`). No security-sensitive paths.

### Findings

- [x] **R1 — HIGH — native** — `.agents/machine/scripts/work_item_sessions.py:264`
  `Head` is compared for equality with HEAD, but the lifecycle commits the row, so every recorded row becomes
  `head-mismatch` and `resume` refuses it. Treat the row as current while HEAD contains `Head`
  (`git merge-base --is-ancestor`); report stale only when diverged.
  Fixed: _head_contains uses merge-base --is-ancestor; stale reason is head-diverged; tests test_later_commits_on_the_branch_keep_the_row_current, test_status_reports_diverged_head_as_stale.
- [x] **R2 — MEDIUM — native** — `.agents/machine/scripts/work_item_sessions.py:326`
  `resume --confirm-closed` is reachable under the auto-approved Codex `resume` prefix rule, so an agent can
  relaunch an `unknown` session without the user's reconciliation, contradicting "unknown authorizes
  nothing". Remove the flag from this helper; reconciliation stays with `open-claude`/`open-codex`.
  Fixed: --confirm-closed removed from resume; doc points unknown reconciliation at open-claude/open-codex.
- [x] **R3 — LOW — native** — `.agents/machine/scripts/work_item_sessions.py:375`
  `record` read-modify-writes the registry without a lock, so concurrent sessions in one checkout can lose a
  row or both claim ownership. Serialize `record`/`remove` with `agent_recovery._claim_lock` on a lock file
  outside the repository.
  Fixed: record/remove run under _registry_lock (agent_recovery._claim_lock in the temp directory); test_concurrent_records_keep_every_row.
- [x] **R4 — LOW — native** — `.agents/machine/scripts/work_item_sessions.py:370`
  On a detached HEAD `record` writes an empty `Branch`; a whitespace trim then makes the line malformed and
  breaks the whole file. Refuse detached HEAD and reject empty field values in `validate`.
  Fixed: record refuses a detached HEAD and validate rejects empty fields; tests test_record_refuses_detached_head, test_empty_field_is_rejected.
- [x] **R5 — LOW — workflow** — `.agents/machine/utility/recover-agents/SKILL.md:37`
  "several rows require an explicit `--handle`" contradicts `resume`, which selects the single `owner` row
  regardless of bounded rows. State the owner-count rule.
  Fixed: recover-agents states that resume without --handle selects the single owner row.
- [x] **R6 — LOW — workflow** — `.agents/machine/resources/work-item-sessions.md:34`
  The doc says `Profile` is compared against the reading machine; only `Machine` is compared and `Profile`
  locates history on resume. Split the bullet.
  Fixed: Machine and Profile bullets split; Profile only locates history on resume.

## Review pass — 2026-10-12 — incremental

**Candidate base:** `afa69fa55a938cde389e56d171db21fac8877660`
**Candidate head:** `5c13ab4e7ddca02f36ef5722302011dd6ff2cdd4`
**Candidate branch:** `Feature/WorkItemSessions`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:ab292007ea8fb141ead4411236cb6f4d587d6fd8cffc86ba4640b5f746e0fa46` `(5 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\1jNF5kys_vwuYr4h3iMEwz\S4rwcCQdvEobnlDrjcf1RI`
**Candidate bundle identity:** `sha256:e7656c7f4ed62ba5b28c30ff58943b65e911306bf02fa109a905ae10ffa72abc`
**Work-order path:** `reviews/Feature-WorkItemSessions.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Native layer: Claude Code `code-review` skill (medium). Lens: `workflow` (`review-lens`). R1–R6 dispositions verified against the delta.

### Findings

- [x] **R7 — LOW — native** — `tests/test_work_item_sessions.py:247`
  `test_concurrent_records_keep_every_row` wraps `_record_locked` in the lock itself instead of driving
  `record()`, so removing the lock from `record()` would still pass. Drive the threads through `WIS.record`.
  Fixed: threads call `WIS.record` with per-thread session ids and a slowed `load`; verified the test fails
  with the lock removed from `record()` and passes with it.
- [x] **R8 — LOW — workflow** — `.agents/machine/utility/recover-agents/SKILL.md:37`
  "with no owner or no rows, pass `--handle`" offers `--handle` for the no-rows case, where `resume` raises
  before reading it. Split the two conditions.
  Fixed: rows without a single owner need `--handle`; no rows start a new owner.

## Review pass — 2026-10-12 — incremental

**Candidate base:** `5c13ab4e7ddca02f36ef5722302011dd6ff2cdd4`
**Candidate head:** `d03b34dd289064840cddebeb07fc6d402ef3ae71`
**Candidate branch:** `Feature/WorkItemSessions`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:f9d9ce71f4ec2b7bafd2a9fb8c6f4ad04b12884445775173731388ffa46893eb` `(3 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\obbv74MnmI5X9gxgWeIA1C\_zVgO8fjG_5h__ytAnlfUT`
**Candidate bundle identity:** `sha256:aeb2cf9ebc08321c827c2f86d4559b0476dc6ffd7439df95bff85573431d3c21`
**Work-order path:** `reviews/Feature-WorkItemSessions.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Native layer: Claude Code `code-review` skill (medium). Lens: `workflow` (`review-lens`).

### Findings

No findings. R7 and R8 dispositions verified.

## Review pass — 2026-10-13 — incremental

**Candidate base:** `d03b34dd289064840cddebeb07fc6d402ef3ae71`
**Candidate head:** `67b45a87b390a722727dc6f428ff08922113b238`
**Candidate branch:** `Feature/WorkItemSessions`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:69c39bad441c9e92dca09869bdd2cd06515a55c4b229718a1d6ed7f855a4f0c8` `(16 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\lRVmo24oi_Xug_5KxuqHSL\hBINm-RI6thx-ILDMdEZch`
**Candidate bundle identity:** `sha256:e99327032211b45c25b81cdc467bcbaf7327dd2e99f27baacab3a5da4b829c25`
**Work-order path:** `reviews/Feature-WorkItemSessions.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Native layer: Claude Code `code-review` skill (high). Lens: `workflow` (`review-lens`). No security-sensitive paths. Resume registration verification is out of scope here (PR #233).

```agent-host-coverage
{"schema_version":1,"shared_source":".agents/machine/scripts/session_store.py","candidate_head":"ba74c9c932e200a049c92c7a3488930c52a12d57","hosts":[{"host":"claude","behavior":"Hooks record Claude session start, turns, stop and end in sessions.db; work_item_sessions claims, reports, resumes and lists interrupted Claude sessions.","source":".agents/machine/scripts/session_store.py","mapping":"Claude machine-hooks.json SessionStart (register_session.py), UserPromptSubmit, Stop and SessionEnd entries; recover-agents routes the CLI.","verification":{"level":"source","result":"passed","evidence":"Windows focused session-store and work-item-session suites: 89 OK; the current base-merge review retained no S1 findings."}},{"host":"codex","behavior":"Hooks record Codex session start, turns and stop in sessions.db; work_item_sessions claims, reports, resumes and lists interrupted Codex sessions.","source":".agents/machine/scripts/session_store.py","mapping":"Codex machine-hooks.json SessionStart via hook_dispatch (register_session.py), UserPromptSubmit and Stop entries; recover-agents routes the CLI.","verification":{"level":"source","result":"passed","evidence":"Windows focused session-store and work-item-session suites: 89 OK; the current base-merge review retained no S1 findings."}}]}
```

### Findings

- [x] **R9 — HIGH — native, workflow** — `.agents/machine/utility/peer-cli/scripts/register_session.py:342`
  `_load_session_store` looks under `HERE.parents[2]` (`.agents/machine` in the package), but `sources.json` ships the
  module only at `PLUGIN_ROOT/resources/machine/scripts/session_store.py`, so installed SessionStart never writes a
  row and `interrupted` finds nothing. Add the packaged candidates (`HERE.parents[4]/resources/machine/scripts` for the
  `.agents/machine/utility/...` layout, `HERE.parents[2]/resources/machine/scripts` for `skills`/`codex-skills`) and
  test the loader against both packaged layouts.
  Fixed: the loader also checks `HERE.parents[4]/resources/machine/scripts`; `LoadSessionStoreTests` build each packaged layout and find the store.
- [x] **R10 — MEDIUM — native** — `.agents/machine/scripts/work_item_sessions.py:137`
  `_read_time_status` returns `closed` for any ended row before the foreign and stale checks, and a not-ended dead
  session skips the worktree check, so `resume` can reopen a foreign session or one whose worktree is gone. Check
  `foreign` first, then liveness for not-ended rows, then the worktree staleness for every resumable row.
  Fixed: foreign first, then liveness for not-ended rows, then worktree staleness for resumable rows; tests cover foreign ended rows and a dead session with a stale worktree.
- [x] **R11 — MEDIUM — native** — `.agents/machine/scripts/work_item_sessions.py:267`
  `resume` without `--handle` only considers owners with `ended_at IS NULL`, so an owner whose tab was closed cleanly
  (`end_reason = 'closed'`) always needs `--handle`. Select the single owner that is not ended or ended `closed`;
  `finished` and `handed_off` owners are not resumable.
  Fixed: owners not ended or ended `closed` are resumable without `--handle`; tests cover `closed` and `finished`.
- [x] **R12 — MEDIUM — native** — `.agents/machine/scripts/session_store.py:196`
  `start_session` clears `ended_at`/`end_reason` but keeps `role = 'owner'`, so a handed-off predecessor that is
  resumed becomes a second live owner. When the previous end reason was `handed_off`, clear its role.
  Fixed: `start_session` clears `role` when the previous end reason was `handed_off`; tests cover both cases.
- [x] **R13 — MEDIUM — native** — `.agents/machine/scripts/work_item_sessions.py:184`
  `claim` reads live owners and then sets ownership outside a transaction, so two concurrent claims can both become
  owner. Wrap the check and the update in one `BEGIN IMMEDIATE` transaction.
  Fixed: claim's owner check and write run in one `BEGIN IMMEDIATE` transaction; a two-thread test fails without it.
- [wontfix] **R14 — LOW — native** — `.agents/machine/scripts/work_item_sessions.py:188`
  `--predecessor` takes ownership from a live owner without a `handing-off` state.
  Disposition: intended by the approved spec ("A predecessor's ownership transfers with `handed_off` and `successor`
  set"); `engineering:handoff` requires the predecessor to stop owned-path writes before launching its successor, so
  the transfer does not create a second writer.
- [x] **R15 — MEDIUM — native** — `.agents/machine/scripts/session_store.py:136`
  `_normalise_remote` keeps only the last two path segments, so one Azure DevOps repository gets different identities
  over HTTPS and SSH, and repositories on different hosts collide. Include the host and the full path, mapping
  `ssh.dev.azure.com:v3/<org>/<project>/<repo>` to `dev.azure.com/<org>/<project>/_git/<repo>`.
  Fixed: identity is lowercase host plus path; GitHub forms and Azure DevOps SSH/HTTPS unify; tests cover collisions.
- [x] **R16 — LOW — native** — `.agents/machine/scripts/work_item_sessions.py:176`
  `--role` is not validated, so `Owner` or `owner ` bypasses the single-owner rule. Accept only `owner` or
  `bounded: <non-empty scope>`.
  Fixed: `_validate_role` accepts only `owner` or `bounded: <scope>` before any write; tests reject variants.
- [x] **R17 — LOW — native** — `.agents/machine/scripts/session_store.py:107`
  `_git` decodes output with `text=True` and no encoding, against `CODE_CONVENTIONS.md`; non-ASCII output can raise
  outside the handled exceptions. Pass `encoding="utf-8", errors="replace"`.
  Fixed: `_git` passes `encoding="utf-8", errors="replace"`; test asserts the arguments.
- [x] **R18 — MEDIUM — native** — `.agents/machine/scripts/work_item_sessions.py:182`
  `claim` from the default branch records it on the work item, after which every unclaimed session on that branch
  auto-attaches to the item. Do not record the repository's default branch (`origin/HEAD`, else `main`/`master`).
  Fixed: claim does not record the default branch (origin/HEAD, else main/master); tests cover both branches.
- [x] **R19 — LOW — native** — `.agents/machine/utility/peer-cli/scripts/finish.py:12`
  `_record_own_end` is duplicated in `close.py` and `finish.py`. Move it into the shared `session_close.py`.
  Fixed: one `_record_own_end` in `session_close.py`; finish and close now record before spawning the observer and reopen on refusal (`reopen_session`), keeping the armed window as on main.
- [x] **R20 — MEDIUM — native** — `.agents/machine/scripts/session_store.py:157`
  Each SessionStart/Stop hook runs three to four `git` subprocesses with 3-second timeouts; on Codex, SessionStart
  shares a 7-second deadline with three other hooks. Collapse the probes into one `rev-parse` call plus the remote
  lookup with a shorter timeout.
  Fixed: hook paths use one combined `rev-parse` plus the remote lookup with a 2 s timeout; test asserts at most two git calls.
- [x] **R21 — MEDIUM — workflow** — `.agents/plugins/harness/machine.json:301`
  The Codex justification calls `interrupted` read-only, but `interrupted --resume` reopens sessions like `resume`.
  State that `--resume` performs the same guarded reopen, limited to rows confirmed dead on this machine (mirror in
  `catalog.json`'s harness field).
  Fixed: justification states `interrupted --resume` and `resume` perform the guarded reopen; mirrored in `catalog.json`; `sync_harness_manifests.py --check` passes.

## Review pass — 2026-10-13 — incremental

**Candidate base:** `67b45a87b390a722727dc6f428ff08922113b238`
**Candidate head:** `3df86558f1dfb2193989cd6db054d8596ffb64a3`
**Candidate branch:** `Feature/WorkItemSessions`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:586570d98298965c232fa061a28417a1503ff89c34691ea1beb67ff9d2af8bc7` `(16 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\64gSe6piqVGbjP6v6C6hB4\_OPV8coGTPixhNEBpA_S9k`
**Candidate bundle identity:** `sha256:a83ed0e2732ddd9d740a78d724851b6dcafeae49b5587cbcad4f2fe66a6084ae`
**Work-order path:** `reviews/Feature-WorkItemSessions.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Native layer: Claude Code `code-review` skill (high). Lens: `workflow` (`review-lens`). The lens's report that removing the
2026-10-12 coverage record was improper is not retained: `base:plan-artifacts` keeps one moving coverage record per
work order and the host check rejects a second one.

### Findings

- [x] **R22 — MEDIUM — native, workflow** — `.agents/machine/scripts/work_item_sessions.py:219`
  Inside claim's `BEGIN IMMEDIATE`, `transfer_ownership` calls `end_session`, which commits and releases the lock before
  `set_session_ownership`, so a concurrent claim can take ownership in the gap and a failure leaves no owner. Move claim
  and handoff into one store function whose statements share a single transaction with no inner commits.
  Fixed: `session_store.claim_work_item` runs the owner check, handoff, demotion and ownership write in one `BEGIN IMMEDIATE` transaction with no inner commits; tests cover concurrent handoff claims and rollback.
- [x] **R23 — MEDIUM — native** — `.agents/machine/scripts/work_item_sessions.py:302`
  Claim never demotes an earlier owner that ended `closed`, so after close, reclaim and close, `resume` without
  `--handle` sees two owners. Keep at most one `role = 'owner'` row per work item: a claim demotes every other owner row
  in the same transaction.
  Fixed: every successful owner claim clears `role` on all other owner rows for the work item; close-reclaim-close then `resume` selects the latest owner.
- [x] **R24 — MEDIUM — native** — `.agents/machine/scripts/session_store.py:228`
  A former owner ended `closed`/`finished` that is resumed with `--handle` comes back as a second live owner; only the
  `handed_off` case clears its role. The single-owner-row rule (R23) removes this; handoff also demotes the predecessor.
  Fixed: demoted and handed-off owners lose `role`, so a resumed former owner is not an owner; tested through SessionStart.
- [x] **R25 — MEDIUM — native** — `.agents/machine/scripts/work_item_sessions.py:356`
  `interrupted --resume` reopens without the worktree staleness check that `resume` applies, contrary to the
  auto-approval justification. Resume only rows whose read-time status is `closed`.
  Fixed: `interrupted` lists each row's read-time status and `--resume` refuses any handle that is not `closed`.
- [x] **R26 — LOW — native** — `.agents/machine/scripts/session_store.py:154`
  The combined `rev-parse HEAD … --git-common-dir` probe fails as a whole on an unborn HEAD, losing the repository
  identity. Fall back to `--git-common-dir` and `symbolic-ref -q HEAD` when the fast probe fails.
  Fixed: the fast probe falls back to `rev-parse --git-common-dir` and `symbolic-ref -q HEAD` on an unborn HEAD; tested.
- [x] **R27 — LOW — native** — `.agents/machine/scripts/session_store.py:161`
  `--abbrev-ref HEAD` can return `heads/<name>` for an ambiguous name, which never equals `branch --show-current`, so
  the row stays stale. Record the branch from `--symbolic-full-name HEAD` with `refs/heads/` stripped, and compare the
  same form.
  Fixed: branches come from `--symbolic-full-name HEAD` with `refs/heads/` stripped; a tag/branch name clash stays non-stale.
- [x] **R28 — MEDIUM — native** — `.agents/machine/scripts/work_item_sessions.py:386`
  `item` creates a work item with the default branch recorded, re-enabling cross-attachment of default-branch sessions.
  Apply the default-branch rule wherever a work item's branch is written.
  Fixed: `_branch_to_record` drops the default branch for both `item` and `claim`.
- [x] **R29 — LOW — native** — `.agents/machine/scripts/work_item_sessions.py:209`
  An item first claimed on the default branch keeps `branch = NULL` after a later claim from its feature branch, so
  auto-attach never works. Set the branch on claim when it is NULL and the current branch is not the default.
  Fixed: `claim` fills a NULL work-item branch from a non-default branch (`set_work_item_branch_if_unset`).
- [x] **R30 — LOW — native** — `.agents/machine/scripts/work_item_sessions.py:162`
  A live session reports its worktree status (`stale`/`unknown`) instead of `live`, inviting a competing owner. Report
  `live` for a live session; staleness applies only to resumable rows.
  Fixed: a live session reports `live` regardless of its worktree.
- [x] **R31 — LOW — native** — `.agents/machine/scripts/session_store.py:141`
  Legacy Azure DevOps remotes (`<org>.visualstudio.com/<project>/_git/<repo>`, `vs-ssh.visualstudio.com:v3/...`) are not
  unified with `dev.azure.com`, and the path is not case-folded as documented. Map both to
  `dev.azure.com/<org>/<project>/_git/<repo>` and lowercase the identity.
  Fixed: legacy `visualstudio.com` HTTPS and `vs-ssh.visualstudio.com` SSH remotes map to `dev.azure.com/<org>/<project>/_git/<repo>`; the identity is fully case-folded.

## Review pass — 2026-10-13 — incremental

**Candidate base:** `3df86558f1dfb2193989cd6db054d8596ffb64a3`
**Candidate head:** `6c4ed0790ea2f1fec7f822292e1ae88238aadeb0`
**Candidate branch:** `Feature/WorkItemSessions`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:173d86c49119bd50cc9887af969df8e5c47d8eb6eef7f84bfcc2af2606d504a1` `(6 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\gvhOkh2MkGpNt3qgK4DxNQ\ycwTrZGtyQ_P8r0Jet12j-`
**Candidate bundle identity:** `sha256:93379fd384bf760b602c4ab90dc03a9a7417b39af40881e432eaa1efcad26eae`
**Work-order path:** `reviews/Feature-WorkItemSessions.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Native layer: Claude Code `code-review` skill (high). Lens: `workflow` (`review-lens`). Not retained: a migration for the
case-folded repository key — `sessions.db` has never shipped, so no recorded rows exist to migrate.

### Findings

- [x] **R32 — MEDIUM — native** — `.agents/machine/scripts/work_item_sessions.py:172`
  `_read_time_status` returns `closed` for rows ended `finished` or `handed_off`, so `resume --handle` (and the R25 gate)
  can reopen a handed-off session beside its live successor in the same worktree. Report those rows as `finished` /
  `handed_off` so only `closed` rows resume.
  Fixed: ended rows report `finished`/`handed_off`; only `closed` resumes; tests refuse a handed-off predecessor and a finished session.
- [x] **R33 — MEDIUM — native** — `.agents/machine/scripts/work_item_sessions.py:216`
  `set_work_item_branch_if_unset` commits before `claim_work_item` and runs for every claimer, so a refused owner claim
  or a bounded helper permanently sets the work item's branch. Fill the branch inside `claim_work_item`'s transaction,
  only for a successful owner claim.
  Fixed: `claim_work_item` fills a NULL branch in its own transaction, only on a successful owner claim; refused and bounded claims leave it unchanged.
- [x] **R34 — LOW — native** — `.agents/machine/scripts/session_store.py:413`
  The single-owner rule lives only in `claim_work_item`. Add a partial unique index on `sessions(work_item)` where
  `role = 'owner'` so the database enforces it.
  Fixed: partial unique index `idx_sessions_one_owner_per_work_item`; schema creation is idempotent; a second owner row raises `IntegrityError`.
- [x] **R35 — LOW — native** — `.agents/machine/scripts/session_store.py:157`
  Short legacy remotes `https://<org>.visualstudio.com/[DefaultCollection/]_git/<repo>` (project named after the
  repository) normalise to nothing and fall back to the local path. Map them to
  `dev.azure.com/<org>/<repo>/_git/<repo>`.
  Fixed: short `visualstudio.com/[DefaultCollection/]_git/<repo>` maps to `dev.azure.com/<org>/<repo>/_git/<repo>`; tested.
- [x] **R36 — LOW — native, workflow** — `.agents/machine/scripts/session_store.py:181`
  The unborn-HEAD fallback also runs after a non-repository cwd or a timeout, and runs `symbolic-ref` even when
  `--git-common-dir` failed, doubling hook git work. Fall back only on a non-timeout failure and skip `symbolic-ref`
  without a common dir.
  Fixed: no fallback after a timeout, and `symbolic-ref` only runs when `--git-common-dir` succeeded; tested.
- [x] **R37 — LOW — native** — `.agents/machine/scripts/work_item_sessions.py:340`
  `interrupted` computes each row's read-time status (process table plus git) and recomputes it for every `--resume`
  handle. Compute once per row and reuse it.
  Fixed: `interrupted` computes each row's status once and reuses it for `--resume`; tested.
- [x] **R38 — LOW — native** — `.agents/machine/scripts/work_item_sessions.py:386`
  `item --status` on an existing item with a NULL branch never fills it from a non-default branch. Apply the same
  branch fill as `claim`.
  Fixed: `item --status` fills a NULL branch from a non-default branch in the same update; tested.
- [x] **R39 — LOW — native** — `.agents/machine/scripts/session_store.py:403`
  The new `claim_work_item` and `_collect_repo_branch_head` docstrings narrate design and behaviour, against the global
  no-comment rule; the test's `# noqa` explanation likewise. Remove them.
  Fixed: narration docstrings removed; tests keep a bare `# noqa: BLE001`.
- [x] **R40 — LOW — native** — `.agents/machine/scripts/work_item_sessions.py:213`
  `claim` resolves repository, branch and HEAD twice. Resolve them once and reuse the result.
  Fixed: `claim` and `item` resolve repository, branch and HEAD once through `_require_repo_branch_head`; tested.

## Review pass — 2026-10-13 — incremental

**Candidate base:** `6c4ed0790ea2f1fec7f822292e1ae88238aadeb0`
**Candidate head:** `e0b1d0da0ea57c374689c08a8f67b6d625861553`
**Candidate branch:** `Feature/WorkItemSessions`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:d6dbba39967b6ecd666f368f01c662515abcda56762fb42d5156938af0ecaf06` `(7 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\0sxD8Dhd9yeoJk9pjyNG5n\MpyOmenC9dggy9M-WIAPxD`
**Candidate bundle identity:** `sha256:4aa82a0185895940b4e045fadf6ae1399eedc6404eabd3e28ae76ccf76a315a3`
**Work-order path:** `reviews/Feature-WorkItemSessions.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Native layer: Codex `codex review` (medium; no findings emitted). Workflow review: parent fallback. No security-sensitive paths.

### Findings

- [x] **R41 — MEDIUM — workflow** — `.agents/machine/scripts/session_store.py:91`
  A database created before the unique-owner index can contain duplicate `owner` rows from the earlier close/reclaim bug. Creating the index before reconciling those rows makes every later `connect` fail with `UNIQUE constraint failed`. Deduplicate existing owner rows in a schema migration before creating the index, retaining the most recently active owner.
  Fixed: schema v2 demotes older duplicate owners before creating the unique index; a migration test retains the most recently active owner.

## Review pass — 2026-10-13 — incremental

**Candidate base:** `e0b1d0da0ea57c374689c08a8f67b6d625861553`
**Candidate head:** `a5d3787acaf8f664e6a8dc2cfc47153e013ef309`
**Candidate branch:** `Feature/WorkItemSessions`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:93394ee3efcbce9c8c33e3adda1e30bbe766710154720e0200e9b863b22abf69` `(4 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\0sxD8Dhd9yeoJk9pjyNG5n\yiUr3cyoeZR8GhpotAAJtD`
**Candidate bundle identity:** `sha256:ec00d3dc18d4ce7b20909b53db6fbbcf0e5320acec7cf000a50e66e2c4033e7a`
**Work-order path:** `reviews/Feature-WorkItemSessions.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Native layer: Codex `codex review` (high). No security-sensitive paths.

### Findings

- [x] **R42 — MEDIUM — native** — `tests/test_session_store.py:73`
  The legacy migration test opens SQLite beneath a directory that does not exist, so the suite fails before exercising the migration.
  Fixed: the fixture creates its database parent before opening SQLite.
- [x] **R43 — HIGH — native** — `.agents/machine/scripts/session_store.py:91`
  Concurrent legacy migrations can use a stale keeper after another connection hands ownership to a successor, leaving no owner.
  Fixed: schema setup holds `BEGIN IMMEDIATE` through migration, index creation and the version update; the regression test asserts the transaction precedes schema reads.

## Review pass — 2026-10-13 — incremental

**Candidate base:** `d15375a3749f01c927921b2860df5c99650d080b`
**Candidate head:** `b83ac4e41b885b2f73c3526c255908d29024aef1`
**Candidate branch:** `Feature/WorkItemSessions`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:77926010de35b0789c389620a480a992f8e413a0161ffe6150ab966c8d84eef5` `(51 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\0sxD8Dhd9yeoJk9pjyNG5n\t_3o0dKowfuSnJxBcVfRYW`
**Candidate bundle identity:** `sha256:cbf02173bd997e24f8c9d09ee65023575576f6faa8c3ca44d7dcd763b0be94e1`
**Work-order path:** `reviews/Feature-WorkItemSessions.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Native layer: Codex `codex review` (high). Fresh lenses: `data-migration`, `api-contract`, `workflow`. No security-sensitive paths.

### Findings

No retained findings. The native reviewer identified four Claude standards-sync issues inherited from `origin/main`; they are unchanged in the PR diff against its current base and outside this S1 review scope. Focused inherited-change suites passed 27, 23, 31 and 23 tests.

## Review pass - 2026-10-13 - incremental

**Candidate base:** `b83ac4e41b885b2f73c3526c255908d29024aef1`
**Candidate head:** `ba74c9c932e200a049c92c7a3488930c52a12d57`
**Candidate branch:** `Feature/WorkItemSessions`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:5757171c929dbe6a7906548e345d03882d9ffaf7a6e3eb2a388dc61fbff8d0cd` `(22 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\0sxD8Dhd9yeoJk9pjyNG5n\GhT9-uEB_wdDRYBLK2g-mW`
**Candidate bundle identity:** `sha256:e9bcec53f4c08830e46d10af0d1a1e87c52bf6c4f01a8fbc3999ffe5d3d64821`
**Work-order path:** `reviews/Feature-WorkItemSessions.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Native layer: Codex `codex review` (high). No security-sensitive paths.

### Findings

No retained findings. This is the current-main merge required to refresh the review basis; the imported changes are not part of the PR's authored S1 diff.

## Review pass - 2026-10-13 - incremental

**Candidate base:** `b83ac4e41b885b2f73c3526c255908d29024aef1`
**Candidate head:** `ba74c9c932e200a049c92c7a3488930c52a12d57`
**Candidate branch:** `Feature/WorkItemSessions`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:5757171c929dbe6a7906548e345d03882d9ffaf7a6e3eb2a388dc61fbff8d0cd` `(22 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\0sxD8Dhd9yeoJk9pjyNG5n\GhT9-uEB_wdDRYBLK2g-mW`
**Candidate bundle identity:** `sha256:e9bcec53f4c08830e46d10af0d1a1e87c52bf6c4f01a8fbc3999ffe5d3d64821`
**Work-order path:** `reviews/Feature-WorkItemSessions.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Native layer: Codex `codex review` (high). No security-sensitive paths.

### Findings

No retained findings. This is the current-main merge required to refresh the review basis; the imported changes are not part of the PR's authored S1 diff.


