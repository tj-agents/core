# Plugin host integration debt

## Arbitrary terminal prose is outside the completion runtime

The completion runtime validates supported workflow receipts and the terminal reports those workflows
produce. Codex and Claude provide no package hook that intercepts arbitrary final prose, so a session can
still type an unsupported completion claim outside that path.

Resolve when both hosts expose a trusted terminal-response interception point that can require the canonical
completion check before a user-visible success claim. Until then, do not claim installed-host adoption from
source tests alone.

## Callout enforcement has bounded host signals

The callout-repair gate blocks automatic feedback substitution and checks paired launcher results
against the prepared standards-repair goal. Claude's Stop hook also holds recognized callouts.
Callout detection covers explicit mistake wording that names standards or workflow mechanisms;
it cannot establish the meaning of every complaint,
whether a standard caused it, or whether assistant text substantively answers a question. Codex has no
registered result or Stop hook, and specialized host tools can bypass normal plugin hooks. Source
regressions and packaging checks do not establish live activation or interception of SendFeedback.

Resolve when both hosts expose trusted semantic callout and answer signals, successful source-owner
handoff evidence, and complete feedback/terminal interception; verify those paths in fresh sessions
with the released hooks trusted. Until then, report the supported boundaries without claiming complete
enforcement of arbitrary prose.

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

## Codex hooks still launch one or two interpreters per gate

Claude hooks use exec form and one dispatcher per plugin and event, because each Git Bash launch on
Windows stalled 15 to 57 seconds under concurrent spawning while direct launches stayed under 10.
Codex manifests are unchanged. Each Codex gate is its own hook, and on Windows
`pre_tool_use_adapter.py` starts a second interpreter for every gate, so one shell call costs up to
two interpreters per gate. How Codex launches `commandWindows` is unmeasured.

Resolve when Codex `PreToolUse` gates run through `hook_dispatch.py`, with the adapter's exit-code
translation applied once to the merged result, and a timing probe of Codex's Windows hook launch
path is recorded.

## The prompt route fires on host-generated turns

On 2026-10-01 the installed UserPromptSubmit `workflow_route.py` attached the full plan-execution
contract (12 KB) to subagent hand-backs and task notifications. Claude delivers those as prompts, and
their text often contains "complete" or "finish". Every background agent result therefore re-injects
the route, whether or not the human authorized execution.

Resolve when a live probe records the UserPromptSubmit payload for an agent hand-back and a task
notification, and the route skips any prompt the payload or transcript marks as non-human, with a
regression test for each.

## Catalog digest guard keys entries by package id alone

`scripts/check_generated_paths.py` compares catalog digests between the merge base and the PR by
package id. If one id appeared in two releases, only the last release's digest would be compared, so a
committed digest change in an earlier release would pass. The catalog currently holds one release.

Resolve when the guard keys each digest by release id and package id, with a test covering two releases
that share a package id.

## Codex hook commands need an inline loader authenticator

`bind_codex_hook_snapshots` embeds a small readable Python bootstrap in each Codex hook command. It reads
the packaged loader, or its retained snapshot when the cache has gone, normalizes newlines, verifies the
loader SHA-256 embedded in the command, stages those bytes in a private temporary file, then calls it with
`runpy`. The authenticated command is still necessary: invoking a packaged loader directly would execute a
mutable file before any package or snapshot integrity check can run.

This narrows the mutable-loader race to bytes checked and staged by the bootstrap; it does not protect
against a same-user attacker who can replace Python, the temporary directory, or the process itself. The
package loader continues to verify the complete selected snapshot before it dispatches a hook. Generation
still enforces cmd.exe's 8191-character command limit, but command length no longer grows with loader size.

## The `docs-and-debt` compatibility entry outlives its split

`engineering:docs-and-debt` was split into `guidance-ownership`, `debt-records` and `working-docs`.
Releases through `v2.1.15` publish the old name, and the `skills` alias table maps one name to one
name, so it cannot redirect a split. The old name therefore ships as a routing-only compatibility entry,
with `base:docs-and-debt` still aliased to it.

Resolve after 2027-04-09: delete the compatibility entry's canonical and host files and its
`base:docs-and-debt` alias, then confirm `grep -rniE "docs-and-debt"` over authored sources finds only
historical plans and reviews.
