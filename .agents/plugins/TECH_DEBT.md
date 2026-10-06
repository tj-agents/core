# Plugin host integration debt

## Generated base tier README points to an absent schema path

The source `.agents/tiers/README.md` links to `../schemas/tier.schema.json`, which exists in the source tree. Packaging moves the schema to `plugins/base/tiers/tier.schema.json` but copies the README without adjusting its link. The generated README therefore fails `docs_reachability.py` on the current main branch.

Resolve when the packaged README links to its shipped schema while the source README still resolves locally, and the documentation reachability check passes on the generated tree.

## Codex cannot guarantee a fail-closed write boundary through plugin hooks

Codex dispatches a tool call when its `PreToolUse` hook process fails or is skipped. PowerShell translated a child router's exit code 2 into hook exit code 1, so live writes continued even though the router printed a denial. The packaged Windows adapter now returns a JSON deny with exit code 0 and denies child failures. Fresh normal-profile Codex and Claude probes blocked a missing-marketplace write after the released hooks were active.

Codex plugin installation and updates do not trust new or changed hook definitions. A fresh v2.1.11 session wrote the disposable probe file while 13 definitions awaited review; `/hooks` trust review activated them and the repeat probe was blocked. The adapter itself can still fail to start, an untrusted or disabled hook can be skipped, and some specialized tools opt out of normal hooks. Marketplace code cannot make those host paths fail closed.

Resolve when Codex provides trusted, fail-closed host policy for every local write path, including hook launch failures, changed definitions and specialized tools. Bind the shared router to that policy and require a fresh-session missing-marketplace write probe as a release gate. Until then, verify live activation after every release that changes a hook definition.

Upstream behavior: https://learn.chatgpt.com/docs/hooks#review-and-trust-hooks and https://github.com/openai/codex/issues/41979.

## Routed skill recovery needs a host delivery proof

The router still blocks a routed write when its owning skill is absent or has no successful load
proof. Codex documents model-visible `PreToolUse` `additionalContext`, but does not specify whether
it is delivered together with a `deny` decision. An isolated CLI probe was stopped by local process
policy before its test hook ran, so it did not establish that combined behavior. The router must not
mark an injected skill as loaded on an unobserved denial or let the pending write run first.

Resolve when a trusted live Codex probe proves that a denied write delivers the complete skill body
and the next invocation can verify that delivery from the session transcript or an equivalent host
acknowledgment. Then add pinned-release install repair for genuinely absent skills and repeat the
missing-marketplace write probe without a restart.

## Catalog digest guard keys entries by package id alone

`scripts/check_generated_paths.py` compares catalog digests between the merge base and the PR by
package id. If one id appeared in two releases, only the last release's digest would be compared, so a
committed digest change in an earlier release would pass. The catalog currently holds one release.

Resolve when the guard keys each digest by release id and package id, with a test covering two releases
that share a package id.

## Launcher terminal detection trusts inherited environment variables

`agent_cli.launch_tab` picks the terminal from `TMUX`, `KITTY_WINDOW_ID` and `KONSOLE_DBUS_WINDOW`.
A GUI program started from a terminal inherits them, so a launcher run inside, for example, VS Code
started from Konsole opens its tab in that Konsole window, or fails if the window has closed.

Resolve when detection confirms the variable belongs to the terminal the caller is attached to, for
example by matching the terminal's own record of its sessions against the caller's process ancestry,
with a test for an inherited variable.
