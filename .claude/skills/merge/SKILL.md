---
name: merge
description: Land the current branch's PR through the merge queue and return to a clean, current base — confirm the PR's own checks are terminal and green, select the end-to-end tier mechanically from whether the diff can break behaviour the hard floor cannot observe, enqueue with auto-merge, poll a capped background loop to one of four terminal states, close the merged worktree, then follow the publish and version-sync consequence to green or migrate its broken consumers. Covers why a queue-gated suite reporting "skipping" on the PR is expected rather than proof it passed, why the admin bypass skips the suites entirely and when it is legitimate, why a skip trailer silently loses to a mandated attribution trailer, and the plan-ledger checkpoints each transition owes. Use whenever the user says merge, merge it, land this PR, or wants the current branch shipped and the repo reset to its base.
domain: process
---

# Landing a PR through the merge queue

The executable counterpart of [`merging`](../merging/SKILL.md): one pass that takes the current branch's PR
from green to landed and leaves the workstation on a clean, current base ready for the next task. `merging`
owns *why* — the currency rule, the four terminal states and the trap that hides one behind another, the
downstream-sync ownership. This owns *how*, including the runnable loop that doc deliberately delegates here
because only an executable procedure can resolve the repo's own slug and check names.

Resolve those mechanically rather than carrying them as configuration. The slug is
`gh repo view --json nameWithOwner`; the check set is whatever `gh pr checks` reports on the PR in front of
you; the queue's own configuration is `gh api repos/{owner}/{repo}/rulesets`. A procedure that names them is a
procedure that goes stale in the repo that renames one.

## What a merge queue changes about reading a PR

- **The queue is the merge path, and it rebuilds every entry on current base.** Its single required check is
  an aggregate that accepts skipped dependencies and reports one result, so jobs with no work are skipped
  before a runner is allocated and still satisfy the gate.
- **A green PR is not proof the required end-to-end suites passed.** Suites gated on `merge_group` report
  **`skipping`** on the PR itself — expected, not a failure. They run *after* you enqueue, inside the merge
  group. Only the queue proves them.
- **`--auto` enqueues; it does not merge.** It returns immediately and the merge lands later, so observe the
  outcome through persistent-workflow when it must outlive this turn, or the foreground listener procedure below; never assume it landed. A full end-to-end merge
  is tens of minutes, and waiting for it must not keep the model running.
- **`--admin` is an escape hatch, not the default.** It force-merges immediately and **bypasses the queue,
  which means the required suites do not run at all.** Use it only when the user explicitly asks to skip the
  queue — a meta-only diff with zero runtime impact ([`merge-docs`](../merge-docs/SKILL.md) is that case as its own
  flow), or a wedged queue. Never because the queue is slow. **Skipping a suite is not the same as skipping
  the queue:** to run less, apply the tier label below and enqueue normally so the hard floor still builds
  against current base.
- **`--delete-branch` is rejected while a queue is enabled.** Delete the branch separately, after it lands.

## Steps

### Scope lock — one source PR and only the automation it causes

Record the current branch's PR number and remote head at entry and keep that delivery identity through the
whole procedure. Do not adopt an adjacent queue entry, a pre-existing generated PR, or a newer similarly named
PR. Step 6 may widen the identity only after proving a publish run was triggered by this PR's landing commit;
[`merging`](../merging/SKILL.md) owns that causal boundary.

### 0. Review first — code or docs, by what the diff touches

Confirm the PR has been reviewed before querying, pushing or merging it. **Which review depends on the diff:**
a meta-only PR (the path list in [`merge-docs`](../merge-docs/SKILL.md)) gates on
[`docs-review`](../docs-review/SKILL.md), not a code review, and normally lands through that flow rather than
this one; a pure close-out — net diff deletions only — is exempt, which that doc states. Any runtime,
product, package or test-selection path makes it a code PR and requires
[`review`](../review/SKILL.md), or [`big-review`](../big-review/SKILL.md) when the branch is
too large for one pass. Commits added after the review require
[`incremental-review`](../incremental-review/SKILL.md). **Do not proceed while findings remain open.**

