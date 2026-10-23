# Required plugin loading

## Authorized outcome

Repair selected-standard loading generically for every tj-agents plugin and consumer,
on Codex and Claude, rather than adding a Python-specific workaround. User explicitly
authorized permanent shared-source repair and machine/repository activation repair.
Keep unrelated Car Hunter feature commits and the dirty primary Core checkout intact.

## Evidence and current owner

- Originating repo selects `python@python-agents` in `.agents/plugins.json` and both
  generated host settings. Codex's running catalog omitted it.
- Actual `codex plugin list --json` for the repo reports that the `python-agents`
  marketplace snapshot has no supported manifest. Presence in Claude's cache does
  not prove Codex activation.
- Older installed launchers explicitly continue without standards on preparation
  failure. Current Core main preserves non-blocking update checks and separately
  needs required-selection admission enforcement; optional update availability must
  remain separate from required installed standards.
- The current router derives routes from available plugins, without first proving
  every repository-selected plugin is installed for the active host. An absent
  plugin can therefore also omit its own routes.
- Existing selection adoption and native inventory tools provide the reusable
  pieces. Extend those, not a parallel Python installation path.

Owner: current Codex session. Source worktree:
`C:/Users/tommy/source/repos/marketplace-car-hunter/.local/core-required-plugin-loading`.
Branch: `Fix/RequiredPluginLoading`; base `40c5ef88` on fresh `origin/main`.
The host exposes no native directory-retarget command; its attachment remains the
originating project. No claim is made that per-command source paths retarget it.

## Delivery and verification

One focused source slice: verify required selections against active-host native
inventory before routed writes and launches, share the check across hosts, preserve
read-only diagnosis, and test arbitrary plugin/marketplace identities and missing,
disabled, broken, wrong-project and valid installations. Update packaging for the
shared runtime. Do not block solely on offline optional update polling.

Then correct demonstrated legacy selections through the supported adoption mechanism,
audit the machine's selected consumer repositories, and use supported setup/update
entry points. Verify fresh-host catalogs separately from source tests. Publish the
eligible personal tooling repair through its repository gates; report Windows,
Linux, Codex and Claude verification separately and retain any unresolved gate.

## Next action

Finish Windows exact-head CI for PR #445 at `53b8649eb51e73d29ace697a67fc0be64c43bbbf`;
Linux and full/incremental source review pass, with no open findings. Then resolve the
remaining landing identity gate and supported machine deployment. The machine has no
GitHub App record; Tommy explicitly granted his login exception for push and PR only.
A clean persistent installer clone is prepared at `C:/Users/tommy/.agents-state/sources/core`;
its supported read-only setup check is running. No machine settings have been applied.
The unrelated dirty development checkout remains intact.

## Implementation checkpoint

Implemented shared required-selection verification for arbitrary plugin/publisher
identities, native-host scope and enabled state, readable installed payloads, bounded
inventory failure, nested repositories, and explicit directory overrides. Shell and
handoff startup refuse missing requirements; diagnostic/install commands remain
available. The write router verifies selections before discovering routes, preventing
an absent plugin from erasing its own gate. Runtime resources ship from one source.
Optional offline update polling remains non-blocking after required admission passes.

Adoption migrates known plugins from individual tj-agents publisher marketplaces to
the canonical marketplace in the selection and both host files together, preserving
foreign publishers and explicit profiles. Audited all 30 registered consumer repos;
only Car Hunter used a retired publisher. Migrated it through preview/write/check.
Native Codex inventory now contains Python, and the newly declared Agent Store and
Workflow dependencies were installed through native `plugin add`.

Windows checks passed: required-plugin tests (9), router (53), adoption (17), handoff
startup (13; one POSIX-only skip), shell launch/profile tests (16; one POSIX-only
skip), setup (47), machine events (26), launch budget (3), source/package layout (25).
Generation, harness validation and tier-payload validation passed. Generated package
files and catalog digests remain uncommitted per current Core instructions.

