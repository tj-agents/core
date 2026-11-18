"""Report live state of conversation PRs, issues and branches, and stalled sessions."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

PULL = re.compile(
    r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<key>\d+)/?\Z"
)
ISSUE = re.compile(
    r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/issues/(?P<key>\d+)/?\Z"
)
BRANCH = re.compile(r"(?P<owner>[^/\s:]+)/(?P<repo>[^/\s:]+):(?P<key>\S+)\Z")
OPEN_STATES = {"OPEN"}
TOKEN = re.compile(r"[a-z0-9]+")
PATH_SEPARATOR = re.compile(r"[\\/]")
STORE_TIMEOUT_SECONDS = 20
RECOVER_TIMEOUT_SECONDS = 120

Session = dict[str, Any]
GraphQL = Callable[[str], dict[str, Any]]
Recorded = Callable[[], list[Session]]
Closed = Callable[[], set[str]]


class CatchUpError(Exception):
    """A live source the report needs could not be read."""


@dataclass(frozen=True)
class Item:
    kind: str
    owner: str
    repo: str
    key: str

    @property
    def reference(self) -> str:
        if self.kind == "branch":
            return f"{self.owner}/{self.repo}:{self.key}"
        path = "pull" if self.kind == "pr" else "issues"
        return f"https://github.com/{self.owner}/{self.repo}/{path}/{self.key}"


def parse(kind: str, value: str) -> Item:
    pattern = {"pr": PULL, "issue": ISSUE, "branch": BRANCH}[kind]
    match = pattern.fullmatch(value.strip())
    if not match:
        raise ValueError(f"Not a GitHub {kind} reference: {value}")
    return Item(kind, match["owner"], match["repo"], match["key"])


PULL_FIELDS = "url title state isDraft mergedAt closedAt headRefName reviewDecision"
ISSUE_FIELDS = "url title state stateReason closedAt"
BRANCH_PULLS = "first: 5, orderBy: {field: CREATED_AT, direction: DESC}"
BRANCH_PULL_FIELDS = "url number title state mergedAt"


def query(items: Sequence[Item]) -> str:
    fields = []
    for index, item in enumerate(items):
        owner, name = json.dumps(item.owner), json.dumps(item.repo)
        if item.kind == "pr":
            body = f"pullRequest(number: {int(item.key)}) {{ {PULL_FIELDS} }}"
        elif item.kind == "issue":
            body = f"issue(number: {int(item.key)}) {{ {ISSUE_FIELDS} }}"
        else:
            ref = json.dumps("refs/heads/" + item.key)
            pulls = f"headRefName: {json.dumps(item.key)}, {BRANCH_PULLS}"
            body = (
                f"ref(qualifiedName: {ref}) {{ name }} "
                f"pullRequests({pulls}) {{ nodes {{ {BRANCH_PULL_FIELDS} }} }}"
            )
        fields.append(
            f"i{index}: repository(owner: {owner}, name: {name}) {{ {body} }}"
        )
    return "query { " + " ".join(fields) + " }"


def gh_graphql(text: str) -> dict[str, Any]:
    completed = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={text}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode != 0:
        raise CatchUpError(completed.stderr.strip() or "gh api graphql failed")
    result: dict[str, Any] = json.loads(completed.stdout)
    return result


def item_state(item: Item, node: dict[str, Any] | None) -> dict[str, Any]:
    state: dict[str, Any] = {"kind": item.kind, "reference": item.reference}
    if node is None:
        return {**state, "state": "MISSING"}
    if item.kind == "pr":
        pull = node.get("pullRequest") or {}
        return {
            **state,
            "state": pull.get("state", "MISSING"),
            "title": pull.get("title"),
            "draft": pull.get("isDraft"),
            "merged_at": pull.get("mergedAt"),
            "review": pull.get("reviewDecision"),
            "branch": pull.get("headRefName"),
        }
    if item.kind == "issue":
        issue = node.get("issue") or {}
        return {
            **state,
            "state": issue.get("state", "MISSING"),
            "title": issue.get("title"),
            "reason": issue.get("stateReason"),
            "closed_at": issue.get("closedAt"),
        }
    pulls = (node.get("pullRequests") or {}).get("nodes") or []
    exists = bool(node.get("ref"))
    open_pulls = [pull for pull in pulls if pull.get("state") in OPEN_STATES]
    branch_state = (
        "OPEN"
        if open_pulls
        else (
            "MERGED"
            if any(p.get("mergedAt") for p in pulls)
            else ("EXISTS" if exists else "DELETED")
        )
    )
    return {
        **state,
        "state": branch_state,
        "exists": exists,
        "branch": item.key,
        "pulls": pulls,
    }


def states(items: Sequence[Item], graphql: GraphQL) -> list[dict[str, Any]]:
    if not items:
        return []
    data = graphql(query(items)).get("data") or {}
    return [item_state(item, data.get(f"i{index}")) for index, item in enumerate(items)]


def subjects_for(
    items: Iterable[dict[str, Any]], extra: Iterable[str]
) -> dict[str, bool]:
    """Map each session subject to whether the work it names is still unfinished.

    A branch is matched by its last segment, which names its worktree; an issue by
    the work-item reference Agent links its sessions to.
    """
    subjects: dict[str, bool] = {}
    for item in items:
        branch = item.get("branch")
        if item["kind"] == "issue":
            issue = parse("issue", item["reference"])
            subject = f"github:github.com/{issue.owner}/{issue.repo}:{issue.key}"
        elif isinstance(branch, str) and branch:
            subject = branch.rsplit("/", 1)[-1]
        else:
            continue
        unfinished = item.get("state") in OPEN_STATES | {"EXISTS"}
        subjects[subject] = subjects.get(subject, False) or unfinished
    for topic in extra:
        subjects.setdefault(topic, False)
    return subjects


def tokens(value: object) -> set[str]:
    return set(TOKEN.findall(str(value or "").casefold()))


def leaf(path: object) -> str:
    return PATH_SEPARATOR.split(str(path or "").rstrip("\\/"))[-1]


def linked_items(session: Mapping[str, Any]) -> list[str]:
    references = []
    for link in session.get("links") or ():
        item = link.get("item") if isinstance(link, dict) else None
        reference = item.get("ref") if isinstance(item, dict) else None
        if isinstance(reference, str):
            references.append(reference)
    return references


def matched_by(subject: str, session: Mapping[str, Any]) -> list[str]:
    if subject in linked_items(session):
        return ["item"]
    fields = {
        "title": tokens(session.get("title")),
        "worktree": tokens(leaf(session.get("worktree"))),
        "cwd": tokens(leaf(session.get("cwd"))),
    }
    wanted = tokens(subject)
    if not wanted or not wanted <= set().union(*fields.values()):
        return []
    return [name for name, found in fields.items() if found & wanted]


def activity(session: Mapping[str, Any]) -> str:
    return str(session.get("ended_at") or session.get("started_at") or "")


def sessions(
    subjects: Mapping[str, bool],
    recorded: Sequence[Session],
    closed: Closed,
    count: int,
) -> list[dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    unfinished: dict[str, bool] = {}
    for subject, open_work in subjects.items():
        matches = sorted(
            (session for session in recorded if matched_by(subject, session)),
            key=activity,
            reverse=True,
        )
        for session in matches[:count]:
            handle = str(session.get("session"))
            entry = found.setdefault(
                handle,
                {
                    "host": session.get("host"),
                    "id": session.get("native_id"),
                    "title": session.get("title"),
                    "activity": activity(session) or None,
                    "items": linked_items(session),
                    "topics": [],
                },
            )
            entry["topics"].append(subject)
            unfinished[handle] = unfinished.get(handle, False) or open_work
    stopped = closed() if found else set()
    for handle, entry in found.items():
        entry["status"] = "closed" if handle in stopped else "live"
        entry["stalled"] = entry["status"] == "closed" and unfinished[handle]
        if entry["stalled"]:
            entry["reopen"] = f"agent:open {handle}"
    return sorted(
        found.values(),
        key=lambda entry: (not entry["stalled"], str(entry["activity"] or "")),
    )


def run_json(command: Sequence[str], timeout: int) -> object:
    executable = shutil.which(command[0])
    if executable is None:
        raise CatchUpError(
            f"{command[0]} is not on PATH; install Agent with tj install"
        )
    shown = " ".join(command)
    try:
        completed = subprocess.run(
            [executable, *command[1:]],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CatchUpError(f"{shown} failed: {error}") from error
    try:
        result: object = json.loads(completed.stdout)
    except ValueError as error:
        detail = completed.stderr.strip() or f"exit {completed.returncode}"
        raise CatchUpError(f"{shown} printed no JSON: {detail}") from error
    return result


def store_sessions() -> list[Session]:
    document = run_json(["agent-store", "sessions"], STORE_TIMEOUT_SECONDS)
    data = document.get("data") if isinstance(document, dict) else None
    recorded = data.get("sessions") if isinstance(data, dict) else None
    if not isinstance(recorded, list):
        raise CatchUpError(f"agent-store sessions failed: {document}")
    return [session for session in recorded if isinstance(session, dict)]


def closed_sessions() -> set[str]:
    """Every recorded session whose agent is not running, by Agent's liveness check."""
    command = ["tj", "recover", "--dry-run", "--older", "--ended"]
    rows = run_json(command, RECOVER_TIMEOUT_SECONDS)
    if not isinstance(rows, list):
        raise CatchUpError(f"{' '.join(command)} did not list sessions: {rows}")
    return {
        row["session"]
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("session"), str)
    }


def report(
    items: Sequence[Item],
    extra_topics: Sequence[str],
    graphql: GraphQL,
    recorded: Recorded,
    closed: Closed,
    count: int,
) -> dict[str, Any]:
    item_states = states(items, graphql)
    subjects = subjects_for(item_states, extra_topics)
    return {
        "items": item_states,
        "sessions": sessions(subjects, recorded() if subjects else [], closed, count),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", action="append", default=[], help="pull request URL")
    parser.add_argument("--issue", action="append", default=[], help="issue URL")
    parser.add_argument(
        "--branch", action="append", default=[], help="owner/repo:branch"
    )
    parser.add_argument(
        "--topic", action="append", default=[], help="extra session-store topic"
    )
    parser.add_argument(
        "--count", type=int, default=10, help="newest sessions kept per subject"
    )
    args = parser.parse_args(argv)
    if args.count < 1:
        parser.error("--count must be positive")
    try:
        items = (
            [parse("pr", value) for value in args.pr]
            + [parse("issue", value) for value in args.issue]
            + [parse("branch", value) for value in args.branch]
        )
        result = report(
            items, args.topic, gh_graphql, store_sessions, closed_sessions, args.count
        )
    except (CatchUpError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
