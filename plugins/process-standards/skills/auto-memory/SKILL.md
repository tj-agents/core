---
name: auto-memory
description: Toggle Codex's auto-memory feature on or off for a project by flipping the `autoMemoryEnabled` key in `.codex/settings.local.json`. Pure toggle — no arguments. Use whenever the user wants to turn memory on or off, disable memory, enable memory, or stop or start memory recall for the project.
domain: process
---

# Auto-memory toggle

A pure toggle for a project's Codex auto-memory feature: it flips `autoMemoryEnabled` in
`.codex/settings.local.json` and reports the new state. No arguments.

The `/memory` command's UI in current builds only *displays* the auto-memory status — it has no
selectable toggle — so this is the fast path for switching it. Codex-only: it controls a Codex
feature and is inert in a harness that has no `autoMemoryEnabled` setting.

## Steps

1. Read `.codex/settings.local.json`.
2. Determine the current state of `autoMemoryEnabled`:
   - key present and `true` → currently ON;
   - key present and `false` → currently OFF;
   - key absent → auto-memory defaults to ON, so treat as ON.
3. Flip it with a single edit:
   - currently ON → set `"autoMemoryEnabled": false`;
   - currently OFF → set `"autoMemoryEnabled": true`;
   - key absent → add `"autoMemoryEnabled": false` as the last key in the root object (insert a
     comma after the current last key).
4. Report the result in one line, e.g. `Auto-memory: ON → OFF`.

## Notes

- This is a settings change; it takes full effect on the next session launch. Say so in the one-line
  report if you just turned it OFF mid-session.
- It controls auto-memory only (recall and saving of `MEMORY.md` / `memory/` files). It does **not**
  affect `AGENTS.md` project instructions, which always load.
- Keep it terminal: do the edit, report the new state, stop. No preamble, no summary.
