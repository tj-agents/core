# Global machine events

Owner: tj-agents/core machine. Authorized by Tommy on 2026-10-20: replace hourly plugin and merge-policy polling with one outbound push subscription per machine, shared GitHub publisher, and bot-identity scheduler removal. No CLI startup work, new hooks, agent test sessions, or unbounded live tests.

## Assessment complete

Choose ntfy.sh's HTTPS newline-delimited JSON stream using Python 3.11 stdlib. It blocks while idle, supplies keepalives and replay, and needs only an unguessable topic. Official references: https://docs.ntfy.sh/subscribe/api/ and https://docs.ntfy.sh/publish/ . Anonymous topics are public; publish only repository names and change categories, never credentials or file contents. Free service limits and finite cache retention mean catch-up must read GitHub on connection establishment after an offline gap. Backoff reconnects transport failures; it never schedules GitHub checks. Gotify (https://github.com/gotify/server) needs a hosted server. GitHub webhook forwarding was already rejected in the supplied background as a testing facility with per-owner limitations. A custom broker/fork adds no required capability. Keeping timers violates the requested outcome.

Hints are versioned JSON: `{"v":1,"repo":"tj-agents/core","changes":["repository","marketplace","merge-policy"]}`. Fields are hints, never policy, commands, URLs, refs or credentials. Restrict repository owners to tj-agents, Concertable and tomjseery. Read current default-branch state from GitHub before applying installed github-actions merge-policy code. Run subprocesses as Tommy with inherited agent/token overrides removed. Apply only committed policies, never a default invented by the listener. Deduplicate identical authoritative revisions and serialize reactions.

## Delivery map

1. github-actions `Feature/EventAction`, base bd1d0ee: shared publisher action, shipped caller writer/scaffold integration and focused fixtures (estimated 400 code/test lines). Add single-repository reconciliation to merge-policy so the core listener never writes rules itself. Validate stdlib tests and generated package consistency.
2. core `Feature/MachineEvents`, base 43d751dc: listener beside plugin_autoupdate, setup migration, Task Scheduler logon/restart and Linux systemd user service, fixture tests (estimated 900 code/test lines). The listener invokes installed merge-policy reconciliation. Catch-up once per listener start and after disconnected intervals, never periodic GitHub scans. Include publisher use after package regeneration because GITHUB_TOKEN pushes do not generate push workflow runs. Validate fixtures and packaging. One bounded real check, on one repository, with no ruleset mutation unless current declared policy requires it.
3. personal `Refactor/BotIdentityOnly`, base 2b8c876: remove scheduler, merge-gates command and corresponding skill text/tests (estimated 100 deleted lines). Setup in core deletes legacy tasks/cron entries. Validate identity fixtures and generation.

The slices are separate repositories; publisher and listener are one coordinated contract. Tommy chose preparation of callers for every existing repository. Inventory contains 62 active repositories; uniform caller files are prepared under core/.worktrees/machine-event-callers, outside published source. Live runtime installation is performed only after the concrete candidate is reviewed and verified.

## Implementation decisions

- Core resolves installed github-actions utility from enabled plugin installations; no machine-local hand assembled helper.
- Topic is kept in machine state and an Actions variable on core so a second machine's setup can reuse it. Publisher uses one repository or organization secret containing that topic; no administrative GitHub credential enters Actions.
- Setup starts one supervised listener with a process lock, removes both former schedulers, and enables restart on failure. No hourly repetition, cron listener, CLI wrapper or host hook.
- Stream reader and reconciler are separate threads with a bounded coalescing queue so package refresh cannot block keepalive/replay ingestion. Failed actions remain pending for bounded retry with backoff; transport reconnection and reconnect catch-up recover dropped hints.
- Setup and installed plugin refresh replace the standalone listener/updater payload; the listener exits when its runtime bytes change and supervision restarts it. Deferred Codex updates use native process-exit waits.

## Verification and remaining work

Implementation exists in all three isolated worktrees. Focused fixtures: core 18 listener/setup + 34 updater; publisher/reconcile 8 + existing merge-policy 13; scaffold 102 (14 platform skips); personal identity 7. The bounded live check received one ntfy push and re-read tj-agents/core, returning undeclared with zero ruleset writes and zero agent sessions. Windows installed acceptance and Linux runtime acceptance are distinct from fixture verification. No agent sessions will be launched.

```agent-host-coverage
{"schema_version":1,"shared_source":".agents/machine/scripts/machine_events.py","hosts":[{"host":"claude","behavior":"Background plugin refresh outside CLI startup","source":".agents/machine/scripts/setup_machine.py","mapping":"machine resources on both hosts","verification":{"level":"planned","result":"pending","evidence":"18 listener/setup fixtures and 34 updater fixtures pass on Windows; bounded transport check remains"}},{"host":"codex","behavior":"Background plugin refresh outside CLI startup","source":".agents/machine/scripts/setup_machine.py","mapping":"machine resources on both hosts","verification":{"level":"planned","result":"pending","evidence":"18 listener/setup fixtures and 34 updater fixtures pass on Windows; bounded transport check remains"}}]}
```

The checked-in Workflow v2 helper cannot record skills because its legacy lookup expects `.agents/skills/plan-execution/SKILL.md`, which does not exist in this canonical layout. Continue with native Git, tests and the maintained artifacts under plan-execution's unavailable-runtime fallback.

The core listener/setup/fixture cutover is atomic: shipping a listener without its service registration would leave it dormant, and deleting the timers before that registration would lose updates. The publisher is a separate repository slice. Runtime packaging passes via the stdlib scripts behind the PowerShell wrapper; pwsh is unavailable on this machine.
