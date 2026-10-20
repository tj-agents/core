---
name: write-debt
description: Record a deliberate shortcut or deferral with its owning area, reasoning and objective resolution condition. Use the explicitly selected provider, otherwise the owning area TECH_DEBT.md and its verified deletion rule. Use when logging tech debt, taking a shortcut, or deciding to leave a defect, risk or rule violation unfixed; working an existing entry down to a PR is the address-debt workflow.

kind: convention
domain: process
---

# Tech debt

Read [the shared problem-record contract](../../resources/problem-records.md). The contract owns common
fields, priorities, repair links, deduplication, blocked and deferred evidence, and retention distinctions.

Known faulty behavior belongs in `engineering:write-bug`; link its repair rather than duplicating that repair
as debt. A debt entry may still name the deliberate deferral or shortcut in its owning area.

Follow the shared contract's explicit provider selection first. Use its create/read/update and verified
closure commands, preserving the owning area, reasoning and exit condition. Provider retention applies;
remote closure may retain history. The file-backed defaults below apply only without a provider.

Record tech debt in the `TECH_DEBT.md` belonging to the area that **owns the problem**; if that area has none,
create it there rather than adding the entry to a broader parent. **One entry per owning area** — two areas
hitting the same underlying cause is two entries, not one in their shared parent, because they are fixed
separately and are usually blocked by different things. **Once the debt is addressed, delete the entire
entry** — a resolved entry retained as an archive is just another stale doc.

**Everything you decide not to fix earns an entry** — a shortcut taken, and equally a defect, risk or rule
violation you noticed and deliberately left alone. A shortcut is acceptable only where it is genuinely,
provably the right call. "Unrelated to what I was doing" is a perfectly good reason to leave a problem and
no reason at all to leave it unwritten. Write it down as you make the decision, with the reasoning and an
objective resolution condition — a problem only one agent ever saw is one nobody will fix.
