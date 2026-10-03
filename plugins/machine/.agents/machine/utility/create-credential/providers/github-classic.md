# GitHub classic personal access token

Prefer a fine-grained token; use classic only where the needed scope exists only there.

URL template:

```text
https://github.com/settings/tokens/new?scopes=<scope,scope>&description=<description>
```

Not settable by URL: expiration — verify the dropdown instead of accepting whatever it shows.

Sudo mode, password and 2FA behave as the fine-grained recipe describes. The generated value starts
`ghp_` — that prefix is the delivery validation.
