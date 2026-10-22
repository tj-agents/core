# Handoff alternatives

Assessment date: 2026-10-12. Authorized scope: compare core with public alternatives, recommend a reuse
decision, and implement the separately requested shared existing-solution convention. This assessment
does not authorize replacing the handoff runtime, installing another tool, or modifying host profiles.

## Recommendation

Keep core's handoff boundary and repair it from concrete failing cases. Reference the external recovery
patterns below; selectively reuse an implementation after a reproduction shows that it fixes the required
behavior. A whole-project fork or replacement is not justified by the inspected evidence. The reported
intermittent failures need exact examples before choosing the first runtime repair.

The useful external ideas are durable identity before submission, explicit uncertainty after a possible
send, reconciliation against the exact recipient, recoverable claims, and bounded delivery observation.
Core already implements several of these in its critical-transfer helper. The visible gaps concern
integration between helpers and actual host acceptance.

## Required behavior

- Start one fresh Codex or Claude session in the exact checkout with its selected task and configuration.
- Carry the canonical goal, authorization, remaining work, and first executable action.
- Distinguish launch submission, recipient acceptance, first progress, and task completion.
- Preserve one writer and reconcile an ambiguous launch before attempting another.
- Recover from a parent interruption without losing the goal or duplicating the recipient.
- Preserve the native interactive CLI and support Windows and Linux.
- Close the predecessor and retire a checkout through verified identity and cleanup gates.

The last requirement is a separate cleanup boundary. Message delivery does not establish that a process
exited or a worktree was removed.

## Inspected snapshots

| Project | Commit | License | Relevant scope |
| --- | --- | --- | --- |
| OpenMOSS/claude-codex-handoff | `baab7913a38bbf114c41c23e6e6bf748b2bf165b` | MIT | Messages between recurring Claude/Codex sessions |
| adelost/agentmux | `5b15d9271700b52c56a604995ef3f4fa52f208cd` | MIT | Durable delivery to addressed coding-agent sessions |
| klittle32/handoff-skill | `57089b6e1ce61498ec70852e46d41b2f8f12fa00` | MIT | Manual context transfer into a fresh session |

These are inspected revisions. No external tool was installed into a host profile and no authenticated
external CLI was launched. Licensing evidence is each revision's LICENSE file; copying substantial
material requires retaining its notice.

## OpenMOSS

The project coordinates already-running agents through append-only streams and per-session cursors.
The protocol specifies claim acquisition, renewal, expired-claim quarantine, replay checks and cursor
advancement after side effects. Those receive-side operations are instructions to agents in the polling
prompts, not guarantees enforced by a shipped receiver helper.

The Python standard-library tools implement outbound send locking and persistence, unread-message wake
classification, read-only diagnostics and archiving. The doctor checks claim/cursor state without repairing
it. No tracked test suite was found. Setup covers PowerShell and Bash; the described orchestration uses
Claude polling and Codex App heartbeat. It does not establish a fresh native CLI takeover, predecessor
process closure, or checkout cleanup. Reset removes collaboration runtime history; it is unsuitable as
generic recovery for an ambiguous core transfer.

References at the inspected revision:

