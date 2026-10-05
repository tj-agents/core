# Guide

Designs the app and explains its code, chapter by chapter. The `engineering:guide` skill owns the content
rules; this file owns the build and excerpt mechanics.

## Build

```bash
guide/open.sh
```

Run it from Git Bash on Windows; `bash` in PowerShell is WSL's. It assembles the page, writes it to the
output path configured in `guide.json`, and opens it. `--build-only` skips opening it. Commit `open.sh`
with the executable bit (`git add --chmod=+x guide/open.sh`) and keep it LF (`*.sh text eol=lf` in
`.gitattributes`); bash rejects CRLF.

## Layout

- `page.html`: the page shell, with its styles, chapter navigation and scripts.
- `chapters/NN-name.html`: one fragment per chapter, in reading order. Each starts with
  `<!-- chapter: id | Title -->`.
- `build.py`: assembles the page and copies code into it from the repository.
- `annotations.json`: optional lettered notes on source lines of an excerpt.
- `guide.json`: the build configuration. Four keys, all required: `title` and `eyebrow` for the page
  header, `repository` (the repository's `https://` URL, used to build source links), and `output` (the
  built page's path, relative to the repository root, forward slashes).

## Code excerpts

Excerpts are located by text, not line numbers, so they follow the code as it moves:

```text
@@CODE src/main.rs "fn main()" block@@
@@CODE Cargo.toml "[lints.rust]" +3@@
@@CODE Cargo.toml "[package]" .. "[dependencies]"@@
```

`block` runs from the anchor line to its matching closing brace, `+N` takes N lines, and `..` runs to the
first later line containing the end text. Join segments with `&` to show an elision between them. The build
fails if an anchor no longer exists.

To annotate an excerpt, add an ID after its path (`@@CODE src/main.rs id=entry "fn main()" block@@`) and
the same ID in `annotations.json` with an `owner` and `marks`. Each mark names a unique substring of one
included line, a `call`, `callback`, `data` or `return` kind, a page `target` ID, a `label` and a `text`.
An optional `focus` names the destination line inside an annotated target.

## Updating

Content rules live with `engineering:guide`. `build.py`, `page.html`, `open.sh` and this `README.md` are
vendored from `engineering:guide-build` and refreshed by its scaffold script — local edits to them will be
overwritten. Repository-specific notes belong in the repository's own instructions, not here.
