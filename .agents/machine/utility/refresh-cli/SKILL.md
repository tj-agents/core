---
name: refresh-cli
description: Install the latest merged tj-agents plugins on this machine in seconds with the hosts' native update, and verify what each host loads. Runs automatically after a merge from `engineering:merge`; otherwise use it as a last resort when a skill or hook is missing or out of date after a merge, or when asked to refresh, update or resync the CLI plugins.
kind: utility
domain: machine
route: infer
---

# Refresh CLI plugins

`<plugin-root>` is the machine plugin directory that holds `.claude-plugin/` and `.codex-plugin/`, two
levels above the `skills/refresh-cli/SKILL.md` or `codex-skills/refresh-cli/SKILL.md` entry point the host
loaded. It is never resolved from the shared `.agents/` copy. Run with `python` on Windows or `python3` on
Linux/macOS:

```sh
python -B '<plugin-root>/resources/machine/scripts/refresh_cli.py' --project '<absolute-checkout>'
```

It resolves `main` for each tj-agents source repository and runs `claude plugin update` only for the Claude
installs behind it, printing each step. It then records the installed generation and prints a JSON report.
Exit 0 means Claude is current. Afterwards, tell the user to run `/reload-plugins` in each open Claude session.
Only the user can run it. Each session's next prompt reports a superseded generation until it reloads.
Codex binds `main` at every launch, so the default run leaves it alone.

`--full` is slow: it updates every marketplace, runs the verified rolling refresh a bound launch performs,
and repairs Claude's registry for both hosts. Use it only when the default run reports a problem it cannot fix.
`--verify-only` reports without changing anything. `--host claude|codex|both` limits the hosts.
