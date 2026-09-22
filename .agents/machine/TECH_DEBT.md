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

## A session pin protects against this tool, not against the host's own update

`--pin` stops `prune_plugin_cache.py` from removing a version directory a running session resolved at
startup. It does not stop Claude Code itself. The host updates a plugin in place and deletes the
superseded directory while sessions are still bound to it, which is how every stop hook in a live
session began failing with `Plugin directory does not exist` on 2026-09-22. Nothing in this repository
sits between the host and its own cache, so that path is unchanged.

What the pin does change: this repository is no longer a second cause of the same failure, and the pin
file records what a session was bound to, which is the evidence a recovery would need.

**Resolution condition.** The host pins a session's resolved plugin directory for that session's
lifetime, or exposes the resolved set so a supervisor can. Until then, do not describe the pin as a
fix for mid-session plugin updates — it bounds our own garbage collection only.

## Codex records no pin

The pin is written by the Claude SessionStart hook only. Codex's `machine-hooks.json` runs
`register_session.py` and not the reconcile, because the reconcile does not read Codex's cache at all
(above). Resolving that entry resolves this one with it.
