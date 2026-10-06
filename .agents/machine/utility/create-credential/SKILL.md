---
name: create-credential
description: Create a token, API key or other credential in the browser from a pre-filled provider URL and deliver the value to its destination without it touching chat, a file or a command line. Use whenever a task needs a credential that does not exist yet — a missing secret, an auth failure traced to a missing token, or Tommy asking to create or rotate one.

kind: utility
domain: machine
route: infer
---

# Create a credential

Do the whole job: build the provider's pre-filled creation URL, drive the browser through the form,
generate, and deliver the value straight to its destination. Hand nothing back as a blank form or a
manual checklist — Tommy's steps are only the ones the agent must never perform: passwords, 2FA or
sudo codes, and the one copy click that moves the value onto the clipboard.

The value never appears in the transcript, a file or a command line. That constraint shapes every
step below.

## Procedure

1. **Resolve the request.** Provider, credential name, scopes, expiry, destination. Default to least
   privilege and the shortest expiry the use survives; ask Tommy for whatever the task does not pin,
   in one question, not a drip.
2. **Build the pre-filled URL** from the provider's recipe under `providers/` beside this file.
   Every field the URL can carry is in the URL.
3. **Open and verify.** With browser automation available, drive the page through the host entry's
   mechanics: check what it actually selected — radios and pre-selections are verified, not assumed —
   and fill what the URL could not. Without browser automation, open the pre-filled URL in the
   default browser and say so explicitly, then let Tommy drive the page himself. Either way, never
   type a password, 2FA code, sudo code or credential value into the page.
4. **Stop for Tommy's steps.** A password, 2FA or sudo prompt is his: name that one step, wait,
   continue. Never type a password, a code or a credential value into any page.
5. **Generate.** The value shows once.
6. **Deliver by clipboard relay.** Ask Tommy to click the provider's copy button — an automated
   click does not reach the OS clipboard. Then run the delivery script; it reads the clipboard,
   validates the value's shape, pipes it over stdin to the destination, clears the clipboard, and
   prints only non-secret metadata:

   ```powershell
   & '<skill-directory>\scripts\deliver-credential.ps1' -Destination gh-secret -Name '<SECRET_NAME>' -Repo '<owner/repo>' -ExpectedPrefix 'github_pat_'
   ```

   When no clipboard is workable, `-Prompt` is Tommy's to run: tell him to open the script in his own
   interactive terminal with `-Prompt` and paste the value once. The agent never runs `-Prompt` itself —
   it has no stdin to paste into.
7. **Verify at the destination.** The script confirms the secret is listed; anything further is
   proven by using the credential where it was needed, never by echoing it.
8. **Record** name, scopes, expiry and destination — never the value — in the owning plan.

## Providers

One recipe per file under `providers/`: the URL template, what the URL cannot set, where the value
appears, its prefix for validation, and known quirks. Adding a provider is adding one file and one
row here.

| Provider | Recipe |
|---|---|
| GitHub fine-grained PAT | [providers/github-fine-grained.md](providers/github-fine-grained.md) |
| GitHub classic PAT | [providers/github-classic.md](providers/github-classic.md) |

## Destinations

`deliver-credential.ps1` owns delivery; every destination takes the value over stdin or in-process,
never on a command line. Adding one is one switch arm in the script and one row here.

| Destination | Delivers to |
|---|---|
| `gh-secret` | GitHub Actions secret, repository (`-Repo`) or organization (`-Org`, `-Visibility`, and `-SelectedRepos` when `-Visibility selected`). Org secrets do not reach private repositories on GitHub Free. |

A host permission layer may deny the first delivery run as credential handling. That denial is
expected once: retry through the host's own recovery, and do not reroute the value through a more
exposed path to avoid the prompt.

## Boundaries

- Never read the value into the transcript, a file or a command line. If a run has no other path,
  say exactly what would be exposed, proceed only on Tommy's explicit acceptance, and offer
  immediate rotation afterwards.
- Real credentials beyond what the task needs: ask first. Revoke test credentials afterwards.
- `gh` is a prerequisite; a missing `gh` fails the step loudly rather than degrading into manual
  instructions. Browser automation is preferred, not required — its absence falls back to step 3's
  default-browser path, never to a blank form or a manual checklist.
- Clearing the clipboard only removes the live value; Windows clipboard history and cloud clipboard
  sync may still retain the copy. If that matters for a given credential, say so and offer to clear
  history too.