**The gate is hook-enforced, and every harness names the checkout in the merge command.**
`.agents/hooks/merge_review_gate.py` (PreToolUse) blocks the agent's merge command until the branch's review
file is current and clean. Codex does not expose an `exec_command` workdir override to hooks, so the merge
procedure never asks the hook to infer one from shell text. Record the worktree's absolute path and use the
single cross-shell envelope shown in Step 4: `pushd "<absolute-worktree>" && gh pr merge <n> ...`. It works
under Bash, cmd and PowerShell, pins the checkout before `gh` runs, and gives Codex one deliberately narrow
target-proof contract. Claude also resolves the checkout from that envelope, retaining its legacy
`cd`/payload-cwd behavior only for compatibility when the envelope is absent. A Codex merge outside
that exact envelope fails closed; simplify the command instead of adding another shell spelling or
asking the user to bypass the hook.

### 1. Find the PR for the current branch

```bash
git rev-parse --abbrev-ref HEAD                 # must not be the default branch
gh pr view --json number,state,title,url --jq '{number,state,title,url}'
```

On the default branch, or with no PR for this branch, **stop** — there is nothing to land
([`open-pr`](../open-pr/SKILL.md) opens one). Already `MERGED` → skip to step 5. `CLOSED` → stop and report.

### 2. Prove the branch is pushed, current with its remote, and current with base

[`merging`](../merging/SKILL.md) owns the rule; two mechanical traps belong here.

- **Uncommitted executable changes, or local ahead of remote → stop** and say so. Do not land a PR that is
  missing local work. A local review artifact may remain as the merge gate; there is no checkpoint-transport
  tail because the push protocol forbids one.
- **`git status -sb` is not a base check.** Its `[ahead N, behind M]` compares against the branch's *own*
  remote, so a branch reads "in sync" while sitting dozens of commits behind base:

  ```bash
  git fetch origin --quiet
  git rev-list --left-right --count origin/main...HEAD   # -> "<behind-base>	<ahead>"
  ```

  Behind by anything → merge base in (never rebase: the PR is up for review, so no force-push), resolve
  conflicts — the version pin file is the usual one — rebuild the affected projects to zero errors, and push.
  This is **non-negotiable when a version-bump PR has landed on base since this branch forked**
  (`git log --oneline origin/main ^HEAD | grep chore/platform-sync`): the branch is pinned to an older
  platform version, so it builds against a stale one. The queue rebuilds on base, but real pin or shape drift
  surfaces there as an ejection instead. Update, run the smallest affected build, push, and require exact-head
  CI before continuing.

### 3. Wait for the PR's own checks to reach a terminal state, then verify green

Wait until no check is `pending` using the token-efficient monitor procedure in
[`merging`](../merging/SKILL.md), then confirm the terminal state with one direct `gh pr checks` read. Where
the harness has no monitor primitive, use this capped background-shell fallback:

```bash
max=60; i=0
while true; do i=$((i+1)); rc=0; out=$(gh pr checks <n> 2>&1) || rc=$?
  case "$rc" in 0|1|8) ;; *) echo "POLL ERROR: $out"; exit 5;; esac
  pend=$(echo "$out" | awk -F'\t' '$2=="pending"' | wc -l)
  fail=$(echo "$out" | awk -F'\t' '$2=="fail"'    | wc -l)
  if [ "$fail" -gt 0 ]; then echo "FAILED"; echo "$out" | awk -F'\t' '$2=="fail"{print $1}'; break; fi
  if [ "$pend" -eq 0 ]; then echo "ALL-TERMINAL"; break; fi
  [ "$i" -ge "$max" ] && { echo "CHECK TIMEOUT after $max polls"; exit 1; }
  sleep 60; done
```

The loop is intentionally silent while nothing changes. It runs as one long-lived process: park the agent on
that process with the longest available tool wait, and do not wake the model to poll its handle at the loop's
interval. Do not mirror unchanged observations into chat or run parallel interactive queries against the same
PR.

- **`skipping` on a `merge_group`-gated suite is expected**, per the section above. The PR-level pass set is
  everything else the repo runs on a pull request.
- **Any failure → do not merge.** Report which job failed and route to the debug procedure
  [`failing-tests`](../failing-tests/SKILL.md) names for that tier. Drive it green, push, and start this
  procedure again.
- Verify the complete terminal check set against the exact remote head before routing a failure or enqueueing.
  GitHub owns that evidence: enqueue *that* remote head, not a newer local commit.

### 4. Select the end-to-end tier mechanically, then enqueue

**This step is the single source of truth for the tier.** End-to-end coverage is required **if and only if
the diff can break behaviour the hard floor cannot observe.** Run the full suite when any positive trigger is
present:

