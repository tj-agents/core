# Skill kinds

`kind` is an open taxonomy shared by the agent marketplace repositories. Every skill must declare one
lowercase ASCII word. Generators validate that shape, not a closed list, so adding a category never requires
editing generator source across repositories.

The vocabulary currently used is:

| Kind | Meaning |
|---|---|
| `contract` | A load-on-demand engineering standard. |
| `lane` | A model-selection role. |
| `lens` | A review perspective. |
| `operation` | One executable process step. |
| `utility` | A machine tool run directly by a session. |
| `workflow` | A coordinated process spanning multiple steps. |

Add a new word here when its meaning is materially distinct. A repository may enforce a semantic invariant
where behavior depends on the kind, such as routed standards being `contract` or host workflow skills being
`workflow`; it must not duplicate this vocabulary as an allowlist.
