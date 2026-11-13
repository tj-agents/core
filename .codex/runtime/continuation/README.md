# Codex CLI continuation runtime

Opt-in. Use it only when the user asks for unattended progress and the unattended software delivery
reference, `references/delivery.md` beside the installed `workflow:continue`, selects it. Installing the
package registers nothing, grants no scheduler permission and proves no host acceptance.

The runtime keeps authorized software work going after its Codex CLI process exits by launching a fresh
headless `codex exec` context in the initialized checkout; other hosts are rejected. Reconcile any existing
registration with its recorded owner before changing continuation mechanisms.

## Initialize and claim the owner

Run the packaged `<workflow-package-root>/.codex/runtime/continuation/continuation_runtime.py`, resolving the
package root from the installed skill entry, or the same path in a Core checkout, with Python 3.12 or newer
(`python` on Windows, `python3` on Linux/macOS):

```text
python -B "<workflow-package-root>/.codex/runtime/continuation/continuation_runtime.py" init --root ROOT --goal GOALPATH --completion TEXT --actions ACTION [ACTION ...] --authority TEXT --harness codex
```

`init` records one owner at `.agents/continuation/owner.json` below the worktree, before any PR exists.
`GOALPATH` is an existing worktree-relative file or an explicit absolute path to an external goal; escapes,
missing files and directories are rejected. On `canonical-owner-path-required`, retry `init --root ROOT`
without `--owner`.

The foreground session claims the owner with `claim --owner OWNER --pid PID`, where PID is that long-lived
session, not a tool shell. The returned `foreground.token` is required by `heartbeat`, `yield` and
`checkpoint`. Heartbeat while working; yield with a reason and next action before waiting; checkpoint only a
real `waiting`, `blocked` or `complete` state. `status --owner OWNER` and `wake --owner OWNER` inspect and
run it.

## Child receipts

The child reports through `CONTINUATION_RESULT_PATH`, `CONTINUATION_NONCE` and `CONTINUATION_OWNER_ID`:
state, reason, next action and an optional exact identity rebind. When a repaired head ends with a terminal
`complete` or `blocked` receipt that releases a recorded delivery binding, it includes the refreshed
binding as `released_binding` plus exact `rebind.old` and `rebind.new` identities matching the owner's PR,
repository, worktree, branch and HEAD. The supervisor checkpoints while it holds the writer lock; the child
never does. The lease coordinates the runtime's own writers only.

## Register the wake

`<workflow-package-root>/.codex/runtime/continuation/delivery_continuation.py` supports `register`, `remove`,
`list` and `wake`. Claim the owner before `register`, yield before waiting, never register a second task for
an owner and remove it only at a terminal result. Pin the native host executable:

```text
python3 -B "<workflow-package-root>/.codex/runtime/continuation/delivery_continuation.py" register --owner OWNER --host-executable /absolute/path/to/codex
python -B "<workflow-package-root>\.codex\runtime\continuation\delivery_continuation.py" register --owner OWNER --host-executable C:\absolute\path\to\codex.exe
```

Linux needs a reachable `systemctl --user` manager and creates a receipt-owned user oneshot service and
timer; Windows needs inbox Windows PowerShell's ScheduledTasks. Neither changes lingering or login policy.
`--dry-run` shows a registration without changing anything. Other platforms have no adapter: say so and
continue in the foreground.

Unattended progress is established only by initialization, claim, registration and an observed wake. The
child runs at the packaged L4 lane. The owner is bound to one worktree and branch and may rebind only a new
head within them; it never moves to another PR or checkout, and finishing its PR does not finish the goal.

Budgets default to six child launches, three consecutive transport failures, a 24-hour deadline and a
900-second child timeout. Tighter user limits win. Never raise them silently or add bypass-permission
flags. An unsupported host or unavailable runtime reports the missing capability and leaves a recoverable
checkpoint.
