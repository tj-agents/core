# Self-repair investigation

Requested investigation, 22 October 2026. This records policy gaps found by source inspection; it does not authorize a workflow redesign or report an observed employer-data disclosure. Audited Core main at 412b8d11493dea9ea27ff5fff1a2cc21e5e751d7.

Current behavior: engineering:session routes user mistake callouts to engineering:self-repair after answering the direct question. Self-repair investigates whether a consumed Core standard, skill, hook, workflow or host enforcement caused or failed to prevent the mistake. It reconciles an existing repair owner, records through the selected profile, and repairs in the current session. Unrelated checkouts require a separate worktree of the standards source repository. Handoff requires the user to ask. Standing authority includes implementation, tests, review, PR, merge and source publication after that repository's gates. Explicit user limits remain binding. Shared ownership/completion/handoff/cleanup failures default to P1 and pause unrelated work and new launches until verified correction or explicit deferral. Completion currently permits repaired/tested/committed source or a recorded blocker, then resumption of the original task. Loaded sessions retain their old instructions.

Personal versus work: this is one shared Engineering workflow, applicable when Engineering is selected. Personal requires explicit personal adoption and selects personal:work-item / personal:create-work-item / personal:address-work-item backed by GitHub. Infonetica employer scope selects its qualified counterparts backed by Azure Boards and employer-native types. Employer incident evidence must remain with the employer provider; a GitHub owner, personal directory or the tj-agents/infonetica source repository does not establish personal scope. Neither installing Core nor repairing a standard authorizes adopting Personal or installing into the consuming repository. Missing/invalid/unavailable provider selection blocks recording and retains unsent facts in active task context with a resolver and resume condition; historical Markdown registers are not a fallback backlog.

## Expected boundary

The workflow should distinguish investigating a callout from establishing a source defect and explain a truthful no-source-change outcome when the existing rule is adequate. A repair originating in an employer checkout should retain its incident and confidential evidence in the employer tracker, identify the separate Core source repair, and specify what sanitized evidence can cross that boundary. Completion should make source correction, publication and installed/fresh-session verification distinguishable.

## Findings

1. No explicit no-source-change disposition: the diagnosis step distinguishes missing, ambiguous, unenforced and ignored rules, but the next mandatory step says to fix the standard and completion names only repaired source or a blocker. It does not explain how to conclude that an adequate rule was ignored without inventing another rule.

2. Origin/source recording ambiguity: self-repair says to use the selected profile, then moves work to the source repository. The recording contract selects from the source primary checkout and protects employer-owned facts, but self-repair does not explicitly preserve the originating employer record, define a sanitized linked Core record, or state which repository supplies selection at each stage. The general confidentiality boundary exists; the cross-repository procedure is underspecified. No actual disclosure was observed.

3. Runtime verification limitation: current authored Engineering hook manifests on both hosts wire the GitHub credential-scope gate, not a callout repair gate. The old callout gate and handoff admission script were deliberately removed. Current self-repair selection and completion are instructional. Existing process-standard tests assert guidance text, not live model compliance. Restoring the removed hook is not implied by this report.

4. Source versus rollout completion: standing authority extends through publication while completion permits a tested local commit; the workflow acknowledges already-loaded instructions remain unchanged. It does not itself define installed-host or fresh-session acceptance for each kind of repair. Other repository policies may impose additional checks.

## Evidence and verification

Core source at audited commit:
- https://github.com/tj-agents/core/blob/412b8d11493dea9ea27ff5fff1a2cc21e5e751d7/.agents/engineering/workflow/self-repair/SKILL.md (trigger, repair boundary, authority and completion).
- https://github.com/tj-agents/core/blob/412b8d11493dea9ea27ff5fff1a2cc21e5e751d7/.agents/engineering/policy/session/SKILL.md (callout selection; questions/reviews alone do not authorize implementation).
- https://github.com/tj-agents/core/blob/412b8d11493dea9ea27ff5fff1a2cc21e5e751d7/.agents/engineering/resources/problem-records.md (provider selection, employer evidence retention and missing-provider behavior).
- https://github.com/tj-agents/core/blob/412b8d11493dea9ea27ff5fff1a2cc21e5e751d7/README.md#refresh-and-repository-boundaries (explicit personal adoption and employer scope).
- https://github.com/tj-agents/core/blob/412b8d11493dea9ea27ff5fff1a2cc21e5e751d7/.agents/plugins/manifests/codex/engineering-hooks.json and corresponding claude/engineering-hooks.json (current wiring).
- https://github.com/tj-agents/core/blob/412b8d11493dea9ea27ff5fff1a2cc21e5e751d7/.agents/hooks/tests/test_process_standards.py (text assertions, not behavioral host proof).

Historical context: local plans/self-repair-admission-deadlock/GOAL.md describes an older callout admission failure. plans/session-store-retention/PLAN.md records the 18 October decision to remove the callout gate, admission.py and forced handoff. Those old plan expectations must not be treated as current runtime behavior.

Validation: python -B -m unittest discover -s .agents/hooks/tests -p test_problem_records.py -v passed all 9 tests on Windows. This verifies provider resolution, primary-worktree selection and rejection paths, not a live work-to-Core repair or model compliance. Installed Personal provider inspection succeeded; existing open Core work items were listed before recording and none matched. Infonetica replacement provider skills were inspected only in the existing Fix-TjAgentsDependencies source worktree; they were not loaded as this repository's governing profile and their installed-host acceptance was not established. No employer tracker was contacted, profile changed, real agent launched, or runtime repair implemented.

## Implications

A callout can interrupt authorized product work and begin a broadly authorized Core delivery. Without explicit causal and cross-repository dispositions, agents may add unnecessary rules, mishandle the relationship between employer incidents and Core repair records, or overstate completion from source-only evidence. These are demonstrated specification gaps and verification limits, not reproduced disclosure or enforcement failures.

## Proposed resolution for a future repair

Agree and document the existing workflow's causal decision outcomes, including an adequate-rule/no-source-change result. Define origin incident versus source repair ownership and provider selection without moving employer details to Personal. Define proportional source/publication/installed acceptance evidence and preserve explicit user limits, existing live repair ownership and monitoring-only deliveries. Verify representative personal and employer paths, including missing providers and an adequate existing rule. Keep implementation pending a repair request; this issue captures the requested investigation.

## Record publication

The selected Core provider resolves to personal:work-item. Existing open Core records were inspected successfully; none matched this investigation. Automatic approval review rejected creation of a GitHub issue because it considered the payload, external destination and Personal-provider use insufficiently authorized. No issue was published. This file preserves the requested investigation; publication remains pending explicit approval of this report and tj-agents/core as the destination.
