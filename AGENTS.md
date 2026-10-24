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

<!-- BEGIN personal:current-solution sha256:2e091b5f18f67fb2302024e817c71d4a0f5234c1ca63ca1c9af5c4eef3b6a128 -->
# Personal projects

These rules are mandatory in projects that explicitly adopt `personal@tj-agents`. Adoption records the
project's personal scope; a home directory, author name or employer association never establishes it.
Employer projects remain outside this profile unless Tommy explicitly changes that scope.

Keep one current supported solution. When replacing behavior, remove the superseded names, aliases,
fallback implementations, adapters, configuration formats and compatibility branches. Coordinate and
migrate all known callers, project declarations, installed registrations, generated artifacts and live
runtime entry points in the same cutover. Do not retain obsolete behavior for hypothetical external users;
coordinate upgrades with the actual collaborating developers.

Verify the entry points people actually use on every supported platform, including Windows and Linux
launch paths where supported. Source edits, successful generation, passing unit tests and version commands
alone do not prove that a migration is complete. Check installed bindings and fresh runtime behavior.
Record any unverified entry point as incomplete, with its resolver and observable acceptance condition.

For example, replacing `old-launch` with `launch` means migrating the registered shell command, project
configuration and actual callers, deleting the old entry, then invoking `launch` from a fresh session on
each supported OS. Running `launch --version` alone leaves the cutover unverified.

```text
Replace old-launch with launch:
1. Migrate the registered shell command, configuration and actual callers.
2. Delete the old entry and regenerate installed settings.
3. Invoke launch from a fresh supported Windows/Linux session and check its actual behavior.
Result: launch --version alone leaves this migration incomplete.
```

Do not independently add a backwards-compatibility exception. Surface an explicit contrary user requirement
as a deliberate policy decision, identify the affected supported behavior and reconcile this profile's
scope before implementing it. Never hide an exception in a fallback or adapter.

Solve the demonstrated problem with the smallest suitable implementation. Add abstractions, dependencies,
configuration switches, duplicate paths or process machinery only for a concrete current need. Prefer the
capabilities the project already selects. Verify the behavior and meaningful failure paths in proportion
to the change; do not add tests that merely repeat the implementation or a checklist with no concrete benefit.

This policy is authored once here. Personal adoption generates its marked native instruction block from
this body and checks it for drift. A selected plugin or an `always` tier alone is not proof of loading.
<!-- END personal:current-solution -->
