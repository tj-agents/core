---
name: handoff
description: Transfer responsibility for a goal or a separate workstream to an independent session with one self-contained prompt. Use for an actual ownership transfer; work returning here uses a subagent.
kind: workflow
domain: process
---

# Hand off to an independent session

Owns the boundary between native subagent delegation and an ownership transfer, and the transfer itself.

## Subagent or handoff

- The current owner keeps the task and needs a bounded result, such as research, planning, validation or
  an implementation slice: native subagent. A fresh context, different topic or separate artifact alone
  transfers nothing.
- Replacing the owner, or giving a distinct authorized workstream its own owner through completion:
  handoff. Perform an explicit transfer request even when this session could do the work. A prepared
  prompt alone is not a handoff.
- A prompt-only request returns the prompt and launches nothing.

## Decision provenance

Carry the user's decisions with their source, separately from a predecessor's proposals. An unaccepted
proposal is an assumption the recipient assesses within the user's constraints. Planning-only authority
stays planning-only through a subagent or a handoff.

## The prompt

One self-contained prompt: the absolute checkout or task directory, the objective, the full requested
outcome, constraints and authority, decisions with their provenance, open questions and the exact next
action. It never narrows the requested outcome. Unresolved architecture is dispatched as it stands from a
verified checkout; the successor owns its design and setup, including isolation before deliverable writes.

## Launch

1. Checkpoint the canonical goal, then stop writing owned paths.
2. Respect a named harness; otherwise use `agent:handoff --host codex`, resolved through native discovery,
   never a guessed path. Keep a user-chosen model, effort or harness; otherwise select a lane the launcher
   accepts through `agent:lanes` and record it with a one-line reason.
3. Write the prompt to a UTF-8 file and invoke the launcher once. Never relaunch because startup is slow;
   reconcile an interrupted or ambiguous launch instead of retrying it.
4. Report submission as launch only; it does not prove the successor read the prompt.

Never keep two writers on one checkout. A side workstream gets its own isolation, through the selected
Engineering worktree operation for software, while the origin keeps its goal, checkout and next action.
When the transferred checkout must later move or be deleted, put `engineering:merging`'s transferred
checkout cleanup in the successor's next action; the predecessor does not perform it after launch. If the
launcher is unavailable, report the missing capability, continue independent work and never claim a
transfer happened.

```text
Input: get a fresh assessment of the cache design and return it so this agent finishes billing.
Route: native subagent; this agent keeps billing.
Input: transfer the migration to a successor through completion.
Route: checkpoint, stop writing, launch one successor with the self-contained prompt.
Input: the user chose Redis; the predecessor proposed a custom coordinator.
Prompt: Redis as the user's decision with its source; the coordinator as an assumption to assess.
```
