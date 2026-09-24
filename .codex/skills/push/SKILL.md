---
name: push
description: Push one stable substantive candidate and prove the remote actually carries it — verify the remote-tracking ref and any open PR head both equal the exact pushed head. Covers publishing known non-merge-ready GitHub review heads without CI, diagnosing a rejected, unconfigured, unauthorised or hook-blocked push instead of retrying blindly, never force-pushing unasked, and never manufacturing a ledger-only transport tail. Use whenever the user wants to push commits, git push, push this branch, publish a diff for human review, or recover a failed push.

kind: operation
domain: process
model: gpt-5.5
---

# Pushing a verified head

Read and follow the [canonical shared definition](../../../.agents/engineering/operation/push/SKILL.md) in full.
This entry point supplies only Codex discovery metadata; the shared procedure is authored once under `.agents/`.
