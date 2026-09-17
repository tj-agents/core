# base-agents

The generic engineering **method** — every repo Tommy owns, naming no product and no stack. Branching,
committing, opening a PR and landing it through a queue, plans and roadmaps and progress ledgers,
handoffs, reviews and addressing what they find, docs and tech debt, worktrees, and driving a red suite
to green tier by tier. It ships the write-time hook that makes a standard fire, so it is the plugin every
repo installs regardless of what it is written in.

The stack halves pair with it: `tomjseery/dotagents` (.NET), `tomjseery/react-agents` (React/TS).
Anything Concertable-specific lives in `Concertable/agent-standards`, which installs this alongside its
own two plugins rather than shipping the method itself.

**How this is authored and delivered — read
[`dotagents/ARCHITECTURE.md`](https://github.com/tomjseery/dotagents/blob/main/ARCHITECTURE.md) before
changing the shape of any of it.** It is the one home for the five tiers and why the repos stay separate,
the authoring → generate → install chain (a plugin *copies* its payload; it can never reference one), the
per-machine setup for both harnesses, and what a new project needs. This README does not restate it.

## Why this repo exists

Process is not a stack, so it had no generic repo to live in and defaulted into a product repo — shipping
from `Concertable/agent-standards` under a plugin named `concertable`, while naming no Concertable type in
41 of its 46 skills and only a delivery reference in the other five. `agent-standards` recorded that
placement and its revisit condition: *"Revisit only if a non-Concertable repo actually wants this
method."* `tomjseery/agent-workboard` did, so the method moved out and this repo is its home.

## Two skill shapes, and why this corpus uses the self-contained one

A skill only pays for a separate doc when something **outside** the repo needs that doc at a stable path.
`dotagents` and `react-agents` route to `standards/<domain>/<TOPIC>.md` because that exact path is
mirrored in `Concertable/agent-standards`, which is how a local roster pairs with its generic twin.

This corpus pairs with nothing, so its skills are **self-contained**: the `SKILL.md` body *is* the
standard. `@`-import cannot rescue the routed shape here — it only expands inside `CLAUDE.md`/`AGENTS.md`,
never inside a `SKILL.md` body — so a router would only add a guaranteed Read tool call for content the
skill will never not need. A self-contained skill declares `domain: process` in front matter, since it
names no doc path for the generator to derive a domain from.

One doc stays routed: `standards/process/ALWAYS_ON_INSTRUCTIONS.md`. It is injected at `SessionStart` by
`always_on_instructions.py` rather than invoked, so something other than a skill needs it at a stable path.

```
.agents/skills/<name>/SKILL.md     The standards themselves. Source of truth — edit here.
                                   Front matter (name, description, domain: process) then the standard.
.agents/skills/<name>/**           Anything else beside a SKILL.md — a script the skill invokes — copied
                                   verbatim into every generated copy, since a plugin cannot reach outside
                                   its own root.

standards/process/ALWAYS_ON_INSTRUCTIONS.md         The one routed doc: injected at SessionStart, not invoked.
.agents/hooks/*.py                 The enforcement mechanisms, shared verbatim by both harnesses,
                                   with their tests beside them.
.claude/hooks/, .codex/hooks/      Each harness's own wiring. Neither duplicates a mechanism; each
                                   just names the shared script to run.
.agents/workflows/                 The multi-agent workflow contract, host manifests and roles.
scripts/*.ps1                      Repo-invariant executables a standard may name as a constant,
                                   vendored into a consumer by .agents/vendor-hooks.ps1.

.agents/sync-generated.ps1         Regenerates .claude/skills/, .claude/agents/, .codex/agents/ and
                                   plugins/process-standards/. Refuses to write when a router and the
                                   tree disagree. CI runs it with -Check.

plugins/process-standards/         Generated. The installable plugin — its own full copy of every
                                   payload, because a plugin cannot reference outside its root.
```

Run after any change to an authored file:

```
pwsh .agents/sync-generated.ps1          # write
pwsh .agents/sync-generated.ps1 -Check   # verify only; what CI runs
```

## The hooks are mechanism, not standards

Each names no product and states no rule. Each reads its opt-in table **from the repo the session is
running in**, does nothing in a repo that carries no such table, and blocks loudly if a table is present
but unreadable — failing open on a malformed table is enforcement that is inert while looking wired.

| Hook | Event | Harness | Opt-in table | Enforces |
|---|---|---|---|---|
| `skill_router.py` | write | both | `.agents/skill-routes.json`, else a shipped registry | the standard owning a path is loaded before it is written |
| `model_routing_guard.py` | write and shell launch | both | — | skills, scripts, workflows, and launch commands pass resolver values instead of literal model selections |
| `always_on_instructions.py` | session start | both | — | `ALWAYS_ON_INSTRUCTIONS.md` is in context from the first turn |
| `merge_review_gate.py` | `gh pr merge` | Claude | `.agents/merge-gate.json` | no merge without a current, clean code-review |
| `plan_handoff_stop_launcher.py` | turn end | Claude | a `_PROGRESS.md` ledger | a selected plan context transfer ends with its continuation pointer |
| `marketplace_refresh.py` | session start | Codex | `.agents/skill-routes.json` or `.agents/profile.json` | refreshes enabled default plugins from Git marketplaces; Claude does this natively from `autoUpdate` |

Claude's wiring is `.claude/hooks/hooks.json`, Codex's is `.codex/hooks/codex-hooks.json`, and neither
duplicates a mechanism — each names the shared `.py` under `.agents/hooks/` to run. A hook that only one
harness runs is authored in that harness's folder, which is why `marketplace_refresh.py` lives under
`.codex/` rather than beside the shared mechanisms.

The Codex refresh launches a detached worker, finds the bundled native CLI when `codex` is absent from
`PATH`, and supplies `CODEX_HOME` explicitly. A successful refresh gets the full one-hour throttle; a
failure is recorded separately and retried after five minutes.

**Two hooks are Claude-only, and the reason is the hook, not the harness.** `merge_review_gate.py`'s whole
vocabulary is `SHELL_TOOLS = {"bash", "powershell"}`; Codex's shell tool name has not been observed in a
real hook payload (`exec_command`, `unified_exec` and `local_shell` all appear in the CLI binary, which is
not evidence), and registering it on a guess would look wired while acting on nothing. The `Stop` gate is
the same shape of open question. Both are asserted as Claude-only by a test, so closing either is a
deliberate change rather than a discovery.

**The router resolves its registry from any installed plugin, not only from its own.** A carved service
repo carries no table of its own; an organisation registers it in a `routes/registry.json` shipped from
*that organisation's* repo, while this file names no organisation. Searching only beside itself would
find nothing in exactly that arrangement.

It exists because reachability was never the problem. A skill applies only if it is invoked: an agent
added a test project, misclassified it, used the wrong assertion library, with both testing skills
installed and listed — and the follow-up review repeated the same blind spot and returned clean. So the
trigger stopped being "the model decided this is relevant" and became **the path being written**.

Its coverage is deliberately partial: matchers are per-tool, so `dotnet new`, a shell heredoc or an MCP
write never reaches it, and injection is not compliance. Where a rule is decidable at build time, the
build is the tier that guarantees; this is the tier that gives fast feedback.

The same table answers the question after the fact, which closes the *review* half of that failure:

```
git diff --name-only <range> | python .agents/hooks/skill_router.py --skills-for   # add --json for a machine
```

## Install

Per machine, not per repo. Provisioning lives in `Concertable/agent-standards` and installs this plugin
in its **generic** scope, alongside `dotnet-standards@dotagents` and `react-standards@react-agents`:

```
powershell -ExecutionPolicy Bypass -File scripts/provision-agent-standards.ps1
powershell -ExecutionPolicy Bypass -File scripts/provision-agent-standards.ps1 -VerifyOnly
```

This repo is private, so provisioning needs git credentials that can read it. Installing is what makes
the skills **and** the hooks live; settings alone never install a plugin.

## Adding a standard

Write it directly at `.agents/skills/<name>/SKILL.md` — front matter (`name`, `description`,
`domain: process`) followed by the standard itself. No separate doc. Run the generator. A skill that
invokes a script puts it beside the `SKILL.md`; the generator ships the whole folder.

The `description` names **both** the content and the trigger — "use when enabling auto-merge, when a PR
seems stuck, when a merge-queue run fails". A vague description means the skill never loads, which is
worse than not having it, and every generated copy carries it verbatim.

One topic per skill; a skill that grows a second unrelated topic gets split, and it earns its own file
once it runs past about eighty lines. Reference a sibling skill **by name in prose** (`` the `plans`
skill ``), never by a doc path — a path reference dangles the moment that doc moves, and `@`-import
cannot rescue it inside a `SKILL.md` body.
