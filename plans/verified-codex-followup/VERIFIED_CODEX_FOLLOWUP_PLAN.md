# Verified Codex follow-up

## Authorized scope

Tommy asked this conversation to fix failed follow-up delivery in core, using this session and lanes instead of another external handoff. Implement and validate a packaged machine skill/helper. Do not change the separate in-session lane execution policy branch or send the original correction again.

## Design

The observed native `codex queue` success meant persisted queue acceptance, not recipient delivery. The target standalone TUI had no reachable shared daemon and its follow-up remained queued without a corresponding user message.

Use only an existing app-server proxy, exact thread UUID and expected cwd. Require the thread to be loaded and able to accept direct input. Steer an active turn with its expected ID, or start a turn on the same loaded idle thread. Never launch/resume another owner, start a daemon, change profile settings, inject terminal keystrokes, or write Codex databases.

Persist a receipt before submission. Repeating the command with that receipt performs status verification only. Verify the client message ID in recipient history before reporting delivery; accepted, unknown and unavailable remain explicit. Delivery does not prove acknowledgment or task completion. Unreachable standalone sessions get an honest paste fallback. Status inspection of the original queue is read-only.

## Sequence and acceptance

1. Implement canonical skill, thin host adapters, shipped helper, and synthetic regression tests.
2. Validate active/idle transport, identity checks, retry safety, queue-only failure, process cleanup and packaging.
3. Run a read-only check of the original incident, independent review, local commit and authorized delivery. Record supported paths and actual host limitations.

## Progress

- Diagnosis confirmed against local Codex 0.157.1 help, generated protocol schemas and selected profile queue/history stores.
- Created isolated branch `Fix/VerifiedCodexFollowup` at `61b5b1ee19f7660ad881839525693fa7387809be`.
- No new recipient message sent; no profile/config changes.
- Implemented the canonical skill, both host adapters and skill-local helper. Twenty-three synthetic behavior and real stdio-process regression tests pass.
- Read-only incident recheck: original message remains queued; matching recipient user-message count is zero.
- No supported shared daemon endpoint exists for the original standalone TUI. The helper must report unavailable there; actual live delivery remains unproven.
- Package generation, sixteen source-layout checks and the packaging script pass.
- A live read-only proxy probe failed explicitly without submitting a message, matching the standalone-session limitation.
- Independent review identified one approval-ownership defect: inbound server requests must not receive a synthetic RPC error from this helper. Fixed by closing the helper without answering; a real stdio regression verifies no response or second turn request.
- Incremental review and exact-head remote validation pending.
- Delivery slice: one utility and its regression/packaging closure; generated copies account for most added lines and remain atomic with their source.
