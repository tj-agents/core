# Code review — Chore/WorkboardSkillTests

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `d27f71b`  `(2026-09-23)`
**Judgment:** `changes-requested`

## Review pass — 2026-09-23 — full

**Candidate base:** `b43fa3f205ba7a2e94a6708554db9a55b83a22d5`
**Candidate head:** `d27f71bf44db4fa1bd89666549ec8be1496f2991`
**Candidate branch:** `Chore/WorkboardSkillTests`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:6c4437c4e39bc712ed446c55f4d284b5eea820d82e7a6fc90f4044c4f8a4e3ba` `(5 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\base-agents\.git\agent-workflow\runs\wb-review-1\review\11705dda643e13d7fbc1a6e1e717731b0023688f510d0c909d0a69bb46e2b99d`
**Candidate bundle identity:** `sha256:9bfeb6bf6a03d689e78c4f891baefa48f8d33120fabfe625c43e7c62d2dc1e91`
**Work-order path:** `reviews/Chore-WorkboardSkillTests.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

**Rules routed:** none. `skill_router.py --skills-for` over the five frozen paths reports
`no readable .agents/skill-routes.json` — this repository ships no route table, so no technical
standard is owed by the changed surface.

**Lens coverage:** the helper selected `native-general` and `workflow`. Both ran in the parent over the
frozen descriptor and materialized bundle, under the skill's stated fallback for unavailable dispatch.
`workflow_ops.py review-prepare` cannot complete on this machine (see the disposition below), so the
descriptor was taken from the bundle its first run left on disk and validated by hand: patch hash,
paths manifest, identity hash and tree-archive hash all reproduce.

### Findings

- [x] **WB1 — MEDIUM — native-general** — `.agents/engineering/utility/workboard/SKILL.md:194`
  The new no-match line claims the whole corpus holds nothing named for the needle, but it is printed
  before the out-of-scope tally and is contradicted by it on the very next line. The real acceptance
  run for this branch shows it:

  ```
  scope: Concertable. 0 open, showing 0. 0 named and marked done, hidden.
  nothing in ~/.claude/plans is named for 'authz'. Plans and roadmaps kept inside a repo are outside this corpus.
  out of scope: 18 in infonetica - rerun with SCOPE=all to include.
  ```

  Those 18 reached `elsewhere` through `about(folder) or about(path.stem)`, so they are precisely
  plans *named* for `authz` — they are merely in another group. The sentence is false whenever
  `elsewhere` is non-empty, and it is the line this branch added to stop the skill answering
  dishonestly, so the defect is self-defeating. It also misleads in the direction that costs most:
  a reader told nothing exists stops looking, which is the failure the plan's defect 3 exists to end.

  Fix: scope the claim to what was actually searched rather than to `~/.claude/plans` as a whole, so
  the out-of-scope line reads as a continuation instead of a rebuttal, and pin it with a test that
  runs the needle with an out-of-group match present.

  Fixed: the line now reads `nothing in scope is named for 'X'; ~/.claude/plans is the whole corpus,
  so a plan or roadmap kept inside a repo is never searched.` The Report section was corrected to say
  the out-of-scope tally counts plans that *are* named for the needle in another group, and both are
  read out together. `test_the_no_match_line_does_not_contradict_the_out_of_scope_tally` pins it;
  reverting the line reddens it and the existing no-match test.

### Verified and dismissed during synthesis

- `akin()`'s dropped direction is safe for every case the corpus relies on. Checked by exercising the
  extracted function over the argued pairs: `authorization`←`auth` yes, `auth`←`authz` no,
  `authored`←`authz` no, `authored`←`authorization` no, `authoring`←`authorization` no,
  `tenancy`←`tenant` yes, `pos`←`postgres` no, `migration`←`migrate` yes, `policies`←`policy` yes,
  `interface`←`internal` no. PR #24's own regression cases still hold against the real corpus:
  `reconcile` reports `every plan named for 'reconcile' is marked done`, `AB-28884` resolves to its
  infonetica group.
- The bounded-remainder stem rule is the right shape rather than the plan's suggested bounded
  *difference*. The difference rule separates the two pairs the plan named but still admits
  `interface`/`internal` (remainders `face`/`nal`, difference 1) and `configure`/`confident`
  (difference 0). Bounding each remainder rejects both.
- The new report branch is correctly ordered. `named` non-empty with `mentioned` empty still prints
  nothing, `named_seen` still wins with `every plan named for 'X' is marked done`, and the text-only
  branch still precedes it, so the new `elif` is reachable only when nothing matched at all.
- The prose rewrite matches the code it describes: five shared leading characters, at most three left
  over on each side, needle-first prefixing. The section still declares three rules and still has three.
- `tests/test_workboard.py` extracts the shipped Gather block rather than a paste, and asserts the
  documented mirror blind spot as current behaviour rather than as a wish. Every assertion was
  mutation-checked against the skill; reverting `akin()` to the merged version reddens exactly the two
  defect tests.
- The catalog digest change is one entry in each of the two generated copies, consistent with a single
  changed engineering skill. `sync-generated.ps1 -Check` and `update_catalog_digests.py --check` both
  report 0 changed at the frozen head.

### Out of scope, unchanged disposition

- `test_merge_review_gate.CanonicalEnvelopeShellTests` fails two tests on this machine and passes on
  CI. Reproduced identically against a pristine `git archive` of `2623d5d`, so it predates this branch,
  which touches no file it covers. The entry recorded in `reviews/Fix-PluginCacheReconcile.md` keeps
  its resolution condition.
- `workflow_ops.py review-prepare` cannot complete on this machine. `load_descriptor` re-invokes
  `materialize_tree`, which reopens the `tree.tar` it just wrote, and the second open fails with
  `OSError: [Errno 22] Invalid argument` on a 4.3 MB archive inside `.git` that is present and mode
  `0o100666`. Reproduced outside the helper with a bare `Path.open("wb")`, so the trigger is
  environmental — a scanner holding the freshly written archive — but the helper only meets it because
  it writes the same archive twice, once to build the bundle and again to validate it. The bundle it
  leaves behind is complete and verifies. Not this branch's code and not its defect; resolves when
  `load_descriptor` validates the existing archive instead of rewriting it, or when the environment
  stops locking it.
