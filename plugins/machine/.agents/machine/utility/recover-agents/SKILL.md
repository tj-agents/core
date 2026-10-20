---
name: recover-agents
description: Inventory local Codex and Claude sessions for relevant work, then reopen only explicitly selected sessions.
kind: utility
domain: machine
route: infer
---

# Recover agent work

Use `search-codex` and `search-claude` for the requested topic or checkout, then use `open-cli` with each
relevant exact id and a concise instruction to continue; it chooses the host and focuses a live tab itself.
`recover --select` below refuses a live session instead of focusing it. The user's recovery
request authorizes those resumes; clarify only when the relevant session or live identity is ambiguous.

The inventory reads the session store (`~/.agents-state/sessions.db`) first: every topic word must appear in the
session's title, id, checkout, repository, branch, or its work item's key, title or plan path. `matched_by` names
the fields that matched, and each result carries its work item. Native histories are scanned only when the store
has no match, or with `--include-history`. Use the current goal or PR state to identify relevant work, then
select only returned `host:id` values. Do not reopen every old session or infer unfinished work from a final
transcript message. Run both commands below with `python` on Windows or `python3` on Linux/macOS.

```sh
python -B '<skill-directory>/../../resources/machine/scripts/agent_recovery.py' recover --topic '<topic>' --checkout '<absolute-checkout>'
```

`recover` is read-only until an exact selection is supplied:

```sh
python -B '<skill-directory>/../../resources/machine/scripts/agent_recovery.py' recover --topic '<topic>' --select 'codex:<native-id>' --prompt 'Continue the requested work.'
```

A selected open is reported only after the resumed session registers in the store or writes its native history;
launch starts the native CLI without refreshing plugins. Exit 1 means the launch failed and prints the
cause; it can be retried after fixing that. Exit 3 means the tab started but the session was not seen to resume;
check that tab and do not retry.

Use `--codex-history-root '<profile>/sessions'` or `--claude-history-root '<profile>/projects'` for an alternate
profile. Unknown live identity requires reconciliation before a resume.

## Continue a work item

When asked to continue a work item, run `work_item_sessions.py status '<feature>/<item>'`, then `resume`
on the same `<feature>/<item>`. Without `--handle` it resumes the single not-ended owner; with several
sessions and no single owner, pass `--handle`; with no sessions, start a new owner from the work item
README's `## Next Steps` and `claim` it. Run `interrupted` to find and resume sessions whose process died
without closing cleanly. See [`work-item-sessions.md`](../../resources/work-item-sessions.md) for the
session store's schema and commands.
