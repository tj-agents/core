---
name: solution-assessment
description: Assess existing capabilities and credible solutions once before choosing how to build a reusable tool, infrastructure capability or technical mechanism. Use before selecting one.
kind: policy
domain: behavior
---

# Assess a solution

Owns the one-time choice of how to build a reusable tool, infrastructure capability or general technical
mechanism, in a new or existing repository.

A design the user prescribed is decided; do not reassess it. An agent's unaccepted proposal is only an
input. Otherwise, before choosing an implementation, check the repository's existing capabilities and
credible public solutions from current primary sources, inspecting implementations when behaviour
matters. Compare adopting, forking, reusing part, building and keeping the current solution against the
intended outcome, and choose the smallest suitable approach. Say which facts were observed, read in source
or only documented. Routine edits and application business behaviour need no assessment.

Solve deterministic work with deterministic code: a script, fixture or dummy process, never a model
session.

```text
Test the session-close watcher against `python -c "import time; time.sleep(600)"`, not a Claude session.
```

The assessment grants no authority to install, run third-party code, replace a component or publish.
