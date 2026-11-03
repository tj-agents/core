---
name: catch-up
description: Reconcile what the current conversation left behind against live repository, pull request and issue state, and report each item as done, superseded or still open. Use when returning to an unfinished or unclosed conversation, or when asked whether it is all done, still relevant or what has changed since.

kind: utility
domain: process
---

# Catch up

Owns the relevance check for a conversation reopened after other work has moved on. It reports; it does
not resume, merge, rebase or close anything. Continuing a named goal afterwards is `workflow:resume`.

1. **Inventory this conversation's leftovers** from its transcript: pull requests, branches, worktrees,
   plan files, records, background tasks and every question or proposal still awaiting the user.
2. **Re-read each against live state** with the shipped script, one call for every item. It reads PR,
   issue and branch state in one GitHub query and searches Agent's session store for each branch:

   ```text
   python -B "<skill-directory>/scripts/catch_up.py" --pr https://github.com/tj-agents/core/pull/551 --branch tj-agents/template:Refactor/SubjectSkillLayout --issue https://github.com/tj-agents/personal/issues/49
   ```

   Use `python3` on Linux/macOS. Its JSON lists each item's `state` and every matching session; a
   `stalled` session is closed while its work item is active or its branch is unmerged, with its `reopen`
   action. Check local worktrees and plan files directly. The conversation's own account of an item is
   never evidence of its current state.
3. **Find what happened since on the same subjects.** Search newer commits, PRs and issues in every
   repository the conversation touched, by subject as well as by name. A later change may have merged,
   closed, reverted or replaced an item under a different title. Name what was searched.
   Add `--topic` to the script for a work item whose sessions do not share its branch name.
4. **Report one line per item, then stop**: done, superseded by a named change, still open with its next
   action and owner, or an obsolete question. Lead with whether the requested work is done. Acting on any
   item is a separate request.

```text
Reopened after four days: "all done?"
Self-repair move: done, template#60 and core#535 merged; installed template lists self-repair.
Approval-command rule: superseded by personal#58, whose gh wrapper prints the command.
Question "rebase personal#50?": obsolete, #50 closed by #58.
core#532: still open and unreviewed; probably obsolete after #58, the user's decision.
Stalled: template#56 and core#528 draft, owner codex:01a187bc closed since 10-30; reopen it to finish.
```
