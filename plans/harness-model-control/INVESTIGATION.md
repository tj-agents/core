# Codex model control and missed side-workstream handoff

## Authorization and ownership

Tommy requested this investigation in a separate Codex session on 2026-09-29, using a simpler
model than Astra. The successor owns only this investigation. The originating session retains
the Concertable/repository-declared plugin migration; do not adopt, edit or close that task.

- Worktree: `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Docs-ModelSwitchHandoffInvestigation`
- Branch: `Docs/ModelSwitchHandoffInvestigation`
- Base: `a0fe999b3f2efc7380b87b1b6e9e25fbbd554f54` from fetched `origin/main`
- Lane: L3, an open investigation without an implementation design yet. The canonical table resolves it to Sol.
- Status: complete. Investigation merged in PR #65 at `17ac27a`; the handoff-routing correction merged in PR #66 at `838580a` after the full CI check passed.

The user first suggested a core skill so Codex could change the main model through what they called
`hardnessinject` / `harnessinject`. Determine the actual mechanism rather than assuming that spelling
names a real tool. Their next explicit instruction was to hand off this investigation, and also find
why the parent did not immediately select a handoff when the conversation diverged substantially.

## Questions to resolve

1. Can this installed Codex harness change the active main chat's model and effort programmatically?
   Distinguish actual current-session switching, changing only a later turn, starting another session,
   CLI profile defaults, and running a cheaper child agent. A skill cannot invent an unavailable tool.
2. What existing core support already covers in-session lane execution, model selection or harness
   injection, and is it actually enabled/delivered in this host? Inspect before proposing another skill.
   An existing checkout is `C:\Users\TommySeery\source\repos\tj-agents\core.worktrees\Fix-InSessionLaneExecution`,
   last observed on `Docs/CloseInSessionLaneExecution` at `328b004`. Treat it as read-only evidence;
   current origin/main may already contain the result. Check current history and exact capabilities.
3. Why did the parent continue the separate model-control investigation inside the migration chat?
   Determine whether the defect is missing/misrouted instructions, absent enforcement, conflicting
   lifecycle guidance, or an execution failure despite a sufficient rule. Inspect actual delivery.
4. What is the smallest grounded correction to make the intended behavior reliable? Specify the
   source owner, existing entry point to update versus justified new skill, activation requirements,
   and meaningful acceptance checks. Do not implement a speculative host feature.

## Observed conversation evidence

- Original task: stop Concertable's globally enabled plugin from affecting unrelated C++ repositories;
  finish the existing repository-declared agent configuration plan.
- User resumed the migration and requested a simpler model. Parent promised cheaper bounded workers
  but stayed on Astra in the main chat. User then explicitly objected to still being on Astra.
- Parent replied that it could not change the active chat model, recommended selecting Sol, and stopped.
  That statement was not based on a complete inspection of core's existing in-session model support.
- User then asked for core capability/skill support and harness injection. This was a distinct authorized
  side workstream. Parent began a local investigation instead of immediately handing it off.
- Parent loaded skill-creator and searched exposed tool metadata for injection/model-switch/session-config
  terms; that search returned no matches. It announced it would have Sol investigate, but no separate
  session had been launched when the user objected again.
- The loaded `plan-execution` workflow already directs distinct authorized side workstreams through
  `engineering:handoff`. The current `handoff` definition explicitly says to select bounded
  side-workstream mode immediately and retain the original goal in its originating session.
- A lower-cost audit comparison child belonged to the original migration; it did not handle this new
  model-control investigation and must not be presented as a completed handoff for it.

## Scope and constraints

Read `AGENTS.md`, `README.md`, and relevant existing skills. Canonical authored instructions and runtime
belong in `.agents`; host trees are adapters and `plugins/*` is generated. Keep shared instructions in
one source. Preserve unrelated work and do not mutate the existing lane-execution checkout, active PRs,
normal user profiles, credentials, or the migration's worktrees. Do not send messages to external users.
Use local code as evidence first; if host contract verification needs browsing, use official primary
sources pinned to the installed version. Record supported behavior separately from inference.

