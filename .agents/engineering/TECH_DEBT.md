# Tech debt — engineering

## The `docs-and-debt` compatibility entry outlives its split

`engineering:docs-and-debt` was split into `engineering:docs` and `engineering:write-debt`.
Releases published before the split ship the old name as the rules owner, and every later release ships it
as a routing-only compatibility entry until it is removed. The `skills` alias table in
`.agents/plugins/compatibility.json` maps one name to one name, so it cannot redirect a split, and
`base:docs-and-debt` stays aliased to the routing entry. A consumer route row that requires the old name is
satisfied by loading the routing entry, which then directs the session to the owner it needs.

Resolve after 2027-04-09, and only once no `tj-agents` repository's route table or instructions on its
default branch names `docs-and-debt` (move each remaining reference to the owner it means first). A
consumer pinned to an earlier release keeps that release's copy and is unaffected. Delete
`.agents/engineering/convention/docs-and-debt/` and both host entry points, the `base:docs-and-debt` alias,
its row in the authored `.agents/catalog/catalog.json` skill roster and
the `docs-and-debt` case in `test_compatibility_entries_only_route_to_their_replacements`,
lower the canonical skill count in `tests/test_source_layout.py` by one, and delete this entry. Then confirm
`git grep -nIi docs-and-debt -- . ':!plugins'` finds only historical plans and reviews.

## The `techdebt` compatibility entry outlives its rename

`engineering:techdebt` was renamed `engineering:address-debt`. Releases before the rename publish the old
name. An alias in `.agents/plugins/compatibility.json` cannot carry a rename that changes the bare name yet
(the router checks proof against the old name; tracked by `Fix/RenameAliasRouting`), so the old name ships
as a routing-only compatibility entry and `base:techdebt` stays aliased to it.

Resolve after 2027-04-10, only once the router follows an alias that changes a bare name
(`Fix/RenameAliasRouting` merged), and only once no `tj-agents` repository's route table or instructions on
its default branch names `techdebt` (move each remaining reference to `engineering:address-debt` first). Delete
`.agents/engineering/workflow/techdebt/` and both host entry points, its row in the authored
`.agents/catalog/catalog.json` skill roster and its case in
`test_compatibility_entries_only_route_to_their_replacements`, retarget `base:techdebt` to
`engineering:address-debt`, lower the canonical skill count in `tests/test_source_layout.py` by one, and
delete this entry. Then confirm `git grep -nIw techdebt -- . ':!plugins'` finds only historical plans and
reviews, the `base:techdebt` alias and the transcript-search examples in `shell/cr.ps1`.