- a user-facing browser or UI flow;
- an HTTP/API or cross-service contract;
- a published package's public shape that consumers bind to; or
- auth or routing behaviour observable only end-to-end.

- **Any positive trigger → the suite cannot be skipped.** Remove every skip label, then add the full-tier
  label so it overrides any historical opt-out trailer or label.
- **No positive trigger → add the skip label and remove the full-tier one.** This is the default for
  everything outside the list; never run the suite "to be safe." In particular an internal refactor, a
  call-site relocation, delegation through a new internal collaborator, and a dependency-injection
  re-registration all skip it when the diff changes no wire contract, crosses no service or package
  boundary, and integration tests over the touched path prove identical behaviour.
- **"Wiring" is not an independent trigger.** It means a runtime value or cross-service contract consumers
  bind to — already covered above. Moving an internal registration or call site is not wiring in that sense
  when integration tests boot the real container and HTTP path and prove the behaviour.
- **The hard floor never changes:** every code PR builds, runs its boundary carve jobs, and runs unit plus
  integration tests, and every PR enters the queue on current base. Never skip *those*.
- Labels are read fresh from the PR inside the merge group, so normalize them exactly as above before
  enqueueing. Do not preserve a stale label that contradicts the mechanical decision.
- **A git trailer expressing the same selection works but is fragile — prefer the label.** Git parses only
  the **last paragraph** of a commit message as trailers. Where a repo mandates its own trailer (an
  attribution line, say), a blank line between the two makes them separate paragraphs and the skip trailer is
  no longer seen — so **the queue silently runs the full suite anyway.** `skipping` on the PR is not evidence
  the skip took, because those suites never run on a PR at all; only the label, or a correctly-blocked
  trailer, changes what the *queue* runs.

```bash
pushd "<absolute-worktree>" && gh pr merge <n> --merge --auto
# no --delete-branch: the queue rejects it
```

Verify **actual queue admission** for the recorded PR and remote head. If admission fails or the head moved,
reconcile before the next source update; never push an observation-only commit, and never silently enqueue a
different head.

### 4b. Wait for it to land — the four-state loop

`--auto` only enqueues. Use [`merging`](../merging/SKILL.md)'s token-efficient monitor procedure until one of
its four terminal states resolves, reporting automatically with no reprompt. It **never retries and never
toggles.** Read all five signals every observation, and the bare state into its own variable — a joined string
never matches `MERGED`, which is how a wait times out instead of reporting a merge that already happened.
Where the harness has no monitor primitive, use this background-shell fallback:

```bash
pr=<n>; repo=$(gh repo view --json nameWithOwner -q .nameWithOwner); max=60; i=0; cleanpolls=0; last=''
while :; do i=$((i+1))
  view=$(gh pr view "$pr" --json state,mergeStateStatus,autoMergeRequest \
    -q '.state+" "+.mergeStateStatus+" "+((.autoMergeRequest!=null)|tostring)' 2>&1) \
    || { echo ">>> #$pr polling error (view): $view"; exit 5; }
  read -r st mss auto <<<"$view"
  inq=$(gh api graphql -f query='{repository(owner:"'"${repo%/*}"'",name:"'"${repo#*/}"'"){pullRequest(number:'"$pr"'){mergeQueueEntry{state}}}}' \
    -q '.data.repository.pullRequest.mergeQueueEntry.state // "no"' 2>&1) \
    || { echo ">>> #$pr polling error (queue): $inq"; exit 5; }
  rc=0; prchecks=$(gh pr checks "$pr" 2>&1) || rc=$?
  case "$rc" in 0|1|8) ;; *) echo ">>> #$pr polling error (checks): $prchecks"; exit 5;; esac
  fail=$(printf '%s\n' "$prchecks" | awk -F'\t' '$2=="fail"{print $1}' | paste -sd, -)
  runs=$(gh run list --event merge_group -L 15 --json conclusion,headBranch \
    --jq '.[]|select(.headBranch|contains("pr-'"$pr"'-"))|.conclusion' 2>&1) \
    || { echo ">>> #$pr polling error (merge-group runs): $runs"; exit 5; }
  mgfail=$(printf '%s\n' "$runs" | grep -c failure || true)
  now="$st/$mss|auto=$auto|queue=$inq|pr-fail=${fail:-none}|merge-group-fail=$mgfail"
  if [ "$now" != "$last" ]; then echo "poll $i: $now"; last="$now"; fi
  case "$st" in
    MERGED) echo ">>> #$pr ✓ MERGED"; exit 0;;
    CLOSED) echo ">>> #$pr CLOSED without merging"; exit 0;;
  esac
  if [ "$mss" = DIRTY ]; then
    echo ">>> #$pr ✗ DIRTY — conflicted with base, auto-merge disabled; update+rebuild+push, then re-arm --auto"; exit 4; fi
  if [ -n "$fail" ] || [ "$mgfail" -gt 0 ]; then
    echo ">>> #$pr ✗ CI FAILED (pr:[$fail] merge_group-failures:$mgfail) — inspect the run, do NOT retry"; exit 2; fi
  if [ "$st" = OPEN ] && [ "$mss" = CLEAN ] && [ "$inq" = no ]; then cleanpolls=$((cleanpolls+1)); else cleanpolls=0; fi
  if [ "$cleanpolls" -ge 6 ]; then
    echo ">>> #$pr ⚠ GREEN but unadmitted ~6min (re-evaluation glitch, NOT a failure) — re-assert auto-merge once"; exit 3; fi
  [ "$i" -ge "$max" ] && { echo ">>> #$pr still [$st/$mss] after $max one-minute polls — surfacing"; exit 1; }
  sleep 60
done
```

