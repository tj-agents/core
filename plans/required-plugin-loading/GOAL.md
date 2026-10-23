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
