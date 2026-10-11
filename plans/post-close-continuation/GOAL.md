# Verify handoff-tab closure before continuing the originating goal

## Authority

Standing `engineering:session-guidance` standards-defect authority. This isolated Core repair may change the shared continuation-close enforcement, focused tests, and this goal; it may be reviewed, published, and merged after normal gates pass.

Checkout: `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-PostCloseGoalContinuation`

## Defect

`peer_cli.py close --force` can remove or invalidate a handoff session's process/registry state without proving that its visible Windows Terminal tab closed. An originating session can therefore claim the handoff is closed, then stop instead of continuing its authorized parent goal while a dead tab remains visible.

## Completion

A forced peer close cannot report closure until `close_tab.py --title` (or an equivalent actual-tab operation) has verified and closed the exact visible tab. A refusal or unresolved tab remains an incomplete close result. The repair has focused source and generated-host regression coverage and is delivered through an exact-head merged PR.

## Next Steps

1. Review the focused candidate and resolve findings.
2. Publish, monitor, merge, verify generated publication, and close this checkout.

## Progress

- 2026-10-11: traced the false success to `close_actual` and `close_entry` accepting a successful terminal-control invocation without re-enumerating the exact tab. Added bounded exact-identity absence confirmation for kitty, tmux, and Windows Terminal; forced peer close now refuses an unavailable terminal adapter, unverifiable Konsole tab, or missing terminal identity instead of reporting host-only closure. Focused peer, tab-close, and close-helper suites pass. Package regeneration and its consistency check pass.

```completion
{
  "outcome": "A cancelled handoff is reported closed only after its visible tab is actually closed.",
  "acceptance": [
    {
      "id": "actual-tab-proof",
      "criterion": "A forced peer close requires actual-tab closure proof before reporting success.",
      "evidence": [],
      "owner": "current execution owner",
      "next_action": "Implement focused host/runtime enforcement and regression coverage."
    },
    {
      "id": "delivery",
      "criterion": "The reviewed candidate passes required CI, merges, and generated package publication is observed.",
      "evidence": [],
      "owner": "current execution owner",
      "next_action": "Publish and merge after local verification and review."
    }
  ],
  "deliveries": [],
  "open_tasks": []
}
```
