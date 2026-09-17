import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS = ROOT / ".agents" / "workflows"
PLUGIN_WORKFLOWS = ROOT / "plugins" / "process-standards" / "workflows"
sys.path.insert(0, str(WORKFLOWS))

from workflow_runtime import (
    ContractViolation,
    RepositoryStateProvider,
    WorkflowContract,
    select_state_provider,
)
from host_runtime import HostAdapterRegistry
from fixtures.routing_fixture import resolved_route


class WorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = WorkflowContract(WORKFLOWS, repository_root=ROOT)
        cls.contract_root = WORKFLOWS / "contract" / "v2"

    def example(self, name):
        return json.loads(
            (self.contract_root / "examples" / name).read_text(encoding="utf-8")
        )

    def boundary(self, capability):
        definition = self.contract.capabilities["delegable_capabilities"][capability]
        return {
            "may_decide": list(definition["may_decide"]),
            "must_not_decide": list(definition["must_not_decide"]),
        }

    def test_bundle_is_internally_compatible(self):
        self.assertEqual(
            {
                "version": "v2",
                "schemas": 5,
                "examples": 8,
                "capabilities": 5,
                "transitions": 9,
                "providers": 1,
                "decks": 1,
                "hosts": 2,
                "roles": 5,
                "release": "A",
                "compatibility_entries": 3,
            },
            self.contract.verify_bundle(),
        )

    def test_semantic_stage_selection_is_evidence_driven(self):
        self.assertEqual(
            ["critical", "strategic", "review", "implementation", "mechanical"],
            self.contract.capabilities["semantic_stage_routing"]["selection_priority"],
        )
        cases = {
            "architecture": "strategic",
            "ci-repair": "implementation",
            "deterministic-inventory": "mechanical",
            "pre-merge": "review",
            "security-sensitive": "critical",
        }
        for signal, expected in cases.items():
            with self.subTest(signal=signal):
                self.assertEqual(expected, self.contract.select_semantic_stage([signal]))
        self.assertEqual(
            "critical",
            self.contract.select_semantic_stage(["mechanical-verification", "high-risk"]),
        )
        with self.assertRaisesRegex(ContractViolation, "unknown semantic stage evidence"):
            self.contract.select_semantic_stage(["unknown"])

    def test_host_semantic_stage_routes_are_exact_and_model_free(self):
        codex = json.loads((WORKFLOWS / "hosts" / "codex.json").read_text(encoding="utf-8"))
        claude = json.loads((WORKFLOWS / "hosts" / "claude.json").read_text(encoding="utf-8"))
        expected = {
            "strategic": {"tags": ["architecture"]},
            "implementation": {},
            "mechanical": {
                "reversibility": "reversible",
                "blast": "file",
                "ambiguity": "specified",
                "verifiability": "compiler",
            },
            "review": {"tags": ["review"]},
            "critical": {"tags": ["security"]},
        }
        for manifest in (codex, claude):
            self.assertEqual(
                expected,
                {stage: value["route"] for stage, value in manifest["semantic_stages"].items()},
            )
            self.assertNotIn('"model":', json.dumps(manifest).lower())
        settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(
            "claude-sonnet-4-6", settings["env"]["ANTHROPIC_DEFAULT_HAIKU_MODEL"]
        )

    def test_every_compatibility_entry_and_replacement_is_an_installed_skill(self):
        skills = WORKFLOWS.parent / "skills"
        for name, entry in self.contract.compatibility["compatibility_entries"].items():
            with self.subTest(entry=name):
                self.assertTrue((skills / name / "SKILL.md").is_file())
                self.assertTrue((skills / entry["replacement"] / "SKILL.md").is_file())

    def test_a_compatibility_entry_stays_a_thin_entry_over_its_replacement(self):
        skills = WORKFLOWS.parent / "skills"
        for name, entry in self.contract.compatibility["compatibility_entries"].items():
            if entry["kind"] != "compatibility-entry":
                continue
            with self.subTest(entry=name):
                body = (skills / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(entry["replacement"], body)
                self.assertLess(len(body.splitlines()), 60)

    def test_release_a_cannot_deprecate_or_remove_an_entry(self):
        contract = WorkflowContract(WORKFLOWS, repository_root=ROOT)
        contract.compatibility["compatibility_entries"]["resume-plan"]["status"] = "deprecated"
        with self.assertRaisesRegex(ContractViolation, "cannot be deprecated before release B"):
            contract.verify_bundle()

    def test_a_compatibility_entry_cannot_replace_another_entry(self):
        contract = WorkflowContract(WORKFLOWS, repository_root=ROOT)
        contract.compatibility["compatibility_entries"]["resume-plan"]["replacement"] = "continue-roadmap"
        with self.assertRaisesRegex(ContractViolation, "names another compatibility entry"):
            contract.verify_bundle()

    def test_bundle_rejects_provider_capabilities_outside_compatibility(self):
        contract = WorkflowContract(WORKFLOWS, repository_root=ROOT)
        capabilities = contract.schemas["provider"]["properties"]["capabilities"]["items"]["enum"]
        capabilities.append("bind-session")
        with self.assertRaisesRegex(ContractViolation, "provider capabilities differ"):
            contract.verify_bundle()

    def test_shared_contract_cannot_trigger_as_a_skill(self):
        self.assertEqual([], list(WORKFLOWS.rglob("SKILL.md")))
        fixture = WORKFLOWS / "fixtures" / "workflow-contract-fixture.template.md"
        self.assertNotEqual("SKILL.md", fixture.name)

    def test_dispatch_rejects_absolute_paths_and_writer_mode_for_a_reader(self):
        dispatch = self.example("dispatch.example.json")
        dispatch["context"]["repository_paths"] = [str(ROOT)]
        with self.assertRaises(ContractViolation):
            self.contract.validate_dispatch(dispatch)

        for path in ("", "../outside", "/etc/passwd", "C:outside.txt", "\\Windows\\win.ini"):
            with self.subTest(path=path):
                dispatch = self.example("dispatch.example.json")
                dispatch["permissions"]["files"] = [path]
                with self.assertRaises(ContractViolation):
                    self.contract.validate_dispatch(dispatch)

        dispatch = self.example("dispatch.example.json")
        dispatch["permissions"]["mode"] = "write"
        with self.assertRaises(ContractViolation):
            self.contract.validate_dispatch(dispatch)

    def test_dispatch_rejects_a_changed_capability_boundary(self):
        dispatch = self.example("dispatch.example.json")
        dispatch["decision_boundary"]["may_decide"] = ["architecture"]
        with self.assertRaises(ContractViolation):
            self.contract.validate_dispatch(dispatch)

        dispatch = self.example("dispatch.example.json")
        dispatch["decision_boundary"]["must_not_decide"].remove("architecture")
        with self.assertRaises(ContractViolation):
            self.contract.validate_dispatch(dispatch)

    def test_mechanical_worker_requires_a_lease_and_writer_result(self):
        dispatch = self.example("dispatch.example.json")
        dispatch["capability"] = "mechanical-worker"
        dispatch["semantic_stage"] = "mechanical"
        dispatch["permissions"]["mode"] = "write"
        dispatch["decision_boundary"] = self.boundary("mechanical-worker")
        dispatch["permissions"]["files"].append(
            ".agents/workflows/contract/v2/capabilities.json"
        )
        with self.assertRaises(ContractViolation):
            self.contract.validate_dispatch(dispatch)

        dispatch["permissions"]["writer_lease"] = {
            "lease_id": "lease-001",
            "paths": [".agents/workflows/contract/v2/capabilities.json"],
        }
        self.contract.validate_dispatch(dispatch)

        dispatch["permissions"]["writer_lease"]["paths"] = ["other.txt"]
        with self.assertRaises(ContractViolation):
            self.contract.validate_dispatch(dispatch)
        dispatch["permissions"]["writer_lease"]["paths"] = [
            ".agents/workflows/contract/v2/capabilities.json"
        ]

        result = self.example("result.example.json")
        with self.assertRaises(ContractViolation):
            self.contract.validate_result(result, dispatch)

        result["writer"] = {
            "changed_paths": [".agents/workflows/contract/v2/capabilities.json"],
            "validation": ["workflow contract verifier passed"],
            "partial_paths": [],
        }
        self.contract.validate_result(result, dispatch)

        result["writer"]["changed_paths"] = ["../outside.txt"]
        with self.assertRaises(ContractViolation):
            self.contract.validate_result(result, dispatch)

        result["writer"]["changed_paths"] = ["other.txt"]
        with self.assertRaises(ContractViolation):
            self.contract.validate_result(result, dispatch)

    def test_result_must_match_dispatch_and_known_evidence(self):
        dispatch = self.example("dispatch.example.json")
        result = self.example("result.example.json")
        result["dispatch_id"] = "dispatch-002"
        with self.assertRaises(ContractViolation):
            self.contract.validate_result(result, dispatch)

    def test_review_lens_result_must_cite_its_exact_immutable_artifacts(self):
        dispatch = self.example("dispatch.example.json")
        dispatch["capability"] = "review-lens"
        dispatch["semantic_stage"] = "review"
        dispatch["decision_boundary"] = self.boundary("review-lens")
        empty_dispatch = json.loads(json.dumps(dispatch))
        empty_dispatch["context"]["immutable_artifacts"] = []
        with self.assertRaises(ContractViolation):
            self.contract.validate_dispatch(empty_dispatch)
        duplicate_dispatch = json.loads(json.dumps(dispatch))
        duplicate_dispatch["context"]["immutable_artifacts"].append(
            duplicate_dispatch["context"]["immutable_artifacts"][0]
        )
        with self.assertRaises(ContractViolation):
            self.contract.validate_dispatch(duplicate_dispatch)
        result = self.example("result.example.json")
        artifact_id = "frozen-candidate"
        result["evidence"].append(
            {
                "evidence_id": artifact_id,
                "kind": "immutable-artifact",
                "locator": dispatch["context"]["immutable_artifacts"][0],
                "detail": "The result used the frozen candidate from its dispatch.",
            }
        )
        result["claims"][0]["evidence_ids"].append(artifact_id)
        result["acceptance_conditions"][0]["evidence_ids"].append(artifact_id)

        self.contract.validate_result(result, dispatch)
        uncited_claim = json.loads(json.dumps(result))
        uncited_claim["claims"][0]["evidence_ids"].remove(artifact_id)
        with self.assertRaises(ContractViolation):
            self.contract.validate_result(uncited_claim, dispatch)
        uncited_condition = json.loads(json.dumps(result))
        uncited_condition["acceptance_conditions"][0]["evidence_ids"].remove(artifact_id)
        with self.assertRaises(ContractViolation):
            self.contract.validate_result(uncited_condition, dispatch)
        duplicate_artifact = json.loads(json.dumps(result))
        duplicate_artifact_id = "duplicate-frozen-candidate"
        duplicate_artifact["evidence"].append(
            {
                "evidence_id": duplicate_artifact_id,
                "kind": "immutable-artifact",
                "locator": dispatch["context"]["immutable_artifacts"][0],
                "detail": "The same frozen candidate was repeated.",
            }
        )
        duplicate_artifact["claims"][0]["evidence_ids"].append(duplicate_artifact_id)
        duplicate_artifact["acceptance_conditions"][0]["evidence_ids"].append(
            duplicate_artifact_id
        )
        with self.assertRaises(ContractViolation):
            self.contract.validate_result(duplicate_artifact, dispatch)
        result["evidence"][-1]["locator"] = "git:" + "0" * 40
        with self.assertRaises(ContractViolation):
            self.contract.validate_result(result, dispatch)

        result = self.example("result.example.json")
        result["claims"][0]["evidence_ids"] = ["missing"]
        with self.assertRaises(ContractViolation):
            self.contract.validate_result(result, dispatch)

    def test_transition_and_gate_records_are_parent_owned_and_typed(self):
        transition = self.contract.transition(
            "fallback", "The bounded role is unavailable.", dispatch_id="dispatch-001"
        )
        self.assertEqual("parent", transition["owner"])
        gate = self.contract.gate(
            "human",
            "open",
            "Tommy",
            "Choose the public contract.",
            "Resume after the choice is recorded in the plan.",
        )
        self.assertEqual("open", gate["status"])
        with self.assertRaises(ContractViolation):
            self.contract.transition("choose-stage", "Shared state chose a task stage.")


class WorkflowGenerationTests(unittest.TestCase):
    def normalized(self, path):
        return path.read_text(encoding="utf-8").replace("\r\n", "\n")

    def test_contract_provider_and_runtime_resources_are_generated_verbatim(self):
        paths = [
            path.relative_to(WORKFLOWS)
            for path in WORKFLOWS.rglob("*")
            if path.is_file()
            and path.suffix != ".pyc"
            and "__pycache__" not in path.parts
        ]
        for relative in paths:
            with self.subTest(path=relative.as_posix()):
                self.assertEqual(
                    self.normalized(WORKFLOWS / relative),
                    self.normalized(PLUGIN_WORKFLOWS / relative),
                )

    def test_generated_plugin_bundle_is_internally_compatible(self):
        self.assertEqual(
            WorkflowContract(WORKFLOWS).verify_bundle(),
            WorkflowContract(PLUGIN_WORKFLOWS).verify_bundle(),
        )

    def test_workflow_plugin_manifests_deliver_distinct_host_payloads_at_one_version(self):
        plugin = ROOT / "plugins" / "process-standards"
        codex = json.loads(
            (plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        claude = json.loads(
            (plugin / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertRegex(codex["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(codex["version"], claude["version"])
        self.assertEqual("./codex-skills/", codex["skills"])
        self.assertEqual("./hooks/codex-hooks.json", codex["hooks"])
        self.assertTrue((plugin / "codex-skills" / "persistent-workflow" / "SKILL.md").is_file())
        self.assertTrue((plugin / "skills" / "persistent-workflow" / "SKILL.md").is_file())
        self.assertTrue((plugin / "codex-agents" / "workflow-review-lens.toml").is_file())
        self.assertTrue((plugin / "agents" / "workflow-review-lens.md").is_file())
        self.assertTrue((plugin / "workflows" / "delivery_runtime.py").is_file())
        self.assertNotIn("workflows", codex)
        self.assertNotIn("workflows", claude)

    def test_generated_host_payloads_do_not_collide_with_shared_skills(self):
        shared = {path.parent.name for path in (ROOT / ".agents" / "skills").glob("*/SKILL.md")}
        claude = {path.parent.name for path in (ROOT / ".claude" / "workflow-skills").glob("*/SKILL.md")}
        codex = {path.parent.name for path in (ROOT / ".codex" / "workflow-skills").glob("*/SKILL.md")}
        self.assertEqual(set(), shared & claude)
        self.assertEqual(set(), shared & codex)

    def test_each_verifier_executes_its_adjacent_bundle(self):
        scripts = (WORKFLOWS / "verify.py", PLUGIN_WORKFLOWS / "verify.py")
        for script in scripts:
            with self.subTest(script=script):
                with tempfile.TemporaryDirectory(dir=ROOT) as temp:
                    root = Path(temp)
                    bundle = root / "workflows"
                    shutil.copytree(
                        script.parent,
                        bundle,
                        ignore=shutil.ignore_patterns("__pycache__"),
                    )
                    completed = subprocess.run(
                        [sys.executable, str(bundle / "verify.py"), "--root", str(root)],
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(0, completed.returncode, completed.stderr)
                    self.assertEqual([], list(bundle.rglob("*.pyc")))

    def test_fixture_skill_inlines_the_gate_contract_without_becoming_discoverable(self):
        template = self.normalized(
            WORKFLOWS / "fixtures" / "workflow-contract-fixture.template.md"
        )
        gates = self.normalized(WORKFLOWS / "contract" / "v2" / "gates.md").strip()
        expected = template.replace("{{WORKFLOW_CONTRACT_V2_GATES}}", gates)
        generated = self.normalized(
            PLUGIN_WORKFLOWS / "fixtures" / "workflow-contract-fixture.md"
        )
        self.assertEqual(expected, generated)
        self.assertNotIn("{{", generated)
        self.assertFalse((ROOT / "plugins" / "process-standards" / "skills" / "workflow-contract-fixture").exists())

    def test_role_fixture_renders_both_host_forms_from_one_body(self):
        body = self.normalized(WORKFLOWS / "fixtures" / "role-body.md").strip()
        codex = self.normalized(
            PLUGIN_WORKFLOWS / "fixtures" / "workflow-contract-fixture.toml"
        )
        claude = self.normalized(
            PLUGIN_WORKFLOWS / "fixtures" / "workflow-contract-fixture.claude.md"
        )
        self.assertIn(body, codex)
        self.assertIn(body, claude)
        self.assertIn('sandbox_mode = "read-only"', codex)
        self.assertIn("tools: Read, Glob, Grep", claude)

    def test_each_host_role_renders_from_one_canonical_body(self):
        codex_manifest = json.loads(
            (WORKFLOWS / "hosts" / "codex.json").read_text(encoding="utf-8")
        )
        claude_manifest = json.loads(
            (WORKFLOWS / "hosts" / "claude.json").read_text(encoding="utf-8")
        )
        self.assertEqual(set(codex_manifest["roles"]), set(claude_manifest["roles"]))
        for capability in codex_manifest["roles"]:
            with self.subTest(capability=capability):
                codex_role = codex_manifest["roles"][capability]
                claude_role = claude_manifest["roles"][capability]
                self.assertEqual(codex_role["body"], claude_role["body"])
                body = self.normalized(
                    WORKFLOWS / "hosts" / codex_role["body"]
                ).strip()
                codex_project = ROOT / ".codex" / "agents" / codex_role["filename"]
                codex_plugin = (
                    ROOT / "plugins" / "process-standards" / "codex-agents" / codex_role["filename"]
                )
                claude_project = ROOT / ".claude" / "agents" / claude_role["filename"]
                claude_plugin = (
                    ROOT / "plugins" / "process-standards" / "agents" / claude_role["filename"]
                )
                self.assertEqual(self.normalized(codex_project), self.normalized(codex_plugin))
                self.assertEqual(self.normalized(claude_project), self.normalized(claude_plugin))
                codex = tomllib.loads(self.normalized(codex_project))
                self.assertEqual(body, codex["developer_instructions"].strip())
                self.assertNotIn("model", codex)
                self.assertNotIn("model_reasoning_effort", codex)
                self.assertFalse(codex["agents"]["enabled"])
                expected_sandbox = "workspace-write" if capability == "mechanical-worker" else "read-only"
                self.assertEqual(expected_sandbox, codex["sandbox_mode"])
                claude = self.normalized(claude_project)
                frontmatter = {
                    key: value
                    for key, value in (
                        line.split(": ", 1)
                        for line in claude.split("---", 2)[1].strip().splitlines()
                    )
                }
                self.assertEqual(body, claude.split("---", 2)[2].strip())
                self.assertNotIn("model", frontmatter)
                self.assertNotIn("effort", frontmatter)
                self.assertEqual("Agent", frontmatter["disallowedTools"])
                self.assertNotIn("Agent", frontmatter["tools"].split(", "))
                if capability == "mechanical-worker":
                    self.assertNotIn("isolation", frontmatter)
                    self.assertEqual(
                        {"Read", "Glob", "Grep", "Write", "Edit", "Bash"},
                        set(frontmatter["tools"].split(", ")),
                    )
                else:
                    self.assertEqual(
                        {"Read", "Glob", "Grep"},
                        set(frontmatter["tools"].split(", ")),
                    )

    def test_host_schema_rejects_inconsistent_invocation_and_fallback_records(self):
        contract = WorkflowContract(WORKFLOWS, repository_root=ROOT)
        invocation = json.loads(
            (
                WORKFLOWS
                / "contract"
                / "v2"
                / "examples"
                / "host.invocation.example.json"
            ).read_text(encoding="utf-8")
        )
        invocation["mode"] = "write"
        with self.assertRaisesRegex(ContractViolation, "oneOf branches"):
            contract.validate("host", invocation)
        invocation["capability"] = "mechanical-worker"
        with self.assertRaisesRegex(ContractViolation, "oneOf branches"):
            contract.validate("host", invocation)
        fallback = json.loads(
            (
                WORKFLOWS
                / "contract"
                / "v2"
                / "examples"
                / "host.fallback.example.json"
            ).read_text(encoding="utf-8")
        )
        fallback["reason_code"] = "cancelled"
        with self.assertRaisesRegex(ContractViolation, "oneOf branches"):
            contract.validate("host", fallback)
        fallback["reason_code"] = "model-unavailable"
        fallback["parent_transition"] = "fallback"
        fallback["failed_model"] = "gpt-5.3-codex-spark"
        with self.assertRaisesRegex(ContractViolation, "oneOf branches"):
            contract.validate("host", fallback)
        fallback.pop("failed_model")
        fallback["next_model"] = "gpt-5.6-terra"
        with self.assertRaisesRegex(ContractViolation, "oneOf branches"):
            contract.validate("host", fallback)
        reconciliation = json.loads(
            (
                WORKFLOWS
                / "contract"
                / "v2"
                / "examples"
                / "host.reconciliation-required.example.json"
            ).read_text(encoding="utf-8")
        )
        for path in ("../outside", "C:/outside"):
            reconciliation["observed_paths"] = [path]
            with self.assertRaisesRegex(ContractViolation, "oneOf branches"):
                contract.validate("host", reconciliation)

    def test_codex_installer_previews_and_preserves_unrelated_agents(self):
        shell = shutil.which("pwsh") or shutil.which("powershell.exe")
        self.assertIsNotNone(shell)
        script = ROOT / ".codex" / "install-workflow-agents.ps1"
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            (project / ".git").mkdir()
            target = project / ".codex" / "agents"
            target.mkdir(parents=True)
            unrelated = target / "unrelated.toml"
            unrelated.write_text('name = "unrelated"\n', encoding="utf-8")
            arguments = [shell, "-NoProfile"]
            if Path(shell).name.lower() == "powershell.exe":
                arguments += ["-ExecutionPolicy", "Bypass"]
            preview = subprocess.run(
                [*arguments, "-File", str(script), "-ProjectRoot", str(project)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, preview.returncode, preview.stderr)
            self.assertIn("PREVIEW ONLY: 5 change(s)", preview.stdout)
            applied = subprocess.run(
                [*arguments, "-File", str(script), "-ProjectRoot", str(project), "-Apply"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, applied.returncode, applied.stderr)
            self.assertEqual(5, len(list(target.glob("workflow-*.toml"))))
            self.assertEqual('name = "unrelated"\n', unrelated.read_text(encoding="utf-8"))
            repeated = subprocess.run(
                [*arguments, "-File", str(script), "-ProjectRoot", str(project), "-Apply"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, repeated.returncode, repeated.stderr)
            self.assertIn("INSTALLED: 0 change(s)", repeated.stdout)

    def test_the_authored_installer_refuses_to_run_without_generated_roles(self):
        shell = shutil.which("pwsh") or shutil.which("powershell.exe")
        self.assertIsNotNone(shell)
        script = WORKFLOWS / "hosts" / "install-codex-agents.ps1"
        arguments = [shell, "-NoProfile"]
        if Path(shell).name.lower() == "powershell.exe":
            arguments += ["-ExecutionPolicy", "Bypass"]
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            (project / ".git").mkdir()
            attempted = subprocess.run(
                [*arguments, "-File", str(script), "-ProjectRoot", str(project)],
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(0, attempted.returncode)
        self.assertIn("No generated role files beside this installer", attempted.stderr)

    def test_codex_installer_rejects_a_reparse_point_target(self):
        shell = shutil.which("pwsh") or shutil.which("powershell.exe")
        self.assertIsNotNone(shell)
        script = ROOT / ".codex" / "install-workflow-agents.ps1"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "project"
            outside = root / "outside"
            (project / ".git").mkdir(parents=True)
            (project / ".codex").mkdir()
            outside.mkdir()
            target = project / ".codex" / "agents"
            if os.name == "nt":
                linked = subprocess.run(
                    ["cmd.exe", "/D", "/C", "mklink", "/J", str(target), str(outside)],
                    capture_output=True,
                    text=True,
                )
                if linked.returncode:
                    self.skipTest(linked.stderr or linked.stdout)
            else:
                target.symlink_to(outside, target_is_directory=True)
            arguments = [shell, "-NoProfile"]
            if Path(shell).name.lower() == "powershell.exe":
                arguments += ["-ExecutionPolicy", "Bypass"]
            completed = subprocess.run(
                [*arguments, "-File", str(script), "-ProjectRoot", str(project), "-Apply"],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, completed.returncode)
            self.assertIn("reparse point", completed.stderr)
            self.assertEqual([], list(outside.iterdir()))

    def test_codex_installer_ignores_unrelated_source_agents(self):
        shell = shutil.which("pwsh") or shutil.which("powershell.exe")
        self.assertIsNotNone(shell)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bundle = root / "bundle" / ".codex"
            source = bundle / "agents"
            shutil.copytree(ROOT / ".codex" / "agents", source)
            script = bundle / "install-workflow-agents.ps1"
            shutil.copy2(ROOT / ".codex" / script.name, script)
            (source / "unrelated.toml").write_text('name = "unrelated"\n', encoding="utf-8")
            project = root / "project"
            (project / ".git").mkdir(parents=True)
            arguments = [shell, "-NoProfile"]
            if Path(shell).name.lower() == "powershell.exe":
                arguments += ["-ExecutionPolicy", "Bypass"]
            completed = subprocess.run(
                [*arguments, "-File", str(script), "-ProjectRoot", str(project), "-Apply"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            target = project / ".codex" / "agents"
            self.assertEqual(5, len(list(target.glob("workflow-*.toml"))))
            self.assertFalse((target / "unrelated.toml").exists())

    def test_generator_preserves_unrelated_host_agents(self):
        shell = shutil.which("pwsh") or shutil.which("powershell.exe")
        self.assertIsNotNone(shell)
        with tempfile.TemporaryDirectory() as temp:
            repository = Path(temp) / "repository"
            shutil.copytree(
                ROOT,
                repository,
                ignore=shutil.ignore_patterns(".git", "__pycache__"),
            )
            unrelated = (
                repository / ".claude" / "agents" / "unrelated.md",
                repository / ".codex" / "agents" / "unrelated.toml",
                repository / "plugins" / "process-standards" / "agents" / "unrelated.md",
                repository / "plugins" / "process-standards" / "codex-agents" / "unrelated.toml",
            )
            for path in unrelated:
                path.write_text("unrelated\n", encoding="utf-8")
            arguments = [shell, "-NoProfile"]
            if Path(shell).name.lower() == "powershell.exe":
                arguments += ["-ExecutionPolicy", "Bypass"]
            completed = subprocess.run(
                [
                    *arguments,
                    "-File",
                    str(repository / ".agents" / "sync-generated.ps1"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            for path in unrelated:
                self.assertEqual("unrelated\n", path.read_text(encoding="utf-8"))


class HostAdapterTests(unittest.TestCase):
    def setUp(self):
        self.contract = WorkflowContract(WORKFLOWS, repository_root=ROOT)
        self.runner = lambda *arguments, **keywords: SimpleNamespace(
            returncode=0,
            stdout="host 1.0\n",
            stderr="",
        )
        self.observed_changes = set()
        self.observer = SimpleNamespace(
            capture=lambda: "baseline",
            changed_since=lambda baseline: set(self.observed_changes),
        )

    def routed_values(self, host, parameters):
        return resolved_route(host, parameters)

    def registry(self, resolver=lambda command: command, repository_root=ROOT, observer=None):
        return HostAdapterRegistry(
            WORKFLOWS,
            repository_root,
            executable_resolver=resolver,
            command_runner=self.runner,
            repository_observer=observer or self.observer,
            route_provider=self.routed_values,
        )

    def dispatch(self, capability="evidence-explorer", dispatch_id="dispatch-001"):
        dispatch = json.loads(
            (WORKFLOWS / "contract" / "v2" / "examples" / "dispatch.example.json").read_text(
                encoding="utf-8"
            )
        )
        dispatch["dispatch_id"] = dispatch_id
        dispatch["capability"] = capability
        definition = self.contract.capabilities["delegable_capabilities"][capability]
        dispatch["semantic_stage"] = definition["default_semantic_stage"]
        dispatch["permissions"]["mode"] = definition["mode"]
        dispatch["decision_boundary"] = {
            "may_decide": list(definition["may_decide"]),
            "must_not_decide": list(definition["must_not_decide"]),
        }
        if capability == "mechanical-worker":
            path = ".agents/workflows/contract/v2/capabilities.json"
            dispatch["permissions"]["files"] = [path]
            dispatch["permissions"]["writer_lease"] = {
                "lease_id": f"lease-{dispatch_id}",
                "paths": [path],
            }
        else:
            dispatch["permissions"].pop("writer_lease", None)
        return dispatch

    def result(self, dispatch, changed_paths=(), partial_paths=()):
        result = json.loads(
            (WORKFLOWS / "contract" / "v2" / "examples" / "result.example.json").read_text(
                encoding="utf-8"
            )
        )
        for field in ("workflow_id", "workflow_run_id", "stage_id", "dispatch_id"):
            result[field] = dispatch[field]
        evidence_id = result["evidence"][0]["evidence_id"]
        result["acceptance_conditions"] = [
            {
                "condition": condition,
                "passed": True,
                "evidence_ids": [evidence_id],
                "detail": "The condition passed.",
            }
            for condition in dispatch["acceptance_conditions"]
        ]
        if dispatch["capability"] == "mechanical-worker":
            result["writer"] = {
                "changed_paths": list(changed_paths),
                "validation": ["focused validation passed"],
                "partial_paths": list(partial_paths),
            }
        return result

    def test_native_probes_report_generated_roles_or_parent_fallback(self):
        smoke = WORKFLOWS / "hosts" / "smoke.py"
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                completed = subprocess.run(
                    [sys.executable, str(smoke), "--root", str(ROOT), "--host", host],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(0, completed.returncode, completed.stderr)
                probe = json.loads(completed.stdout)
                self.contract.validate("host", probe)
                self.assertEqual(5, len(probe["available_roles"]))
                if probe["status"] == "unavailable":
                    self.assertEqual("host-unavailable", probe["reason_code"])

    def test_unavailable_host_returns_typed_parent_fallback(self):
        registry = self.registry(lambda command: None)
        dispatch = self.dispatch()
        probe = registry.probe("codex")
        self.assertEqual("unavailable", probe["status"])
        fallback = registry.prepare("codex", dispatch, probe=probe)
        self.assertEqual("host-fallback", fallback["record_type"])
        self.assertEqual("host-unavailable", fallback["reason_code"])

    def test_unavailable_role_and_model_use_declared_typed_routes(self):
        registry = self.registry()
        dispatch = self.dispatch()
        probe = registry.probe("claude")
        probe["available_roles"].remove("evidence-explorer")
        fallback = registry.prepare("claude", dispatch, probe=probe)
        self.assertEqual("role-unavailable", fallback["reason_code"])
        probe = registry.probe("claude")
        fallback = registry.prepare(
            "claude", dispatch, probe=probe, available_models={"opus"}
        )
        self.assertEqual("model-unavailable", fallback["reason_code"])
        self.assertEqual("fallback", fallback["parent_transition"])
        dispatch["semantic_stage"] = "strategic"
        paused = registry.prepare(
            "claude", dispatch, probe=probe, available_models={"sonnet"}
        )
        self.assertEqual("pause", paused["parent_transition"])
        self.assertEqual("model-unavailable", paused["reason_code"])

    def test_codex_review_uses_the_routed_complex_reasoning_model(self):
        registry = self.registry()
        dispatch = self.dispatch("review-lens")
        probe = registry.probe("codex")

        invocation = registry.prepare(
            "codex",
            dispatch,
            probe=probe,
            available_models={"gpt-5.6-sol"},
        )

        self.assertEqual("review", invocation["semantic_stage"])
        self.assertEqual("L1", invocation["routing_lane"])
        self.assertEqual("gpt-5.6-sol", invocation["primary_model"])
        self.assertEqual("gpt-5.6-sol", invocation["model"])
        self.assertEqual("primary", invocation["model_selection"])
        self.assertEqual("workflow_review_lens", invocation["agent_name"])
        self.assertEqual("workflow_review_lens", invocation["role_agent_name"])
        self.assertEqual("../roles/review-lens.md", invocation["role_body"])

        paused = registry.prepare(
            "codex",
            self.dispatch("review-lens", "dispatch-002"),
            probe=probe,
            available_models={"gpt-5.6-terra"},
        )
        self.assertEqual("model-unavailable", paused["reason_code"])
        self.assertEqual("pause", paused["parent_transition"])

    def test_codex_review_launch_failure_pauses_without_substituting_a_lane(self):
        registry = self.registry()
        dispatch = self.dispatch("review-lens")
        probe = registry.probe("codex")
        primary = registry.prepare("codex", dispatch, probe=probe)

        fallback = registry.report_model_unavailable(
            "codex",
            dispatch,
            primary,
            "The routed model is unavailable.",
        )

        self.assertEqual("model-unavailable", fallback["reason_code"])
        self.assertEqual("pause", fallback["parent_transition"])
        self.assertEqual("gpt-5.6-sol", fallback["failed_model"])
        self.assertIsNone(fallback["next_model"])

    def test_claude_nondefault_stage_uses_routed_values_with_the_role_agent(self):
        registry = self.registry()
        dispatch = self.dispatch("evidence-explorer")
        dispatch["semantic_stage"] = "strategic"

        invocation = registry.prepare(
            "claude",
            dispatch,
            probe=registry.probe("claude"),
        )

        self.assertEqual("opus", invocation["model"])
        self.assertEqual("primary", invocation["model_selection"])
        self.assertEqual("L1", invocation["routing_lane"])
        self.assertEqual("workflow-evidence-explorer", invocation["agent_name"])
        self.assertEqual("workflow-evidence-explorer", invocation["role_agent_name"])

    def test_available_host_rejects_missing_routing_output(self):
        registry = HostAdapterRegistry(
            WORKFLOWS,
            ROOT,
            executable_resolver=lambda command: command,
            command_runner=self.runner,
            repository_observer=self.observer,
        )
        with self.assertRaisesRegex(ContractViolation, "requires resolved routing output"):
            registry.prepare("codex", self.dispatch(), probe=registry.probe("codex"))

    def test_partial_role_install_keeps_available_capabilities_usable(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            target = project / ".codex" / "agents"
            target.mkdir(parents=True)
            target.joinpath("workflow-evidence-explorer.toml").write_text("", encoding="utf-8")
            registry = self.registry(repository_root=project)
            probe = registry.probe("codex")
            self.assertEqual("available", probe["status"])
            self.assertEqual(["evidence-explorer"], probe["available_roles"])
            available = registry.prepare("codex", self.dispatch(), probe=probe)
            self.assertEqual("host-invocation", available["record_type"])
            missing = registry.prepare(
                "codex",
                self.dispatch("log-analyst", "dispatch-002"),
                probe=probe,
            )
            self.assertEqual("role-unavailable", missing["reason_code"])

    def test_probe_identity_and_empty_versions_cannot_claim_availability(self):
        empty_runner = lambda *arguments, **keywords: SimpleNamespace(
            returncode=0,
            stdout="",
            stderr="",
        )
        registry = HostAdapterRegistry(
            WORKFLOWS,
            ROOT,
            executable_resolver=lambda command: command,
            command_runner=empty_runner,
        )
        probe = registry.probe("codex")
        self.assertEqual("unavailable", probe["status"])
        self.assertEqual("host-unavailable", probe["reason_code"])
        foreign_probe = self.registry().probe("claude")
        with self.assertRaisesRegex(ContractViolation, "different host"):
            registry.prepare("codex", self.dispatch(), probe=foreign_probe)

    def test_invalid_result_falls_back_and_releases_dispatch(self):
        registry = self.registry()
        dispatch = self.dispatch()
        invocation = registry.prepare("codex", dispatch, probe=registry.probe("codex"))
        self.assertEqual("host-invocation", invocation["record_type"])
        result = json.loads(
            (WORKFLOWS / "contract" / "v2" / "examples" / "result.example.json").read_text(
                encoding="utf-8"
            )
        )
        result["dispatch_id"] = "wrong-dispatch"
        fallback = registry.accept_result("codex", dispatch, result)
        self.assertEqual("invalid-result", fallback["reason_code"])
        self.assertEqual({}, registry.active_dispatches)

    def test_only_the_prepared_host_can_complete_an_active_dispatch(self):
        registry = self.registry()
        dispatch = self.dispatch()
        registry.prepare("codex", dispatch, probe=registry.probe("codex"))
        result = json.loads(
            (WORKFLOWS / "contract" / "v2" / "examples" / "result.example.json").read_text(
                encoding="utf-8"
            )
        )
        foreign = registry.accept_result("claude", dispatch, result)
        self.assertEqual("invalid-result", foreign["reason_code"])
        self.assertIn(dispatch["dispatch_id"], registry.active_dispatches)
        accepted = registry.accept_result("codex", dispatch, result)
        self.assertEqual("complete", accepted["status"])
        replayed = registry.accept_result("codex", dispatch, result)
        self.assertEqual("invalid-result", replayed["reason_code"])

    def test_independent_readers_can_remain_active_together(self):
        registry = self.registry()
        first = self.dispatch(dispatch_id="dispatch-001")
        second = self.dispatch(dispatch_id="dispatch-002")
        second["stage_id"] = "contract-discovery-secondary"
        probe = registry.probe("codex")
        registry.prepare("codex", first, probe=probe)
        registry.prepare("codex", second, probe=probe)
        self.assertEqual({"dispatch-001", "dispatch-002"}, set(registry.active_dispatches))

    def test_equivalent_semantic_stage_dispatch_is_rejected(self):
        registry = self.registry()
        first = self.dispatch(dispatch_id="dispatch-001")
        duplicate = self.dispatch(dispatch_id="dispatch-002")
        probe = registry.probe("codex")
        registry.prepare("codex", first, probe=probe)
        with self.assertRaisesRegex(ContractViolation, "equivalent semantic-stage"):
            registry.prepare("codex", duplicate, probe=probe)

    def test_writer_result_paths_must_match_observed_leased_changes(self):
        registry = self.registry()
        dispatch = self.dispatch("mechanical-worker")
        leased = dispatch["permissions"]["writer_lease"]["paths"][0]
        registry.prepare("claude", dispatch, probe=registry.probe("claude"))
        self.observed_changes = {leased}
        accepted = registry.accept_result(
            "claude",
            dispatch,
            self.result(dispatch, changed_paths=[leased]),
        )
        self.assertEqual("complete", accepted["status"])

        dispatch = self.dispatch("mechanical-worker", "dispatch-002")
        registry.prepare("claude", dispatch, probe=registry.probe("claude"))
        self.observed_changes = {".agents/workflows/unleased.txt"}
        rejected = registry.accept_result("claude", dispatch, self.result(dispatch))
        self.assertEqual("host-reconciliation-required", rejected["record_type"])
        self.assertEqual("invalid-result", rejected["reason_code"])
        self.assertIn("unleased", rejected["detail"])
        self.assertEqual([".agents/workflows/unleased.txt"], rejected["observed_paths"])
        with self.assertRaisesRegex(ContractViolation, "another writer lease"):
            registry.prepare(
                "claude",
                self.dispatch("mechanical-worker", "dispatch-003"),
                probe=registry.probe("claude"),
            )
        completed = registry.complete_reconciliation("claude", dispatch["dispatch_id"])
        self.assertEqual("invalid-result", completed["reason_code"])

        dispatch = self.dispatch("mechanical-worker", "dispatch-004")
        leased = dispatch["permissions"]["writer_lease"]["paths"][0]
        self.observed_changes = set()
        registry.prepare("claude", dispatch, probe=registry.probe("claude"))
        self.observed_changes = {leased}
        invalid = self.result(dispatch, changed_paths=[leased])
        invalid["evidence"] = []
        rejected = registry.accept_result("claude", dispatch, invalid)
        self.assertEqual("host-reconciliation-required", rejected["record_type"])
        self.assertEqual([leased], rejected["observed_paths"])
        registry.complete_reconciliation("claude", dispatch["dispatch_id"])

    def test_simultaneous_writers_have_exactly_one_lease_winner(self):
        registries = (self.registry(), self.registry())
        probe = registries[0].probe("claude")
        dispatches = (
            self.dispatch("mechanical-worker", "dispatch-001"),
            self.dispatch("mechanical-worker", "dispatch-002"),
        )
        barrier = Barrier(2)

        def prepare(pair):
            registry, dispatch = pair
            barrier.wait()
            try:
                return registry.prepare("claude", dispatch, probe=probe)["record_type"]
            except ContractViolation:
                return "rejected"

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(
                pool.map(
                    prepare,
                    zip(registries, dispatches),
                )
            )
        self.assertEqual(["host-invocation", "rejected"], sorted(outcomes))
        for registry, dispatch in zip(registries, dispatches):
            if dispatch["dispatch_id"] in registry.active_dispatches:
                registry.request_cancel("claude", dispatch["dispatch_id"])
                registry.confirm_cancelled("claude", dispatch["dispatch_id"])

    def test_subprocess_writers_have_exactly_one_repository_lease_winner(self):
        worker = (
            ROOT
            / ".agents"
            / "hooks"
            / "tests"
            / "fixtures"
            / "workflow_writer_lease_worker.py"
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repository = root / "repository"
            control = root / "control"
            control.mkdir()
            subprocess.run(["git", "init", "-q", str(repository)], check=True)
            processes = [
                subprocess.Popen(
                    [
                        sys.executable,
                        "-B",
                        str(worker),
                        str(WORKFLOWS),
                        str(repository),
                        str(control),
                        str(index),
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for index in range(2)
            ]
            deadline = time.monotonic() + 10
            while len(list(control.glob("ready-*"))) < 2:
                if time.monotonic() >= deadline:
                    for process in processes:
                        process.kill()
                    self.fail("writer subprocesses did not reach the barrier")
                time.sleep(0.01)
            (control / "go").write_text("", encoding="utf-8")
            completed = [process.communicate(timeout=10) for process in processes]
            for process, (_, stderr) in zip(processes, completed):
                self.assertEqual(0, process.returncode, stderr)
            self.assertEqual(
                ["rejected", "winner"],
                sorted(stdout.strip() for stdout, _ in completed),
            )

    def test_cancellation_retains_writer_lease_until_host_confirmation(self):
        registry = self.registry()
        first = self.dispatch("mechanical-worker", "dispatch-001")
        second = self.dispatch("mechanical-worker", "dispatch-002")
        probe = registry.probe("claude")
        registry.prepare("claude", first, probe=probe)
        with self.assertRaisesRegex(ContractViolation, "another writer lease"):
            registry.prepare("claude", second, probe=probe)
        request = registry.request_cancel("claude", first["dispatch_id"])
        self.assertEqual("host-cancel-request", request["record_type"])
        with self.assertRaisesRegex(ContractViolation, "another writer lease"):
            registry.prepare("claude", second, probe=probe)
        leased = first["permissions"]["writer_lease"]["paths"][0]
        self.observed_changes = {leased}
        reconciliation = registry.confirm_cancelled("claude", first["dispatch_id"])
        self.assertEqual("host-reconciliation-required", reconciliation["record_type"])
        self.assertEqual("cancelled", reconciliation["reason_code"])
        self.assertEqual([leased], reconciliation["observed_paths"])
        with self.assertRaisesRegex(ContractViolation, "another writer lease"):
            registry.prepare("claude", second, probe=probe)
        cancelled = registry.complete_reconciliation("claude", first["dispatch_id"])
        self.assertEqual("cancelled", cancelled["reason_code"])
        self.observed_changes = set()
        invocation = registry.prepare("claude", second, probe=probe)
        self.assertEqual(second["permissions"]["writer_lease"]["lease_id"], invocation["writer_lease_id"])
        registry.request_cancel("claude", second["dispatch_id"])
        registry.confirm_cancelled("claude", second["dispatch_id"])

    def test_invalid_cancellation_terminal_keeps_dispatch_and_lease_active(self):
        registry = self.registry()
        first = self.dispatch("mechanical-worker", "dispatch-001")
        second = self.dispatch("mechanical-worker", "dispatch-002")
        probe = registry.probe("claude")
        registry.prepare("claude", first, probe=probe)
        registry.request_cancel("claude", first["dispatch_id"])
        with self.assertRaises(ContractViolation):
            registry.confirm_cancelled("claude", first["dispatch_id"], detail="")
        self.assertIn(first["dispatch_id"], registry.active_dispatches)
        with self.assertRaisesRegex(ContractViolation, "another writer lease"):
            registry.prepare("claude", second, probe=probe)
        registry.confirm_cancelled("claude", first["dispatch_id"])


class RepositoryProviderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        subprocess.run(["git", "init", "-q", "-b", "Feature/provider-fixture", str(self.root)], check=True)
        subprocess.run(
            ["git", "-C", str(self.root), "config", "user.email", "provider@example.test"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.root), "config", "user.name", "Provider Test"],
            check=True,
        )
        plan_dir = self.root / "plans" / "runtime"
        plan_dir.mkdir(parents=True)
        (plan_dir / "RUNTIME_PLAN.md").write_text("# Runtime plan\n", encoding="utf-8")
        (plan_dir / "RUNTIME_ROADMAP.md").write_text("# Runtime roadmap\n", encoding="utf-8")
        review_dir = self.root / "reviews"
        review_dir.mkdir()
        self.review = review_dir / "runtime.md"
        self.review.write_text(
            "\n".join(
                [
                    "# Runtime review",
                    "",
                    "## Findings",
                    "",
                    "- [ ] **BUG1 — HIGH — correctness** — `runtime.py:1`",
                    "- [~] **NAT1 — MEDIUM — native** — `runtime.py:2`",
                    "- [x] **SEC1 — HIGH — security** — `runtime.py:3`",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        self.ledger = plan_dir / "RUNTIME_PROGRESS.md"
        self.ledger.write_text(
            "\n".join(
                [
                    "# Runtime progress",
                    "",
                    "- Plan: `plans/runtime/RUNTIME_PLAN.md`",
                    "- Roadmap: `plans/runtime/RUNTIME_ROADMAP.md`",
                    "- Roadmap item: `runtime/provider-fixture`",
                    f"- Worktree: `{self.root}`",
                    "- Branch: `Feature/provider-fixture`",
                    "- PR: `not opened`",
                    "",
                    "## Current state",
                    "",
                    "Contract runtime implementation is active.",
                    "",
                    "## Next Steps",
                    "",
                    "Run the contract verification gate.",
                    "",
                    "## Verification",
                    "",
                    "Pending.",
                    "",
                    "## Reviews",
                    "",
                    "Current work order: [runtime review](reviews/runtime.md).",
                    "",
                    "## Decisions, discoveries, blockers, and deviations",
                    "",
                    "- The repository artifacts remain portable.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        subprocess.run(
            ["git", "-C", str(self.root), "commit", "-q", "-m", "provider fixture"],
            check=True,
        )
        self.contract = WorkflowContract(WORKFLOWS)
        self.provider = RepositoryStateProvider(self.root, self.contract)

    def test_repository_provider_resolves_portable_state_and_git_identity(self):
        self.assertEqual("available", self.provider.probe()["status"])
        self.assertEqual(self.root, self.provider.contract.repository_root)
        state = self.provider.resolve(
            "plans/runtime/RUNTIME_PROGRESS.md",
            "runtime/provider-fixture-001",
            "contract-verification",
        )
        self.assertEqual("runtime/provider-fixture", state["workflow_id"])
        self.assertEqual("Feature/provider-fixture", state["owner"]["branch"])
        self.assertEqual("continue", state["transition"]["transition"])
        self.assertEqual(
            ["reviews/runtime.md#BUG1", "reviews/runtime.md#NAT1"],
            state["open_findings"],
        )
        self.assertIs(state, self.provider.validate_checkpoint(state))

    def test_repository_provider_rejects_stale_worktree_identity(self):
        text = self.ledger.read_text(encoding="utf-8")
        self.ledger.write_text(
            text.replace(str(self.root), str(self.root / "other")),
            encoding="utf-8",
        )
        with self.assertRaises(ContractViolation):
            self.provider.resolve(
                "plans/runtime/RUNTIME_PROGRESS.md",
                "runtime/provider-fixture-001",
                "contract-verification",
            )

    def test_repository_provider_rejects_a_missing_review_work_order(self):
        text = self.ledger.read_text(encoding="utf-8")
        self.ledger.write_text(
            text.replace("reviews/runtime.md", "reviews/missing.md"),
            encoding="utf-8",
        )
        with self.assertRaises(ContractViolation):
            self.provider.resolve(
                "plans/runtime/RUNTIME_PROGRESS.md",
                "runtime/provider-fixture-001",
                "contract-verification",
            )

    def test_repository_provider_rejects_stale_checkpoint_state(self):
        state = self.provider.resolve(
            "plans/runtime/RUNTIME_PROGRESS.md",
            "runtime/provider-fixture-001",
            "contract-verification",
        )
        state["owner"]["head"] = "stale"
        with self.assertRaises(ContractViolation):
            self.provider.validate_checkpoint(state)

        state = self.provider.resolve(
            "plans/runtime/RUNTIME_PROGRESS.md",
            "runtime/provider-fixture-001",
            "contract-verification",
        )
        text = self.ledger.read_text(encoding="utf-8")
        self.ledger.write_text(
            text.replace("Run the contract verification gate.", "Run the changed gate."),
            encoding="utf-8",
        )
        with self.assertRaises(ContractViolation):
            self.provider.validate_checkpoint(state)

    def test_kandev_is_an_external_deck_not_a_state_provider(self):
        selected = select_state_provider(self.root, self.contract)
        self.assertIsInstance(selected, RepositoryStateProvider)
        self.assertEqual(["repository"], self.contract.schemas["provider"]["properties"]["provider_id"]["enum"])
        deck = self.contract.compatibility["execution_decks"]["kandev"]
        self.assertFalse(deck["workflow_state_api"])
        self.assertEqual("native-cli-passthrough", deck["launch_mode"])
        resource = (self.contract.contract_root / deck["resource"]).resolve()
        self.assertIn("CLI Passthrough", resource.read_text(encoding="utf-8"))

    def test_contract_binding_rejects_a_different_repository(self):
        contract = WorkflowContract(WORKFLOWS, repository_root=ROOT)
        with self.assertRaises(ContractViolation):
            RepositoryStateProvider(self.root, contract)
        with self.assertRaises(ContractViolation):
            select_state_provider(self.root, contract)

    def test_selected_provider_rejects_a_link_escape(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        outside_root = Path(outside.name).resolve()
        (outside_root / "outside.txt").write_text("outside", encoding="utf-8")
        (outside_root / "OUTSIDE_PLAN.md").write_text("# Outside\n", encoding="utf-8")
        link = self.root / "escape"
        if os.name == "nt":
            completed = subprocess.run(
                ["cmd.exe", "/D", "/C", "mklink", "/J", str(link), str(outside_root)],
                capture_output=True,
                text=True,
            )
            if completed.returncode:
                self.skipTest(completed.stderr or completed.stdout)
        else:
            link.symlink_to(outside_root, target_is_directory=True)

        selected = select_state_provider(self.root, self.contract)
        dispatch = json.loads(
            (WORKFLOWS / "contract" / "v2" / "examples" / "dispatch.example.json").read_text(
                encoding="utf-8"
            )
        )
        dispatch["permissions"]["files"] = ["escape/outside.txt"]
        with self.assertRaises(ContractViolation):
            selected.contract.validate_dispatch(dispatch)

        text = self.ledger.read_text(encoding="utf-8")
        self.ledger.write_text(
            text.replace("plans/runtime/RUNTIME_PLAN.md", "escape/OUTSIDE_PLAN.md"),
            encoding="utf-8",
        )
        with self.assertRaises(ContractViolation):
            selected.resolve(
                "plans/runtime/RUNTIME_PROGRESS.md",
                "runtime/provider-fixture-001",
                "contract-verification",
            )


if __name__ == "__main__":
    unittest.main()
