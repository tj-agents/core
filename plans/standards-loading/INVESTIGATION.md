# Standards loading: investigation and recommendation

2026-11-12. Research only; nothing implemented. Evidence was reproduced against the installed plugins
(`base` 6339abcf / dab78bb9) and current host docs.

## Verdict

The standards are not the problem. The loading design is. Standard bodies are injected by a PreToolUse hook,
and that has three structural faults. Trimming would not fix any of them:

1. **The standard arrives after the edit.** Claude Code places PreToolUse `additionalContext` "next to the
   tool result" ([hooks docs](https://code.claude.com/docs/en/hooks)). The write has already been composed
   and applied before the agent sees the standard. Every first write to a file therefore happens without the
   standard, by construction. This explains the cli session: `rust:errors` *was* injected on the first
   write and the code still broke it.
2. **One hook output is capped at 10,000 characters, with no setting to raise it.** Anything longer is saved
   to a file with a 2,000-character preview, and the agent is not told to read the file (docs; CHANGELOG
   2.1.89). One stack does not fit: Rust's core standards alone are 12.4k characters, Python's 34k and
   .NET's 167k. The hook pages the rest into "later writes" that may never happen.
3. **Selection is per repository, not per file.** `path_standards` takes the stack whose path matches, then
   appends *every other* gated stack. It also never filters profiles. The result is that each write sees
   the same queue of 30 standards (61k characters).

The agent-loaded path that should back this up is also broken, for three reasons. The skill listing drops
most descriptions. Skill entries are pointer stubs. And the hook's wording tells agents the standards
arrive automatically.

No widely used collection delivers standards the way we do. They all use short always-on rules, rules

## 1. Delivery today, measured

| Channel | What it carries | Measured |
| --- | --- | --- |
| SessionStart (`tier_gate.py --session-context`) | Tier and scope statement, ubiquitous plugin list | 1,277 chars in core. It takes **12.2 s** and always ends with "time limit reached while evaluating repositories" and scope "undetermined". Core has 89 nested worktrees under `.worktrees/`, and scanning them exceeds `GIT_TIMEOUT = 10`. |
| PreToolUse on `Read\|Edit\|Write\|MultiEdit\|NotebookEdit\|Glob\|Grep` | Tier context. On writes it also carries standard bodies, ≤10,000 chars | cli worktree (rust + python + github-actions): **7.8 s on a Read, 9.5–13.5 s on an Edit**, with other sessions running. `TOOL_CONTEXT_SECONDS = 20`, so a loaded machine flips classification to "undetermined". |
| Skill listing | Name + description, model-decided loading | 22 tj-agents plugins are installed at **user scope**: 253 skills, all listed in every repo. In this session about 54 of roughly 258 tj-agents entries show a description. The rest, including `rust:build`, `rust:domain-design` and every selected `python:*` except `style`, are names only. |
| Skill entry (`skills/<name>/SKILL.md`) | What the Skill tool loads | For **110 of 119** standards, the entry only says "Read and follow the canonical definition". Loading a standard takes two hops. |
| AGENTS.md "Repository standards" index | "Before the first edit, read the full standards…" | Present in core. The cli worktree's AGENTS.md has none and only says "Apply the selected `rust@tj-agents` standards." |

### What a write receives (reproduced in `cli.worktrees/Feature-82-TjMessage`)

| Write | Hook injects | Deferred |
| --- | --- | --- |
| 1st `src/main.rs` (9,712 chars) | rust:build, domain-design, errors, explanation, libraries, testing | rust:structure, style, persistence, all github-actions:*, all python:* |
| 2nd (9,801 chars) | rust:structure, style, **persistence** (no database in this repo) | github-actions:*, python:* |
| 3rd (9,553 chars) | github-actions:build, domain-design, errors, explanation, libraries, security | python:* |

`.github/workflows/ci.yml`, `scripts/x.py`, `Cargo.toml` and `tests/x.rs` all select the same 30 standards
(61,271 chars), only reordered. It takes about seven writes to drain the queue.

What a write *should* receive:

- A Rust source write needs about 6 standards, ~10k chars: structure, errors, style, domain-design, build,
  testing.
