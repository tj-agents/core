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
