# open-cli always reopens a closed session

Authorized by Tommy on 2026-10-18: "Fix it. You should always be able to open a fucking CLI."

## Outcome

`open-cli` reopens a closed Claude or Codex session. A stale launch receipt from an earlier reopen never
blocks it, and a session file that vanishes mid-scan never crashes the search.

## Delivery

PR #294 (`Fix/OpenCliAlwaysOpens`). Merge is authorized under the standing tj-agents auto-merge instruction
once exact-head CI is green and independent review is clean.

## Progress

- f5293ac8: receipts record the startup wrapper identity; `--confirm-closed` releases untracked receipts;
  search skips vanished files. Stuck session `01a1415f-…` reopened live with the fixed script.
- c5b1a787: review fixes. Receipts also track the native child (POSIX `start_new_session`); an unreadable
  start time is inconclusive.
- Incremental review of c5b1a787: both prior findings resolved, no defects; one coverage gap.
- 00827872: tests assert both Popen paths report the native child pid (mutation-checked).
- Canonical review of 00827872 (native layer): ambiguous receipts captured identity once; a later
  native child was untracked. 3b35b1d4 re-reads the kept status file.
- Further passes: F3 (pid reuse after status re-read) and F4 (double status read) fixed in 710e2b96;
  skill retry rule reconciled in 5fae6b7c. Final pass approved at 710e2b96.
- Done: PR #294 merged 2026-10-18 as `3b10da0f24a0cc55b325fdc510df7bbed2b76a96`. Follow-ups recorded as B015 and B016 in the primary
  checkout's `BUGS.md`.

```completion
{
  "outcome": "open-cli reopens a closed session even after an earlier verified reopen, and topic search survives vanished session files.",
  "acceptance": [
    {
      "id": "stale-receipt-released",
      "criterion": "A launch receipt releases once its launched processes are gone, and --confirm-closed releases an untracked one.",
      "evidence": [
        {"source": "tests/test_agent_recovery.py", "result": "tests/test_agent_recovery.py and tests/test_startup_binding.py: 62 passed at 710e2b96; PR #294 merged as 3b10da0f"},
        {"source": "live reopen of 01a1415f-6448-7123-8b17-c7fb67aee637", "result": "legacy receipt released with --confirm-closed; new receipt recorded wrapper pid 5172"}
      ],
      "owner": "Claude session on Fix/OpenCliAlwaysOpens",
      "next_action": "None; delivered in PR #294."
    },
    {
      "id": "search-survives-vanished-file",
      "criterion": "Topic search skips a session file removed during the scan.",
      "evidence": [
        {"source": "tests/test_agent_recovery.py::test_search_skips_a_session_file_removed_during_the_scan", "result": "passed"}
      ],
      "owner": "Claude session on Fix/OpenCliAlwaysOpens",
      "next_action": "None; delivered in PR #294."
    }
  ],
  "deliveries": [
    {"repository": "tj-agents/core", "pr": 294, "head": "710e2b96622256c7c181522b72537d82c3e5418a"}
  ],
  "open_tasks": []
}
```
