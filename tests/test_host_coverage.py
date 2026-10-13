import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/base/policy/plan-artifacts/scripts/host_coverage.py"
SPEC = importlib.util.spec_from_file_location("host_coverage", SCRIPT)
coverage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(coverage)
HEAD = "a" * 40


def record(stage="plan"):
    value = {
        "schema_version": 1,
        "shared_source": ".agents/base/policy/plan-artifacts/SKILL.md",
        "hosts": [
            {
                "host": "claude",
                "behavior": "loads the shared plan contract",
                "source": ".claude/skills/plan-artifacts/SKILL.md",
                "mapping": "plugins/base/skills/plan-artifacts/SKILL.md",
                "verification": {"level": "planned", "result": "pending", "evidence": "focused command is recorded"},
            },
            {
                "host": "codex",
                "behavior": "loads the shared plan contract",
                "source": ".codex/skills/plan-artifacts/SKILL.md",
                "mapping": "plugins/base/codex-skills/plan-artifacts/SKILL.md",
                "verification": {"level": "planned", "result": "pending", "evidence": "focused command is recorded"},
            },
        ],
    }
    if stage == "review":
        value["candidate_head"] = HEAD
        for item in value["hosts"]:
            item["verification"] = {"level": "source", "result": "passed", "evidence": "focused source test passed"}
    return value


def write_document(directory, value):
    path = Path(directory) / "PLAN.md"
    path.write_text("# Coverage\n\n```agent-host-coverage\n" + json.dumps(value) + "\n```\n", encoding="utf-8")
    return path


class HostCoverageTests(unittest.TestCase):
    def test_agent_surface_classifies_shared_sources_and_mapping(self):
        paths = coverage.agent_surface_paths([
            ".agents/plugins/sources.json", ".agents/workflows/workflow_ops.py", ".claude/skills/example/SKILL.md",
            ".codex/skills/example/SKILL.md", "docs/guide.md", "product/AGENTS.md",
        ])
        self.assertEqual([
            ".agents/plugins/sources.json", ".agents/workflows/workflow_ops.py", ".claude/skills/example/SKILL.md",
            ".codex/skills/example/SKILL.md", "product/AGENTS.md",
        ], paths)

    def test_ordinary_product_paths_do_not_require_coverage(self):
        self.assertEqual([], coverage.agent_surface_paths(["src/api.py", "docs/guide.md", "tests/test_api.py"]))

    def test_requires_each_host(self):
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                value = record()
                value["hosts"] = [entry for entry in value["hosts"] if entry["host"] != host]
                errors = coverage.validate_record(value, "plan")
                self.assertTrue(errors)
                self.assertIn("hosts must contain exactly Claude and Codex", errors)

    def test_review_rejects_pending_evidence(self):
        value = record("review")
        value["hosts"][0]["verification"] = {"level": "planned", "result": "pending", "evidence": "planned command"}
        errors = coverage.validate_record(value, "review", HEAD)
        self.assertTrue(any("review evidence" in error for error in errors))

    def test_documented_host_exception_is_accepted(self):
        value = record("review")
        value["hosts"][1]["verification"] = {"level": "source", "result": "limited", "evidence": ".agents/lanes/codex.json declares skill_supports_effort false"}
        value["hosts"][1]["exception"] = {
            "constraint_evidence": ".agents/lanes/codex.json sets skill_supports_effort to false",
            "supported_other_host_outcome": "Claude source verification resolves per-skill effort",
        }
        self.assertEqual([], coverage.validate_record(value, "review", HEAD))

    def test_duplicate_hosts_and_placeholders_are_rejected(self):
        value = record()
        value["hosts"][1]["host"] = "claude"
        value["hosts"][0]["mapping"] = "TBD"
        errors = coverage.validate_record(value, "plan")
        self.assertTrue(any("duplicated" in error for error in errors))
        self.assertTrue(any("mapping" in error for error in errors))

    def test_review_candidate_head_must_match_frozen_candidate(self):
        value = record("review")
        value["candidate_head"] = "b" * 40
        errors = coverage.validate_record(value, "review", HEAD)
        self.assertIn("candidate_head does not match the frozen candidate", errors)

    def test_cli_rejects_malformed_record(self):
        with tempfile.TemporaryDirectory() as raw:
            path = write_document(raw, {"schema_version": 1})
            result = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), "--stage", "plan", "--document", str(path)],
                capture_output=True, text=True,
            )
        self.assertEqual(1, result.returncode)
        self.assertFalse(json.loads(result.stdout)["valid"])

    def test_duplicate_json_keys_are_rejected(self):
        records, errors = coverage.parse_records(
            "```agent-host-coverage\n{\"schema_version\":1,\"schema_version\":1}\n```"
        )
        self.assertEqual([], records)
        self.assertTrue(any("duplicate JSON key" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
