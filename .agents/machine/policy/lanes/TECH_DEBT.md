# Tech debt — lanes

## D001: The default delegation host is all-or-nothing instead of a weighted split

`handoff` sends every requested handoff with no named host to Codex. On 2026-10-12 Tommy said the
default is wrong. When he names no host, delegated work should go to Codex about two times in three and stay
on Claude about one time in three. Today an ambiguous request either goes to Codex every time or, as happened
in the azure app-profile goal, is read as choosing Claude.

- Kind: debt.
- Observed/reported: 2026-10-12. Tommy reported it after a Claude session treated "do u wanna finish this
  off" as an explicit Claude choice and ran the implementation in Claude lane agents. Cause confirmed: the
  rule text below has no default split.
- Source owner: `workflow:handoff`, plus any launcher or workflow that applies the host choice.
- Priority: P2. It changes the cost and host mix of delegated work, but no active harm is observed.
- State: open. Repair link: none.
- Next action: replace the handoff's Codex-only default with a weighted 2:1 Codex-to-Claude default when
  the user names no host. Make the draw recorded and reproducible
  per dispatch, so a run can say which host it drew and why. An explicit user choice still wins.
- Resolution condition: the handoff policy states the 2:1 default, and the code that picks a delegation host
  applies it with an explicit-choice override. A test shows both hosts are selected at the configured ratio
  for unspecified requests, and never against an explicit choice.
- Verification evidence: the handoff rule text ("otherwise select `machine:handoff-codex`"), and Tommy's
  2026-10-12 instruction.
