# Code review — Fix/FlaggedStandardsDefectHandoff

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `901e3b9155f59d6efdb5ad097c09039f4c3fdf26`  `(2026-10-04)`
**Judgment:** `changes-requested`

## Review pass — 2026-10-04 — full

**Candidate base:** `0c658509e77a7639aad4eb2ad7b9b7310264396c`
**Candidate head:** `901e3b9155f59d6efdb5ad097c09039f4c3fdf26`
**Candidate branch:** `Fix/FlaggedStandardsDefectHandoff`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:080288ab75e22389f1e7ef151cdbda1dfb0fe85723b630b3f5586aadf92d97f4` `(3 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\review-flagged-standards-defect-handoff\review\4058eef49ea7be2de97229570088b4f8b4befe0aab2472fd0666d0875af13de0`
**Candidate bundle identity:** `sha256:f9e4b879eeab395f40041bf4cda137aa2dabd04008d98de329abb26871a1ed72`
**Work-order path:** `reviews/Fix-FlaggedStandardsDefectHandoff.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Native layer: Claude Code built-in `code-review` skill (high) over the frozen range. Lenses dispatched
(helper-selected): api-contract, workflow. Security layer not required (`first_path` and
`trunk_first_path` both null). Routed skills: none returned by review-prepare.

Dropped at synthesis: "failed to prevent a mistake" is too broad (native) — intentional, Tommy's explicit
requirement that any standards-caused mistake hands off so it never recurs; adopt the
`repository-harness.json` overlay instead of a hand-written settings file (native) — the overlay is read
only beside a `capabilities.lock.json`, no repository in the org has adopted one, and adopting one would
also pin core's plugin selection and marketplace revision in project settings, a separate adoption
decision; the file owns only `permissions.allow`, the key `repo_config.py` would own, so a later adoption
moves these entries into the overlay; the self-check reloads standards at every commit / conflicts with the
stage-pointer rule (native, workflow) — the pre-commit check is the stage that enters those standards, and
Tommy explicitly asked for active self-checking; add an "inseparable from the current task" carve-out
(workflow) — the defect lives in the standards repository, never a step of the consuming task, and an
inline-fix carve-out would reopen the deferral loophole this change closes; `python3` spelling of
`check_generated_paths.py` (api-contract) — CI's ubuntu-only guard spelling, agents on this repository's
Windows hosts run `python`.

### Findings

- [x] **F1 — HIGH — native** — `.claude/settings.json:17`
  `git commit *`, `git push *` and `gh pr merge *` (and PowerShell twins) auto-approve `git push --force`,
  remote branch deletion, `gh pr merge --admin` and `git commit --no-verify`, ungating what session-guidance
  says stays gated. None of them was among the classifier-blocked calls. Fix: remove the git and gh
  delivery rules; delivery stays on the normal permission flow and the merge gates.
- [x] **F2 — MEDIUM — native** — `.claude/settings.json:4`
  `Edit(/**)` from the main checkout covers every other session's `.worktrees/**` checkout and the
  generated `plugins/**` tree. Fix: allow only the authored roots (`.agents`, `.claude/skills`, `.codex`,
  `.github`, `cli-session-recovery`, `docs`, `plans`, `reviews`, `scripts`, `shell`, `tests`, root `*.md`,
  `install.ps1`).
- [x] **F3 — MEDIUM — native** — `.agents/engineering/contract/session-guidance/SKILL.md:59`
  "Unless the current goal owns it" is undefined; a consuming session can claim its goal owns the defect
  because it is fixing the resulting mistake locally, repeating the B2B failure. Fix: "… is the exception
  unless the current goal is repairing that package".
- [x] **F4 — LOW — native, workflow** — `.agents/engineering/contract/session-guidance/SKILL.md:65`
  "announcing a later or separate fix instead is a violation" can read as covering an honestly reported
  launcher failure, which `engineering:handoff` prescribes. Fix: "instead of launching".
- [x] **F5 — LOW — native** — `.agents/hooks/tests/test_process_standards.py:103`
  Only the reconcile sentence is pinned; the same-turn handoff, the violation clause and the
  caused-or-failed-to-prevent scope have no regression assertion. Fix: pin them.
- [x] **F6 — LOW — native, api-contract** — `.claude/settings.json:9`
  Test-script and unittest rules are asymmetric between Bash and PowerShell, use a mid-path glob that can
  match `..` traversal, let `unittest *` discover anywhere, and miss the prescribed
  `./cli-session-recovery/tests/cli-session-vault.tests.ps1` and `powershell.exe … -File
  tests/codex-terminal-profile.tests.ps1` steps. Fix: enumerate the CI-prescribed scripts and discover
  roots exactly, identically for both tools.
- [x] **F7 — LOW — native** — `.agents/engineering/contract/session-guidance/SKILL.md:62`
  "whether the user or a self-check finds it" restates what "a mistake" already covers in an always-loaded
  file. Fix: remove the clause.

### Disposition — 2026-10-04

All seven fixed in one remediation commit. F1: git and gh delivery rules removed. F2: `Edit` limited to
the authored roots, excluding `.worktrees/**`, generated `plugins/**`, `CAPABILITIES.md`,
`.claude-plugin/**` and `.claude/settings.json`. F3/F4/F7: session-guidance reworded. F5: new
`test_a_standards_defect_hands_off_in_the_same_turn` pins the four behavior phrases. F6: the CI-prescribed
scripts and discover roots enumerated exactly and identically for Bash and PowerShell. Validation:
`test_process_standards.py` (20), `tests/test_source_layout.py` (17), `tests/test_engineering_hooks.py`
(7) OK; `sync-generated.ps1 -Check` and `sync_harness_manifests.py --check` green after local
regeneration (output left uncommitted). An incremental pass over the fixing commit follows.
