# Work item session store

Central local record of every native Claude/Codex session and work-item status, written by hooks.
Location: `~/.agents-state/sessions.db` (honouring `AGENT_STATE_DIRECTORY`), SQLite in WAL mode. No
`ACTIVE_SESSIONS.md` and no `Status:` field in work-item READMEs; status lives in the database.

## Tables

- `sessions`: one row per `<host>:<native-session-id>` handle, never deleted. Columns: host,
  session_id, machine, profile, title, cwd, repo, branch, head, work_item, role (`owner` or
  `bounded: <scope>`), pid, pid_started_at, started_at, last_activity_at, turn_state
  (`working`/`awaiting_input`), ended_at, end_reason (`finished`/`closed`/`handed_off`), predecessor,
  successor.
- `work_items`: one row per `<repo>:<feature>/<item>` key. Columns: repo, feature, item, status
  (`proposed`/`active`/`blocked`/`paused`/`delivery-gated`/`done`), branch, pr, updated_at.
- `repo` is the `origin` remote as lowercase host plus path (`github.com/owner/name`; Azure DevOps SSH, HTTPS and legacy `visualstudio.com` remotes map to `dev.azure.com/<org>/<project>/_git/<repo>`, including the short `<org>.visualstudio.com/[DefaultCollection/]_git/<repo>` form, which maps to `dev.azure.com/<org>/<repo>/_git/<repo>`), else the absolute `git-common-dir`.

## Hook lifecycle

SessionStart (called in-process from `register_session.py`, after its existing registry write) upserts
the row and clears `ended_at`/`end_reason`, because a resumed session is alive again. UserPromptSubmit
sets `turn_state: working`. Prompt and Stop repair a missing current-session row through the native
registrar, including its PID and process start identity. Stop sets `turn_state: awaiting_input` and
refreshes cwd/branch/head. Claude
SessionEnd sets `ended_at` and keeps an earlier end reason, else `closed`. Codex has no SessionEnd hook,
so a hand-closed Codex tab reads as interrupted. Start and Stop attach an unclaimed session to a work item
when exactly one non-`done` work item in the same repo records the current branch. `finish.py`/`close.py`
best-effort record `finished`/`closed` for their own session before closing it.

## Read-time status

Computed, never trusted from storage, in order: `foreign` when the recorded machine differs; for a
not-ended row, `live`/`unknown` from `agent_recovery.liveness`; an ended row reports `finished`/
`handed_off` directly; otherwise (ended `closed`, or not-ended and dead), worktree staleness
(`stale`/`unknown` when the worktree is missing, its branch differs, or its recorded HEAD is not an
ancestor of the worktree's current HEAD), else `closed`. Only `closed` authorizes a resume.

## Commands

`work_item_sessions.py` is the only CLI over the store. Run it with `python` on Windows or `python3` on
Linux/macOS:

```sh
python '<skill-directory>/../../resources/machine/scripts/work_item_sessions.py' status '<feature>/<item>'
python '<skill-directory>/../../resources/machine/scripts/work_item_sessions.py' resume '<feature>/<item>'
```

- `claim <feature>/<item> --host claude|codex [--role owner|"bounded: <scope>"] [--predecessor <handle>]`:
  creates the work item (`active`, current branch, or no branch when it is the repository's default
  branch) when absent; a successful `owner` claim also fills a still-`NULL` branch, in the same
  transaction, when the current branch is not the default. Refuses a second live owner unless
  `--predecessor` names the live owner's handle, which hands its ownership off. Claiming `owner` runs one
  transaction that also clears `role` on every other owner row for the key, so at most one row owns a
  work item at a time, ever; a partial unique index enforces this at the database level. `--role` must be
  exactly `owner` or `bounded: <non-empty scope>`.
- `status <feature>/<item>`: read-only; reports each session's role, turn state and computed status.
- `find --worktree <absolute-path>`: read-only; reports the work item and handle recorded for that path.
- `resume <feature>/<item> [--handle <handle>]`: without `--handle`, resumes the single owner that is not
  ended or ended `closed`; refuses foreign, stale, live, unknown, finished or handed-off sessions, then
  calls `agent_recovery.open_session`.
- `interrupted [--all-repos] [--resume-all | --resume <handle>...]`: lists not-ended sessions whose recorded pid is dead, grouped by
  work item with their last turn state and computed status; resumes only listed handles whose status is
  `closed`, refusing stale, unknown, foreign, live, finished or handed-off ones.
  `--all-repos` uses this machine's whole registry and runs outside a Git repository. `--resume-all`
  selects eligible sessions deterministically, excludes completed work items, and opens them serially.
  Individual errors leave the other launches running; fresh native registration is required before
  success is reported. Repeated runs skip live sessions and respect pending or ambiguous launch receipts.
- `end --host claude|codex --reason finished|closed|handed_off [--successor <handle>]`: records the
  current session's end reason.
- `item <feature>/<item> --status <status> [--pr <url>]`: records work-item status, filling a still-`NULL`
  branch from a non-default branch.
