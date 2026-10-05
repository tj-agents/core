import argparse
import html
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

GUIDE = Path(__file__).resolve().parent
REPO = GUIDE.parent

CODE = re.compile(r"@@CODE (\S+) (?:id=([a-z][a-z0-9-]*) )?(.+?)@@")
SEGMENT = re.compile(r'"(.+?)"\s*(block|\+\d+|\.\.\s*"(.+?)")')
META = re.compile(r"<!--\s*chapter:\s*(.+?)\s*\|\s*(.+?)\s*-->")
SLUG = re.compile(r"[a-z][a-z0-9-]*\Z")
KINDS = {"call": "Call →", "callback": "Callback →", "data": "Data →", "return": "Return ↩"}
LANGUAGES = {
    ".rs": ("rust", "//", ["prism-rust"]),
    ".toml": ("toml", "#", ["prism-toml"]),
    ".yml": ("yaml", "#", ["prism-yaml"]),
    ".yaml": ("yaml", "#", ["prism-yaml"]),
    ".ps1": ("powershell", "#", ["prism-powershell"]),
    ".py": ("python", "#", ["prism-python"]),
    ".ts": ("typescript", "//", ["prism-typescript"]),
    ".tsx": ("tsx", "//", ["prism-jsx", "prism-typescript", "prism-tsx"]),
    ".js": ("javascript", "//", []),
    ".jsx": ("jsx", "//", ["prism-jsx"]),
    ".cs": ("csharp", "//", ["prism-csharp"]),
    ".json": ("json", "#", ["prism-json"]),
    ".sh": ("bash", "#", ["prism-bash"]),
}
CONFIG_KEYS = ("title", "eyebrow", "repository", "output")


def config(path):
    if not path.exists():
        raise SystemExit(f"guide.json: missing file {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"guide.json: invalid JSON ({error})")
    if not isinstance(data, dict):
        raise SystemExit("guide.json: expected object")
    for key in CONFIG_KEYS:
        if key not in data:
            raise SystemExit(f"guide.json: missing key {key!r}")
    for key in data:
        if key not in CONFIG_KEYS:
            raise SystemExit(f"guide.json: unknown key {key!r}")
    for key in CONFIG_KEYS:
        if not isinstance(data[key], str) or not data[key]:
            raise SystemExit(f"guide.json: empty value for {key!r}")
    if data["repository"].endswith("/"):
        data["repository"] = data["repository"][:-1]
    return data


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SystemExit(f"annotations: duplicate key {key!r}")
        result[key] = value
    return result


def annotations(path):
    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)
    if not isinstance(data, dict):
        raise SystemExit("annotations: expected object")
    for excerpt, entry in data.items():
        if not SLUG.fullmatch(excerpt) or not isinstance(entry, dict) or set(entry) != {"owner", "marks"}:
            raise SystemExit(f"annotations: malformed excerpt {excerpt!r}")
        if not isinstance(entry["owner"], str) or not entry["owner"] or not isinstance(entry["marks"], list):
            raise SystemExit(f"annotations: malformed fields in {excerpt}")
        ids = set()
        for mark in entry["marks"]:
            if not isinstance(mark, dict) or set(mark) not in ({"id", "match", "kind", "target", "label", "text"},
                                                               {"id", "match", "kind", "target", "label", "text", "focus"}):
                raise SystemExit(f"annotations: malformed mark in {excerpt}")
            if (not isinstance(mark["id"], str) or not SLUG.fullmatch(mark["id"])
                    or mark["id"] in ids):
                raise SystemExit(f"annotations: duplicate or invalid mark ID in {excerpt}")
            ids.add(mark["id"])
            if (not isinstance(mark["kind"], str) or mark["kind"] not in KINDS
                    or not isinstance(mark["target"], str) or not mark["target"] or mark["target"].startswith("#")):
                raise SystemExit(f"annotations: invalid kind or target in {excerpt}-{mark['id']}")
            if any(not isinstance(mark[field], str) or not mark[field] for field in ("match", "label", "text")):
                raise SystemExit(f"annotations: invalid text in {excerpt}-{mark['id']}")
            if "focus" in mark and (not isinstance(mark["focus"], str) or not mark["focus"]):
                raise SystemExit(f"annotations: invalid focus in {excerpt}-{mark['id']}")
    return data


