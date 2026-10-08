---
name: merge
description: Land the current branch's PR through the merge queue and return to a clean, current base — confirm the PR's own checks are terminal and green, select the end-to-end tier mechanically from whether the diff can break behaviour the hard floor cannot observe, enqueue with auto-merge, monitor the exact binding to one of four terminal states, close the merged worktree, then follow the publish and version-sync consequence to green or migrate its broken consumers. Covers why a queue-gated suite reporting "skipping" on the PR is expected rather than proof it passed, why the admin bypass skips the suites entirely and when it is legitimate, why a skip trailer silently loses to a mandated attribution trailer, and the plan-ledger checkpoints each transition owes. Use whenever the user says merge, merge it, land this PR, or wants the current branch shipped and the repo reset to its base.

kind: workflow
domain: process
---

# Landing a PR through the merge queue

The executable counterpart of `engineering:merging`: one pass that takes the current branch's PR
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
  queue — a meta-only diff with zero runtime impact (`engineering:merge-docs` is that case as its own
  flow), or a wedged queue. Never because the queue is slow. **Skipping a suite is not the same as skipping
  the queue:** to run less, apply the tier label below and enqueue normally so the hard floor still builds
  against current base.
- **`--delete-branch` is rejected while a queue is enabled.** Delete the branch separately, after it lands.

## Steps

Immediately before every merge attempt, fetch the current PR body and require nonempty What and Why:

```bash
python <workflow-ops> --root <absolute-worktree> --workflow-run-id pr-body-<n> pr-body-check --pr <pr-url>
```

Resolve `<workflow-ops>` to `.agents/workflows/workflow_ops.py` in a source checkout or
`workflows/workflow_ops.py` under the installed engineering package. Repair a failed body check through
`engineering:open-pr`, preserving attribution, then repeat this fresh check before merging. PR body
metadata can change without changing the head; a previous check or delivery binding cannot satisfy it.

### Scope lock — one source PR and only the automation it causes

Record the current branch's PR number and remote head at entry and keep that delivery identity through the
whole procedure. Do not adopt an adjacent queue entry, a pre-existing generated PR, or a newer similarly named
PR. Step 6 may widen the identity only after proving a publish run was triggered by this PR's landing commit;
`engineering:merging` owns that causal boundary.

### 0. Review first — code or docs, by what the diff touches

Confirm the PR has been reviewed before querying, pushing or merging it. **Which review depends on the diff:**
a meta-only PR (the path list in `engineering:merge-docs`) gates on
`engineering:docs-review`, not a code review, and normally lands through that flow rather than
this one; a pure close-out — net diff deletions only — is exempt, which that doc states. Any runtime,
product, package or test-selection path makes it a code PR and requires
`engineering:review`, or `engineering:big-review` when the branch is
too large for one pass. Commits added after the review require
`engineering:incremental-review`. **Do not proceed while findings remain open.**

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
(`engineering:open-pr` opens one). Already `MERGED` → skip to step 5. `CLOSED` → stop and report.

For a manually managed stack, resolve the PR's current base and the stack trunk before enabling merge.
A child targeting an unmerged parent's branch is not eligible: continue the lower layer's delivery and
record that dependency instead of merging the child into the parent. After the parent lands, verify
retargeting/restacking, rerun affected checks and refresh the child's delivery binding. Verified native
stack merging may handle the chain atomically; follow its documented semantics and confirm every layer's
required review and checks. A green persistent-delivery action alone does not override this base gate.

### 2. Prove the branch is pushed and preserve the final-review synchronization

`engineering:merging` owns the rule; two mechanical traps belong here.

- **Uncommitted executable changes, or local ahead of remote → stop** and say so. Do not land a PR that is
  missing local work. A local review artifact may remain as the merge gate; there is no checkpoint-transport
  tail because the push protocol forbids one.
