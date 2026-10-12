# Repository settings

Repositories may add `.agents/settings.json` with a `configuration` object. Core reads only
`configuration.core.auto_merge`; it is `false` when absent. A present settings file is authoritative,
so `delivery-authorization.json` supplies its legacy preference only when `.agents/settings.json` is absent.

```json
{
  "configuration": {
    "core": {"auto_merge": true}
  }
}
```

The preference never grants merge authority. Existing scoped or standing authorization, holds, reviews,
checks, and security gates still decide whether the guarded command may arm auto-merge. Other valid
namespace objects and unrelated root settings remain opaque to Core.