def find(lines, text, start, where):
    for index in range(start, len(lines)):
        if text in lines[index]:
            return index
    raise SystemExit(f"{where}: anchor not found: {text!r}")


def segments(specs, where):
    matches = list(SEGMENT.finditer(specs))
    rest = SEGMENT.sub("", specs).replace("&", "").strip()
    if not matches or rest:
        raise SystemExit(f"{where}: bad snippet spec {specs!r}")
    return [m.groups() for m in matches]


def segment(lines, parts, where):
    anchor, mode, end_text = parts
    first = find(lines, anchor, 0, where)
    if mode == "block":
        depth, opened = 0, False
        for last in range(first, len(lines)):
            depth += lines[last].count("{") - lines[last].count("}")
            opened = opened or "{" in lines[last]
            if opened and depth <= 0:
                return first, last
        raise SystemExit(f"{where}: unbalanced block at {anchor!r}")
    if mode.startswith("+"):
        count = int(mode[1:])
        if count < 1:
            raise SystemExit(f"{where}: {anchor!r} {mode}: count must be at least +1")
        if first + count > len(lines):
            raise SystemExit(f"{where}: {anchor!r} {mode}: runs past end of file")
        return first, first + count - 1
    return first, find(lines, end_text, first + 1, where)


def render_code(match, chapter, annotations_data, seen, revision, focus_rows, config_data, prism_components):
    rel, excerpt, specs = match.groups()
    source = REPO / rel
    if not source.exists():
        raise SystemExit(f"{chapter}: missing file {source}")
    language, comment, components = LANGUAGES.get(Path(rel).suffix, ("none", "#", []))
    for component in components:
        if component not in prism_components:
            prism_components.append(component)
    lines = source.read_text(encoding="utf-8").splitlines()
    where = f"{chapter}: {rel}"
    ranges = [segment(lines, parts, where) for parts in segments(specs, where)]
    chunks = [lines[a : b + 1] for a, b in ranges]
    indents = [len(l) - len(l.lstrip(" ")) for c in chunks for l in c if l.strip()]
    cut = min(indents) if indents else 0
    out = []
    for i, chunk in enumerate(chunks):
        body = [l[cut:] if l.strip() else "" for l in chunk]
        if i:
            first = next((l for l in body if l.strip()), "")
            out.append(" " * (len(first) - len(first.lstrip(" "))) + f"{comment} …")
        out.extend(body)
    label = ", ".join(f"{a + 1}–{b + 1}" if a != b else f"{a + 1}" for a, b in ranges)
    if excerpt is not None:
        if excerpt not in annotations_data:
            raise SystemExit(f"{chapter}: {excerpt}: missing annotations")
        if excerpt in seen:
            raise SystemExit(f"{chapter}: duplicate excerpt ID {excerpt}")
        seen.add(excerpt)
        entry = annotations_data[excerpt]
        by_line = {}
        for letter, mark in enumerate(entry["marks"]):
            found = [(a + offset, line) for a, b in ranges for offset, line in enumerate(lines[a:b + 1]) if mark["match"] in line]
            if len(found) != 1:
                raise SystemExit(f"{chapter}: {excerpt}: match {mark['match']!r} found {len(found)} included source lines")
            mark["letter"] = chr(ord("A") + letter) if letter < 26 else str(letter + 1)
            by_line.setdefault(found[0][0], []).append(mark)
        focus_rows[excerpt] = {
            "rows": [(f"{excerpt}-line-{number + 1}", lines[number])
                     for a, b in ranges for number in range(a, b + 1)],
            "default": f"{excerpt}-line-{min(by_line) + 1}" if by_line else f"{excerpt}-line-{ranges[0][0] + 1}",
        }
        rows = []
        for index, (a, b) in enumerate(ranges):
            if index:
                rows.append('<span class="source-row elision"><span class="source-gutter" aria-hidden="true">⋯</span><span class="source-marks"></span><span class="source-text">… omitted source lines …</span></span>')
            for number in range(a, b + 1):
                source_text = lines[number][cut:] if lines[number].strip() else ""
                markers = []
                for mark in by_line.get(number, []):
                    marker_id = f"{excerpt}-{mark['id']}"
                    markers.append(f'<a id="{marker_id}" class="line-mark" href="#@@FOCUS:{marker_id}@@" aria-label="{html.escape(mark["label"], quote=True)}" aria-describedby="{marker_id}-note">{mark["letter"]}</a>')
                rows.append(f'<span class="source-row" id="{excerpt}-line-{number + 1}"><span class="source-gutter" aria-hidden="true">{number + 1}</span><span class="source-marks">{" ".join(markers)}</span><span class="source-text">{html.escape(source_text)}</span></span>')
        notes = []
        for mark in entry["marks"]:
            marker_id = f"{excerpt}-{mark['id']}"
            notes.append(f'<li id="{marker_id}-note" class="trace-note"><span class="trace-kind">{mark["letter"]} · {KINDS[mark["kind"]]}</span> <span><strong>{html.escape(mark["label"])}</strong> — {html.escape(mark["text"])}</span></li>')
        def source_link(a, b):
            if b > a:
                return f'<a href="{config_data["repository"]}/blob/{revision}/{rel}#L{a + 1}-L{b + 1}">lines {a + 1}–{b + 1}</a>'
            return f'<a href="{config_data["repository"]}/blob/{revision}/{rel}#L{a + 1}">lines {a + 1}</a>'

        source_links = " ".join(source_link(a, b) for a, b in ranges)
        return (f'<figure class="code annotated-code" id="{excerpt}" data-lang="{language}"><figcaption><span class="path">{html.escape(rel)}</span><span class="lines">{source_links}</span></figcaption>'
                f'<div class="annotation-grid"><div class="code-viewport"><pre><code>{chr(10).join(rows)}</code></pre></div><aside class="annotation-notes" aria-label="{html.escape(entry["owner"], quote=True)} annotations"><span class="annotation-owner">{html.escape(entry["owner"])}</span><ul>{"".join(notes)}</ul></aside></div></figure>')
    return (
        '<figure class="code"><figcaption>'
        f'<span class="path">{html.escape(rel)}</span><span class="lines">lines {label}</span>'
        f'</figcaption><pre><code class="language-{language}">{html.escape(chr(10).join(out).rstrip())}'
        "</code></pre></figure>"
    )