The initial handoff authorized investigation, isolated probes and a concrete correction proposal. Tommy's
subsequent instruction authorizes implementing and delivering the actionable handoff-routing correction.
No host model-control action was exposed, so do not change normal model configuration or invent a main-chat
switch. Keep the user's lower-model preference.

## Completion expectation

Write the findings and concrete next action in this same file, with exact file/symbol or official-source
evidence, observed host capabilities and any true missing capability. Explain the handoff failure using
specific evidence, not a generic apology or a redundant new rule. Report which correction is actionable
and which requires a host feature or explicit user decision. Keep the migration separate.

## Next Steps

The core investigation and actionable handoff-routing correction are complete. The correction routes
direct handoff requests, has focused regression coverage, and was delivered in PR #66. The Concertable
migration remains with its original owner. A main-chat model switch remains dependent on an exposed
Codex host action; do not simulate it through a profile change or substitute session.

## Findings — 2026-09-29

### 1. Model and effort control in this host

No callable tool exposed to this Codex session changes the current main chat's model or effort. The
available tool metadata contains no session-configuration or harness-injection action, and a repository
search found no `harnessinject` or `hardnessinject` mechanism. This establishes the capability boundary
for this session, not a claim that no OpenAI product can ever update a session. `codex` is unavailable on
this shell's PATH, so no installed CLI version or live CLI command behavior was established here.

The mechanisms that do exist have distinct effects:

