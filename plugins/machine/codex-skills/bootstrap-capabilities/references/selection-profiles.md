# Source-owned selection profiles

`scripts/selection_profiles.py` is an optional read-only adapter. Call
`validate_metadata(metadata, owner_package, candidate_ids)` before consumption, or
`evaluate(metadata, owner_package, candidate_ids, scope_root, filenames)` to validate and evaluate.
Metadata is a parsed immutable source object supplied by the caller; the reader never loads or executes
package code. The caller verifies the pinned owner/native manifests and supplies actual canonical
`marketplace/package` candidates from that same snapshot. Every output is a native slug qualified by
the owner's marketplace and must exist in that roster. Dependency closure belongs to the caller.

The caller supplies one explicit existing directory root and complete canonical relative filenames.
An invalid root raises `ValueError` before evaluation, including when filenames match markers. This module
does no discovery, ancestor search, Git invocation, network access, installation, lock selection,
platform inference or writes. Git tracking and bounded non-Git discovery belong to the orchestrator;
partial discovery must never be supplied as a complete list.

Schema version 1 requires exactly `schema_version`, `owner_package`, `document`, `markers`,
`valid_profile_plugins`, and ordered `forms`. Unknown metadata keys at every level are rejected.
`markers` contains `suffixes`, `basenames`, and output `plugins`. Suffixes begin with a dot and match
case-insensitively; basenames match exactly. Neither contains path separators. Marker results survive
missing or invalid source documents.

Each form has a unique nonempty `name`, a `select` object, named `fields`, and `selection_groups`.
Selectors require `path` and `type` (`object`, `array`, or `scalar`); only scalar selectors may have
a finite `values` domain. Paths are arrays of nonempty object-key strings; an empty path denotes
the selected value. A missing path, wrong type, or out-of-domain selector allows the next form.
Once selected, a form is terminal, including when its fields are invalid.

Fields require `path`, `type`, and a nonempty finite domain: scalar `values` or array `members`.
An optional `default` must satisfy the domain. Missing differs from explicit null. Domains contain
only finite JSON scalars; equality preserves JSON types, including boolean versus number, while
`1` and `1.0` are equal numbers. Unknown source properties and duplicate array entries are allowed.
Each group contains `rules`; each rule has `field`, output `plugins`, and exactly one operator:
`equals` for a declared scalar or `intersects` for declared array members. Groups match independently;
only the first matching rule in each group contributes output. Rule outputs must be nonempty.

`document` is a canonical relative forward-slash path. Document paths and filenames reject embedded NUL.
The reader rejects absolute/drive paths,
traversal, non-file targets, and links resolving outside the explicit root. It reads at most 1 MiB
of UTF-8 JSON and requires an object. Missing files contribute no profile outputs; other read/parse
failures produce diagnostics. Valid profiles add `valid_profile_plugins` and matched rule outputs.

The deterministic result contains sorted `selected_ids`, sorted unique `marker_matches`,
`selected_form` (or null), validated `fields`, `matched_rules` as zero-based group/rule index pairs,
and `diagnostics`. Invalid selected forms retain their name and marker outputs while adding one
field-specific diagnostic. Invalid metadata or incomplete/invalid caller inputs raise `ValueError`.

The compact fixture `tests/fixtures/selection-profile.json` shows a source-owned C++ declaration:
`.agents/skill-routes.json` prefers a modern `profile` over legacy `kind` and `layers`; `cpp` markers
alone choose no toolchain or API. `gpp`/`msvc` and `win32` are selected by explicit finite profile
values. Those names and paths are example data only; the runtime contains no C++ literals.
