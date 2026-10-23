---
name: close
description: Close this CLI session when everything you were asked to do is finished, as your last action. Not for closing another session.
kind: utility
domain: machine
route: infer
---

# Close the finished session

Close when every outcome you own is finished: delivery, validation and handoffs are done, and nothing
waits on an answer, approval or check. A PR waiting only for the user's review or merge is finished work. Honor an
explicit keep-open request. Do not offer optional follow-ups to avoid closing.

A user callout about a mistake opens an unresolved repair outcome. Answer the direct question and preserve
the repair outcome until its current owner resolves it before reassessing completion. When engineering is
selected, `engineering:session` owns assessment of that outcome and `engineering:self-repair` owns
eligibility for a separate standards repair. A question about missed close-out does not instruct you to close
immediately.

```text
User: "Why didn't you close when the work was done?"
Action: explain the omission and keep the repair outcome active. When engineering is selected, assess the
active task under engineering:session and apply engineering:self-repair's source and authority decision only
for a suspected reusable tooling defect.
```

Close with the host's own close capability if it exposes one (a tool that archives or settles the current
thread). Otherwise, as your last command, run:

```text
python -B <skill-directory>/scripts/close_session.py arm      # Windows
python3 -B <skill-directory>/scripts/close_session.py arm     # Linux/macOS
```

Then give the final reply and end the turn. A detached watcher closes this session's tab and process once
the turn has ended and stayed idle for about 3 seconds. A new prompt before then cancels it. Arming does
not prove closure; a refusal leaves the session open, and its reason is recorded in
`~/.agents-state/session-close/<session-id>.json`.

Closure means the exact terminal tab is gone and the registered host has exited. If tab ownership or
closure cannot be verified, preserve the session and report the refusal. Never substitute process exit
for tab closure.

Closing never removes a worktree. After closing, the watcher runs the worktree sweep, which removes the
checkout only if its PR merged and nothing is left in it.

`peer-cli` closes other sessions.
