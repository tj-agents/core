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
    def test_one_assessment_reuses_identical_git_queries_without_stale_later_results(self):
        found = [gate.Declaration(name, "tj-agents", {
            "tier": name, "stack": "Rust", "applies": "stack-present",
            "detect": {'glob': "*.rs"},
        }) for name in ("rust-one", "rust-two")]
        with patch.object(gate, "_run_git", return_value="") as git:
            self.assertEqual(2, len(gate.assess(self.root, found).blocked))
            self.assertEqual(1, git.call_count)
            git.return_value = "src/main.rs\0"
            self.assertEqual(2, len(gate.assess(self.root, found).applicable))
            self.assertEqual(2, git.call_count)

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

    def test_selection_exposes_shared_results(self):
        data = {"tier": "example", "applies": "stack-present",
                "detect": {"all": [{"glob": "*.csproj"}, {"file": "project.csproj"}]}}
        declaration = gate.Declaration("example", "test", data)
        result = gate.assess(self.root, [declaration])
        self.assertEqual([item.id for item, _ in result.applicable], ["example@test"])
        self.assertEqual(result.selections[0]["scope"], str(self.root))
        self.assertEqual(result.selections[0]["evidence"], ("project.csproj",))
        self.assertEqual(result.diagnostics, ())

    def test_force_and_owner_identity_do_not_establish_governing_selection(self):
        data = {"tier": "example", "applies": "stack-present",
                "detect": {"file": "missing"}}
        declaration = gate.Declaration("example", "test", data)
        with patch.object(gate.os, "environ", {**gate.os.environ, "AGENTS_TIER_OVERRIDE": "example"}), \
                patch.object(gate, "repository_identity", return_value="tj-agents/example"):
            result = gate.assess(self.root, [declaration])
        self.assertEqual(result.applicable, [])
        self.assertEqual(result.blocked, [declaration])

    def test_session_reports_unknown_configuration(self):
        declaration = gate.Declaration("example", "test", {
            "tier": "example", "applies": "stack-present", "detect": {"fact": "unknown"}})
        output = gate.statement(self.root, [declaration])
        self.assertIn("Configuration diagnostic", output)
        self.assertIn("Provide scoped evidence for fact: unknown", output)

    def test_discovery_reports_retired_fields_and_parse_failures(self):
        for name, body in (("future", json.dumps({"schema_version": 99, "tier": "future", "applies": "always"})), ("broken", "{")):
            payload = self.root / name / name / "1"
            payload.mkdir(parents=True)
            (payload / "tier.json").write_text(body, encoding="utf-8")
        diagnostics = []
        found = gate.declarations([self.root], diagnostics=diagnostics)
        self.assertEqual([item.id for item in found], ["broken@broken", "future@future"])
        self.assertTrue(all(item.diagnostics for item in found))
        self.assertEqual([item["code"] for item in diagnostics], ["unreadable-declaration", "malformed-declaration"])


    def install(self, plugin, body):
        cache = self.root / "config" / "plugins" / "cache"
        payload = cache / "test-market" / plugin / "1"
        skill = payload / "skills" / "rule"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: rule\nkind: convention\n---\n", encoding="utf-8")
        if body is not None:
            (payload / "tier.json").write_text(body if isinstance(body, str) else json.dumps(body), encoding="utf-8")
        registry_path = cache.parent / "installed_plugins.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8")) if registry_path.exists() else {"plugins": {}}
        registry["plugins"][plugin + "@test-market"] = [{"installPath": str(payload)}]
        registry_path.write_text(json.dumps(registry), encoding="utf-8")
        return cache, payload

    def test_invalid_installed_declarations_are_diagnosed(self):
        valid = {"tier": "invalid", "applies": "stack-present", "detect": {"all": []}}
        for body in (valid, dict(valid, detect={"not": {"file": "project.csproj"}}),
                     dict(valid, owner_repository=17), dict(valid, schema_version=99), "{", []):
            with self.subTest(body=body):
                plugin = "invalid" + str(len(list((self.root / "config").glob("**/tier.json"))))
                cache, payload = self.install(plugin, body)
                with patch.object(gate, "cache_roots", return_value=[cache]):
                    result = gate.assess(self.root)
                    selection = next(item for item in result.selections if item["plugin_id"] == plugin + "@test-market")
                    self.assertFalse(selection["matched"])
                    self.assertTrue(selection["diagnostics"])

    def test_mixed_validity_keeps_every_valid_convention_and_ordinary_plugins(self):
        predicates = ({"glob": "*.csproj"}, {"file": "project.csproj"}, {"all": [{"glob": "*.csproj"}]})
        for index, detect in enumerate(predicates, start=1):
            cache, _ = self.install("valid" + str(index), {"tier": "valid" + str(index),
                                                          "applies": "stack-present", "detect": detect})
        self.install("invalid", {"tier": "invalid", "applies": "stack-present", "detect": {"all": []}})
        self.install("unknown", {"tier": "unknown", "applies": "stack-present", "detect": {"fact": "missing"}})
        self.install("ordinary", None)
        with patch.object(gate, "cache_roots", return_value=[cache]):
            result = gate.assess(self.root)
            self.assertEqual([item.plugin for item, _ in result.applicable], ["valid1", "valid2", "valid3"])
            self.assertNotIn("ordinary", [item.plugin for item in result.blocked])
            listing = gate.statement(self.root)
            self.assertIn("Configuration diagnostic", listing)
            self.assertIn("Provide scoped evidence for fact: missing", listing)
            for version in (1, 2, 3):
                self.assertIn("Applies here: `valid" + str(version) + ":*`", listing)
            diagnostics = []
            gate.declarations([cache], diagnostics=diagnostics)
            self.assertFalse(any("ordinary" in item["path"] for item in diagnostics))

    def test_payload_checker_accepts_predicates_and_rejects_invalid_composition(self):
        data = {"tier": "example", "applies": "stack-present",
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
