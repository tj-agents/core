import re


HEADING = re.compile(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$")
LABEL = re.compile(r"^ {0,3}\*\*([^*\n]+?:)\*\*(?:\s+(.*)|\s*)$")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
FOOTER = re.compile(
    r"^(?:generated (?:with|by)\b|co-authored-by:|🤖\s*generated\b|authored (?:with|by)\b)",
    re.IGNORECASE,
)
LIST_ITEM = re.compile(r"^(\s*)(?:[-+*]|\d+[.)])\s+(.+?)\s*$")


def unchecked_tasks(body):
    if not isinstance(body, str):
        return []
    tasks = []
    fence = None
    list_indents = []
    visible = re.sub(r"<!--[\s\S]*?(?:-->|$)", "", body.lstrip("\ufeff"))
    for line in visible.splitlines():
        marker = FENCE.match(line)
        if marker:
            if not line.startswith((" ", "\t")):
                list_indents = []
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not line[marker.end():].strip():
                fence = None
            continue
        if fence is not None:
            continue
        if line.lstrip().startswith(">"):
            list_indents = []
            continue
        if not line.strip():
            continue
        item = LIST_ITEM.match(line)
        if item:
            indent = len(item.group(1).expandtabs(4))
            nested = any(value < indent for value in list_indents)
            if indent < 4 or nested:
                list_indents = [value for value in list_indents if value < indent] + [indent]
                text = item.group(2)
                if text.startswith("[ ] "):
                    tasks.append(text[4:])
            continue
        if not line.startswith((" ", "\t")):
            list_indents = []
    return tasks


def validate_pr_body(body):
    if not isinstance(body, str):
        return {"valid": False, "errors": ["PR body is missing or unreadable"]}
    sections = {"what": [], "why": []}
    found = set()
    current = None
    fence = None
    visible = re.sub(r"<!--[\s\S]*?(?:-->|$)", "", body.lstrip("\ufeff"))
    for line in visible.splitlines():
        marker = FENCE.match(line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not line[marker.end():].strip():
                fence = None
            continue
        if fence is not None or line.expandtabs(4).startswith("    ") or line.lstrip().startswith(">"):
            continue
        heading = HEADING.match(line)
        label = LABEL.match(line)
        if heading or label:
            name = (heading or label).group(1).strip().rstrip(":").strip().lower()
            current = name if name in sections else None
            if current:
                found.add(current)
                if label and label.group(2):
                    text = label.group(2).strip()
                    if not FOOTER.match(text) and re.search(r"\w", text):
                        sections[current].append(text)
            continue
        text = line.strip().strip("*_~ ")
        text = re.sub(r"^(?:[-+*]|\d+[.)])\s*(?:\[[ xX]\])?\s*", "", text)
        if current and not FOOTER.match(text) and re.search(r"[\w]", text):
            sections[current].append(text)
    errors = []
    for name in sections:
        if name not in found:
            errors.append(f"Missing {name.title()} section")
        elif not sections[name]:
            errors.append(f"Empty {name.title()} section")
    return {"valid": not errors, "errors": errors}
