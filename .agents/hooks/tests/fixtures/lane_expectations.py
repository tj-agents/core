"""What an authored SKILL.md is expected to look like once generated for one harness.

A self-contained skill ships verbatim, with one exception: a `lane:` declaration is resolved into that
harness's own model keys. Every generation-parity test needs the same expectation, so it lives here rather
than being restated -- and restated slightly differently -- in each of them.
"""

import json
import re
from pathlib import Path


LANES = Path(__file__).resolve().parents[3] / "lanes"


def _table(host):
    return json.loads((LANES / f"{host}.json").read_text(encoding="utf-8-sig"))


def generated_payload(authored, host):
    """The authored text as it should appear in `host`'s generated payload."""
    lane = re.search(r"(?m)^lane:[ \t]*(\S+)[ \t]*$", authored)
    if not lane:
        return authored

    table = _table(host)
    rung = table["lanes"][lane.group(1)]
    lines = [f"model: {rung['model']}"]
    # Claude carries the rung's effort in front matter; Codex has no per-skill effort key, so its payload
    # gets the model alone and the rung's effort reaches it through a lane agent instead.
    if host == "claude" and table["effort_key"] in rung:
        lines.append(f"effort: {rung[table['effort_key']]}")
    return re.sub(
        r"(?m)^lane:[ \t]*\S+[ \t]*\r?\n", "\n".join(lines) + "\n", authored, count=1
    )


def authored_skill(name):
    root = Path(__file__).resolve().parents[4]
    matches = [p for scope in ("base", "engineering", "machine")
               for p in (root / ".agents" / scope).rglob("SKILL.md") if p.parent.name == name]
    if len(matches) != 1:
        raise AssertionError(f"Expected one authored owner for {name}: {matches}")
    return matches[0]


def packaged_adapter(root, name, host):
    authored = (Path(root) / f".{host}" / "skills" / name / "SKILL.md").read_text(
        encoding="utf-8"
    )
    return authored.replace("../../../.agents/", "../../.agents/")
