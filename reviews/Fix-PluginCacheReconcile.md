# Code review — Fix/PluginCacheReconcile

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `fbcb83dbff5dc347c67ca0e0754aec06b4a954ef`  `(2026-09-22)`
**Judgment:** `approved`

## Review pass — 2026-09-22 — full

**Candidate base:** `0972aae2cf324bc004e6bde4c3d9d65440fc62ac`
**Candidate head:** `261cde666fe28306966c7e5da57f38fec8403ef4`
**Candidate branch:** `Fix/PluginCacheReconcile`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:2da3c35cebd6fbcd10e2290608a50f6f621a6bb18e58089a24872ab8bd3daa5e` `(94 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\base-agents\.git\agent-workflow\runs\review-plugincache-20260922\review\5f1630691842a6656c25de3df7afdb551f684e9fc9b4a51b9199cbc28e854afc`
**Candidate bundle identity:** `sha256:0190e6da279e41cad09d2b7134572124b5c09dc166eafdcdd8cd092518955046`
**Work-order path:** `reviews/Fix-PluginCacheReconcile.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

### Findings

- [x] **PC1 — MEDIUM — native-general** — `.agents/machine/scripts/prune_plugin_cache.py:225`
  `state_directory()` defaults to `Path.home() / ".agents"`, but the machine plugin already owns
  `AGENT_STATE_DIRECTORY` in `.agents/machine/peer-cli/scripts/register_session.py:22`, where the same
  variable defaults to `Path.home() / ".agents-state"`. Two scripts in one plugin therefore read one
  env var and resolve two different roots when it is unset. The default chosen here is also a foreign
  directory: `~/.agents-state/` is the machine plugin's own state home (`cli-sessions/`, `currency/`,
  `published-manifest.json`), while `~/.agents/` belongs to the deprecated agent-standards deployment
  (`skills/`, `standards/`, `claude-marketplace-refresh.json`, `sync-claude-skill-stubs.ps1`). Once the
  packaged SessionStart hook ships, every throttled notice writes `plugin-cache-notice.json` into that
  unrelated system's directory. Not yet observed on disk only because the hook is not installed at the
  reviewed head. Fix: default to `Path.home() / ".agents-state"` so the unset-variable case matches the
  plugin's existing owner, and keep the notice state under the machine plugin's own root.

No other finding was retained. Verified and dismissed during synthesis: reparse-point removal is correct
(`Path.unlink()` on a Windows directory junction succeeds and leaves the target intact, confirmed
empirically); the `AGENT_STATE_DIRECTORY` variable name itself matches the plugin convention; `classify`
accumulates into a shared `states` dict but each plugin's entries are disjoint, so no cross-plugin
mislabelling occurs; both hosts' packaged SessionStart hook commands resolve to files that exist in the
generated payloads; and no reference to the removed `machine/utility` path segment remains anywhere in the
tree under any path separator.

  **Resolved** in `fbcb83d`: the default is now `Path.home() / ".agents-state"`, matching
  `register_session.py`. Verified the delta contains exactly that one-line change.

## Review pass - 2026-09-22 - incremental

**Candidate base:** `261cde666fe28306966c7e5da57f38fec8403ef4`
**Candidate head:** `fbcb83dbff5dc347c67ca0e0754aec06b4a954ef`
**Candidate branch:** `Fix/PluginCacheReconcile`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:1aee893cc5c522574163d9f0a9e010d9cd27612979d44058643c2317832c909b` `(5 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\base-agents\.git\agent-workflow\runs\review-plugincache-20260922\review\35e1ffdec0e78c95db54c32fb1ec2ed557093df6e63991d65a3f95a9c745fe7d`
**Candidate bundle identity:** `sha256:4ad14816568aec4476f3972f14e78ff5abee7588f1901cf6f73cf6274fd2db4b`
**Work-order path:** `reviews/Fix-PluginCacheReconcile.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

### Findings

No new findings. The delta is the PC1 remediation only: the one-line default change in
`.agents/machine/scripts/prune_plugin_cache.py`, its regenerated payload copy, the two catalog digests
that follow from it, and this work order. The regenerated copy is byte-identical to its source apart
from checkout line endings, which `test_generated_text_bytes_are_stable_across_checkout_line_endings`
already owns. Reconcile tests and both generation checks pass at the frozen head.
