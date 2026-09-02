import subprocess
import sys
import tempfile
from pathlib import Path


class PlanAuthoringHarness:
    def __init__(
        self,
        workflows,
        workflow_contract,
        select_state_provider,
    ):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.workflows = Path(workflows).resolve()
        self.workflow_contract = workflow_contract
        self.select_state_provider = select_state_provider
        self.contract = workflow_contract(self.workflows, repository_root=self.root)
        self.plan = "plans/webhooks/IDEMPOTENT_WEBHOOK_PLAN.md"
        self.roadmap = "plans/webhooks/WEBHOOKS_ROADMAP.md"
        self.ledger = "plans/webhooks/IDEMPOTENT_WEBHOOK_PROGRESS.md"
        self.initialize_repository()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.temp.cleanup()

    def git(self, *arguments):
        return subprocess.run(
            ["git", "-C", str(self.root), *arguments],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def commit(self, message):
        self.git("add", ".")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def initialize_repository(self):
        subprocess.run(
            ["git", "init", "-q", "-b", "main", str(self.root)],
            check=True,
            capture_output=True,
        )
        self.git("config", "user.email", "authoring@example.test")
        self.git("config", "user.name", "Plan Authoring Test")
        self.write(
            "requirements/webhooks.md",
            "# Webhook requirements\n\nDeliver each webhook idempotently and retain retry evidence.\n",
        )
        self.write(
            self.roadmap,
            "# Webhooks roadmap\n\n- [ ] Add idempotent processing. `webhooks/idempotent-processing`\n",
        )
        self.baseline = self.commit("authoring fixture baseline")

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

    def author(self):
        self.plan_text = "\n".join(
                [
                    "# Idempotent webhook processing plan",
                    "",
                    "## Outcome",
                    "",
                    "Repeated delivery produces one durable effect and observable retry evidence.",
                    "",
                    "## Constraints",
                    "",
                    "- Preserve the published webhook contract.",
                    "- Keep product implementation out of planning-only work.",
                    "",
                    "## Phase 1 - durable receipt",
                    "",
                    "- Persist one delivery identity before invoking behavior.",
                    "- Gate: focused receipt and duplicate-delivery tests pass.",
                    "",
                    "## Phase 2 - retry consumption",
                    "",
                    "- Consume recorded failures without duplicating the effect.",
                    "- Gate: retry integration tests and the full repository suite pass.",
                    "",
                    "## Completion",
                    "",
                    "Both phases are reviewed, green, and consumed by the webhook entry point.",
                    "",
                ]
            )
        self.write(self.plan, self.plan_text)
        self.write(
            self.ledger,
            "\n".join(
                [
                    "# Idempotent webhook processing progress",
                    "",
                    f"- Plan: `{self.plan}`",
                    f"- Roadmap: `{self.roadmap}`",
                    "- Roadmap item: `webhooks/idempotent-processing`",
                    f"- Worktree: `{self.root}`",
                    "- Branch: `main`",
                    "- PR: not opened",
                    "- Dependency/package gates: none",
                    "",
                    "## Current state",
                    "",
                    "The implementation-ready two-phase plan is authored.",
                    "",
                    "## Next Steps",
                    "",
                    "Implement Phase 1 and prove its focused receipt gate.",
                    "",
                    "## Completed work",
                    "",
                    "- Requirements and objective phase gates are recorded.",
                    "",
                    "## Verification",
                    "",
                    "- Plan graph pending this commit.",
                    "",
                    "## Reviews",
                    "",
                    "No implementation review is open.",
                    "",
                    "## Decisions, discoveries, blockers, and deviations",
                    "",
                    "- Repository state is the portable provider fallback.",
                    "",
                ]
            ),
        )
        return self.commit("author durable webhook plan")

    def run(self, scenario):
        head = self.author()
        graph = self.verify_plan_graph()
        provider = self.select_state_provider(self.root, contract=self.contract)
        probe = provider.probe()
        state = provider.resolve(
            self.ledger,
            "acceptance/plan-authoring",
            "implementation-ready",
        )
        provider.validate_checkpoint(state)
        changed = self.git("diff", "--name-only", f"{self.baseline}..{head}").splitlines()
        worktrees = sum(
            line.startswith("worktree ")
            for line in self.git("worktree", "list", "--porcelain").splitlines()
        )
        transfer = None
        terminal = "complete"
        if scenario["implementation_authorized"]:
            terminal = "continue"
            transfer = self.contract.transition(
                "continue",
                "The same parent enters plan execution with the authored identity.",
                target_stage_id="plan-execution",
            )
        return {
            "workflow": "plan-authoring",
            "terminal": terminal,
            "implementation_authorized": scenario["implementation_authorized"],
            "probe": probe,
            "state": state,
            "transfer": transfer,
            "changed_paths": changed,
            "worktree_count": worktrees,
            "plan_graph": graph,
            "head": head,
            "phase_gate_count": self.plan_text.count("- Gate:"),
            "plan_mentions_roadmap": self.roadmap in self.plan_text,
            "execution_identity": state["workflow_id"] if transfer else None,
        }
