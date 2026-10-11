# Codex terminal cleanup stop enforcement

Status: in progress

## Outcome

Codex blocks a terminal session exit after a confirmed merged PR until merge cleanup completes, matching the existing Claude enforcement.

## Scope and authority

The user explicitly requested diagnosis and permanent repair of the missed terminal close. This standards-source repair is authorized through implementation, validation, review, pull request, merge, and generated publication once repository gates pass.

## Progress

- Cause established: `merge_cleanup_gate.py` implements `Stop` blocking, but the Codex engineering manifest invokes only `continuation_stop.py`; Claude invokes the cleanup gate too.
- Isolated delivery branch: `Fix/CodexMergeCleanupStop`.

## Next action

Validate the Codex Stop-hook repair; then review, publish, merge, regenerate, and confirm terminal cleanup protection.
