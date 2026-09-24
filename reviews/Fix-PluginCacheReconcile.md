# Code review — Fix/PluginCacheReconcile

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `6a7600f`  `(2026-09-23)`
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

## Review pass - 2026-09-22 - incremental

**Candidate base:** `fbcb83dbff5dc347c67ca0e0754aec06b4a954ef`
**Candidate head:** `a82ed3b`
**Candidate branch:** `Fix/PluginCacheReconcile`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:06e7405821fe39b82d73347465d46f2ab226a245fb16e4ef88c98eae22359a1b` `(14 paths)`
**Work-order path:** `reviews/Fix-PluginCacheReconcile.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Reviewed natively in the owning session; no lens subagent was dispatched. The delta carries the two
properties the prior passes did not cover - a session pin that makes removal a liveness check, and a
reader for the rename alias table - plus the work-order commit itself.

### Findings

- [x] **PC2 — MEDIUM — native-general** — `.agents/machine/scripts/prune_plugin_cache.py:record_pin`
  The pin file is keyed by the hook's parent pid, and two sessions can share one parent. Writing the
  file replaced its `paths`, so a second session's pin dropped the first session's directory from the
  held set while that session was still bound to it. That is the failure the pin exists to prevent,
  reintroduced by the pin's own bookkeeping. Narrow - it needs a shared long-lived parent - but the
  consequence is exactly failure 3 and the safe direction costs nothing.

  **Resolved** in `a82ed3b`: `record_pin` unions the live registry set with whatever the file already
  holds, via `held_by()`, which reads an unreadable pin as holding nothing. Over-retention stays
  bounded by expiry; a lost pin was not bounded by anything. Two tests cover it.

Verified and dismissed during synthesis:

- `read_pins` treating an unreadable pin as expired is correct, not a silent swallow: such a pin names
  no paths to protect, so trusting it would only defer its own removal indefinitely.
- The dry run reads the pin registry and writes nothing; the sweep sits inside the `--apply` branch and
  under `--pin`, and a test asserts the dry-run case.
- `classify` gives `PINNED` precedence over every dead state and excludes it from `--keep-previous`, so
  a pinned directory cannot be consumed by the retention count.
- One-hop alias following cannot loop; the chain test asserts a two-hop chain is not resolved.
- An unreadable alias table resolves to no aliases rather than an error, which can only restore the
  behaviour that preceded it - asserted by test.
- `skill_aliases()` probes the packaged sibling then the source-tree spelling; both are exercised, the
  first by the synthetic-plugin tests and the second by the shipped-table test.
- `ALIAS_CANDIDATES` is computed at import from `__file__`, so a vendored copy resolves against its own
  location exactly as `SHIPPED_ROUTES_DIR` already does.
- The alias is consulted only when nothing resolved, so an exact match always wins over a rename record.

Not fixed here, unchanged disposition: `test_merge_review_gate.CanonicalEnvelopeShellTests` still fails
two tests on this machine and passes on CI. This branch touches no file it covers. The entry recorded
in the completed pass above keeps its resolution condition.

## Review pass - 2026-09-23 - incremental

**Candidate base:** `a82ed3bd360c6a2d30ca4a4535d0291582d8ca5c`
**Candidate head:** `6a7600f9362aaade10231eb336608a7b9962a363`
**Candidate branch:** `Fix/PluginCacheReconcile`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:5344335b3bbe24f5d516b9ba8bd79619286595f131fe5d4b58666a540026fd66` `(9 paths)`
**Work-order path:** `reviews/Fix-PluginCacheReconcile.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Two fresh read-only lenses were dispatched over `a82ed3b..4d34cad` — one on matcher correctness, one
on prose/code agreement and the corpus-selection change — alongside the owning session's native pass.
The range was re-frozen at `6a7600f` to carry the remediation, as the passes above did. The delta is
the `/workboard` skill: repo-group scoping, subject matching, and the corpus rule.

### Findings

- [x] **WB1 — HIGH — lens:matcher** — `.agents/engineering/utility/workboard/SKILL.md` `matches()`
  The needle was lowercased but never tokenized, while every candidate word came from `[a-z0-9]+`.
  Any punctuation in the needle therefore made all three clauses structurally unsatisfiable, and the
  run printed zero rows with no diagnostic at all. Demonstrated: `FILTER=AB-28884` from
  `infonetica/cris-diligence` returned nothing while `cris-diligence/AB-28884-country-risk-domain-split.md`
  sat in the corpus; `pr-633` and a pasted leading space failed the same way. This is the exact defect
  class the change was made to remove.

  **Resolved** in `6a7600f`: the needle goes through the same `words()` normalizer and every typed
  word must match, which also makes a multi-word needle work — `b2b accept` now finds
  `B2B_ACCEPT_UNION_HANDOFF.md`. Verified from both repos.

