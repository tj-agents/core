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

## D002 - Focus a live session that never registered its terminal tab

- **Kind:** debt. **Observed/reported:** 2026-10-16, review of the `open-cli` PR.
- **Cause:** `open-cli` focuses a verified-live session through the tab recorded in the `cli-sessions` registry at SessionStart. A session started before that hook existed, or in a terminal the registry cannot identify, has no tab to focus, so `reopen` reports the failure instead of focusing it.
- **Impact and priority:** P3; the user is told why and is never given a second writer.
- **Source owner:** Core machine peer-cli registry. **State:** deferred.
- **Deferral:** the registry is the only exact tab identity; a title guess could focus the wrong tab. **blocked_by:** design of a verified fallback. **Resolver:** Core machine owner. **Resume when:** a live session without a registry entry is reported.
- **Next action:** assess recovering the tab from the live process's ancestor terminal handle.
- **Resolution condition:** `reopen` focuses a verified-live session that has no registry entry, or states a verified reason it cannot. Delete this entry after verification.

## D003 - Windows Terminal tab titles are mutable

- **Kind:** debt. **Observed/reported:** 2026-10-16, review of the `open-cli` PR.
- **Cause:** the Windows Terminal adapter often sees an empty automation id, so focus and close match a tab by the title recorded at registration. Claude and Codex rewrite the title while running, so the recorded title can stop matching.
- **Impact and priority:** P3; focus fails with "absent or ambiguous" rather than touching a wrong tab.
- **Source owner:** Core machine peer-cli Windows Terminal adapter. **State:** deferred.
- **Deferral:** no stable per-tab identity is exposed by UI Automation on this build. **blocked_by:** an observable stable identifier. **Resolver:** Core machine owner. **Resume when:** Windows Terminal exposes an automation id or the registry records the tab's runtime id.
- **Next action:** record and match the tab's runtime id alongside its title.
- **Resolution condition:** focus and close find a live session's tab after its title changed. Delete this entry after verification.
