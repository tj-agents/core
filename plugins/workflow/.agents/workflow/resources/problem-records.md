# Work and problem records

Owns which tracker a repository uses and what happens to a problem noticed during other work. The selected
profile owns item content, native types, tracker operations, retention and when recording is permitted.
Core never selects a profile for a repository. Agent Store links working sessions to the profile's verified
item references; session ownership stays there and backlog content stays in the profile's tracker.

## Repository selection

Identify the affected system and the source repository that owns its cause; the checkout where it was
observed is only evidence. If ownership is unclear, ask which system and outcome the user means, keep the
facts and continue independent work.

The source repository's primary checkout, the first non-bare entry of `git worktree list --porcelain`,
declares its provider: a committed `.problem-records.json` naming the provider's qualified read operation,
such as `{"schema_version":1,"provider":"<profile>:work-item"}`, or a selected profile in
`.agents/plugins.json` that declares a default provider. A feature worktree's copy never overrides it.
Resolve the selection before any tracker operation:

```text
python -B <hooks>/problem_records.py --root <repository> --operation create|read|address --harness claude|codex
```

Use `python3` on Linux/macOS. `<hooks>` is the installed Engineering plugin's `hooks` directory, or
`.agents/hooks` in a Core checkout. Follow the printed `skill`. A failure, including a directory outside
any repository, blocks the tracker operation.

## Incidental problems

When a bug, mistake or deliberate debt is noticed or reported during goal A:

1. Keep A's goal and next action.
2. Tell the user what was found.
3. Record it only through the selected profile's create operation, when that profile's policy and the
   user's authority permit. A local Markdown note is not a record.

A question, frustration or callout alone leaves A active. Recording a problem does not prioritize,
implement or hand it off; honour an explicit request to do so while keeping A's remaining work. Fix a
defect inside A only when evidence shows A's own acceptance depends on it.

While recording is blocked, pending or declined, keep the facts in A with the resolver and resume
condition. Never create a substitute item, switch provider or install another profile.

```text
A: add report export. B: an unrelated terminal-close bug is reported.
Tell the user about B; record it through the selected profile's create operation; continue report export.
The export's own acceptance check fails because its CSV writer corrupts quoted fields: fix that within A.
"Fix the terminal bug first": keep A's next action, then reconcile B's owner and enter its repair.
```
