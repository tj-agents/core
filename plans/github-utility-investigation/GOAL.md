# Investigate deterministic GitHub agent utilities

## Outcome and authority

Updated authority, 2026-10-21: Tommy has now requested creation of a general `tj-agents/github` utility package, usable by personal and work projects. This supersedes the investigation-only restriction for package scaffolding, implementation, validation, repository creation and initial publication. Carry the completed assessment forward; standalone GitHub tasks are the concrete consumers. Initial scope is comments, review discussions and compact PR context, with GitHub Actions workflow standards remaining in github-actions. Do not alter Core's review lifecycle or automatically adopt the new package in other projects. The creation work now belongs to C:/Users/TommySeery/source/repos/tj-agents/github/plans/github-utilities/GOAL.md; this file remains the assessment and source handoff.

Tommy requested one independent investigation on 2026-10-21. Conclude whether a GitHub agent standards/capability package with deterministic utilities is a good idea, and recommend the smallest suitable implementation. Report the recommendation directly to Tommy in this CLI. This is investigation only: no implementation, repository creation, installation, permission changes, GitHub posts, pushes, PRs, merges, scheduler registration, additional agent launches or native review sessions.

This is a bounded side workstream. The originating session retains the Core naming audit and session skill rename. You are not alone in the codebase. Do not edit, revert, close or adopt the originating session or another session's task. Your isolated checkout is C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Docs-GitHubUtilityInvestigation on Docs/GitHubUtilityInvestigation, based at 01637cc63afd7da7cb3cd80f9e3139a86d4f75d3. Source and other repository reads are allowed. This goal may hold a concise assessment checkpoint; other source writes are outside scope. Keep this CLI tab open for Tommy's follow-up after your answer.

## User context

Tommy wants engineering review to become a minimal wrapper around the host's native review, ensuring it reads the standards applicable to the diff from the repository's actual imports/selections. Review findings and his requested dispositions should remain in the active conversation context, not a separate memory product, database or Markdown review work order. Posted comments naturally persist on GitHub. This future direction is not authority to remove current review gates here.

He proposed a separate tj-agents GitHub standards/capability repository, distinct from github-actions, with discoverable actions such as github:post-comment or github:post calling deterministic scripts with parameters. He asked whether that is a good idea and whether it improves token use. His latest clarification is that the handoff should only conclude whether the idea is good and how deterministic utilities like this should be implemented in the best way possible.

## Questions to resolve

- Compare existing native gh commands, available connector tools, a thin standards-only skill, and a small deterministic script adapter. Identify what each already supplies before proposing custom code.
- Determine whether a new package/repository is justified or an existing owner should host it. Inspect Core, marketplace selections, github-actions and work-items ownership without changing them.
- Recommend precise action names and boundaries, including top-level PR/issue comments versus inline review comments or a batch review. Do not decide the package is needed in advance.
- Separate model judgment (finding content, applicable standards, whether to post, user disposition) from deterministic mechanics (target validation, exact commit/path/line, structured requests, duplicate handling, errors and compact output).
- Explain token implications honestly: skills/discovery/prompt size, repeated reasoning, tool schemas and output, batching, and the risk that another wrapper costs more. No invented benchmark numbers or assumption that context persists after it is lost. Explain what happens at compaction/resume without building a new memory system.
- Preserve explicit posting authority, exact repository/PR identity, native authentication scope, Windows/Linux portability, and deterministic fixture testing. Do not create new hooks or gates. Do not test by posting or by launching agents.

## Evidence and assessment

Use current primary documentation for GitHub CLI/API and relevant host capabilities. Inspect existing source where behavior matters. Distinguish observed behavior, source inspection and documentation claims. Carry forward useful evidence rather than repeating an assessment after compaction.

Useful starting points: sibling repositories under C:/Users/TommySeery/source/repos/tj-agents; this checkout's .agents/engineering/workflow/review, .agents/engineering/convention/review-lifecycle, host adapters in .codex and .claude, and .agents/workflows. The current marketplace checkout has github-actions and work-items selections but no general github package in its inspected manifest. This is initial local evidence, not proof that no such remote repository exists.

## Next Steps

