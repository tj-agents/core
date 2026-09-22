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
