---
name: git-auth
description: Use existing native Git and gh authentication for the selected repository, diagnose refused GitHub access, and preserve the user's credential configuration. Use when GitHub access is refused or before an authorized Git or gh operation needs verified access.

kind: policy
domain: process
---

# Select native GitHub access

Owns repository-scoped use of existing native Git and gh authentication, including evidence-based diagnosis
of refused GitHub access. It never creates an enrollment, binds a checkout to an employer credential, or
routes access through a separate token store or gateway.

```text
Repository: github.com/acme/project; the user authorizes a read-only access check.
Run: git ls-remote origin
     gh auth status
     gh repo view acme/project --json viewerPermission
Result: the remote reachability, active gh identity and repository permission are known; no credential,
        host setting or repository binding changed.
```

## Keep scope and identity explicit

Use the checkout's configured remote and the user's existing Git credential helpers and `gh` authentication.
Keep global native helpers and any already-configured GitHub MCP helper intact. A configured MCP helper is
optional evidence for the operation; Git and `gh` do not require it and it must not become a credential
gateway.

Personal policy applies only after the repository explicitly adopts Personal. A bot identity also requires
its own explicit opt-in and configuration. Repository ownership, a GitHub account, an employer remote, or
access to a credential does not establish either scope.

Do not create tokens, change `gh` login state, alter global Git credential helpers, replace `HOME` or
`GH_CONFIG_DIR`, add a repository-specific credential binding, or create a separate token vault. A global
native helper remains the user's configuration; do not replace it to route one employer or checkout.

## Diagnose the refused operation

Start with the least invasive authorized native check for the selected remote. Use Git to establish remote
reachability and `gh` to identify its active account and the repository permission needed for the requested
operation. When an actual authorized operation is refused, distinguish evidence for invalid or missing
authentication, the wrong active identity, missing repository permission, required organization SSO, and a
network or service failure.

Treat organization SSO as GitHub's own authorization step. Report the concrete GitHub response and its
organization or authorization link when available; do not infer an SSO state from the repository owner or
try to change organization policy. A denied operation that lacks enough evidence remains unavailable rather
than a guessed permission finding.

Only the user may authorize a native authentication change. If they do, use the normal Git or `gh` flow they
selected and re-run the relevant repository check. Never request, print, paste, pass through command
arguments, add to environment dumps, automate through the clipboard, or write a token, password, private key
or session credential to a file.

Existing repository access does not authorize a different administration operation. Request only the
operation the user has authorized, and report the missing access or evidence when it cannot be verified.
