---
name: recover-agents
description: Recover interrupted Codex and Claude agents through the deterministic local session-registry script. Use after a crash or reboot, to reopen all interrupted agents, or to resume a specific recorded work item or historical session.
kind: utility
domain: machine
route: infer
---

# Recover agent work

For a crash, reboot, or request to reopen all interrupted agents, execute this command directly. The
script selects sessions from SQLite, checks their identity and checkout, and resumes eligible agents
serially. It reports skipped sessions and individual failures. Do not assemble the session selection
with AI or search transcripts before running it. Use `python` on Windows and `python3` on Linux/macOS.

```sh
python -B '<skill-directory>/../../resources/machine/scripts/work_item_sessions.py' interrupted --all-repos --resume-all
```

Omit `--resume-all` for an inventory without launching agents. Repeated runs skip live agents and retain
pending or ambiguous launch safeguards. A recovered session is successful only after its fresh native
registration is verified. The database initializes itself when absent; a new PC starts with an empty
registry and needs its native histories to resume sessions from another machine. Historical JSON files
do not distinguish completed work from crash interruption and are not automatically reopened.

## Recover a specific historical session

Use `search-codex` and `search-claude` for the requested topic or checkout, then use `open-codex` and
`open-claude` for the relevant exact sessions with a concise instruction to continue. The user's recovery
request authorizes those resumes; clarify only when the relevant session or live identity is ambiguous.

Inventory both native histories first. The result groups the host, original checkout, title and exact native id.
Use the current goal or PR state to identify relevant work, then select only its returned `host:id` values. Do not
reopen every old session or infer unfinished work from a final transcript message. Run both commands below
with `python` on Windows or `python3` on Linux/macOS.

```sh
python '<skill-directory>/../../resources/machine/scripts/agent_recovery.py' recover --topic '<topic>' --checkout '<absolute-checkout>'
```

`recover` is read-only until an exact selection is supplied:

```sh
python '<skill-directory>/../../resources/machine/scripts/agent_recovery.py' recover --checkout '<absolute-checkout>' --select 'codex:<native-id>' --prompt 'Continue the requested work.'
```

Use `--codex-history-root '<profile>/sessions'` or `--claude-history-root '<profile>/projects'` for an alternate
profile. Unknown live identity requires reconciliation before a
resume, and ambiguous terminal launch results must not be retried.

## Continue a work item

When asked to continue a work item, run `work_item_sessions.py status '<feature>/<item>'`, then `resume`
on the same `<feature>/<item>`. Without `--handle` it resumes the single not-ended owner; with several
sessions and no single owner, pass `--handle`; with no sessions, start a new owner from the work item
README's `## Next Steps` and `claim` it. Run `interrupted` to find and resume sessions whose process died
without closing cleanly. See [`work-item-sessions.md`](../../resources/work-item-sessions.md) for the
session store's schema and commands.
