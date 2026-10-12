# Repository settings

Repositories may add `.agents/settings.json` with a `configuration` object. Core reads
`configuration.core.auto_merge` and `configuration.core.auto_approve_design`; each is `false` when absent.
A present settings file is authoritative, so `delivery-authorization.json` supplies its legacy auto-merge
preference only when `.agents/settings.json` is absent. Routine design approval has no legacy fallback.

```json
{
  "configuration": {
    "core": {
      "auto_merge": true,
      "auto_approve_design": true
    }
  }
}
```

The auto-merge preference never grants merge authority. Existing scoped or standing authorization, holds,
reviews, checks, and security gates still decide whether the guarded command may arm auto-merge.
`auto_approve_design` lets an agent make and record routine design and convention choices only within work
the user already authorized. Planning-only work remains planning-only, and explicit user decision
reservations, task scope, and stricter repository rules still apply. It grants no merge, publication,
installation, permission, or other external authority. Other valid namespace objects and unrelated root
settings remain opaque to Core. Enable this key only after selecting a core release that understands it;
older strict readers reject unknown core settings. Source verification does not establish installed-host
trust or acceptance.
