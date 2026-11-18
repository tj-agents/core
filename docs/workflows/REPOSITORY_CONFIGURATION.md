# Repository configuration

Repositories may add `.agents/configuration.json` with version `1` and namespace objects. Core currently reads only `configuration.core.auto_merge`; it is `false` when absent. A present configuration is authoritative, so legacy `delivery-authorization.json` can supply that preference only when the new configuration file is absent.

```json
{
  "schema_version": 1,
  "configuration": {
    "core": {"auto_merge": true}
  }
}
```

The preference never grants merge authority. Existing authorization, hold, review, check, and security gates still decide whether the guarded command may arm auto-merge. Future marketplace namespaces remain opaque to Core.
