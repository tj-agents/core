r"""PostToolUse/PostToolUseFailure/Stop hook: a red test run selects its own repair loop.

The failure this exists for: over one PR roughly six runs came back red - local integration, local E2E
three times, the merge queue three times - and `failing-tests` was never loaded once. Each time the agent
reported the failure to the human and waited for direction, which is the first thing that skill's own body
prohibits. The human drove the diagnose/fix cycle by hand for about eight hours.

Nothing could have caught it. `.agents/skill-routes.json` is keyed on the PATH BEING WRITTEN, so it cannot
fire on "a run came back red" - there is no write. `always_on_instructions.py` names the skill once at SessionStart,
thousands of turns before the first failure. Every other tooth in this plugin is a PreToolUse block on a
command shape. A red run is the one trigger only visible AFTER the tool ran, so it needs the events that
see a result.

Three registrations, because a red run arrives in three different shapes:

- **PostToolUseFailure** - the runner exited non-zero. A local `dotnet test` or `./scripts/*.ps1` run.
- **PostToolUse** - the command SUCCEEDED and its output reports someone else's failure. `gh run view` /
  `gh pr checks` reading a failed merge-queue run is the whole merge-queue path, and it exits 0.
- **Stop** - the tooth for the actual observed behaviour. An injection at the moment of failure is only a
  prompt; an agent that decides to report and wait never issues another tool call, so nothing else in this
  file would ever see it again. Stop blocks the turn from ending while a red run stands unanswered.

Two shapes are deliberately NOT a red run, and getting either wrong produces a hook that fires constantly
and is therefore ignored:

- **A build, restore or compile error.** `failing-tests` says so in its own description and routes those to
  the ordinary build loop. A run that never produced a test result has nothing to triage. So evidence is
  graded: a counted test failure (`Failed!`, `Failed: 3`, `[FAIL]`, `2 failed`) is red whatever else the log
  says, while a suite-level verdict carrying no count (`TESTS FAILED`) is red only when no build/restore
  error is present - `scripts/test.ps1` prints exactly that verdict for a project that never built.
- **A command that legitimately exits non-zero.** `grep` with no match, `git diff --quiet`, `gh run view` on
  a run still going. So the trigger is the COMMAND SHAPE plus failure evidence in its output, never a
  non-zero exit on its own. A shape this file does not recognise as a test runner is invisible to it.

Fires once per failure, never once per line: one hook invocation is one tool call, the whole output is
matched as a unit, and one message is emitted no matter how many `Failed X` lines it contains.

Tier routing follows `failing-tests`' own table. The tier comes from the command where the command makes it
knowable (`./scripts/e2e.ps1 ui`, a `dotnet test` naming an `*.IntegrationTests` project) and from the
failing job name where the failure came from CI; where neither settles it, an E2E failure routes to
`e2e-debug`, which covers both tiers. A merge-queue run additionally owes `merging`, because the queue's own
state machine is the second thing that session got wrong.

Silent once every owed skill is proven loaded in this session's transcript - the same proof
`skill_router.py` uses, imported rather than reimplemented so the two cannot disagree about what "loaded"
means. Silent in any repo that has not opted into routing, exactly as the instruction injector is.

Contract: exit 0 = say nothing; exit 2 = stderr is fed back to the agent (PostToolUse* cannot block, the
tool already ran). Stop instead prints the `{"decision": "block"}` envelope. Anything unexpected exits 0 -
a broken gate must never wedge a session.
"""

import hashlib
import json
import re
import sys
import tempfile
from collections import namedtuple
from pathlib import Path

import skill_router
from hook_runtime import claim_invocation

# Skill descriptions carry non-ASCII punctuation, and this text is what the agent acts on. Windows
# defaults these streams to cp1252, which renders it as mojibake.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


