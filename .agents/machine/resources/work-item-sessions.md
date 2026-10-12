# Work item session registry

Interim durable record of active native Claude/Codex sessions per work item, until Termboard supersedes
it. Location: `plans/features/<feature>/work-items/<work-item>/ACTIVE_SESSIONS.md`. Absence means no
recorded session for that work item.

## Format

```markdown
# Active sessions

## codex:01a12aa7-5b58-7312-9400-ef710762147f
- Role: owner
- State: active
- Machine: <hostname>
- Profile: <absolute config dir>
- Title: <tab title or none>
- Worktree: <absolute path>
- Branch: <branch>
- PR: <https URL, or not opened>
- Head: <40 lowercase hex>
- Predecessor: <handle, or none>
- Successor: <handle, or none>
- Verified: <UTC ISO-8601 ending in Z, e.g. 2026-10-12T19:30:00Z>
- Resume: `machine:open-codex --id <id>`
```

One `## <handle>` section per session, `<host>:<native-session-id>`, host `claude` or `codex`. Handles are
unique; exactly the 13 fields above, each once, in any order, no unknown fields.

- `Role`: `owner` (at most one per work item, the delivery-branch writer) or `bounded: <scope>` for a
  concurrent agent with a disjoint scope.
- `State`: `active` or `handing-off`. Liveness is never stored.
- `Machine`/`Profile`: `socket.gethostname()` and the host's config directory (`CLAUDE_CONFIG_DIR` or
  `~/.claude`; `CODEX_HOME` or `~/.codex`), compared case-insensitively against the reading machine.
- `Worktree`/`Branch`/`Head`: the recording session's absolute git worktree, current branch and HEAD.
- `PR`: an `https://` URL or `not opened`.
- `Predecessor`/`Successor`: a valid handle or `none`.
- `Resume`: exactly `` `machine:open-claude --resume <id>` `` or `` `machine:open-codex --id <id>` ``.

## Lifecycle

Record a row on taking ownership (plan pickup, handoff acknowledgement, or a bounded lease). Refresh
`Head`/`PR`/`Verified` only at material checkpoints, in the same substantive commit as the work-item
README update. Handoff: the predecessor sets `State: handing-off` before launch; the successor records its
row with `Predecessor:` set, which removes the predecessor's row. Remove a row once that session's work is
terminal, in the commit that records the outcome. The file is deleted when its last row is removed.

## Read-time status

Computed, never written: `live`/`closed`/`unknown` from `agent_recovery.liveness`, `foreign` when `Machine`
differs from the reading machine, and `stale` (`worktree-missing`, `branch-mismatch`, `head-mismatch`, or `branch-unknown`/`head-unknown`)
when git cannot confirm the recorded worktree. `unknown`, `stale` and `foreign` authorize nothing: no resume, no
new writer and no worktree deletion until the row is reconciled.

## Helper

`work_item_sessions.py` parses, validates, reports status, finds a work item by worktree, resumes the
recorded session through the guarded `agent_recovery.open_session`, and records/removes the current
session's row. Run it with `python` on Windows or `python3` on Linux/macOS:

```sh
python '<skill-directory>/../../resources/machine/scripts/work_item_sessions.py' status '<work-item-directory>'
python '<skill-directory>/../../resources/machine/scripts/work_item_sessions.py' resume '<work-item-directory>'
```

Subcommands: `validate`, `status`, `find --worktree <dir> --root <repo-root>...`, `resume [--handle H]`,
`record --host claude|codex --role <owner|bounded: scope>`, `remove [--handle H] [--host H]`.
