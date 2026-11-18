# Stop the placement gate blocking untokenizable commands that create no worktree
Status: launched as a bounded side workstream on 2026-10-12 from core `Fix/ContinuationProbeGate`.
## Outcome
`.agents/hooks/worktree_placement_gate.py` no longer blocks a shell command that does not invoke `git worktree add` merely because one of its segments cannot be tokenized.
## Authorization
Standing standards-defect authority from `engineering:session-guidance`: diagnose, implement, focused tests, record the bug, review, one final required CI, open the PR and merge under core policy. No installed-profile, cache, hook-disabling or global configuration changes.
## Ownership
Worktree: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-WorktreeGateTokenizeFailure
Branch: Fix/WorktreeGateTokenizeFailure
Base: c91b60c955ad4a3f0f7a9383fc20f1c4a6b58510 (origin/main)
This successor owns only this workstream. The originating session keeps `Fix/ContinuationProbeGate` and its continuation-runtime goal; do not touch that branch, its files or its BUGS.md entries B008/B009 (take the next free number after reconciling main and open PRs).
## Evidence
A PowerShell tool call `git commit -q -F - @'<multi-line message mentioning "the recorded worktree">'@; git log --oneline -1` was rejected with "worktree creation must not be hidden in a compound shell command." Reproduced at c91b60c: `shell_segments` yields two segments; `tokens_of` (`shlex.split(..., posix=False)`) raises on the here-string segment, so `parse_creation` returns `("invalid", None)` regardless of whether the segment invokes `git worktree add`; the command reaches classification at all because it mentions "worktree". The same command with "worktree" replaced by "checkout" passes. `creation_segments` already guards its own unparseable fallback with `\bgit(?:\.exe)?\b.*\bworktree\s+add\b`; `parse_creation` has no equivalent guard. Fail-closed behavior for a genuinely unparseable `git ... worktree add` segment must be preserved.
## Launch blocker (2026-10-12)
The predecessor's first launch attempt was interrupted by the 21:27 PC crash; no Codex session ever referenced this checkout. The relaunch of `machine:handoff-codex`'s documented command (`launch_codex.py ... --lane L4 --bypass-hook-trust`) was denied by Claude's auto-mode classifier ("Safety Bypass Flag"). Related defect: `.agents/plugins/harness/machine.json` declares no `permissions`, although `machine:handoff-codex` and `machine:handoff-claude` tell agents to run their launchers, contrary to `.agents/plugins/harness/AGENTS.md` ("Never rely on a classifier retry"). Whether to declare a launcher allow rule that includes `--bypass-hook-trust` is a security decision reserved for Tommy.
Blocked: launching this successor. Blocked by: Tommy. Unblock action: approve or declare the launcher permission, or launch this goal manually. Resume when: a session acknowledges pickup below.
## Lane
L4: specified repair with code-level judgement and focused tests.
## Acceptance
An untokenizable segment that contains no `git … worktree add` is not treated as a creation, in both PowerShell and Bash classification; an untokenizable segment that does still fails closed; existing placement-gate tests pass; both-host coverage is recorded; review, final required CI, merge and causal generated output are observed.
## Next Steps
Acknowledge pickup here. Read core AGENTS.md, CODE_CONVENTIONS.md and the bugfix workflow. Add a failing regression in the placement-gate tests reproducing the here-string false positive, repair `parse_creation`, record the bug in BUGS.md, then review, run final required CI once, open the PR and merge. Report the result in this goal.