HOOK_NAME = "red-run-gate"
# Plugin-qualified because both ship from the engineering package, not from this repo's plugin. resolved_skill
# walks every installed skill root, so the qualifier is what stops an unqualified lookup binding to a
# same-named local skill in some other consumer repository.
OWNER_SKILL = "engineering:failing-tests"
QUEUE_SKILL = "engineering:merging"
# Lowercased, and asserted against the manifest matcher: a shell the matcher omits never reaches this
# file, and a shell this file omits is waved through when it does.
SHELL_TOOLS = {"bash", "powershell"}
# Where a harness puts what the tool produced. The command itself is never read as output - a
# `dotnet test --filter Failed` would otherwise be its own failure evidence.
RESULT_KEYS = ("tool_response", "tool_error", "tool_result", "tool_output")

Runner = namedtuple("Runner", "label tier source")

TIER_SKILLS = {
    "unit": (),
    "integration": ("integration-debug",),
    "e2e-api": ("e2e-api-debug",),
    "e2e-ui": ("e2e-ui-debug",),
    "e2e": ("e2e-debug",),
}

_E2E_SCRIPT = re.compile(r"scripts[\\/]e2e\.ps1(?P<rest>[^\r\n;|&]*)", re.I)
_UNIT_SCRIPT = re.compile(r"scripts[\\/]unit\.ps1", re.I)
_INTEGRATION_SCRIPT = re.compile(r"scripts[\\/]integration\.ps1", re.I)
_TEST_SCRIPT = re.compile(r"scripts[\\/]test\.ps1(?P<rest>[^\r\n;|&]*)", re.I)
_LOCAL_PLATFORM_TEST = re.compile(r"scripts[\\/]local-platform\.ps1\s+test\b", re.I)
_DOTNET_TEST = re.compile(r"\bdotnet\s+(?:test|vstest)\b", re.I)
_NODE_TEST = re.compile(
    r"\b(?:npm|pnpm|yarn)\s+(?:run\s+)?test\b"
    r"|\bnpx\s+(?:vitest|jest|playwright)\b"
    r"|\b(?:vitest|jest)\s+run\b"
    r"|\bplaywright\s+test\b"
    r"|\bpytest\b"
    r"|\bpython\s+-m\s+(?:pytest|unittest)\b",
    re.I,
)
_GH_CI_READ = re.compile(r"\bgh\s+(?:run\s+(?:view|list|watch)|pr\s+checks)\b")

# A counted test failure. Red whatever else the log says.
_COUNTED_TEST_FAILURE = (
    re.compile(r"\bFailed!"),
    re.compile(r"\bfailed:\s*(?!0\b)\d+", re.I),
    re.compile(r"\[FAIL\]"),
    re.compile(r"^\s*FAIL\s+\d+\s+of\s+\d+\s+failed", re.M | re.I),
    re.compile(r"\bFAILED:\s*(?!0\b)\d+\s+project\(s\) had test failures", re.I),
    re.compile(r"\b(?!0\b)\d+\s+(?:tests?\s+)?failed\b", re.I),
    re.compile(r"\bTest Run Failed\b", re.I),
)
# A suite-level verdict carrying no count. `scripts/test.ps1` prints it for a project that never built
# too, so it is red only in the absence of a build error.
_SUITE_VERDICT = (
    re.compile(r"\bTESTS FAILED\b", re.I),
    re.compile(r"\bat least one suite did not pass\b", re.I),
)
_BUILD_FAILURE = (
    re.compile(r"\berror\s+(?:CS|MSB|NU|NETSDK|TS|BC|AD)\d+", re.I),
    re.compile(r"\bBuild FAILED\b", re.I),
    re.compile(r"\bThe build failed\b", re.I),
    re.compile(r"\bRestore failed\b", re.I),
    re.compile(r"\bbuild or run failed\b", re.I),
    re.compile(r"^\s*FAILED \(no results\)", re.M | re.I),
    re.compile(r"\bMSB\d{4}\b"),
)
_CI_FAILURE = (
    re.compile(r'"conclusion"\s*:\s*"(?:failure|startup_failure|timed_out|action_required)"', re.I),
    re.compile(r'"state"\s*:\s*"(?:FAILURE|ERROR)"', re.I),
    re.compile(r"^\s*[X×✖✗✘]\s+\S", re.M),
    re.compile(r"\b(?!0\b)\d+\s+failing\b", re.I),
    re.compile(r"^\S[^\r\n]*\bfail\b", re.M | re.I),
    re.compile(r"\bProcess completed with exit code [1-9]"),
)
_CI_FAILED_JOB = (
    re.compile(r"^\s*[X×✖✗✘]\s+(?P<job>[^\r\n]+?)\s+in\s+\d", re.M),
    re.compile(r"^(?P<job>\S[^\r\n\t]*?)[\t ]+fail\b", re.M | re.I),
)
_MERGE_QUEUE = re.compile(r"merge_group|gh-readonly-queue|merge queue", re.I)
_UI_JOB = re.compile(r"\bui\b|browser|playwright|reqnroll", re.I)
_API_JOB = re.compile(r"\bapi\b|service", re.I)
_E2E_JOB = re.compile(r"\be2e\b|end-to-end", re.I)


