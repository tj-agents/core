# Plugin host integration debt

## Repository skills can be available without core lifecycle hooks

On 2026-10-11, the active native Codex 0.162.1 profile exposed core skills from this repository's
`.codex/skills` adapters, but native `plugin list --json` listed only OpenAI remote plugins. No core
machine package was installed, and the current CLI session had no entry in the machine session registry.
Skill discovery therefore did not establish installation of the machine SessionStart hook required by
`close.py`. The historical startup hook outcome was not recovered; the current installation and missing
registration were directly inspected.

The current profile was repaired with native installation of the three core packages, authenticated
trust for 13 hook definitions, and the shipped session recorder. This establishes the current CLI's
attachment; it does not supply automatic installation or prove fresh-session hook execution.

`codex_marketplace_sync.sync_codex_standards` refreshes already enabled Git plugins and can succeed with
none selected. `handoff-codex` checks that refresh and submits a terminal launch but does not establish
core dependency installation or a registered successor attachment. Installing the merged work plugin
does not itself supply this mechanism: [work PR #1](https://github.com/tj-agents/work/pull/1) merged on
2026-10-10, but its published manifests declare skills without lifecycle hooks, and its
[README](https://github.com/tj-agents/work/blob/main/README.md) delegates repository-local installation
of work, base and machine together to the employer plugin. That procedure does not establish automatic
machine adoption in this core checkout.
The work PR explicitly excluded normal-profile migration and its related rollout from delivery.
[Shared marketplace registration PR #3](https://github.com/tj-agents/marketplace/pull/3) and
[employer integration PR #6](https://github.com/tj-agents/infonetica/pull/6) were still open during this
inspection. Merged producer source did not establish consumer installation or injection.

**Resolution condition.** The owning installation/bootstrap flow resolves and installs the required
core runtime capabilities into the exact launching profile and repository scope. A fresh native session
must demonstrate enabled/trusted lifecycle hooks and a registry receipt bound to its session, host
PID/start time, checkout and terminal. Repository skill discovery and launcher submission remain
insufficient acceptance evidence. Verify dependency adoption for both personal and employer repository
paths on Codex and Claude without silently broadening employer scope.

## Consolidate core packaging and marketplace names as core@agents

Tommy requested on 2026-10-11 that this repository publish one `core@agents` plugin containing its core
capabilities, with consistent identities such as `cpp@agents` for stack owners. The published core
manifests still use the `base-agents` marketplace and separate `base`, `engineering` and `machine`
packages. The [central marketplace](https://github.com/tj-agents/marketplace/blob/main/.claude-plugin/marketplace.json)
is named `tj-agents` and also lists those three packages separately. The inspected Claude profile still
uses `engineering@base-agents` and `cpp@cpp-agents`. Repository names have changed without completing
the requested package and installed-profile identity migration.

**Resolution condition.** Agree the cross-repository migration in `tj-agents/docs`, implement one core
distribution in this repository, and publish the consistent `agents` marketplace. Update generated
manifests, capability catalogs/locks, dependency declarations, bootstrap, launchers, hook trust and
installed-profile migration together. Verify fresh installation and upgrades from the existing names
on both hosts and platforms, preserving canonical authored ownership below `.agents`. Retire the old
identities once migration is proven; this debt record does not authorize changes in other repositories.

## Continuation Stop enforcement still needs installed-host acceptance

Codex and Claude expose Stop events that can keep an unfinished execution active. The shared
continuation gate checks session execution obligations, canonical owners, delivery identity and
registered wakes; source and package tests alone do not establish that a host loaded and trusted it.
An untrusted, disabled or failed-to-launch hook can still be skipped by the host, and arbitrary prose
without an observed execution obligation cannot manufacture execution authority.

Resolve when fresh Codex and Claude sessions in independent personal repositories prove that an
unfinished authorized goal cannot end without verified completion, a genuine typed gate or a matching
registered wake, including repeated Stop events and hook refresh/trust activation. Keep that live
acceptance distinct from source test results.

## Callout enforcement has bounded host signals

The callout-repair gate blocks automatic feedback substitution and checks paired launcher results
against the prepared standards-repair goal. Both host manifests dispatch the gate at Stop.
Callout detection covers explicit mistake wording that names standards or workflow mechanisms;
it cannot establish the meaning of every complaint,
whether a standard caused it, or whether assistant text substantively answers a question. Specialized
host tools can bypass normal plugin hooks. Source
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

## Delivery merge gates have unequal host wiring

The engineering harness and host manifests wire `merge_review_gate.py` and
`persistent_workflow_merge_gate.py` for Claude only. Codex has body-validation and cleanup wiring,
but the manifest contains neither merge gate. This establishes a wiring difference, not a proven
Codex API limitation or installed-host execution. Both hosts can run the shared workflow helpers;
source review and delivery authorization still require their recorded evidence.

Resolver: the existing configurable-auto-merge/delivery owner on `Feature/ConfigurableAutoMerge`,
with the rollout retained by the originating Rust-discovery session. Keep that implementation separate
from the both-host planning/review evidence repair.

Resolve when the delivery owner records each host's supported review/enqueue interception path,
wires and verifies equivalent gates where the host supports them, and documents any observed
API/runtime constraint with the other host's supported outcome. Require fresh trusted-session
Claude and Codex acceptance evidence before claiming installed enforcement parity.

## Host skill entry points are copied by hand

Every skill has a canonical `SKILL.md` and two host entry points under `.codex/skills/` and
`.claude/skills/`. The entry points repeat the canonical name, description, kind and domain and a fixed
reference body. `validate_adapters` in `scripts/sync_plugin_packages.py` fails generation when a copy
drifts, so the copies cannot silently disagree, but an author still writes each one by hand and every
description change touches three files. kit-layout repositories already generate their host skill
directories.

Resolve when generation emits the plain host entry points from the canonical definitions, so only an
entry with a genuine host difference (`extended_host_adapters`) is authored under `.codex/` or `.claude/`,
and `engineering:skill-authoring` no longer tells authors to copy the description.

## Codex Windows sandbox setup fails before shell execution

On 2026-10-10, attempts to read the installed plan-execution and lanes entry points failed with
orchestrator_helper_exit_nonzero and helper_unknown_error: setup refresh had errors before PowerShell
started. The same files read successfully through unsandboxed execution. Tommy explicitly deferred
this host issue while the continuation enforcement repair proceeds; do not conflate it with missing
shared core capabilities.

Resolve separately when sandboxed file reads and repository commands launch without escalation.

## Generation packages skill-local `TECH_DEBT.md` files

Package generation copies every file beside a canonical `SKILL.md` into the canonical package tree and
both host discovery entries, so a skill-local `TECH_DEBT.md` ships three times in each generated package.
`bootstrap-capabilities` does so today. Consumers receive maintainer records, and the `address-debt` survey of
every `TECH_DEBT.md` sees the generated copies beside the authored one. Until this is fixed, an entry owned
by one skill lives in its package's `TECH_DEBT.md` (for example `.agents/engineering/TECH_DEBT.md`).

Resolve when generation excludes `TECH_DEBT.md` from skill-local resources, with a test, and no
`TECH_DEBT.md` appears under `plugins/` after `pwsh .agents/sync-generated.ps1`.