No source change is claimed published or installed machine-wide yet. The originating
running session cannot retroactively acquire a new native catalog. Fresh-host
activation, shared launcher deployment, Linux acceptance and broader installed-host
verification remain required; source tests and native inventory are distinct evidence.

## Native activation checkpoint

Car Hunter migration committed locally as `e8c80a7`; product changes remain unpublished.
Actual required-selection admission passes for both Codex (25 enabled roots, all seven
required identities present) and Claude (seven enabled roots). A fresh ephemeral Codex
session listed `python:style`, `python:testing`, `workflow:run`, `agent-store:inspect`
and read the canonical Python style definition successfully. Evidence is retained in
the originating project's `.local/fresh-codex-standards-proof.log` and `.txt`.
One admission attempt timed out under concurrent refresh/review load; it correctly
refused admission, and subsequent native inventory took 1.93 seconds and passed.

Claude's supported refresh installed/updated the seven required plugins but reported
legacy registrations for C++, .NET and React still referenced elsewhere; it refused
to remove those registrations. Do not conflate current-project admission with global
retirement of those registrations. Shared source review remains in progress. Requested
an explicit one-time publishing identity exception; no answer means no authorization.

## Review corrections

Native review of `43620f9f` found two actionable P2 gaps: cache directories alone
did not prove readable host manifests/payloads, and global CLI options could prevent
maintenance-command recovery. Both are corrected with regression coverage (11 required
plugin tests now pass). Directory overrides are parsed only before the command, so
prompt arguments cannot change the checked project. Repeated inventory timeouts under
load justified raising the bounded native admission budget from three to five seconds,
still below the seven-second dispatch deadline.

The updater suite exposed a synthetic recovery test inheriting the running session's
snapshot and real home/plugin roots. Its subprocess now uses a disposable home,
project and plugin roots and its own preserved snapshot; all 43 updater tests pass.
Actual Codex and Claude admission passes with host manifest/payload validation enabled.
No shared runtime has been deployed yet.

## Publication checkpoint

Published and verified head `457ad350c49ffd02760b7f19443628d3d6a38556` at
https://github.com/tj-agents/core/pull/445 (draft). Body validation passed and delivery
binding records this exact identity. Windows and Linux CI run `39986038049` is active;
the generated-output guard and guidance checks passed. Native follow-up review is
active. Router recheck passed 52 cases with one 20-second fixture timeout; that exact
case passed unchanged on focused rerun. Do not call the full rerun green.

The publication exception does not install a GitHub App or change the standing
identity policy. App-policy-compliant merge, shared rollout, supported machine
installation and fresh launcher failure/success checks remain open.

Follow-up native review found two further admission gaps: an unknown global flag
could stop directory resolution before `--cd`, and malformed non-list declarations
were skipped. Directory scanning now continues across native options and subcommands,
stops at the explicit `--` delimiter, and never interprets a later positional word as
a maintenance command. Known option values cannot become maintenance commands.
Malformed skills/agents/commands declarations are rejected; valid inline hook objects
remain supported. All 12 required-plugin tests and 13 startup tests pass (one POSIX
skip). The correction is substantive and will refresh the existing PR head and CI.

CI run `39986038049` exposed fixture-only regressions: red-run and duplicate-router
fixtures copied the router without its new verifier dependency, and Windows short
temporary paths differed from the runtime's resolved paths. Fixtures now include the
shipped helper and normalize their temporary root. Red-run tests pass (12), hook
runtime tests pass (20; one platform skip). The final native review also found
Claude's optional worktree name could look like a maintenance subcommand. Boolean
global flags are now classified only for Codex; Claude optional argument forms stay
subject to admission. All 13 required-plugin and 13 startup tests pass (one POSIX skip).

Final delta review found help/version after Claude global options needed an independent
diagnostic bypass. Native diagnostic flags now bypass admission before maintenance
subcommand classification, but only outside `--` and outside consumed option values.
All 14 required-plugin tests, 13 startup tests and 16 launcher tests pass (the latter
two each have one POSIX skip). Existing agent-mode optional-value cases stay blocked.

