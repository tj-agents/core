# Review capability completion

## Outcome and authority

Tommy authorized completing and merging this work on 2026-10-21. This supersedes the earlier local-only investigation restriction. The owner is Codex session `01a15f16-40b2-7540-a573-ddb0b8d3da47`, executing in `.worktrees/Refactor-ReviewCapability` on `Refactor/ReviewCapability` from `origin/main` at `ccecdab5`. No existing implementation owner was verified; the historical Claude discussions left no review implementation to resume.

## Acceptance

- `review` is a bounded utility usable directly or by a workflow, with a concise shared definition and genuine host adapters.
- Relevant review standards come from exactly the reviewed repository's injected selection, including replacements and repositories without a route table. Unrelated installed standards are excluded.
- Existing workflow callers retain their immutable candidate, independent review, security, finding and delivery evidence requirements through their existing owners.
- `big-review` and `big-review-all` become `staged-review` and `staged-review-all`; migrate authored callers and both hosts, deleting the obsolete public entries under this repository's personal policy.
- Sweeps of reviewed or rebased stacks review relative changes; history rewriting does not silently trigger a full repeat review or discard earlier findings.
- Focused checks, source/package validation, independent review and exact-head Windows/Linux CI pass; merge the PR and follow its generated publication to completion.

## Scope and implementation

One coherent delivery slice: review capability/classification, standards selection, staged naming and the callers/tests needed to preserve their behavior. Reuse native reviewers, injected guidance and existing review evidence helpers. Do not create another review engine or state store. Measure the final diff and reassess if substantive code/tests exceed the repository's slice guidance.

SQLite discovery/registration is separate work. Its missing association and the stale helper used during investigation remain recorded in the primary checkout's `.agents/machine/TECH_DEBT.md`; do not repair them here.

## Progress

