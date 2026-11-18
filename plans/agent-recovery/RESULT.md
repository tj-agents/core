# Agent recovery delivered

PR #151 merged at 6c56b76f2103f7e4b6365b78921cc9f04375494f after exact-head CI run37798028254 passed. All five shared skills live in .agents/machine/utility with thin entries for Codex and Claude.

Search returns saved conversation identity, topic/title/checkout, profile and live status. Opening resumes the exact native session in its saved directory with a continuation instruction. Live-session identity checks, serialized launch receipts and conservative handling of ambiguous launches prevent duplicate writers. recover-agents coordinates both pairs and validates selected sessions before opening them.

Local integrated137 tests passed with12 platform skips; package/harness/source guards and full PR CI passed. Installed plugins were updated through their supported native paths and inspected directly.

Native review used the permitted internal fallback after automatic approval review rejected a separate source-payload review. No rejected payload was sent. Historical user work was not reopened; the unrelated Sol-owned handoff remains untouched.

Installed package evidence:

```json
{
  "codex": {
    "package": "C:\\Users\\TommySeery\\.codex\\plugins\\cache\\base-agents\\machine\\2.1.16",
    "skills": [
      "search-codex",
      "open-codex",
      "search-claude",
      "open-claude",
      "recover-agents"
    ],
    "helper": "C:\\Users\\TommySeery\\.codex\\plugins\\cache\\base-agents\\machine\\2.1.16\\resources\\machine\\scripts\\agent_recovery.py",
    "resources": "loaded",
    "help": "passed"
  },
  "claude": {
    "package": "C:\\Users\\TommySeery\\.claude\\plugins\\cache\\base-agents\\machine\\6e2e2db3d1ad",
    "skills": [
      "search-codex",
      "open-codex",
      "search-claude",
      "open-claude",
      "recover-agents"
    ],
    "helper": "C:\\Users\\TommySeery\\.claude\\plugins\\cache\\base-agents\\machine\\6e2e2db3d1ad\\resources\\machine\\scripts\\agent_recovery.py",
    "resources": "loaded",
    "help": "passed"
  },
  "native_search": {
    "host": "codex",
    "id": "01a11b14-2ce8-71b1-95c5-0a97f5d383a6",
    "cwd": "C:\\Users\\TommySeery\\source\\repos\\tj-agents\\core\\.worktrees\\Fix-SkillHarnessGrants",
    "profile": "c:\\users\\tommyseery\\.codex",
    "status": "live"
  }
}
```
