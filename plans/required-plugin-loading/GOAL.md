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

Review and publish the tested source candidate, complete Linux CI, then install through
the supported setup/update path and verify fresh native hosts. Publication currently
requires resolving the Personal bot-identity policy: its supported wrapper reports
zero App records on this machine. Do not substitute Tommy's credentials silently.

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
