---
name: search
description: Search local Codex or Claude conversation text using the packaged history reader. Use when the user asks where a past conversation discussed a subject.
kind: utility
domain: machine
---

# Search conversation history

Requires Python 3.9+ and the selected harness's local transcript data. Use the packaged read-only helper:

```text
python -B "<skill-directory>/../../resources/machine/utility/scripts/history.py" search --host codex --pattern "<literal term>"
```

Select `--host claude` for Claude. Respect the named harness; otherwise use the current host. The default
search is literal and case-insensitive over user/assistant message text. `--regex` explicitly enables a
regular expression; `--show-lines` returns matching text only when the user needs it. Use `--project`,
`--cwd`, `--count` or `--history-root` to narrow the request. Quote arguments for the calling shell.

The helper reads CODEX_HOME/sessions or CLAUDE_CONFIG_DIR/projects, with their native home defaults.
Those are user data locations, not executable dependencies. It does not search tool payloads, write
transcripts or upload data. Missing directories fail clearly; no matches produce an empty list.
Summarize relevant hits and returned resume commands without dumping raw transcripts or publishing data.
