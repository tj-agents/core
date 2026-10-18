# Agent discovery debt

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