- A Python write needs about 10, ~30k.
- A .NET write needs the 9 core standards (~29k) plus whichever adopted profiles apply.

Only Rust comes close to fitting one hook output, and none of them arrive before the write.

## 2. Why the 10,000-character bound exists

The bound is real, not assumed. Claude Code 2.1.89: "Changed hook output over 10,000 characters to be saved
to disk with a file path + a 2,000-character preview". The current docs say the cap "has no setting or
environment variable to raise it". Codex's default `additionalContextLimit` is 2,500 tokens. Base raises it
to 5,000 for `apply_patch`, so Codex carries the same text. The bound is correctly measured. The mistake is
using hook output as a document channel at all.

Invoked skill bodies have no comparable cap. "the rendered SKILL.md content enters the conversation as a
single message and stays there" ([skills docs](https://code.claude.com/docs/en/skills)). After compaction,
5,000 tokens per skill are re-attached.

## 3. The standards themselves

- **Size:** 119 standards. Median 2,718 chars, p90 6,563, max 31,764 (`engineering:plans`). Public medians
  are larger: anthropics/skills 8.3 KB, obra/superpowers 7.8 KB, wshobson/agents 5.5 KB. **The set is not an
  outlier in size; ours are smaller.**
- **Count:** 253 skills is large, but wshobson/agents ships 185 skills plus 202 agents. The outlier is
  installing all 22 plugins at user scope, so .NET, React and Azure descriptions compete for the listing in a
  Rust repo. The listing budget is 2% of context (2.1.32), and descriptions are dropped beyond it.
- **Descriptions:** median 251 chars, max 1,036, total 79.6k. None reaches the 1,536 cap. Trimming them helps
  the listing only slightly. Scoping installs helps a lot.
- **Dead weight:**
  - 10 stubs under 400 chars say "nothing applies until it is recorded here": dotnet:build, react:build,
    domain-design and errors, azure:domain-design, errors, libraries and testing, rust:libraries,
    rust:testing. They spend listing slots and injection slots and govern nothing.
  - `*:explanation` (~500 chars per stack) governs how code is quoted in explanations, not files, yet it is
    injected on every write.
- **Profiles:** 40 standards (200k chars) belong to non-core profiles, such as rust:persistence and
  dotnet:errors-carriers. Profile adoption never reaches selection.

## 4. Comparison

| Collection | Selection | Delivery | Size |
| --- | --- | --- | --- |
| Claude Code native | `.claude/rules/*.md` with `paths:`; skill `paths:` | Rule loads on Read/Write/Edit of a matching file (Read comes first, so before the edit) | CLAUDE.md under 200 lines |
| Codex native | Nested AGENTS.md (root down to cwd, 32 KiB); skills listing (2% / 8k chars) | Always-on docs; agent-loaded skills; no glob activation | |
| Cursor | always / glob / agent-requested / manual | Start of context | Rules under 500 lines |
| GitHub Copilot | `applyTo` globs | Instructions per request | |
| Windsurf, Continue | always / glob / model-decided | System message | Legacy 6k/12k caps |
| anthropics/skills, wshobson/agents, github/awesome-copilot | Agent-decided skills, `applyTo` globs | Skill load | SKILL.md median 5.5–8.3 KB |
| obra/superpowers (317k★) | One SessionStart hook injects a 3.2 KB "how to use skills" body; everything else via the Skill tool | **No PreToolUse** | 15 skills |

PreToolUse body injection shows up only in niche tools, such as aiwg's `pretooluse-context`. An open Claude
Code request records its weakness: injected text "loses identity". The hooks that large collections ship do
governance (blocking or auditing), not delivery.

## 5. Why tj-agents moved to hook injection

