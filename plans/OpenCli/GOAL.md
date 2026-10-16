# Goal: one host-agnostic `open-cli` skill

Source owner: tj-agents/core (machine plugin: open-claude, open-codex, recover-agents, agent_recovery.py)
Authorization: Tommy, 2026-10-16: "it should just be open-cli the skill ... it shouldn't matter what the agent is it just
opens back that agent up whatever kind of agent it is", then "just do whatever, get this fucking thing done".
Implementation, tests, review, PR and merge per Core's own gates. No `--force`, no hook bypass.
Do not touch the plugin-scoping work (plans/PluginScoping), consumer repos, or ~/.claude/settings.json.

## Outcome
1. New skill `machine:open-cli`: input is a session id, a topic, or a directory. It resolves the session across Claude
   and Codex history (reuse `resources/machine/scripts/agent_recovery.py`), then reopens it in its own host. The caller
   never chooses a host.
2. If the session is verified live, focus the existing terminal tab instead of refusing (today `open_claude.py --resume`
   prints "verified live; refusing to create a duplicate writer" and the user cannot find the window).
3. `open-claude` and `open-codex` remain as internal host adapters; `recover-agents` points at `open-cli`.
4. Tests for resolution across both hosts, the live-session focus path, and the no-duplicate-writer guarantee. Windows and Linux.

## Next Steps
1. `cd` into a new worktree from origin/main (`Feature/OpenCli`) in tj-agents/core; verify path, branch, clean status.
2. Read `.agents/machine/utility/{open-claude,open-codex,recover-agents}` and `agent_recovery.py`; implement the outcome above.
3. `pwsh .agents/sync-generated.ps1`, then `-Check`; focused tests only; PR; deliver per Core gates.

## Progress
- 2026-10-16: goal created by the plugin-scoping session (tj-agents [6caeea]). Not started.
- 2026-10-16: implemented in `Feature/OpenCli` (worktree `.worktrees/Feature-OpenCli`): `agent_recovery.py reopen`
  (resolve across hosts, focus live, reopen closed), `close_tab.py --session --focus` plus `-Focus` in the Windows
  Terminal adapter, `machine:open-cli` skill and host entries, `recover-agents` pointer. Focused tests green
  (agent_recovery, close_tab, open_claude, source_layout); sync `-Check` clean. Next: PR, review, merge.
