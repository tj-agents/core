---
name: plans
description: Supporting contract for plan, roadmap, and progress-ledger structure, ownership, dependency states, phase gates, closeout, and context-transfer criteria. Load while a task workflow authors, executes, reconciles, checkpoints, or closes durable plan state; it does not own natural-language planning or implementation requests, which select plan-authoring, plan-execution, continue-roadmap, or update-roadmap.
domain: process
---

# Plans

**Git history is the archive.** A plan is a working document for *unfinished* work; a finished plan kept "for
reference" is rot that misleads the next reader into thinking the work is still pending.

## Roadmap → plan → progress

- A **roadmap** (`<EPIC>_ROADMAP.md`) is an epic's living tracker: no ledger, never deleted, alive until the
  epic ships. Each of its items spins off its own plan and keeps the tick when that plan is deleted. Each
  checklist item contains its stable `<epic>/<slug>` key as an inline backticked token; the spun-off ledger
  records that exact value as its `Roadmap item:`.
- A **plan** (`<NAME>_PLAN.md`) is the design and the outstanding phases for one buildable item.
- A **progress ledger** (`<NAME>_PROGRESS.md`), in the same folder, is a **compact rolling snapshot of current
  operational truth** — not an append-only history. Keep both current throughout the work.
- A **standing reference or RFC** that informs an epic but spins off no phases keeps a **bare stem** — no
  `_PLAN`/`_PROGRESS` suffix — so the graph tooling never treats it as a plan owing a ledger.

Folder per epic: the roadmap and every plan it spins off live inside it. A plan's ledger owns its logical
workstream across delivery PRs; its worktree and branch are temporary execution state, safe to recreate from
the remote default branch once the prior PR's worktree is removed.

A legacy plan with no ledger stays valid: reconstruct the state from the plan and repository evidence, then
create the ledger before recording further progress.

## The active delivery branch owns current planning state

Before implementation begins, planning-only work may be authored and landed through a docs branch. Once a
delivery slice has a branch and worktree, that checkout's plan and ledger are the current state for the slice.
Material updates ride the same substantive commits as the work they describe. Never maintain a second live
copy in the normal checkout and never edit one logical ledger from two worktrees.
Naming or opening a plan, ledger, or roadmap obliges **reading its active owner's current state before
acting**. The copy in another checkout may be stale, and remembered state is not current state.

After a delivery PR merges, the default branch inherits its planning state. Any remaining work starts a fresh
worktree from that current remote default and continues the same plan. An in-flight sibling reads the owning
branch or PR when it needs newer evidence; it does not create a competing ledger copy.

**A plan must not cite its roadmap — but an agent working the plan may read it.** The document dependency
runs one way: a plan is spun off *from* an item and reports completion back to it, and a plan that cites the
roadmap couples the disposable artifact to the permanent one. Reading is different from citing: the roadmap
is also the epic's cross-plan dependency map, so navigate by it, then never write a reference to it into the
plan.

Keep the roadmap current when scope, dependency ordering, ownership, or terminal state materially changes.
Include that update in the substantive commit that carries the transition; do not create a roadmap-only tail
for routine workflow evidence.

## Shape of a plan

A plan describes a chunk of work too big for one commit, broken into **phases that are each independently
shippable and each end green**. A phase states what it changes, why, its verification gate, and — whenever it
ships a capability something else consumes — its **consumption contract**. Phases sequence so that every
intermediate state builds and passes.

**The consumption contract is a required part of any phase that ships a consumable capability, on the same
footing as the verification gate** — not an aside to fill in later. It pins who calls the capability and the
exact shape it hands back: payload, sync vs async, inline vs file/download. Design it from what the *consumer*
needs, not from what is convenient to emit. You may defer the *consumer itself* — the UI, the calling
service — to a named later phase or plan; you may **never** defer the *output contract*. A producer with an
undecided output is not a shippable phase: it cannot be named, typed, or tested against a consumer, and the
gap resurfaces downstream as naming churn over a thing whose job was never fixed.

## What a ledger must contain

