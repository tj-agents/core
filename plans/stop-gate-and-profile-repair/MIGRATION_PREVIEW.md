# Scoped preference migration preview

The handoff excludes edits to employer repositories. Completing the user C++ naming migration
requires preserving the existing project opt-outs in the following local settings files.

For each file, keep the existing values and add these equivalent keys under `enabledPlugins`:
`cpp@tj-agents: false`, `msvc@tj-agents: false`, `win32@tj-agents: false`.
No code, tracked settings, permissions or other preferences change.

Files:
- `C:\Users\TommySeery\source\repos\infonetica\cris-authz\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\infonetica\cris-preaward-app\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\infonetica\cris-auth\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\infonetica\cris-auth-config\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\infonetica\cris-configuration-v2\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\infonetica\cris-diligence\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\infonetica\cris-erm-tfs\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\infonetica\cris-reverseproxy\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\infonetica\cris-service-bus\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\infonetica\infra-shiboleth-idp\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\infonetica\zanzibar-poc\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\infonetica\cris-erm\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\infonetica\cris-postaward\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\infonetica\cris-users\.claude\settings.local.json`
- `C:\Users\TommySeery\source\repos\infonetica\standards-docs\.claude\settings.local.json`
