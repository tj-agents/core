---
name: create-credential
description: Create a token, API key or other credential in the browser from a pre-filled provider URL and deliver the value to its destination without it touching chat, a file or a command line. Use whenever a task needs a credential that does not exist yet — a missing secret, an auth failure traced to a missing token, or Tommy asking to create or rotate one.

kind: utility
domain: machine
route: infer
---

# Create a credential

Read and follow the [canonical shared definition](../../.agents/machine/utility/create-credential/SKILL.md) in full.
This entry adds the Codex browser mechanics the canonical procedure delegates to the host.

## Browser mechanics

Use the installed `browser@openai-bundled` plugin's `control-in-app-browser` skill and select
Chrome; it owns setup, tab binding and interaction. Do not substitute Computer Use or standalone
Playwright while that plugin is available.

If no browser backend connects, fall back without weakening the delivery: open the pre-filled URL
in the default browser with `Start-Process '<url>'`, let Tommy work the form, and deliver with the
canonical script's `-Prompt` mode so the value still never appears in chat or a command line.
