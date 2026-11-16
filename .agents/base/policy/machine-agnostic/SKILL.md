---
name: machine-agnostic
description: Keep everything working from a fresh clone on any machine, with local state only as the rebuildable output of a scripted command. Use when adding or changing setup, configuration, credentials, tools, state, records or anything else a run depends on.
kind: policy
domain: behavior
---

# Machine-agnostic

Owns where the things a run depends on may live. Everything works the same on any machine from a fresh
clone plus remote services, such as GitHub, package registries and the selected work-item provider.
Committed repository content and those services are the only records of a choice.

Anything that must exist locally (installed tools and shims, generated configuration, caches, a secret's
local copy) is created by a scripted command shipped by its owner: `tj install`, a declared setup step or
an onboard command. Re-running that command on a new machine rebuilds it. Never hand-edit local state or
ask the user to. Never treat `~/.agents-state`, host settings, agent memory or a checkout's untracked
files as the record of a choice: record the choice in the repository or the remote service, and let the
command derive local state from it.

A secret's issuer is its source of truth. The owning onboard command enrols its local copy into the OS
credential store or the owner's protected state, and can enrol it again on another machine.

Machine-wide installation stays inert outside the repositories that commit its use. Per-checkout state
never substitutes for a committed choice: every clone and worktree reads the same committed declaration.

```text
Choice: this project's agents push as its GitHub App.
Record: commit the repository's access declaration, never only a local identity file.
Local: `tj install` installs the shared gh shim and Git helper; one onboard command enrols the App key.
New machine: clone, `tj install`, onboard. Same behaviour, nothing copied by hand.
```