- **`git status -sb` is not a base check.** Its `[ahead N, behind M]` compares against the branch's *own*
  remote, so a branch reads "in sync" while sitting dozens of commits behind base:

  ```bash
  git fetch origin --quiet
  git rev-list --left-right --count <actual-base>...HEAD   # -> "<behind-base>	<ahead>"
  ```

  Before final review, reconcile any movement in the actual base, rebuild the affected scope, push,
  freeze the candidate, and review. A standalone branch may merge `origin/<default>`; a stack child
  follows the verified restacking procedure against its immediate parent. After the review watermark exists, run `workflow_ops.py review-reconcile` against
  its descriptor. Disjoint base-only movement preserves the exact reviewed head and proceeds to merge-group
  validation. Relevant movement, including a platform pin or routed rule change, requires an update, focused
  validation, push, and incremental review.

### 3. Wait for the PR's own checks to reach a terminal state, then verify green

Wait until no check is pending through the reconnect-safe monitor from
`engineering:remote-validation`, then confirm the terminal state with one direct read:

```bash
python .agents/workflows/workflow_ops.py --workflow-run-id <id> monitor --kind pr --id <n> --head <remote-head>
```

Start the command through the host's notification or scheduled-continuation primitive. Reconnect with the
same command after interruption. Do not query its process handle or the forge at the poll interval.

- **`skipping` on a `merge_group`-gated suite is expected**, per the section above. The PR-level pass set is
  everything else the repo runs on a pull request.
- **Any failure → do not merge.** Report which job failed and route to the debug procedure
  `engineering:failing-tests` names for that tier. Drive it green, push, and start this
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

### 4b. Wait for it to land — one reconnect-safe monitor

`--auto` only enqueues. Use `engineering:merging`'s token-efficient monitor procedure until one of
its four terminal states resolves, reporting automatically with no reprompt. It **never retries and never
toggles.** Read all five signals every observation, and the bare state into its own variable — a joined string
never matches `MERGED`, which is how a wait times out instead of reporting a merge that already happened.
Bind the recorded PR and remote head before waiting:

```bash
python .agents/workflows/workflow_ops.py --workflow-run-id <id> monitor --kind pr --id <n> --head <remote-head>
```

Run exactly one monitor through the host's notification or scheduled continuation. Reconnect with the same
identity after interruption. The compact transition or terminal document is the whole progress report;
unchanged observations remain silent and never create a model turn or user-facing update.

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
  next source update. On merge, retain the result as evidence for the next delivery stage.

### 5. Return to a clean base and retire any isolated checkout

Before removing persistent state, inspect the completed delivery binding. A standalone PR removes its
continuation. A plan-managed binding with a workflow handoff keeps the one existing continuation, closes only
the merged PR binding, checkpoints the merge, and transfers to the recorded `plan-execution` stage. That
stage reconciles an existing successor layer or starts the next branch in a checkout selected under
`engineering:git-branching`, before rebinding the same task to that layer's exact head and runs. Never carry the completed PR's review
watermark or delivery binding into the successor; the successor re-resolves merge authorization from the
goal's recorded authorization (`engineering:merging`).

Resolve the primary checkout from the first `worktree` record in `git worktree list --porcelain`; never
remove that path. When it sits on the merged branch or the default, move it to the fetched remote default
before closing any linked worktree; when it hosts any other branch, leave it there and run
`git -C <primary-checkout> fetch origin <default>` only:

```bash
git -C <primary-checkout> checkout <default>
git -C <primary-checkout> pull --ff-only origin <default>
```

Compare the recorded target checkout in the delivery binding with the resolved primary checkout and the
current host attachment before invoking either cleanup path below. When the target is the primary checkout,
or the session is already attached to the primary checkout, do not retarget or hand off; continue cleanup
and branch deletion in the current session.

