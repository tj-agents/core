from pathlib import Path


def test_publication_runs_after_successful_aggregate_with_skipped_ancestors() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    job = workflow.split("\n  regenerate:\n", 1)[1]
    condition = job.split("    if: >-\n", 1)[1].split("\n    needs:", 1)[0]
    assert "!cancelled()" in condition
    assert "needs.ci-required.result == 'success'" in condition
    assert "github.event_name == 'push'" in condition
    assert (
        "github.ref == format('refs/heads/{0}', github.event.repository.default_branch)"
        in condition
    )
    assert (
        "!startsWith(github.event.head_commit.message, 'Regenerate packages for ')"
        in condition
    )
    assert "    needs: ci-required\n" in job
