# Code review — Docs/CrossPlatformConvention

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `07532d92b3fcf3888d79d0c91ce40974214287f9`  `(2026-10-09)`
**Judgment:** `changes-requested`

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