When the session remains attached to the primary checkout or another retained checkout, finish Step 6,
any plan close-out and the report, then run exactly this argument-free command as the final action:

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File <machine:peer-cli skill-directory>/scripts/close.ps1
```

It verifies this session's registered host and attachment, closes only its own CLI or uniquely identified
tab, and records verified session exit while preserving checkout files and Git state. A retained checkout
or deleted branch does not prove that the CLI exited. If verification fails, preserve the session and
resolve its registry or attachment evidence before retrying.

Only when the recorded target is a linked worktree, the host is attached to that target, and the target
differs from the primary checkout, the session closes itself as the delivery's final action, after Step 6,
any plan close-out and the report. Run gate 1 below, then from inside that worktree run exactly this, with
no arguments and no leading `&`, because the harness allow rule matches only this string, written with
forward slashes since the Bash tool strips backslashes:

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File <machine:peer-cli skill-directory>/scripts/finish.ps1
```

It verifies the receipt, detaches a reaper that removes the worktree and branch once this session exits, and
closes this session's CLI and tab. The reaper's result and the cleanup reminder surface any failure to the
next session. A per-command `workdir`, shell `cd`, or `git -C` does not retarget Codex or Claude and is not
evidence that the old directory can be deleted.

- Only when `finish.ps1` is unavailable or its preflight fails: if the harness exposes its native host
  command interface, invoke `/cd <primary-checkout>` there and continue only after the host confirms that
  the session is attached to the primary checkout.
- Only when `finish.ps1` is unavailable or its preflight fails: if that interface is unavailable, invoke
  the unqualified `handoff` workflow once with the primary checkout. Checkpoint the exact repository, merged
  PR, branch, remote head, target worktree, primary checkout, and remote default. Put the remaining Step 5
  cleanup and final inventory in the successor's `## Next Steps`. After verified launcher submission the
  predecessor stops repository-scoped work; it cannot end its own host session, so the successor's
  `## Next Steps` gates on the recorded release marker and then closes the predecessor's CLI and tab through
  `handoff`'s `machine:peer-cli` release procedure, and the predecessor does not run either cleanup path. The
  successor is the sole cleanup owner: after closing the predecessor, it selects the helper or native-Git
  path below, requires the physical target path to be absent, and then continues this delivery.

Do not make the user choose between these paths or teach them this lifecycle detail. Only the final manual
`/cd` pause already defined by `base:cd` applies when the automatic handoff capability is genuinely
unavailable or its diagnosed launcher fails.

Resolve the repository's own worktree command under the primary checkout and prefer it for a
worktree-developed branch. It refuses every unsafe state and handles the platform details — junctions, long
paths, Git administration, branch deletion — and the repository's own docs own that list, so trust the
refusal instead of second-guessing it:

```powershell
$worktreeHelper = Join-Path <primary-checkout> 'scripts/worktrees.ps1'
if (Test-Path -LiteralPath $worktreeHelper -PathType Leaf) {
    & $worktreeHelper close -Worktree <path> -PullRequest <n> [-PlanManaged]
}
```

Add `-PlanManaged` when a plan owns the work. If that exact primary-checkout helper path is absent, do not
skip cleanup. Apply the same gates with native Git from the primary checkout:

1. From inside the target worktree run exactly `python -B <skill-directory>/scripts/cleanup_proof.py`; from
   elsewhere add `--worktree <target> --branch <branch> --head <remote-head> --pr <n>`. It refuses the
   primary checkout, a detached or mismatched target,
   a PR that is not `MERGED` at exactly that head, a merge commit absent from `origin/<default>` (the
   squash/rebase-safe containment proof), and a still-open PR for the head. Run from inside a proven
   merged target, it sets uncommitted leftovers aside under `<state>/merge-cleanup/set-aside/` and cleans
   the tree; from elsewhere a dirty tree still preserves. `preserve:` stops cleanup.
