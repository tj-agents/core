import copy
import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath


SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
DEBUG_ROUTES = {
    "unit": "failing-tests",
    "integration": "integration-debug",
    "e2e-api": "e2e-api-debug",
    "e2e-ui": "e2e-ui-debug",
    "e2e-both": "e2e-debug",
    "e2e-ui-regression": "e2e-ui-debug",
}


class DeliveryContractViolation(ValueError):
    pass


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
        if not isinstance(binding["completion_condition"], str) or not binding["completion_condition"]:
            raise DeliveryContractViolation("completion condition is required")
        if "workflow_handoff" in binding:
            self._validate_workflow_handoff(binding["workflow_handoff"])
        return binding

    def owner_key(self, binding):
        self.validate_binding(binding)
        if "workflow_handoff" in binding:
            handoff = binding["workflow_handoff"]
            return json.dumps(
                [
                    "workflow",
                    binding["repository"],
                    handoff["workflow_id"],
                    handoff["state_artifact"],
                ],
                ensure_ascii=False,
                separators=(",", ":"),
            )
        return json.dumps(
            [
                binding["repository"],
                str(binding["pr_number"]),
                str(PureWindowsPath(binding["worktree"])),
                binding["branch"],
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def binding_key(self, binding):
        return json.dumps(
            [
                self.owner_key(binding),
                str(binding["pr_number"]),
                str(PureWindowsPath(binding["worktree"])),
                binding["branch"],
                binding["remote_head_sha"],
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def continuation_operation(self, binding, existing):
        owner_key = self.owner_key(binding)
        matches = [item for item in existing if item["owner_key"] == owner_key]
        if len(matches) > 1:
            raise DeliveryContractViolation("more than one continuation owns this delivery")
        if matches:
            return {
                "operation": "update",
                "task_id": matches[0]["task_id"],
                "owner_key": owner_key,
                "binding_key": self.binding_key(binding),
            }
        return {
            "operation": "create",
            "task_id": None,
            "owner_key": owner_key,
            "binding_key": self.binding_key(binding),
        }

    def rebind_after_owner_push(self, binding, new_head, pending_evidence, owner_push):
        self.validate_binding(binding)
        if not owner_push:
            raise DeliveryContractViolation("only this delivery owner may rebind after a push")
        self._validate_sha(new_head, "new remote head")
        if new_head == binding["remote_head_sha"]:
            raise DeliveryContractViolation("repair push did not create a new remote head")
        updated = copy.deepcopy(binding)
        updated["remote_head_sha"] = new_head
        updated["pending_evidence"] = copy.deepcopy(pending_evidence)
        updated["review"]["reviewed_sha"] = None
        updated.pop("last_state_token", None)
        return self.validate_binding(updated)

    def rebind_to_successor(
        self,
        binding,
        successor,
        parent_transfer,
        successor_authorization=None,
    ):
        self.validate_binding(binding)
        self.validate_binding(successor)
        if not parent_transfer:
            raise DeliveryContractViolation("only the parent may transfer to a successor delivery")
        if "workflow_handoff" not in binding or "workflow_handoff" not in successor:
            raise DeliveryContractViolation("successor rebind requires a workflow handoff")
        if binding["workflow_handoff"] != successor["workflow_handoff"]:
            raise DeliveryContractViolation("successor belongs to another workflow handoff")
        if binding["repository"] != successor["repository"]:
            raise DeliveryContractViolation("successor belongs to another repository")
        if binding["pr_number"] == successor["pr_number"]:
            raise DeliveryContractViolation("successor must bind a different PR")
        updated = copy.deepcopy(successor)
        branch_slug = updated["branch"].replace("/", "-").replace("\\", "-")
        updated["review"] = {
            "work_order": f"reviews/{branch_slug}.md",
            "work_order_order": copy.deepcopy(successor["review"]["work_order_order"]),
            "reviewed_sha": None,
        }
        updated["merge_authorization"] = {"mode": "absent", "instruction": None}
        if successor_authorization is not None:
            self._validate_successor_authorization(updated, successor_authorization)
            updated["merge_authorization"] = {
                "mode": successor_authorization["mode"],
                "instruction": successor_authorization["instruction"],
            }
        return self.validate_binding(updated)

    def decide(self, binding, observation):
        self.validate_binding(binding)
        required = {
            "pr_number",
            "remote_head_sha",
            "state",
            "state_token",
            "checks_conclusion",
            "review_judgment",
            "reviewed_sha",
        }
        missing = required - set(observation)
        if missing:
            raise DeliveryContractViolation(f"delivery observation is missing {sorted(missing)!r}")
        if observation["state"] not in {"open", "merged", "closed", "superseded"}:
            raise DeliveryContractViolation("delivery observation has an unknown PR state")
        if not isinstance(observation["state_token"], str) or not observation["state_token"]:
            raise DeliveryContractViolation("delivery observation requires a state token")
        if observation["pr_number"] != binding["pr_number"]:
            return self._cleanup("superseded", "The observed PR differs from the bound PR.")
        if observation["remote_head_sha"] != binding["remote_head_sha"]:
            return self._cleanup(
                "external-head-replacement",
                "The remote head changed outside this delivery owner's rebind operation.",
                human_decision=True,
            )
        review_judgment = observation["review_judgment"]
        if review_judgment not in {"pending", "clean", "findings"}:
            raise DeliveryContractViolation("delivery observation has an unknown review judgment")
        reviewed_sha = observation["reviewed_sha"]
        if reviewed_sha is not None:
            self._validate_sha(reviewed_sha, "observed review head")
            if review_judgment in {"clean", "findings"} and reviewed_sha != binding["remote_head_sha"]:
                raise DeliveryContractViolation("review evidence belongs to another head")
        if review_judgment in {"clean", "findings"} and reviewed_sha is None:
            raise DeliveryContractViolation("completed review evidence requires its reviewed head")
        if review_judgment == "pending" and reviewed_sha is not None:
            raise DeliveryContractViolation("pending review evidence cannot carry a reviewed head")
        if observation["state"] == "merged" and "workflow_handoff" in binding:
            handoff = binding["workflow_handoff"]
            return {
                "kind": "transfer",
                "semantic_stage": "implementation",
                "skill": handoff["next_stage"],
                "workflow_handoff": copy.deepcopy(handoff),
                "reason": "The current PR merged and the owning workflow has a recorded successor stage.",
                "close_delivery_binding": True,
                "remove_continuation": False,
            }
        if observation["state"] in {"merged", "closed", "superseded"}:
            return self._cleanup(observation["state"], "The bound PR reached a terminal state.")
        if observation["state_token"] == binding.get("last_state_token"):
            return {
                "kind": "noop",
                "reason": "Authoritative forge state is unchanged.",
                "remove_continuation": False,
            }
        if observation["checks_conclusion"] == "failure":
            return self._failure_dispatch(binding, observation)
        if observation["checks_conclusion"] == "pending":
            return {
                "kind": "wait",
                "reason": "Exact-head checks remain pending.",
                "remove_continuation": False,
            }
        if observation["checks_conclusion"] != "success":
            return self._cleanup(
                "human-decision",
                "Exact-head validation has an unsupported terminal conclusion.",
                human_decision=True,
            )
        if review_judgment == "findings":
            return {
                "kind": "dispatch",
                "semantic_stage": "implementation",
                "skill": "address-review",
                "fresh_context": False,
                "reason": "Current-head review has actionable findings.",
                "remove_continuation": False,
            }
        if review_judgment == "pending":
            skill = "incremental-review" if binding["review"]["reviewed_sha"] else "review"
            return {
                "kind": "dispatch",
                "semantic_stage": "review",
                "skill": skill,
                "fresh_context": True,
                "reason": "Exact-head checks are green and current-head independent review is required.",
                "remove_continuation": False,
            }
        authorization = binding["merge_authorization"]
        if authorization["mode"] == "absent":
            return self._cleanup(
                "merge-authorization",
                "The current head is green and reviewed but merge authorization is absent.",
                human_decision=True,
            )
        return {
            "kind": "merge",
            "semantic_stage": "review",
            "skill": "merge",
            "authorization": copy.deepcopy(authorization),
            "reason": "The exact head is green, independently reviewed, and explicitly authorized.",
            "remove_continuation": False,
        }

    def _failure_dispatch(self, binding, observation):
        evidence = observation.get("failed_evidence")
        if evidence is None:
            raise DeliveryContractViolation("failed exact-head checks require failed evidence")
        self._validate_evidence(evidence, binding["remote_head_sha"])
        pending = {self._evidence_identity(item) for item in binding["pending_evidence"]}
        identity = self._evidence_identity(evidence)
        if identity not in pending:
            raise DeliveryContractViolation("failed evidence is not part of the bound pending evidence")
        tier = observation.get("failure_tier")
        if tier not in DEBUG_ROUTES:
            raise DeliveryContractViolation("failed test tier has no debug route")
        signature = observation.get("failure_signature")
        if not isinstance(signature, str) or not signature:
            raise DeliveryContractViolation("failed test evidence requires a failure signature")
        skill = DEBUG_ROUTES[tier]
        prompt = "\n".join(
            [
                f"Enter the {skill} skill in a fresh context and repair only this exact-head failure.",
                f"Repository: {binding['repository']}",
                f"PR: {binding['pr_url']} #{binding['pr_number']}",
                f"Worktree: {binding['worktree']}",
                f"Branch: {binding['branch']}",
                f"Bound remote head: {binding['remote_head_sha']}",
                f"Check ID: {evidence['check_id']}",
                f"Run ID: {evidence['run_id']}",
                f"Run head: {evidence['head_sha']}",
                f"Failure: {signature}",
                "Read the remote log first, reproduce only the failing scope, run focused validation, and return structured repair evidence to the parent.",
                "Do not merge, approve, widen scope, or create another delivery monitor.",
            ]
        )
        if evidence.get("event") == "merge_group":
            prompt = prompt.replace(
                f"Run head: {evidence['head_sha']}",
                "\n".join(
                    [
                        f"Run head: {evidence['head_sha']}",
                        f"Bound PR source head: {evidence['pr_head_sha']}",
                    ]
                ),
            )
        return {
            "kind": "dispatch",
            "semantic_stage": "implementation",
            "skill": skill,
            "fresh_context": True,
            "prompt": prompt,
            "reason": "An exact-head test failure selected its tier-specific debugging workflow.",
            "remove_continuation": False,
        }

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

    def _validate_successor_authorization(self, successor, authorization):
        required = {
            "repository",
            "pr_number",
            "branch",
            "remote_head_sha",
            "mode",
            "instruction",
        }
        if not isinstance(authorization, dict) or set(authorization) != required:
            raise DeliveryContractViolation("successor authorization has an invalid shape")
        for field in ("repository", "pr_number", "branch", "remote_head_sha"):
            if authorization[field] != successor[field]:
                raise DeliveryContractViolation(
                    "successor authorization does not bind the exact successor"
                )
        if authorization["mode"] not in {"auto", "merge"}:
            raise DeliveryContractViolation("successor authorization mode is invalid")
        if not isinstance(authorization["instruction"], str) or not authorization["instruction"]:
            raise DeliveryContractViolation("successor authorization requires its recorded instruction")

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

    def _cleanup(self, terminal, reason, human_decision=False):
        return {
            "kind": "human-gate" if human_decision else "cleanup",
            "terminal": terminal,
            "reason": reason,
            "remove_continuation": True,
        }