| Date | Change | Stated reason |
| --- | --- | --- |
| 2026-09-24 | core #17 `86bf7f78`: tier gate, advisory SessionStart, `GIT_TIMEOUT = 10` | Say which stacks apply |
| 2026-10-23 | core #440 `f2440a66` "StackWriteGate": PreToolUse **blocks** writes until a stack standard is loaded | "8 of 10 main sessions with C# edits had loaded none before their first edit, and 8 subagents wrote 348 C# edits with none. Nothing enforced it." |
| 2026-10-27 | core #512 `b8e9a52d`, #520 `8dcbf9f8`: every PreToolUse hook removed; 10 KB SessionStart preload removed | The router rebuild "took 63 s against a 25 s deadline"; "Skills are selected from their descriptions, which is the Agent Skills design." |
| 2026-11-09 | core #585 `a24949ee`: **inject bodies** on PreToolUse, 40k bound | "in practice nothing loaded them. A whole day of Python … was written without Tommy's Python standards." "Not yet watched live." |
| 2026-11-09 | core #589 `3e201797`: 10k bound + deferral | 40.1 KB injection was saved to a file instead, seen live. Other stacks after the file's own: "by design in #585". |
| 2026-11-10 | agent #138 `84be488`: `tj prepare` renders the AGENTS.md "Repository standards" index (core profiles only) | "Repository-selected standards can remain undiscovered before code edits" |

The hook was meant to solve a real problem that still exists: agents left to judgement do not load
But the history has two clear lessons:

