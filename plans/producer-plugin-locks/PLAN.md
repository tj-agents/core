# Project producer plugin locks

Owner: codex:01a1415f-6448-7123-8b17-c7fb67aee637. Authorized by Tommy's 16 October work-items implementation and personal adoption goal; shared plan is docs/plans/problem-management/PLAN.md. This slice is generic machine selection support, with no tracker behavior.

Observed gap: schema-3 plugin-lock forces base/engineering/machine@tj-agents, while shipped harness requirements and existing native installations use base-agents from tj-agents/core. Selecting both duplicates Core identities. Preserve existing aggregate locks and defaults; allow one complete Core triplet from base-agents with an immutable producer pin, and explicit --core-marketplace selection. Extending a producer lock preserves its choice. Explicit conversion keeps stack/foreign selections and pins, removes only replaced Core identities and an unused old marketplace. Reject mixed/partial Core selection and producer source impersonation. Keep all writes project-scoped; no global profile or employer changes.

Validate old lock behavior plus producer-only adoption, extension, explicit conversion, malformed/conflicting declarations, harness composition and both generated host settings. Ship schema, utility guidance and harness ownership together. Focused tests, generation, independent review and Windows/Linux CI precede delivery. Core generated distribution output remains uncommitted. Base: origin/main 1509abf8, containing PR #272 and its generated publication. The parent Rolling Plugin Sync owner remains untouched.

Next: implement the bounded compatibility change, verify, review and deliver under the original goal authority.

Implementation keeps schema 3 backward compatible and adds an explicit Core marketplace option, validates producer source identity, composes existing harness overlays and ships the schema with machine. A new test initially asserted a fully qualified aggregate identity against an existing helper that strips @tj-agents; fixed that assertion to check the helper's actual contract. No runtime failure or test weakening was involved. Focused validation is running.

Validation: 14 plugin-lock, 22 adoption, 38 repository-config and 9 bump tests pass (83 total). The generator already ships catalog schemas; redundant explicit resource mapping was removed. Refreshed disposable catalog digests using the generator-required command; generated catalog and plugin trees will be restored before commit. Native source generation and freshness are checked before freezing review.
