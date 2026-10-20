# Work and problem record admission

Core consumes canonical work-item identities. It does not create, update, close, retain, or publish
problem records.

Load the qualified Work Items writer that matches the request:

| Request | Writer |
| --- | --- |
| Untyped recording request | `work-items:write-issue` |
| Faulty software behavior | `work-items:write-bug` |
| Observed agent or process error | `work-items:write-mistake` |
| Deliberate shortcut or deferred compromise | `work-items:write-debt` |
| New or changed behavior | `work-items:write-feature` |
| Concrete work with a completion condition | `work-items:write-task` |

The Work Items package owns provider admission, reconciliation, facts, persistence, retention, and
verified closure. Its writers use the source primary checkout's explicit provider selection. Missing,
invalid, unavailable, or offline selection blocks recording: retain unsent facts in the active task or
goal with the resolver and observable resume condition. Do not create a Markdown register or select a
different backend.

Plans, review artifacts, and roadmaps retain design and recovery evidence and link canonical item
identities; they are not a live queue. Preserve existing records and history. Repository and employer
policy controls where evidence may go; never redirect employer-owned facts to a personal provider.
