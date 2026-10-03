---
name: create-credential
description: Create a token, API key or other credential in the browser from a pre-filled provider URL and deliver the value to its destination without it touching chat, a file or a command line. Use whenever a task needs a credential that does not exist yet — a missing secret, an auth failure traced to a missing token, or Tommy asking to create or rotate one.

kind: utility
domain: machine
route: infer
---

# Create a credential

Read and follow the [canonical shared definition](../../../.agents/machine/utility/create-credential/SKILL.md) in full.
This entry adds the Claude in Chrome mechanics the canonical procedure delegates to the host.

## Browser mechanics

Invoke the `claude-in-chrome` skill before its tools, then load every tool the flow needs in one
ToolSearch call: `tabs_context_mcp`, `tabs_create_mcp`, `navigate`, `computer`, `read_page`, and
`form_input` for fields the URL cannot set. Open the pre-filled URL in a new tab and verify the
page's actual selections with `read_page` before and after filling.

## Recorded quirks (2026-10-03)

- An automated click on the provider's copy button does not reach the OS clipboard, and a script
  calling `navigator.clipboard.writeText` hung the page for 45 seconds. The copy click is Tommy's;
  never script it.
- Reading the value from the DOM works but puts it in the transcript — only on Tommy's explicit
  acceptance, per the canonical boundaries.
- Claude Code's auto-mode classifier may deny the first delivery run as "Credential
  Materialization"; a PermissionDenied hook then allows a retry. Retry once; do not reroute the
  value to avoid the prompt.
