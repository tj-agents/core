# Tech debt — lanes

## The default delegation host is all-or-nothing instead of a weighted split

`lanes` says a Claude parent hands multi-phase work and every delegated design, implementation or review
phase to Codex unless the user explicitly chooses Claude. On 2026-10-12 Tommy said the default is wrong. When he
names no host, delegated work should go to Codex about two times in three and stay on Claude about one time
in three. Today an ambiguous request either goes to Codex every time or, as happened in the azure app-profile
goal, is read as choosing Claude.

- Kind: debt. Source owner: `engineering:lanes` (this folder), plus any launcher or workflow that applies the
  host choice.
- Priority: P2. It changes the cost and host mix of delegated work, but no active harm is observed.
- State: open. Repair link: none.
- Next action: replace the "unless the user explicitly chooses Claude" sentence with a weighted default of
  2:1 Codex to Claude when the user names no host. Make the draw recorded and reproducible per dispatch, so
  a run can say which host it drew and why. An explicit user choice still wins.
- Resolution condition: the lanes policy states the 2:1 default, and the code that picks a delegation host
  applies it with an explicit-choice override. A test shows both hosts are selected at the configured
  ratio for unspecified requests, and never against an explicit choice.
- Verification evidence: the current rule text in `SKILL.md` ("A Claude parent hands multi-phase work and
  every delegated design, implementation, or review phase to Codex before delegating, unless the user
  explicitly chooses Claude"), and Tommy's 2026-10-12 instruction.
