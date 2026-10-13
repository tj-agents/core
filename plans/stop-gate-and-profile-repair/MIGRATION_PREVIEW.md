# Scoped preference migration preview

The handoff excludes edits to employer repositories. Completing the user C++ naming migration
requires preserving the existing project opt-outs in the following local settings files.

For each file, keep the existing values and add these equivalent keys under `enabledPlugins`:
`cpp@tj-agents: false`, `msvc@tj-agents: false`, `win32@tj-agents: false`.
No code, tracked settings, permissions or other preferences change.

Files:
- `C:\Users\TommySeery\source\repos\company\authz-service\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\company\costing-app\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\company\auth-service\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\company\auth-service-config\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\company\config-service\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\company\diligence-service\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\company\erm-legacy\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\company\reverse-proxy\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\company\cris-service-bus\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\company\infra-shiboleth-idp\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\company\zanzibar-poc\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\company\erm-service\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\company\postaward-service\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\company\users-service\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\company\standards-docs\.claude\settings.local.json`
