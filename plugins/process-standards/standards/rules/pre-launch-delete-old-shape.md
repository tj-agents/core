# Nothing is live — delete the old shape, never preserve it

**This project is pre-launch: no production data, no deployed version to keep working, no external
consumer.** So the durable answer is deletion, not a compatibility layer. A change replaces the old shape
outright and rewrites its callers, tests, seed data and docs in the same stroke. No compatibility adapter,
no legacy envelope, no V1/V2 coexistence, no deprecation window, no straddle or dual-run, no retained-data
backfill, and no column, reader or overload kept "until its cutover".

A **new** type named `Legacy*`, `*V1`, `Old*` or `*Compat` is the smell: it says an old shape survived a
change that existed to remove it. Backfill tooling for data nobody has, and parity oracles for behaviour
nobody depends on, are invented work — worse than wasted, because the next design inherits the dead
vocabulary and builds on it.

**The exception is evidenced, never assumed.** Real deployed data, or a published package consumed outside
this workspace, changes the answer — confirm it exists before designing around it. "There might be data"
is not evidence, and the careful-compatibility instinct is the most expensive wrong default available here.