def harness_of(data):
    """Codex hook payloads carry a turn id; Claude hook payloads do not."""
    return "codex" if ("turn_id" in data or "turnId" in data) else "claude"


def command_text(tool_name, tool_input):
    """The shell text the call ran, or None for a tool this gate has no vocabulary for."""
    if not isinstance(tool_input, dict):
        return None
    if str(tool_name).lower() not in SHELL_TOOLS:
        return None
    for key in ("command", "cmd", "script"):
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(value, list):
            joined = " ".join(str(part) for part in value if isinstance(part, (str, int, float)))
            if joined.strip():
                return joined
    return None


def result_text(data):
    parts = []
    for key in RESULT_KEYS:
        value = data.get(key)
        if value is not None:
            parts.extend(skill_router.strings(value))
    return "\n".join(parts)


def was_interrupted(data):
    """A cancelled run is not a red run - the human stopped it, so no verdict was reached."""
    for key in RESULT_KEYS:
        value = data.get(key)
        if isinstance(value, dict) and value.get("interrupted"):
            return True
    return False


def _e2e_tier(text):
    ui = _UI_JOB.search(text) is not None
    api = _API_JOB.search(text) is not None
    if ui and not api:
        return "e2e-ui"
    if api and not ui:
        return "e2e-api"
    return "e2e"


def _dotnet_tier(command):
    lowered = command.lower()
    if "e2etests.ui" in lowered:
        return "e2e-ui"
    if "e2etests" in lowered:
        return "e2e-api"
    if "integrationtests" in lowered:
        return "integration"
    if "unittests" in lowered or "architecturetests" in lowered:
        return "unit"
    return None


def _suite_tier(rest):
    if re.search(r"\be2e\b", rest, re.I):
        return _e2e_tier(rest)
    if re.search(r"\bintegration\b", rest, re.I):
        return "integration"
    if re.search(r"\bunit\b", rest, re.I):
        return "unit"
    return None


def classify_runner(command):
    """The test runner this command IS, or None. Shape first - a non-zero exit alone means nothing."""
    match = _E2E_SCRIPT.search(command)
    if match:
        return Runner("scripts/e2e.ps1", _e2e_tier(match.group("rest")), "local")
    if _INTEGRATION_SCRIPT.search(command):
        return Runner("scripts/integration.ps1", "integration", "local")
    if _UNIT_SCRIPT.search(command):
        return Runner("scripts/unit.ps1", "unit", "local")
    match = _TEST_SCRIPT.search(command)
    if match:
        return Runner("scripts/test.ps1", _suite_tier(match.group("rest")), "local")
    if _LOCAL_PLATFORM_TEST.search(command):
        return Runner("scripts/local-platform.ps1 test", _dotnet_tier(command), "local")
    if _DOTNET_TEST.search(command):
        return Runner("dotnet test", _dotnet_tier(command), "local")
    if _NODE_TEST.search(command):
        return Runner("the front-end test runner", None, "local")
    if _GH_CI_READ.search(command):
        return Runner("a CI / merge-queue result read", None, "ci")
    return None


