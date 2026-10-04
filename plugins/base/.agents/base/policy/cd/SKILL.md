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

Use the host's native command interface rather than sending `/cd` through a shell. If that interface is
not exposed to the agent, resolve and invoke the unqualified `handoff` workflow with the exact target
checkout. That workflow checkpoints the current owner, selects the supported Codex launcher by default,
starts exactly one successor, verifies launcher submission, and releases the original writer.

When the transfer exists to release the current directory for removal, the handoff must make the successor
the sole owner of the removal and final filesystem verification. After verified launcher submission the
original stops repository-scoped work and releases its host session; it must not attempt the removal itself.
The successor continues from the target checkout only after the predecessor no longer holds the old path,
and treats any removal error or residual path as incomplete cleanup.

Only after the automatic `handoff` capability is genuinely unavailable, or its launcher fails after
diagnosis, give the user the exact `/cd <absolute-path>` command and pause repository-scoped work until the
session has been retargeted. Never claim that a shell directory change updated the session, and never make
manual `/cd` the normal transfer path.