Every `<NAME>_PLAN.md` has at least one same-directory `<NAME>_PROGRESS.md` companion, created with the plan.
**A plan may have several ledgers** — one per parallel workstream, each named for that workstream; the
`- Plan:` header is the authoritative plan↔ledger grouping, not the filename.

Required headers: `Plan:`, `Roadmap:`, and the stable `<epic>/<slug>` `Roadmap item:` key. Together they form
the roadmap→plan→ledger graph that `plan_graph.py` checks. Reconstruct them from the plan and roadmap when
adopting a legacy ledger.

Each ledger keeps these current sections:

- plan, absolute worktree, branch, PR, and relevant dependency or package gates;
- current state, including partial/uncommitted work the next agent must preserve;
- completed milestones, normally one concise item per phase or delivery gate with commit/PR evidence;
- the latest verification, and review state under the literal heading `## Reviews` — the name
  `plan_graph.py` reads to gate a merge on a recorded review — including every open finding and its
  disposition;
- decisions, discoveries, blockers, and deviations that still affect execution and cannot be safely
  reconstructed from code or durable artifacts;
- **`## Next Steps`** — the single resolved action for the next agent, as concrete self-contained steps. If
  no action can proceed, start it with the four blocker fields below. This is the **single source of truth**
  for what to do next; resume and handoff prompts point here instead of restating it.

The retention test for every entry is: **could removing this fact cause a fresh agent to take the wrong
action or repeat a costly failed approach?** If not, remove it. The checkpoint standard owns the mechanical
size warning and safe compaction procedure.

[`plan-checkpoint`](../plan-checkpoint/SKILL.md) owns the small set of transitions that require a durable update.
Ordinary reports, commits, pushes, review stages, preflights, polls, and remote observations do not.

## Verification gate per phase

Every phase, no exceptions:

- Run required generators, grep/invariant gates, and the smallest affected project or frontend build.
- Run focused unit tests for the changed behaviour.
- Commit the completed reversible work locally. Push only when the accumulated commits form a stable
  candidate that needs remote validation or a real handoff. Exact-head PR CI is authoritative for the full
  solution and complete test matrix.

## Never leave the codebase out of sync — the plan isn't done until the whole thing is

A refactor isn't finished when the convenient half lands. If a package boundary forces it into multiple PRs,
do them back-to-back — but the plan stays open until **all** of them land and the codebase is in sync again.
Merging the consumer and calling the plan done while the producer still speaks the old shape is the thing to
never do.

## Breaking published-contract changes — capture them, don't force them in

Where services compile against *published* packages rather than the source sitting beside them, use the
`dotnet:package-cutover` standard to classify a contract change. A breaking change cannot land in one PR:
consumers only see the new shape once the package republishes.

When you hit one mid-feature, **don't force it into the current PR and don't derail the feature to do it.**
Capture it in a dedicated plan (design, expand/contract steps, why it is multi-merge), record both dependency
graphs, and do every consumer preparation step an exact local producer artifact supports. Keep those
consumers delivery-gated until the published-package revalidation.

## The delivery state vocabulary

Use these states consistently in roadmaps, plans, ledgers, reports, and handoffs:

- **implementation-blocked** — a required source/API/design or trustworthy exact artifact is unavailable;
- **implementable, delivery-gated** — local implementation can proceed, but the branch cannot merge yet;
- **delivery-ready** — implementation, tests, and review are green against the recorded exact producer
  artifact; published-baseline revalidation remains;
- **merge-ready** — temporary inputs are gone and the branch is green against the real published baseline;
- **terminal** — all required merge, publication, sync, and closeout gates are complete.

When an exact local package is sufficient, record its producer commit, package version, hashes, and
reproducible location; never commit a machine-specific feed path, temporary version pin, or local-only
configuration.

## Delivery gates do not automatically block implementation

For work spanning branches, packages, or generated syncs, keep **two** dependency graphs: what must exist to
implement and verify locally, and what must land before delivery. A PR, publication, or sync gate blocks local
implementation only when the required source, API, design, or exact test artifact is unavailable. Otherwise
prepare the consumer in its own worktree, test it against the exact producer artifact, and leave it
delivery-gated until it passes again against the published baseline.

