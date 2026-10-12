# Installed Stop-hook recovery

## Objective

Determine and implement the supported Core delivery/recovery path for a stale installed engineering Stop hook that falsely blocks a valid continuation binding with `binding-head-changed`. Deliver the repair as an isolated Core change; do not modify the controller-association PR #209, its continuation owner, or installed plugin-cache files by hand.

## Evidence

On 2026-10-12, the controller-association checkout at `Fix/ControllerGoalAssociation` was at `e7df895d41a2faaab73743f98978b08212a99bc0`, matching both its continuation owner and `.agents/persistent-workflow-binding.json`. The source hook now reads `remote_head_sha`, but the installed cache `base-agents/engineering/2.1.16/hooks/continuation_stop.py` still reads `binding.get("head")` after normalization, which guarantees the false failure.

The source correction alone does not update a running or stale installed plugin package. The supported recovery must preserve hook trust and package integrity, work on Windows and Linux, and prevent future sessions from being trapped by the obsolete cache.

## Scope

- Diagnose the supported installation, refresh, versioning and host-reload path.
- Make the minimal canonical-source change(s), tests and release/delivery wiring needed to recover safely.
- Record the precise user action, if any, required to update an already-running host.
- Do not patch `C:\Users\TommySeery\.codex\plugins\cache` directly, disable hooks, rewrite PR #209 runtime state, or delete locks/receipts as a workaround.

## Authorization

This is the bounded standards-defect side workstream required by `engineering:session-guidance`. Normal Core implementation, tests, PR and merge are authorized; profile installation, destructive cleanup and bypassing host trust remain gated.

## Handoff lane

Lane: L3. The fault is clear, but the supported deployment/recovery behavior and host cache/trust boundaries require an open investigation.

## Completion

- A supported remedy is implemented and validated on Windows and Linux where Core owns the behavior.
- The canonical source has regression coverage for the faulty normalization path and recovery path.
- Documentation distinguishes source repair from installed-cache recovery and gives a safe, exact operator action.
- No workaround mutates an installed cache or continuation state by hand.

## Next Steps

1. Read `README.md`, `CODE_CONVENTIONS.md`, `PACKAGING.md`, the current source and cached `continuation_stop.py`, and the plugin install/update contracts.
2. Map how a released source fix reaches an existing Codex session and a newly opened session; identify the smallest supported remediation.
3. Implement, validate and deliver the focused fix from this checkout.

- Scope: only installed Stop-hook cache recovery.
- Current slice: supported recovery-path diagnosis.
- Remaining scope: implementation, tests, review and delivery.
- Done when: an obsolete installed hook cannot indefinitely trap a valid session after the source repair is released and the documented supported recovery action is taken.
