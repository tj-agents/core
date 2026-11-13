# Repository settings

Repositories may add `.agents/settings.json` with a `configuration` object. Core reads
`configuration.core.auto_approve`, which is `false` when absent. It supports only the `all` and `design`
boolean members. Its only currently supported routine category is `design`, including convention choices.

```json
{
  "configuration": {
    "core": {
      "auto_approve": {
        "design": true
      }
    }
  }
}
```

An all-categories opt-in is:

```json
{"configuration":{"core":{"auto_approve":{"all":true}}}}
```

Omitted `all` and `design` members default to `false`. An explicit `design` member overrides `all`, so
`{"all":true,"design":false}` disables routine design approval. A present empty object disables design
approval.

`auto_approve` lets an agent make and record routine design and convention choices only within work the
user already authorized. Planning-only work remains planning-only, and explicit user decision reservations,
task scope, and stricter repository rules still apply. It grants no merge, publication, installation,
permission, or other external authority. Other valid namespace objects and unrelated root settings remain
opaque to Core. Source verification does not establish installed-host trust or acceptance.