Actively hand off every independent implementation path. Parallel means independently owned work made ready
for its eventual merge order — not branches that are already mergeable today.

## Write a fact into the plan that owns it

When one plan surfaces a fact belonging to a sibling—a required phase, consumed contract, or design-changing
decision—route it to that plan's active owner. If no active branch owns the sibling, update it in the current
substantive planning change. If another worktree owns it, record a compact handoff and let that owner include
the update at its next material checkpoint. Never copy the same fact into both ledgers.

## Cross-plan blockers are two-way handoffs

A waiting plan never polls another branch and never relies on a human remembering its prompt. Read the epic
roadmap to find which sibling plan owns the dependency and open that plan's ledger for its live state; don't
guess from memory. Then, for an edge that genuinely blocks *implementation*:

1. the waiting ledger records the blocker fields below and stops polling;
2. every ledger named by `Blocked by:` gains a **`## Downstream handoffs`** entry with the waiting ledger,
   its worktree, and the same gate — this exact heading is the durable return path `plan_graph.py` checks;
3. when the owner crosses the gate, it updates and compacts the waiting ledger in that same session and
   surfaces its resume prompt;
4. an owner plan or ledger is never closed while a downstream handoff remains undispatched.

## Hard blockers — hand off the resolver, never the blocked plan

If safe authorized work in the current session can remove the obstacle, or local implementation can proceed
while delivery waits, do that work; it is not a hard blocker. Otherwise `## Next Steps` must begin with four
single-line fields, reported verbatim in the final response:

```text
Blocked: <the exact unmet gate>
Blocked by: <the owning ..._PROGRESS.md ledger, or the external owner>
Unblock action: <what must be done, by whom or where>
Resume when: <the objective evidence that proves the gate opened>
```

When the blocker or user action concerns an existing PR — especially permission to make it ready or merge
it — include a clickable `PR #<number>` link in the relevant field and in the report. **Never ask
for merge permission with only a bare PR number.** Route the resolving work by ownership:

- existing PR, plan, or session → register the downstream handoff, name the owner, emit no prompt;
- no owner and a separate context is appropriate → emit a paste-ready dispatch prompt for the resolver,
  including the blocked ledger and the condition it unlocks. This is not the blocked plan's pointer;
- user or external action only → replace the four fields with one
  `Paused: <who> — <action and observable resume condition>` line and give that action directly.

Do not create a checkpoint merely to prove an unchanged blocker is still blocked. **A blocked or human-gated
plan never emits its own resume pointer** — its ledger and final report name the blocker, its owner, the
action that removes it, and the evidence that makes resumption valid.