- [x] **WB2 — HIGH — lens:corpus** — same file, corpus selection
  Restricting the corpus to one directory deep excluded real plans, so the prose claim that nothing
  nested is a plan was false. `Concertable/Post Launch Scalability/WORKFLOW_DIVERGENCE_DECISION.md` —
  a 54KB decision doc with no depth-2 namesake — became permanently invisible.

  **Resolved** in `6a7600f`: a **flat** subfolder (no subdirectories of its own) is a plan folder and
  is read; only a subfolder with its own structure is a copied repository tree and is skipped whole.
  Profiled every depth-2 directory to confirm the test is total on this corpus: all six mirrors have
  subdirectories, every hand-made folder has none. Selection goes 170 → 172 files, 80% still excluded.
  Two plans dropped inside `Concertable/b2b/` remain invisible; the skill now states that blind spot
  and says to move such a file up rather than teaching the rule to guess.

- [x] **WB3 — MEDIUM — native + both lenses** — same file, bucket/report interaction
  The completion filter ran after bucket selection, so a plan named for the needle but marked done
  left `named` empty; `rows = named or mentioned` then fell back to text-only rows and printed
  `no plan is named for '<needle>'`. Demonstrated: `FILTER=reconcile` from this worktree printed that
  line while `base-agents/PLUGIN_CACHE_RECONCILE.md` is named for it and merely finished. The reader is
  instructed to read those lines out, so the false claim propagates. `hidden` was also charged across
  both buckets while only one is ever printed.

  **Resolved** in `6a7600f`: a `named_seen` flag distinguishes the two cases and the run now says
  `every plan named for 'reconcile' is marked done`; `hidden` counts name hits only and the footer
  says so.

- [x] **WB4 — MEDIUM — lens:corpus** — same file, "Report"
  "only about one in eight uses checkboxes" was measured on the pre-change walk (112/841 = 13.3%).
  The change invalidated it: 4 of 172 selected files carry checkboxes, about one in forty. Independently
  re-measured before correcting the prose.

  **Resolved** in `6a7600f`: restated as one in forty.

- [x] **WB5 — LOW — lens:corpus** — same file, scope skip
  A loose root plan gets `group = None`, so the out-of-group skip never fired and all seven listed in
  every session regardless of `SCOPE` — including `vectorized-gathering-pinwheel.md`, which is
  Infonetica due-diligence work. The prose asserting the guarantee sits in the changed section.

  **Resolved** in `6a7600f`: an ungrouped root plan is `unfiled`, counted in the one-line notice and
  shown only under `SCOPE=all`. The `"(loose)"` display placeholder no longer feeds the matcher, which
  also retires the lens's separate observation that `FILTER=loose` reported every root plan as named.

- [x] **WB6 — LOW — native** — same file, `plan_files()` / `group_of()`
  Replacing `rglob` with `glob` dropped the `.git`/`node_modules` guard, and `pathlib.Path.glob` does
  match dotted directories (confirmed empirically). No such directory exists under `~/.claude/plans`
  today, so the exposure was latent rather than live — but the machine-transferable direction puts
  plans inside repositories. Separately `group_of()` called `repos.iterdir()` unguarded, so a machine
  with no `~/source/repos` got a `FileNotFoundError` instead of a board.

  **Resolved** in `6a7600f`: guard restored, `repos.is_dir()` checked.

- [x] **WB7 — LOW — lens:matcher** — same file, argument parsing
  `limit = int(sys.argv[2] or 20)` was unguarded while `FILTER` and `SCOPE` were not, so `LIMIT=all`
  killed the whole run with a traceback and a negative value made `showing %d` disagree with the rows
  printed. Pre-existing rather than introduced here, fixed because it is one line in a file already
  open. `path.stat()` sat outside the `try` that guards the read, so a plan deleted mid-run by another
  session destroyed the board after all the work was done.

  **Resolved** in `6a7600f`: `LIMIT` falls back to 20 unless it is a non-negative integer; `mtime` is
  read under the same guard as the text.

Verified and dismissed during synthesis:

- `group_of` is O(files x repos) with no memoization. Measured at 0.070s of a ~1.0s run on the real
  corpus (12 distinct projects, 170 files); memoizing saves 0.062s and was not worth the change.
- The empty-needle path is safe: `about("")` is `all()` over an empty token list, so every file buckets
  as `named` and the unfiltered board is unchanged.
- `rows = named or mentioned` aliases a bucket and `rows.sort()` mutates it in place; nothing after
  that point reads bucket order, only length and truthiness, so there is no observable effect.
- The generated copies are byte-identical to their canonical source, the two host entry points differ
  only in the host name and their relative link depth is correct, and nothing else in the repository
  asserts the frontmatter description text.
- `HTTPServer` tokenizing to one word is the known cost of the lower-to-upper boundary rule, not a
  separate defect.

Not fixed here, unchanged disposition: `test_merge_review_gate.CanonicalEnvelopeShellTests` still fails
two tests on this machine and passes on CI. This delta touches no file it covers.
