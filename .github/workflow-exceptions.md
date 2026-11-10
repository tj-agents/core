# Workflow exceptions

Each zizmor exception names one exact rule, workflow, line and column.
Job naming exceptions in `workflow-baseline.json` preserve published check contexts.

| Rule | Location | Reason |
| --- | --- | --- |
| `undocumented-permissions` | `ci.yml:319:7` | Tommy forbids explanatory code comments. The exact permission grants the named qualification, status-reading or release-publication job its required API access. |
