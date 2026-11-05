from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def merge_step() -> str:
    guidance = (ROOT / ".agents/engineering/workflow/merge/SKILL.md").read_text(
        encoding="utf-8"
    )
    return guidance.split("### 4.", 1)[1].split("### 4b.", 1)[0]


def test_required_approval_allows_an_ordinary_exact_head_merge() -> None:
    step = merge_step()
    assert "requires_approval: true" in step
    assert "agents_may_merge" not in step
    assert "actual required human approval" in step
    assert "current-head review" in step
    assert "terminal and green" in step
    command = next(line for line in step.splitlines() if "&& gh pr merge" in line)
    assert 'pushd "<absolute-worktree>"' in command
    assert "--repo <owner/repository>" in command
    assert "--match-head-commit <remote-head>" in command
    assert "--auto" not in command
    assert "--admin" not in command


def test_disabled_auto_merge_preserves_authorized_ordinary_delivery() -> None:
    step = merge_step()
    assert "auto_merge" in step
    assert "disabled" in step
    assert "ordinary merge" in step
    assert "standing stops" in step
    assert "explicit holds" in step
    assert "settings" in step
    assert "GitHub still enforces its ruleset" in step
    assert "github-actions:merge-policy" in step


def test_missing_approval_waits_without_enabling_auto_merge() -> None:
    step = merge_step()
    assert "If required approval is missing" in step
    assert "request the owner's review" in step
    assert "when auto-merge is enabled" in step
    assert "Never enable auto-merge" in step
