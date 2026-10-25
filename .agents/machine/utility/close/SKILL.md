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
the repair outcome until its current owner resolves it before reassessing completion.
`workflow:session` owns assessment of that outcome; when engineering is selected,
`engineering:self-repair` owns eligibility for a separate standards repair. A question about missed
close-out does not instruct you to close immediately.

```text
User: "Why didn't you close when the work was done?"
Action: explain the omission and keep the repair outcome active. Assess the active task under
workflow:session; when engineering is selected, apply engineering:self-repair's source and
authority decision only for a suspected reusable tooling defect.
```

Close with the host's own capability if it verifiably closes only this CLI client. Archiving or settling
a thread alone does not establish client exit. Otherwise, as your last command, run:

```text
python -B <skill-directory>/scripts/close_session.py arm      # Windows
python3 -B <skill-directory>/scripts/close_session.py arm     # Linux/macOS
```

Then give the final reply and end the turn. A detached watcher closes this session's CLI client once
the turn has ended and stayed idle for about 3 seconds. A new prompt before then cancels it. Arming does
not prove closure; a refusal leaves the session open, and its reason is recorded in
`~/.agents-state/session-close/<session-id>.json`.

Closure means the verified frontend process has exited. Preserve shared backend processes, other CLI
clients, and the terminal containing this CLI. Worktree sharing does not prevent independent CLI closure.
If the individual client cannot be attributed and verified, preserve it and report the refusal. Never
terminate a shared backend or process tree to close one conversation.

```text
Two Codex clients use the same backend and worktree:
Close the verified frontend for this conversation. The other client and backend stay alive;
the terminal returns to its shell and the worktree remains on disk.
```

A session in a linked worktree also closes itself, unarmed, when a turn ends with its tree clean and its
branch's pull request merged at HEAD during the session.

Closing never removes a worktree or runs a worktree sweep. Checkout cleanup is a separate explicit
operation owned by `engineering:prune-worktrees` or `engineering:open-worktree`.

`peer-cli` closes other sessions.