Assessment complete. Tommy approved saved-account creation once ("lets upload it then? yep go"). Public tj-agents/github was created; both uploads and subsequent API calls used the App. Exact origin/main ab92e0c0612ac45058b414feee604b688744f413 was pushed/fetched and producer CI39602407139 passed on Windows/Linux and native host CLI marketplace acceptance. The bounded follow-up removed an obsolete generated Personal workflow using current publisher e7d0db0 write/check. The new owning goal remains C:/Users/TommySeery/source/repos/tj-agents/github/plans/github-utilities/GOAL.md. Fresh installed-host sessions, independent native review and marketplace catalog integration remain unverified/pending; no live posting performed.

Tommy additionally requested tracing unfinished merge-policy scaffold/bypass work and loading its conversation. Found exact closed Claude ebb28a53-18a4-4bf2-8792-cc7a8ff693bd in core/.worktrees/Feature-MergePolicyBypass; canonical private plan ~/.claude/plans/core/lean-harness.md and handoff-closeout-and-merge-policy.md. github-actions PR14/15 and core PR323 are merged. Scaffold prompt/integration, per-repository policy rollout and bypass activation were not completed. Current merge policy keeps App authorship, uses agents_may_merge to choose approval requirements, and admin PR bypass permits Tommy's manual merge; there is no per-repo author-identity switch. New github repo has no policy declaration and its rulesets API returns []. Event-channel source shipped in a later session but initial caller/listener activation remains pending. Recovery is one user-requested reopen of the exact closed owner, preserving the old pause and prohibitions on applying live rulesets/enabling bypass; no source ownership transfer or revival of completed work.

Lane: L3, because this is an open investigation with unresolved implementation and ownership alternatives.
Launch budget: exactly one supported handoff attempt; no self-delegation or agent launch loops.

## Completed assessment — 2026-10-21

Verdict: deterministic GitHub mechanics are a good idea when they remove repeated work. The current posting need does not require a new repository, another model, or a wrapper for every `gh` command. Start with existing commands and concise guidance in the existing engineering review owner. Add one packaged helper there only for the target/head validation, request reconciliation and compact results that the caller actually needs. A separately selected `github` package becomes justified when standalone GitHub tasks or another implemented consumer need the same mechanics. It would be a sound long-term owner, distinct from github-actions; that is a conditional extraction, not a prerequisite for posting a comment.

This is a completed idea assessment, not an approved implementation plan. Adoption, forking, selective reuse, custom code and keeping the current solution were considered: prefer adopting `gh` and already available connector operations, selectively retain Core's useful target/standards resolution, and write only missing adapter behavior. Forking GitHub CLI or adding a new MCP server for these operations is disproportionate. Keeping direct commands is the smallest solution for occasional posting. A standards-only addition teaches the boundaries but does not itself enforce validation or retries.

### Evidence inspected

- Observed this checkout at `01637cc63afd7da7cb3cd80f9e3139a86d4f75d3` on `Docs/GitHubUtilityInvestigation`. Its `.agents/plugins.json` selects base, engineering, machine and personal. Actual applicability must also use the host's resolved selection/tier evidence; this session's supplied gate includes github-actions and excludes unrelated language stacks.
- Source inspection: `.agents/engineering/workflow/review/SKILL.md`, `.agents/engineering/convention/review-lifecycle/SKILL.md`, both hosts' `skills/review/SKILL.md`, `.agents/workflows/workflow_ops.py` and the skill router. Review currently mandates a native layer plus orchestration and work-order evidence. `route_findings` reuses the router; review preparation freezes paths and rule identities. These are possible reuse points, not proof that all selected external standards reach a fresh native reviewer. The proposed simplification requires a separate authorized cutover of every current gate/reader.
- Source inspection: sibling `github-actions/README.md` owns CI/deployment workflows, merge-policy and machine-event utilities. Sibling `work-items/README.md`, its `manage/SKILL.md` and implementation plan describe a local schema/preview slice, with GitHub transport still planned. A general comments transport should not become work-item semantics or CI policy. Core owns engineering review and its current host adapters.
- Source inspection: sibling marketplace `catalog.json` has github-actions and work-items but no general github entry. Read-only authenticated connector repository search returned 17 visible tj-agents repositories and no repository named github. This is bounded discovery, not proof about all private/unindexed repositories. Local sibling sources were inspected without fetching or changing them; freshness against remote main was not established.
- Observed connector schemas advertise `add_comment_to_issue` for top-level PR conversation comments, `add_review_to_pr` with commit and inline-comment fields, and `reply_to_review_comment`. The first tool's schema accepts `pr_number`; its name alone does not prove ordinary-issue support. Repository search succeeded; write tools were not exercised. Connector availability and credentials on another host remain separate acceptance conditions.
- Current primary documentation supports `gh pr comment`/`gh issue comment`, review submission with `gh pr review`, and nested JSON, pagination and response filtering with `gh api`. The review REST endpoint accepts one review with multiple comments; inline comments have commit/path/line/side coordinates. The official GitHub MCP server already supplies related operations and configurable toolsets; it is a reuse option, not the identity of this session's connector.
- Local `gh --version` failed before returning a version because its existing profile configuration was unreadable in the sandbox. No auth/profile permissions were changed. CLI/API conclusions are documentation-backed; installed CLI posting and Windows/Linux execution were not tested.

