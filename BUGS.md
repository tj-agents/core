# Bugs


## B001 - Verified self-host remains alive after Windows Terminal discovery refuses

- Kind: bug. Observed/reported: 2026-10-12; exact close.py invocation refused Windows Terminal target is absent or ambiguous after observer acceptance/arming; observer cancelled because host did not exit.
- Cause: confirmed self-close/finish catches TerminalUnavailable only, while absent/ambiguous actual target raises TerminalRefusal. Own PID/start/attachment verified; current UI inventory has zero actual tabs. Infrastructure cause of UI discovery failure remains unknown.
- Impact/priority: P2; completed CLIs remain open and cleanup completion is unreliable.
- Source owner: machine peer-cli close.py/finish.py and directly causal closure guidance. State: in-progress.
- Repair link: plans/verified-self-close/GOAL.md, Fix/VerifiedSelfCloseFallback.
- Next action: independently reproduce refusal and repair verified self-process fallback while preserving peer-tab and unknown/PID-change refusal.
- Resolution condition: focused observer/process/identity regressions and Windows/Linux CI pass; reviewed source repair merged and causal generated packages verified.
- Verification evidence: exact registry entry PID9104/start1791756662.4871101; predecessor observer 1f29421b77f448e39c489f380948dbc2.json accepted/armed then cancelled; current actual_tab_count=0.
