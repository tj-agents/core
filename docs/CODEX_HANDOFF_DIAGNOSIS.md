# Codex handoff diagnosis — 2026-10-20

Assessment complete: repair the existing launch-status contract. Native repository trust owns project-config admission; the existing SessionStart dispatcher already acknowledges startup and invokes session registration. No new hook, trust gate, launch-time refresh, package installer or dependency is needed.

## Evidence

The laptop receipts `tj-agents-handoff-pw3rm2d3/status.json` and `tj-agents-handoff-ngnnlrdr/status.json` failed at 15:24:38 and 15:25:15 UTC (16:24–16:25 BST), respectively. The first stopped at `reading-selection` in package `85e3a0d3`; the second reached `waiting-session-start` in `43d751dc`. Neither retained a native startup trace.

The saved user configuration `config.toml.pre-bot-identity.bak` (16:21:31 BST) has no trust entry for the personal repository root. It trusts a different personal worktree. The personal repository configuration already existed at 15:51:54 BST and declares the tj-agents Git marketplace and machine plugin. The current user configuration (16:28:20 BST) adds trust for the personal repository root and still has no user-level tj-agents marketplace. These timestamps support a trust-admission explanation for the historical missing configuration and acknowledgement; the receipts alone cannot prove which screen the TUI displayed.

An isolated native configuration fixture on Codex 0.163.0-alpha.1 used the same personal repository and user-enabled machine plugin, without a user marketplace. With explicit untrusted repository state, config/read returned no tj-agents marketplace and reported that project-local config, hooks and exec policies were disabled. With trusted repository state, the same read returned the repository marketplace with no disabled reason. Only initialize and config/read were called; no agent thread was started or plugin installed. The fixture required --no-daemon to avoid fresh-profile daemon initialization.

Current native discovery in the normal profile returns machine@tj-agents enabled and its SessionStart hook enabled and trusted, sourced from plugins/cache/tj-agents/machine/local/hooks/codex.json. Invoking that installed hook with a synthetic SessionStart payload acknowledged startup in 1.26 seconds. A packaged regression fixture also asserts the exact acknowledgement token and the session registration JSON. Acknowledgement is written by hook_dispatch before register_session executes; a marker alone does not prove registration finished.

Claude installed_plugins.json separately contains a user machine@tj-agents registration at 43d751dc and a project registration at 85e3a0d3 for core/.worktrees/Feature-CloseWatcher. Updating the user installation does not replace that project-scoped registration or instructions already loaded in an active Claude session. The older package still contains the removed launch preflight. This is scoped native refresh/adoption state, separate from the current launcher timeout defect. Refresh and reload the owning Claude scope when adopting the published repair; do not rewrite installed cache bytes or reintroduce launch-time refresh.

## Repair and fixture acceptance

Previously the 20-second missing-ack error entered broad exception cleanup and terminated the live native process tree, closing its tab. The wrapper now reports unconfirmed startup and preserves the original child, continuing to observe a late acknowledgement. The parent returns uncertainty (exit 3) with the exact receipt and an explicit instruction not to relaunch. Verified startup still requires the exact attempt token. Native exit and actual launch failures retain their existing behavior.

Deterministic fixtures cover a real dummy child surviving the deadline and retaining exit code 7 for both host names; late acknowledgement confirming the same PID; truthful unconfirmed status; one tab submission with no retry; packaged machine hook acknowledgement and registration; and existing executable, terminal, handoff and configuration behavior. Fixtures use temporary directories including spaces and non-ASCII characters. No real agent session is used by these tests.

Windows focused suites pass. The registration suite initially exposed a local inherited Git environment issue: Windows environment restoration dropped an empty GIT_CONFIG_VALUE_1 while GIT_CONFIG_COUNT remained 5. The unchanged suite passes with process-local GIT_CONFIG_COUNT=0 for its temporary local repositories; no authentication setting or assertion was weakened. Linux fixture execution and the one bounded real handoff are pending at this checkpoint.
