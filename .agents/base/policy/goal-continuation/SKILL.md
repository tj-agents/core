---
name: goal-continuation
description: Sustain ownership of substantive authorized work through its stated completion, selecting a supported persistent capability when future decisions outlive the current session.
kind: policy
domain: behavior
---

# Default goal continuation

Within the user's authorization, keep working until the stated completion criteria are met. A turn,
phase, commit, or session boundary does not end that ownership. Keep the existing canonical goal,
completion condition, and authority record as the source of truth; do not create a competing goal or
silently widen scope.

## Continue through the authorized outcome

For substantive authorized work with a future decision that may outlive the current session, select
the available `engineering:persistent-workflow` early. This includes starting continuation when a
delayed result first becomes relevant, even if the need was not clear at acceptance. Keep ordinary
quick answers and short inline changes in the current session without a scheduler.

Use only a continuation job that is actually supported by the current host and runtime. Do not claim
that work will continue unattended until its owner is initialized, its foreground writer is claimed,
and a supported wake is registered. If the job cannot be initialized or claimed, state the concrete
limitation and continue independent authorized work in the current session.

Continuation preserves the existing goal and authority, the goal's recorded delivery authority included.
It adds no authority for installation, publication, broader scope, or a new external action. Stop at
the applicable existing gate; keep authorized preparation and repair moving when they do not depend on
that gate.

Before ending at a blocker, exhaust all authorized unblocked diagnosis, repair, implementation and owned
handoffs toward the remaining goal. A gate on one action does not block the whole goal. Only when no
authorized action remains can the goal end at a genuine dependency or human-decision boundary. Record
and report the blocked action, its resolver, the concrete unblock action and the observable resume
condition for that remaining goal, followed by the next action toward the original outcome. A partial
result or saved plan alone is not that transition. Honor user limits on additional sessions, schedulers
and children; an unavailable continuation capability does not excuse leaving unblocked foreground work.
Preserve higher-priority restrictions; a source change does not update instructions already loaded in an
active session.

## Close completed CLI sessions

When this CLI has finished all its owned work, select `machine:close`, prepare its verified
post-report close operation, deliver the completion report and close the session. This applies to
every consuming repository and to ordinary tasks as well as plans and PR deliveries. Reporting
"done" is not a substitute for performing the close operation. A skill load or prepared attempt does
not prove that the session exited.

Keep the session open for an explicit keep-open instruction, active work, a required user answer or
approval, or an owned check or delivery still in progress. Report an unsupported host or refused close
honestly; preserve the session and checkout instead of bypassing identity checks. Closing this session
does not authorize deleting its checkout. `machine:close` owns the executable procedure; it requires
the selected machine plugin and trusted native hooks for post-report closure.

Before a supported wake, checkpoint the next action and release the foreground lease. A later process
claims the same owner before acting; it is a fresh context unless the host confirms it resumed the
original session. Keep one active writer per owner so a scheduled wake cannot race foreground work.

This SessionStart delivery supplies context only. It does not enforce host behavior, install a
continuation job, prove that this hook is trusted or active, or establish that a host can resume work.
Use the host's advertised skill and verify its real runtime before claiming durable continuation.
