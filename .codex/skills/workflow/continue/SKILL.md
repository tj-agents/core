---
name: continue
description: Establish Codex continuation for an existing authorized goal whose next decision requires a later wake.
kind: workflow
domain: process
---

Read the [shared continuation workflow](../../../../.agents/workflow/workflow/continue/SKILL.md).
It owns goal identity, authority, existing-owner reconciliation and observed-wake requirements.

Use native `/goal` for turn-by-turn continuation. For delayed work, use the owning conversation's
native Scheduled interface when the current surface exposes it. Desktop and supported web surfaces
provide Scheduled management; CLI and IDE do not. A native goal alone does not establish a durable timed
wake after its process exits.

```text
An authorized report needs a later source export -> native goal and an available Scheduled wake.
Software delivery must survive a Codex CLI exit -> the selected Engineering package supplies its durable transport.
```

For a missing native surface, retain the concrete capability gate and continue authorized foreground
work. For software delivery, resolve the package containing the installed `engineering:merge` entry and
read its `.codex/runtime/continuation/README.md`. It supplies the required Codex CLI transport under this
same `workflow:continue` operation. Other goals retain their own acceptance criteria.
