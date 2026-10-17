# Close completed CLI sessions through a public Core operation

Status: Complete
PR: https://github.com/tj-agents/core/pull/285
Source owner: machine/close and base/goal-continuation
Repair workflow: engineering:self-repair

## Problem and authorization

PluginScoping completed and the agent reported done without invoking the buried close helper.
Tommy authorized a dedicated skill and clarified that this CLI must close whenever all its owned work
is done, in every Core-consuming repository, for ordinary tasks as well as plans and merges.
This repair preserves other sessions, their checkouts and unrelated OpenCli, HandoffScope, harness
injection and plugin-dependency work. No force or hook bypass is authorized.

## Delivered behavior

Core #285 merged source head `a8d716be16cb1f067b899e4a4f8b7b2bec2876f4` as
`16d0d994b42664fb727b2518bcf605fcd006b5a2`. The merge-triggered regeneration job published
`8ecfe3e9c8626638b7c5c5a1637f94c74c4a80f1` with the shared skill and both host mappings.

- `machine:close` prepares before the report, routes at Stop, and completes in the foreground after
  other Stop-gate feedback permits closure. Stop itself never signals a process.
- Base guidance applies it to all completed CLI-owned work. Code and documentation delivery select
  the same owner; peer-cli's self-close helpers remain its underlying runtime.
- A new prompt cancels preparation. Atomic turn-state comparison, exact PID/start-time identity,
  shared-process refusal and verified exit observers preserve active work and other sessions.
- Default closure retains the checkout. Removal still requires the existing merged-worktree proof.
- Runtime dependencies ship together. No author-checkout fallback or per-repo helper is required.

## Verification

Exact-head PR CI [39044207226](https://github.com/tj-agents/core/actions/runs/39044207226) passed
Windows, Linux and the required aggregate. Focused local checks passed: 21 operation regressions,
39 close/finish regressions, 22 source-layout regressions, 19 harness declarations, the SQLite prompt
race and a Windows disposable registered-host proof. Generation and -Check passed.

The initial independent native review findings were fixed. Later native attempts refused unrelated
publisher-catalog mismatches, and the configured workflow lens was unavailable. The documented parent
fallback reviewed those frozen deltas; no fresh native approval or installed live-Claude/Codex
acceptance is claimed. The disposable-host proof establishes the runtime boundaries separately. Post-merge main CI
[39045611951](https://github.com/tj-agents/core/actions/runs/39045611951) also passed both platforms
and the regeneration job; the generated publication is on main.

## Next Steps

No implementation remains. Core #285 is merged, published and green after the merge. Consuming
repositories pick up the new shared operation through their normal rolling session sync.

## Completion evidence

```completion
{
  "outcome": "Completed CLI work has one shipped Core close operation and a host backstop in every consuming repository.",
  "acceptance": [
    {
      "id": "public-operation",
      "criterion": "A shipped machine:close operation is discoverable on both hosts",
      "evidence": [
        {
          "source": "https://github.com/tj-agents/core/pull/285",
          "result": "Merged; regeneration published the canonical utility, both adapters and runtime dependencies."
        }
      ],
      "owner": null,
      "next_action": null
    },
    {
      "id": "generic-selection",
      "criterion": "Every Core-consuming repository selects closure for all completed CLI-owned work",
      "evidence": [
        {
          "source": ".agents/base/policy/goal-continuation/SKILL.md and merge/merge-docs/peer-cli guidance",
          "result": "Shared policy and terminal owners select machine:close without requiring a PR or plan."
        }
      ],
      "owner": null,
      "next_action": null
    },
    {
      "id": "safe-lifecycle",
      "criterion": "Reports, other Stop gates, new prompts and exact registered identities gate closure",
      "evidence": [
        {
          "source": ".agents/machine/utility/close/scripts/close_session.py and focused process/SQLite regressions",
          "result": "Stop never signals; post-report completion is explicit, new prompts cancel, shared identities refuse, checkout retention is default."
        }
      ],
      "owner": null,
      "next_action": null
    },
    {
      "id": "platform-validation",
      "criterion": "Required source and runtime checks pass on Windows and Linux",
      "evidence": [
        {
          "source": "https://github.com/tj-agents/core/actions/runs/39044207226",
          "result": "Success at the exact merged source head, including both platform verification jobs and ci-required."
        }
      ],
      "owner": null,
      "next_action": null
    },
    {
      "id": "publication",
      "criterion": "The exact merge-triggered publication and post-merge checks succeed",
      "evidence": [
        {
          "source": "https://github.com/tj-agents/core/actions/runs/39045611951",
          "result": "Succeeded at merge 16d0d994b42664fb727b2518bcf605fcd006b5a2, including regeneration and Windows/Linux verification; generated publication 8ecfe3e9c8626638b7c5c5a1637f94c74c4a80f1 is on main."
        }
      ],
      "owner": null,
      "next_action": null
    }
  ],
  "deliveries": [
    {
      "repository": "tj-agents/core",
      "pr": 285,
      "head": "a8d716be16cb1f067b899e4a4f8b7b2bec2876f4"
    }
  ],
  "open_tasks": []
}
```

## Host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/machine/utility/close and .agents/base/policy/goal-continuation",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Close this CLI after all owned work, report and other Stop gates; retain checkout by default",
      "source": ".agents/machine/utility/close/SKILL.md and scripts/close_session.py",
      "mapping": ".claude/skills/close and .agents/plugins/manifests/claude/machine-hooks.json",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Claude transcript parsing, prompt cancellation, post-report routing and permission declarations covered by focused source tests. Windows disposable registered-host closure passed. Installed Claude acceptance is not claimed."
      }
    },
    {
      "host": "codex",
      "behavior": "Close this CLI after all owned work, report and other Stop gates; retain checkout by default",
      "source": ".agents/machine/utility/close/SKILL.md and scripts/close_session.py",
      "mapping": ".codex/skills/close and .agents/plugins/manifests/codex/machine-hooks.json",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Codex final-channel transcript parsing, prompt cancellation, post-report routing and permission declarations covered by focused source tests. Windows disposable registered-host closure passed. Installed Codex acceptance is not claimed."
      }
    }
  ]
}
```
