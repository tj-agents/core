"""Report live state of conversation PRs, issues and branches, and stalled sessions."""

from __future__ import annotations

import argparse
import importlib
import json
import re
import subprocess
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PULL = re.compile(
    r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<key>\d+)/?\Z"
)
ISSUE = re.compile(
    r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/issues/(?P<key>\d+)/?\Z"
)
BRANCH = re.compile(r"(?P<owner>[^/\s:]+)/(?P<repo>[^/\s:]+):(?P<key>\S+)\Z")
OPEN_STATES = {"OPEN"}

Search = Callable[[str], list[dict[str, Any]]]
GraphQL = Callable[[str], dict[str, Any]]


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
        raise RuntimeError(completed.stderr.strip() or "gh api graphql failed")
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


def topics_for(
    items: Iterable[dict[str, Any]], extra: Iterable[str]
) -> dict[str, bool]:
    """Map each session-search topic to whether the work it names is still unmerged.

    A branch searches by its last segment: the store matches every topic word, and a
    prefix such as Refactor/ is not stored with the session.
    """
    topics: dict[str, bool] = {}
    for item in items:
        branch = item.get("branch")
        if isinstance(branch, str) and branch:
            topic = branch.rsplit("/", 1)[-1]
            unmerged = item.get("state") in OPEN_STATES | {"EXISTS"}
            topics[topic] = topics.get(topic, False) or unmerged
    for topic in extra:
        topics.setdefault(topic, False)
    return topics


def sessions(topics: dict[str, bool], search: Search) -> list[dict[str, Any]]:
    found: dict[tuple[str, str], dict[str, Any]] = {}
    for topic, unmerged in topics.items():
        for session in search(topic):
            key = (str(session.get("host")), str(session.get("id")))
            entry = found.setdefault(
                key,
                {
                    "host": key[0],
                    "id": key[1],
                    "status": session.get("status"),
                    "activity": session.get("activity"),
                    "work_item": session.get("work_item"),
                    "topics": [],
                    "unmerged": False,
                    "owner": False,
                },
            )
            entry["topics"].append(topic)
            matched = set(session.get("matched_by") or ())
            if matched - {"message"}:
                entry["owner"] = True
                entry["unmerged"] = entry["unmerged"] or unmerged
    for entry in found.values():
        work_item = entry["work_item"] or {}
        active = work_item.get("status") == "active"
        owns = entry["owner"] and (active or entry["unmerged"])
        entry["stalled"] = entry["status"] == "closed" and owns
        if entry["stalled"]:
            entry["reopen"] = f"agent:open {entry['host']}:{entry['id']}"
        del entry["unmerged"], entry["owner"]
    return sorted(
        found.values(),
        key=lambda entry: (not entry["stalled"], str(entry["activity"] or "")),
    )


def agent_runtime() -> Path:
    here = Path(__file__).resolve()
    for root in here.parents:
        for candidate in (
            root / ".agents" / "agent" / "runtime",
            root
            / ".agents"
            / "dependencies"
            / "agent"
            / ".agents"
            / "agent"
            / "runtime",
        ):
            if (candidate / "tj_agent" / "recovery.py").is_file():
                return candidate
    raise RuntimeError(
        f"Agent's tj_agent.recovery runtime was not found relative to {here}."
    )


def recovery_search(count: int) -> Search:
    sys.path.insert(0, str(agent_runtime()))
    recovery = importlib.import_module("tj_agent.recovery")

    def search(topic: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = recovery.search(topic=topic, count=count)
        return result

    return search


def report(
    items: Sequence[Item], extra_topics: Sequence[str], graphql: GraphQL, search: Search
) -> dict[str, Any]:
    item_states = states(items, graphql)
    return {
        "items": item_states,
        "sessions": sessions(topics_for(item_states, extra_topics), search),
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
    parser.add_argument("--count", type=int, default=10)
    args = parser.parse_args(argv)
    try:
        items = (
            [parse("pr", value) for value in args.pr]
            + [parse("issue", value) for value in args.issue]
            + [parse("branch", value) for value in args.branch]
        )
        result = report(items, args.topic, gh_graphql, recovery_search(args.count))
    except (RuntimeError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
