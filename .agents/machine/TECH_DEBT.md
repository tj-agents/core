# Tech debt — machine

## The Codex plugin cache is not reconciled

`~/.codex/plugins/cache/` accumulates orphaned plugin payloads exactly as the Claude cache did, and
`scripts/prune_plugin_cache.py` does not touch it.

Registry-is-truth, the rule the reconcile rests on, does not hold for Codex. Its registry is
`~/.codex/config.toml`, whose plugin entries record `enabled = true` and no install path at all, so a
cached directory cannot be matched to a live install. Those entries are also stale in their own right —
they still name plugins that were renamed away — which makes that registry the wrong copy rather than
the authoritative one. Pruning against it would preserve dead payloads and could remove live ones.

Left deliberately rather than guessed: the alternative is inventing a liveness rule for a source
already verified to be incorrect, shipped in the same change as the reconcile it would undermine.

**Resolution condition.** Either the Codex registry records a per-plugin install path, or its plugin
entries are reconciled against the marketplaces it actually resolves so the installed set can be
trusted. When either holds, add a Codex registry reader behind the same report-by-default,
fail-closed contract and delete this entry.

## Claude keeps a superseded plugin directory for 14 days, not for a session's lifetime

On 2026-09-22 every stop hook in a live session failed with `Plugin directory does not exist` after an
update. Claude Code 2.1.282 instead writes `.orphaned_at` into the superseded version directory and
deletes it 14 days later, so hooks keep their loaded path
([cleanup](https://code.claude.com/docs/en/plugins/loading#cleanup-of-previous-versions)); eight such
directories per core plugin were still present on 2026-09-28. `prune_plugin_cache.py --apply` keeps them
inside that window and `--pin` covers the live sessions it records. A session running longer than 14
days can still lose its hooks, and nothing in this repository sits between the host and its own cleanup.

**Resolution condition.** The host keeps a session's resolved plugin directory for that session's
lifetime, or exposes the resolved set so a supervisor can.

## Codex records no pin

The pin is written by the Claude SessionStart hook only. Codex's `machine-hooks.json` runs
`register_session.py` and not the reconcile, because the reconcile does not read Codex's cache at all
(above). Resolving that entry resolves this one with it.

## Launcher terminal detection trusts inherited environment variables

`agent_cli.launch_tab` picks the terminal from `TMUX`, `KITTY_WINDOW_ID` and `KONSOLE_DBUS_WINDOW`.
A GUI program started from a terminal inherits them, so a launcher run inside, for example, VS Code
started from Konsole opens its tab in that Konsole window, or fails if the window has closed.

Resolve when detection confirms the variable belongs to the terminal the caller is attached to, for
example by matching the terminal's own record of its sessions against the caller's process ancestry,
with a test for an inherited variable.