Conversely, when a turn deliberately transfers an **actionable, non-terminal** plan owned by the current
worktree to another context, it must end with the exact continuation pointer whose shape is
the `handoff` skill's. Actionable `## Next Steps`, local implementation completion, or a phase boundary
alone does not require that transfer; the context-transfer decision is owned by
[End of a phase — leave it compaction/clear-safe](#end-of-a-phase--leave-it-compactionclear-safe).

## Lifecycle

1. **Write the plan and ledger** when the work spans multiple commits or PRs or needs design first. Before
   creating them, check plans, branches, worktrees, and PRs for the same work, then assign each logical
   workstream exactly one ledger.
2. **Branch, then work a delivery slice** from the current remote default. That branch and worktree own the
   plan's current state for one PR-sized slice.
3. **At a material milestone, update the plan and compact ledger before the substantive commit.** Check off
   or strike shipped phases, retain only current recovery state, and stage those edits with the work.
4. **Keep both artifacts after the last local phase while delivery is live.** Make the ledger's exact next
   action the gate that now owns progress — **review comes first: never write a merge as the next step until
   a review is recorded** (a `## Reviews` entry or a review watermark); then PR, merge, publication,
   dependency, or platform sync. `plan_graph.py` enforces this. Once the PR merges, close its worktree; if
   work remains, create a fresh one from the current remote default and resume the same ledger.
5. **Close out only after the entire lifecycle is terminal.** Record the final transition and delete the
   plan and ledger in the next substantive commit or one final docs-only closeout. Never push a commit whose
   only purpose is to record a remote observation.

### Plans outlive PR worktrees

A worktree owns one PR-sized delivery slice, while the plan survives through the commits merged to the
default branch. Once the PR merges, remove the worktree and create a fresh one from the current remote default
if work remains. Never reopen a merged branch to append observations; the forge owns remote evidence until a
later substantive commit or final closeout needs it.

### Check `git status` before the close-out commit

Lifecycle 5 assumes the plan is already a **tracked** file you `git rm`. The case that slips through is a plan
written and fully implemented in the same session: it exists only as an **untracked** working-tree file, so a
blanket `git add -A` before the close-out commit **stages it as a new file** — the exact opposite of deleting
it — and it ships inside the PR as rot.

So run `git status --short` over the plans tree and eyeball it:

- a plan closed by this change must **not** appear as `A`/`??` (born-and-done → never stage it, or `git rm`);
- a tracked plan whose final lifecycle gate is terminal must appear as `D`, not survive untouched;
- its `_PROGRESS.md` companion must disappear too, and must not be added by the close-out change.

Mechanically: after the close-out commit, no terminal plan is in the tree — as an addition or a survivor.

## End of a phase — leave it compaction/clear-safe

A phase isn't done when the code is green; it's done when **nothing important lives only in the chat
context**. At its material checkpoint: the plan checked off or struck, the ledger compact with one exact next
action, and any decision or convention worth
carrying forward written into the doc that owns it. Anything you'd be annoyed to re-derive — a command that
worked, a gotcha hit — belongs in the commit message or that doc, not left implicit in the context. A phase
boundary makes the conversation disposable; it does not require disposing of it.

**Continue in the current context by default** when the next action belongs to the same logical workstream,
the loaded goals, constraints, decisions, and evidence remain relevant and coherent, and the user's existing
authorization covers the next phase. Move directly into that work after the durable checkpoint; do not stop
for a handoff or ask the user to name the next phase merely because one phase completed.

Transfer to a fresh context only when at least one of these conditions is true:

- the user explicitly asks to clear, restart, or hand the work to another context;
- the next action changes owner, worktree, PR, or logical workstream, or a workflow deliberately requires an
  independent context for unbiased review or isolated judgment;
- the next plan section is materially separate and the earlier reasoning would distract from, rather than
  help with, the new work;
- the context is genuinely degraded: repeated compaction has lost needed detail, important facts are being
  re-derived, conflicting stale assumptions remain loaded, or too little usable capacity remains to execute
  the next slice safely.

Age, transcript length, an actionable ledger, or a phase boundary by itself is not evidence that context is
degraded. When a transfer condition does apply, make the checkpoint durable and emit the exact handoff from
the `handoff` skill; do not emit one as routine phase-ending ceremony.

## Finishing, superseding, abandoning

- **Finished** → delete the plan and its ledger, once the whole lifecycle is terminal — not merely once the
  final local phase is committed.
- **Superseded or rejected** → delete it the moment that is decided. Don't leave a tombstone.
- **Partially done** → keep it, but strike out or check off the shipped sections in the same workflow
  checkpoint, so what remains is only the outstanding work.

## Rename definition-of-done: the grep gate

A rename is done **only when `grep -rniE "<oldterm>"` over the entire repository returns zero** — every tier,
no exceptions: type names, identifiers in **every** casing (PascalCase, camelCase, snake_case, kebab-case),
locals, fields, params, comments, string literals, test ids, HTTP routes, JSON keys, storage paths, file and
folder names, and docs.

**There is no "cosmetic tier."** A field typed `INewThing` still named `oldThing`, or a comment still using the
old word, is *not done* — it is exactly the dishonest naming the rename exists to remove.

Run the grep before claiming done. The only acceptable non-zero result is an **explicit written allowlist** of
deliberate survivors, each justified: a word that legitimately means something else now, a shared published
contract, a wire value kept on purpose. "I renamed the types, the build is green, tests pass" is not the bar —
the grep is. **Remove the discretion:** grep, allowlist, zero.
