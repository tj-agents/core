# core

Read `README.md` before changing repository structure.
Personal applies only to explicitly adopted personal projects. GitHub ownership and permission to commit
agent configuration do not establish personal scope. Infonetica is work scope, including the
`tj-agents/infonetica` plugin source repository and every worktree: never select or inject Personal there.
Read the target repository's README.md and AGENTS.md before selecting its policy profiles.
Read [`CODE_CONVENTIONS.md`](CODE_CONVENTIONS.md) before changing runtime scripts, hooks, or launchers.
Install machine state only through `./setup.ps1` or `./setup.sh`; rerunning converges.
Shipped code must run on Windows and Linux; follow
[Supported platforms](CODE_CONVENTIONS.md#supported-platforms).

Machine setup and standards injection are reproducible Core deliverables. Implement their behavior in
repository-owned code reached through the setup and sync entry points, with shared Python logic for
Windows and Linux. A repair confined to one machine's profile, plugin cache or local settings is
incomplete: carry it into source, then deploy it through those entry points. Verify effective native-host
standards discovery and the affected behavior in a fresh session on each supported platform; report
missing prerequisites or remaining verification explicitly. Keep credentials and native trust decisions
under their existing controls. See [Machine setup and updates](README.md#machine-setup-and-updates).

```text
One laptop is missing Engineering after setup:
1. Repair the repository-owned selection, installation or injection path that caused the omission.
2. Run setup and sync through their supported entry points on Windows and Linux.
3. Verify Engineering discovery and the affected operation in fresh native host sessions.
Result: copying a cached skill onto that laptop alone does not complete the repair.
```

Global design and cross-repository plans belong in [`tj-agents/docs`](https://github.com/tj-agents/docs).
Keep core implementation plans here and link to shared designs instead of copying them.

`.agents/` is the only canonical home for host-neutral capability definitions, workflow contracts,
shared hooks, schemas, tests and resources. Logical Base, Agent Store, Engineering and Machine ownership lives below
that directory; it must not be recreated as authored top-level source trees.

`.codex/` contains Codex-only entry points, adapters, agent definitions and configuration. `.claude/`
contains Claude-only equivalents. Authored host manifests and hook wiring live under
`.agents/plugins/manifests/` and are mapped explicitly by `.agents/plugins/sources.json`. A host entry
point references its canonical definition in `.agents/` and adds only genuine host differences; never
copy a shared instruction body into either host tree as another authored source.

`plugins/*` is generated distribution output, never an authored source tree, and never part of a PR:
CI's guard rejects generated paths and the post-merge job regenerates and commits them on main. Run
`pwsh .agents/sync-generated.ps1` locally only to refresh the tree for tests, and leave its output
uncommitted. See [`SOURCE_LAYOUT.md`](SOURCE_LAYOUT.md).

Read [`engineering:skill-authoring`](.agents/engineering/convention/skill-authoring/SKILL.md) before
deciding to create, split, merge, rename or retire a skill, including while planning one.

A utility skill must not depend on a manually assembled, machine-local file the plugin does not ship.
See [`PACKAGING.md`](PACKAGING.md).

For machine setup, event handling or repository adoption, read the
[refresh and repository boundaries](README.md#refresh-and-repository-boundaries) before changing them.
Preserve the separation with the [machine event fixtures](tests/test_machine_events.py); repository
adoption and local exclusions follow [machine:plugin-selection](.agents/machine/utility/plugin-selection/SKILL.md).
Consumer validation and native refresh share `.agents/machine/scripts/plugin_autoupdate.py`.
Follow the [shared catalog's identity policy](https://github.com/tj-agents/marketplace#readme)
when changing marketplace declarations or installed-registration cleanup.

This repository owns common agent behavior, selected engineering process and machine utilities.
`plan-artifacts` supplies maintained plans without requiring an engineering lifecycle. Stack standards,
product profiles and product-specific enforcement remain with their scope owners. Shared runtime recovery
and host acceptance remain part of P2; source generation alone does not establish adoption.

<!-- BEGIN personal:rules sha256:f878befe2d5e1e69bc6e5cc2ed10c6e684ce894987ff4a9861c7cc2b802fe802 -->
# Personal rules

These rules govern every project that explicitly adopts `personal@tj-agents`. Adoption records the
project's personal scope; a home directory, author name or employer association never establishes it, and
employer projects stay outside this profile unless the user explicitly extends that scope. Before planning
or starting work, confirm the task is clear against each rule below.

## 1. Clean cut

Keep one current supported solution. When replacing behavior, remove the superseded names, aliases,
fallback implementations, adapters, configuration formats, compatibility branches and forwarding or
migration docs. Migrate all known callers, project declarations, installed registrations, generated
artifacts and live runtime entry points in the same cutover, and coordinate upgrades with the actual
collaborating developers. A commit that removes or renames a skill while a tracked source still names its
old `<package>:<name>` is blocked until every reference is migrated or deleted.

Verify the entry points people actually use on every supported platform, including Windows and Linux
launch paths where supported. Source edits, successful generation, passing unit tests and version commands
alone leave a migration unproven; check installed bindings and fresh runtime behavior. Record any
unverified entry point as incomplete, with its resolver and observable acceptance condition.

```text
Replace old-launch with launch:
1. Migrate the registered shell command, configuration and actual callers.
2. Delete the old entry and regenerate installed settings.
3. Invoke launch from a fresh supported Windows/Linux session and check its actual behavior.
Result: launch --version alone leaves this migration incomplete.
```

A backwards-compatibility exception exists only as an explicit user requirement. Surface it as a
deliberate policy decision, identify the affected supported behavior and reconcile this profile's scope
before implementing it, keeping the exception visible rather than inside a fallback or adapter.

## 2. Proportionate implementation

Solve the demonstrated problem with the smallest suitable implementation. Add abstractions, dependencies,
configuration switches, duplicate paths or process machinery only for a concrete current need. Prefer the
capabilities the project already selects. Verify the behavior and meaningful failure paths in proportion
to the change, with tests that prove behavior rather than restate the implementation.

## 3. Plans

Track work as a GitHub issue or project item. A plan committed under `plans/` is only the detailed
implementation plan behind one such item and links to it; working plans stay machine-local.

This policy is authored once here. A selecting project receives it at SessionStart, and adoption generates
its marked native instruction block from this body and checks it for drift. A selected plugin or an
`always` tier alone is not proof of loading.
<!-- END personal:rules -->
