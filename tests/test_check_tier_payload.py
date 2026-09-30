"""The payload checker fails loudly on every shape drift a tier repository could ship."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / ".agents" / "hooks" / "check_tier_payload.py"


def load_module():
    specification = importlib.util.spec_from_file_location("check_tier_payload", SCRIPT)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


checker = load_module()


TIER = {
    "schema_version": 1,
    "tier": "dotnet",
    "stack": ".NET",
    "applies": "stack-present",
    "detect": {"globs": ["*.csproj"]},
}


class PayloadTree(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def declare(self, names):
        payloads = self.root / ".agents" / "plugins"
        payloads.mkdir(parents=True, exist_ok=True)
        body = {"payloads": {name: [name] for name in names}}
        (payloads / "payloads.json").write_text(json.dumps(body), encoding="utf-8")

    def payload(self, name, tier=TIER, skills=(("persistence", "contract"),)):
        payload = self.root / "plugins" / name
        payload.mkdir(parents=True, exist_ok=True)
        if tier is not None:
            (payload / "tier.json").write_text(json.dumps(tier), encoding="utf-8")
        listed = []
        for skill_name, kind in skills:
            skill = payload / "skills" / skill_name
            skill.mkdir(parents=True, exist_ok=True)
            (skill / "SKILL.md").write_text(
                f"---\nname: {skill_name}\ndescription: rule\nkind: {kind}\n---\n\n# {skill_name}\n",
                encoding="utf-8",
            )
            listed.append(f"- `{skill_name}` — {kind} — `.agents/{kind}/{skill_name}/SKILL.md`")
        (payload / "INDEX.md").write_text(
            "# capabilities\n\n" + "\n".join(listed) + "\n", encoding="utf-8"
        )
        (payload / "selection.json").write_text(
            json.dumps({"plugin": name, "skills": [skill_name for skill_name, _ in skills]}),
            encoding="utf-8",
        )
        return payload

    def test_a_conforming_payload_passes(self):
        self.declare(["dotnet"])
        self.payload("dotnet")
        self.assertEqual(checker.check(self.root), [])

    def test_a_missing_tier_declaration_fails(self):
        self.declare(["dotnet"])
        self.payload("dotnet", tier=None)
        problems = checker.check(self.root)
        self.assertTrue(any("no tier.json" in problem for problem in problems), problems)

    def test_undeclared_generator_output_fails(self):
        self.declare(["dotnet"])
        self.payload("dotnet")
        self.payload("dotnet-standards")
        problems = checker.check(self.root)
        self.assertTrue(any("dotnet-standards is not declared" in problem for problem in problems), problems)

    def test_a_declared_payload_that_does_not_exist_fails(self):
        self.declare(["dotnet", "ghost"])
        self.payload("dotnet")
        problems = checker.check(self.root)
        self.assertTrue(any("ghost is declared but does not exist" in problem for problem in problems), problems)

    def test_a_stack_tier_without_a_matcher_fails(self):
        self.declare(["dotnet"])
        self.payload("dotnet", tier=dict(TIER, detect={}))
        problems = checker.check(self.root)
        self.assertTrue(any("detect has no matcher" in problem for problem in problems), problems)

    def test_a_remote_matcher_requires_schema_version_two(self):
        self.declare(["dotnet"])
        self.payload("dotnet", tier=dict(TIER, detect={"remote": ["^infonetica/"]}))
        problems = checker.check(self.root)
        self.assertTrue(any("schema_version 1" in problem for problem in problems), problems)

        self.payload("dotnet", tier=dict(TIER, schema_version=2, detect={"remote": ["^infonetica/"]}))
        self.assertEqual(checker.check(self.root), [])

    def test_front_matter_must_carry_the_kind_marker(self):
        self.declare(["dotnet"])
        payload = self.payload("dotnet")
        skill = payload / "skills" / "persistence" / "SKILL.md"
        skill.write_text("---\nname: persistence\ndescription: rule\n---\n\n# persistence\n", encoding="utf-8")
        problems = checker.check(self.root)
        self.assertTrue(any("kind" in problem for problem in problems), problems)

    def test_the_index_must_match_the_shipped_skills_exactly(self):
        self.declare(["dotnet"])
        payload = self.payload("dotnet")
        (payload / "INDEX.md").write_text(
            "# capabilities\n\n- `persistence` — contract — x\n- `phantom` — contract — x\n",
            encoding="utf-8",
        )
        problems = checker.check(self.root)
        self.assertTrue(any("lists 'phantom'" in problem for problem in problems), problems)

        (payload / "INDEX.md").write_text("# capabilities\n", encoding="utf-8")
        problems = checker.check(self.root)
        self.assertTrue(any("does not list shipped skill 'persistence'" in problem for problem in problems), problems)

    def test_selection_must_name_only_shipped_skills(self):
        self.declare(["dotnet"])
        payload = self.payload("dotnet")
        (payload / "selection.json").write_text(
            json.dumps({"plugin": "dotnet", "profiles": {"core": ["phantom"]}}), encoding="utf-8"
        )
        problems = checker.check(self.root)
        self.assertTrue(any("names 'phantom'" in problem for problem in problems), problems)

    def test_this_repository_conforms(self):
        self.assertEqual(checker.check(ROOT), [])


if __name__ == "__main__":
    unittest.main()
