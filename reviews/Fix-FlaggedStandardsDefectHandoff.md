# Code review — Fix/FlaggedStandardsDefectHandoff

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `07333b763732c6034903ab9128b2831137a3902d`  `(2026-10-04)`
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

## Review pass — 2026-10-04 — incremental

**Candidate base:** `901e3b9155f59d6efdb5ad097c09039f4c3fdf26`
**Candidate head:** `07333b763732c6034903ab9128b2831137a3902d`
**Candidate branch:** `Fix/FlaggedStandardsDefectHandoff`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:eff2fecac7deaf671f469c27812a3d5908bcc656948ac236797076ed185fbf02` `(4 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\review-flagged-standards-defect-handoff-inc1\review\7942624e899b062fb19baedb610bc54f06a6b95c572e74f60bbc91db5e2d3bf5`
**Candidate bundle identity:** `sha256:280bec391e2eb558a395d6a109759a4bebcd14a1547a7b1e1559d8e8e1bd8708`
**Work-order path:** `reviews/Fix-FlaggedStandardsDefectHandoff.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

Native layer: Claude Code built-in `code-review` skill (high) over the delta. Lenses: api-contract,
workflow. Security layer not required (`first_path` and `trunk_first_path` both null).

Dropped at synthesis: the reconcile sentence's debt-entry outcome could absorb a standards defect (native)
— the exception sentence directly above already removes standards defects from the debt path, and
restating it in the reconcile list adds words to an always-loaded file; `unittest discover -s tests *`
admits a second `-s` (native) — the allowed `Edit(/tests/**)` already lets an agent write and run any test
code, so discover arguments add no capability the list does not grant deliberately; the bare
`sync_harness_manifests.py` and bare `discover` rules (api-contract) — harmless natural spellings (the
script never writes), kept as headroom.

### Findings (incremental)

- [x] **F8 — MEDIUM — native, workflow** — `.agents/engineering/contract/session-guidance/SKILL.md:59`
  "unless the current goal is repairing that package" names only the package although the subject covers
  its source repository, and a consuming session could claim it repairs the package by patching a local
  copy. Fix: "unless the current goal already works in that repository" — an objective test a
  consuming-side patch cannot meet.
- [x] **F9 — MEDIUM — native** — `.claude/settings.json:1`
  Removing every delivery rule (F1) leaves the standing-authorized commit, push, PR and merge steps
  prompting in core, the stall Tommy asked to end. Fix: allow `git add/commit/push` and the `gh pr`/`gh
  run` steps, with deny rules for force pushes, refspec forces, remote deletion, `--mirror`,
  `--no-verify` and `gh pr merge --admin`.
- [x] **F10 — LOW — native, api-contract** — `.claude/settings.json:4`
  `Edit(/.agents/**)` still covers the generated `.agents/plugins/marketplace.json`, contradicting the F2
  disposition. Fix: deny `Edit(/.agents/plugins/marketplace.json)`.
- [x] **F11 — LOW — native** — `.claude/settings.json:47`
  The enumeration dropped `./tests/install.tests.ps1`. Fix: add it.
- [x] **F12 — LOW — native** — `.claude/settings.json:33`
  `.agents/workflows/workflow_ops.py`, which `engineering:plan-execution` prescribes, lost its rule. Fix:
  allow `python .agents/workflows/workflow_ops.py *` and the `-B` spelling.
- [x] **F13 — LOW — native** — `.claude/settings.json:26`
  `Bash(./<script>.ps1)` entries can never run (Git Bash cannot execute a PowerShell script directly).
  Fix: keep only `Bash(pwsh ./…)` forms; PowerShell keeps both.
- [x] **F14 — LOW — native** — `.claude/settings.json:1`
  The hand-kept list will drift from the commands CI prescribes. Fix: a test asserting every command the
  `verify` job runs matches a `PowerShell(...)` allow rule.
- [x] **F15 — LOW — native** — `.agents/hooks/tests/test_process_standards.py:110`
  The handoff test does not pin the rule's subject. Fix: pin "A defect in a consumed standards package or
  its source repository is the exception" with the new carve-out.

### Disposition — 2026-10-04 (incremental)

All eight fixed in one remediation commit. F8: carve-out is now "unless the current goal already works in
that repository". F9: delivery allows restored with deny rules for force, refspec force, `--delete`/`-d`,
`--mirror`, `--no-verify` and `gh pr merge --admin` on both shells. F10: `Edit` denied on
`.agents/plugins/marketplace.json`. F11–F13: `install.tests.ps1` and `workflow_ops.py` added, direct
`.ps1` Bash entries dropped. F14: `tests/test_repository_permissions.py` asserts every `verify`-job command
(16 parsed) matches a PowerShell allow rule, the destructive forms are denied on both shells, and no
generated root is editable. F15: the subject and carve-out are pinned. Validation:
`test_repository_permissions.py` (3), `test_process_standards.py` (20), `test_source_layout.py` (17) OK;
`sync-generated.ps1 -Check` and `sync_harness_manifests.py --check` green after local regeneration
(output left uncommitted). A final incremental pass over the fixing commit follows.
