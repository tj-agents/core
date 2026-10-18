---
name: refresh-cli
description: Refresh Claude's and Codex's installed tj-agents plugins to current main in one command, repair what each host actually loads, and verify it. Use when a skill or hook is missing or out of date after a merge, when /reload-plugins still shows old standards, or when asked to refresh, update or resync the CLI plugins.
kind: utility
domain: machine
route: infer
---

# Refresh CLI plugins

Run with `python` on Windows or `python3` on Linux/macOS, from the repository whose selection should be
refreshed:

```sh
python -B '<skill-directory>/../../resources/machine/scripts/refresh_cli.py' --project '<absolute-checkout>'
```

For each host it updates every registered tj-agents marketplace, runs the same verified rolling refresh a
bound launch performs, and repairs Claude's plugin registry so the recorded `version` names the refreshed
install. It then compares every enabled tj-agents package with its repository's `main` and prints a JSON
report. Exit 0 means both hosts are current; otherwise each entry's `problems` names what is stale.
Bound Codex launches build each session's packages from `main`, so Codex's `unused_stale_cache` lists
only cached copies that a launch bypassing the tj-agents launcher would load.

Pass `--host claude` or `--host codex` for one host, and `--verify-only` to report without changing
anything. A refresh takes a few minutes. Afterwards, run `/reload-plugins` in each open Claude session;
new Codex sessions load the refreshed packages.
