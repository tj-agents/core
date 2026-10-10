---
name: debt-records
description: Recording tech debt — an entry in the TECH_DEBT.md of the area that owns the problem, one entry per owning area, everything deliberately left unfixed written down with its reasoning and an objective resolution condition, every noticed problem fixed, handed off or recorded on the default branch before moving on, and the whole entry deleted once the debt is addressed. Use when logging tech debt, taking a shortcut, or deciding to leave a defect, risk or rule violation unfixed; working an existing entry down to a PR is the techdebt workflow.

kind: convention
domain: process
---

# Tech debt

Record tech debt in the `TECH_DEBT.md` belonging to the area that **owns the problem**; if that area has none,
create it there rather than adding the entry to a broader parent. **One entry per owning area** — two areas
hitting the same underlying cause is two entries, not one in their shared parent, because they are fixed
separately and are usually blocked by different things. **Once the debt is addressed, delete the entire
entry** — a resolved entry retained as an archive is just another stale doc.

**Everything you decide not to fix, and do not hand off, earns an entry** — a shortcut taken, and equally a
defect, risk or rule violation you noticed and deliberately left alone. A shortcut is acceptable only where
it is genuinely, provably the right call; "unrelated to what I was doing" is a perfectly good reason to
leave a problem and no reason at all to leave it unwritten. Write it down as you make the decision, with the
reasoning and an objective resolution condition — a problem only one agent ever saw is one nobody will fix.

**Every problem you notice is fixed, handed off or recorded before you move on, and the outcome reaches the
default branch.** Handing off means launching a side workstream through `engineering:handoff`, or giving the
problem to the active owner of its fix who confirms it is in their goal; that goal, which ends in a merged
fix, is then the record. Anything else left unfixed gets the entry above, merged to the default branch in
the current PR when that PR will land, otherwise in its own docs-only PR opened straight away. That PR is a
meta-only slice with the same standing authorization planning artifacts have, and it lands as
`engineering:plans`' "Planning artifacts always land" defines, including its validation, docs review and
typed delivery gates. A chat reply, a message, an issue, a scratch file or an entry on a branch that may
never merge is not a record.
