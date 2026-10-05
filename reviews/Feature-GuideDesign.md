# Code review — Feature/GuideDesign

> **This file is a work order, not a discussion.** If you're handed this file, fix the open `[ ]`
> findings directly and report what changed. Tick each `[x]` as you land it. Pause only for a genuinely
> irreversible or ambiguous finding: record its durable disposition, take the safe path, and keep going.

**Review status:** `complete`
**Reviewed up to commit:** `b5015684b690bb8affe83f88f3d4f5e26bcd87ae`  `(2026-10-05)`
**Judgment:** `approved`

## Review pass — 2026-10-05 — full

**Candidate base:** `df1bc41edf4aec8e6d0b85025c97cf1cfb73f302`
**Candidate head:** `d8cfd0810665bf3649e03ae652eec25af2ad7b9e`
**Candidate branch:** `Feature/GuideDesign`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:8290032643198346dd13ef3d87d80061534f09d1e3b4066e406621ec4f55a6e6` `(15 paths)`
**Candidate bundle:** `removed after completion`
**Candidate bundle identity:** `sha256:74988fc72ae8e5c3c1924cc0858f64dcc40d263677f50dfcade45cfb18aaf044`
**Work-order path:** `reviews/Feature-GuideDesign.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Layers: native Claude Code `code-review` (high) over the frozen range; `api-contract` and `workflow`
lenses over the materialized bundle. No tier conventions apply, no route table, no security-sensitive
paths (`first_path` and `trunk_first_path` null), so no security layer was required. The workflow lens
returned no findings (source ownership, kinds, packaging, registration, cross-references and the
`.gitattributes` blast radius all verified against the frozen tree, including a tree-wide enumeration
proving `template/open.sh` is the only tracked `.sh` file). Parent dropped nothing as pre-existing: every
changed file is new in this candidate. Native findings on `+0` and past-EOF `+N` merged as one defect.

### Findings

- [x] **F1 — MEDIUM — native/correctness** — `.agents/engineering/utility/guide-build/template/build.py:120`
  A `+N` segment is never validated: `+N` past end-of-file raises a raw IndexError on annotated excerpts
  (`lines[number]`) and silently truncates plain excerpts while labelling and linking nonexistent lines;
  `+0` is accepted and yields an inverted empty range labelled `lines 1–0`. Fix: in `segment()`'s `+N`
  branch, require `N >= 1` and `first + N <= len(lines)`, exiting with the builder's `SystemExit` style.
- [x] **F2 — MEDIUM — native/correctness** — `.agents/engineering/utility/guide-build/template/page.html:1`
  No `<!doctype html>` and no `<html lang>`, so every built guide renders in quirks mode and declares no
  document language. Fix: open the template with `<!doctype html>` and `<html lang="en">`.
- [x] **F3 — MEDIUM — native/correctness** — `.agents/engineering/utility/guide-build/scripts/scaffold.py:13`
  Drift comparison is byte-exact with only `open.sh` EOL-normalized, so a consumer checkout that
  materializes CRLF (`* text=auto` or autocrlf) reports perpetual drift for `build.py`/`page.html`/
  `README.md` and rewrites them on every run. Fix: normalize CRLF→LF on both sides for all builder-owned
  files in compare and write.
- [x] **F4 — MEDIUM — api-contract** — `.agents/engineering/utility/guide-build/template/README.md:41`
  The annotation-mark schema omits the required `id` field (`build.py` rejects a mark without a unique
  slug `id`, and it forms the marker/footnote anchors), so an author following the README exactly gets
  `annotations: malformed mark`. Fix: add `id` to the documented mark fields.
- [x] **F5 — LOW — native/correctness** — `.agents/engineering/utility/guide-build/scripts/scaffold.py:28`
  Refresh `continue`s when bytes match before reaching the POSIX chmod, so a lost executable bit on
  `open.sh` is never repaired. Fix: apply the chmod whenever `open.sh` is present on POSIX, outside the
  changed-only branch.