Primary references consulted (documentation claims, not live posting verification):

```text
https://cli.github.com/manual/gh_pr_comment
https://cli.github.com/manual/gh_issue_comment
https://cli.github.com/manual/gh_pr_review
https://cli.github.com/manual/gh_api
https://cli.github.com/manual/gh_help_environment
https://docs.github.com/en/rest/issues/comments
https://docs.github.com/en/rest/pulls/comments
https://docs.github.com/en/rest/pulls/reviews
https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api
https://github.com/github/github-mcp-server
https://developers.openai.com/codex/skills/
https://developers.openai.com/blog/custom-code-review-rules-for-codex
https://developers.openai.com/api/docs/guides/compaction
https://code.claude.com/docs/en/skills
```

### Smallest boundary and proposed interface

Model/host responsibilities: native review, finding content and severity, applying the actual selected/imported standards to the changed paths, user dispositions, and deciding whether an authorized post should occur. Pass the native reviewer the exact candidate and resolved applicable standard sources/bodies through its supported context mechanism. Missing imports or unavailable standards are explicit gaps. A posting helper does not discover standards, judge findings, remember conversations, approve its own posts, or launch a reviewer.

Use direct `gh pr comment <number> --repo <owner/repo> --body-file <file>` for an ordinary PR conversation comment. Issue comments use `gh issue comment`. `gh pr review` submits an overall review; inline findings and batches use structured `gh api` requests to the review endpoints. Prefer an existing connector when its documented schema supplies the required operation and the current host already authorizes that credential context. Choose one transport for an operation; do not silently switch account, connector or credential scope after an error.

If implementing an adapter, use one small stdlib Python CLI around argument-array `gh` subprocess calls, with UTF-8 JSON through stdin/files and compact JSON results. Do not build shell command strings from comment bodies. Ship it beside the existing canonical review skill, using installed-relative resource paths and both existing host adapters. `gh` and the Python interpreter are explicit prerequisites. Future extraction would move the owner and callers together, using the existing marketplace/adoption and harness-manifest machinery without new hooks or gates.

Keep distinct operations in that one helper:

| Operation | Resource and required identity |
|---|---|
| `comment-create` | Top-level issue or PR conversation comment; explicit host, owner/repo, target kind, number and body |
| `review-create` | One PR review with explicit event, expected head SHA, summary and zero or more exact inline coordinates |
| `review-reply` | Reply to an existing top-level review-comment ID verified against that repository and PR |

For independently discoverable future skills, prefer `github:post-comment` and `github:post-review` to the ambiguous `github:post`. A one-line inline finding can use `review-create` with one comment; it does not need another skill. Keep replies with the posting subject until they have independently consumed guidance. These are proposed names, not created entries; installed inventories searched showed no matching post-comment/post-review entry, but a full collision check remains an implementation prerequisite. A bare `comments` skill already exists in an installed language package.

