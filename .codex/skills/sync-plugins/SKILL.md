---
name: sync-plugins
description: Refresh this CLI's tj-agents plugins and continue authorized work through the host's supported adoption mechanism when a fresh process is required. Run it yourself, without asking, whenever plugins look outdated - a skill or hook is missing or behaves like an older version, or a plugin PR just merged - or when asked to sync, reload, refresh or update the plugins.
kind: utility
domain: machine
---

# Sync plugins

Read the [canonical shared definition](../../../.agents/machine/utility/sync-plugins/SKILL.md).
This entry point adds only Codex's mechanism.

## Codex

Codex has no in-session reload. A stale-standards write block or another mandatory fresh-process change
selects automatic continuation of the authorized task. Stop deliverable writes and checkpoint the complete
objective, authority and limits, reserved decisions, checkout/branch/PR, dirty work, validation and remaining
work, with one executable `## Next Steps`. Use an absolute UTF-8 checkpoint outside tracked source, linking
any existing canonical goal. The user should not need to restart, paste a prompt or run a resume command.

For a task without an existing recorded execution owner, obtain the stable receipt first
(Windows; use `python3` on Linux/macOS):

```text
python -B '<skill-directory>/scripts/sync_plugins.py' --project '<absolute-checkout>' --continuation-status
```

Add this section to the checkpoint, using the returned absolute receipt path:

```text
## Execution readiness
Verdict: ready
Execution authorization: implementation
Transfer: required
Receipt: <returned-absolute-receipt>
```

Run from the exact checkout after stopping owned-path writes (Windows; use `python3` on Linux/macOS):

```text
python -B '<skill-directory>/scripts/sync_plugins.py' --host codex --project '<absolute-checkout>' --continue-codex '<absolute-checkpoint>'
```

The command refreshes first and invokes `machine:handoff-codex` once after success, including when the
installed bytes report `current` while this process still needs them. It retains installation and hook
trust checks. The successor receives the checkpoint and acknowledges the immutable attempt before writing.
The predecessor stays read-only and observes pickup with `--continuation-status`, using `workflow:handoff`'s
verified execution pickup procedure and five-minute observation budget. Report startup, acknowledgement
and first-action evidence separately.

The same native session, profile and checkout reserve the same receipt. Repeating a submitted or uncertain
attempt never launches again. A refresh failure or confirmed launcher failure reports its concrete cause;
fix that prerequisite and repeat the same command. Exit 3 or interruption after launch begins retains the
reservation: inspect its launcher/startup evidence through `workflow:handoff` before retry or writer reclaim.

Existing recorded execution or continuation owners use `workflow:handoff` and their supported foreground
release/claim mechanism instead; this standalone command refuses to bypass a recorded execution. Carry
the existing owner reference and use verified execution pickup to invoke one `machine:handoff-codex`
automatically. If its owner interface or launcher is unavailable, report the observed blocker, receipt,
resolver and retry path. Preserve trust and reservations rather than substituting a routine manual restart.
