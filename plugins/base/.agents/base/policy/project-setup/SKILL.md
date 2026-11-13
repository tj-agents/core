---
name: project-setup
description: Select and inject a repository's standards when creating a project or adding a technology stack. Use before writing code in a new repository or adopting a new stack.
kind: policy
domain: behavior
---

# Set up a project

Owns selecting a repository's standards when it is created or adopts a technology stack.

Identify the owning standards packages and inject them through `agent:plugins`. For a new repository, take
its personal or work scope from the user's statement or a recorded profile adoption in its instructions;
otherwise ask the user and wait. Never infer scope from the checkout path, GitHub owner or author.

Complete the utility's project write and passing check before writing governed code or calling the setup
finished, even when a solution assessment is already complete. If the injector or current publisher
sources are unavailable, keep governed writes pending and report the missing capability.

```text
New car-hunting repository; the request says nothing about personal or work scope.
Ask which it is before choosing policy profiles. Apply the chosen scope with the project's stack.
Write and check the resulting project selection before starting governed code.
```
