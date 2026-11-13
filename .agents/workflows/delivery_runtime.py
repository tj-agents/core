"""Validation for the per-worktree delivery binding the Codex continuation runtime reads."""

import copy
import re
from pathlib import Path, PurePosixPath, PureWindowsPath


SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class DeliveryContractViolation(ValueError):
    pass


BINDING_FILE = ".agents/delivery-binding.json"
ARTIFACT_ALIASES = (
    ("repo", "repository"),
    ("pr", "pr_number"),
    ("pr_url", "pr_url"),
    ("branch", "branch"),
    ("worktree", "worktree"),
    ("head", "remote_head_sha"),
)
ARTIFACT_CARRIED = (
    "pending_evidence",
    "review",
    "merge_authorization",
    "auto_merge",
    "completion_condition",
    "workflow_handoff",
    "last_state_token",
)


def binding_from_artifact(artifact):
    """The contract binding an artifact records, so a reader never re-derives the mapping."""
    binding = {}
    for short, long in ARTIFACT_ALIASES:
        if short in artifact:
            binding[long] = artifact[short]
    for field in ARTIFACT_CARRIED:
        if field in artifact:
            binding[field] = copy.deepcopy(artifact[field])
    return binding



class PersistentDeliveryRouter:
    def validate_binding(self, binding):
        required = {
            "repository",
            "pr_url",
            "pr_number",
            "worktree",
            "branch",
            "remote_head_sha",
            "pending_evidence",
            "review",
            "merge_authorization",
            "completion_condition",
        }
        missing = required - set(binding)
        if missing:
            raise DeliveryContractViolation(f"delivery binding is missing {sorted(missing)!r}")
        repository = binding["repository"]
        if not isinstance(repository, str) or repository.count("/") != 1:
            raise DeliveryContractViolation("repository must be an owner/name slug")
        if not isinstance(binding["pr_number"], int) or binding["pr_number"] < 1:
            raise DeliveryContractViolation("PR number must be positive")
        expected_pr_url = f"https://github.com/{repository}/pull/{binding['pr_number']}"
        if binding["pr_url"].rstrip("/") != expected_pr_url:
            raise DeliveryContractViolation("PR URL does not match the bound repository and number")
        worktree = binding["worktree"]
        if not (
            isinstance(worktree, str)
            and (Path(worktree).is_absolute() or PureWindowsPath(worktree).is_absolute())
        ):
            raise DeliveryContractViolation("worktree must be absolute")
        if not isinstance(binding["branch"], str) or not binding["branch"]:
            raise DeliveryContractViolation("branch is required")
        self._validate_sha(binding["remote_head_sha"], "remote head")
        seen = set()
        for evidence in binding["pending_evidence"]:
            self._validate_evidence(evidence, binding["remote_head_sha"])
            identity = self._evidence_identity(evidence)
            if identity in seen:
                raise DeliveryContractViolation("pending evidence contains a duplicate check/run")
            seen.add(identity)
        review = binding["review"]
        if set(review) != {"work_order", "work_order_order", "reviewed_sha"}:
            raise DeliveryContractViolation("review binding has an invalid shape")
        if not isinstance(review["work_order"], str) or not review["work_order"]:
            raise DeliveryContractViolation("review work order is required")
        if not isinstance(review["work_order_order"], list) or not review["work_order_order"]:
            raise DeliveryContractViolation("review work order order is required")
        if (
            any(not isinstance(item, str) or not item for item in review["work_order_order"])
            or len(review["work_order_order"]) != len(set(review["work_order_order"]))
        ):
            raise DeliveryContractViolation("review work order order must be unique nonempty stages")
        if review["reviewed_sha"] is not None:
            self._validate_sha(review["reviewed_sha"], "review watermark")
        authorization = binding["merge_authorization"]
        if set(authorization) != {"mode", "instruction"}:
            raise DeliveryContractViolation("merge authorization has an invalid shape")
        if authorization["mode"] not in {"absent", "auto", "merge"}:
            raise DeliveryContractViolation("merge authorization mode is invalid")
        if authorization["mode"] == "absent" and authorization["instruction"] is not None:
            raise DeliveryContractViolation("absent merge authorization cannot carry an instruction")
        if authorization["mode"] != "absent" and not authorization["instruction"]:
            raise DeliveryContractViolation("merge authorization requires its recorded instruction")
        if "auto_merge" in binding and type(binding["auto_merge"]) is not bool:
            raise DeliveryContractViolation("auto-merge setting must be a boolean")
        if not isinstance(binding["completion_condition"], str) or not binding["completion_condition"]:
            raise DeliveryContractViolation("completion condition is required")
        if "workflow_handoff" in binding:
            self._validate_workflow_handoff(binding["workflow_handoff"])
        return binding

    def _validate_evidence(self, evidence, head):
        base = {"check_id", "run_id", "head_sha"}
        merge_group = base | {"event", "pr_head_sha"}
        keys = frozenset(evidence)
        if keys not in {frozenset(base), frozenset(merge_group)}:
            raise DeliveryContractViolation("check/run evidence has an invalid shape")
        if evidence["check_id"] in {None, ""} or evidence["run_id"] in {None, ""}:
            raise DeliveryContractViolation("check and run IDs are required")
        self._validate_sha(evidence["head_sha"], "check/run head")
        if set(evidence) == base:
            if evidence["head_sha"] != head:
                raise DeliveryContractViolation("check/run evidence belongs to another head")
            return
        if evidence["event"] != "merge_group":
            raise DeliveryContractViolation("extended check/run evidence must be a merge group")
        self._validate_sha(evidence["pr_head_sha"], "merge-group PR head")
        if evidence["pr_head_sha"] != head:
            raise DeliveryContractViolation("merge-group evidence belongs to another PR head")

    def _validate_workflow_handoff(self, handoff):
        if set(handoff) != {"workflow_id", "state_artifact", "next_stage"}:
            raise DeliveryContractViolation("workflow handoff has an invalid shape")
        if not isinstance(handoff["workflow_id"], str) or not handoff["workflow_id"]:
            raise DeliveryContractViolation("workflow handoff requires an identifier")
        state_artifact = handoff["state_artifact"]
        if not isinstance(state_artifact, str) or not state_artifact:
            raise DeliveryContractViolation("workflow handoff state artifact must be repository-relative")
        path = PurePosixPath(state_artifact.replace("\\", "/"))
        windows_path = PureWindowsPath(state_artifact)
        if path.is_absolute() or windows_path.anchor or ".." in path.parts:
            raise DeliveryContractViolation("workflow handoff state artifact must be repository-relative")
        if not isinstance(handoff["next_stage"], str) or not handoff["next_stage"]:
            raise DeliveryContractViolation("workflow handoff requires a next stage")

    def _evidence_identity(self, evidence):
        return (
            str(evidence["check_id"]),
            str(evidence["run_id"]),
            evidence["head_sha"],
            evidence.get("event"),
            evidence.get("pr_head_sha"),
        )

    def _validate_sha(self, value, label):
        if not isinstance(value, str) or not SHA_PATTERN.fullmatch(value):
            raise DeliveryContractViolation(f"{label} must be a full lowercase SHA")
