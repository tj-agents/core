---
name: reset-test-explorer
description: Reset Visual Studio's test discovery when its cache is lying — the IDE registers a project as a test container only when the IDE itself builds it, and trait rewriting happens at compile time, so a populated bin directory lets it skip the build and keep serving a stale discovery. Covers which symptoms this fixes and which are real test failures belonging to a tier's debug procedure, enumerating the generated-test projects rather than working from a remembered list, why a command-line build afterwards recreates the exact condition being cleared, and judging the result by shape rather than by a test count. Use whenever Test Explorer shows trait groups the build strips, a project's tests missing while a sibling's show, or wrong test counts after scenarios were added or removed.
domain: process
---

# Resetting the IDE's test discovery when its cache lies

Visual Studio caches test discovery per solution, under a `TestStore` folder inside the `.vs` directory
beside the solution file. Two properties of that cache make it go stale in one specific way, and no amount of
re-running tests clears it:

- **Only a build performed by the IDE registers a project as a test container.** A binary built from the
  command line is not registered, so if the IDE decides a project is already up to date — because `bin/` is
  populated — it may skip the build and never register the project at all.
- **Trait rewriting happens at compile time.** Where a build task strips a scenario runner's auto-generated
  traits and injects the project's own category before compilation, the IDE's own build always applies it.
  What the cache is showing is what a *previous* discovery produced, not what the current build produces.

So the reset is: force the IDE to rebuild the generated-test projects from nothing, and delete the discovery
cache so it rediscovers from scratch.

Symptoms this fixes, and only these:

- Trait groups appearing that the build strips — a scenario-title group, a default test-type group, or a
  category derived from a scenario tag.
- A project's tests missing entirely while a sibling's show.
- Wrong test counts after scenarios were added or removed.

A test that *fails* is not this. Route that to the tier that owns it: [`integration-debug`](../integration-debug/SKILL.md),
[`e2e-api-debug`](../e2e-api-debug/SKILL.md) or [`e2e-ui-debug`](../e2e-ui-debug/SKILL.md).

## Step 1 — have the IDE closed

Tell the user to close Visual Studio, and wait for confirmation. Deleting the cache underneath a running
instance leaves it half-written, which looks like the original symptom.

## Step 2 — delete the build output and the cache together, in one shot

Every project that carries `.feature` files needs its `bin/` and `obj/` removed — that is what forces the IDE
to build, and therefore register, each one. Enumerate them rather than working from a remembered list; a
project added since the last reset is exactly the one whose tests are missing.

```powershell
$projects = Get-ChildItem -Recurse -Filter *.csproj |
    Where-Object { Get-ChildItem $_.Directory -Recurse -Filter *.feature -ErrorAction SilentlyContinue }
$projects | ForEach-Object { $_.FullName }   # show what is about to be cleaned
$projects | ForEach-Object {
    Remove-Item -Recurse -Force (Join-Path $_.Directory 'bin') -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force (Join-Path $_.Directory 'obj') -ErrorAction SilentlyContinue
}
Remove-Item -Recurse -Force '<solution-dir>/.vs' -ErrorAction SilentlyContinue
```

**Do not follow this with a command-line build.** A command-line build repopulates `bin/`, which is the
condition that makes the IDE skip its own build — and skipping its own build is the whole cause.

## Step 3 — hand the build back to the user

Tell them:

> Open Visual Studio, then run Build All (`Ctrl+Shift+B`) before opening Test Explorer, and let the build
> finish completely first.

## Judge the result by shape, never by a count

After the build, tests should group by the category each test project declares as an assembly trait — its
tier. The verdict is: **every expected tier present, and no stripped group anywhere** — no scenario-title
group, no default test-type group, no scenario-tag-derived category.

A count would be wrong by the next scenario anyone writes, which is why neither this doc nor the report
states one.

## Notes

- Only the generated-test projects need their build output removed. Projects the IDE has already built in a
  previous session are already registered.
- The categories to *keep* are the ones each project declares itself as an assembly trait — the tier names.
  The ones to expect gone are the runner's generated ones.
- The trait-rewriting task runs before compilation on both incremental and full builds, so a stripped group
  reappearing means either the task did not run or the cache is stale. The full reset above covers both.
  Deleting only the `TestStore` folder sometimes clears a purely stale cache — but never follow that with a
  command-line build of a generated-test project, for the reason in Step 2.
- To sub-group inside a tier by project, add Project as a secondary grouping level in Test Explorer.
