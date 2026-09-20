---
name: sync-checkout
description: Bring the whole local checkout up to date with reality, not just the current branch — fetch and prune, repair a stale origin/HEAD so the default branch is resolved rather than assumed, then detect whether the branch you are on already shipped (switch back to a clean default and delete it safely) or is still open (report drift and merge the default in when behind and clean). Covers why persistent branches are never auto-deleted, why merge and never rebase, and why brand-new local work looks identical to a shipped branch through one gh call. Use whenever the user wants to sync, sync with main, refresh the checkout, get up to date, or start a session on a clean current tree.

kind: operation
domain: process
model: gpt-5.6-luna
---

# Bringing the checkout up to date

Read and follow the [canonical shared definition](../../.agents/engineering/operation/sync-checkout/SKILL.md) in full.
This entry point supplies only Codex discovery metadata; the shared procedure is authored once under `.agents/`.