The Linux full runtime suite reached 1,196 tests with one failure: the migration
regression's expected plugin list implicitly depended on the generated roster.
CI's sibling publisher checkouts enrich that roster with real Python/React
dependencies, while the workstation's isolated source tree does not. The migration
test now supplies an explicit two-plugin roster, isolating the behavior it asserts;
all 17 adoption tests pass. Production dependency expansion remains unchanged.

The diagnostic delta passed native review. A parent audit against both installed
CLIs found shared maintenance words could be ordinary prompts on the other host.
Maintenance exemptions now use separate native command sets; cross-host words such
as Claude `features` and Codex `plugins` require admission. All 15 required-plugin
tests and 13 startup tests pass (one POSIX skip). This is the final runtime correction
identified by the current audit; exact-head CI and rollout remain open.

## Complete-candidate review checkpoint

Integrated current main through merge `c24d6fa86fca5e920b5cf14b349c6074609941c2`,
preserving the unrelated dirty primary checkout. Frozen review descriptor and bundle
were generated against base `3f109a3e1ea9470ea7e68b6e7b82df0cb8637dd3`;
the full native review ran in a clean detached checkout. Canonical work order and
private receipt record a completed changes-requested pass with R1 (attached `-C`)
and R2 (effective launch configuration). The packaged review-lens model was unavailable;
one fresh default read-only workflow specialist supplied the independent check.

Both findings are corrected in source. Attached short option values retain native
directory/config boundaries. Claude receives settings, setting sources and plugin
paths in inventory. Actual native probes proved Codex ignores disabling activation
overrides in plugin inventory, so the supported guard refuses unverifiable Codex
profile, feature and non-model config overrides in selected repositories; bounded
model/reasoning overrides and maintenance diagnostics remain available. The same
real verifier is exercised through shell and handoff admission tests. Required-plugin
tests pass (19), startup (14; one POSIX skip), launcher (17; one POSIX skip).
Source remediation still needs an incremental frozen review and exact-head CI.

Incremental review of `20a54197d61859dc2a46d3eed43c071370b14241` confirmed the
two fixes and found R3: native inventory cwd had been normalized to the selection
root, changing the meaning of relative Claude settings/plugin paths. Preserve the
actual launch directory for native inventory and registration scope, while selecting
required identities at the repository root. The new regression passes, including a
subdirectory-scoped install. A real Claude CLI probe from a subdirectory with a
relative disabling settings file now refuses admission. Required-plugin tests20,
startup14 and shell17 pass (one POSIX skip in each latter suite). Full review history
and dispositions are retained in the canonical Git-private work order and receipts.

## Supported installation scope

The standalone managed source clone is prepared at
`C:/Users/tommy/.agents-state/sources/core`, preserving the dirty development
checkout. Its full read-only setup check demonstrated drift in unrelated remote
event/publisher and merge-policy settings across many repositories, as well as the
required runtime and shell bindings. Applying the whole installer would exceed this
repair's current publication identity exception and mix unrelated machine changes.

The supported setup entry now accepts repeated `--step` names, preserves declared
order and required preconditions, and leaves default full-setup behavior unchanged.
It can therefore install the admission runtime and shell bindings without checking
or applying unrelated publisher settings. Tests exercise that boundary through the
real CLI entry point, including unknown-step rejection. All 50 setup tests pass.
Frozen incremental review found R4: profiles selected alone could omit their runtime.
The correction automatically includes the runtime for shell profiles, preserves order,
and adds the isolated selection to the CLI regression. All 50 setup tests pass.
The supported Windows profiles-only scoped preflight applied no settings and
automatically included the runtime. Final exact-head native and independent review
approved8503ed96, with R4 resolved and all50 setup tests passing. Linux CI passed;
Windows shared-runtime CI is still running. Both Windows and Linux CI passed the earlier
53b8649e guard candidate.

