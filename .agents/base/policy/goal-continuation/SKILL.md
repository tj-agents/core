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

## Check existing solutions before building

Before choosing an implementation for a new project, reusable tool, infrastructure capability, or
general technical mechanism, check the repository's existing capabilities and credible public
solutions. Use current primary sources, and inspect the relevant implementation when its behavior
matters. A similar name or README promise does not establish that a solution meets the requirements.
If external research is unavailable, record that limitation instead of claiming no alternative exists.

Compare adoption, a fork, selective reuse, a custom implementation, and keeping the current solution
against the actual outcome. Consider supported platforms, integration and packaging, failure recovery,
maintenance, security, licensing and attribution, and the cost of carrying local changes. Distinguish
observed behavior from source inspection and documentation claims. Recommend the smallest approach
that meets the requirements; record the useful sources, remaining gaps, and reason for the choice in
the existing goal, plan, or decision artifact. For a small task, a brief rationale in task context is enough.

Keep the check proportionate. Routine edits with a known implementation need no broad search, and
application-specific business behavior does not require finding another product to fork. Assess a
reusable technical component inside that feature when one is being selected. Reuse a recorded
assessment until requirements, evidence, or dependencies materially change. Research grants no
additional authority to install, execute third-party code, replace a component, or publish changes;
those actions retain the task's existing gates. Preserve upstream notices when copying licensed material.

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

Before ending at a blocker, establish what action is blocked and whether diagnosis, repair or an owned
handoff can resolve it within the existing authorization. Perform that work when available. A gate on
one action does not end ownership of the remaining goal. When an external decision is still required,
record and report the blocked action, its resolver, the concrete unblock action and the observable resume
condition, followed by the next action toward the original outcome. A partial result or saved plan alone
is not that transition. Preserve higher-priority restrictions; a source change does not update instructions
already loaded in an active session.

Before a supported wake, checkpoint the next action and release the foreground lease. A later process
claims the same owner before acting; it is a fresh context unless the host confirms it resumed the
original session. Keep one active writer per owner so a scheduled wake cannot race foreground work.

This SessionStart delivery supplies context only. It does not enforce host behavior, install a
continuation job, prove that this hook is trusted or active, or establish that a host can resume work.
Use the host's advertised skill and verify its real runtime before claiming durable continuation.
