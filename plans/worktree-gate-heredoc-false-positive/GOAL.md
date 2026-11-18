# Worktree placement gate blocks Bash heredocs that create no worktree

## Authorization

Standing standards-defect authorization from `engineering:session-guidance` ("Maintain the right source owner"): diagnose, implement, test, open the PR and merge once this repository's gates pass. Installing into other scopes, publishing elsewhere and destructive operations stay gated. Launched as a bounded side workstream by Claude session `claude:c27c07bf-a274-466a-a10e-10ef96f36841` (work-item sessions goal, `Feature/WorkItemSessions`), which keeps its own goal and checkout. Do not touch that checkout or PR #209.

## Checkout

`C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-WorktreeGateHeredocFalsePositive`, branch `Fix/WorktreeGateHeredocFalsePositive`, from `origin/main` at `c91b60c955ad4a3f0f7a9383fc20f1c4a6b58510`.

## Defect (verified by replay against the installed engineering package `3b41211db4b6`)

`.agents/hooks/worktree_placement_gate.py` blocked two Claude Bash calls that contained no `git worktree add`, with "worktree creation must not be hidden in a compound shell command". Both were `python - <<'EOF' ... EOF` heredocs holding Python or Markdown.

Cause: `shell_segments` does not understand heredocs, so each body line becomes a segment. `parse_creation` (`worktree_placement_gate.py:304-307`) returns `("invalid", None)` whenever `tokens_of` (`shlex.split(..., posix=False)`) raises, before it checks that the segment is a git worktree-add at all. Lines with Python `'''` strings or Markdown backticks fail tokenization, so they count as "creations". `main` then reports the compound-command reason because more than one segment exists.

Replay evidence (exact blocked commands, outside the repository):

- `C:\Users\TOMMYS~1\AppData\Local\Temp\claude\C--Users-TommySeery-source-repos-tj-agents-core--worktrees-Feature-WorkItemSessions\c27c07bf-a274-466a-a10e-10ef96f36841\scratchpad\blocked\blocked_0.txt` — 27 segments, 3 "invalid" creations, each a `rep('''...` line with `tokens_of` → None.
- `...\scratchpad\blocked\blocked_1.txt` — 16 segments, 1 "invalid" creation, a Markdown line with backticks.
- Replay script: `...\scratchpad\replay_gate.py <hooks-dir> <transcript.jsonl> <out-dir>`.

Second observation, unconfirmed: a standalone Bash call `git -C "C:/Users/TommySeery/source/repos/tj-agents/core" worktree add -b "Fix/WorktreeGateHeredocFalsePositive" -- "C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-WorktreeGateHeredocFalsePositive" "origin/main"` was refused with "the checkout and destination could not be resolved safely". The identical PowerShell call with backslash paths succeeded. Determine whether forward-slash Windows paths from Git Bash are wrongly rejected; fix only if that is a real defect.

## Completion expectation

- An untokenizable segment counts as a creation only when its text could actually be a git worktree-add; heredoc or other non-git text is ignored. Real hidden or compound worktree creation must still be blocked. Do not weaken the gate's bypass protections; keep the existing tests green.
- Regression tests reproduce both replayed commands (or minimal equivalents) as allowed, plus a heredoc that contains a real `git worktree add` line staying blocked. Tests run on Windows and Linux.
- Update the canonical source only; never commit generated `plugins/*`. Run `pwsh .agents/sync-generated.ps1 -Check` after a throwaway regeneration and restore `plugins/`.
- Review, PR and merge through Core's normal gates (`engineering:review`, `engineering:open-pr`, `engineering:merge`).

## Next Steps

Lane: L4 — a specified fix inside a testable hook; the remaining judgement is the narrow non-git classification.

1. Read `AGENTS.md`, `CODE_CONVENTIONS.md` and `.agents/hooks/worktree_placement_gate.py` with its tests (`.agents/hooks/tests/test_worktree_placement_gate.py` or the nearest equivalent).
2. Write the failing regression tests, then fix `parse_creation`/`creation_segments`, and check the forward-slash path observation.
3. Commit, review, open the PR and merge; record the outcome here.

- Scope: whole plan through all remaining phases and terminal delivery.
- Current slice: the gate fix and its regression tests.
- Remaining scope: none beyond this fix.
- Done when: the fix is merged to `main` and this goal records the PR.
