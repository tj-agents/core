import contextlib
import copy
import subprocess
import sys
import tempfile
from pathlib import Path


class PlanWorkflowHarness:
    parent_events = {
        "implement-phase-one",
        "implement-phase-two",
        "implement-phase",
        "focused-validate",
        "continue",
        "select-next-phase",
        "parent-diagnosis",
        "repair",
        "revalidate",
        "address-review",
        "incremental-review",
    }

    def __init__(
        self,
        workflows,
        workflow_contract,
        select_state_provider,
    ):
        self.temp = tempfile.TemporaryDirectory()
        self.container = Path(self.temp.name).resolve()
        self.admin_root = self.container / "admin"
        self.root = self.container / "slice-one"
        self.workflows = Path(workflows).resolve()
        self.branch = "Feature/plan-acceptance"
        self.workflow_contract = workflow_contract
        self.select_state_provider = select_state_provider
        self.contract = workflow_contract(self.workflows, repository_root=self.root)
        self.ledger = "plans/runtime/RUNTIME_PROGRESS.md"
        self.plan = "plans/runtime/RUNTIME_PLAN.md"
        self.roadmap = "plans/runtime/RUNTIME_ROADMAP.md"
        self.template = Path(__file__).with_name("plan_progress.template").read_text(
            encoding="utf-8"
        )
        self.provider = None
        self.provider_probe = None
        self.last_state = None
        self.next_temp = None
        self.next_root = None
        self.initialize_repository()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.next_root is not None:
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(self.admin_root),
                    "worktree",
                    "remove",
                    "--force",
                    str(self.next_root),
                ],
                check=False,
                capture_output=True,
            )
        if self.next_temp is not None:
            self.next_temp.cleanup()
        self.temp.cleanup()

    def git(self, *arguments):
        return subprocess.run(
            ["git", "-C", str(self.root), *arguments],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def admin_git(self, *arguments):
        return subprocess.run(
            ["git", "-C", str(self.admin_root), *arguments],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def initialize_repository(self):
        subprocess.run(
            ["git", "init", "-q", "-b", "main", str(self.admin_root)],
            check=True,
            capture_output=True,
        )
        self.admin_git("config", "user.email", "plan@example.test")
        self.admin_git("config", "user.name", "Plan Test")
        plan_path = self.admin_root / self.plan
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text("# Runtime plan\n", encoding="utf-8")
        roadmap_path = self.admin_root / self.roadmap
        roadmap_path.write_text(
            "# Runtime roadmap\n\n- [ ] Exercise plan execution. `runtime/plan-execution`\n",
            encoding="utf-8",
        )
        ledger_path = self.admin_root / self.ledger
        ledger_path.write_text(
            self.template.replace("__WORKTREE__", str(self.root))
            .replace("__BRANCH__", self.branch)
            .replace("__NEXT_STEPS__", "Implement phase one."),
            encoding="utf-8",
        )
        self.admin_git("add", ".")
        self.admin_git("commit", "-q", "-m", "plan fixture baseline")
        self.admin_git(
            "worktree",
            "add",
            "-q",
            "-b",
            self.branch,
            str(self.root),
            "main",
        )
        self.provider_probe, self.provider = self.new_provider()

    def write_ledger(self, next_steps):
        content = (
            self.template.replace("__WORKTREE__", str(self.root))
            .replace("__BRANCH__", self.branch)
            .replace("__NEXT_STEPS__", next_steps)
        )
        path = self.root / self.ledger
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def commit(self, message):
        self.git("add", ".")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def verify_plan_graph(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(self.workflows.parent / "hooks" / "plan_graph.py"),
                "--root",
                str(self.root),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode:
            raise AssertionError((completed.stdout + completed.stderr).strip())
        return completed.stdout.strip()

    def new_provider(self):
        provider = self.select_state_provider(self.root, contract=self.contract)
        return provider.probe(), provider

    def resolve(self, stage):
        state = self.provider.resolve(
            self.ledger,
            "acceptance/plan-execution",
            stage,
        )
        self.provider.validate_checkpoint(state)
        self.last_state = state
        return state

    def checkpoint(self, event, next_steps):
        self.write_ledger(next_steps)
        self.commit(event)
        state = self.resolve(event)
        return {
            "transition": self.contract.transition(
                "checkpoint",
                "A material plan transition was persisted.",
                target_stage_id=event,
            ),
            "state": state,
        }

    @contextlib.contextmanager
    def record_corpus_reads(self):
        reads = []
        original = Path.read_text
        root = self.root

        def tracked(instance, *arguments, **keywords):
            try:
                relative = Path(instance).resolve().relative_to(root)
            except ValueError:
                relative = None
            if relative is not None and relative.parts and relative.parts[0] == "plans":
                reads.append(relative.as_posix())
            return original(instance, *arguments, **keywords)

        Path.read_text = tracked
        try:
            yield reads
        finally:
            Path.read_text = original

    def git_identity(self):
        return {
            "worktree": str(Path(self.git("rev-parse", "--show-toplevel")).resolve()),
            "branch": self.git("branch", "--show-current"),
            "head": self.git("rev-parse", "HEAD"),
            "dirty": bool(self.git("status", "--porcelain")),
        }

    def continuation_summary(self, next_steps, branch=None, dirty=False):
        return {
            "workflow_id": "runtime/plan-execution",
            "plan": self.plan,
            "ledger": self.ledger,
            "roadmap": self.roadmap,
            "worktree": str(self.root),
            "branch": branch or self.branch,
            "status": "active",
            "dirty": dirty,
            "next_action": next_steps,
        }

    def trust_continuation(self, summary, identity):
        required = (
            "workflow_id",
            "plan",
            "ledger",
            "roadmap",
            "worktree",
            "branch",
            "status",
            "next_action",
        )
        if any(not summary.get(name) for name in required):
            return False
        if Path(summary["worktree"]).resolve() != Path(identity["worktree"]).resolve():
            return False
        if summary["dirty"] != identity["dirty"]:
            return False
        return summary["branch"] == identity["branch"]

    def state_from_summary(self, summary, identity, workflow_run_id, stage_id):
        state = {
            "contract_version": self.contract.version,
            "workflow_id": summary["workflow_id"],
            "workflow_run_id": workflow_run_id,
            "stage_id": stage_id,
            "status": summary["status"],
            "provider_id": "repository",
            "owner": {
                "repository": self.root.name,
                "worktree": identity["worktree"],
                "branch": identity["branch"],
                "head": identity["head"],
            },
            "artifacts": {
                "plan": summary["plan"],
                "ledger": summary["ledger"],
                "roadmap": summary["roadmap"],
                "reviews": [],
            },
            "decisions": [],
            "open_findings": [],
            "next_action": {
                "kind": "continue",
                "description": summary["next_action"],
                "scope": "whole plan through all remaining phases and terminal delivery",
                "current_slice": summary["next_action"],
                "remaining_scope": "later phases, delivery, and closeout remain",
                "done_when": "the whole fixture plan is delivered and closed",
            },
            "transition": self.contract.transition(
                "continue",
                "A trustworthy continuation summary resolved the current next action.",
                target_stage_id=stage_id,
            ),
        }
        return self.contract.validate("state", state)

    def accept_continuation(self, scenario):
        summary = self.continuation_summary(scenario["continuation"]["next_steps"])
        with self.record_corpus_reads() as reads:
            identity = self.git_identity()
            trusted = self.trust_continuation(summary, identity)
            state = self.state_from_summary(
                summary,
                identity,
                "acceptance/plan-execution",
                "resume-from-continuation",
            )
        with self.record_corpus_reads() as corpus_reads:
            corpus_state = self.resolve("resume-from-continuation")
        return {
            "trusted": trusted,
            "corpus_reads": list(reads),
            "state": state,
            "corpus_reads_when_read": list(corpus_reads),
            "corpus_state": corpus_state,
        }

    def contradicted_continuation(self, scenario):
        summary = self.continuation_summary(
            scenario["continuation"]["next_steps"],
            branch="Feature/plan-acceptance-stale",
        )
        with self.record_corpus_reads() as reads:
            identity = self.git_identity()
            trusted = self.trust_continuation(summary, identity)
            state = None if trusted else self.resolve("resume-from-corpus")
        return {
            "trusted": trusted,
            "corpus_reads": list(reads),
            "state": state,
        }

    def block(self, scenario):
        blocker = scenario["blocker"]
        self.write_ledger(
            "\n".join(
                [
                    f"Blocked: {blocker['reason']}",
                    f"Blocked by: {blocker['owner']}",
                    f"Unblock action: {blocker['action']}",
                    f"Resume when: {blocker['resume']}",
                ]
            )
        )
        self.commit("record dependency blocker")
        return self.resolve("dependency-blocked")

    def reciprocal_return(self, scenario):
        blocker = scenario["blocker"]
        path = self.root / blocker["owner"]
        path.parent.mkdir(parents=True, exist_ok=True)
        dependency_plan = path.with_name("DEPENDENCY_PLAN.md")
        dependency_roadmap = path.with_name("DEPENDENCY_ROADMAP.md")
        dependency_plan.write_text("# Dependency plan\n", encoding="utf-8")
        dependency_roadmap.write_text(
            "# Dependency roadmap\n\n- [ ] Publish dependency contract. "
            "`dependency/published-contract`\n",
            encoding="utf-8",
        )
        path.write_text(
            "\n".join(
                [
                    "# Dependency progress",
                    "",
                    f"- Plan: {dependency_plan.relative_to(self.root).as_posix()}",
                    f"- Roadmap: {dependency_roadmap.relative_to(self.root).as_posix()}",
                    "- Roadmap item: dependency/published-contract",
                    f"- Worktree: {self.root}",
                    f"- Branch: {self.branch}",
                    "- PR: not opened",
                    "",
                    "## Current state",
                    "",
                    "The dependency owner has a reciprocal return path.",
                    "",
                    "## Next Steps",
                    "",
                    f"Return to `{self.ledger}` when {blocker['resume']}",
                    "Scope: current slice only; full plan remains incomplete.",
                    "Current slice: wait for the recorded dependency return condition.",
                    "Remaining scope: the owning plan resumes after the dependency returns.",
                    "Done when: the dependency return is observable; the full plan remains open.",
                    "",
                    "## Completed work",
                    "",
                    "The reciprocal return was recorded.",
                    "",
                    "## Verification",
                    "",
                    "Pending.",
                    "",
                    "## Reviews",
                    "",
                    "No review work order is open.",
                    "",
                    "## Decisions, discoveries, blockers, and deviations",
                    "",
                    "- Repository state is the portable provider fallback.",
                    "",
                    "## Downstream handoffs",
                    "",
                    f"- `{self.ledger}` in `{self.root}`; return when {blocker['resume']}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        self.commit("record reciprocal return")
        return {
            "transition": self.contract.transition(
                "block",
                blocker["reason"],
                resume_condition=blocker["resume"],
            ),
            "gate": self.last_state["blocker"],
            "return_path": blocker["owner"],
            "return_target": self.ledger,
            "plan_graph": self.verify_plan_graph(),
        }

    def transfer(self, scenario):
        self.write_ledger(
            "\n".join(
                [
                    "Transfer: Resume from the durable plan checkpoint.",
                    "Transfer to: fresh-parent",
                    "Resume stage: resume-from-checkpoint",
                    f"Resume when: {scenario['resume_condition']}",
                ]
            )
        )
        self.commit("record context transfer")
        state = self.resolve("transfer-checkpoint")
        re_resolved = self.provider.resolve(
            self.ledger,
            "acceptance/plan-execution",
            "transfer-checkpoint",
        )
        self.provider.validate_checkpoint(re_resolved)
        return {
            "state": state,
            "re_resolved": re_resolved,
            "gate": self.contract.gate(
                "context-transfer",
                "open",
                "fresh-parent",
                "Read the plan and ledger from the owning worktree.",
                scenario["resume_condition"],
                [self.ledger],
            ),
        }

    def rollover_slice(self, scenario):
        previous = copy.deepcopy(self.last_state)
        self.admin_git("merge", "--ff-only", self.branch)
        main_head = self.admin_git("rev-parse", "main")
        self.admin_git("worktree", "remove", "--force", str(self.root))
        worktree_paths = {
            Path(line.removeprefix("worktree ")).resolve()
            for line in self.admin_git("worktree", "list", "--porcelain").splitlines()
            if line.startswith("worktree ")
        }
        self.next_temp = tempfile.TemporaryDirectory()
        self.next_root = Path(self.next_temp.name).resolve() / "checkout"
        next_branch = "Feature/plan-acceptance-slice-two"
        self.admin_git(
            "worktree",
            "add",
            "-q",
            "-b",
            next_branch,
            str(self.next_root),
            "main",
        )
        ledger = self.next_root / self.ledger
        content = (
            self.template.replace("__WORKTREE__", str(self.next_root))
            .replace("__BRANCH__", next_branch)
            .replace("__NEXT_STEPS__", scenario["rollover_next_steps"])
        )
        ledger.write_text(content, encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(self.next_root), "add", self.ledger],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.next_root),
                "commit",
                "-q",
                "-m",
                "roll plan into slice two",
            ],
            check=True,
            capture_output=True,
        )
        contract = self.workflow_contract(
            self.workflows,
            repository_root=self.next_root,
        )
        provider = self.select_state_provider(self.next_root, contract=contract)
        state = provider.resolve(
            self.ledger,
            "acceptance/plan-execution",
            "slice-two",
        )
        provider.validate_checkpoint(state)
        self.last_state = state
        merge_base = subprocess.run(
            ["git", "-C", str(self.next_root), "merge-base", "main", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return {
            "transition": contract.transition(
                "continue",
                "The next PR slice resumed from fresh default.",
                target_stage_id="slice-two",
            ),
            "previous_owner": previous["owner"],
            "state": state,
            "main_head": main_head,
            "merge_base": merge_base,
            "old_owner_closed": self.root not in worktree_paths,
        }

    def execute_event(self, scenario, event):
        if event == "resolve":
            return {"probe": self.provider_probe, "state": self.resolve("resolve")}
        if event in scenario["checkpoints"]:
            return self.checkpoint(event, scenario["checkpoints"][event])
        if event == "validation-failed":
            return self.contract.transition(
                "retry",
                "The parent diagnoses the failed validation before retrying.",
                target_stage_id="parent-diagnosis",
            )
        if event == "review-finding":
            return self.contract.transition(
                "retry",
                "The parent addresses the confirmed review finding before incremental review.",
                target_stage_id="address-review",
            )
        if event == "resume-plan-entry":
            return {"entry": "resume-plan", "owner": "plan-execution"}
        if event == "continue-roadmap-entry":
            return {"entry": "continue-roadmap", "owner": "plan-authoring"}
        if event == "accept-continuation":
            return self.accept_continuation(scenario)
        if event == "contradicted-continuation":
            return self.contradicted_continuation(scenario)
        if event == "block":
            return self.block(scenario)
        if event == "reciprocal-return":
            return self.reciprocal_return(scenario)
        if event == "transfer":
            return self.transfer(scenario)
        if event == "merge-slice":
            return self.contract.transition(
                "continue",
                "The reviewed delivery slice merged.",
                target_stage_id="rollover-slice",
            )
        if event == "rollover-slice":
            return self.rollover_slice(scenario)
        if event == "restart":
            previous = copy.deepcopy(self.last_state)
            self.provider_probe, self.provider = self.new_provider()
            return {
                "provider_id": self.provider.provider_id,
                "previous_head": previous["owner"]["head"],
                "previous_next_action": previous["next_action"],
            }
        if event == "re-resolve":
            return self.resolve("restart-recovery")
        if event == "complete":
            self.write_ledger("Complete: The scripted plan lifecycle is terminal.")
            self.commit("complete plan fixture")
            return self.resolve("complete")
        if event in self.parent_events:
            return self.contract.transition(
                "continue",
                f"The parent completed the {event} stage.",
                target_stage_id=event,
            )
        raise AssertionError(f"unhandled plan workflow event {event!r}")

    def run(self, scenario):
        events = [
            {"event": event, "record": self.execute_event(scenario, event)}
            for event in scenario["events"]
        ]
        return {
            "entry": scenario["entry"],
            "workflow": scenario["workflow"],
            "events": events,
            "terminal_kind": scenario["terminal"],
            "terminal": events[-1]["record"],
        }
