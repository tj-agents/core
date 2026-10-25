import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "hooks"))

import delivery_runtime
import merge_review_gate
import workflow_ops


class AutoMergeError(RuntimeError):
    pass


def parse_root(argv):
    if len(argv) != 3 or argv[1] != "--root":
        raise AutoMergeError("usage: auto_merge.py --root <absolute-checkout>")
    root = Path(argv[2])
    if not root.is_absolute():
        raise AutoMergeError("--root must name an absolute checkout")
    try:
        return root.resolve(strict=True)
    except OSError as error:
        raise AutoMergeError(f"--root cannot be resolved: {error}") from error


def read_binding(root):
    try:
        artifact = json.loads((root / delivery_runtime.BINDING_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise AutoMergeError(f"delivery binding cannot be read: {error}") from error
    if not isinstance(artifact, dict):
        raise AutoMergeError("delivery binding must be an object")
    binding = delivery_runtime.binding_from_artifact(artifact)
    binding.setdefault("auto_merge", False)
    try:
        delivery_runtime.PersistentDeliveryRouter().validate_binding(binding)
    except delivery_runtime.DeliveryContractViolation as error:
        raise AutoMergeError(str(error)) from error
    return binding


def exact_local_identity(root, binding):
    if Path(binding["worktree"]).resolve() != root:
        raise AutoMergeError("binding worktree does not match --root")
    if workflow_ops.repository_root(root) != root:
        raise AutoMergeError("--root is not the checkout root")
    if workflow_ops.repository_slug(root) != binding["repository"]:
        raise AutoMergeError("checkout repository does not match the binding")
    if workflow_ops.git(root, "branch", "--show-current") != binding["branch"]:
        raise AutoMergeError("checkout branch does not match the binding")
    if workflow_ops.git(root, "rev-parse", "HEAD") != binding["remote_head_sha"]:
        raise AutoMergeError("checkout HEAD does not match the binding")
    remote = workflow_ops.run_process(
        ["git", "ls-remote", "origin", f"refs/heads/{binding['branch']}"], root
    ).stdout.split()
    if not remote or remote[0] != binding["remote_head_sha"]:
        raise AutoMergeError("origin branch head does not match the binding")


def green_exact_head(value, head):
    if str(value.get("state", "")).lower() != "open" or value.get("isDraft") is not False:
        raise AutoMergeError("PR is not open and ready")
    merge_state = str(value.get("mergeStateStatus", "")).upper()
    awaiting_review = (
        merge_state == "BLOCKED"
        and value.get("reviewDecision") == "REVIEW_REQUIRED"
        and value.get("mergeable") == "MERGEABLE"
    )
    if merge_state != "CLEAN" and not awaiting_review:
        raise AutoMergeError("PR base is not eligible for merge")
    if value.get("headRefOid") != head:
        raise AutoMergeError("PR head does not match the binding")
    rollup = value.get("statusCheckRollup")
    if not isinstance(rollup, list) or not rollup:
        raise AutoMergeError("PR has no established exact-head checks")
    for check in rollup:
        if not isinstance(check, dict):
            raise AutoMergeError("PR checks cannot be read")
        if "status" in check or "conclusion" in check:
            if str(check.get("status", "")).lower() != "completed" or str(
                check.get("conclusion", "")
            ).lower() not in {"success", "neutral", "skipped"}:
                raise AutoMergeError("PR checks are not green")
        elif str(check.get("state", "")).lower() not in {"success", "neutral", "skipped"}:
            raise AutoMergeError("PR checks are not green")


def current_authorization(root, binding, value):
    reported = [str(item.get("path")) for item in value.get("files") or [] if item.get("path")]
    changed = workflow_ops.changed_paths(root, binding["pr_number"], reported, value.get("changedFiles"))
    labels = [str(item.get("name")) for item in value.get("labels") or [] if item.get("name")]
    resolution = workflow_ops.standing_authorization(root, changed, labels)
    approval = workflow_ops.scoped_approval(
        root, binding["repository"], binding["pr_number"], binding["branch"], None
    )
    if approval is not None and (
        resolution["stopped_by"] is None
        or resolution["stopped_by"]["class"] == "no-recorded-authorization"
    ):
        resolution["merge_authorization"] = {
            "mode": approval["mode"], "instruction": approval["instruction"]
        }
        resolution["stopped_by"] = None
    if not binding["auto_merge"] or resolution["auto_merge"] is not True:
        raise AutoMergeError("repository auto_merge is not enabled")
    if resolution["stopped_by"] is not None or resolution["merge_authorization"]["mode"] == "absent":
        raise AutoMergeError("current authorization does not permit merge")
    if resolution["merge_authorization"] != binding["merge_authorization"]:
        raise AutoMergeError("current authorization does not match the binding")
    return changed


def current_review(root, binding, changed):
    merge_review_gate._GIT_CWD[0] = str(root)
    config = merge_review_gate.find_config(root)
    if config is None:
        raise AutoMergeError("canonical merge review configuration is absent")
    try:
        patterns = merge_review_gate.security_patterns(config)
    except merge_review_gate.ConfigUnusable as error:
        raise AutoMergeError(str(error)) from error
    slug = binding["branch"].replace("/", "-").replace("\\", "-")
    work_order = f"reviews/{slug}.md"
    try:
        evidence = workflow_ops.review_evidence.resolve(
            root, binding["branch"], binding["remote_head_sha"],
            lambda *args: workflow_ops.git(root, *args),
        )
        review = evidence["body"]
    except workflow_ops.review_evidence.ReviewEvidenceError as error:
        raise AutoMergeError(str(error)) from error
    if merge_review_gate.review_completion_problem(review):
        raise AutoMergeError("review work order is incomplete")
    reviewed = merge_review_gate.work_order_sha_field(review, "Reviewed up to commit")
    head = binding["remote_head_sha"]
    if reviewed in {None, "invalid"} or not (
        head.lower().startswith(reviewed) or reviewed.startswith(head.lower())
    ) and not merge_review_gate.review_only(reviewed, head):
        raise AutoMergeError("review evidence is stale")
    if merge_review_gate.unresolved_review_items(review):
        raise AutoMergeError("review has unresolved findings")
    if merge_review_gate.touches_security(changed, patterns):
        security_reviewed = merge_review_gate.work_order_sha_field(review, "Security-reviewed up to commit")
        if security_reviewed in {None, "invalid"} or not (
            head.lower().startswith(security_reviewed) or security_reviewed.startswith(head.lower())
        ) and merge_review_gate.security_no_longer_covered(
            security_reviewed, head, patterns, work_order
        ):
            raise AutoMergeError("security review evidence is absent or stale")


def arm(root):
    binding = read_binding(root)
    exact_local_identity(root, binding)
    value = workflow_ops.pull_request_state(root, binding["pr_number"], binding["repository"])
    if value.get("number") != binding["pr_number"] or value.get("headRefName") != binding["branch"]:
        raise AutoMergeError("PR identity does not match the binding")
    green_exact_head(value, binding["remote_head_sha"])
    changed = current_authorization(root, binding, value)
    current_review(root, binding, changed)
    workflow_ops.run_process(
        [
            "gh", "pr", "merge", str(binding["pr_number"]), "--repo", binding["repository"],
            "--merge", "--auto", "--match-head-commit", binding["remote_head_sha"],
        ],
        root,
    )


def main(argv=None):
    try:
        arm(parse_root(sys.argv if argv is None else argv))
    except (AutoMergeError, workflow_ops.WorkflowOperationError, OSError) as error:
        print(f"auto-merge: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
