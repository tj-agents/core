---
name: skill-routes
description: Building a repo's `.agents/skill-routes.json` — the layered floor-plus-route model where every matching row fires and the floors always apply, why a row keyed on a top-level directory cannot port to a carved repo while one keyed on architecture ports verbatim, the row fields (path, command, skills, conditional, content_requires, note, deny), the required tier that blocks versus the conditional tier that only advises, command routes that gate delivery commands on the procedure owning them, and the registry that ships a carved service repo's table inside the plugin instead of committing one per repo. Use when adding or changing a route or a command route, building a new repo's route table, carving a service repo, or deciding how to key a row's path.

kind: contract
domain: process
---

# Building a repo's skill-route table

Read and follow the [canonical shared definition](../../.agents/engineering/contract/skill-routes/SKILL.md) in full.
This entry point supplies only Codex discovery metadata; the shared procedure is authored once under `.agents/`.
