# Unfinished delivery returned without continuation

Canonical record: `tj-agents/core#364`, recurrence comment `6365095127` and verified-cause comment `6365370676`.
Related records: `tj-agents/core#415` and `tj-agents/core#400`.
Native conversation: `codex:01a16053-d03d-7753-8ad9-3174781fba89`.

## Observed failure

At 12:05:55.505 UTC on 23 October 2026, the owner returned a final response with
authorized work unfinished, no necessary question, and no verified continuation.
PR355 remained open at `c6778af225a897afdeeac1d78062b8bcc3a15990`; its exact-head
CI39942526220 had passed. Review, merge and installed activation remained pending.
Tommy had to return to request the merge and call out the missing listener.

The immediate trigger was repeated automatic permission-review timeouts, including
read-only commands. The tool explicitly said the timeout did not establish that
the action was unsafe. The owner treated that temporary execution failure as the
end of task ownership instead of preserving a monitored continuation.

The native transcript
`rollout-2026-10-21T22-17-48-01a16053-d03d-7753-8ad9-3174781fba89.jsonl`
records the final response at line13620 and `task_complete` at line13623,
12:07:34.248 UTC. No Stop decision was observed in the filtered interval.

## Why Core did not prevent it

Commit `40cab46184b379c0588403b892bf564670f9a8bc`, 19 October 2026 at
20:13:59 UTC, deliberately removed `continuation_stop` and `workflow_route` from
both host manifests. Its message, "Remove procedural hooks and the pre-launch
standards refresh", describes them as procedural enforcement and notes eight
follow-up fixes to `continuation_stop`.

Published parent `23da17c6`, current main `4925ad43`, and candidate `c6778af2`
all have Engineering hooks containing only `PreToolUse` in
`.agents/plugins/manifests/codex/engineering-hooks.json`. The installed generated
manifest matches published main, normalized SHA256
`045b8557f6927ed36074d4cc1a1b5cc1bfe0dcc8053974b299f03c4e8d7254ed`.
Base supplies SessionStart context. Machine's Stop hook records session state;
it does not enforce continuation. Workflow's manifest also has no such hook.

The source gate and its tests still exist, but they are unwired. Their presence
does not establish live enforcement. This incident is not a regression introduced
by PR355, an isolated CI fixture leaking into the user profile, or evidence that
the scheduler itself failed. The owner failed to activate the supported
continuation required by the current prose contract; automatic Stop prevention
had intentionally been retired.

## Evidence limits and existing ownership

Before recovery changes, primary Core had no continuation owner, scheduler receipt
or delivery binding. Selection and Lifecycle also lacked owner/scheduler receipts
and retained older human-gate bindings. Standard route and Stop-marker receipts
for both raw and qualified native identities were absent after resumption. These
observations do not prove the exact filesystem state at the earlier Stop event.
The historical active Engineering hook digest is not retained in this transcript.

Current resumed process1964 started at12:33:44UTC using the native Codex executable
and the same conversation ID. Its identity is not the earlier process identity.

Dormant `once_per_stop` retry suppression, the weak `documented_blocker` check and
informal resume parsing are separate source concerns; none is established as this
incident's causal path. Do not restore the retired gate implicitly. Reconcile the
existing continuation repair owners recorded in#364 and the now-stale wired-hook
assumption in#400 before choosing an enforcement mechanism.

## Recovery and acceptance

Continue the same authorized goal and preserve the original checkout and native
conversation. Record this recurrence through Personal's existing-item operation.
Runtime owner `7eeb7b98f1145de79d2c8708` now binds PR355 at `d2c122f8` to verified native PID1964. Scheduler registration succeeded; an observed wake recorded `foreground-owned`, retained the live lease and launched no competing child. Foreground heartbeats and one exact-head CI listener remain active. This demonstrates recovery ownership, not unattended behavior after every failure mode. Yield the foreground lease explicitly before an unattended handoff; a stale lease on a live process does not authorize takeover.

The prevention acceptance scenario is an unfinished authorized goal encountering
temporary command or approval failures. On both supported hosts, verify continued
foreground ownership or a real registered wake through recovery, including
repeated final/Stop attempts. A final status paragraph, another prose instruction,
passing dormant unit tests or green source CI does not satisfy that condition.
This incident remains open until that behavioral acceptance is observed.

PR355 subsequently merged the reviewed polling-repair head `2952750d` at
`b1fa5c68a1c532cc2190832828dfdcdca82664e5`, 23 October 2026 at 13:59:24 UTC,
after exact-head CI39963544250 passed on Windows and Linux. The same registered
continuation remains active through causal publication39965800923. Delivery of
this PR does not close the separate continuation-prevention acceptance above.
