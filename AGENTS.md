# core

Core authors and publishes only the `base`, `workflow`, `engineering` and `docs` plugins. Behavior that acts on an
agent session belongs in `tj-agents/agent`, deterministic CLI and OS mechanics in `tj-agents/cli`, plugin
generation and checks in `tj-agents/template`, and stack standards in their stack repository. Never author,
copy or refactor another repository's package here; the generator rejects a scope the marketplace publishes
from elsewhere. Agent code reaches Core only as the staged, git-ignored `.agents/dependencies/` export.

Read `README.md` before changing repository structure.
Personal applies only to explicitly adopted personal projects. GitHub ownership and permission to commit
agent configuration do not establish personal scope. Infonetica is work scope, including the
`tj-agents/infonetica` plugin source repository and every worktree: never select or inject Personal there.
Read the target repository's README.md and AGENTS.md before selecting its policy profiles.
Read [`CODE_CONVENTIONS.md`](CODE_CONVENTIONS.md) before changing runtime scripts or hooks.
Shipped code must run on Windows and Linux; follow
[Supported platforms](CODE_CONVENTIONS.md#supported-platforms).

Marketplace owns plugin identities, source repositories and dependencies. Follow the
[shared ownership decision](https://github.com/tj-agents/docs/blob/main/PLUGINS.md) when changing
selection.

Current architecture and cross-repository reference documentation belong in
[`tj-agents/docs`](https://github.com/tj-agents/docs); follow its `AGENTS.md` for scope.
Keep Core's proposals, implementation plans and audit evidence with the owning source work or its PR.

```text
Implemented cross-repository ownership -> update the existing Docs reference.
Core capability audit and CI results -> retain with Core's source work or PR.
```

`.agents/` holds only host-neutral shared source: Base, Engineering, Workflow and Docs definitions, workflow
contracts, shared hooks, schemas, tests and resources. `.codex/` holds Codex-only entry points, adapters,
agent definitions and configuration; `.claude/` holds the Claude-only equivalents. A host entry point
references its canonical definition in `.agents/` and adds only genuine host differences; never copy a shared
instruction body into either host tree.

`plugins/*` is generated distribution output, never an authored source tree, and never part of a PR:
CI's guard rejects generated paths and the post-merge job regenerates and commits them on main. Run
`pwsh .agents/sync-generated.ps1` locally only to refresh the tree for tests, and leave its output
uncommitted. See [`SOURCE_LAYOUT.md`](SOURCE_LAYOUT.md).

Read [`engineering:skill-authoring`](.agents/engineering/convention/skill-authoring/SKILL.md) before
deciding to create, split, merge, rename or retire a skill, including while planning one.

A utility skill must not depend on a manually assembled, machine-local file the plugin does not ship.
See [`PACKAGING.md`](PACKAGING.md).

<!-- BEGIN personal:rules sha256:eee7a719bb90e67aaa81ac101a45836dd099bc745fee61216c99ec7d6075f12d -->
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
collaborating developers. Run each migration once during the cutover and delete it; never ship migration
or cleanup code that runs again later. CI fails a commit that removes or renames a skill while a tracked source
still names its old `<package>:<name>`.

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
