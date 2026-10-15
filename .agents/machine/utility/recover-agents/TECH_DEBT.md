# Agent discovery debt

## D001 - Discover work and its sessions without knowing the work-item identifier

- **Kind:** debt. **Observed/reported:** 2026-10-15; Tommy suggested a future search-agent skill after asking how the existing terminal-cleanup owner was found.
- **Cause:** this session knew the identifier from the migration mappings, checked SQLite directly, then verified the exact item using the published status command. It did not discover the owner through a general work-item search.
- **Impact and priority:** P3; agents may miss existing owners when only a topic or description is known.
- **Source owner:** Core machine recover-agents and work-item/session discovery. **State:** deferred.
- **Repair link:** `.agents/machine/utility/recover-agents/TECH_DEBT.md#D001`; existing `search-codex`, `search-claude`, `recover-agents` and `work_item_sessions.py` remain the capabilities to assess. No new skill name or implementation is selected.
- **Deferral:** requested as future work; current P1 terminal cleanup takes priority. **blocked_by:** capacity. **Resolver:** Core machine discovery owner. **Resume when:** that owner accepts the bounded discovery proposal.
- **Next action:** assess existing search capabilities and the SQLite work-item/session metadata for topic, title and path discovery before deciding whether to extend an existing skill or add one; follow skill-authoring for that decision.
- **Resolution condition:** an unknown-identifier topic query finds the existing work item, its current status, canonical plan and exact associated native sessions, with ambiguity reported and no duplicate owner launched. Delete this entry after verification.
- **Verification evidence:** shipped exact-item status command was used successfully; no unified topic discovery or future skill delivery is claimed.
