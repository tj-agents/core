---
name: close
description: Close this CLI after all its owned work is done, in any repository. Use when finishing the session, reporting the requested work complete, or asked to close this CLI; not for closing another session.
kind: utility
domain: machine
route: infer
---

# Close the completed CLI

This operation applies in every repository consuming Core. A merge, PR, plan, or completion-check
record is not a prerequisite. Select it whenever this CLI has finished all its owned work.

1. Verify the requested outcome, required delivery, validation, cleanup and owned handoffs are complete.
   A pending answer, approval, check or delivery is still owned work. Honor an explicit keep-open request.
   Do not offer optional follow-up work merely to avoid closing a completed session.
2. Before the final completion report, run `python -B <skill-directory>/scripts/close_session.py arm`
   on Windows, or `python3 -B <skill-directory>/scripts/close_session.py arm` on Linux/macOS.
   It resolves this host's verified registry attachment and prepares a single post-report close attempt.
   The default retains the checkout. Only add `--remove-worktree` after `engineering:merge`'s fresh
   cleanup proof has authorized removing this exact merged linked worktree. Never pass a peer identity,
   arbitrary target, force option, or raw process-kill command.
3. Deliver the completion report, then end the turn. The machine plugin's Stop hook observes that report,
   refreshes the exact registered host identity, and invokes the existing `close.py` or `finish.py` helper.
   Do not perform more work after arming. A new user prompt cancels the pending attempt.

Successful arming proves preparation, not closure. The existing helper still requires an unended
`awaiting_input` turn, unchanged activity immediately before close, exact PID/start-time identity,
and its verified exit observer. Only observed session exit proves closure. A refusal preserves the
session and checkout; report the concrete limitation without claiming that the CLI closed or bypassing
the identity checks. A host without active trusted Stop hooks cannot promise post-report closure.

`peer-cli` owns other sessions. This skill owns this session's terminal operation. The runtime is Python
3.9+ and ships with the machine plugin; it does not depend on scripts vendored into the consuming repo.
