import argparse
import json
import re
import subprocess
from pathlib import Path

from pr_body import unchecked_tasks


FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})completion\s*$", re.IGNORECASE)
SHA = re.compile(r"[0-9a-f]{40}")


class CompletionError(RuntimeError):
    pass


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def visible_tasks(markdown):
    return unchecked_tasks(markdown)


def completion_document(goal):
    try:
        body = Path(goal).read_text(encoding="utf-8")
    except OSError as error:
        raise CompletionError(f"completion goal could not be read: {error}") from error
    blocks = []
    lines = re.sub(r"<!--[\s\S]*?(?:-->|$)", "", body.lstrip("\ufeff")).splitlines()
    index = 0
    outer = None
    while index < len(lines):
        fence = re.match(r"^ {0,3}(`{3,}|~{3,})", lines[index])
        if outer is not None:
            if fence and fence.group(1)[0] == outer[0] and len(fence.group(1)) >= len(outer) and not lines[index][fence.end():].strip():
                outer = None
            index += 1
            continue
        marker = FENCE.match(lines[index])
        if marker is None:
            if fence:
                outer = fence.group(1)
            index += 1
            continue
        token = marker.group(1)
        end = index + 1
        while end < len(lines):
            close = re.match(r"^ {0,3}(`{3,}|~{3,})\s*$", lines[end])
            if close and close.group(1)[0] == token[0] and len(close.group(1)) >= len(token):
                break
            end += 1
        if end == len(lines):
            raise CompletionError("completion fence is not closed")
        try:
            blocks.append(json.loads("\n".join(lines[index + 1:end])))
        except json.JSONDecodeError as error:
            raise CompletionError(f"completion JSON is invalid: {error.msg}") from error
        index = end + 1
    if len(blocks) != 1:
        raise CompletionError("goal requires exactly one completion JSON fence")
    return body, blocks[0]


def identity(value, name):
    if not isinstance(value, dict) or set(value) != {"repository", "pr", "head"}:
        raise CompletionError(f"{name} requires repository, pr, and head")
    if not nonempty(value["repository"]) or type(value["pr"]) is not int or value["pr"] < 1:
        raise CompletionError(f"{name} has an invalid repository or PR")
    if not isinstance(value["head"], str) or SHA.fullmatch(value["head"]) is None:
        raise CompletionError(f"{name} requires a forty-character head SHA")
    return {"repository": value["repository"].strip(), "pr": value["pr"], "head": value["head"]}


def bound_identity(binding):
    if binding is None:
        return None
    if not isinstance(binding, dict):
        raise CompletionError("runtime delivery binding is unreadable")
    value = {
        "repository": binding.get("repository", binding.get("repo")),
        "pr": binding.get("pr", binding.get("pr_number")),
        "head": binding.get("head", binding.get("remote_head_sha")),
    }
    return identity(value, "runtime delivery binding")


def validate_document(document):
    if not isinstance(document, dict) or set(document) != {"outcome", "acceptance", "deliveries", "open_tasks"}:
        raise CompletionError("completion JSON requires outcome, acceptance, deliveries, and open_tasks")
    if not nonempty(document["outcome"]):
        raise CompletionError("completion outcome is required")
    acceptance = document["acceptance"]
    if not isinstance(acceptance, list) or not acceptance:
        raise CompletionError("completion acceptance is required")
    seen = set()
    pending = []
    for item in acceptance:
        if not isinstance(item, dict) or set(item) != {"id", "criterion", "evidence", "owner", "next_action"}:
            raise CompletionError("completion acceptance has an invalid shape")
        if not nonempty(item["id"]) or not nonempty(item["criterion"]):
            raise CompletionError("completion acceptance requires id and criterion")
        if item["id"] in seen:
            raise CompletionError("completion acceptance ids must be unique")
        seen.add(item["id"])
        if not isinstance(item["evidence"], list):
            raise CompletionError("completion acceptance evidence must be a list")
        for evidence in item["evidence"]:
            if not isinstance(evidence, dict) or set(evidence) != {"source", "result"}:
                raise CompletionError("completion evidence requires source and result")
            if not nonempty(evidence["source"]) or not nonempty(evidence["result"]):
                raise CompletionError("completion evidence source and result are required")
        if not item["evidence"]:
            if not nonempty(item["owner"]) or not nonempty(item["next_action"]):
                raise CompletionError("pending completion acceptance requires owner and next_action")
            pending.append({"id": item["id"], "text": item["criterion"], "owner": item["owner"], "next_action": item["next_action"]})
    deliveries = []
    identities = set()
    if not isinstance(document["deliveries"], list):
        raise CompletionError("completion deliveries must be a list")
    for item in document["deliveries"]:
        entry = identity(item, "completion delivery")
        key = tuple(entry.values())
        if key in identities:
            raise CompletionError("completion deliveries must be unique")
        identities.add(key)
        deliveries.append(entry)
    if not isinstance(document["open_tasks"], list):
        raise CompletionError("completion open_tasks must be a list")
    tasks = []
    task_keys = set()
    for item in document["open_tasks"]:
        if not isinstance(item, dict) or set(item) != {"repository", "pr", "head", "text", "owner", "next_action"}:
            raise CompletionError("completion open task has an invalid shape")
        entry = identity({key: item[key] for key in ("repository", "pr", "head")}, "completion open task")
        if any(not nonempty(item[key]) for key in ("text", "owner", "next_action")):
            raise CompletionError("completion open task requires text, owner, and next_action")
        key = (*entry.values(), item["text"])
        if key in task_keys:
            raise CompletionError("completion open tasks must be unique")
        task_keys.add(key)
        tasks.append({**entry, "text": item["text"], "owner": item["owner"], "next_action": item["next_action"]})
    return acceptance, deliveries, pending, tasks


