---
name: guide-build
description: Scaffold, refresh and build a repository's guide/ folder from the shipped builder — a vendored build.py, page.html, open.sh and README.md configured by guide/guide.json, with text-anchored code excerpts, lettered annotations, link validation, and one bash script that builds and opens the page on Linux and Windows (Git Bash). Use when creating a repository's guide folder, refreshing its vendored builder, building the page, or writing excerpt directives or annotations.

kind: utility
domain: process
---

# Build the guide folder

This skill ships the guide builder; a repository vendors a copy and owns its content. Scaffold or
refresh with:

```bash
python "<skill-directory>/scripts/scaffold.py" --repo <repository-root>
```

- Builder-owned, overwritten on every run: `guide/build.py`, `guide/page.html`, `guide/open.sh` and
  `guide/README.md`. A local edit to them is drift: the script reports each file it replaced, and
  `--check` reports drift without writing. Repository-specific notes go in the repository's own
  instructions, never in the vendored files.
- Repository-owned, created only when missing: `guide/guide.json` (title, eyebrow, repository URL and
  output path — fill the skeleton before the first build), `guide/annotations.json` and
  `guide/chapters/`.
- On POSIX the script marks `open.sh` executable; on Windows commit that bit with
  `git add --chmod=+x guide/open.sh`.

Build and open the page with `guide/open.sh` from Git Bash; `--build-only` skips opening it. It needs
Python 3.9+ as `python3` or `python` on PATH and fails with a clear message otherwise. The vendored
`guide/README.md` documents the chapter layout, the excerpt directives and the annotation format for
chapter authors; `engineering:guide` owns what the chapters say.
