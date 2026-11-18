"""Workflow catch-up: live item states and stalled sessions."""

import json
import os
import runpy
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ".agents/workflow/utility/catch-up/scripts/catch_up.py"
PACKAGED_SCRIPT = "skills/catch-up/scripts/catch_up.py"

PR = "https://github.com/tj-agents/core/pull/551"
ISSUE = "https://github.com/tj-agents/personal/issues/49"
BRANCH = "tj-agents/template:Refactor/SubjectSkillLayout"


def graphql_response(text: str) -> dict[str, Any]:
    assert text.count("repository(") == 3
    return {
        "data": {
            "i0": {
                "pullRequest": {
                    "state": "MERGED",
                    "title": "Add catch-up",
                    "isDraft": False,
                    "mergedAt": "2026-11-03T12:00:00Z",
                    "reviewDecision": "APPROVED",
                    "headRefName": "Feature/CatchUp",
                }
            },
            "i1": {
                "issue": {
                    "state": "OPEN",
                    "title": "Approval command",
                    "stateReason": None,
                    "closedAt": None,
                }
            },
            "i2": {
                "ref": {"name": "Refactor/SubjectSkillLayout"},
                "pullRequests": {
                    "nodes": [
                        {
                            "url": "https://github.com/tj-agents/template/pull/56",
                            "number": 56,
                            "state": "OPEN",
                            "mergedAt": None,
                        }
                    ]
                },
            },
        }
    }


def session(
    handle: str,
    *,
    worktree: str | None = None,
    title: str = "",
    links: tuple[str, ...] = (),
    started_at: str = "2026-11-01T00:00:00Z",
) -> dict[str, Any]:
    host, native_id = handle.split(":", 1)
    return {
        "session": handle,
        "host": host,
        "native_id": native_id,
        "title": title,
        "worktree": worktree,
        "cwd": worktree or "C:\\Users\\someone\\source\\repos\\notes",
        "state": "active",
        "started_at": started_at,
        "ended_at": None,
        "links": [{"item": {"ref": ref}, "role": "owner"} for ref in links],
    }


RECORDED = [
    session(
        "codex:01a187bc",
        worktree="C:\\Users\\someone\\source\\repos\\template\\.worktrees\\"
        "Refactor-SubjectSkillLayout",
    ),
    session("claude:36c6da7d", worktree="/home/someone/core.worktrees/Feature-CatchUp"),
    session(
        "codex:5e1f0a22",
        title="approval command",
        links=("github:github.com/tj-agents/personal:49",),
    ),
    session("claude:f8af11f2", title="subject skills and their layout"),
    session(
        "claude:9b0c4d11", worktree="/home/someone/core.worktrees/Fix-CatchUpRuntime"
    ),
]
CLOSED = {"codex:01a187bc", "claude:36c6da7d", "codex:5e1f0a22", "claude:f8af11f2"}


@pytest.fixture(scope="module")
def catch_up() -> dict[str, Any]:
    return runpy.run_path(str(ROOT / SCRIPT))


def report(catch_up: dict[str, Any], closed: Callable[[], set[str]]) -> dict[str, Any]:
    parse = catch_up["parse"]
    items = [parse("pr", PR), parse("issue", ISSUE), parse("branch", BRANCH)]
    result: dict[str, Any] = catch_up["report"](
        items, [], graphql_response, lambda: RECORDED, closed, 10
    )
    return result


def by_id(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["id"]: entry for entry in result["sessions"]}


def test_report_lists_live_item_states(catch_up: dict[str, Any]) -> None:
    states = {
        item["reference"]: item["state"]
        for item in report(catch_up, lambda: CLOSED)["items"]
    }
    assert states == {PR: "MERGED", ISSUE: "OPEN", BRANCH: "OPEN"}


