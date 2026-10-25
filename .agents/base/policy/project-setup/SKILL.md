---
name: project-setup
description: Select and inject a repository's standards when creating a project or adding a technology stack. Use before writing code in a new repository or adopting a new stack.
kind: policy
domain: behavior
---

# Set up a project

When creating a repository or adding a technology stack, identify its owning standards packages and inject them into that repository through `agent:plugins`. For a new repository, determine whether it is personal or work before selecting policy profiles. If neither the user's statement nor a recorded profile adoption in its instructions establishes that scope, ask the user directly and wait for the answer. Use the stated scope when selecting the project's policy profile through that utility. Never infer scope from the checkout path, GitHub owner, or author.

Complete the utility's project write and passing check before writing governed code or claiming the operation is finished. This requirement applies even when a solution assessment is already complete. If the injector or current publisher sources are unavailable, keep governed writes pending and report the missing capability.

```text
New car-hunting repository; the request says nothing about personal or work scope.
Ask which it is before choosing policy profiles. Apply the chosen scope with the project's stack.
Write and check the resulting project selection before starting governed code.
```
