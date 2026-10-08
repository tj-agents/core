---
name: search-codex
description: Find top-level native Codex sessions by topic or checkout before resuming one.
kind: utility
domain: machine
route: infer
---

# Search Codex sessions

Search local Codex history read-only. It returns only bounded metadata for top-level CLI sessions, including
the exact native id, original directory, activity, profile and live status. Do not expose raw transcripts.

```sh
python '<skill-directory>/../../resources/machine/scripts/agent_recovery.py' search --host codex --topic '<topic>' --checkout '<absolute-checkout>'
```

Use the returned native id and recorded directory with `open-codex`; never infer an id from a preview.
