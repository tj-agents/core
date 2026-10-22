# A finished CLI can always close itself after moving checkout

Authorized by Tommy on 2026-10-18 after `machine:close` refused to close session `2c4453fe`: "We need to fix it
so this thing never fucking happens again."

## Outcome

`machine:close` closes a completed session even after the host moved it into another checkout (worktree
attach or `/cd`), and removes its merged worktree when armed with `--remove-worktree`.

## Delivery

PR #296 (`Fix/CloseFollowsMovedSession`). Merge is authorized under the standing tj-agents auto-merge
instruction once exact-head CI is green and the canonical review is approved.

## Progress

- Cause confirmed: `cli-sessions/<id>.json` kept the SessionStart `cwd` while `sessions.db` moved it on every
  Stop; `session_close.awaiting_input_activity` requires them equal.
- 2b3b6acf: the Stop hook moves the registry `cwd` with the store's. 145 tests passed; both new tests fail
  without the fix.
- Full review at 2b3b6acf: changes-requested. F1 (handoff admission exact cwd match) fixed in 6e08a3e2;
  F2 (close ticket pinned cwd) fixed in acff78fe. 129 tests passed at acff78fe.
- Further review fixes: checkout-root recording (4d4e1b8a), launch_cwd lookup and failed-write consistency
  (0f9106ca, f94e9d4c). Final review approved at f94e9d4c.
- Done: PR #296 merged 2026-10-18 as `f977af1eac8db7faad5ea03db78ce1cfb6afe294`.
- Dependency: PR #294's merge Step 5 cleanup (remove `.worktrees/Fix-OpenCliAlwaysOpens`) needs this
  session's verified exit, which this defect blocks. This session's hooks run the installed plugin at
  `669d90ef`, so after #296 merges run the merged `session_store.follow_registered_cwd` for session
  `2c4453fe`, then `machine:close` with `--remove-worktree`.

```completion
{
  "outcome": "machine:close closes a completed session after the host moved it into another checkout.",
  "acceptance": [
    {
      "id": "moved-session-closes",
      "criterion": "After a Stop from a moved checkout, session_close accepts the session's refreshed registry attachment for both hosts.",
      "evidence": [
        {"source": "tests/test_finish.py::test_a_session_that_moved_checkout_still_matches_its_attachment_after_stop", "result": "passed at f94e9d4c (171 session/close/peer tests); PR #296 merged as f977af1e"}
      ],
      "owner": "Claude session 2c4453fe",
      "next_action": "None; delivered in PR #296."
    }
  ],
  "deliveries": [
    {"repository": "tj-agents/core", "pr": 296, "head": "f94e9d4cd66ec3d45d6919180a8f86af67d717d2"}
  ],
  "open_tasks": []
}
```
