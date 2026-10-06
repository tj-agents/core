import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / ".agents" / "hooks" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load("tier_gate")
checker = load("check_tier_payload")


class Predicates(unittest.TestCase):
    def setUp(self):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.root = Path(holder.name)
        (self.root / "project.csproj").write_text("<Project />", encoding="utf-8")

    def test_nested_positive_composition_requires_every_conjunct(self):
        node = {"all": [{"glob": "*.csproj"}, {"any": [{"file": "adopted.json"}, {"file": "other.json"}]}]}
        self.assertFalse(gate.evaluate_predicate(self.root, node).matched)
        (self.root / "adopted.json").write_text("{}", encoding="utf-8")
        result = gate.evaluate_predicate(self.root, node)
        self.assertTrue(result.matched)
        self.assertEqual(result.scope, str(self.root))
        self.assertEqual(result.evidence, ("project.csproj", "adopted.json"))

    def test_unknown_branch_cannot_be_hidden_by_a_matching_alternative(self):
        node = {"any": [{"file": "project.csproj"}, {"fact": "technology.unknown"}]}
        result = gate.evaluate_predicate(self.root, node)
        self.assertFalse(result.matched)
        self.assertEqual(result.diagnostics[0]["code"], "unknown-fact")
        self.assertEqual(result.diagnostics[0]["path"], "detect.any[1]")

    def test_invalid_member_is_diagnosed_even_when_another_member_matches(self):
        for invalid in ({"all": []}, {"not": {"file": "x"}}, {"file": "x", "glob": "*"},
                        {"remote": "["}, {"content": {"glob": "*", "pattern": "["}},
                        {"context": {"key": "house", "equals": "tommy", "contains": "tommy"}}):
            with self.subTest(invalid=invalid):
                result = gate.evaluate_predicate(self.root, {"any": [{"file": "project.csproj"}, invalid]})
                self.assertFalse(result.matched)
                self.assertTrue(result.diagnostics)

    def test_fact_results_preserve_evidence_and_require_the_same_scope(self):
        fact = gate.PredicateResult(self.root, True, ["project.csproj"])
        result = gate.evaluate_predicate(self.root, {"fact": "language.dotnet"}, {"language.dotnet": fact})
        self.assertTrue(result.matched)
        self.assertEqual(result.prerequisites, ("language.dotnet",))
        self.assertEqual(result.evidence, ("project.csproj",))
        unrelated = gate.PredicateResult(self.root / "other", True, ["other.csproj"])
        result = gate.evaluate_predicate(self.root, {"fact": "language.dotnet"}, {"language.dotnet": unrelated})
        self.assertFalse(result.matched)
        self.assertEqual(result.diagnostics[0]["code"], "invalid-fact")

    def test_context_equality_membership_and_unknowns(self):
        contexts = {"house.dotnet": "tommy", "architecture": ["capability-repositories"]}
        for value in ({"key": "house.dotnet", "equals": "tommy"},
                      {"key": "architecture", "contains": "capability-repositories"}):
            self.assertTrue(gate.evaluate_predicate(self.root, {"context": value}, contexts=contexts).matched)
        result = gate.evaluate_predicate(self.root, {"context": {"key": "unknown", "equals": "tommy"}}, contexts=contexts)
        self.assertEqual(result.diagnostics[0]["code"], "unknown-context")
        result = gate.evaluate_predicate(self.root, {"context": {"key": "house.dotnet", "contains": "tommy"}}, contexts=contexts)
        self.assertEqual(result.diagnostics[0]["code"], "invalid-context")

    def test_content_and_remote_primitives(self):
        result = gate.evaluate_predicate(self.root, {"content": {"glob": "*.csproj", "pattern": "Project"}})
        self.assertTrue(result.matched)
        self.assertFalse(gate.evaluate_predicate(self.root, {"remote": "^infonetica/"}).matched)

    def test_v3_selection_exposes_shared_results(self):
        data = {"schema_version": 3, "tier": "example", "applies": "stack-present",
                "detect": {"all": [{"glob": "*.csproj"}, {"file": "project.csproj"}]}}
        declaration = gate.Declaration("example", "test", data)
        result = gate.assess(self.root, [declaration])
        self.assertEqual([item.id for item, _ in result.applicable], ["example@test"])
        self.assertEqual(result.selections[0]["scope"], str(self.root))
        self.assertEqual(result.selections[0]["evidence"], ("project.csproj",))
        self.assertEqual(result.diagnostics, ())

    def test_v3_force_and_owner_identity_do_not_establish_governing_selection(self):
        data = {"schema_version": 3, "tier": "example", "applies": "stack-present",
                "owner_repository": "tj-agents/example", "detect": {"file": "missing"}}
        declaration = gate.Declaration("example", "test", data)
        with patch.dict(gate.os.environ, {gate.OVERRIDE_VARIABLE: "example"}), \
                patch.object(gate, "repository_identity", return_value="tj-agents/example"):
            result = gate.assess(self.root, [declaration])
        self.assertEqual(result.applicable, [])
        self.assertEqual(result.blocked, [declaration])
        self.assertNotIn(gate.OVERRIDE_VARIABLE, gate.refusal(declaration, "example", self.root))

    def test_review_and_session_report_unknown_configuration(self):
        declaration = gate.Declaration("example", "test", {
            "schema_version": 3, "tier": "example", "applies": "stack-present", "detect": {"fact": "unknown"}})
        for output in (gate.statement(self.root, [declaration]), gate.conventions(self.root, [declaration])):
            self.assertIn("Configuration diagnostic", output)
            self.assertIn("Provide scoped evidence for fact: unknown", output)

    def test_discovery_reports_version_and_parse_failures(self):
        for name, body in (("future", json.dumps({"schema_version": 99})), ("broken", "{")):
            payload = self.root / name / name / "1"
            payload.mkdir(parents=True)
            (payload / "tier.json").write_text(body, encoding="utf-8")
        diagnostics = []
        self.assertEqual(gate.declarations([self.root], diagnostics=diagnostics), [])
        self.assertEqual([item["code"] for item in diagnostics], ["unreadable-declaration", "unsupported-version"])

    def test_payload_checker_accepts_v3_and_rejects_invalid_composition(self):
        data = {"schema_version": 3, "tier": "example", "applies": "stack-present",
                "detect": {"all": [{"fact": "language.dotnet"}, {"context": {"key": "house", "equals": "tommy"}}]}}
        path = self.root / "tier.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        problems = []
        checker.check_tier_declaration(self.root, problems)
        self.assertEqual(problems, [])
        data["detect"] = {"all": []}
        path.write_text(json.dumps(data), encoding="utf-8")
        checker.check_tier_declaration(self.root, problems)
        self.assertIn("non-empty array", problems[0])


if __name__ == "__main__":
    unittest.main()
