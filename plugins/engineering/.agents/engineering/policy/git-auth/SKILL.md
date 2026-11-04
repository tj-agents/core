---
name: git-auth
description: Select GitHub credentials for the owning work, diagnose denied access, and honor an explicitly authorized fine-grained or classic token choice. Use when access is refused or before requesting, creating or widening credentials.

kind: policy
domain: process
---

# Select credentials for the owning work

Keep access decisions tied to the owning organization, requested operations and the user's authority.
A refused call requires diagnosis; never switch token types, widen scopes or change organization policy
automatically. Use the selected profile's existing GitHub App when it already supplies the needed access.

```text
Fine-grained token awaits employer admin approval, which the user cannot obtain.
User explicitly chooses classic repository access with employer SSO.
Select github:access classic onboarding; keep employer routing and secure storage in force.
Do not generate another fine-grained token or request organization administration scopes.
```

## Offer the supported token choices

A fine-grained personal access token has one resource owner and selected repository permissions. Prefer
it when the organization permits it and required approval is available. State the actual resource owner,
repository access and permissions; its creation URL does not preselect repositories.

A classic personal access token is a supported choice when the user explicitly authorizes its broader
scope. It can reach repositories beyond the owning organization, so never describe the credential itself
as organization-scoped. For ordinary private repository work use `repo`; include `workflow` when workflow
writes are needed. Employer SSO authorization and organization restrictions still apply. Classic-token
SSO authorization and fine-grained administrator approval are different steps.

`github:access` owns both onboarding forms, token validation, secure storage, rotation, tool routing and
readiness checks. An employer-owned profile declares its default method and repository access, including
all repositories in that organization when authorized. Preserve the selected checkout and organization
boundaries even when the underlying credential is broader. Personal GitHub App setup keeps its owner.

## Diagnose and complete the selected flow

Distinguish invalid authentication, wrong identity, missing SSO authorization, pending organization
approval, insufficient repository permissions and unavailable network checks from observed evidence.
Do not call a token ready merely because the local submission page received it. Verify actual access
through the selected Git, gh and MCP routes before claiming readiness.

The human creates and submits a token through the secure local flow and completes required GitHub/SSO
actions. Never request the value in chat, command arguments, environment dumps, clipboard automation or
files. Do not configure an account-wide gh login as an employer-routing shortcut.

Existing repository access does not grant authority for an unrelated administration operation. Request
additional permissions only for an explicitly authorized operation that needs them. If no authorized
credential can perform a check, record it unavailable and explain the missing evidence; never turn a
refused check into a guessed finding.
