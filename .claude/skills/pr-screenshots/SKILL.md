---
name: pr-screenshots
description: Capturing and attaching real visual evidence to a PR that touches UI — logging in against a live running instance rather than a mock, the local-setup gaps a fresh checkout hits that CI never shows (missing environment-scoped config, machine-level secrets, shared local resources colliding across concurrent checkouts), never resetting another checkout's shared state to unblock your own, and attaching inline (hosting the image on a scratch branch in the same repo and linking its raw-content URL) rather than posting a link to somewhere else. Use when a PR changes UI and needs screenshots, when asked to show what a page looks like, or when attaching an image to a pull request.

kind: contract
domain: process
---

# Visual evidence for a PR

Read and follow the [canonical shared definition](../../../.agents/engineering/contract/pr-screenshots/SKILL.md) in full.
This entry point supplies only Claude discovery metadata; the shared procedure is authored once under `.agents/`.