- [x] **F6 — LOW — native/error-handling** — `.agents/engineering/utility/guide-build/template/build.py:215`
  `git()` uses `check=True` with `capture_output`, so a missing `.git` or unborn HEAD dies with a raw
  `CalledProcessError` and git's actual stderr is hidden. Fix: catch and exit with
  `SystemExit(f"git {args}: {stderr}")`.
- [x] **F7 — LOW — native/error-handling** — `.agents/engineering/utility/guide-build/template/build.py:300`
  `resolve_focus_links` runs before the unused-annotations check, so an unused entry that still has marks
  fails with the misleading `expected one source-line destination` instead of `unused annotations`. Fix:
  move the `seen != set(annotations_data)` check ahead of `resolve_focus_links`, and cover the
  marks-present case in the test.
- [x] **F8 — LOW — native/correctness** — `.agents/engineering/utility/guide-build/template/build.py:193`
  `CHAPTER_REF` handles only `and`-joined lists, so `chapters 1, 2 and 3` links and validates only
  chapter 1; dangling comma-list references pass the build. Fix: extend the tail to accept `, N` as well
  as `and N`, linking and validating every number.
- [x] **F9 — LOW — native/correctness** — `.agents/engineering/utility/guide-build/template/build.py:182`
  Annotated-excerpt source links anchor `#L{a+1}` while their text claims `lines a–b`, and a single-line
  range renders `lines 5–5`. Fix: anchor `#L{a+1}-L{b+1}` for ranges, and mirror the plain path's
  single-line label/anchor.
- [x] **F10 — LOW — native/efficiency** — `.agents/engineering/utility/guide-build/template/build.py:245`
  Duplicate-ID validation is O(n²) (`ids.count` per element); a mature guide mints thousands of IDs.
  Fix: use `collections.Counter`.
- [x] **F11 — LOW — api-contract** — `.agents/engineering/utility/guide-build/template/README.md:18`
  The author-facing `@@N@@` chapter-number placeholder is substituted by `build.py` and pinned by the
  tests but documented nowhere. Fix: document it in the README's Layout section.

### Remediation — 2026-10-05

All 11 findings fixed on this branch (no wontfix). F1/F6/F7/F8/F9/F10 in `template/build.py` (+N bounds
validation, git stderr surfaced via SystemExit, unused-annotations check moved ahead of focus-link
resolution, comma chapter lists linked and validated, range-anchored single-or-range source links,
Counter-based duplicate check); F3/F5 in `scripts/scaffold.py` (CRLF-insensitive compare-and-write for
all builder-owned files, exec bit re-asserted on POSIX every run); F2 in `template/page.html` (doctype +
`<html lang="en">`); F4/F11 in `template/README.md` (mark `id` documented, `@@N@@` documented).
Validation: guide-build suite 23 tests OK (1 POSIX skip on Windows), source-layout suite OK, packaging
suite PASS, generation and digests clean. Incremental pass over the remediation delta follows below.

## Review pass — 2026-10-05 — incremental

