---
name: pr-screenshots
description: Capturing and attaching real visual evidence to a PR that touches UI — logging in against a live running instance rather than a mock, the local-setup gaps a fresh checkout hits that CI never shows (missing environment-scoped config, machine-level secrets, shared local resources colliding across concurrent checkouts), never resetting another checkout's shared state to unblock your own, and attaching inline (hosting the image on a scratch branch in the same repo and linking its raw-content URL) rather than posting a link to somewhere else. Use when a PR changes UI and needs screenshots, when asked to show what a page looks like, or when attaching an image to a pull request.
domain: process
---

# Visual evidence for a PR

A frontend change is not reviewed until someone has seen it render. Code review proves the diff is
internally consistent; it does not prove the page looks right, the login flow completes, or the empty
state reads as intended. **When a PR touches UI, attach real screenshots of the running app to the PR
itself** — not a description of what it should look like.

## The screenshots must be real

Log in with real credentials against a real running instance of the app, not a mocked or storybook-style
render. A screenshot of a component in isolation proves the component compiles; it does not prove the
page a user actually reaches looks right — missing chrome, an unstyled shell, a broken redirect only
show up end-to-end.

Before launching anything, check whether a project skill already covers running this app — its author
already solved the cold-start problems. If none exists, the generic launch-and-drive pattern (dev
server, headless browser, `wait-for` over `sleep`) is a separate concern from this doc; this doc picks up
once the app is actually reachable.

## A fresh checkout may have gaps CI papers over

CI and any long-running dev environment already have their local setup done; a fresh worktree or a
machine's first run of a given service often does not, and the failure looks like a broken feature
instead of missing setup:

- **Environment-scoped config that exists for CI/test but not for ad-hoc local runs.** A per-environment
  settings file often exists for a "test" or "CI" environment (because automation depends on it) but not
  for a plain local run, so the exact config a fresh login needs — redirect URIs, allowed origins — may
  simply not exist yet outside that one environment. Check for the gap before assuming the feature itself
  is broken.
- **Secrets that live outside the checkout.** A per-machine secret store (env vars, a local secrets file,
  a credential manager entry) is not per-worktree — once set on the machine, it should already be there;
  if the app fails at startup demanding one, that is a one-time machine setup step, not a code bug.
- **Shared local resources colliding across concurrent checkouts.** A named local resource — a database
  volume, a fixed port, a lock file — that is not scoped per checkout will collide the moment two
  worktrees try to run the same service at once. A same-looking error on a fresh worktree that another
  checkout's run doesn't hit is often exactly this, not a regression.

None of these are reasons to fake the screenshot instead. Fix the gap (and if it is a real, repeatable
gap rather than a one-off, that fix is itself worth landing — a missing config file or a shared resource
that should have been scoped per checkout is tech debt regardless of why it was found).

**Never touch another checkout's shared state to unblock your own** — a Docker volume, a database, a
lock file another running session might depend on. Give your own run an isolated copy instead of
resetting the shared one.

## Capturing the screenshot

Drive the real login flow, land on the actual route under review, and capture the page — not just that
it loaded, but that the specific thing under review renders (the populated state if data exists, the
empty state and a note that it's the empty state if it doesn't). Capture every route/state the PR
actually changed, not just the entry page.

## Attaching to the PR — inline images, not a link to somewhere else

**"Attach to the PR" means the image renders inline in the PR thread**, not a link the reviewer has to
open elsewhere. A forge's comment API generally has no direct image-upload endpoint reachable from a
CLI/script context (the browser drag-drop path is a separate, session-authenticated upload flow), so
uploading to an unrelated external host (a public gist, an image-sharing service) is usually both the
wrong trust boundary for a private repo's screenshots and unnecessary — the PR's own repository can host
the image itself:

1. Push the image(s) to a scratch branch in the **same repository** (never the app's own PR branch —
   this is hosting, not part of the change), on a stable, easily-found path (e.g. one folder per PR
   number).
2. Reference each image by its raw-content URL at that commit in a PR comment
   (`![caption](<raw-content-url-for-this-forge>/<branch-or-sha>/<path>.png)`) — this is what makes it
   render inline instead of as a bare link.
3. **This step is additive only.** Add the new image file(s) to whatever is already on that branch;
   never clear or replace what's there first. A scratch/hosting branch still lives in the shared
   repository — clearing it wholesale is exactly the kind of destructive step that needs a human's
   go-ahead, and it's never actually necessary: a new PR's images just get a new path.
4. The branch is disposable infrastructure, not part of the change under review — it never merges.

**Litmus:** *if the reviewer has to click a link and load a separate page to see the picture, it isn't
attached yet — it's linked.*
