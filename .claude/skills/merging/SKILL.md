---
name: merging
description: Landing a PR safely through a GitHub merge queue — bring the branch current with base before enabling auto-merge (a behind branch either sits BLOCKED forever or merges code never built against current base), then confirm the outcome with one capped background poll loop that emits transitions only and resolves to exactly one of four terminal states (merged, a failed check, conflicted-so-auto-merge-was-silently-disabled, or green-but-never-admitted), never retrying or toggling a genuine failure, never swallowing poll errors, and telling a failed merge-queue run apart from the re-evaluation glitch by inspecting `merge_group` runs rather than PR state; plus owning only the generated downstream version-bump PR causally produced by that merge, never a pre-existing or superseding PR. Use after enabling auto-merge, when a PR seems stuck, when a merge-queue run fails, or before starting new work on a possibly-broken base.
domain: process
---

# Merging

## Persistent continuation

When a queue, check, publication, or generated sync will resolve after this turn, enter the current harness's
persistent-workflow skill. It reads persistent-delivery, binds this exact PR/head/worktree and uses the native
continuation mechanism. That owner classifies a real failure by test tier, dispatches its corresponding debug
skill in a fresh context, rebinds after a push, obtains the required review, and reaches merge only under
explicit authorization. The background-loop fallback below is
for a foreground turn with no persistent host capability; it does not provide cross-restart continuation.
## The branch MUST be current with base before auto-merge is enabled

Enabling auto-merge on a branch that is behind base is the miss never to repeat. GitHub either holds the PR
`BLOCKED`/`BEHIND` — so it silently never merges — or it merges code that was **never built against current
base**. Update first, then enable, always. Run it in the branch's **own** checkout or worktree; a session
sitting in the wrong checkout is exactly how the staleness goes unnoticed.

```bash
git fetch origin --quiet
behind=$(git rev-list --count HEAD..origin/main)
[ "$behind" -gt 0 ] && { echo ">>> $behind commits behind main — update before enabling auto-merge"; \
  git merge origin/main --no-edit && <rebuild affected projects to 0 errors> && git push; }
# only when $behind is 0 AND the rebuild is green → gh pr merge <PR> --auto
```

A branch that is behind also risks a stale pinned dependency version; merging base brings the current pin with
it, so updating first keeps that correct too.

## Confirm the outcome with a token-efficient, transition-only monitor

Use [`remote-validation`](../remote-validation/SKILL.md)'s no-model-polling rule. Prefer the harness's
notification, webhook, `Monitor` or recurring-listener primitive for a long merge wait. Bind it to the exact
PR and run identifiers, query no more than once a minute, **emit only when the state tuple changes**, and cap
its lifetime. When it wakes, perform one direct GitHub read before acting; the listener is the efficient
notification mechanism, while the direct read is the authoritative terminal-state confirmation.

If the harness has no notification primitive, use one equivalent long-lived background shell loop. That one
process owns every query and sleep internally; park the agent on it with the longest available tool wait.
**Never wake a model at the poll interval merely to wait on the process again.** An
unchanged observation is neither progress nor a reason to narrate, restart the monitor, poll its tool handle,
or issue another interactive query. The monitor **never retries and never toggles**: a failed check is a real
failure to surface and debug, not something to poke.

1. **Merged** — report the landing sha and stop.
2. **A check failed** — report the failing job, point at the run log, and **stop. Do not retry**; re-running a
   genuinely failing suite just fails again. When persistent delivery owns the wait, bind the exact run head
   and bound PR source head, classify the tier, and immediately dispatch one fresh debugging context with the
   corresponding debug skill and complete failure evidence. In the foreground fallback with no persistent
   host capability only, hand off to a dedicated debugging session with a ready-to-paste
   dispatch prompt: worktree path, branch, PR, failing scenarios, and the failure signature. Emit it as soon as
   the failure is obviously genuine (deterministic, in the changed area); only an environment-signature failure
   — the whole suite dead at startup — waits for a fresh-stack re-run before dispatch.
3. **Conflicted mid-wait** — base moved while you waited, the PR went `DIRTY`, and **GitHub silently disabled
   auto-merge when it did.** Nothing is wrong with the work and nothing is retrying; the PR simply stopped
   being enqueued. This is the state that looks most like "still waiting" and is the easiest hour to lose.
   Update the branch, rebuild, push, and re-arm auto-merge.