CHAPTER_REF = re.compile(r"\b([Cc]hapters?) (\d+)((?:(?:,? and|,) \d+)*)")
UNLINKED = re.compile(r"(<svg\b.*?</svg>|<pre\b.*?</pre>|<a\b.*?</a>|<!--.*?-->|<[^>]+>)", re.S)


def link_chapters(text, ids, where):
    def target(number):
        chapter_id = ids.get(int(number))
        if chapter_id is None:
            raise SystemExit(f"{where}: reference to missing chapter {number}")
        return f"#{chapter_id}"

    def replace(match):
        word, first, rest = match.groups()
        if not rest:
            return f'<a href="{target(first)}">{word} {first}</a>'
        numbers = re.sub(r"\d+", lambda m: f'<a href="{target(m.group(0))}">{m.group(0)}</a>', rest)
        return f'{word} <a href="{target(first)}">{first}</a>{numbers}'

    return "".join(part if UNLINKED.fullmatch(part) else CHAPTER_REF.sub(replace, part)
                   for part in UNLINKED.split(text))


def git(*args):
    try:
        return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True,
                              check=True).stdout.strip()
    except subprocess.CalledProcessError as error:
        stderr = (error.stderr or "").strip() or str(error)
        raise SystemExit(f"git {' '.join(args)}: {stderr}")


