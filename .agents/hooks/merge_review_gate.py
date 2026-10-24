r"""Shared review-currency checks for a PR merge.

`auto_merge.py` and `workflow_ops.py` both need to know whether a review work order is
complete, current and clean for the exact head being merged, and whether that head touches
security-sensitive paths needing a current `**Security-reviewed up to commit:** \`<sha>\``
marker too — stamped by `review` Stage 6 after its host security review.

A repo opts in by carrying `.agents/merge-gate.json`, which also names the repo's own
security-sensitive paths — its inventory, rather than this module's. The generic patterns
below (workflows, auth/secret vocabulary) apply everywhere and stay here.
"""

import json
import re
from pathlib import Path

from hook_runtime import run_command


_GIT_CWD = ["."]


def git(*args):
    return run_command(
        ["git", *args], capture_output=True, text=True, check=True, cwd=_GIT_CWD[0]
    ).stdout.strip()


CONFIG_FILE = ".agents/merge-gate.json"

# Paths whose change makes a diff security-sensitive — a merge touching any of
# these needs a current `Security-reviewed up to commit:` marker too. Kept
# targeted (concrete high-value areas) so unrelated merges are never blocked.
# These hold in any repo; a repo's own service and project names go in its
# CONFIG_FILE under `security_paths`.
_SECURITY_PATTERNS = (
    re.compile(r"^\.github/workflows/"),
    re.compile(r"(?:^|/)\.agents/settings\.json$", re.IGNORECASE),
    re.compile(r"(?i)(authoriz|authentic|credential|\bsecret|password|apikey|api_key)"),
)


class ConfigUnusable(Exception):
    """The repo opted into the gate and the table cannot be read. Never silently ignored."""


def find_config(cwd):
    """The opted-in repo root at or above `cwd`, or None. Walking up rather than asking git
    keeps a worktree, a submodule and a plain checkout on the same answer."""
    try:
        base = Path(cwd).resolve()
    except OSError:
        return None
    for candidate in (base, *base.parents):
        if (candidate / CONFIG_FILE).is_file():
            return candidate / CONFIG_FILE
    return None


def security_patterns(config_path):
    """The generic patterns plus the repo's own. A present but broken table is a loud stop:
    failing open here would leave the gate inert while looking wired."""
    patterns = list(_SECURITY_PATTERNS)
    try:
        parsed = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ConfigUnusable(f"{CONFIG_FILE} exists but could not be read: {error}") from error
    declared = parsed.get("security_paths", [])
    if not isinstance(declared, list):
        raise ConfigUnusable(f"{CONFIG_FILE} `security_paths` must be a list.")
    for entry in declared:
        try:
            patterns.append(re.compile(entry))
        except (TypeError, re.error) as error:
            raise ConfigUnusable(f"{CONFIG_FILE} `security_paths` entry {entry!r}: {error}") from error
    return patterns


def touches_security(changed_paths, patterns=_SECURITY_PATTERNS):
    for path in changed_paths:
        for pat in patterns:
            if pat.search(path):
                return path
    return None


def review_only(base, head):
    """True when everything between base and head touched reviews/ alone.

    Stamping the marker is itself a commit, so a review can never be stamped AT the
    commit that contains it. Demanding marker == head therefore blocks every honestly
    reviewed PR, which is why this gate could not be satisfied from any checkout.
    Nothing reviewable changed, so the review is still current.
    """
    try:
        changed = git("diff", "--name-only", base + ".." + head).splitlines()
    except Exception:  # noqa: BLE001 - unresolvable range -> treat as stale, fail closed
        return False
    return bool(changed) and all(x.startswith("reviews/") for x in changed)


def work_order_metadata_lines(review):
    fence = None
    for line in review.splitlines():
        spaces = len(line) - len(line.lstrip(" "))
        stripped = line[spaces:]
        marker_match = re.match(r"(`{3,}|~{3,})", stripped) if spaces <= 3 else None
        if marker_match:
            marker = marker_match.group(1)
            suffix = stripped[len(marker):]
            if fence is None:
                fence = (marker[0], len(marker))
            elif (
                marker[0] == fence[0]
                and len(marker) >= fence[1]
                and not suffix.strip()
            ):
                fence = None
            continue
        if fence is None and spaces < 4 and not line.startswith("\t"):
            yield line


