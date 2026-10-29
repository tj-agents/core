---
name: continue
description: Establish Codex continuation for an existing authorized goal whose next decision requires a later wake.
metadata:
  tj-agents-kind: workflow
  tj-agents-domain: process
---

Read the [shared continuation workflow](../../../../.agents/workflow/skills/continue/SKILL.md).
It owns goal identity, authority, existing-owner reconciliation and observed-wake requirements.

Use native `/goal` for turn-by-turn continuation. For delayed work, use the owning conversation's
native Scheduled interface when the current surface exposes it. Desktop and supported web surfaces
provide Scheduled management; CLI and IDE do not. A native goal alone does not establish a durable timed
wake after its process exits.

```text
An authorized report needs a later source export -> native goal and an available Scheduled wake.
Software delivery must survive a Codex CLI exit -> engineering:persistent-delivery supplies its durable transport.
```

For a missing native surface, retain the concrete capability gate and continue authorized foreground
work. Software delivery loads `engineering:persistent-delivery` for its existing evidence contract and
required durable CLI transport. This generic workflow does not add PR or merge requirements to other goals.