def resolve_focus_links(page, annotations_data, focus_rows):
    for excerpt, entry in annotations_data.items():
        for mark in entry["marks"]:
            target = mark["target"]
            destination = target
            if target in focus_rows:
                destination = focus_rows[target]["default"]
                if "focus" in mark:
                    matches = [row_id for row_id, source_text in focus_rows[target]["rows"]
                               if mark["focus"] in source_text]
                    if len(matches) != 1:
                        raise SystemExit(f"annotations: {excerpt}-{mark['id']}: destination focus found {len(matches)} source lines")
                    destination = matches[0]
            elif "focus" in mark:
                raise SystemExit(f"annotations: {excerpt}-{mark['id']}: focus target is not an annotated excerpt")
            marker_id = f"{excerpt}-{mark['id']}"
            token = f"@@FOCUS:{marker_id}@@"
            if page.count(f'id="{marker_id}" class="line-mark" href="#{token}"') != 1:
                raise SystemExit(f"annotations: {marker_id}: expected one source-line destination")
            page = page.replace(token, destination)
    return page


def validate_page_links(page):
    ids = re.findall(r'\bid="([^"]+)"', page)
    counts = Counter(ids)
    duplicates = sorted(value for value, count in counts.items() if count > 1)
    if duplicates:
        raise SystemExit(f"duplicate page IDs: {duplicates}")
    targets = re.findall(r'href="#([^"]+)"', page)
    missing = sorted(set(targets) - set(ids))
    if missing:
        raise SystemExit(f"missing internal targets: {missing}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out")
    parser.add_argument("--print-output", action="store_true")
    args = parser.parse_args()

    config_data = config(GUIDE / "guide.json")
    out = Path(args.out) if args.out else REPO / config_data["output"]

    if args.print_output:
        print(out)
        return

    annotations_data = annotations(GUIDE / "annotations.json")
    seen = set()
    focus_rows = {}
    prism_components = []
    revision = git("rev-parse", "HEAD")

    paths = sorted((GUIDE / "chapters").glob("*.html"))
    ids = {}
    for number, path in enumerate(paths, start=1):
        meta = META.search(path.read_text(encoding="utf-8"))
        if not meta:
            raise SystemExit(f"{path.name}: missing <!-- chapter: id | title --> header")
        ids[number] = meta.group(1)

    chapters, toc = [], []
    for number, path in enumerate(paths, start=1):
        text = path.read_text(encoding="utf-8")
        chapter_id, title = META.search(text).groups()
        text = CODE.sub(lambda m: render_code(m, path.name, annotations_data, seen, revision, focus_rows, config_data, prism_components), text)
        text = link_chapters(text, ids, path.name)
        text = text.replace("@@N@@", str(number))
        chapters.append(text)
        toc.append(f'<li><a href="#{chapter_id}"><span class="n">{number}</span>{title}</a></li>')

    if seen != set(annotations_data):
        raise SystemExit(f"unused annotations: {sorted(set(annotations_data) - seen)}")

    page = (GUIDE / "page.html").read_text(encoding="utf-8")
    page = page.replace("@@TITLE@@", config_data["title"]).replace("@@EYEBROW@@", config_data["eyebrow"])
    page = page.replace("@@REPO_NAME@@", config_data["repository"].rsplit("/", 1)[-1])
    prism_tags = "\n".join(
        f'<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/{component}.min.js"></script>'
        for component in prism_components
    )
    page = page.replace("@@PRISM_COMPONENTS@@", prism_tags)
    page = page.replace("@@TOC@@", "\n".join(toc)).replace("@@CHAPTERS@@", "\n".join(chapters))
    page = resolve_focus_links(page, annotations_data, focus_rows)
    page = page.replace("@@REPO_SHA@@", git("rev-parse", "--short", "HEAD"))
    validate_page_links(page)
    leftover = re.findall(r"@@[A-Z_]+[^@]*@@", page)
    if leftover:
        raise SystemExit(f"unresolved placeholders: {leftover[:5]}")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out} ({len(chapters)} chapters, {len(page) // 1024} KiB)")


if __name__ == "__main__":
    main()