Handoff launchers resolve agent_cli from packaged machine resources, which contain
startup_binding, launch_status and required_plugins together. The installed shell
runtime uses launch_check directly. The package mapping ships the complete scripts
directory; startup_binding is not required in the shell-only runtime file set.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/machine/scripts/required_plugins.py",
  "hosts": [
    {"host":"claude","behavior":"Require selected native standards before agent work.","source":".agents/machine/scripts/required_plugins.py","mapping":".agents/plugins/sources.json and plugin_autoupdate.RUNTIME","verification":{"level":"source","result":"passed","evidence":"Shared admission, shell and handoff tests pass; native settings override probe refuses disabled requirements. Shared installed launcher deployment remains open."}},
    {"host":"codex","behavior":"Require selected native standards before agent work.","source":".agents/machine/scripts/required_plugins.py","mapping":".agents/plugins/sources.json and plugin_autoupdate.RUNTIME","verification":{"level":"source","result":"passed","evidence":"Shared admission, shell and handoff tests pass; native override limitation is guarded explicitly. Fresh consumer catalog and standards read passed. Shared installed launcher deployment remains open."}}
  ]
}
```

```completion
{
  "outcome": "Every repository-selected standards plugin is verified for its native host, and missing imports cannot silently permit agent startup or routed writes.",
  "acceptance": [
    {
      "id": "consumer-activation",
      "criterion": "Car Hunter uses canonical plugin selections and a fresh Codex session can read its Python standards.",
      "evidence": [{"source": "Car Hunter commit e8c80a7 and .local/fresh-codex-standards-proof.log", "result": "Both native inventories pass all seven requirements; fresh Codex lists Python, Workflow and Agent Store skills and reads Python style."}],
      "owner": "current execution session",
      "next_action": "Preserve the verified migration."
    },
    {
      "id": "shared-rollout",
      "criterion": "The shared guard passes Windows and Linux CI, lands and is installed through supported setup, with fresh launcher success and missing-plugin failure verified.",
      "evidence": [],
      "owner": "current execution session; GitHub App identity setup owned by Tommy",
      "next_action": "Complete PR 445 validation, resolve policy-compliant landing and preserve unrelated primary-checkout edits during supported installation."
    }
  ],
  "deliveries": [{"repository": "tj-agents/core", "pr": 445, "head": "8503ed9682259beac1b6a769bc00e809fe4757aa"}],
  "open_tasks": [
    {"repository": "tj-agents/core", "pr": 445, "head": "8503ed9682259beac1b6a769bc00e809fe4757aa", "text": "Complete Windows exact-head CI.", "owner": "current execution session", "next_action": "Final source review and Linux CI passed; observe run39997465752 for Windows completion. Earlier guard CI passed both platforms."},
    {"repository": "tj-agents/core", "pr": 445, "head": "8503ed9682259beac1b6a769bc00e809fe4757aa", "text": "Land and deploy the shared runtime through supported machine setup.", "owner": "current execution session; GitHub App setup owned by Tommy", "next_action": "Await the pending explicit landing identity exception (existing exception covers push/PR only), land after all checks pass, then run supported setup from the prepared managed clone and verify fresh hosts. No settings have been applied."}
  ]
}
```


## Launcher integration after main moved

Tommy explicitly authorized review and merge, including the existing-login identity
exception for this repair's merge, and accepted existing hook integration provided
core remains generic. Required plugin names come from repository selection, with
no hard-coded Python, .NET or React inventory in the shared verifier.

Candidate8503ed96 passed complete Windows and Linux CI. Main then landed PR446,
which scopes optional refresh by launch host and preserves running Codex sessions.
Conflict resolution retains that scoping/environment cleanup together with required
plugin admission, argument forwarding and refusal on verifier failure. Focused
launcher18 (one POSIX skip), required20, startup14 (one POSIX skip), setup50,
updater46 and reload34 tests pass. The first sandbox launcher run could not start
pwsh; the unchanged suite passed under normal machine execution. New exact-head
review and CI are required before landing. Machine installation remains outstanding.