| Mechanism | Observed support | Effect |
| --- | --- | --- |
| Work/Codex model picker | [OpenAI's Work and Codex help](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex) documents manual model and reasoning selection and says Codex keeps a manual selection. | User-controlled selection for the chat; this session has no tool to operate that picker. The active turn cannot be retroactively changed. |
| Agents API session update | [OpenAI's Agents API configuration guide](https://developers.openai.com/api/docs/guides/agents-api/configuration) documents updating a session's model and effort for later turns while preserving history. | This is an API capability for Agents API sessions. No evidence binds this Codex Desktop chat to that API or exposes its session update action here. |
| Responses `configuration_update` | [OpenAI's reasoning guide](https://developers.openai.com/api/docs/guides/reasoning) documents an input item for later reasoning effort changes. | Effort only in a caller-managed Responses conversation; it is not a Codex Desktop model-switch tool. |
| Codex skill front matter | `.agents/engineering/contract/lanes/SKILL.md` says generated `model:` metadata re-points the model for a skill, and installed `engineering/2.1.16/codex-skills/plan-execution/SKILL.md` carries `model: gpt-6-sol`. | Source intent and packaged metadata are verified. The skill was read as a file in this session; no native skill-invocation tool or live model-transition receipt was available to verify a main-chat switch. Codex skills have no per-skill effort key in `.agents/lanes/codex.json`. |
| Delegated lane agent | `.agents/lanes/codex.json`, generated `plugins/engineering/codex-agents/lane-l3.toml`, and the exposed `lane_l3` agent role carry the Sol/high pair. | Runs a child task at that pair; parent model and ownership stay separate. |
| Codex handoff launcher | `.agents/machine/handoff-codex/scripts/launch-codex.ps1` resolves `-Lane` and passes `--model` plus `--config model_reasoning_effort=...` to a new native CLI process. | Starts another session; it cannot change this chat. |
| CLI/profile defaults | The same launcher omits model arguments to inherit the CLI default. | Affects launches using those defaults; changing a normal profile is neither an in-place switch nor authorized by this investigation. |

The exact active model after reading a skill remains unverified. In particular, the repository's
front-matter assertion must not be used as proof that loading `plan-execution` switched the main chat
from Astra to Sol. The product-specific host needs an observable model receipt or a controlled live probe
to establish that behavior. The OpenAI help page supports manual selection, while the Agents API page
cannot be applied to this Desktop session without an exposed bridge.

### 2. Existing core support and delivery

`origin/main` at `a0fe999` already contains the in-session lane-execution correction. Commit `328b004`
only retired its completed plan; `44dd87e` and `45a1820` added the current lane/ownership guidance.
`.agents/engineering/contract/lanes/SKILL.md` explicitly separates lane selection from ownership,
normally keeps small and medium work with its parent, and says not to launch another session solely for
model cost. `.agents/engineering/workflow/plan-execution/SKILL.md` routes a distinct, independently
actionable, separately authorized side workstream to `engineering:handoff` while retaining the original
goal. `.agents/engineering/workflow/handoff/SKILL.md` supplies the isolated-checkout and one-successor
procedure. The installed engineering 2.1.16 copy has that same handoff rule, and this session received
the packaged `engineering:session-guidance` context. The exposed lane-agent roles show agent delivery;
neither package presence nor generated source proves every host hook is trusted and running.

`.agents/plugins/manifests/codex/engineering-hooks.json` wires `workflow_route.py` on
`UserPromptSubmit`. Its `selects_side_workstream_handoff` requires an explicit side-workstream phrase,
a nearby handoff/delegate/launch verb, and either a root `GOAL.md` or an explicit active-work phrase.
It injects the handoff contract as additional context. It does not classify a new topic semantically,
does not inspect a plan in another location, and is not a fail-closed enforcement gate. The focused
tests in `.agents/hooks/tests/test_workflow_route.py` exercise those literal prompt shapes only.

### 3. Why the parent missed the handoff

The handoff's recorded conversation evidence says the parent loaded `plan-execution`, then began
investigating the new core capability in the migration chat and searched tool metadata there. At the
point that request became a distinct authorized workstream, the plan-execution rule above already
selected a bounded handoff. The explicit later handoff request removed any ambiguity. This is an
execution/routing miss despite a sufficient canonical rule, not a missing model-control skill or a
conflict with the lane contract. The earlier child audit was part of the migration and did not transfer
this core investigation.

The prompt hook could not reliably recover the initial miss: it selects only lexical side-workstream
handoff prompts, and the recorded initial request was to investigate/add core model support. The exact
September 29 parent prompt and hook event were not available in the local Codex transcript store, so
whether this specific hook fired is unverified. A transcript search for the terms returned an older
September 26 session, not the parent chat. Do not infer a hook activation failure from that absence.

### 4. Actionable correction and verification

Do not add a model-switch skill or duplicate the side-workstream rule. The smallest core correction is
to improve selection of the existing handoff entry point: give
`.agents/engineering/workflow/handoff/SKILL.md` front matter a trigger that names a distinct authorized
side workstream, and extend `.agents/hooks/workflow_route.py` so a direct handoff request selects the
existing handoff contract even when the user does not say the literal words "side task" or
"workstream". Preserve the prompt-only and planning-only boundaries. This addresses discoverability
and the explicit-request case; it cannot guarantee that an arbitrary new topic will be recognized as
a side workstream. If guaranteed semantic detection is required, the host must expose active-goal
state and a suitable routing/enforcement event. Another prose rule would not supply that guarantee.

Before delivery, replay the actual parent prompt when it becomes available, add targeted cases to
`.agents/hooks/tests/test_workflow_route.py`, and run a trusted live-host probe: with an active migration
goal, introduce an independent core request, verify one isolated handoff is selected and launched, and
verify the migration remains owned by the parent. Check the installed hook trust/activation state rather
than treating generated files as adoption. For a future main-chat model feature, require an exposed host
action and a receipt showing the same chat's next turn uses the selected model and effort while its
history and goal persist. Until then, use the manual picker for that chat or the existing lane agent and
new-session mechanisms for their respective scopes.

## Verification recorded

- Read `AGENTS.md`, `README.md`, the canonical plan-execution, lanes, handoff and launcher contracts,
  installed engineering 2.1.16 entry points, hook wiring and focused tests.
- Confirmed `origin/main` contains `328b004` and its preceding in-session lane work.
- Searched exposed tool metadata and local sources for model/session injection controls; none were
  exposed. `codex --version` and `codex --help` could not run because `codex` is absent from PATH.
- Checked official OpenAI Work/Codex, Agents API and Responses documentation, keeping each product's
  mechanism separate.
- `python -B -m unittest discover -s .agents/hooks/tests -p test_workflow_route.py`: 12 passed.
- `pwsh .agents/sync-generated.ps1 -Check`: 385 package files checked, 0 changed, 0 pruned.
