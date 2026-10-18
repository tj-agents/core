# Session store retention and in-session repair

## Outcome

1. `~/.agents-state/sessions.db` drops a session once its work is done, so `recover` and
   `work_item_sessions.py interrupted` list only sessions that may need resuming.
2. A session does its own work. It never hands off to Codex because it runs on Claude, and a mistake
   callout is repaired in the current session instead of being forced through a handoff.

## Evidence (2026-10-18, installed machine 669d90ef)

- No `DELETE` anywhere in the session store, and the documented schema said sessions are "never deleted".
  31 sessions in the store, 23 never ended; `interrupted` returned 14 handles after a crash, most days old.
- `lanes`, `session-guidance`, `handoff` and `plans` told a Claude parent to hand all implementation and
  review to Codex. `callout_repair_gate.py` denied every non-read tool after a callout until a handoff
  launcher ran. A Claude session with a good context tried to launch a Codex handoff for this fix.

## Decisions (Tommy, 2026-10-18)

- Delete rows; don't mark them inactive. Delete at closeout, with no just-in-case sweep.
- Remove the Claude→Codex rule, the callout gate and the forced self-repair handoff.

## Delivered on `Fix/SessionStoreRetention`

- The `finish`/`close` exit observer deletes the session row after it verifies the host exited.
  `item --status done` deletes the item's other sessions and keeps the caller's.
- Handoff happens only on user request or when a separate session is needed. `self-repair` fixes the
  standard here, in its own worktree when the current checkout holds unrelated work.
- Deleted `callout_repair_gate.py`, `admission.py` (handoff disposition), their tests and all wiring.

## Out of scope

- `work_items` rows stay as the durable status record.
- Enforcing work-item registration at prompt time: 10 of 14 interrupted sessions had no work item.
- A one-time cleanup of rows already in the local store.

## Progress

- 2026-10-18: two commits landed (session deletion; routing removal). Callout-gate removal under test.
  `test_resume_start_clears_ended_at_and_end_reason` and the register-session store integration test
  flaked once under full-suite load (the 2s git probe returned `None`); both pass alone and on origin/main.

## Next Steps

Finish the gate-removal test run, commit, push, and open the PR with `gh pr create`.
