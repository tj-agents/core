# docs-and-debt compatibility debt

## The compatibility entry outlives its split

`engineering:docs-and-debt` was split into `guidance-ownership`, `debt-records` and `working-docs`.
Releases published before the split ship the old name as the rules owner, and every later release ships it
as a routing-only compatibility entry until it is removed. The `skills` alias table in
`.agents/plugins/compatibility.json` maps one name to one name, so it cannot redirect a split, and
`base:docs-and-debt` stays aliased to the routing entry. A consumer route row that requires the old name is
satisfied by loading the routing entry, which then directs the session to the owner it needs.

Resolve after 2027-04-09, and only once no `tj-agents` repository's route table, instructions or pinned
release still names `docs-and-debt` (move each remaining reference to the owner it means first): delete
this directory and both host entry points, the `base:docs-and-debt` alias, its row in the authored
`.agents/catalog/catalog.json` skill roster, and lower the canonical skill count in
`tests/test_source_layout.py` by one. Then confirm `grep -rniE "docs-and-debt"` over authored sources
finds only historical plans and reviews.
