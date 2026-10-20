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

Closing never removes a worktree. After closing, the watcher runs the worktree sweep, which removes the
checkout only if its PR merged and nothing is left in it.

`peer-cli` closes other sessions.
