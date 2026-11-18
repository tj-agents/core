import importlib
import importlib.util
import json
import subprocess
import sys
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUDGET_SECONDS = 10
IDENTITY = ("-c", "user.name=Freshness Test", "-c", "user.email=fresh@example.invalid")
SELECTION = '{"schema_version": 1, "plugins": ["base@tj-agents"]}\n'
MERGED = {"number": 7, "state": "MERGED", "url": "https://example.invalid/pull/7"}


def _load_gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "checkout_freshness_gate", ROOT / ".agents/hooks/tier_gate.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = _load_gate()
freshness = importlib.import_module("checkout_freshness")


def git(directory: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *IDENTITY, "-C", str(directory), *arguments],
        capture_output=True,
        encoding="utf-8",
        check=True,
        timeout=30,
    )
    return completed.stdout.strip()


def commit(directory: Path, name: str, content: str = "change\n") -> None:
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    git(directory, "add", "--", name)
    git(directory, "commit", "--quiet", "-m", f"Add {name}")


def advance(publisher: Path, count: int, prefix: str = "main") -> None:
    for index in range(count):
        commit(publisher, f"{prefix}-{index}.txt")
    git(publisher, "push", "--quiet", "origin", "HEAD:main")


class Remote:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.origin = root / "origin.git"
        self.publisher = root / "publisher"
        git(
            root, "init", "--quiet", "--bare", "--initial-branch=main", str(self.origin)
        )
        git(root, "clone", "--quiet", str(self.origin), str(self.publisher))
        git(self.publisher, "symbolic-ref", "HEAD", "refs/heads/main")
        commit(self.publisher, "README.md", "readme\n")
        git(self.publisher, "push", "--quiet", "origin", "HEAD:main")

    def clone(self, name: str = "checkout") -> Path:
        checkout = self.root / name
        git(self.root, "clone", "--quiet", str(self.origin), str(checkout))
        return checkout

    def merge(self, branch: str) -> None:
        git(self.publisher, "fetch", "--quiet", "origin")
        merge = ("merge", "--quiet", "--no-ff", "-m", f"Merge {branch}")
        git(self.publisher, *merge, f"origin/{branch}")
        git(self.publisher, "push", "--quiet", "origin", "HEAD:main")


@pytest.fixture
def remote(tmp_path: Path) -> Remote:
    return Remote(tmp_path)


@pytest.fixture(autouse=True)
def isolated_freshness(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        freshness, "pull_request", lambda checkout, branch: (True, None)
    )
    monkeypatch.setattr(freshness, "FETCH_SECONDS", 20.0)
    monkeypatch.setattr(freshness, "TOTAL_SECONDS", 40.0)


def feature(checkout: Path, branch: str) -> str:
    git(checkout, "switch", "--quiet", "-c", branch)
    commit(checkout, f"{branch.replace('/', '-')}.txt")
    git(checkout, "push", "--quiet", "-u", "origin", branch)
    return git(checkout, "rev-parse", "HEAD")


def bounded(directory: Path) -> str:
    with ThreadPoolExecutor(max_workers=1) as pool:
        result: str = pool.submit(freshness.notice, directory).result(BUDGET_SECONDS)
        return result


def hang(checkout: Path) -> None:
    sleeper = f"'{Path(sys.executable).as_posix()}' -c 'import time; time.sleep(60)'"
    git(checkout, "config", "remote.origin.uploadpack", sleeper)


def test_clean_default_branch_behind_fast_forwards_in_one_line(remote: Remote) -> None:
    checkout = remote.clone()
    advance(remote.publisher, 2)

    notice = freshness.notice(checkout)

    assert notice.startswith(
        "Checkout freshness: fast-forwarded main by 2 commits to origin/main ("
    )
    assert "\n" not in notice
    assert git(checkout, "rev-parse", "HEAD") == git(
        checkout, "rev-parse", "origin/main"
    )


def test_dirty_default_branch_is_reported_and_not_fast_forwarded(
    remote: Remote,
) -> None:
    checkout = remote.clone()
    before = git(checkout, "rev-parse", "HEAD")
    (checkout / "README.md").write_text("local edit\n", encoding="utf-8")
    advance(remote.publisher, 2)

    notice = freshness.notice(checkout)

    assert notice.startswith(
        "STALE CHECKOUT: main is 2 commits behind origin/main and has uncommitted"
    )
    assert "engineering:sync-checkout" in notice
    assert git(checkout, "rev-parse", "HEAD") == before
    assert (checkout / "README.md").read_text(encoding="utf-8") == "local edit\n"


