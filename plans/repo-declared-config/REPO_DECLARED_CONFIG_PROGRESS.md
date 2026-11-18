# Repo-declared agent configuration — progress

- Plan: `plans/repo-declared-config/REPO_DECLARED_CONFIG_PLAN.md`
- Roadmap: `plans/repo-declared-config/REPO_DECLARED_CONFIG_ROADMAP.md`
- Roadmap item: `repo-declared-config/transitive-core`
- Worktree: not created (successor creates one from `origin/main`)
- Branch: not created
- PR: not opened
- Dependency/package gates: none
- Last reconciled: 2026-09-26 at the Codex handoff
- Status: authorized for execution; handed to Codex.

## Authorization (2026-09-26, Tommy)

Execute this plan. Everything points at core only transitively: a repository declares its
domain marketplace (cpp, react, dotnet, concertable), each of which depends on core, so lanes
and core's agents arrive without the repository naming core. Delete all machine-local agent
settings; they cause the drift. The Concertable plugin loads only in Concertable repositories.
Retire Concertable's duplicate lanes and delivery. Add a guard so this cannot recur. Commit,
push and open PRs per core's conventions. Merging follows each repository's review gate.

## Evidence (2026-09-26, from a Claude session in `cpp/windows/winwrap`)

- `concertable@agents` (source `Concertable/agents`, checkout
  `C:\Users\TommySeery\source\repos\Concertable\agents`) was enabled at user scope in
  `~/.codex/config.toml` and in `~/.claude/settings.json` `enabledPlugins`. The 2026-09-23
  user-scope disable applied to the old ID `concertable@agent-standards`; the reinstall under
  the new ID came back enabled. As a stopgap that session set both entries to `false`; those
  lines are machine-local state to delete, not a fix.
- Its Codex SessionStart hook `plugins/concertable/hooks/codex_delivery.py` (registered in
  `hooks/codex/hooks.json`) copies its stale five-lane `codex-agents/*.toml` into
  `<repo>/.codex/agents/` for any git repository with `.agents/skill-routes.json`. Copies were
  found in `cpp/windows/winwrap` and `cpp/windows/sandbox-hwid` (both deleted), and in
  `Concertable/{agents,b2b,docs}`. Core's own ladder has seven lanes in `~/.codex/agents`.
- With user scope, Concertable's Claude hooks (skill router, merge-review gate) also ran in the
  cpp repositories.
- `cpp/windows/{winwrap,sandbox-hwid}/.codex/config.toml` (tracked) enable/disable individual
  cpp-agents plugins and disable the dead ID `concertable@agent-standards`. Under this plan they
  declare only the cpp marketplace.
- `Concertable/{auth,customer,payment,search}/.claude/settings.json` enable the dead ID
  `concertable@agent-standards`. No Concertable repository has a `.codex/config.toml`.

## Current state (2026-09-23)

- The plan is on `main`, amended with the tj-agents-only source rule and the per-machine
  migration procedure. No implementation branch exists yet.
- This PC (first machine):
  - All four canonical repositories are cloned under
    `C:\Users\tommy\source\repos\tj-agents\{core,cpp,react,dotnet}`.
  - The older `C:\Users\tommy\source\repos\base-agents` checkout is 87 commits behind with
    uncommitted `plan-artifacts` edits and live worktrees; it is not retired.
  - Claude now has `base`, `engineering` and `machine@base-agents` (source `tj-agents/core`)
    at user scope, and `concertable@agent-standards` is disabled at user scope, so Claude's
    lanes and gates come from core. This is an interim user-scope state until phase 4.
  - `~/.claude/settings.json` still has other user-scope plugins, `tomjseery/*` sources for
    `dotagents` and `react-agents`, and `cpp-agents` without `autoUpdate`. Its auto-mode
    environment text names `Concertable/concertable` as the trusted repo for every session;
    that belongs in the Concertable repository's project settings (user decision).
  - `~/.codex/agents` holds the ten shared Codex agents installed by core's engineering
    package (owned via `.base-agents-delivery.json`); Codex cannot load agents from plugins, so
    the plan must decide how this stays repository-declared.
- `sandbox-hwid` (first consumer): routes resolve for Claude and Codex after cpp-agents v0.3.0
  adoption, but through user-scope installs.

## Next Steps

Scope: the whole plan, phases 1–4 and the guard, through delivery.
Current slice: step 1, proving how Claude and Codex resolve a child marketplace's dependency on core.
Remaining scope: steps 2–5 below, then phase 3 self-heal.
Done when: winwrap, sandbox-hwid and every Concertable repository declare only their domain
marketplace; Claude and Codex sessions there get core's lanes, routes and gates transitively; no
user-scope plugin settings, `~/.codex/agents` or repository `.codex/agents` remain; and the guard
fails on any reintroduction.

A separate core worktree, `.worktrees/Fix-Codex-Hook-Activation`, has unrelated uncommitted Codex
hook work. Do not edit or adopt it, and expect overlap in `.agents/plugins/manifests/codex/`.

Owner: Codex (handoff 2026-09-26). Acknowledge here, then work in a fresh worktree from
`origin/main` for each repository you change. This file's and the plan's 2026-09-26 edits are
uncommitted in the `core` main checkout; carry them into your first core PR.

1. **Prove the transitive mechanism first.** Establish, with evidence from the installed Claude
   Code and Codex versions, how a child marketplace depends on core so a repository declaring
   only the child gets core's skills, hooks and agents. This covers Codex agents, which cannot
   load from plugins today. If a harness cannot resolve it, solve it inside core and the child
   marketplaces, never in repositories or machine settings. Record the finding here.
2. Phase 1: inventory `Concertable/agents` `plugins/concertable` against core; port anything
   generic core lacks. Declare the concertable marketplace in each Concertable repository.
   Then delete Concertable's duplicates: `codex-agents/`, `codex_delivery.py` and its hook
   registration, and the duplicate router and gates.
3. Phase 2 generator. Regenerate `cpp/windows/{winwrap,sandbox-hwid}` and the Concertable
   repositories to declare only their domain marketplace.
4. Phase 4 machine cleanup, only after 1–3 work. Back up `~/.claude/settings.json` and
   `~/.codex/config.toml`, then delete user-scope `enabledPlugins`/`extraKnownMarketplaces`,
   the Codex plugin/marketplace tables, `~/.codex/agents` and `~/.codex/skills`, and any stray
   `<repo>/.codex/agents`. Verify a Claude and a Codex session in `cpp/windows/winwrap` and in
   one Concertable repository still get lanes and routes.
5. Guard: ship the read-only verifier (design item 4). Add a core test that fails if any plugin
   writes agent files into a repository or if user-scope plugin enablement exists.

Phase 3 (self-heal) follows as planned.