- [PROTOCOL.md](https://github.com/OpenMOSS/claude-codex-handoff/blob/baab7913a38bbf114c41c23e6e6bf748b2bf165b/PROTOCOL.md): cursor/replay rules, expired claims, shutdown and reset.
- [codex-heartbeat-prompt.md](https://github.com/OpenMOSS/claude-codex-handoff/blob/baab7913a38bbf114c41c23e6e6bf748b2bf165b/prompts/codex-heartbeat-prompt.md): agent-followed receive loop.
- [tools/send.py](https://github.com/OpenMOSS/claude-codex-handoff/blob/baab7913a38bbf114c41c23e6e6bf748b2bf165b/tools/send.py): outbound lock and durable writing.
- [tools/doctor.py](https://github.com/OpenMOSS/claude-codex-handoff/blob/baab7913a38bbf114c41c23e6e6bf748b2bf165b/tools/doctor.py): read-only claim/cursor checks.
- [README.md](https://github.com/OpenMOSS/claude-codex-handoff/blob/baab7913a38bbf114c41c23e6e6bf748b2bf165b/README.md): prerequisites and session setup.

Decision: reference its replay and claim-recovery design. A fork introduces another collaboration model
without supplying core's terminal launch and cleanup requirements. No copied code is selected yet.

## Agentmux

The delivery spool assigns stable identities before transport. Its queue uses atomic creation and
replacement, idempotency keys and per-session write leases. A submission fence records uncertainty
before sending Enter. Submitted work is preserved for receipt reconciliation; unverified delivery and
proven cancellation are distinct outcomes. Blocked pre-submit handoffs return to their original sender.

These are useful implemented runtime patterns. Their code depends on other agentmux modules, session
addressing, queue state and transport integration. Documented prerequisites are Node 20+, tmux 3.2+,
and Linux, macOS or WSL. The broader project includes a native runtime and Discord integration; its
documented platform boundary does not establish native Windows Terminal parity with core.

References at the inspected revision:

- [delivery-fence.mjs](https://github.com/adelost/agentmux/blob/5b15d9271700b52c56a604995ef3f4fa52f208cd/core/delivery-fence.mjs): persist uncertainty before sending Enter.
- [delivery-queue.mjs](https://github.com/adelost/agentmux/blob/5b15d9271700b52c56a604995ef3f4fa52f208cd/core/delivery-queue.mjs): durable identity, idempotency and session leases.
- [delivery-queue-policy.mjs](https://github.com/adelost/agentmux/blob/5b15d9271700b52c56a604995ef3f4fa52f208cd/core/delivery-queue-policy.mjs): bounded retries and explicit terminal outcomes.
- [delivery-handoff.mjs](https://github.com/adelost/agentmux/blob/5b15d9271700b52c56a604995ef3f4fa52f208cd/core/delivery-handoff.mjs): notify the recorded sender of a blocked handoff.
- [README.md](https://github.com/adelost/agentmux/blob/5b15d9271700b52c56a604995ef3f4fa52f208cd/README.md): prerequisites and delivery contract.

Decision: reference the failure states and recovery evidence. Copying the whole queue carries a large
integration surface into a Python utility. Consider a narrow adaptation for a reproduced gap. Tests were
inspected but not executed here, where Node is unavailable; runtime reliability is not independently proven.

## Handoff-skill

The skill selects context around the goal, writes a handoff document and prints an opening message.
The user opens the next session and pastes that message. It offers a portable context format and
structural/output verifiers. It does not automate launch, acknowledgement, predecessor release or cleanup.

References: [SKILL.md](https://github.com/klittle32/handoff-skill/blob/57089b6e1ce61498ec70852e46d41b2f8f12fa00/SKILL.md)
and [README.md](https://github.com/klittle32/handoff-skill/blob/57089b6e1ce61498ec70852e46d41b2f8f12fa00/README.md).
The structural verifier passed all 80 assertions. No generated handoff sample was supplied for the output
verifier. Those structural assertions do not qualify autonomous host acceptance.

Decision: reference context selection if a failing case shows missing context. Copying its whole skill
would create another instruction owner without providing the automated runtime.

## Core evidence

The [handoff contract](../../.agents/engineering/workflow/handoff/SKILL.md) distinguishes ordinary launches,
full transfers, critical verified pickup and side workstreams. Critical transfers use
[transfer.py](../../.agents/engineering/workflow/handoff/scripts/transfer.py): atomic receipts bind the
goal digest, checkout, Git identity, harness and attempt. Matching acknowledgement and first-action
evidence are separate states. An interrupted launch becomes uncertain and cannot be retried blindly.
The helper explicitly does not implement a general writer lease or prove host acceptance.

The [Codex launcher](../../.agents/machine/utility/handoff-codex/scripts/launch_codex.py) selects a native
binary, resolves the requested model/effort, refreshes standards, launches through the terminal adapter
and prints submission evidence. The
[Claude launcher](../../.agents/machine/utility/handoff-claude/scripts/launch_claude.py) uses the same
adapter. Ordinary transfers and side workstreams do not automatically acquire the critical-transfer
receipt. Integration still depends on the agent following multiple procedure steps correctly.

Known launch and cleanup failures have existing owners in
[core issues](https://github.com/tj-agents/core/issues), including [core#390](https://github.com/tj-agents/core/issues/390): the pre-launch Claude refresh has no overall
process-tree deadline, own-session observer startup can fail, and a surviving Windows shell can pin a
worktree. Existing native session-name diagnostics also show that a launcher title does not prove the
name the user sees. Reconcile those repair owners before creating another repair.

The critical-transfer implementation artifact separates source/subprocess tests and in-session pickup
from authenticated independent terminal launch and normal installed-host acceptance. The 11 receipt
regressions passed during this assessment. They do not prove the whole native handoff lifecycle.

## Decision among the requested options

| Option | Assessment |
| --- | --- |
| Reference | Recommended now: cite the exact patterns and inspected revisions above. |
| Fork | Not justified for this boundary; candidates solve different workflows or introduce a broader runtime. |
| Copy selected parts | Conditional on a reproduced gap, isolated dependencies, preserved licensing and Windows/Linux verification. |
| Repair core | Recommended after a concrete failure identifies the layer and its existing repair owner. |
| Do nothing | Suitable for a satisfied requirement; known launch/closure gaps make it a poor overall response here. |

## Next action

Capture one failure with source/target harness, checkout, launcher output and exit, receipt state if
present, and observed recipient/predecessor state. Classify it as pre-launch, ambiguous submission,
pickup, context/authorization, duplicate ownership or closure/cleanup. The first runtime action is a
disposable failing regression in that layer, followed by comparison of the smallest fixes. This
assessment recommends a direction; it is not an implementation-ready runtime replacement plan.

