import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS = ROOT / ".agents" / "workflows"
SKILLS = ROOT / ".agents" / "skills"
sys.path.insert(0, str(WORKFLOWS))

from workflow_runtime import WorkflowContract


ROLE_SHAPED = re.compile(r"`([a-z0-9]+(?:-[a-z0-9]+)*-(?:analyst|explorer|lens|worker))`")


class WorkflowAdoptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = WorkflowContract(WORKFLOWS, repository_root=ROOT)
        cls.capabilities = set(cls.contract.capabilities["delegable_capabilities"])
        cls.skills = {
            path.parent.name: path.read_text(encoding="utf-8")
            for path in sorted(SKILLS.glob("*/SKILL.md"))
        }
        cls.hosts = {
            host: json.loads(
                (WORKFLOWS / "hosts" / f"{host}.json").read_text(encoding="utf-8")
            )
            for host in ("codex", "claude")
        }

    def adopters(self):
        return {
            name: body
            for name, body in self.skills.items()
            if any(capability in body for capability in self.capabilities)
        }

    def test_every_role_shaped_name_a_skill_uses_is_a_declared_capability(self):
        for name, body in self.skills.items():
            for candidate in set(ROLE_SHAPED.findall(body)) - set(self.skills):
                with self.subTest(skill=name, capability=candidate):
                    self.assertIn(candidate, self.capabilities)

    def test_no_skill_names_a_host_agent(self):
        forbidden = set()
        for manifest in self.hosts.values():
            for role in manifest["roles"].values():
                forbidden.add(role["agent_name"])
        for name, body in self.skills.items():
            for token in sorted(forbidden):
                with self.subTest(skill=name, token=token):
                    self.assertNotIn(token, body)

    def test_the_adopting_specialists_bind_to_the_versioned_bundle(self):
        for name in ("plan-authoring", "techdebt"):
            with self.subTest(skill=name):
                body = self.skills[name]
                self.assertIn(".agents/workflows/contract/v2", body)
                self.assertIn("../../workflows/contract/v2", body)

    def test_a_read_heavy_and_a_stateful_specialist_have_adopted_the_contract(self):
        adopters = self.adopters()
        self.assertIn("plan-authoring", adopters)
        self.assertIn("techdebt", adopters)
        self.assertEqual(set(), {"evidence-explorer", "test-impact-analyst"} - set(
            capability for capability in self.capabilities
            if capability in adopters["plan-authoring"]
        ))
        self.assertNotIn("mechanical-worker", adopters["plan-authoring"])
        self.assertIn("mechanical-worker", adopters["techdebt"])
        self.assertIn("plan-checkpoint", adopters["techdebt"])

    def test_specialist_adoption_did_not_move_parent_authority(self):
        for name in ("plan-authoring", "techdebt"):
            with self.subTest(skill=name):
                body = self.skills[name]
                self.assertIn("parent", body)
                self.assertNotIn("nested dispatch", body)


if __name__ == "__main__":
    unittest.main()