- **The gate (#440) was the right primitive.** It was removed for latency (the router rebuild), not because
  gating failed.
- **Injection (#585) swapped the gate for a channel that is capped and arrives after the write.** It was
  merged unwatched.

Index and hook also disagree: the agent index skips non-core profiles, and the hook injects them.

### We have been round this loop before

| Period | Mechanism | How it ended |
| --- | --- | --- |
| 2026-09-16 → 10-27 | `skill_router.py`: a path → skills route table, **blocking the write until the transcript proved the skills loaded** | Removed in #512. Rebuilding the project picture on every write took 63 s under `~/.claude` and seconds per edit elsewhere. Every skill on a route blocked: 7 for a plain C++ header. Codex hooks were disabled, and route tables were missing in nested worktrees (debt record 2026-10-09). |
| 2026-10-27 → 11-09 | Descriptions only plus an advisory SessionStart line (the superpowers argument) | Nothing loaded. A day of Python was written without the standards. |
| 2026-11-09 → now | PreToolUse body injection | Arrives after the write, capped at 10k, per-repo selection (this report) |

Unmerged leftovers:

- **core `Docs/ContinuationAndStandardsDebt`** (2 commits, 2026-10-09, never a PR). It records "Applicable
  domain standards are missed before implementation and review", reproduced on .NET DDD. Its acceptance
  test: "a trusted fresh-session probe must deny a relevant write without load proof and allow it after
  successful reads".
- **`core/.worktrees/Feature-StandardsSourceOwnership`** (16 uncommitted files, no PR).
- **`plans/conditional-skill-routes`** (2026-09-27, never started). It splits required from conditional
  routes, which fixes the 7-skills-per-header problem.
- **Open:** python #37 (run the Python checks after edits) and core #443 (codebase conventions win).

So the gate below is the September router again. It is still the right primitive. It failed for three
reasons, and each needs a fix this time:

| What failed | What it needs now |
| --- | --- |
| Cost | Read precomputed routes and run no scan |
| Over-requiring | Required core plus adopted profiles only |
| Codex inactive | Proven by a fresh-session probe on both hosts |

Existing items this touches: core #598 (reduce skill discovery metadata), docs #16 (scoped standards
composition), agent #117 (standards sweep), agent #91 (profile scope).

## Decisions (Tommy, 2026-11-13)

- **Approved:** implement the gate design through self-repair.
- **Merge policy:**
  - Configurable, with bot identity as the switch. Enabled means bot identity plus approval; otherwise
    merge on green.
  - Owner: the delivery-speed session (N3 in tj-agents/github), wired to the generic bot identity the
    "lane selection" session will resume.
- **Backlog:** close PRs that are stale and conflicting (keep their branches), land the live ones. The
  delivery-speed session runs its existing triage of 151 PRs.
- **No scheduled sweep.** The fix is a pipeline that lands work: merge on green, every PR backed by an item.
- **This session owns** every base-hook change (delivery-speed D1–D4, R1) together with the gate. Install
  scope is already handled by agent#180.

## Implementation as built (supersedes parts of §6)

The work is **one core PR** (`Fix/StandardsWriteGate`):

- **No routes file and no agent or template change.** The gate resolves the repository root on the
  filesystem and reads `.agents/plugins.json`. It then reads the selected payloads' tier path predicates
  and canonical standard paths, all without git.
- **"Loaded" means the canonical SKILL.md was read:**
  - Claude: a `Read` hook guarded by `if: Read(**/SKILL.md)`, so ordinary reads cost nothing.
  - Codex: a shell command that names the path.
- **Why reads, not Skill calls:** because the gate counts reads, the pointer-stub entries need no
  regeneration across the stack repos, and deleting placeholders is not required.
- **Placeholders are kept.** They are the empty contract slots that `rust:learning`'s procedure records into
  ("start empty and grow only from decisions made in his projects"). Each costs about 200 characters to read.
- PR: https://github.com/tj-agents/core/pull/610

## 6. Recommendation

Stop delivering bodies through hooks. Deliver standards the way every comparable system does: a short
routing statement that is always present, plus skills the agent loads whole. Keep one deterministic hook,
but make it a gate that runs before the write, not a document channel.

1. **Per-file routing, precomputed.** `tj prepare` resolves each stack's path predicates once into a small
   routes file: glob → that stack's required `core` standards plus the profiles the repo adopted, without
   `explanation`. This is data for the gate, not an instruction. AGENTS.md prose is advisory and
   nondeterministic, so it carries no part of the guarantee.
2. **A write gate instead of injection.** PreToolUse on the write tools (Claude `Edit|Write|MultiEdit|NotebookEdit`,
   Codex `apply_patch`):
   - It denies a governed write until this agent has loaded that file's required standards.
   - The deny reason names exactly the missing skills (under 500 chars, well within every cap).
   - A deny is the only PreToolUse output that takes effect *before* the write.
   - Loads are recorded from the host's own Skill/skill-read events into the existing per-agent ledger,
     and the ledger resets on compaction as today.
   - On Claude, the Skill tool call names the skill. On Codex, a load is a SKILL.md read, so detecting it is
     the design point to settle.
   - The gate guarantees the standard is *in context before the write*. It cannot guarantee the agent obeys
     it. Mechanical rules belong in checks after the edit (python #37), and the rest in review.
   - It runs no repository scan on Read/Glob/Grep, which removes the 8–13 s per-read latency.
3. **Self-contained skill entries.** The generator writes the canonical body into the discovery entry, so
   one Skill call delivers the standard. Today 110 of 119 entries are pointers.
4. **Clean cut:**
   - Delete `compose_injection`, the deferral note and the `HOOK_CONTEXT_CHARACTERS` budget.
   - Delete the "injected once per agent" header and standards on reads.
   - Delete the 10 placeholder standards. Recreate one when there is something to record.
5. **Install scope (coordinate):** install stack plugins per project from `.agents/plugins.json` instead of
   at user scope, so the listing shows the descriptions that matter. The "personal delivery speed" session
   owns plugin loading and `tj install`, so this item goes to that session, not to me.
6. **Separate defect:** the tier gate's workspace scan walks nested `.worktrees/` git roots and overruns
   its 10 s deadline. Core is "undetermined" on every start. File it separately through self-repair.

Considered and rejected:

- **Trimming.** It cannot make standards arrive before the edit, and ours are already below public norms.
- **Raising or splitting the bound.** Hosts cap each hook field, and the timing is still after the write.
- **Generated `.claude/rules/` per repo.** Native and well timed on Claude, but it is Claude-only, it copies
  bodies into each repository (drift), and Codex has no equivalent.
  it is the floor of this recommendation. The cli session is evidence that an agent with a clear "load before
  first edit" instruction still skips it, and the gate is the smallest mechanism that guarantees the standard
  is in context before the write.

This revives #440's gate without what killed it:

- **No router rebuild.** Routing is precomputed by `tj prepare`, and the gate reads one small file.
- **No work on reads.**

Owning repositories:

| Repository | Change |
| --- | --- |
| **core** (`base` hooks) | Gate replaces injection; scan fix |
| **agent** (`.agents/agent/runtime/standards.py`, `tj prepare`) | Per-glob routing block and a routing file the gate reads |
| **template** (generator) | Self-contained skill entries |
| **rust**, **react**, **azure**, **dotnet** | Delete placeholder standards |
| install scope | Through the delivery-speed session |