4. **Green but never admitted** — the PR is `CLEAN`, every check passes, auto-merge is on, and GitHub never
   adds it to the queue. That is an auto-merge **re-evaluation glitch** (enabled while checks were pending,
   then never looked at again), **not** a test failure. The remedy is a **one-time** action: re-assert
   auto-merge once (disable then re-enable) or break-glass admin-merge. Never an automated loop.

**Telling state 2 from state 4 requires inspecting the actual run results, not just PR state — this is the
trap.** After a `merge_group` run fails, GitHub ejects the PR back to `OPEN`/`CLEAN`/not-queued, which looks
**identical** to the never-admitted glitch. The failure lives on the merge-queue's own
`gh-readonly-queue/...pr-<N>-...` run, not on the PR head's checks, so a PR-checks query alone will not show
it. The loop must also scan `merge_group` run conclusions for this PR: a failed one means state 2 (debug it);
none ever dispatched means state 4 (nudge it once). Conflating them is how a real failure gets mistaken for a
stall, and vice versa.

**Never swallow poll errors.** A `2>/dev/null || continue` makes a broken CLI look identical to "still
waiting". Capture stderr and surface the failed query as a terminal polling error. Keep the last complete
state tuple, emit the next one only when it differs, and **cap** the loop so a persistent failure surfaces
instead of hanging forever. User-facing updates follow the same rule: transitions, failures and the terminal
outcome only — never a transcript of unchanged polls.

Read **five** signals every poll, never fewer, for the **same PR recorded at entry**: the PR's bare `state`;
its merge-state status (a `DIRTY` value is state 3); whether an auto-merge request is still attached; whether
the merge queue actually holds an entry for it (no entry is what makes state 4 recognisable); and the
conclusions of the merge queue's own runs (what makes state 2 recognisable). Read the state and the merge-state
status into **separate** variables — a joined string never matches `MERGED`, so the loop times out instead of
reporting the merge.
An adjacent queue entry, a similarly named branch or a newer PR never silently becomes the target.

The runnable loop lives in [`merge`](../merge/SKILL.md), the executable counterpart of this doc, which
resolves the repo's own slug and check names at run time rather than naming them. A second copy
here would be the drift this corpus exists to prevent.

## Whoever merges owns only the generated downstream PR that merge caused

Where a merge triggers a package republish and an automated version-bump PR across consumers, that causally
linked PR is part of the merge, not an afterthought. **Ownership is causal, not topical:** prove the publish
run was triggered by the landing commit, then identify the sync from that run's recorded version, branch or PR
metadata. A name such as `platform-sync`, being open at the same time, or touching the same consumers proves
nothing.

- **Non-breaking → it auto-merges green in minutes. Breaking** — a published type moved and a consumer no
  longer compiles against the new pin — **→ it goes red, and until it is fixed every consumer is stranded on a
  broken pin.**
- **A pre-existing generated PR is out of scope.** Healthy, pending or already automation-owned, it is not a
  prerequisite for the selected PR and must not be reviewed, labelled, enqueued, waited on or otherwise
  mutated. The only repository-wide exception is the explicit branch-time check for an **open red** sync
  below.
- **Follow only the causally linked PR to green or merged.** If it is red, migrate the failing consumers **in
  that PR** (legal now: the new version is on the feed), build to zero errors, and push. **Never leave a red
  sync PR behind.**
- **Leave healthy automation alone.** When the generated PR's own workflow promises to validate and
  auto-merge it, do not add a manual review, re-arm it speculatively or merge it by hand. Intervene only after
  the causally linked publication, checks or auto-merge actually fail.
- **Supersession transfers ownership.** If a later publish from an unrelated landing closes or replaces the
  sync being followed, verify that provenance and stop. The later producer owns its replacement; do not adopt
  the new PR and turn one delivery into an unbounded chase through the queue.
- **Before branching for new work, confirm no open red sync PR** — don't build on a mid-break platform. That is
  a branch-time check, not a per-prompt one.
- Back it with automation that opens a tracking issue and labels the PR the moment a sync goes red, so a broken
  sync cannot rot unnoticed when a merge bypassed the normal path.

## No workflow arms merge automation on an ordinary PR

Marking a PR ready for review changes its review state, not its merge authorization. **No CI workflow may
enable auto-merge or merge an ordinary PR in response to a PR lifecycle event** — `opened`, `reopened`,
`synchronize`, or `ready_for_review`. Only an explicit merge instruction starts the delivery. The one
exception is a repository-owned **generated** PR — the `platform-sync`/version-bump kind above: its own
workflow may arm auto-merge for itself as part of the already-authorized producer chain, and that scoped
automation must never generalise to ordinary PRs.