def is_red_run(runner, output):
    if runner.source == "ci":
        return any(pattern.search(output) for pattern in _CI_FAILURE)
    if any(pattern.search(output) for pattern in _COUNTED_TEST_FAILURE):
        return True
    if any(pattern.search(output) for pattern in _BUILD_FAILURE):
        return False
    return any(pattern.search(output) for pattern in _SUITE_VERDICT)


def ci_tier(output):
    for pattern in _CI_FAILED_JOB:
        for match in pattern.finditer(output):
            job = match.group("job")
            if _E2E_JOB.search(job):
                return _e2e_tier(job)
            if _UI_JOB.search(job):
                return "e2e-ui"
            if "integration" in job.lower():
                return "integration"
            if "unit" in job.lower():
                return "unit"
    return None


def owed_skills(runner, output):
    tier = runner.tier
    if runner.source == "ci" and tier is None:
        tier = ci_tier(output)
    names = [OWNER_SKILL]
    names.extend(TIER_SKILLS.get(tier, ()))
    if runner.source == "ci" and _MERGE_QUEUE.search(output):
        names.append(QUEUE_SKILL)
    ordered, seen = [], set()
    for name in names:
        if name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


def has_jurisdiction(cwd):
    """Opted in exactly as the router is: the repo's own table, or the shipped registry.

    Carrying the table is the opt-in, not what is in it - an empty `routes` list still means this repo
    asked for the standards corpus, and every rule this gate names is bound to a red run, never a path.
    """
    root = skill_router.find_repo_root(cwd)
    if root is None:
        return False
    try:
        return skill_router.load_routes(root) is not None
    except skill_router.RoutesUnusable:
        return True


def resolve(names, harness):
    """name -> (description, path), with a None description for a skill the harness cannot see."""
    resolved = {}
    for name in names:
        found = skill_router.resolved_skill(name, harness)
        if found is None and ":" in name:
            # Prefer the qualified identity, but never let an uninstalled marketplace disarm the Stop
            # gate: handle_stop releases the turn when the owner cannot be resolved, so a machine
            # without base-agents would end a turn on a red run unchallenged. A repo that still hosts
            # the skill unqualified answers instead.
            found = skill_router.resolved_skill(name.rpartition(":")[2], harness)
        if found is None:
            resolved[name] = (None, None)
        else:
            path, body = found
            resolved[name] = (skill_router.description_of(body), path)
    return resolved


def unproven(names, resolved, data, harness):
    """The owed skills this session's transcript does not prove were loaded.

    No transcript means no proof either way, and an unprovable session still has to be told - so every
    owed name comes back unproven rather than silently trusted.
    """
    codex_skills = []
    if harness == "codex":
        for name, (description, path) in resolved.items():
            if description is None or path is None:
                continue
            try:
                body = Path(path).read_text(encoding="utf-8-sig")
            except OSError:
                continue
            codex_skills.append((name.rpartition(":")[2] or name, path, body))
    outcomes = skill_router.transcript_skill_outcomes(
        data.get("transcript_path") or data.get("transcriptPath"), codex_skills
    )
    if outcomes is None:
        return list(names)
    return [name for name in names if outcomes.get(name.rpartition(":")[2] or name) is not True]


def state_path(session_id):
    key = hashlib.sha256((session_id or "nosession").encode()).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"red-run-gate-{key}.json"