2. For a linked target, run `git -C <primary-checkout> worktree remove -- <target-worktree>` without
   `--force`, then delete the local branch with `git -C <primary-checkout> branch -d <branch>`. For a branch
   developed in the primary checkout, the checkout-and-fast-forward above replaces the removal step; delete
   the old local branch with the same lowercase `-d` only after it is no longer checked out. Double-quote each
   path and run each command on its own; that exact form is what the plugin's harness grant approves; when
   `-d` refuses a squash- or rebase-merged branch, the proof covers exactly this head, so delete it with
   `git -C <primary-checkout> branch -D <branch>`.
3. Re-run `git worktree list --porcelain`, the local branch inventory, and primary-checkout status. The
   target must be absent, the local merged branch must be gone, a primary checkout moved to the default must be
   current on it, and pre-existing user files must remain. Treat any removal error or residual target path
   as incomplete cleanup; never replace the failed command with a forced removal or raw recursive deletion.

**Step 5 is a blocking post-merge gate. Do not report terminal delivery or leave the cleanup for a later
session until `finish.ps1` has run or host retargeting plus the helper or native-Git path has produced the
final inventory above. Only the `finish.ps1` path may enter Step 6 first.** The
worktree-cleanup audit gate and the merge-cleanup gate are backstops that make a missed cleanup visible, not
a substitute for doing it immediately.

If plan work remains, reconcile and continue an existing successor stack layer, including its base,
head, review evidence and delivery binding. When no successor exists, start the next branch from the
updated base and select its checkout under `engineering:git-branching`; resume the same ledger. Remote
observation alone needs no new checkout. Select a checkout when a substantive close-out edit is required.

### 6. Follow the publish and version-sync consequence to a terminal state

`engineering:merging` owns the rule — whoever merges owns only the generated downstream PR that
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
- **Close plan-managed delivery from a checkout selected under `engineering:git-branching`.** Before
  deleting the goal, run the fresh completion check above. A missing, invalid, or failing record leaves the
  plan and its owned actions in place. Once
  publication and sync are terminal, record the final transition, delete the plan and ledger, and tick
  the owning roadmap item in one docs-only
  closeout commit. Review it per `engineering:docs-review` — skipped for a pure close-out — and
  land it through `engineering:merge-docs`.

## Plan-managed delivery records material boundaries only

Resolve the plan and delivery identity before step 0. During queue observation, GitHub owns checks, admission,
ejection, merge, publication, and sync chronology. Update the ledger only for a genuine blocker or ownership
handoff, a stable fix milestone that will ride its substantive commit, or the final terminal closeout. PR
discovery, labels, successful checks, admission, polling, base sync, and no-op publication observations do not
each create a checkpoint. Never create a commit merely to make the ledger agree with a remote timeline.

## Report

Every goal completion and plan closeout requires exactly one fenced `completion` record. A missing or
invalid record is incomplete. Run a fresh completion check before claiming the requested user outcome or
deleting its goal:

```bash
python -B <completion-check> --goal <absolute-goal> --root <absolute-worktree> --bound-repository <owner/repo> --bound-pr <n> --bound-head <forty-character-head>
```

Resolve `<completion-check>` to `.agents/workflows/completion.py` in source or
`workflows/completion.py` in an installed engineering package. On a failing result, retain the goal and
report its owned next actions as incomplete.

One short report: the PR that merged (number plus merge commit); whether the full suite ran because a
positive trigger was present or was skipped by label because none was; that the base is synced; and that the
branch — and its worktree, if the work was done in one — is cleaned up. For plan-managed work, that the
close-out PR landed and any isolated checkout was removed. Then the sync outcome: **nothing published, sync merged
green at a new version, or sync went red and you migrated its consumers** (which files, now green) — never
"merged, and left a red sync PR behind." If you stopped early, say exactly what is blocking and what is
needed.

Keep it terminal: verify green → enqueue → wait for `MERGED` → complete checkout cleanup → sync the base →
follow the sync PR to green or migrate it → land the plan close-out → complete checkout cleanup → summarize →
run `finish.ps1` when the session is attached to the removable merged worktree, or `close.ps1` when its
checkout is retained. No preamble.
