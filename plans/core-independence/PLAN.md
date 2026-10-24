# Core independence

Rule (AGENTS.md): other packages depend on core; core never names them. Adoption shortcuts and scaffolders
stay with their owners. Each slice moves the knowledge to its owner and deletes it from core in the same
cutover, migrating every caller.

## Done
- core#447 + dotnet#77: plugin-selection roster and `--stack` deleted. Requirements come from the
  tj-agents marketplace catalog's `dependencies` (marketplace#25). Neutral adopt tests and a guard test.

## Remaining (inventory 2026-10-23, file:line on core main)
1. **Publisher trust.** `plugin_selection.py:16` `ALLOWED_OWNERS` and `.agents/hooks/repo-owners.json`
   name Concertable, tomjseery and ThomasSeery. `machine_events.py:17,44,59-60,65` and
   `legacy_marketplaces.py:16` do the same. Decide where approved publishers are declared (candidate: the
   marketplace catalog), then remove the names from core.
2. **.NET knowledge in core hooks.**
   - `project_facts.py` parses MSBuild/npm.
   - `tier.schema.json` and `standards-context.schema.json` enumerate nuget/npm.
   - `red_run_gate.py:53,83-89,145-155,208-210` knows `dotnet test`, the IntegrationTests/E2ETests naming
     and CS/MSB/NU codes.
   - `docs_reachability.py:12,145` special-cases test `.csproj`.

   Each hook needs a declared extension point that the stack's `tier.json` or its own hook fills.
3. **Debug-skill slugs core doesn't ship.** `red_run_gate.py:33-39` and `delivery_runtime.py:9-16`
   hard-code integration-debug and e2e-*-debug. These should be routed from the owning stack's
   declarations.
4. **Profile special cases.**
   - `problem_records.py:17,50-75` maps personal to `personal:work-item`.
   - `plugins/skill-references.json:3-9` allow-lists personal and infonetica skills.
   - Prose in `workflow/resources/problem-records.md`, `self-repair/SKILL.md`, `plans/SKILL.md`
     (Concertable profile) and `README.md`.
5. **Template coupling.** docs-review, docs and skill-authoring require `template:check`.
   `repository-harness.json` and `.claude/settings.json` run `check_skill_references` with template, react
   and dotnet roots.
6. **github-actions coupling.** `machine_events.py:110-120` calls the github-actions plugin's
   `merge_policy.py`.
7. **skill-routes.** `skill-routes/SKILL.md:44-73` documents dotnet/react route kinds for a script that
   doesn't exist.
8. **Prose examples** naming stacks in docstrings and skills. These are D-category and go with the
   slice that touches each file.

Widen `CoreIndependenceTests` to each cleaned area as its slice lands, and to all of `.agents/` at the end.