def test_default_branch_with_local_commits_is_not_fast_forwarded(
    remote: Remote,
) -> None:
    checkout = remote.clone()
    commit(checkout, "local.txt")
    before = git(checkout, "rev-parse", "HEAD")
    advance(remote.publisher, 1)

    notice = freshness.notice(checkout)

    assert "main is 1 commit behind and 1 commit ahead of origin/main" in notice
    assert git(checkout, "rev-parse", "HEAD") == before


def test_live_feature_branch_behind_is_reported_with_its_count_and_left_unchanged(
    remote: Remote,
) -> None:
    checkout = remote.clone()
    head = feature(checkout, "Feature/Live")
    advance(remote.publisher, 3)

    notice = freshness.notice(checkout)

    assert notice.startswith(
        "STALE CHECKOUT: branch Feature/Live is 3 commits behind origin/main."
    )
    assert "No pull request exists for it." in notice
    assert "run `engineering:sync-checkout` to merge origin/main into this" in notice
    assert git(checkout, "rev-parse", "HEAD") == head
    assert git(checkout, "branch", "--show-current") == "Feature/Live"


def test_branch_contained_in_the_default_branch_is_reported_as_shipped(
    remote: Remote,
) -> None:
    checkout = remote.clone()
    head = feature(checkout, "Feature/Done")
    remote.merge("Feature/Done")
    advance(remote.publisher, 1)

    notice = freshness.notice(checkout)

    assert "branch Feature/Done is 2 commits behind origin/main." in notice
    assert "It is fully contained in origin/main." in notice
    assert "(`git switch main`, then `git merge --ff-only origin/main`)" in notice
    assert git(checkout, "rev-parse", "HEAD") == head