Require explicit posting authority from the conversation. A skill selection, review request or request parameter cannot establish user consent on its own. Validate the explicit host/repository, target kind/number, current authenticated principal and expected PR head before writes. Use native authentication; do not retrieve/log tokens, broaden scopes or switch accounts automatically. Verify changed paths and line/range/side against the reviewed diff, including deletions and renames; reject unavailable or invalid anchors. Never guess another repository or silently relocate a comment. Approval and request-changes events require authority for those effects, not merely permission to leave findings.

Anchor a review to its exact commit and return that commit. A preflight head check cannot make posting atomic against a concurrent push; GitHub may accept a review of the earlier commit. Report any observed movement and do not claim an exactly-current-head guarantee.

Use a stable request identifier and remote marker/payload identity to reconcile repeated requests against the authenticated author's comments/reviews, paginating fully. Return an existing matching result; a changed payload under the same identifier is a conflict. `--edit-last` is not sufficient identity for updating one specific bot comment. For a timeout after POST, read back and reconcile before any retry; return `outcome-unknown` if the result cannot be determined. This is best-effort duplicate prevention, not exactly-once delivery across concurrent processes. Serialize writes in one invocation, honor GitHub rate-limit responses and return actionable permission/validation errors without blind retry. One review request can batch related findings; verify what GitHub persisted before declaring the batch complete. No local ledger/database is necessary.

Return status, host/repo/target, actual actor, commit where applicable, created/reused resource IDs/URLs and concise error/retry information. Do not echo the full diff or posted body by default. Temporary API payloads are transport inputs, not review work orders.

Verification owed by any implementation: deterministic mocked gh/API fixtures on Windows and Linux for wrong repository/PR/head, invalid anchors, renamed/deleted lines, Unicode/quotes/newlines, denied auth, pagination, duplicate requests, ambiguous POST results, batch validation and throttling. Validate installed-relative packaging and each host's actual invocation. No model sessions or live posts are needed for these fixture tests. This investigation ran none of those implementation tests and makes no runtime acceptance claim.

### Token and conversation consequences

Expected savings come from avoiding repeated endpoint/schema/quoting decisions, filtering API output, and batching several inline findings into one operation. The code executes outside model inference when run; its source need not be loaded into the conversation. Finding text, substantive review and judgment still consume tokens.

Costs include every additional skill's discovery entry, loaded instruction body, exposed tool schemas, call/result messages, validation round trips and maintenance. GitHub MCP already supports narrowing enabled tools/toolsets. A thin wrapper around a single native comment command may cost more than it saves. Prefer the existing skill and one helper over an action-per-skill/tool catalog. No token or latency benchmark was performed; no numerical saving or guaranteed break-even is claimed. Measure equivalent authorized tasks, including discovery and recovery costs, before claiming improvement.

Keep findings and dispositions in the active conversation, with GitHub owning posted comments. Host-native resume/compaction is the continuity mechanism. Preserve target/head, outstanding findings, user dispositions, posting authority and posted IDs in its summary when supported; reread changed remote state and restore selected standards as needed. A summary may omit details. Missing unposted findings cannot be reconstructed from GitHub, and missing authority cannot be inferred; recover the native transcript or ask Tommy for the missing information before the dependent action. Reinvoke skills when needed. Do not create a Markdown review work order, memory product or database for this proposed design. Existing review artifacts/gates remain unchanged until a separately authorized migration.

```agent-host-coverage
{"schema_version":1,"shared_source":".agents/engineering/workflow/review/SKILL.md","hosts":[{"host":"claude","behavior":"Proposed native review with applicable standards and explicitly authorized deterministic GitHub posting","source":".agents/engineering/workflow/review/SKILL.md","mapping":".claude/skills/review/SKILL.md","verification":{"level":"planned","result":"pending","evidence":"Shared contract and Claude adapter inspected; no implementation, native review session or posting performed"}},{"host":"codex","behavior":"Proposed native review with applicable standards and explicitly authorized deterministic GitHub posting","source":".agents/engineering/workflow/review/SKILL.md","mapping":".codex/skills/review/SKILL.md","verification":{"level":"planned","result":"pending","evidence":"Shared contract, Codex adapter and advertised connector schemas inspected; no implementation, native review session or posting performed"}}]}
```
