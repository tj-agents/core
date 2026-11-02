from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def authored_skill(name: str) -> Path:
    paths = {
        "merge": ".agents/engineering/workflow/merge/SKILL.md",
        "merging": ".agents/engineering/policy/merging/SKILL.md",
        "plans": ".agents/engineering/convention/plans/SKILL.md",
        "workflow:run": ".agents/workflow/workflow/run/SKILL.md",
        "handoff": ".agents/workflow/workflow/handoff/SKILL.md",
    }
    return ROOT / paths[name]


def test_merge_cleanup_targets_one_proven_worktree() -> None:
    body = authored_skill("merge").read_text(encoding="utf-8")
    cleanup = body.split(
        "### 5. Return to a clean base and record targeted checkout cleanup", maxsplit=1
    )[1].split("### 6. Follow the publish", maxsplit=1)[0]
    flat = " ".join(cleanup.split())
    assert (
        cleanup.count("--session-close <agent-peer-skill>/scripts/session_close.py")
        == 2
    )
    for required in (
        "never remove that path",
        "Classify only the checkout this delivery owns",
        "exact merged-head obligation",
        "every recorded holder released",
        "launch the deterministic worker before arming frontend release",
        "recent-edit guard",
        "verifies the target path is absent",
        "Do not run a repository-wide sweep as a closeout shortcut",
        "`pending`, with its resolver and resume condition",
        "Preparation preserves each delivery's obligation and terminal receipt",
        "every previously launched worker is observed exited",
        "an exact `verified` receipt",
    ):
        assert required in flat
    for retired in (
        "scripts/worktree_sweep.py",
        "finish.py",
        "scripts/close.py",
        "machine:close",
        "worktrees.ps1",
        "worktree remove --force",
    ):
        assert retired not in cleanup


def test_plan_pair_retirement_names_declared_sources_before_removal() -> None:
    plans = " ".join(authored_skill("plans").read_text(encoding="utf-8").split())
    run = " ".join(authored_skill("workflow:run").read_text(encoding="utf-8").split())
    for required in (
        "--artifact",
        "--retire-source",
        "before deleting the goal",
        "responsibility aggregate and other evidence remain live",
    ):
        assert required in plans
    assert "<workflow-plugin-root>/workflows/completion.py" in run


def test_handoff_does_not_create_a_routine_cleanup_successor() -> None:
    handoff = " ".join(authored_skill("handoff").read_text(encoding="utf-8").split())
    cleanup = " ".join(authored_skill("merging").read_text(encoding="utf-8").split())
    assert "explicit transfer may include a checkout operation" in handoff
    assert (
        "generic handoff neither requires nor creates a separate cleanup successor"
        in handoff
    )
    assert "deterministic worker running outside the target" in cleanup
    assert (
        "Host exit, scheduler submission, or partial Git cleanup is not evidence"
        in cleanup
    )
    assert "Do not create a routine handoff or new session for cleanup" in cleanup
