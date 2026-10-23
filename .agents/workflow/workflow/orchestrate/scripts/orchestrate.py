"""Drive dependent worker sessions from one orchestration file (Python 3.9+)."""
import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

VERSION = 1
HOSTS = ("claude", "codex", "subagent")
DONE_WHEN = ("merged", "pushed", "reported")
REPORTS = ("done", "question", "failed", "progress")
TOOLS = ("gh", "git", "launch-claude", "launch-codex", "peer-cli", "codex-followup", "codex", "codex-home",
         "worktree-sweep")
FAILED_CHECKS = {"FAILURE", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED", "STARTUP_FAILURE", "ERROR", "STALE"}
LOCK_SECONDS = 120
STALE_LOCK_SECONDS = 3600
COMMAND_SECONDS = 120
LAUNCH_SECONDS = 600
DROPPED_MERGE_SECONDS = 300


class OrchestrationError(RuntimeError):
    pass


def package_root():
    skill = Path(__file__).resolve().parent.parent
    if skill.parent.name in {"skills", "codex-skills"}:
        return skill.parent.parent
    if skill.parent.name == "workflow" and skill.parents[1].name == "workflow" and skill.parents[2].name == ".agents":
        return skill.parents[3]
    raise OrchestrationError("the script has no supported runtime anchor")


def session_reader():
    path = package_root() / ".agents" / "agent-store" / "runtime" / "reader.py"
    spec = importlib.util.spec_from_file_location("orchestrate_store_reader", path)
    if spec is None or spec.loader is None:
        raise OrchestrationError(f"Agent Store reader is unavailable: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def state_directory():
    override = os.environ.get("AGENT_STATE_DIRECTORY")
    return Path(override) if override else Path.home() / ".agents-state"


def default_file(name):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name or ""):
        raise OrchestrationError("an orchestration name is lowercase letters, digits and hyphens")
    return state_directory() / "orchestrations" / f"{name}.json"


def side_directory(path):
    return Path(path).with_suffix(".d")


def now():
    return time.time()


def same_path_key(value):
    return os.path.normcase(str(Path(value).resolve()))


@contextlib.contextmanager
def locked(path):
    lock = Path(str(path) + ".lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    deadline = now() + LOCK_SECONDS
    while True:
        try:
            descriptor = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            with contextlib.suppress(OSError):
                if now() - lock.stat().st_mtime > STALE_LOCK_SECONDS:
                    lock.unlink()
                    continue
            if now() >= deadline:
                raise OrchestrationError(f"orchestration file is locked: {lock}")
            time.sleep(0.1)
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        os.close(descriptor)
        yield
    finally:
        with contextlib.suppress(OSError):
            lock.unlink()


def load(path):
    try:
        state = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise OrchestrationError(f"no orchestration file at {path}; run init first")
    except ValueError as error:
        raise OrchestrationError(f"orchestration file is not JSON: {error}")
    if state.get("version") != VERSION:
        raise OrchestrationError(f"unsupported orchestration version {state.get('version')!r}")
    return state


def save(path, state):
    path = Path(path)
    staging = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    staging.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(staging, path)


def run(command, cwd=None, timeout=COMMAND_SECONDS):
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=timeout, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as error:
        return 127, "", str(error)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def tool(state, name):
    value = state["tools"].get(name)
    if name in ("gh", "git") and not value:
        return [name]
    if not value:
        return None
    if value.endswith(".py"):
        return [sys.executable, "-B", value]
    return [value]


def git(state, cwd, *args):
    return run(tool(state, "git") + list(args), cwd=cwd)


def gh_json(state, *args, cwd=None):
    code, output, error = run(tool(state, "gh") + list(args), cwd=cwd)
    if code != 0:
        return None, error or output
    try:
        return json.loads(output), None
    except ValueError:
        return None, "gh returned non-JSON output"


def last_json(text):
    with contextlib.suppress(ValueError):
        return json.loads(text)
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line.startswith("{") or line.startswith("["):
            with contextlib.suppress(ValueError):
                return json.loads(line)
    return None


def reports(path, worker_id):
    file = side_directory(path) / "reports" / f"{worker_id}.jsonl"
    found = []
    if file.is_file():
        for line in file.read_text(encoding="utf-8").splitlines():
            with contextlib.suppress(ValueError):
                found.append(json.loads(line))
    return found


def checks_summary(rollup):
    pending, failed = [], []
    for check in rollup or []:
        name = check.get("name") or check.get("context") or "check"
        if check.get("__typename") == "StatusContext" or "state" in check and "status" not in check:
            state = (check.get("state") or "").upper()
            if state in ("PENDING", "EXPECTED"):
                pending.append(name)
            elif state in FAILED_CHECKS:
                failed.append(name)
            continue
        if (check.get("status") or "").upper() != "COMPLETED":
            pending.append(name)
        elif (check.get("conclusion") or "").upper() in FAILED_CHECKS:
            failed.append(name)
    if failed:
        return {"state": "failed", "names": sorted(set(failed))}
    if pending:
        return {"state": "pending", "names": sorted(set(pending))}
    return {"state": "green", "names": []}


def pr_label(state, worker, number):
    repos = {other.get("slug") for other in state["workers"].values()
             if other.get("pr") == number and other.get("slug")}
    if len(repos) > 1 and worker.get("slug"):
        return f"{worker['slug'].split('/')[-1]}#{number}"
    return f"#{number}"


class Observer:
    """Reads registry, process, forge and checkout state; never writes any of them."""

    def __init__(self, path, state, forge=True):
        self.path = path
        self.state = state
        self.forge = forge
        self._peers = None
        self._queried = set()
        self._reader = None

    def reader(self):
        if self._reader is None:
            self._reader = session_reader().ReadOnlyWorkItemStore()
        return self._reader

    def session(self, handle):
        seen = set()
        while handle and handle not in seen:
            seen.add(handle)
            try:
                rows = self.reader().sessions(handles=[handle])
            except Exception as error:
                return {"handle": handle, "error": str(error)}
            if not rows:
                return {"handle": handle, "missing": True}
            row = rows[0]
            if row.get("successor") and row.get("ended_at"):
                handle = row["successor"]
                continue
            return row
        return {"handle": handle, "missing": True}

    def bind_launch(self, worker):
        try:
            target = same_path_key(worker["worktree"])
            rows = [row for row in self.reader().sessions() if row.get("cwd") and same_path_key(row["cwd"]) == target]
        except Exception:
            return None
        child = worker.get("child_pid")
        after = (worker.get("launched_at") or 0) - 5
        for row in sorted(rows, key=lambda item: item.get("started_at") or 0, reverse=True):
            if child and row.get("pid") == child:
                return row["handle"]
        for row in sorted(rows, key=lambda item: item.get("started_at") or 0, reverse=True):
            if row.get("title") == worker["title"] and (row.get("started_at") or 0) >= after:
                return row["handle"]
        return None

    def peers(self, wanted):
        if self._peers is None or not wanted <= self._queried:
            self._peers, self._queried = {}, set(wanted)
            for worker in self.state["workers"].values():
                if worker.get("session") and worker["phase"] != "closed":
                    row = self.session(worker["session"])
                    if row.get("session_id"):
                        self._queried.add(row["session_id"])
            command = tool(self.state, "peer-cli")
            if command and self._queried:
                arguments = ["list", "--all", "--json"]
                for value in sorted(self._queried):
                    arguments += ["--id", value]
                code, output, _ = run(command + arguments)
                values = last_json(output) if code == 0 else None
                for item in values or []:
                    if item.get("session_id"):
                        self._peers[item["session_id"]] = item
        return self._peers

    def alive(self, row):
        if not row or not row.get("session_id"):
            return None
        peer = self.peers({row["session_id"]}).get(row["session_id"])
        return None if peer is None else peer.get("alive")

    def pull_request(self, worker):
        if not self.forge or worker["host"] == "subagent" and not worker.get("branch"):
            return None
        if not worker.get("slug"):
            value, _ = gh_json(self.state, "repo", "view", "--json", "nameWithOwner", cwd=worker["repo"])
            if value:
                worker["slug"] = value["nameWithOwner"]
        if not worker.get("slug"):
            return {"error": "repository has no GitHub identity"}
        fields = "number,state,isDraft,headRefOid,mergedAt,url,reviewDecision,statusCheckRollup,autoMergeRequest"
        target = str(worker["pr"]) if worker.get("pr") else worker.get("branch")
        if not target:
            return None
        value, error = gh_json(self.state, "pr", "view", target, "--repo", worker["slug"], "--json", fields)
        if value is None:
            return None if "no pull requests found" in (error or "").lower() else {"error": error}
        worker["pr"] = value["number"]
        value["checks"] = checks_summary(value.pop("statusCheckRollup", None))
        return value

    def checkout(self, worker):
        location = worker.get("worktree")
        if not location or not Path(location).is_dir():
            return {"exists": False}
        code, porcelain, _ = git(self.state, location, "status", "--porcelain")
        _, unpushed, _ = git(self.state, location, "rev-list", "--count", "HEAD", "--not", "--remotes")
        _, head, _ = git(self.state, location, "rev-parse", "HEAD")
        return {"exists": True, "dirty": code != 0 or bool(porcelain), "head": head,
                "unpushed": int(unpushed) if unpushed.isdigit() else None}

    def observe(self, worker):
        if worker.get("worktree") and not worker.get("session") and worker["host"] != "subagent" \
                and worker["phase"] == "dispatched":
            worker["session"] = self.bind_launch(worker)
        row = self.session(worker["session"]) if worker.get("session") else None
        return {"session": row, "alive": self.alive(row), "pr": self.pull_request(worker),
                "checkout": self.checkout(worker), "reports": reports(self.path, worker["id"])}


def latest_report(observation):
    found = [item for item in observation["reports"] if item.get("status") != "progress"]
    return found[-1] if found else None


def idle(observation):
    row = observation["session"]
    if row is None:
        return False
    return bool(row.get("ended_at")) or row.get("turn_state") == "awaiting_input" or observation["alive"] is False


def finished(worker, observation):
    if worker["phase"] == "closed":
        return True
    report = latest_report(observation)
    pr = observation["pr"] or {}
    if worker["done_when"] == "merged":
        return pr.get("state") == "MERGED"
    if worker["done_when"] == "reported":
        return bool(report) and report.get("status") == "done"
    checkout = observation["checkout"]
    return (bool(report) and report.get("status") == "done" and checkout.get("exists")
            and not checkout.get("dirty") and checkout.get("unpushed") == 0)


def open_decisions(state, worker_id=None):
    return [decision for decision in state["decisions"].values()
            if decision["status"] == "open" and (worker_id is None or decision.get("worker") == worker_id)]


def here(state):
    return state.get("title") or "here"


def sync_decisions(state, worker, observation):
    report = latest_report(observation)
    for index, item in enumerate(observation["reports"]):
        if item.get("status") != "question":
            continue
        key = f"{worker['id']}-q{index + 1}"
        if key not in state["decisions"]:
            state["decisions"][key] = {
                "id": key, "kind": "question", "worker": worker["id"], "status": "open",
                "where": worker["title"] if item.get("where") == "worker" else here(state),
                "question": item.get("text") or "", "say": item.get("reply") or "your answer",
                "created_at": item.get("at") or now()}
    row = observation["session"] or {}
    for decision in open_decisions(state, worker["id"]):
        if decision["kind"] not in ("question", "paste"):
            continue
        if report and report.get("at", 0) > decision["created_at"]:
            decision["status"] = "superseded"
        elif (decision["where"] == worker["title"] and row.get("turn_state") == "working"
              and (row.get("last_activity_at") or 0) > decision["created_at"]):
            decision["status"] = "answered in tab"
    pr = observation["pr"] or {}
    number = pr.get("number")
    if worker["done_when"] != "merged" or not number or worker.get("merge") == "never":
        return
    key = f"merge-{worker['id']}-{number}"
    decision = state["decisions"].get(key)
    ready = (pr.get("state") == "OPEN" and not pr.get("isDraft") and pr["checks"]["state"] == "green"
             and bool(report) and report.get("status") == "done")
    if pr.get("state") == "MERGED":
        if decision and decision["status"] in ("open", "approved"):
            decision["status"] = "executed"
        return
    if decision and decision["status"] == "approved" and decision.get("head") != pr.get("headRefOid"):
        decision.update(status="open", note="new commits since approval; approve the new head",
                        head=pr.get("headRefOid"), requested_head=None)
    elif (decision and decision["status"] == "approved" and decision.get("requested_head") == pr.get("headRefOid")
          and pr.get("state") == "OPEN" and not pr.get("autoMergeRequest")
          and now() - decision.get("requested_at", now()) > DROPPED_MERGE_SECONDS):
        decision.update(status="open", requested_head=None,
                        note="the merge request was dropped (queue ejection or conflict); approve again after checking")
    if not ready:
        if decision and decision["status"] == "open":
            decision["status"] = "withdrawn"
        return
    if decision is None or decision["status"] == "withdrawn":
        state["decisions"][key] = {
            "id": key, "kind": "merge", "worker": worker["id"], "status": "open", "where": here(state),
            "question": f"merge {worker['title']} ({pr.get('url')})",
            "say": f"merge {pr_label(state, worker, number)}", "pr": number, "head": pr.get("headRefOid"),
            "created_at": now()}
    elif decision["status"] == "open":
        decision["head"] = pr.get("headRefOid")


def merge_approved(state, worker, observation):
    pr = observation["pr"] or {}
    for decision in state["decisions"].values():
        if (decision["kind"] != "merge" or decision.get("worker") != worker["id"]
                or decision["status"] != "approved" or decision.get("pr") != pr.get("number")):
            continue
        if decision.get("head") != pr.get("headRefOid") or pr.get("state") != "OPEN":
            continue
        if pr["checks"]["state"] != "green":
            decision["note"] = "waiting for green checks at the approved head"
            continue
        if decision.get("requested_head") == decision["head"]:
            continue
        method = worker.get("merge_method") or "merge"
        code, output, error = run(tool(state, "gh") + [
            "pr", "merge", str(pr["number"]), "--repo", worker["slug"], f"--{method}", "--auto",
            "--match-head-commit", decision["head"]])
        decision["merge_output"] = (output or error)[-2000:]
        if code == 0:
            decision.update(requested_head=decision["head"], requested_at=now(), note="merge requested")
        else:
            decision.update(status="open", requested_head=None,
                            note="merge command failed: " + decision["merge_output"][-300:])
        return {"worker": worker["id"], "pr": pr["number"], "ok": code == 0, "output": decision["merge_output"]}
    return None


def blocked_on(state, worker, observations):
    waiting = []
    for name in worker["depends_on"]:
        other = state["workers"].get(name)
        if other is None or not finished(other, observations[name]):
            waiting.append(name)
    return waiting


def describe(state, worker, observation, observations):
    if worker["phase"] == "closed":
        return "closed", worker.get("close_result") or "", ""
    if worker["phase"] == "failed":
        return "failed", worker.get("failure") or "", "decide whether to relaunch"
    if worker["phase"] == "pending":
        waiting = blocked_on(state, worker, observations)
        if waiting:
            return "pending", "waiting on " + ", ".join(waiting), ""
        return "ready", "", "dispatch on next tick"
    pr = observation["pr"] or {}
    decisions = open_decisions(state, worker["id"])
    report = latest_report(observation)
    done = finished(worker, observation)
    row = observation["session"]
    if row is None and worker["host"] != "subagent":
        return "launching", "session not yet registered", ""
    if row and row.get("missing"):
        return "unknown", "session missing from registry", "adopt or relaunch"
    if decisions:
        first = decisions[0]
        return ("waiting", f"decision: {first['question']}", f"{first['where']}: say \"{first['say']}\"")
    if done:
        return "done", "", "close-out" if worker["host"] != "subagent" else ""
    if pr.get("state") == "OPEN":
        checks = pr["checks"]
        if checks["state"] == "pending":
            return "ci", "checks running: " + ", ".join(checks["names"][:3]), "wait"
        if checks["state"] == "failed":
            return "ci-failed", "failed: " + ", ".join(checks["names"][:3]), "worker fixes and pushes"
        if pr.get("autoMergeRequest"):
            return "merging", "merge queue", "wait"
    if worker["host"] == "subagent":
        return "running", "", "wait for the subagent result"
    if not idle(observation):
        return "working", "", "wait"
    if report and report.get("status") == "failed":
        return "failed", report.get("text") or "", "read the worker's report"
    if report and report.get("status") == "done":
        if worker["done_when"] == "merged" and not pr:
            return "idle", "reported done but no PR found", f"ask {worker['title']} to open its PR"
        if worker.get("merge") == "never":
            return "idle", "awaiting merge by its owner", "wait"
        return "idle", "reported done", "wait"
    return "idle", "no report yet", f"ask {worker['title']} for status"


def closeable(state, worker, observation):
    if worker["phase"] != "dispatched" or not finished(worker, observation):
        return None
    if open_decisions(state, worker["id"]):
        return "open decision"
    checkout = observation["checkout"]
    if checkout.get("exists") and (checkout.get("dirty") or checkout.get("unpushed")):
        return "unpushed or uncommitted work in the worktree"
    if worker["host"] == "subagent":
        return ""
    if not idle(observation):
        return "worker is still working"
    if observation["alive"] is None and not (observation["session"] or {}).get("ended_at"):
        return "liveness unknown; close the tab by hand"
    return ""


def close_out(state, worker, observation):
    reason = closeable(state, worker, observation)
    if reason is None:
        return None
    if reason:
        worker["close_blocker"] = reason
        return None
    row = observation["session"] or {}
    peer = tool(state, "peer-cli")
    result = "closed"
    if worker["host"] != "subagent" and row.get("session_id") and observation["alive"] is not False:
        if row.get("handle") == state.get("orchestrator"):
            worker["close_blocker"] = "refusing to close the orchestrator itself"
            return None
        if peer is None:
            worker["close_blocker"] = "peer-cli is not configured"
            return None
        code, output, error = run(peer + ["close", row["session_id"], "--force"])
        if code != 0:
            worker["close_blocker"] = f"peer-cli refused: {error or output}"
            return None
    sweep = tool(state, "worktree-sweep")
    if sweep and worker.get("worktree"):
        code, output, error = run(sweep + ["--repo", worker["repo"]])
        swept = last_json(output) or {}
        kept = {path: verdict for paths in swept.values() if isinstance(paths, dict)
                for path, verdict in paths.items() if isinstance(verdict, str)}
        verdict = next((value for path, value in kept.items()
                        if same_path_key(path) == same_path_key(worker["worktree"])), None)
        result = f"closed; worktree {verdict}" if verdict else "closed"
    worker.update(phase="closed", closed_at=now(), close_result=result)
    worker.pop("close_blocker", None)
    return {"worker": worker["id"], "result": result}


def default_branch(state, repo):
    code, output, _ = git(state, repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    return output.split("/", 1)[1] if code == 0 and "/" in output else "main"


def make_worktree(state, worker):
    repo = Path(worker["repo"])
    location = Path(worker.get("worktree") or repo / ".worktrees" / worker["branch"].replace("/", "-"))
    if location.is_dir():
        code, branch, _ = git(state, location, "rev-parse", "--abbrev-ref", "HEAD")
        if code != 0 or branch != worker["branch"]:
            raise OrchestrationError(f"{location} exists but is not on {worker['branch']}")
        return location
    git(state, repo, "fetch", "origin", "--prune")
    code, _, _ = git(state, repo, "rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{worker['branch']}")
    if code == 0:
        arguments = ["worktree", "add", str(location), worker["branch"]]
    else:
        arguments = ["worktree", "add", str(location), "-b", worker["branch"],
                     f"origin/{default_branch(state, repo)}"]
    code, output, error = git(state, repo, *arguments)
    if code != 0:
        raise OrchestrationError(f"git worktree add failed: {error or output}")
    return location


def brief(path, state, worker):
    body = Path(worker["prompt_path"]).read_text(encoding="utf-8").rstrip()
    script = Path(__file__).resolve()
    report = f'"{sys.executable}" -B "{script}" report --file "{Path(path).resolve()}" --worker {worker["id"]}'
    if worker["done_when"] == "merged":
        finish = ("Open or update the PR, run the repository's review gates, and wait for its checks "
                  "before reporting done. Do not merge: the orchestrator merges after Tommy approves.")
    elif worker["done_when"] == "pushed":
        finish = "Commit and push your work before reporting done."
    else:
        finish = "Report done with a one-paragraph result."
    lines = [
        body, "", "## Orchestration",
        f"You are worker `{worker['id']}` ({worker['title']}) in orchestration `{state['name']}`.",
        f"Work only in `{worker['worktree']}` on branch `{worker['branch']}`."
        if worker.get("branch") else f"Work only in `{worker['worktree']}`.",
        "Read that repository's README.md and AGENTS.md first and follow its current conventions.",
        finish,
        f"Report done: {report} --status done --text \"<result>\"",
        f"Report a decision you need: {report} --status question --text \"<question>\" --reply \"<exact answer options>\"",
        f"Report a failure: {report} --status failed --text \"<what blocked you>\"",
        "After reporting, stop and wait; the orchestrator closes this session when your work is merged.",
    ]
    target = side_directory(path) / "prompts" / f"{worker['id']}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def launch(path, state, worker):
    if worker["host"] == "subagent":
        location = make_worktree(state, worker) if worker.get("branch") else Path(worker["repo"])
        worker["worktree"] = str(location)
        prompt = brief(path, state, worker)
        worker.update(phase="dispatched", launched_at=now())
        return {"kind": "agent", "worker": worker["id"], "title": worker["title"], "prompt_path": str(prompt),
                "lane": worker.get("lane"), "worktree": str(location)}
    if worker.get("session"):
        return send(path, state, worker, brief_for_existing(path, state, worker))
    launcher = tool(state, f"launch-{worker['host']}")
    if launcher is None:
        raise OrchestrationError(f"launch-{worker['host']} is not configured")
    worker["worktree"] = str(make_worktree(state, worker))
    prompt = brief(path, state, worker)
    command = launcher + ["--working-directory", worker["worktree"], "--prompt-path", str(prompt),
                          "--title", worker["title"]]
    if worker.get("model"):
        command += ["--model", worker["model"]]
        if worker.get("effort"):
            command += ["--effort" if worker["host"] == "claude" else "--reasoning-effort", worker["effort"]]
    else:
        command += ["--lane", worker.get("lane") or "L4"]
    if worker.get("skip_permissions") and worker["host"] == "claude":
        command.append("--dangerously-skip-permissions")
    worker["launched_at"] = now()
    code, output, error = run(command, cwd=worker["worktree"], timeout=LAUNCH_SECONDS)
    receipt = last_json(output) or {}
    if code == 0 and receipt.get("startup") == "verified":
        worker["phase"] = "dispatched"
        status = {}
        with contextlib.suppress(OSError, ValueError, TypeError):
            status = json.loads(Path(receipt["status_path"]).read_text(encoding="utf-8"))
        worker["child_pid"] = status.get("child_pid")
        return {"kind": "launched", "worker": worker["id"], "title": worker["title"]}
    if code == 3:
        worker.update(phase="dispatched", note="startup unconfirmed; do not relaunch")
        return {"kind": "launched", "worker": worker["id"], "title": worker["title"], "unconfirmed": True}
    worker.update(phase="failed", failure=(error or output or f"launcher exit {code}")[-1000:])
    return {"kind": "launch-failed", "worker": worker["id"], "title": worker["title"], "error": worker["failure"]}


def brief_for_existing(path, state, worker):
    if not worker.get("worktree"):
        worker["worktree"] = worker.get("cwd") or worker["repo"]
    return brief(path, state, worker)


def send(path, state, worker, message):
    worker.update(phase="dispatched", launched_at=now())
    if worker["host"] == "codex":
        followup = tool(state, "codex-followup")
        row = Observer(path, state, forge=False).session(worker["session"]) or {}
        if followup and state["tools"].get("codex") and state["tools"].get("codex-home") and row.get("session_id"):
            receipt = side_directory(path) / "receipts" / f"{worker['id']}-{int(now())}.json"
            receipt.parent.mkdir(parents=True, exist_ok=True)
            code, output, _ = run(followup + [
                "--codex", state["tools"]["codex"], "--timeout", "20", "send", "--thread", row["session_id"],
                "--cwd", row.get("cwd") or worker["worktree"], "--codex-home", state["tools"]["codex-home"],
                "--message-file", str(message), "--receipt", str(receipt)])
            status = (last_json(output) or {}).get("status")
            if code == 0 and status in ("delivered", "accepted"):
                return {"kind": "sent", "worker": worker["id"], "title": worker["title"]}
        key = f"{worker['id']}-paste-{int(now())}"
        state["decisions"][key] = {
            "id": key, "kind": "paste", "worker": worker["id"], "status": "open", "where": worker["title"],
            "question": f"paste the prompt into {worker['title']} (Codex follow-up unavailable)",
            "say": f"the contents of {message}", "created_at": now()}
        return {"kind": "paste", "worker": worker["id"], "title": worker["title"], "message_path": str(message)}
    return {"kind": "send", "worker": worker["id"], "title": worker["title"], "message_path": str(message),
            "session": worker["session"]}


def local_fingerprint(worker, observation):
    row = observation["session"] or {}
    return {"phase": worker["phase"], "session": row.get("handle"), "turn": row.get("turn_state"),
            "ended": bool(row.get("ended_at")), "reports": len(observation["reports"])}


def slow_fingerprint(observation):
    pr = observation["pr"] or {}
    return {"alive": observation["alive"], "pr": pr.get("state"), "head": pr.get("headRefOid"),
            "checks": (pr.get("checks") or {}).get("state"), "queued": bool(pr.get("autoMergeRequest"))}


def fingerprint(worker, observation):
    return {"local": local_fingerprint(worker, observation), "slow": slow_fingerprint(observation)}


def render(state, rows, actions):
    lines = []
    widths = (12, 28, 10, 44)
    header = ("worker", "tab", "state", "blocker / next")
    lines.append("  ".join(value.ljust(width) for value, width in zip(header, widths)))
    for row in rows:
        detail = row["blocker"] + (f" -> {row['next']}" if row["next"] else "")
        pr = f" [{row['pr']}]" if row.get("pr") else ""
        values = (row["worker"], row["title"] + pr, row["state"], detail)
        lines.append("  ".join(str(value).ljust(width) for value, width in zip(values, widths)))
    decisions = open_decisions(state)
    lines.append("")
    lines.append("Decisions for Tommy:" if decisions else "Decisions for Tommy: none")
    for index, decision in enumerate(decisions, 1):
        note = f" ({decision['note']})" if decision.get("note") else ""
        lines.append(f"{index}. {decision['where']}: say \"{decision['say']}\" - {decision['question']}{note}"
                     f" [{decision['id']}]")
    for action in actions:
        if action["kind"] in ("send", "agent", "paste", "launch-failed"):
            lines.append(f"Action for the orchestrator: {json.dumps(action, sort_keys=True)}")
    return "\n".join(lines)


def collect(path, state, forge=True):
    observer = Observer(path, state, forge=forge)
    return {name: observer.observe(worker) for name, worker in state["workers"].items()}


def rows_for(state, observations):
    rows = []
    for name, worker in state["workers"].items():
        label, blocker, step = describe(state, worker, observations[name], observations)
        pr = (observations[name]["pr"] or {}).get("number")
        rows.append({"worker": name, "title": worker["title"], "state": label, "blocker": blocker, "next": step,
                     "pr": pr_label(state, worker, pr) if pr else None,
                     "session": (observations[name]["session"] or {}).get("handle")})
    return rows


def tick(path, state, dispatch=True):
    observations = collect(path, state)
    actions = []
    for name, worker in state["workers"].items():
        if worker["phase"] == "dispatched":
            sync_decisions(state, worker, observations[name])
            merged = merge_approved(state, worker, observations[name])
            if merged:
                actions.append(dict(merged, kind="merge"))
    for name, worker in state["workers"].items():
        closed = close_out(state, worker, observations[name])
        if closed:
            actions.append(dict(closed, kind="closed"))
    if dispatch:
        for name, worker in state["workers"].items():
            if worker["phase"] == "pending" and not blocked_on(state, worker, observations):
                try:
                    actions.append(launch(path, state, worker))
                except OrchestrationError as error:
                    worker.update(phase="failed", failure=str(error))
                    actions.append({"kind": "launch-failed", "worker": name, "title": worker["title"],
                                    "error": str(error)})
                observations[name] = Observer(path, state).observe(worker)
    state["fingerprint"] = {name: fingerprint(worker, observations[name])
                            for name, worker in state["workers"].items()}
    state["ticked_at"] = now()
    return rows_for(state, observations), actions


def wait(path, poll, slow_poll, timeout):
    started = now()
    baseline = load(path).get("fingerprint") or {}
    last_slow = 0.0
    while True:
        state = load(path)
        if set(state["workers"]) != set(baseline):
            return {"changed": ["workers"], "timeout": False}
        slow = now() - last_slow >= slow_poll
        observer = Observer(path, state, forge=slow)
        changed = []
        for name, worker in state["workers"].items():
            if worker["phase"] in ("closed", "failed"):
                continue
            if slow:
                observation = observer.observe(worker)
                if slow_fingerprint(observation) != baseline[name].get("slow"):
                    changed.append(name)
                    continue
            else:
                observation = {"session": observer.session(worker["session"]) if worker.get("session") else None,
                               "reports": reports(path, worker["id"])}
                if worker.get("worktree") and not worker.get("session") and worker["phase"] == "dispatched"                         and worker["host"] != "subagent":
                    bound = observer.bind_launch(worker)
                    observation["session"] = observer.session(bound) if bound else None
            if local_fingerprint(worker, observation) != baseline[name].get("local"):
                changed.append(name)
        if slow:
            last_slow = now()
        if changed:
            return {"changed": changed, "timeout": False}
        if now() - started >= timeout:
            return {"changed": [], "timeout": True}
        time.sleep(poll)


def resolve_file(args):
    return Path(args.file).resolve() if args.file else default_file(args.name)


def add_worker(state, args):
    if args.id in state["workers"]:
        raise OrchestrationError(f"worker {args.id} already exists")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", args.id):
        raise OrchestrationError("a worker id is lowercase letters, digits and hyphens")
    if any(worker["title"] == args.title for worker in state["workers"].values()):
        raise OrchestrationError(f"another worker already uses the tab title {args.title!r}")
    depends = [name for name in (args.depends_on or "").split(",") if name]
    unknown = [name for name in depends if name not in state["workers"]]
    if unknown:
        raise OrchestrationError(f"unknown dependency: {', '.join(unknown)}")
    if args.host != "subagent" and not args.branch and not getattr(args, "session", None):
        raise OrchestrationError("a native worker needs --branch for its own worktree")
    return {
        "id": args.id, "title": args.title, "host": args.host, "repo": str(Path(args.repo).resolve()),
        "branch": args.branch, "worktree": None, "lane": args.lane, "model": args.model, "effort": args.effort,
        "skip_permissions": args.skip_permissions, "prompt_path": str(Path(args.prompt).resolve()) if args.prompt else None,
        "depends_on": depends, "done_when": args.done_when, "merge": args.merge, "merge_method": args.merge_method,
        "pr": args.pr, "slug": None, "session": None, "phase": "pending", "added_at": now()}


def command_init(args):
    path = resolve_file(args)
    path.parent.mkdir(parents=True, exist_ok=True)
    with locked(path):
        if path.exists():
            raise OrchestrationError(f"{path} already exists")
        save(path, {"version": VERSION, "name": args.name, "title": args.title, "orchestrator": args.orchestrator,
                    "tools": {}, "workers": {}, "decisions": {}, "fingerprint": {}, "created_at": now()})
    return {"file": str(path)}


def command_configure(args):
    path = resolve_file(args)
    with locked(path):
        state = load(path)
        for pair in args.tool or []:
            name, _, value = pair.partition("=")
            if name not in TOOLS:
                raise OrchestrationError(f"unknown tool {name!r}; expected one of {', '.join(TOOLS)}")
            state["tools"][name] = value or None
        if args.title is not None:
            state["title"] = args.title
        if args.orchestrator is not None:
            state["orchestrator"] = args.orchestrator
        save(path, state)
    missing = [name for name, value in state["tools"].items() if value and name not in ("gh", "git", "codex")
               and not Path(value).exists()]
    return {"tools": state["tools"], "missing": missing}


def command_add(args):
    path = resolve_file(args)
    with locked(path):
        state = load(path)
        worker = add_worker(state, args)
        if worker["prompt_path"] is None:
            raise OrchestrationError("--prompt is required")
        state["workers"][args.id] = worker
        save(path, state)
    return {"worker": args.id}


def command_adopt(args):
    path = resolve_file(args)
    with locked(path):
        state = load(path)
        reader = session_reader().ReadOnlyWorkItemStore()
        rows = [row for row in reader.sessions() if args.session in (row.get("handle"), row.get("session_id"))
                or row.get("title") == args.session]
        live = [row for row in rows if not row.get("ended_at")] or rows
        if len(live) != 1:
            raise OrchestrationError(f"{len(live)} registered sessions match {args.session!r}; use the exact handle")
        row = live[0]
        args.host = row["host"]
        args.repo = args.repo or row.get("cwd")
        args.title = args.title or row.get("title") or row["handle"]
        args.branch = args.branch or row.get("branch")
        worker = add_worker(state, args)
        worker.update(session=row["handle"], worktree=row.get("cwd"), cwd=row.get("cwd"))
        worker["phase"] = "pending" if worker["prompt_path"] else "dispatched"
        state["workers"][args.id] = worker
        save(path, state)
    return {"worker": args.id, "session": row["handle"], "phase": worker["phase"]}


def command_report(args):
    path = resolve_file(args)
    state = load(path)
    if args.worker not in state["workers"]:
        raise OrchestrationError(f"unknown worker {args.worker}")
    file = side_directory(path) / "reports" / f"{args.worker}.jsonl"
    file.parent.mkdir(parents=True, exist_ok=True)
    entry = {"status": args.status, "text": args.text, "reply": args.reply, "where": args.where, "at": now()}
    with open(file, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return {"worker": args.worker, "status": args.status}


def command_ask(args):
    path = resolve_file(args)
    with locked(path):
        state = load(path)
        if args.worker and args.worker not in state["workers"]:
            raise OrchestrationError(f"unknown worker {args.worker}")
        key = args.id or f"ask-{len(state['decisions']) + 1}"
        state["decisions"][key] = {"id": key, "kind": "question", "worker": args.worker, "status": "open",
                                   "where": args.where or here(state), "question": args.question,
                                   "say": args.say, "created_at": now()}
        save(path, state)
    return {"decision": key}


def command_answer(args):
    path = resolve_file(args)
    with locked(path):
        state = load(path)
        decision = state["decisions"].get(args.id)
        if decision is None or decision["status"] != "open":
            raise OrchestrationError(f"no open decision {args.id}")
        decision.update(status="approved" if decision["kind"] == "merge" else "answered",
                        answer=args.text, answered_at=now())
        decision.pop("note", None)
        save(path, state)
    return {"decision": args.id, "status": decision["status"], "head": decision.get("head")}


def command_mark(args):
    path = resolve_file(args)
    with locked(path):
        state = load(path)
        worker = state["workers"].get(args.worker)
        if worker is None:
            raise OrchestrationError(f"unknown worker {args.worker}")
        if args.state == "pending":
            worker.update(phase="pending", failure=None, session=None if not args.keep_session else worker["session"])
        else:
            worker.update(phase=args.state)
        save(path, state)
    return {"worker": args.worker, "phase": worker["phase"]}


def command_status(args):
    path = resolve_file(args)
    state = load(path)
    observations = collect(path, state)
    for name, worker in state["workers"].items():
        if worker["phase"] == "dispatched":
            sync_decisions(state, worker, observations[name])
    return {"rows": rows_for(state, observations), "decisions": open_decisions(state), "actions": [],
            "_state": state}


def command_tick(args):
    path = resolve_file(args)
    with locked(path):
        state = load(path)
        rows, actions = tick(path, state, dispatch=not args.no_dispatch)
        save(path, state)
    return {"rows": rows, "decisions": open_decisions(state), "actions": actions, "_state": state}


def command_wait(args):
    return wait(resolve_file(args), args.poll, args.slow_poll, args.timeout)


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--file")
    common.add_argument("--name", default="default")
    common.add_argument("--json", action="store_true")
    commands = root.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", parents=[common])
    init.add_argument("--title")
    init.add_argument("--orchestrator")

    configure = commands.add_parser("configure", parents=[common])
    configure.add_argument("--tool", action="append", metavar="NAME=PATH")
    configure.add_argument("--title")
    configure.add_argument("--orchestrator")

    for name in ("add", "adopt"):
        sub = commands.add_parser(name, parents=[common])
        sub.add_argument("--id", required=True)
        sub.add_argument("--title", required=name == "add")
        sub.add_argument("--repo", required=name == "add")
        sub.add_argument("--branch")
        sub.add_argument("--prompt", required=name == "add")
        sub.add_argument("--lane", choices=("L1", "L2", "L3", "L4", "L5", "L6"))
        sub.add_argument("--model")
        sub.add_argument("--effort")
        sub.add_argument("--skip-permissions", action="store_true")
        sub.add_argument("--depends-on")
        sub.add_argument("--done-when", choices=DONE_WHEN, default="merged")
        sub.add_argument("--merge", choices=("ask", "never"), default="ask")
        sub.add_argument("--merge-method", choices=("merge", "squash", "rebase"), default="merge")
        sub.add_argument("--pr", type=int)
        if name == "add":
            sub.add_argument("--host", choices=HOSTS, required=True)
        else:
            sub.add_argument("--session", required=True)

    report = commands.add_parser("report", parents=[common])
    report.add_argument("--worker", required=True)
    report.add_argument("--status", choices=REPORTS, required=True)
    report.add_argument("--text", default="")
    report.add_argument("--reply")
    report.add_argument("--where", choices=("here", "worker"), default="here")

    ask = commands.add_parser("ask", parents=[common])
    ask.add_argument("--id")
    ask.add_argument("--worker")
    ask.add_argument("--where")
    ask.add_argument("--question", required=True)
    ask.add_argument("--say", required=True)

    answer = commands.add_parser("answer", parents=[common])
    answer.add_argument("id")
    answer.add_argument("--text", default="")

    mark = commands.add_parser("mark", parents=[common])
    mark.add_argument("worker")
    mark.add_argument("state", choices=("pending", "failed", "closed"))
    mark.add_argument("--keep-session", action="store_true")

    commands.add_parser("status", parents=[common])
    tick_parser = commands.add_parser("tick", parents=[common])
    tick_parser.add_argument("--no-dispatch", action="store_true")

    wait_parser = commands.add_parser("wait", parents=[common])
    wait_parser.add_argument("--poll", type=float, default=5.0)
    wait_parser.add_argument("--slow-poll", type=float, default=60.0)
    wait_parser.add_argument("--timeout", type=float, default=3600.0)
    return root


HANDLERS = {"init": command_init, "configure": command_configure, "add": command_add, "adopt": command_adopt,
            "report": command_report, "ask": command_ask, "answer": command_answer, "mark": command_mark,
            "status": command_status, "tick": command_tick, "wait": command_wait}


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        result = HANDLERS[args.command](args)
    except OrchestrationError as error:
        print(f"orchestrate: {error}", file=sys.stderr)
        return 2
    state = result.pop("_state", None)
    if args.json or state is None:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render(state, result["rows"], result["actions"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