Run exactly one monitor or fallback loop. Its transition lines and terminal line are the whole progress report;
unchanged polls stay inside that process, stay silent, and never create a model turn or user-facing
update.

- **A failed check dispatches; it does not retry.** When `persistent-workflow` owns the delivery, route the
  exact failed check/run through `persistent-delivery`, classify its tier, and immediately dispatch one fresh
  debugging context with the complete binding and failure signature. Only in the explicit foreground fallback
  with no persistent host capability, emit a ready-to-paste dispatch prompt for a dedicated
  debug session — worktree path, branch, PR, failing scenarios, failure signature — as soon as the failure is
  obviously genuine. Only an environment-signature failure (the whole suite dead at startup) waits for a
  fresh-stack re-run first.
- **If the queue ejects the PR because a suite went red in the merge group**, treat it exactly like any red
  suite: debug it, fix the real bug, push, and run this procedure again. **Never fall back to `--admin` to
  force past a red suite** — that defeats the entire gate. A genuine ejection is a material blocker: record
  the failing run and next fix once, then debug it. Only after the PR is open and unlocked may a stable fix
  candidate create a new remote head.
- Reconcile closed-without-merge, failed checks, sustained green-but-unadmitted, and timeout states before the
  next source update. On merge, retain the result as evidence for the fresh worktree.

### 5. Return to a clean base, and remove the merged worktree immediately

Before removing persistent state, inspect the completed delivery binding. A standalone PR removes its
continuation. A plan-managed binding with a workflow handoff keeps the one existing continuation, closes only
the merged PR binding, checkpoints the merge, and transfers to the recorded `plan-execution` stage. That
stage creates the successor worktree and PR before the same task is rebound to its exact head and runs. Never
carry the completed PR's review watermark or merge authorization into the successor.

```bash
git checkout main && git pull --ff-only origin main
```

From another checkout, close a worktree-developed branch with the repository's own worktree command rather
than by hand. It refuses every unsafe state and handles the platform details — junctions, long paths, Git
administration, branch deletion — and the repository's own docs own that list, so trust the refusal instead
of second-guessing it:

```powershell
./scripts/worktrees.ps1 close -Worktree <path> -PullRequest <n> [-PlanManaged]
```

Add `-PlanManaged` when a plan owns the work. A branch developed in the main checkout has no worktree to
close; apply the same evidence by hand.

If plan work remains, create its next PR-scoped worktree from the updated base and resume the same ledger. If
only remote gates remain, use a fresh close-out worktree.

### 6. Follow the publish and version-sync consequence to a terminal state

[`merging`](../merging/SKILL.md) owns the rule — whoever merges owns only the generated downstream PR that
merge caused, and a causally linked red one is never left behind. The mechanics:

- **Will a sync fire?** A publish runs on any merge that touches **publishable source**, and the version
  bumps every time, so almost every code merge opens a sync PR — most green and auto-merge in minutes.
  Resolve "publishable source" from the repo's own publish workflow's path filter, not from a remembered
  directory name: in a monorepo it is a subtree, in a carved service repo it is the repo. A merge touching
  none of it publishes nothing and you are done.
