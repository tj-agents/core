import json
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

from fixtures.routing_fixture import resolved_route


class StaticObserver:
    def capture(self):
        return set()

    def changed_since(self, baseline):
        return set()


class TaskWorkflowHarness:
    host_events = {
        "parallel-readers",
        "reader-invalid",
        "parent-fallback",
        "writer-one-leased",
        "writer-two-rejected",
        "writer-one-terminal",
        "writer-two-leased",
        "writer-two-terminal",
        "repository-probe",
        "checkpoint",
        "pause",
    }

    def __init__(
        self,
        root,
        workflows,
        host,
        host_adapter_registry,
        writer_lease_registry,
        contract_violation,
        select_state_provider,
        deck="bare-cli",
    ):
        self.root = Path(root)
        self.workflows = Path(workflows)
        self.host = host
        self.contract_violation = contract_violation
        self.select_state_provider = select_state_provider
        if deck not in {"bare-cli", "kandev"}:
            raise ValueError(f"unsupported execution deck {deck}")
        self.deck = deck
        self.registry = host_adapter_registry(
            self.workflows,
            self.root,
            executable_resolver=lambda command: command,
            command_runner=lambda *args, **kwargs: SimpleNamespace(
                returncode=0,
                stdout="workflow-host 1.0\n",
                stderr="",
            ),
            lease_registry=writer_lease_registry(),
            repository_observer=StaticObserver(),
            route_provider=resolved_route,
        )
        self.contract = self.registry.contract

    def dispatch(self, scenario, capability, index):
        definition = self.contract.capabilities["delegable_capabilities"][capability]
        workflow = scenario["expected_workflow"]
        skill_path = f".agents/skills/{workflow}/SKILL.md"
        dispatch_id = f"{self.host}-{scenario['id']}-{index}"
        permissions = {
            "mode": definition["mode"],
            "files": [skill_path],
            "tools": ["read", "search"],
            "allow_subdispatch": False,
        }
        if capability == "mechanical-worker":
            permissions.update(
                tools=["read", "edit"],
                writer_lease={"lease_id": f"lease-{dispatch_id}", "paths": [skill_path]},
            )
        return {
            "contract_version": self.contract.version,
            "workflow_id": workflow,
            "workflow_run_id": f"acceptance/{scenario['id']}",
            "stage_id": f"{scenario['id']}/{capability}",
            "dispatch_id": dispatch_id,
            "capability": capability,
            "objective": f"{scenario['request']} Return only bounded {capability} evidence.",
            "context": {
                "repository_paths": [skill_path],
                "immutable_artifacts": [f"fixture:{scenario['id']}"],
                "supplied_logs": ["fixture:noisy-log"] if capability == "log-analyst" else [],
                "prior_decisions": ["The parent retains task and lifecycle decisions."],
                "assumptions": [],
            },
            "permissions": permissions,
            "result_schema": "result.schema.json",
            "decision_boundary": {
                "may_decide": list(definition["may_decide"]),
                "must_not_decide": list(definition["must_not_decide"]),
            },
            "acceptance_conditions": [
                f"Return cited {capability} evidence without selecting the parent decision."
            ],
            "deadline": {"cancellation_condition": "Cancel when the fixture baseline changes."},
            "failure_behavior": {
                "uncertainty": "State uncertainty and plausible alternatives.",
                "missing_context": "Return incomplete and name the missing context.",
                "conflicting_evidence": "Return conflicting evidence without choosing the parent decision.",
                "incomplete_result": "Return the completed conditions and exact remaining gap.",
            },
        }

    def result(self, dispatch):
        evidence_id = f"evidence-{dispatch['dispatch_id']}"
        condition = dispatch["acceptance_conditions"][0]
        result = {
            "contract_version": self.contract.version,
            "workflow_id": dispatch["workflow_id"],
            "workflow_run_id": dispatch["workflow_run_id"],
            "stage_id": dispatch["stage_id"],
            "dispatch_id": dispatch["dispatch_id"],
            "status": "complete",
            "summary": f"Bounded {dispatch['capability']} evidence returned to the parent.",
            "claims": [
                {
                    "claim": f"The {dispatch['capability']} acceptance condition is supported.",
                    "evidence_ids": [evidence_id],
                    "confidence": 95,
                    "uncertainty": "",
                    "alternatives": [],
                }
            ],
            "evidence": [
                {
                    "evidence_id": evidence_id,
                    "kind": "repository",
                    "locator": dispatch["context"]["repository_paths"][0],
                    "detail": f"Fixture evidence for {dispatch['stage_id']}.",
                }
            ],
            "acceptance_conditions": [
                {
                    "condition": condition,
                    "passed": True,
                    "evidence_ids": [evidence_id],
                    "detail": "The bounded result cites its fixture evidence.",
                }
            ],
            "open_questions": [],
        }
        if dispatch["capability"] == "mechanical-worker":
            result["writer"] = {
                "changed_paths": [],
                "validation": ["The no-op mechanical fixture completed."],
                "partial_paths": [],
            }
        return result

    def dispatch_records(self, scenario):
        probe = self.registry.probe(self.host)
        dispatches = [
            self.dispatch(scenario, capability, index)
            for index, capability in enumerate(scenario["dispatches"], start=1)
        ]
        records = {}
        if scenario["id"] == "complex-bug":
            for dispatch in dispatches:
                self.registry.prepare(self.host, dispatch, probe=probe)
            records["parallel-readers"] = {"active": len(self.registry.active_dispatches)}
            for dispatch in dispatches:
                self.registry.accept_result(self.host, dispatch, self.result(dispatch))
        elif scenario["id"] == "failure-recovery":
            dispatch = dispatches[0]
            self.registry.prepare(self.host, dispatch, probe=probe)
            invalid = self.result(dispatch)
            invalid["dispatch_id"] = "wrong-dispatch"
            fallback = self.registry.accept_result(self.host, dispatch, invalid)
            records["reader-invalid"] = {"reason": fallback["reason_code"]}
            records["parent-fallback"] = fallback
        elif scenario["id"] == "writer-serialization":
            first, second = dispatches
            records["writer-one-leased"] = self.registry.prepare(
                self.host, first, probe=probe
            )
            try:
                self.registry.prepare(self.host, second, probe=probe)
            except self.contract_violation as error:
                records["writer-two-rejected"] = {"detail": str(error)}
            else:
                raise AssertionError("the second writer acquired an overlapping lease")
            records["writer-one-terminal"] = self.registry.accept_result(
                self.host, first, self.result(first)
            )
            records["writer-two-leased"] = self.registry.prepare(
                self.host, second, probe=probe
            )
            records["writer-two-terminal"] = self.registry.accept_result(
                self.host, second, self.result(second)
            )
        else:
            for dispatch in dispatches:
                self.registry.prepare(self.host, dispatch, probe=probe)
                self.registry.accept_result(self.host, dispatch, self.result(dispatch))
        return records

    def prepare_provider_fixture(self, root, scenario):
        branch = "Feature/provider-acceptance"
        subprocess.run(["git", "init", "-q", "-b", branch, str(root)], check=True)
        for key, value in (
            ("user.email", "provider@example.test"),
            ("user.name", "Provider Test"),
        ):
            subprocess.run(
                ["git", "-C", str(root), "config", key, value],
                check=True,
            )
        plan, ledger = scenario["durable_artifacts"]
        roadmap = "plans/agent-workflows/AGENT_WORKFLOWS_ROADMAP.md"
        for relative in (plan, roadmap):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {path.stem}\n", encoding="utf-8")
        template = Path(__file__).with_name("provider_progress.template").read_text(
            encoding="utf-8"
        )
        ledger_path = root / ledger
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(
            template.format(plan=plan, roadmap=roadmap, worktree=root, branch=branch),
            encoding="utf-8",
        )
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(
            ["git", "-C", str(root), "commit", "-q", "-m", "provider fixture"],
            check=True,
        )
        return ledger

    def provider_records(self, scenario):
        expected_provider = scenario.get("state_provider")
        if expected_provider is None:
            return {}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            ledger = self.prepare_provider_fixture(root, scenario)
            contract = self.contract.__class__(self.workflows, repository_root=root)
            provider = self.select_state_provider(root, contract=contract)
            if provider.provider_id != expected_provider:
                raise AssertionError(
                    f"scenario expected {expected_provider} state but selected {provider.provider_id}"
                )
            probe = provider.probe()
            state = provider.resolve(
                ledger,
                f"acceptance/{scenario['id']}",
                "durable-promotion",
            )
            return {
                "repository-probe": probe,
                "checkpoint": provider.validate_checkpoint(state),
            }

    def run(self, scenario):
        records = self.dispatch_records(scenario)
        records.update(self.provider_records(scenario))
        if scenario["terminal"]["kind"] == "human-gate":
            terminal = scenario["terminal"]
            records["pause"] = self.contract.gate(
                "human",
                "open",
                terminal["owner"],
                terminal["action"],
                terminal["resume_condition"],
                terminal["evidence"],
            )
        observed = []
        for event in scenario["events"]:
            if event in records:
                record = records[event]
            elif event in self.host_events:
                raise AssertionError(f"host event {event!r} was declared but not executed")
            elif event == "complete":
                record = self.contract.transition("complete", "The scripted outcome is terminal.")
            else:
                record = self.contract.transition(
                    "continue",
                    f"The parent advanced the scripted {event} stage.",
                    target_stage_id=event,
                )
            observed.append({"event": event, "record": record})
        return {
            "workflow": scenario["expected_workflow"],
            "host": self.host,
            "deck": self.deck,
            "events": observed,
            "terminal": observed[-1]["record"],
        }