**Candidate base:** `d8cfd0810665bf3649e03ae652eec25af2ad7b9e`
**Candidate head:** `e7210633575881c282bcbaefbd05d1e6563c2700`
**Candidate branch:** `Feature/GuideDesign`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:5b95b8ec0be52517a583ef5db584864b2b831d5cf73ab858de604d564dcc5481` `(7 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\guide-design-review-2\review\f80d99380ba0f6c3a9937503c79b361b15223b3de560e0c4d5aa5c1630689e62`
**Candidate bundle identity:** `sha256:17828794539dcb35d5584d8fc9186cf0c00562b091192756323e8c83484cd94d`
**Work-order path:** `reviews/Feature-GuideDesign.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

Layers: native Claude Code `code-review` (medium) over `d8cfd08..e721063`; `workflow` lens over the
materialized bundle (no findings: authored-only paths, work-order integrity, catalog digest-only change,
no machine-local paths, README claims match build.py). Native layer verified all eleven F1-F11 fixes
correct and found one regression introduced by the F8 fix:

- [x] **F12 — MEDIUM — native/correctness** — `.agents/engineering/utility/guide-build/template/build.py:204`
  The widened `CHAPTER_REF` tail `(?:(?:,? and|,) \d+)*` consumes bare `, N` in ordinary prose, so
  "in chapter 3, 12 tests cover this" fails the build with `reference to missing chapter 12` (or
  mislinks when that chapter exists). Fix: consume a comma run only when it terminates in an `and N`
  element — tail `((?:(?:, \d+)*,? and \d+)?)` — and add a prose-safety test.

### Remediation — 2026-10-05 (F12)

Fixed on this branch: the chapter-list tail now consumes a comma run only when it ends in an `and N`
element, so "chapters 1, 2 and 3" still links every number while prose like "in chapter 1, 12 tests"
builds untouched (new prose-safety test; 24 tests OK, 1 POSIX skip). Incremental pass below.

## Review pass — 2026-10-05 — incremental

**Candidate base:** `e7210633575881c282bcbaefbd05d1e6563c2700`
**Candidate head:** `55709c246a95c096b49ae95710cdce504fad5395`
**Candidate branch:** `Feature/GuideDesign`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:ece889ba7fea8c1632ee315d4e3c0385eb7bd9869d364efda90bec603d760984` `(4 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\guide-design-review-3\review\3abbad0cb437cfc3297d18492e0edb7b7379ad633dbd7c04669d173d690ae31b`
**Candidate bundle identity:** `sha256:dc75a3d1c4d66aa6e44e31fccaf618a4d53486cf5e7e1a155f417ddf8c90a252`
**Work-order path:** `reviews/Feature-GuideDesign.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

Layers: native Claude Code `code-review` (medium) over `e721063..55709c2`; `workflow` lens over the
materialized bundle (no findings; its one noted evidence gap — F12's text across status flips — is
parent-resolved: those edits were status-only). Native layer confirmed the F12 fix and its test, with one
residual of the same class:

- [x] **F13 — LOW — native/correctness** — `.agents/engineering/utility/guide-build/template/build.py:204`
  The tail permits the optional Oxford comma with zero preceding `, N` elements, so prose like
  "chapter 1, and 2 others" consumes `, and 2` and fails or mislinks. Fix: require at least one comma
  element before the optional Oxford comma — tail `((?:(?:, \d+)+,?)? and \d+)?` — keeping
  "chapters 1 and 2", "chapters 1, 2 and 3" and "chapters 1, 2, and 3" linked; add prose and Oxford tests.

### Remediation — 2026-10-05 (F13)

Fixed on this branch: the Oxford comma is now permitted only after at least one comma element
(verified empirically against all seven reference phrasings), with prose and Oxford-list tests added
(26 tests OK, 1 POSIX skip). Incremental pass below.

## Review pass — 2026-10-05 — incremental

**Candidate base:** `55709c246a95c096b49ae95710cdce504fad5395`
**Candidate head:** `b5015684b690bb8affe83f88f3d4f5e26bcd87ae`
**Candidate branch:** `Feature/GuideDesign`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:ece889ba7fea8c1632ee315d4e3c0385eb7bd9869d364efda90bec603d760984` `(4 paths)`
**Candidate bundle:** `C:\Users\TommySeery\source\repos\tj-agents\core\.git\agent-workflow\runs\guide-design-review-4\review\5dc4f50e914c917ae70a6d6aa85a396a53999a2188060a5797fbdf75a9dbfcda`
**Candidate bundle identity:** `sha256:57b8bf05d1419e97d2c8b7ecd775d533e85e7bffd147c0d76d75161235869eae`
**Work-order path:** `reviews/Feature-GuideDesign.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

### Findings

No findings. Layers: native Claude Code `code-review` (medium) over `55709c2..b501568` — zero findings,
with the F13 regex empirically exercised against nine phrasings, the now-optional capture group verified
against `link_chapters`' falsy check, digests confirmed current, and the 26-test suite re-run green at
the head; `workflow` lens over the materialized bundle — zero findings (authored-only paths, digest-only
catalog change, work-order edits append/status-only, test placement verified). The one noted non-finding
("chapter 1 and 2 other repos" consuming ` and 2`) is the construct's intended meaning, predates this
branch, and is unchanged by it.

