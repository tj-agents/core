---
name: search-claude
description: Find top-level native Claude sessions by topic or checkout before resuming one.
kind: utility
domain: machine
route: infer
---

# Search Claude sessions

Search local Claude history read-only and use the exact native id it returns. Results contain bounded metadata,
not raw transcripts, and omit sidechains.

```sh
python '<skill-directory>/../../resources/machine/scripts/agent_recovery.py' search --host claude --topic '<topic>' --checkout '<absolute-checkout>'
```
