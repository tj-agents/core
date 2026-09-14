# base-agents

Read `README.md` before changing the shape of anything here.

## Where a file is authored

| Authored in | Holds |
|---|---|
| `.agents/` | what both harnesses use — skills and the files beside them, hook mechanisms, workflows, routes |
| `.claude/`, `.codex/` | only what one harness alone can use — its hook wiring, its agents, and a `workflow-skills/<name>` whose body differs per harness because the mechanisms it names differ |

`.claude/skills/`, `.claude/agents/`, `.codex/agents/` and everything under `plugins/` are **generated**.
Edit the `.agents/` source and run `pwsh .agents/sync-generated.ps1`. A file hand-placed in a generated
root is deleted on the next run, not kept.

A skill is harness-specific when the harness **running** it is — never when the thing it *targets* is.
`handoff-codex` launches Codex but is invoked from Claude, so it is shared; `persistent-workflow` is split
because the scheduling mechanisms it names exist only in one harness each. Ask which harness executes the
skill, not which agent its name mentions.