def test_report_marks_closed_owner_of_unmerged_branch_stalled(
    catch_up: dict[str, Any],
) -> None:
    sessions = by_id(report(catch_up, lambda: CLOSED))
    assert sessions["01a187bc"]["topics"] == ["SubjectSkillLayout"]
    assert sessions["01a187bc"]["stalled"]
    assert sessions["01a187bc"]["reopen"] == "agent:open codex:01a187bc"


def test_report_marks_closed_owner_of_open_issue_stalled(
    catch_up: dict[str, Any],
) -> None:
    sessions = by_id(report(catch_up, lambda: CLOSED))
    assert sessions["5e1f0a22"]["items"] == ["github:github.com/tj-agents/personal:49"]
    assert sessions["5e1f0a22"]["stalled"]


def test_report_leaves_merged_branch_owner_and_unrelated_sessions_alone(
    catch_up: dict[str, Any],
) -> None:
    sessions = by_id(report(catch_up, lambda: CLOSED))
    assert not sessions["36c6da7d"]["stalled"]
    assert "reopen" not in sessions["36c6da7d"]
    assert "f8af11f2" not in sessions
    assert "9b0c4d11" not in sessions


def test_report_never_marks_a_live_session_stalled(catch_up: dict[str, Any]) -> None:
    sessions = by_id(report(catch_up, set))
    assert sessions["01a187bc"]["status"] == "live"
    assert not sessions["01a187bc"]["stalled"]


def test_report_skips_liveness_when_no_session_matches(
    catch_up: dict[str, Any],
) -> None:
    def closed() -> set[str]:
        raise AssertionError("liveness read without a matching session")

    result = catch_up["report"]([], ["Unrelated"], graphql_response, list, closed, 10)
    assert result == {"items": [], "sessions": []}


def test_parse_rejects_a_reference_of_the_wrong_kind(
    catch_up: dict[str, Any],
) -> None:
    with pytest.raises(ValueError, match="pr reference"):
        catch_up["parse"]("pr", ISSUE)


def fake_tools(directory: Path, responses: dict[str, object]) -> Path:
    directory.mkdir()
    for name, response in responses.items():
        (directory / f"{name}.json").write_text(json.dumps(response), encoding="utf-8")
        if os.name == "nt":
            (directory / f"{name}.cmd").write_text(
                f'@type "%~dp0{name}.json"\r\n', encoding="utf-8"
            )
        else:
            launcher = directory / name
            launcher.write_text(
                f'#!/bin/sh\ncat "$(dirname "$0")/{name}.json"\n', encoding="utf-8"
            )
            launcher.chmod(0o755)
    return directory


def run_script(
    monkeypatch: pytest.MonkeyPatch, script: Path, tools: Path, *arguments: str
) -> subprocess.CompletedProcess[str]:
    monkeypatch.setenv("PATH", os.pathsep.join([str(tools), os.defpath]))
    return subprocess.run(
        [sys.executable, "-I", "-B", str(script), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )


def test_generated_package_reports_stalled_sessions_from_installed_agent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = tmp_path / "relocated package ü"
    shutil.copytree(
        ROOT / "plugins/workflow", package, ignore=shutil.ignore_patterns("__pycache__")
    )
    tools = fake_tools(
        tmp_path / "tools",
        {
            "agent-store": {"ok": True, "data": {"sessions": RECORDED}},
            "tj": [{"session": handle, "action": "resume"} for handle in CLOSED],
        },
    )
    result = run_script(
        monkeypatch, package / PACKAGED_SCRIPT, tools, "--topic", "SubjectSkillLayout"
    )
    assert result.returncode == 0, result.stderr
    sessions = by_id(json.loads(result.stdout))
    assert set(sessions) == {"01a187bc"}
    assert sessions["01a187bc"]["status"] == "closed"


def test_script_names_the_missing_agent_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tools = tmp_path / "empty"
    tools.mkdir()
    result = run_script(
        monkeypatch, ROOT / SCRIPT, tools, "--topic", "SubjectSkillLayout"
    )
    assert result.returncode == 1
    assert "agent-store is not on PATH" in result.stderr
