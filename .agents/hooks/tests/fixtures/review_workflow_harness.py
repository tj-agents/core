import hashlib
import io
import json
import shutil
import subprocess
import tarfile
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Lock
from types import SimpleNamespace


class StaticObserver:
    def capture(self):
        return set()

    def changed_since(self, baseline):
        return set()


class ReviewWorkflowHarness:
    def __init__(
        self,
        root,
        workflows,
        repository,
        host,
        scenario,
        host_adapter_registry,
        writer_lease_registry,
    ):
        self.root = Path(root)
        self.workflows = Path(workflows)
        self.repository = Path(repository)
        self.host = host
        self.scenario = scenario
        self.events = []
        self.bundle_paths = set()
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
        )
        self.contract = self.registry.contract
        self.prepare_repository()

    def cleanup(self):
        for path in list(self.bundle_paths):
            self.cleanup_bundle({"bundle_path": str(path)})

    def git(self, *args):
        return subprocess.run(
            ["git", *args],
            cwd=str(self.repository),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def git_bytes(self, *args):
        return subprocess.run(
            ["git", *args],
            cwd=str(self.repository),
            check=True,
            capture_output=True,
        ).stdout

    def write(self, relative, body):
        path = self.repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def commit_paths(self, message, *paths):
        self.git("add", "--", *paths)
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def prepare_repository(self):
        self.git("init", "-q", "-b", "main", ".")
        self.git("config", "user.email", "review@example.test")
        self.git("config", "user.name", "Review Fixture")
        self.write("src/alpha.txt", "alpha\n")
        self.write("src/beta.txt", "beta\n")
        self.write("tests/test_alpha.txt", "covers alpha\n")
        self.base = self.commit("baseline")
        self.git("checkout", "-q", "-b", "Feature/review-fixture")
        self.write("src/alpha.txt", "\n")
        self.write("src/beta.txt", "beta two\n")
        self.write("tests/test_alpha.txt", "covers alpha and beta\n")
        self.head = self.commit("candidate")

    def freeze(self, base=None, head=None, scope=None, mode="new"):
        frozen_base = base or self.base
        frozen_head = head or self.head
        command = [
            "-c",
            "core.quotepath=false",
            "diff",
            "--name-only",
            "-z",
            frozen_base,
            frozen_head,
        ]
        if scope:
            command.extend(["--", scope])
        paths = sorted(
            path.decode("utf-8")
            for path in self.git_bytes(*command).split(b"\0")
            if path
        )
        digest = hashlib.sha256("\0".join(paths).encode("utf-8")).hexdigest()
        candidate = {
            "base": frozen_base,
            "head": frozen_head,
            "branch": "Feature/review-fixture",
            "scope": scope or "all",
            "paths": paths,
            "path_digest": digest,
            "path_count": len(paths),
            "work_order": "reviews/Feature-review-fixture.md",
            "work_order_mode": mode,
        }
        return self.materialize(candidate)

    def materialize(self, candidate):
        bundle_path = Path(
            tempfile.mkdtemp(prefix="agent-review-candidate-")
        ).resolve()
        self.bundle_paths.add(bundle_path)
        tree_path = bundle_path / "tree"
        tree_path.mkdir()
        archive_bytes = self.git_bytes(
            "archive",
            "--format=tar",
            candidate["head"],
        )
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:") as archive:
            archive.extractall(tree_path, filter="data")
        patch_bytes = self.git_bytes(
            "diff",
            "--binary",
            "--full-index",
            candidate["base"],
            candidate["head"],
        )
        paths_bytes = "\0".join(candidate["paths"]).encode("utf-8")
        (bundle_path / "candidate.patch").write_bytes(patch_bytes)
        (bundle_path / "paths.nul").write_bytes(paths_bytes)
        identity = {
            "base": candidate["base"],
            "branch": candidate["branch"],
            "head": candidate["head"],
            "patch_sha256": hashlib.sha256(patch_bytes).hexdigest(),
            "path_count": candidate["path_count"],
            "path_digest": candidate["path_digest"],
            "paths_sha256": hashlib.sha256(paths_bytes).hexdigest(),
            "scope": candidate["scope"],
            "tree_oid": self.git("rev-parse", f"{candidate['head']}^{{tree}}"),
            "work_order": candidate["work_order"],
            "work_order_mode": candidate["work_order_mode"],
        }
        identity_bytes = json.dumps(
            identity,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        (bundle_path / "identity.json").write_bytes(identity_bytes)
        candidate["bundle_path"] = str(bundle_path)
        candidate["bundle_identity"] = hashlib.sha256(identity_bytes).hexdigest()
        return candidate

    def cleanup_bundle(self, candidate):
        bundle_path = Path(candidate["bundle_path"]).resolve()
        temporary_root = Path(tempfile.gettempdir()).resolve()
        if (
            bundle_path.parent == temporary_root
            and bundle_path.name.startswith("agent-review-candidate-")
        ):
            shutil.rmtree(bundle_path, ignore_errors=True)
        self.bundle_paths.discard(bundle_path)

    def artifacts(self, candidate):
        return [
            f"git-base:{candidate['base']}",
            f"git-head:{candidate['head']}",
            f"path-set-sha256:{candidate['path_digest']}",
            f"candidate-bundle:{candidate['bundle_path']}",
            f"candidate-bundle-sha256:{candidate['bundle_identity']}",
        ]

    def native_review(self, candidate):
        self.events.append("native-general")
        return {
            "artifacts": self.artifacts(candidate),
            "candidates": [
                {
                    "fingerprint": "alpha-empty",
                    "locator": "src/alpha.txt:1",
                    "claim": "The candidate removes the required alpha token.",
                    "correction": "Restore the required token.",
                }
            ],
        }

    def dispatch(self, candidate, lens, index):
        capability = self.contract.capabilities["delegable_capabilities"]["review-lens"]
        dispatch_id = f"{self.host}-review-{index}"
        condition = f"Return bounded {lens['name']} evidence over the frozen candidate."
        return {
            "contract_version": self.contract.version,
            "workflow_id": "review",
            "workflow_run_id": "acceptance/review-family",
            "stage_id": f"review/{lens['name']}-{index}",
            "dispatch_id": dispatch_id,
            "capability": "review-lens",
            "objective": condition,
            "context": {
                "repository_paths": list(lens["paths"]),
                "immutable_artifacts": self.artifacts(candidate),
                "supplied_logs": [],
                "prior_decisions": ["The parent retains severity and final judgment."],
                "assumptions": [],
            },
            "permissions": {
                "mode": "read",
                "files": list(lens["paths"]),
                "tools": ["read", "search"],
                "allow_subdispatch": False,
            },
            "result_schema": "result.schema.json",
            "decision_boundary": {
                "may_decide": list(capability["may_decide"]),
                "must_not_decide": list(capability["must_not_decide"]),
            },
            "acceptance_conditions": [condition],
            "deadline": {"cancellation_condition": "Cancel when the frozen candidate is obsolete."},
            "failure_behavior": {
                "uncertainty": "State uncertainty without assigning severity.",
                "missing_context": "Return incomplete and name the missing context.",
                "conflicting_evidence": "Return the conflict without a final judgment.",
                "incomplete_result": "Return the exact unfinished bounded check.",
            },
        }

    def result(self, dispatch, lens):
        evidence_id = f"evidence-{dispatch['dispatch_id']}"
        locator = f"{lens['paths'][0]}:1"
        artifact_evidence = [
            {
                "evidence_id": f"artifact-{dispatch['dispatch_id']}-{index}",
                "kind": "immutable-artifact",
                "locator": artifact,
                "detail": "The lens used this frozen candidate identity.",
            }
            for index, artifact in enumerate(
                dispatch["context"]["immutable_artifacts"],
                start=1,
            )
        ]
        cited = [item["evidence_id"] for item in artifact_evidence] + [evidence_id]
        return {
            "contract_version": self.contract.version,
            "workflow_id": dispatch["workflow_id"],
            "workflow_run_id": dispatch["workflow_run_id"],
            "stage_id": dispatch["stage_id"],
            "dispatch_id": dispatch["dispatch_id"],
            "status": "complete",
            "summary": f"Bounded {lens['name']} evidence.",
            "claims": [
                {
                    "claim": f"fingerprint={lens['fingerprint']}; correction=repair {lens['name']}",
                    "evidence_ids": cited,
                    "confidence": 95,
                    "uncertainty": "",
                    "alternatives": [],
                }
            ],
            "evidence": artifact_evidence + [
                {
                    "evidence_id": evidence_id,
                    "kind": "repository",
                    "locator": locator,
                    "detail": f"Evidence from the bounded {lens['name']} lens.",
                }
            ],
            "acceptance_conditions": [
                {
                    "condition": dispatch["acceptance_conditions"][0],
                    "passed": True,
                    "evidence_ids": cited,
                    "detail": "The claim cites the frozen candidate.",
                }
            ],
            "open_questions": [],
        }

    def accept_review_result(self, dispatch, result):
        return self.registry.accept_result(self.host, dispatch, result)

    def waves(self):
        waves = []
        for lens in self.scenario["lenses"]:
            paths = set(lens["paths"])
            for wave in waves:
                if paths.isdisjoint(wave["paths"]):
                    wave["lenses"].append(lens)
                    wave["paths"].update(paths)
                    break
            else:
                waves.append({"lenses": [lens], "paths": set(paths)})
        return [wave["lenses"] for wave in waves]

    def staged_state(self, **overrides):
        state = {
            "anchor": self.head,
            "coverage": ["x", "x"],
            "notes_status": "complete",
            "summary_status": "complete",
            "pass_judgment": "approved",
            "judgment": "approved",
            "status": "complete",
            "watermark": self.head,
            "security_required": False,
            "security_watermark": None,
            "security_evidence": True,
        }
        state.update(overrides)
        return state

    def staged_transition(self, state):
        if "~" in state["coverage"]:
            return "resume-area"
        if " " in state["coverage"]:
            return "review-area"
        finalized = (
            state["notes_status"] == "complete"
            and state["summary_status"] == "complete"
            and state["pass_judgment"] in ("approved", "changes-requested")
            and state["judgment"] in ("approved", "changes-requested")
            and state["status"] == "complete"
            and state["watermark"] == state["anchor"]
            and (
                not state["security_required"]
                or state["security_watermark"] == state["anchor"]
            )
        )
        return "complete" if finalized else "parent-finalization"

    def finalize_staged(self, state):
        if state["security_required"] and not state["security_evidence"]:
            return {
                "events": ["security-review"],
                "state": dict(state),
                "transition": self.staged_transition(state),
            }
        finalized = dict(state)
        finalized.update(
            {
                "notes_status": "complete",
                "summary_status": "complete",
                "pass_judgment": "approved",
                "judgment": "approved",
                "status": "complete",
                "watermark": state["anchor"],
            }
        )
        if state["security_required"]:
            finalized["security_watermark"] = state["anchor"]
        return {
            "events": ["parent-finalization"],
            "state": finalized,
            "transition": self.staged_transition(finalized),
        }

    def addressing_ready(self, state):
        final_judgments = ("approved", "changes-requested")
        return (
            state["status"] == "complete"
            and state["judgment"] in final_judgments
            and state["pass_judgment"] in final_judgments
            and all(item == "x" for item in state["coverage"])
            and state["notes_status"] == "complete"
            and state["summary_status"] == "complete"
            and state["watermark"] == state["anchor"]
            and (
                not state["security_required"]
                or state["security_watermark"] == state["anchor"]
            )
        )

    def synthesize(self, native, records):
        candidates = list(native["candidates"])
        for record in records:
            result_claim = record["result"]["claims"][0]
            claim = result_claim["claim"]
            fingerprint, correction = claim.split("; ")
            cited = set(result_claim["evidence_ids"])
            repository_evidence = next(
                item
                for item in record["result"]["evidence"]
                if item["kind"] == "repository" and item["evidence_id"] in cited
            )
            candidates.append(
                {
                    "fingerprint": fingerprint.removeprefix("fingerprint="),
                    "locator": repository_evidence["locator"],
                    "claim": f"The {record['lens']['name']} lens confirmed a candidate defect.",
                    "correction": correction.removeprefix("correction="),
                }
            )
        deduplicated = {}
        for candidate in candidates:
            deduplicated.setdefault(candidate["fingerprint"], candidate)
        findings = []
        for index, candidate in enumerate(deduplicated.values(), start=1):
            severity = "HIGH" if candidate["locator"].startswith("src/") else "MEDIUM"
            findings.append(
                {
                    "id": f"R{index}",
                    "severity": severity,
                    **candidate,
                }
            )
        return {
            "findings": findings,
            "judgment": "changes-requested" if findings else "approved",
        }

    def work_order_text(self, candidate, synthesis, status="complete", marker=None):
        lines = [
            "# Code review - Feature/review-fixture",
            "",
            f"**Review status:** `{status}`",
        ]
        if marker:
            lines.append(f"**Reviewed up to commit:** `{marker}`  `(fixture)`")
        lines.extend(
            (
                f"**Judgment:** `{synthesis['judgment']}`",
                "",
                "## Review pass - fixture - full",
                "",
                f"**Candidate base:** `{candidate['base']}`",
                f"**Candidate head:** `{candidate['head']}`",
                f"**Candidate branch:** `{candidate['branch']}`",
                f"**Candidate scope:** `{candidate['scope']}`",
                f"**Candidate path-set:** `sha256:{candidate['path_digest']}` `({candidate['path_count']} paths)`",
                f"**Candidate bundle:** `{candidate['bundle_path']}`",
                f"**Candidate bundle identity:** `sha256:{candidate['bundle_identity']}`",
                f"**Work-order path:** `{candidate['work_order']}`",
                f"**Work-order mode:** `{candidate['work_order_mode']}`",
                f"**Pass judgment:** `{synthesis['judgment']}`",
                "",
                "### Findings",
                "",
            )
        )
        for finding in synthesis["findings"]:
            lines.extend(
                (
                    f"- [ ] **{finding['id']} - {finding['severity']} - parent-verified** - `{finding['locator']}`",
                    f"  {finding['claim']} {finding['correction']}",
                )
            )
        return "\n".join(lines) + "\n"

    def write_work_order(self, candidate, synthesis):
        path = self.repository / candidate["work_order"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            self.work_order_text(candidate, synthesis, marker=candidate["head"]),
            encoding="utf-8",
        )
        return path

    def review(self):
        candidate = self.freeze()
        try:
            before = self.git("rev-parse", "HEAD")
            native = self.native_review(candidate)
            probe = self.registry.probe(self.host)
            records = []
            peak_active = 0
            peak_executing = 0
            wave_sizes = []
            index = 0
            for wave in self.waves():
                prepared = []
                for lens in wave:
                    index += 1
                    dispatch = self.dispatch(candidate, lens, index)
                    self.registry.prepare(self.host, dispatch, probe=probe)
                    prepared.append((lens, dispatch))
                wave_sizes.append(len(prepared))
                peak_active = max(peak_active, len(self.registry.active_dispatches))
                self.events.append("lens-wave")
                if len(prepared) == 1:
                    lens, dispatch = prepared[0]
                    result = self.result(dispatch, lens)
                    accepted = self.accept_review_result(dispatch, result)
                    records.append(
                        {"lens": lens, "dispatch": dispatch, "result": accepted}
                    )
                    peak_executing = max(peak_executing, 1)
                    continue
                ready = Barrier(len(prepared))
                overlapping = Barrier(len(prepared))
                lock = Lock()
                execution = {"active": 0, "peak": 0}

                def execute(item):
                    lens, dispatch = item
                    ready.wait()
                    with lock:
                        execution["active"] += 1
                        execution["peak"] = max(execution["peak"], execution["active"])
                    overlapping.wait()
                    result = self.result(dispatch, lens)
                    accepted = self.accept_review_result(dispatch, result)
                    with lock:
                        execution["active"] -= 1
                    return {"lens": lens, "dispatch": dispatch, "result": accepted}

                with ThreadPoolExecutor(max_workers=len(prepared)) as executor:
                    records.extend(executor.map(execute, prepared))
                peak_executing = max(peak_executing, execution["peak"])
            synthesis = self.synthesize(native, records)
            work_order = self.write_work_order(candidate, synthesis)
            self.events.append("parent-synthesis")
            return {
                "candidate": candidate,
                "native": native,
                "records": records,
                "synthesis": synthesis,
                "work_order": work_order,
                "peak_active": peak_active,
                "peak_executing": peak_executing,
                "wave_sizes": wave_sizes,
                "head_before": before,
                "head_after": self.git("rev-parse", "HEAD"),
                "events": list(self.events),
            }
        finally:
            self.cleanup_bundle(candidate)

    def invalid_severity_result(self, candidate):
        try:
            lens = self.scenario["lenses"][0]
            dispatch = self.dispatch(candidate, lens, 99)
            self.registry.prepare(self.host, dispatch, probe=self.registry.probe(self.host))
            result = self.result(dispatch, lens)
            result["severity"] = "HIGH"
            return self.accept_review_result(dispatch, result)
        finally:
            self.cleanup_bundle(candidate)

    def mismatched_artifact_result(self, candidate):
        try:
            lens = self.scenario["lenses"][0]
            dispatch = self.dispatch(candidate, lens, 98)
            self.registry.prepare(self.host, dispatch, probe=self.registry.probe(self.host))
            result = self.result(dispatch, lens)
            result["evidence"][0]["locator"] = "git-base:" + "0" * 40
            return self.accept_review_result(dispatch, result)
        finally:
            self.cleanup_bundle(candidate)

    def move_head_and_cancel(self, candidate):
        lens = self.scenario["lenses"][0]
        dispatch = self.dispatch(candidate, lens, 100)
        self.registry.prepare(self.host, dispatch, probe=self.registry.probe(self.host))
        self.write("src/beta.txt", "beta three\n")
        later_head = self.commit("later candidate")
        request = self.registry.request_cancel(self.host, dispatch["dispatch_id"])
        terminal = self.registry.confirm_cancelled(self.host, dispatch["dispatch_id"])
        outcome = {
            "dispatch": dispatch,
            "later_head": later_head,
            "request": request,
            "terminal": terminal,
            "bundle_path": candidate["bundle_path"],
        }
        self.cleanup_bundle(candidate)
        return outcome

    def address_and_increment(self, outcome):
        work_order = outcome["work_order"]
        original = work_order.read_text(encoding="utf-8")
        in_progress = original.replace("- [ ] **R1", "- [~] **R1", 1)
        work_order.write_text(in_progress, encoding="utf-8")
        self.write("src/alpha.txt", "alpha restored\n")
        first_fixing_head = self.commit_paths("fix R1", "src/alpha.txt")
        next_finding = in_progress.replace(
            "- [~] **R1",
            "- [x] **R1",
            1,
        ).replace(
            "Restore the required token.",
            "Restore the required token. Fixed by the R1 commit.",
            1,
        ).replace(
            "- [ ] **R2",
            "- [~] **R2",
            1,
        )
        work_order.write_text(next_finding, encoding="utf-8")
        self.write("tests/test_alpha.txt", "covers alpha, beta, and the empty-token case\n")
        fixing_head = self.commit_paths("fix R2", "tests/test_alpha.txt")
        incremental = self.freeze(
            base=outcome["candidate"]["head"],
            head=fixing_head,
            mode="append",
        )
        resolved = next_finding.replace(
            "- [~] **R2",
            "- [x] **R2",
            1,
        ).replace(
            "repair test-impact",
            "repair test-impact. Fixed by the R2 commit.",
            1,
        ).replace(
            f"**Reviewed up to commit:** `{outcome['candidate']['head']}`",
            f"**Reviewed up to commit:** `{fixing_head}`",
            1,
        ).replace(
            "**Judgment:** `changes-requested`",
            "**Judgment:** `approved`",
            1,
        )
        resolved += (
            "\n## Review pass - fixture - incremental\n\n"
            f"**Candidate base:** `{incremental['base']}`\n"
            f"**Candidate head:** `{incremental['head']}`\n"
            f"**Candidate branch:** `{incremental['branch']}`\n"
            f"**Candidate scope:** `{incremental['scope']}`\n"
            f"**Candidate path-set:** `sha256:{incremental['path_digest']}` `({incremental['path_count']} paths)`\n"
            f"**Candidate bundle:** `{incremental['bundle_path']}`\n"
            f"**Candidate bundle identity:** `sha256:{incremental['bundle_identity']}`\n"
            f"**Work-order path:** `{incremental['work_order']}`\n"
            f"**Work-order mode:** `{incremental['work_order_mode']}`\n"
            "**Pass judgment:** `approved`\n"
            "\nNo new findings.\n"
        )
        work_order.write_text(resolved, encoding="utf-8")
        result = {
            "original": original,
            "final": resolved,
            "first_fixing_head": first_fixing_head,
            "fixing_head": fixing_head,
            "first_fixing_paths": self.git(
                "diff-tree", "--no-commit-id", "--name-only", "-r", first_fixing_head
            ).splitlines(),
            "second_fixing_paths": self.git(
                "diff-tree", "--no-commit-id", "--name-only", "-r", fixing_head
            ).splitlines(),
        }
        self.cleanup_bundle(incremental)
        return result
