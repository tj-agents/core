# Kandev execution-deck boundary

Kandev is the outer agentic coding deck, not a workflow-state provider. It owns the task board, the task's
isolated worktree, native Claude or Codex session presentation and resume, and independently resumable
top-level tasks or subtasks.

Managed profiles use CLI Passthrough so the real host TUI loads repository instructions, project skills,
project-scoped agents, hooks, MCP configuration, and subscription-backed authentication. The workflow
contract does not call a Kandev API, store Kandev task or session identifiers, or mirror Kandev's task graph.

Inside one task, the host-native parent owns task selection, reasoning, bounded dispatch, review synthesis,
and acceptance. Independent read-only roles may overlap. Every writer remains serialized under one exact
repository lease. Work requiring its own independently resumable worktree belongs in another Kandev task or
subtask, not another writer inside the same workflow.

Bare Claude or Codex sessions consume the same generated workflows and repository state. Kandev absence
never changes workflow selection or makes portable repository work unavailable.
