# Code review — Docs/CrossPlatformConvention

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `bf4f3d239f6f6919d931d4a2676559869a6bdbad`  `(2026-10-09)`
**Judgment:** `approved`

## Review pass — 2026-10-09 — docs

**Candidate base:** `21b482cb43b7e210ba211f262cccd7902715335c`
**Candidate head:** `07532d92b3fcf3888d79d0c91ce40974214287f9`
**Candidate branch:** `Docs/CrossPlatformConvention`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:f43271685f508678aa1eb999f2af28a8940f21937d47ffb03615f1690f48190f` `(3 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/OSAPltYvPDjVIAPcHAYhfw/RBKE8ZeA1D6KfEYnUpYvhH`
**Candidate bundle identity:** `sha256:bdff017d0e58daed5badd31cc54db09e303185f0c61b5bb227dc92cf9a73fd6b`
**Work-order path:** `reviews/Docs-CrossPlatformConvention.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

### Findings

- [x] **INST1 — MEDIUM — followability** — `CODE_CONVENTIONS.md:35`
  The new Supported platforms rules are already contradicted by shipped text this change leaves alone, and
  nothing owns the remediation: `peer-cli`'s SKILL.md never says it is Windows-only, `peer-cli` (line 70),
  `merge` Step 5 and `merge-docs` tell the agent to run `powershell.exe` with no platform, thirteen SKILL.md
  files say bare `python`, and the Windows-only PowerShell test suites have no Linux counterpart. State
  `peer-cli`'s Windows-only status in its SKILL.md now, and add a plan step that owns bringing the rest of
  the shipped instructions into line, with a checkable pass condition.

  Resolved: `peer-cli`'s SKILL.md now opens with its Windows-only status, and plan step 10 owns the rest
  (bare `python`, unlabelled `powershell.exe`/`pwsh`/`wt.exe`, Windows-only skills and test suites).

- [x] **HOME1 — MEDIUM — one-rule-one-home** — `AGENTS.md:5`
  AGENTS.md restates the rule as a present fact ("Everything this repository ships runs on Windows and
  Linux") and drops its Windows-only exception, so the copy already disagrees with its owner. Make the line
  a pointer that states the requirement and links Supported platforms.

  Resolved: the AGENTS.md line now states the requirement and points at Supported platforms.

- [x] **CON1 — LOW — contradiction** — `CODE_CONVENTIONS.md:5`
  The unchanged opening "Use the language and runtime appropriate to the repository and host" now competes
  with the Python mandate. Point it at Supported platforms for this repository's shipped code.

  Resolved: the opening line defers to Supported platforms for this repository's shipped code.

- [x] **ACC1 — LOW — accuracy** — `CODE_CONVENTIONS.md:48`
  `sync-generated.ps1` is named without its path; the script is `.agents/sync-generated.ps1`, as AGENTS.md
  writes it. Use the full path.

  Resolved: the tooling list names `.agents/sync-generated.ps1`.

- [x] **INST2 — LOW — followability** — `plans/linux-port/LINUX_PORT_PLAN.md:74`
  Step 9 is ticked while the required-check decision has no Next Steps entry, and "merge Step 5's session
  exit" can be read as the plan's own step 5. Add the pending ruleset question to Next Steps and name the
  `merge` skill's Step 5 explicitly.

  Resolved: Next Steps names the `merge` skill's Step 5 and asks the ruleset question after a few green
  `verify-linux` runs.

Native layer: Claude Code's built-in `code-review` (medium) over the frozen range. Documentation lenses
(accuracy, contradiction, one-rule-one-home, concision, dangling references, followability) ran in the parent
over the immutable bundle; `docs_reachability.py --root <bundle>/tree` reported 0 errors. Dropped: Linux CI
coverage for `.codex/install-workflow-agents.ps1` (pre-existing CI scope, below the bar for this docs pass).
No changed path matched the merge gate's security inventory, so no security marker is required.

## Review pass — 2026-10-09 — incremental

**Candidate base:** `07532d92b3fcf3888d79d0c91ce40974214287f9`
**Candidate head:** `03af0efce86ca9a18185621959e83a02000016f8`
**Candidate branch:** `Docs/CrossPlatformConvention`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:d2e3bed390dff6db348dfdece9810e5cfdc5ec06a8abf56039b5b06156deb732` `(5 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/qJctf4SOy93W8hHVTgl_eC/BA84EU0FQPg_PRmpw3ZPf9`
**Candidate bundle identity:** `sha256:9490debe5995772ef8f31251bf7f8c56025da149f07fb811e083dee8f0c70316`
**Work-order path:** `reviews/Docs-CrossPlatformConvention.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

- [x] **INST3 — LOW — followability** — `.agents/machine/utility/peer-cli/SKILL.md:72`
  The `powershell.exe ... close.ps1` instruction still names no platform at the point of use. Say "on
  Windows" there.

  Resolved: the instruction now reads "on Windows run exactly".

- [x] **INST4 — LOW — followability** — `.agents/machine/utility/peer-cli/SKILL.md:3`
  The Windows-only status is invisible in the `description` that hosts route on. Add it to the description
  in the shared definition and both host entry points.

  Resolved: all three descriptions end with "Windows only until its Python port lands."

- [x] **INST5 — LOW — followability** — `plans/linux-port/LINUX_PORT_PLAN.md:64`
  Step 10's pass condition checks only SKILL.md files under `.agents/`, names a `merge-docs` "Step 5" that
  does not exist, and its test-suite clause reads as conflicting with the plan's out-of-scope repository
  test tooling. Widen it to shipped Markdown under `.agents/`, `.claude/` and `.codex/`, name `merge-docs`'
  Report, and scope the test clause to suites of shipped scripts.

  Resolved as described.

- [x] **INST6 — LOW — followability** — `plans/linux-port/LINUX_PORT_PLAN.md:74`
  Current progress does not mention step 10 or the `peer-cli` label. Record both.

  Resolved: Current progress records them.

Dropped: `merge` Step 5 lacking a Linux path (pre-existing; plan step 5 is next and ports `close`/`finish`
first); `persistent-workflow` (its SKILL.md already names its adapter as the Windows adapter beside a
Python runtime); restoring the Python mandate to AGENTS.md (the line above already requires reading
`CODE_CONVENTIONS.md` before runtime changes, and HOME1 removed that copy deliberately); the local bundle
path (the work-order contract records it). Native layer: built-in `code-review` (medium); documentation
lenses in the parent; `docs_reachability.py` 0 errors. No security-sensitive path.

## Review pass — 2026-10-09 — incremental

**Candidate base:** `03af0efce86ca9a18185621959e83a02000016f8`
**Candidate head:** `fb65ab8881ec9908b0874d4d2db31ee4c37d60b3`
**Candidate branch:** `Docs/CrossPlatformConvention`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:24330ff8c7dc18bd21c09546a598559a429ca0798cb781abdb87859f106abade` `(5 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/xQ-D9YvpPpJccvLNw_XaDc/sR44spyCSQP191gd_q-WJR`
**Candidate bundle identity:** `sha256:9e4b0868e72c06465041514d32263ee0f36c5afae68520e1c71a2033cf94b060`
**Work-order path:** `reviews/Docs-CrossPlatformConvention.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

- [x] **REV1 — LOW — workflow** — `reviews/Docs-CrossPlatformConvention.md:7`
  The previous pass was committed with its judgment set but the top-level status still `in-progress` and the
  watermark at `07532d9`. Finalize each pass's header in the same commit as its findings.

  Resolved: the committed watermark moved from `07532d9` directly to this pass's head `fb65ab8`, covering
  the previous pass's `03af0ef` as well; this pass's remediation went to the next incremental pass.

- [x] **INST7 — LOW — accuracy** — `plans/linux-port/LINUX_PORT_PLAN.md:75`
  Current progress attributes the `peer-cli` label and step 10 to `CODE_CONVENTIONS.md`; the PR made them.
  Attribute them to #166.

  Resolved.

- [x] **INST8 — LOW — consistency** — `.agents/machine/utility/peer-cli/SKILL.md:3`
  The description spells "Windows only" while the body and the convention spell "Windows-only". Use
  "Windows-only" in all three descriptions.

  Resolved.

Dropped: a post-port concern that `close-tab.ps1` stays Windows-only (step 5 rewrites the description when
it ports the skill); step 10's "including" examples (the general clause already covers every bare `python`).
Native layer: built-in `code-review` (medium); documentation lenses in the parent. No security-sensitive path.

## Review pass — 2026-10-09 — incremental

**Candidate base:** `fb65ab8881ec9908b0874d4d2db31ee4c37d60b3`
**Candidate head:** `bf4f3d239f6f6919d931d4a2676559869a6bdbad`
**Candidate branch:** `Docs/CrossPlatformConvention`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:24330ff8c7dc18bd21c09546a598559a429ca0798cb781abdb87859f106abade` `(5 paths)`
**Candidate bundle:** `/tmp/review/VStsc1BqWYIHGazuKQv89R/rVc76uykpvE-rMFBdoYhtf/eNiTz8dJHxfbvVgrSeWm0J`
**Candidate bundle identity:** `sha256:8073d92624407fff9970428ab19d02a0c2deef90f2a1cff457862a608182696b`
**Work-order path:** `reviews/Docs-CrossPlatformConvention.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

### Findings

No new findings. The `peer-cli` descriptions agree across the shared definition and both host entry points,
and the plan attributes the label and step 10 to #166. REV1's resolution was corrected while finalizing this
pass: the committed watermark never sat at `03af0ef`. Dropped: marking #166 "in review" in the plan (the
statement is true once this PR merges with it), the superseded spelling quoted in INST4's frozen resolution,
and line width (no rule sets one). Native layer: built-in `code-review` (medium); documentation lenses in the
parent. No security-sensitive path.
