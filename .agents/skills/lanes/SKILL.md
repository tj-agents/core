---
name: lanes
description: Pick the model and thinking effort a piece of work is worth by declaring an ordinal lane (L1 most capable to L5 cheapest) that each harness resolves to its own model, so no skill, agent or workflow stage ever names a model. Covers the ladder and what each rung is for, the four questions that choose a rung, re-routing per phase rather than running a whole task in its highest lane, where a lane is applied (skill front matter, a delegated lane agent, a workflow stage), and the three places the Claude and Codex ladders are deliberately not level. Use when adding or reviewing a skill or agent, when clerical work is running on an expensive model, when tempted to write a model name anywhere, or when a new model needs pricing into the ladder.

kind: contract
domain: process
---

# Lanes

**A lane is what work is worth, not which model runs it.** Declare `lane: L4`; never write a model name.
Two tables — `claude.json` and `codex.json` — are the only places a model name may appear, so a new model
or a reprice is a one-file change per harness and every consumer inherits it. They live at
`.agents/lanes/` in the standards repo and at `../../lanes/` from an installed plugin skill, alongside
`resolve.py`.

## The ladder

L1 is the most capable rung and L5 the cheapest. The same `LN` means the same *relative* capability on
both harnesses, which is the whole point: one declaration, two resolutions.

| Lane | For | Resolves to |
|---|---|---|
| **L1** | the mistake cannot be taken back — stored data shape, a published contract, a merge that lands | top family, the setting above its default |
| **L2** | open-ended judgement — architecture, plan authoring, a diagnosis with no known answer | top family, default setting |
| **L3** | specified work a compiler or suite will catch — features, bugfixes, review lenses | the workhorse family, high setting |
| **L4** | mechanical work whose shape is already decided — scripted edits, docs, ledger upkeep | the workhorse family, reduced setting |
| **L5** | clerical work with a small input — commit, push, pull, sync, one poll | the cheapest usable model |

**This document deliberately names no model.** Which model each rung resolves to is data, in the two
tables, and a rule stated in prose beside the data is a second copy waiting to disagree with it. Run
`resolve.py --lanes` from whichever of the two locations above exists here for the current pairings.

**Only a skill that IS the task may declare a lane.** A standard or supporting contract — anything loaded
*during* other work to be consulted — must not, because its lane would re-point the model of whatever task
loaded it: a migration would drop to the docs rung for having read the persistence standard. The generator
refuses a lane on a routed standard for exactly this reason; for a self-contained process skill the test is
whether an agent *runs* it or *reads* it. `commit` takes a lane; `committing` does not.

**No declaration means inherit the session's model** — not a default rung. A lane is opt-in per skill, so
adding one is a visible, reviewable decision and no skill silently changes model because a default moved.
L3 is what ordinary work declares; declare it explicitly rather than relying on absence.

## Choosing a rung — four questions, in this order

1. **Reversibility.** Can the mistake be taken back? A one-way change — stored data shape, a published
   contract, a merge — is L1 whatever else is true. Undo cost dominates every other signal.
2. **Blast radius.** How far does a mistake reach — one file, a module, a service, production? Service or
   production reach lifts the rung by one.
3. **Ambiguity.** Is the answer known and this is typing, or is the problem open? Open is never below L2;
   fully specified is never above L3.
4. **Verifiability.** What catches the mistake — a compiler, a test suite, or only human judgement?
   Compiler-caught work drops a rung; judgement-only work does not.

Nothing here says "how hard does this feel". A long mechanical edit is still L4; a three-line change to a
published contract is still L1.

**Re-route per phase.** One task is usually open/judgement while it is being designed, then specified and
test-caught while it is built, then clerical to commit and push. Route each phase. Running the whole task
in the rung its hardest phase needed is the waste this ladder exists to stop, and running the design phase
in the rung its cleanup needed is how a bad design gets built efficiently.

## Where a lane is applied

- **A skill** declares `lane:` in front matter. The generator resolves it and stamps the harness's own
  keys into each generated payload, re-pointing the running model for that skill and nothing else:
  `model:` plus `effort:` for Claude, `model:` alone for Codex — **Codex has no per-skill effort key**, so
  a Codex skill gets the rung's model at whatever effort the session is on. Where that half matters, use
  a delegated lane agent, which is the only place Codex can carry `model_reasoning_effort`.
- **A delegated lane agent** (`lane-l4`, `lane-l5`) is the alternative for cheap work that runs many
  turns. Prompt caches are model-scoped and a mid-conversation effort change invalidates the message
  cache, so re-pointing the main loop for a single clerical turn can cost more than it saves, while a
  delegated agent carries only its own small prompt and leaves the parent's cache intact. Reach for it
  when the cheap work is a loop — a monitor, a bulk pass — not a one-shot.
- **A workflow stage** keeps its own pinned model in `.agents/workflows/hosts/*.json`, because those pins
  live under the workflow contract's version rather than being re-resolved at dispatch. They are derived
  from the ladder and a test asserts they still agree with it, so a rung and its stage cannot drift apart
  — but the pin is the value the runtime reads.

## Where the two ladders are not level — know these before trusting parity

1. **L5 is a capability step on Claude, not just a price step.** Its model rejects `effort` outright and
   its context window is a fifth of every rung above it, so a clerical skill that reads a large diff or a
   long transcript fails on L5 where L4 would not. The Claude table records that ceiling; the Codex one
   records `null`, meaning *unrecorded*, not unlimited.
2. **Codex has no family below its small one.** Its L5 is the same model as L4 at the lowest setting, so
   the gap between those two rungs is smaller than on Claude, where L5 drops a family. Work that genuinely
   needs the cheapest thing available saves more on Claude than on Codex.
3. **A specialist model is a second axis, not a rung.** Codex's review stage names its own review-tuned
   model with a fallback — chosen for the *kind* of work, not its capability rank. Such a choice is
   declared as a `specialist` on the stage, never as its own lane, and it then owns its effort too;
   folding it into the ladder would imply a capability ordering that is not what it means.

## Anti-patterns

- **A model name outside the lane tables.** In a skill, an agent, a workflow script, a hook, a settings
  file: every one of those is a place that has to be found again at the next model release.
- **A lane picked by how the work feels** rather than by the four questions. That is how every rung drifts
  to L1 and the ladder stops meaning anything.
- **An alias where an ID belongs.** The tables carry exact model IDs because `ANTHROPIC_DEFAULT_*_MODEL`
  re-points a family alias — an alias can silently resolve to a different, dearer model than intended.
- **A new rung for a model that is merely different.** Rungs are ordinal. A model that is cheaper *and*
  weaker is a rung; a model that is sideways is a specialist.