2026-10-21: verified current main and open PRs, checked historical discussion checkpoints, created the isolated delivery worktree and began the bounded implementation. Implemented the utility cutover, selected-plugin resolver, clean staged rename and relative rebased sweep guidance. Focused resolver, native-layer and source-layout checks pass; completing remaining selection assertions before independent review. PR: not opened.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/engineering/utility/review/SKILL.md",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Bounded native review with repository-selected conventions and staged selectors",
      "source": ".claude/skills/review/SKILL.md",
      "mapping": "Extended host adapter to shared utility; native reviewer remains host-specific",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "test_review_native_layer.py: native names, packaged shared body and consumer repository checks; test_source_layout.py: host adapters and self-contained packages"
      }
    },
    {
      "host": "codex",
      "behavior": "Bounded native review with repository-selected conventions and staged selectors",
      "source": ".codex/skills/review/SKILL.md",
      "mapping": "Extended host adapter to shared utility; native reviewer remains host-specific",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "test_review_native_layer.py: native names, packaged shared body and consumer repository checks; test_source_layout.py: host adapters and self-contained packages"
      }
    }
  ]
}
```

Pre-review checkpoint: 10 resolver tests, 11 native/package consumer checks, 22 source-layout checks, 14 review workflow checks and 22 process checks pass. Guidance examples and host coverage validate. No installed-name collisions. Scope is one atomic review capability cutover; generated output stays outside the PR. Native Codex inventory currently fails on an unrelated stale cpp-agents marketplace path, so installed-host acceptance is not claimed; independent native-general fallback will review the immutable commit.

Independent review of 4b071b20 found missing lifecycle evidence for standalone --fix and an unspecified frozen checkout for Codex non-current targets. Both are repaired in the follow-up. The follow-up also makes rebase sweeps return before descendant-only preparation, scopes native inventory to the reviewed repository, and ignores malformed metadata from unselected enabled plugins. Resolver tests: 11 passed; native/package tests: 11 passed; tier tests: 34 passed using a fixture environment without inherited command-line Git configuration (the local empty-value restoration issue is external). Next: incremental review of this commit, exact-head CI, merge and generated publication. PR: https://github.com/tj-agents/core/pull/338.

Independent incremental and security review of 9ebaa21e found a relative host executable could be resolved again after entering the reviewed repository. Freeze that executable as an absolute path before dispatch. The regression check passes with all 12 resolver tests. No other defects were reported; final security verification, exact-head CI and delivery follow this fix.

```completion
{
  "outcome": "Complete and merge the review utility, exact injected standards and staged naming cutover.",
  "acceptance": [
    {
      "id": "utility",
      "criterion": "Review is a bounded utility usable alone or within a workflow.",
      "evidence": [
        {
          "source": ".agents/engineering/utility/review/SKILL.md and test_review_native_layer.py",
          "result": "Shared utility and both adapters verified; 11 native/package tests passed."
        }
      ],
      "owner": null,
      "next_action": null
    },
    {
      "id": "injection",
      "criterion": "Apply relevant standards from exactly the repository selected current-host injected packages.",
      "evidence": [
        {
          "source": "tests/test_review_rules.py",
          "result": "12 resolver tests passed, including no-route, exclusions, replacement, exact host version, missing-scope rejection and executable path regression."
        }
      ],
      "owner": null,
      "next_action": null
    },
    {
      "id": "lifecycle",
      "criterion": "Workflow callers retain candidate, independent review, security and finding evidence.",
      "evidence": [
        {
          "source": ".git/agent-workflow/reviews/af1d0a03cad97e09f18f029a38f601ba05b547b77c9ef7812834414c99a66506/work-order.md",
          "result": "General, incremental and security review completed; R1/R2/R3 resolved; final review receipt sealed at 7809ddcf."
        }
      ],
      "owner": null,
      "next_action": null
    },
    {
      "id": "names",
      "criterion": "Replace big-review and big-review-all with staged-review and staged-review-all.",
      "evidence": [
        {
          "source": "Source layout, host adapter and package checks",
          "result": "Both host entries and callers migrated; obsolete authored aliases removed; generated output excluded from source PR."
        }
      ],
      "owner": null,
      "next_action": null
    },
    {
      "id": "sweeps",
      "criterion": "Rebase sweeps preserve earlier coverage and review relative changes.",
      "evidence": [
        {
          "source": ".agents/engineering/workflow/incremental-review/SKILL.md and incremental reviewer",
          "result": "Range-diff, equivalent patch preservation, conflict-resolution review and design-sweep return verified with no residual finding."
        }
      ],
      "owner": null,
      "next_action": null
    },
    {
      "id": "delivery",
      "criterion": "Final-head Windows/Linux CI, source merge and generated publication are verified.",
      "evidence": [
        {
          "source": "PR #338 at 7809ddcf; CI runs 39638381524 and 39638998529",
          "result": "Both exact-head Windows/Linux verification sets, guards, guidance checks and aggregate ci-required passed."
        },
        {
          "source": "PR #338; merge adc01470a4a13861cd77c2da5e46ef5d20a8372e",
          "result": "MERGED on 2026-10-21T17:15:06Z at the reviewed source head."
        },
        {
          "source": "CI push run 39642118651, regenerate job 119368067161; generated main commit 90f1d9d29866692fddcdf27f0506e930743cf2c0",
          "result": "Causal publication job succeeded; generated commit names the source merge and contains the utility body, selected-rules helper and staged host entries; obsolete public names absent."
        },
        {
          "source": "PR #341, merge 2bd18badc411b2bbe2a1e501c5c681dcd0372dbf",
          "result": "Pure plan-deletion closeout merged with all exact-head checks green; the completed record remains local."
        }
      ],
      "owner": null,
      "next_action": null
    }
  ],
  "deliveries": [
    {
      "repository": "tj-agents/core",
      "pr": 338,
      "head": "7809ddcfefa295f6882735c8637edc9e55907715"
    },
    {
      "repository": "tj-agents/core",
      "pr": 341,
      "head": "6df0ec4ed2257397ee8326fe9f2d1e3696fb2886"
    }
  ],
  "open_tasks": []
}
```

Delivery verified 2026-10-21: PR #338 merged as adc01470; generated packages published as 90f1d9d2. Source and packaged checks passed on Windows and Linux. Fresh installed-host loading remains outside this source acceptance because the unrelated stale marketplace configuration is recorded for separate repair. The main push verification matrix remains visible in GitHub; its publication job is already successful.
