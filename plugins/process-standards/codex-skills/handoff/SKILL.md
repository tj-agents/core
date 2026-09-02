---
name: handoff
description: The exact shape of a continuation, resume or handoff prompt after a context transfer has been selected — the worktree opener followed by the two-line pointer at the plan and the ledger whose `## Next Steps` holds the work, the one `Why:` line that introduces it, why nothing plan-specific may be restated in the prompt, what a self-contained non-plan prompt needs instead, and which turns emit no pointer because the current context remains useful or the plan is blocked or human-gated. Use when writing any resume or dispatch prompt, when the plans standard's context-transfer criteria apply, when the Stop hook rejects an attempted handoff, or when deciding whether this turn owns a ledger's handoff.
domain: process
---

# Handoff

**This doc is the continuation pointer's exact shape** — nothing else defines it. The context-transfer
criteria that decide whether an actionable non-terminal plan needs one are in the `plans` skill.

**Hard final-response gate for a selected plan context transfer:** if the turn elects to move an owned or
explicitly targeted actionable `_PROGRESS.md` ledger to another context, the response is incomplete until it
ends with the pointer below. An actionable ledger by itself never selects a transfer. Merely naming a
dependency ledger for reading, or editing its copy from another plan's worktree to register a return handoff,
does not claim it. A ledger whose declared worktree already exists elsewhere is left to that owner unless the
turn explicitly targets that worktree. A summary or paraphrased next action is not the handoff. The
`plan_handoff_stop.py` Stop hook validates an attempted transfer and supplies the exact handoff for one bounded
repair attempt; it never recursively blocks the repair response.

- Start with the worktree opener — `cd <absolute-worktree-path>`, or `/open-worktree <Type>/<Name>` when
  the worktree doesn't exist yet — and keep it inside the paste-ready prompt.
- For **non-plan** work, make the prompt self-contained for zero context: name the branch or PR, relevant
  working files, and exact next action.
- For **plan-managed** work, introduce each handoff with one `Why:` line derived from the first paragraph of
  the ledger's current `## Next Steps`. This makes the purpose explicit without duplicating the operational
  procedure. Then end with the paste-ready prompt, which is ONLY the pointer — an opener line then the read
  line:

  ```text
  Why: `<LEDGER>_PROGRESS.md` owns unfinished work from this turn: <short next-action reason>
  ```

  ```
  <opener>
  Read @<absolute-owning-worktree-plan-path> and @<absolute-owning-worktree-ledger-path> and do what its `## Next Steps` says.
  ```

  Nothing follows the pointer. The final-response shape is a result summary, the `Why:` line, then the
  two-line pointer as the final content.

  The `<opener>` is `/open-worktree <Type>/<epic>_<name>` when the plan's worktree doesn't exist yet — a
  freshly-written plan, after a clear with no live worktree, or normal continuation after a prior PR's
  worktree was removed — so implementation runs in an isolated worktree, never the main checkout; it's
  `cd <absolute-worktree-path>` once that worktree exists. Nothing else plan-specific goes in the prompt — no
  branch to verify, checkpoints, gates, commands, or next action; every such specific lives in the ledger (its
  header and `## Next Steps`), so the prompt can't drift. Both read paths are absolute paths into the same
  owning worktree the opener selects. Before a delivery worktree exists, they may point at the planning-only
  checkout; the first delivery branch then carries the plan and ledger with the work.
- When a context transfer is selected, end with one prompt that advances the ledger owned by this turn. Emit
  several only when this turn explicitly owns several independently executable worktrees. Do not emit
  pointers for other live worktrees merely because their ledgers were dependency inputs or received
  return-handoff edits. A delivery
  gate does not suppress an implementation pointer when the owned ledger has safe local work; only an
  implementation blocker does.
- A blocked plan never emits its own continuation pointer. First do any safe, authorized work that can remove
  the blocker in this session. If the gate still cannot move, record the four-line blocker schema from
  the `plans` skill at the start of `## Next Steps`, report those lines verbatim, and route the
  unblock action — a registered downstream handoff with no prompt, a dispatch prompt for the resolver, or a
  `Paused:` line for a human decision. Never re-poll an unchanged blocker into repeated "still blocked"
  commits. The Stop hook requires a blocked plan's four lines verbatim, rejects its continuation pointer, and
  stays silent for a paused plan.
- When the transfer criteria in the `plans` skill apply, emit the handoff instead of asking whether
  to continue. Otherwise continue in the current context without emitting one.
- Before an implementation PR merges, route it through the repository's review workflow, and through its
  incremental review after later code commits.
- When nothing remains, state that the work is complete without a continuation prompt.
