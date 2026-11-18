---
name: cd
description: Keep the active agent session attached to the exact repository or worktree that now owns the task. Use whenever work moves to a different directory, including after creating, cloning, moving, renaming, locating, or selecting a repository or worktree.
kind: policy
domain: behavior
---

# Keep the session in the working repository

When the task moves to a different repository or worktree, invoke the host's native
`/cd <absolute-path>` command immediately after the target directory exists and before continuing
repository-scoped work. Use the resolved repository or worktree root, including after creating, cloning,
moving, renaming, locating, or selecting it.

A shell `cd`, a per-command working directory, `git -C`, or an absolute file path changes where one
operation runs; it does not retarget the host session or its project association. None is a substitute
for `/cd`. Do not leave the conversation attached to the directory it happened to start in when another
directory now owns the work.

Moving, renaming, or deleting the directory that currently owns the host session has the same ordering
requirement. Retarget the host **before** any helper or native command unregisters or removes that directory.
A successful Git removal, or an empty residual directory, does not prove the host attachment was released;
the old path remaining on disk is incomplete cleanup.

Keep the same conversation and owner. Use the host's native directory-changing interface when it is
exposed to the agent; never send `/cd` through a shell. If the agent cannot invoke that interface, give
the user the exact `/cd <absolute-path>` command to enter in the host's input box, then ask them to say
`continue`. Explain that this changes the current conversation's directory. Pause repository-scoped work
until the host reports the target directory, retain the task and context, and leave this session open.
The directory change is a user action, not a request to approve the implementation again.

Missing agent access to `/cd` does not authorize a handoff, another terminal, a successor, or closing this
conversation. Use `workflow:handoff` only for a separately authorized context transfer. If the host has no
native directory-changing command, report that limitation and give the supported exact resume command
for this existing conversation; do not create or fork another conversation.

```text
Task moves to C:/work/meal-estimator; the agent has no native directory-control tool.
Reply: Enter /cd C:/work/meal-estimator in Codex, then say continue.
Keep this conversation open. Resume after the host reports C:/work/meal-estimator.
```

When the transfer exists to release the current directory for removal, the handoff must make the successor
the sole owner of the removal and final filesystem verification. After verified launcher submission the
original stops repository-scoped work; a completed delivery closes its own session through
`engineering:merge` Step 5's `finish`; only when that is unavailable does the `handoff` successor own the
removal, closing the predecessor through `agent:peer`, and the original must not attempt the removal itself.
The successor continues from the target checkout only after the predecessor no longer holds the old path,
and treats any removal error or residual path as incomplete cleanup.

For a separately authorized transfer needed to release a directory for removal, follow the ownership
and cleanup ordering above. A pending manual `/cd` keeps the current owner and is not a completed outcome.