def work_order_field(review, label):
    prefix = f"**{label}:**"
    lines = [
        line
        for line in work_order_metadata_lines(review)
        if line.lstrip().startswith(prefix)
    ]
    if not lines:
        return None
    if len(lines) != 1:
        return "invalid"
    match = re.fullmatch(re.escape(prefix) + r"\s*`([^`]+)`\s*", lines[0])
    return match.group(1).casefold() if match else "invalid"


def work_order_sha_field(review, label):
    prefix = f"**{label}:**"
    lines = [
        line
        for line in work_order_metadata_lines(review)
        if line.lstrip().startswith(prefix)
    ]
    if not lines:
        return None
    if len(lines) != 1:
        return "invalid"
    match = re.fullmatch(
        re.escape(prefix) + r"\s*`([0-9a-fA-F]{7,40})`(?:\s+.*)?",
        lines[0],
    )
    return match.group(1).lower() if match else "invalid"


def review_status(review):
    return work_order_field(review, "Review status")


def review_judgment(review):
    return work_order_field(review, "Judgment")


def staged_work_order(review):
    headings = {
        "## Coverage",
        "## Rules manifest",
        "## Cross-area notes",
        "## Parent finalization",
    }
    for line in work_order_metadata_lines(review):
        stripped = line.strip()
        if stripped in headings or re.match(
            r"^## Review pass\b.*\bstaged(?::|$)", stripped
        ):
            return True
    return False


def review_completion_problem(review):
    status = review_status(review)
    judgment = review_judgment(review)
    notes_status = work_order_field(review, "Cross-area notes status")
    summary_status = work_order_field(review, "Parent summary status")
    if status is None:
        return "has no `Review status`"
    if status != "complete":
        return "has review status '" + status + "'"
    if judgment not in ("approved", "changes-requested"):
        return "has no valid final parent judgment"
    if staged_work_order(review) or notes_status is not None or summary_status is not None:
        if notes_status != "complete" or summary_status != "complete":
            return "has incomplete parent finalization state"
    return None


def unresolved_review_items(review):
    return [
        line.strip()
        for line in review.splitlines()
        if re.match(r"^\s*-\s*\[(?:\s|~)\]", line)
    ]


def security_no_longer_covered(marker, head, patterns, work_order=None):
    """True when a security-sensitive path changed between the security marker and head.

    Asking instead whether ANY commit landed leaves the gate with no legal exit: an ordinary doc or
    ledger commit makes the marker stale, while the review procedure runs its security layer only for
    a security-sensitive range and so never re-stamps it. Sensitive paths untouched since the security
    review are still covered by it.

    `work_order` — this branch's own `reviews/<slug>.md` and nothing else — is excluded for the same
    reason `review_only` exists one layer up, and the self-reference bites harder here. That path is
    derived from the branch slug, so a branch named for the thing it fixes — Fix/CredentialScoping,
    Fix/AuthenticationRetry — writes `credential` or `authentic` into the artifact's own path, where
    the generic vocabulary matches it. Stamping the marker is itself a commit to that path, so
    stamping restales the marker, and the branch cannot be merged from any checkout. A review
    artifact is the evidence of a review, never the subject of one.

    Exactly that one path, never the `reviews/` directory: a prefix match would also excuse
    `reviews/rotate-credentials.py`, or another branch's work order arriving on a merge from main,
    and would put anything a writer chose to place under `reviews/` permanently beyond staleness
    detection once a first marker existed.
    """
    try:
        changed = git("diff", "--name-only", marker + ".." + head).splitlines()
    except Exception:  # noqa: BLE001 - unresolvable range -> fail closed
        return True
    reviewable = [path for path in changed if path != work_order]
    return touches_security(reviewable, patterns) is not None
