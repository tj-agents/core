# Stop the worktree placement gate blocking commands that create no worktree

Status: launched 2026-10-12 as a bounded side workstream from the Claude session that owns
`Fix/HeadlessContinuationTurnRelease` (PR229). This goal is independent of that one; do not adopt, edit or
close it.

Authorization: `engineering:session-guidance` standing standards-defect authority. It covers diagnosis,
implementation, testing, opening a PR and normal merge once Core gates pass. Installation in other scopes,
publication outside tj-agents/core and destructive actions remain gated. Routine design delegation is
false (`.agents/settings.json` has no `configuration.core.auto_approve`), so record design choices and
their rationale here.

Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-PlacementGateHeredocTokens
Branch: Fix/PlacementGateHeredocTokens
Base: origin/main 7ac3aee (verify the full SHA on pickup).
PR: not opened.
Lane: L4. The cause is reproduced below and the repair is a bounded, testable fix inside one hook.

## Claude handoff checkpoint

Transfer requested by the user on 2026-10-12. This is a handoff of this isolated side workstream only;
the originating `Fix/HeadlessContinuationTurnRelease` session remains outside this worktree and is not
adopted, edited, or closed here.

Checkout: `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-PlacementGateHeredocTokens`
Branch: `Fix/PlacementGateHeredocTokens`
Head: `7ac3aeeb630f232870f9d5ae17663ef2befb2518`
PR: not opened.
Design delegation: false; source: `configuration.core.auto_approve` default in `.agents/settings.json`.
Launch lane: L4, because the remaining work is a specified, testable implementation and regression fix in
one hook. No reproduction or implementation action has been run in this checkout before this handoff.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/hooks/worktree_placement_gate.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "PreToolUse Bash worktree-placement gate",
      "source": ".agents/hooks/worktree_placement_gate.py",
      "mapping": ".agents/plugins/manifests/claude/engineering-hooks.json",
      "verification": {
        "level": "planned",
        "result": "pending",
        "evidence": "Add and run the Claude Bash heredoc regression payload."
      }
    },
    {
      "host": "codex",
      "behavior": "Bash worktree-placement gate",
      "source": ".agents/hooks/worktree_placement_gate.py",
      "mapping": ".agents/plugins/manifests/codex/engineering-hooks.json",
      "verification": {
        "level": "planned",
        "result": "pending",
        "evidence": "Add and run the Codex Bash heredoc regression payload."
      }
    }
  ]
}
```

## Observed defect (reproduced)

On 2026-10-12, the Claude PreToolUse Bash hook `worktree_placement_gate.py` (installed engineering
c91b60c955ad) blocked a command that creates no worktree. It reported "worktree creation must not be
hidden in a compound shell command." The command was `cd <checkout> && python - <<'EOF' ... EOF`, a
Python heredoc that edits a Markdown file, followed by a `workflow_ops.py` call and a `grep`. It contained
no `git worktree add`.

Reproduction: load the installed hook and run `shell_segments(command, "bash")` and
`parse_creation(segment)` on that command. `shell_segments` returned 13 segments, because it splits the
quoted heredoc body into command segments. Two body lines that do not tokenize as shell, because of
unbalanced quotes such as `STOP1's`, made `parse_creation` return `("invalid", None)` at its
`tokens is None` check. That check comes before the parser looks for a `git worktree add`. In
`creation_segments`, any non-None classification counts as a creation, so `main()` blocked at
`len(creations) != 1`. A whole-command fallback regex already exists for unparseable commands
(`creation_segments`, `segments is None` branch: `\bgit(?:\.exe)?\b.*\bworktree\s+add\b`). The
per-segment path has no equivalent check.

Source owner: `.agents/hooks/worktree_placement_gate.py` and its tests under `.agents/hooks/tests/`.
Both host manifests wire it (`.agents/plugins/manifests/{claude,codex}/engineering-hooks.json`). B007 in
`BUGS.md` and PR220 introduced the gate; this is a new false positive, not a reopening of B007.

## Outcome and acceptance

A command with no `git worktree add` in any segment is never blocked, including one whose heredoc body or
quoted text fails shell tokenization. Every genuine creation case the gate already rejects still blocks:
sibling, nested, compound, substitution, ambiguous or unparseable `git worktree add`. Verified internal
creation still passes.

Choose the smallest repair, for example: classify a segment as `invalid` only when it actually mentions
`git ... worktree add`, and/or treat a quoted heredoc body as data. Do not disable the gate or weaken its
creation checks.

Add disposable regressions on both hosts' Bash payload shapes. Cover a heredoc body with unbalanced
quotes and no worktree add (allowed). Pair it with an unparseable segment that does contain
`git worktree add` (still blocked). Record the bug in root `BUGS.md` with the next free `B` id: check
remote branches, since `origin/Fix/HookDeliveryIdentity` uses B008–B010 and
`Fix/HeadlessContinuationTurnRelease` uses B011. Follow `AGENTS.md`, `CODE_CONVENTIONS.md`, zero code
comments, and generated-output discipline: never commit `plugins/*` or catalog digests. Record an
`agent-host-coverage` record per `base:plan-artifacts`.

## Next Steps

1. Acknowledge pickup here with the exact checkout, branch and head. Re-run the reproduction above against
   the source hook in this checkout, and record the result.
2. Implement the smallest fix with focused regressions under `engineering:bugfix`. Commit, run the
   canonical review, open the PR and merge it normally once required gates pass. Keep this goal current
   with delivery evidence, then finish only this side session.