def test_branch_whose_pull_request_merged_is_reported_with_the_pull_request(
    remote: Remote, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkout = remote.clone()
    feature(checkout, "Feature/Squashed")
    advance(remote.publisher, 1, "squash")
    monkeypatch.setattr(
        freshness, "pull_request", lambda checkout, branch: (True, MERGED)
    )

    notice = freshness.notice(checkout)

    assert "branch Feature/Squashed is 1 commit behind origin/main." in notice
    assert f"Its PR #7 is MERGED ({MERGED['url']})." in notice
    assert "or run `engineering:sync-checkout` to retire this branch" in notice


def test_branch_whose_remote_branch_is_gone_is_reported_as_shipped(
    remote: Remote,
) -> None:
    checkout = remote.clone()
    feature(checkout, "Feature/Gone")
    git(remote.publisher, "push", "--quiet", "origin", "--delete", "Feature/Gone")
    advance(remote.publisher, 1)

    notice = freshness.notice(checkout)

    assert "Its remote branch origin/Feature/Gone is gone." in notice
    assert "switch to main" in notice


def test_checkout_without_the_default_branch_selection_says_plugins_will_not_load(
    remote: Remote,
) -> None:
    checkout = remote.clone()
    feature(checkout, "Feature/Old")
    commit(remote.publisher, ".agents/plugins.json", SELECTION)
    git(remote.publisher, "push", "--quiet", "origin", "HEAD:main")

    lines = freshness.notice(checkout).splitlines()

    assert lines[0].startswith(
        "STALE CHECKOUT: branch Feature/Old is 1 commit behind origin/main."
    )
    assert lines[1].startswith(
        "PLUGINS WILL NOT LOAD: this checkout has no .agents/plugins.json"
    )


def test_fast_forward_that_adds_the_selection_asks_for_a_restart(
    remote: Remote,
) -> None:
    checkout = remote.clone()
    commit(remote.publisher, ".agents/plugins.json", SELECTION)
    git(remote.publisher, "push", "--quiet", "origin", "HEAD:main")

    lines = freshness.notice(checkout).splitlines()

    assert lines[0].startswith("Checkout freshness: fast-forwarded main by 1 commit")
    assert lines[1] == (
        "The update added .agents/plugins.json; "
        "restart the session so its plugins load."
    )


def test_current_checkout_says_nothing(remote: Remote) -> None:
    assert freshness.notice(remote.clone()) == ""


def test_unreachable_remote_fails_open_and_compares_with_the_last_fetch(
    remote: Remote, tmp_path: Path
) -> None:
    checkout = remote.clone()
    advance(remote.publisher, 1)
    git(checkout, "fetch", "--quiet", "origin")
    git(checkout, "remote", "set-url", "origin", str(tmp_path / "missing.git"))

    lines = bounded(checkout).splitlines()

    assert lines[0].startswith("Checkout freshness: could not fetch origin (")
    assert lines[0].endswith("; compared with the last fetched origin/main.")
    assert lines[1].startswith("Checkout freshness: fast-forwarded main by 1 commit")


def test_hanging_fetch_is_abandoned_at_its_timeout(
    remote: Remote, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkout = remote.clone()
    hang(checkout)
    monkeypatch.setattr(freshness, "FETCH_SECONDS", 1.0)

    assert bounded(checkout) == (
        "Checkout freshness: could not fetch origin (timed out or could not start); "
        "compared with the last fetched origin/main."
    )


def test_no_repository_no_origin_and_detached_head_say_nothing(
    remote: Remote, tmp_path: Path
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    local = tmp_path / "local"
    git(tmp_path, "init", "--quiet", str(local))
    commit(local, "README.md")
    detached = remote.clone("detached")
    git(detached, "switch", "--quiet", "--detach")
    advance(remote.publisher, 1)

    assert freshness.notice(outside) == ""
    assert freshness.notice(local) == ""
    assert freshness.notice(detached) == ""


def test_any_failure_yields_no_notice(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def broken(directory: Path, deadline: float) -> None:
        raise RuntimeError(str(directory))

    monkeypatch.setattr(freshness, "fetched", broken)

    assert freshness.begin(tmp_path)() == ""


def test_session_start_starts_the_fetch_before_the_standards_statement(
    remote: Remote, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkout = remote.clone()
    advance(remote.publisher, 1)
    order: list[str] = []
    begin = freshness.begin

    def tracked_begin(directory: Path) -> Callable[[], str]:
        order.append("begin")
        finish: Callable[[], str] = begin(directory)
        return finish

    def tracked_statement(directory: Path) -> str:
        order.append("statement")
        return ""

    arguments = ["tier_gate.py", "--session-context", "--project", str(checkout)]
    monkeypatch.setattr(gate, "begin_checkout_freshness", tracked_begin)
    monkeypatch.setattr(gate, "statement", tracked_statement)
    monkeypatch.setattr(gate.sys, "argv", arguments)
    monkeypatch.setattr(gate, "_stdin_payload", dict)

    assert gate.main() == 0
    assert order == ["begin", "statement"]


def registered_session_start(cwd: Path) -> subprocess.CompletedProcess[str]:
    package = ROOT / "plugins/base"
    manifest = json.loads((package / "hooks/claude.json").read_text(encoding="utf-8"))
    hook = manifest["hooks"]["SessionStart"][0]["hooks"][0]
    arguments = [
        argument.replace("${CLAUDE_PLUGIN_ROOT}", str(package))
        for argument in hook["args"]
    ]
    payload = {
        "hook_event_name": "SessionStart",
        "cwd": str(cwd),
        "session_id": "fresh",
    }
    return subprocess.run(
        [hook["command"], *arguments],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=cwd,
        timeout=min(BUDGET_SECONDS, hook["timeout"]),
        check=False,
    )


def test_registered_session_start_leads_with_the_notice_within_budget(
    remote: Remote,
) -> None:
    checkout = remote.clone()
    advance(remote.publisher, 2)

    result = registered_session_start(checkout)

    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert "decision" not in output
    message = output["systemMessage"]
    assert message.startswith("Checkout freshness: fast-forwarded main by 2 commits")
    context = output["hookSpecificOutput"]
    assert context["hookEventName"] == "SessionStart"
    assert context["additionalContext"].startswith(message)


def test_registered_session_start_with_a_hanging_remote_stays_within_budget(
    remote: Remote,
) -> None:
    checkout = remote.clone()
    hang(checkout)

    result = registered_session_start(checkout)

    assert result.returncode == 0, result.stderr
    message = json.loads(result.stdout)["systemMessage"]
    assert message.startswith("Checkout freshness: could not fetch origin")