def forge_state(delivery, root):
    result = subprocess.run(
        ["gh", "pr", "view", str(delivery["pr"]), "--repo", delivery["repository"],
         "--json", "number,headRefOid,state,body"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        raise CompletionError(f"could not refresh delivery PR #{delivery['pr']}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise CompletionError(f"delivery PR #{delivery['pr']} returned invalid forge data") from error


def completion_check(goal, bound_delivery=None, root=None, viewer=None):
    body, document = completion_document(goal)
    acceptance, deliveries, pending, open_tasks = validate_document(document)
    required = bound_identity(bound_delivery)
    identities = {tuple(item.values()) for item in deliveries}
    blockers = []
    unresolved = list(pending)
    if required is not None and tuple(required.values()) not in identities:
        blockers.append("bound delivery is absent from completion deliveries")
    if pending:
        blockers.extend(f"acceptance {item['id']} lacks evidence" for item in pending)
    for task in open_tasks:
        blockers.append(f"open task remains: {task['text']}")
        unresolved.append(task)
    for task in visible_tasks(body):
        blockers.append(f"goal task is unchecked: {task}")
    fetched = []
    for delivery in deliveries:
        value = (viewer or forge_state)(delivery, root)
        if not isinstance(value, dict):
            raise CompletionError(f"delivery PR #{delivery['pr']} returned unreadable forge data")
        if value.get("number") != delivery["pr"] or value.get("headRefOid") != delivery["head"]:
            blockers.append(f"delivery PR #{delivery['pr']} identity changed")
        if value.get("state") != "MERGED":
            blockers.append(f"delivery PR #{delivery['pr']} is not merged")
        body = value.get("body")
        if not isinstance(body, str):
            blockers.append(f"delivery PR #{delivery['pr']} body is unreadable")
            body = ""
        for task in unchecked_tasks(body):
            owned = next((item for item in open_tasks if item["repository"] == delivery["repository"]
                          and item["pr"] == delivery["pr"] and item["head"] == delivery["head"]
                          and item["text"] == task), None)
            if owned is None:
                blockers.append(f"delivery PR #{delivery['pr']} unchecked task lacks owner: {task}")
                unresolved.append({**delivery, "text": task, "owner": None, "next_action": None})
            blockers.append(f"delivery PR #{delivery['pr']} has unchecked task: {task}")
        fetched.append({"repository": delivery["repository"], "pr": delivery["pr"], "head": delivery["head"],
                        "state": value.get("state")})
    return {
        "operation": "completion-check",
        "outcome": document["outcome"],
        "ready": not blockers,
        "blockers": blockers,
        "open_tasks": unresolved,
        "deliveries": fetched,
    }


def parser():
    result = argparse.ArgumentParser()
    result.add_argument("--goal", required=True)
    result.add_argument("--root", default=".")
    result.add_argument("--bound-repository")
    result.add_argument("--bound-pr", type=int)
    result.add_argument("--bound-head")
    return result


def main(argv=None):
    arguments = parser().parse_args(argv)
    values = (arguments.bound_repository, arguments.bound_pr, arguments.bound_head)
    if any(value is not None for value in values) and not all(value is not None for value in values):
        raise CompletionError("bound delivery requires repository, pr, and head together")
    binding = None if not all(value is not None for value in values) else {
        "repository": arguments.bound_repository,
        "pr": arguments.bound_pr,
        "head": arguments.bound_head,
    }
    result = completion_check(Path(arguments.goal), binding, Path(arguments.root))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CompletionError as error:
        print(json.dumps({"operation": "completion-check", "ready": False, "error": str(error)}))
        raise SystemExit(2)
