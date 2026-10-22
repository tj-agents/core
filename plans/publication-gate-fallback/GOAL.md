# CLIs start while core main awaits regeneration

Authorized by Tommy on 2026-10-18 after `codex resume` failed with catalog digest drift at `a9937191`: "fix
this please".

## Outcome

Claude and Codex startup never fails because `main`'s tip is a merge whose generated publication has not
landed yet; it uses the last published core commit instead.

## Delivery

PR #300 (`Fix/PublicationGateFallback`). Merge is authorized under the standing tj-agents auto-merge
instruction once exact-head CI is green and the canonical review is approved.

## Progress

- Cause confirmed: `rolling_plugins._state` ran the publication gate on `main`'s tip only; `a9937191` fails
  with the reported drift and its regenerate commit landed 17 seconds later.
- f7ed0705: first approach fell back to the last regenerated commit.
- 567829f3: per Tommy, startup instead builds an unpublished tip locally with CI's regenerate steps; the real
  a9937191 build matched CI's 10fe0938 publication byte for byte.
- f8c9523b, 96468e39: review fixes (chained errors, bounded pruned cache, OSError handling). CI green at
  96468e39.
- Done: PR #300 merged 2026-10-18 as `615b49c298a7df7272465b626369ab377499bdc9`.

```completion
{
  "outcome": "Claude and Codex startup builds an unpublished core main locally instead of failing.",
  "acceptance": [
    {
      "id": "unpublished-main-falls-back",
      "criterion": "A main tip that fails the publication gate is generated locally and served; a tip that cannot be generated still fails.",
      "evidence": [
        {"source": "tests/test_rolling_plugins.py::test_unpublished_core_main_is_generated_locally_for_startup", "result": "passed at 96468e39; CI green"},
        {"source": "real tj-agents/core history", "result": "a9937191 generated locally matched CI's 10fe0938 publication"}
      ],
      "owner": "Claude session 2c4453fe",
      "next_action": "None; delivered in PR #300."
    }
  ],
  "deliveries": [
    {"repository": "tj-agents/core", "pr": 300, "head": "96468e39d73b3ce515fffa5a1d538f6791b22d85"}
  ],
  "open_tasks": []
}
```
