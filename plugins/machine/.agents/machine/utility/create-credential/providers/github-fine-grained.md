# GitHub fine-grained personal access token

URL template — include every parameter the request pins:

```text
https://github.com/settings/personal-access-tokens/new?name=<name>&description=<description>&target_name=<owner>&expires_in=<days>&<permission>=<read|write>
```

- `<permission>=<read|write>` repeats per permission, named as GitHub's query parameter, e.g.
  `contents=read`, `actions=read`. Source: GitHub docs, "Managing your personal access tokens".
- `target_name` selects the resource owner (user or organization).

Not settable by URL: repository selection. For an organization owner the form has opened with "All
repositories" already selected — verify the checked `install_target` radio, never assume it.

GitHub may demand sudo mode, a password or a 2FA code before showing the form. That step is Tommy's.

After Generate, the value appears once, in an `input` whose value starts `github_pat_` — that prefix
is the delivery validation. The copy button is Tommy's click; an automated click does not reach the
OS clipboard.