def load_state(session_id):
    try:
        state = json.loads(state_path(session_id).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return state if isinstance(state, dict) else None


def save_state(session_id, state):
    try:
        state_path(session_id).write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        pass  # a gate that cannot persist should still nag, never crash


def clear_state(session_id):
    try:
        state_path(session_id).unlink()
    except OSError:
        pass


def skill_lines(names, resolved, harness):
    lines = []
    for name in names:
        description, path = resolved[name]
        lines.append(f"  * {skill_router.invocable_name(name, path)}")
        if description is None:
            lines.append(
                f"      NOT INSTALLED FOR {harness.upper()} - no SKILL.md is available to the active"
                " harness. Drive the failure to green with the repository's own test guidance and"
                " report the missing skill; it is a deployment fault."
            )
            continue
        lines.append(f"      {description}")
        if harness == "codex" and path is not None:
            lines.append(f"      READ THIS WHOLE FILE: {path}")
    return lines


def first_line(command):
    stripped = (command or "").strip()
    return stripped.splitlines()[0][:300] if stripped else "(command unavailable)"


def failure_message(command, names, resolved, harness):
    lines = [
        "RED RUN - a test run came back red, and the skill that owns the repair loop is not loaded:",
        "",
        f"  {first_line(command)}",
        "",
    ]
    lines.extend(skill_lines(names, resolved, harness))
    lines += [
        "",
        "Invoke the skill(s) above now and drive this run to green: run -> diagnose -> fix -> re-run."
        " Reporting the failure and waiting for direction is the exact behaviour failing-tests exists"
        " to replace. This is a test failure, not a build error - the gate does not fire on those.",
    ]
    return "\n".join(lines)


def stop_message(command, names, resolved, harness):
    lines = [
        "RED RUN - this turn cannot end with a red run nobody has entered the repair loop for:",
        "",
        f"  {first_line(command)}",
        "",
    ]
    lines.extend(skill_lines(names, resolved, harness))
    lines += [
        "",
        "Invoke the skill(s) above and continue the loop. This gate fires once per red run, so if the"
        " human explicitly asked for a status report rather than a fix, say that and stop.",
    ]
    return "\n".join(lines)


def handle_result(data):
    command = command_text(data.get("tool_name"), data.get("tool_input") or {})
    if not command or was_interrupted(data):
        return 0
    runner = classify_runner(command)
    if runner is None:
        return 0
    output = result_text(data)
    if not output or not is_red_run(runner, output):
        return 0
    # After the cheap regex gates, not before: this runs on every shell call in the session, and
    # jurisdiction costs a directory walk and a `.git/config` read.
    if not has_jurisdiction(data.get("cwd") or "."):
        return 0

    harness = harness_of(data)
    names = owed_skills(runner, output)
    resolved = resolve(names, harness)
    session = data.get("session_id") or data.get("sessionId")
    if not unproven(names, resolved, data, harness):
        clear_state(session)
        return 0
    if not claim_invocation(data, HOOK_NAME):
        return 0
    save_state(session, {"command": command, "skills": names, "answered": False})
    sys.stderr.write(failure_message(command, names, resolved, harness))
    return 2


def handle_stop(data):
    if data.get("stop_hook_active") or data.get("stopHookActive"):
        return 0
    session = data.get("session_id") or data.get("sessionId")
    state = load_state(session)
    if not state or state.get("answered"):
        return 0
    names = [name for name in state.get("skills") or [] if isinstance(name, str)]
    if not names:
        clear_state(session)
        return 0
    if not has_jurisdiction(data.get("cwd") or "."):
        return 0

    harness = harness_of(data)
    resolved = resolve(names, harness)
    if resolved.get(OWNER_SKILL, (None, None))[0] is None:
        # Nothing to load: blocking the turn on a skill this harness cannot see only wedges it.
        clear_state(session)
        return 0
    # The turn is held on the parent skill alone. A tier procedure applies only when its runner and
    # harness match the red run, which this file cannot judge - so it is named, never made a condition.
    if OWNER_SKILL not in unproven([OWNER_SKILL], resolved, data, harness):
        clear_state(session)
        return 0
    if not claim_invocation(data, HOOK_NAME):
        return 0

    state["answered"] = True
    save_state(session, state)
    json.dump(
        {
            "decision": "block",
            "reason": stop_message(state.get("command") or "", names, resolved, harness),
        },
        sys.stdout,
    )
    sys.stdout.write("\n")
    return 0


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    if not isinstance(data, dict):
        return 0
    event = data.get("hook_event_name") or data.get("hookEventName") or ""
    if event == "Stop":
        return handle_stop(data)
    return handle_result(data)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