- **If it did:** find the publish run whose triggering `head_sha` is the merge commit. GitHub owns its
  discovery and terminal evidence. A failed, cancelled, missing or timed-out publication is a material
  blocker; record its run and next action once. Where nothing publishable changed, no ledger entry is owed.
- **If publication succeeded**, identify the sync PR from the publish run's emitted version, branch or PR
  metadata and require that it was created after that run. Never select the first or newest open sync by name;
  any sync that already existed, or whose producer has a different landing sha, is out of scope. Retain the
  exact number, URL, branch, version and initial state, then monitor *its* checks. A pin bump is package-only,
  so the end-to-end suites no-op and the gate is build plus unit plus integration — usually a few minutes,
  using the same token-efficient monitor rule (shell fallback shown):

  ```bash
  sync_branch=<exact-branch-emitted-by-publish>; max=10; i=0
  while true; do i=$((i+1)); rc=0; sp=$(gh pr list --state all --json number,headRefName \
      --jq '.[] | select(.headRefName=="'"$sync_branch"'") | .number' 2>&1) || rc=$?
    [ "$rc" -eq 0 ] || { echo "SYNC DISCOVERY ERROR: $sp"; exit 5; }
    [ -n "$sp" ] && { echo "sync PR #$sp"; break; }
    [ "$i" -ge "$max" ] && { echo "SYNC DISCOVERY TIMEOUT"; exit 1; }; sleep 60; done
  max=60; i=0
  while true; do i=$((i+1)); rc=0; out=$(gh pr checks "$sp" 2>&1) || rc=$?
    case "$rc" in 0|1|8) ;; *) echo "POLL ERROR: $out"; exit 5;; esac
    echo "$out" | awk -F'\t' '$2=="pending"' | grep -q . \
      || { echo "SYNC CHECKS TERMINAL"; break; }
    [ "$i" -ge "$max" ] && { echo "SYNC CHECK TIMEOUT"; exit 1; }; sleep 60; done
  ```

- **Green** → confirm the PR's own automation still owns auto-merge. Do not review it manually, re-arm it
  speculatively or merge it by hand. Record the terminal publication/sync transition at final closeout, not in
  observation-only commits.
- **Superseded by a later unrelated publish** → verify the replacement producer's different landing sha and
  stop. Ownership transfers to that producer; do not follow the replacement and extend this delivery's scope.
- **Red** → **do not walk away.** Read the failing build log, find the broken consumers, and **migrate them in
  that PR** — legal now, the version is on the feed. Check out the sync branch in its **own** checkout, apply
  the fix, run the smallest builds covering every reported consumer, and push; auto-merge lands it once
  exact-head CI greens. The build job may report only the first broken file, so use the replacement PR's CI
  build to discover the rest rather than starting a full local solution build. Record the red state once as a
  blocker, then commit fixes locally, run targeted builds, and make one stable push. GitHub retains replacement
  checks and merge evidence. Never push the source plan's recovery commits to either PR.
- **Close plan-managed delivery from the fresh close-out worktree.** Once publication and sync are terminal,
  record the final transition, delete the plan and ledger, and tick the owning roadmap item in one docs-only
  closeout commit. Review it per [`docs-review`](../docs-review/SKILL.md) — skipped for a pure close-out — and
  land it through [`merge-docs`](../merge-docs/SKILL.md).

## Plan-managed delivery records material boundaries only

Resolve the plan and delivery identity before step 0. During queue observation, GitHub owns checks, admission,
ejection, merge, publication, and sync chronology. Update the ledger only for a genuine blocker or ownership
handoff, a stable fix milestone that will ride its substantive commit, or the final terminal closeout. PR
discovery, labels, successful checks, admission, polling, base sync, and no-op publication observations do not
each create a checkpoint. Never create a commit merely to make the ledger agree with a remote timeline.

## Report

One short report: the PR that merged (number plus merge commit); whether the full suite ran because a
positive trigger was present or was skipped by label because none was; that the base is synced; and that the
branch — and its worktree, if the work was done in one — is cleaned up. For plan-managed work, that the
close-out PR landed and its worktree was removed. Then the sync outcome: **nothing published, sync merged
green at a new version, or sync went red and you migrated its consumers** (which files, now green) — never
"merged, and left a red sync PR behind." If you stopped early, say exactly what is blocking and what is
needed.

Keep it terminal: verify green → enqueue → wait for `MERGED` → remove the worktree → sync the base → follow
the sync PR to green or migrate it → land the plan close-out → remove the close-out worktree → summarize →
stop. No preamble.
