import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/workflow/contract/plan-artifacts/SKILL.md"
TEMPLATE = ROOT / ".agents/workflow/contract/plan-artifacts/templates/PLAN.md"
SCRIPT = ROOT / ".agents/workflow/contract/plan-artifacts/scripts/host_coverage.py"


class PlanArtifactTests(unittest.TestCase):
    def test_canonical_workflow_contract_keeps_template_and_host_coverage_helper(self):
        self.assertTrue(SKILL.is_file())
        self.assertTrue(TEMPLATE.is_file())
        self.assertTrue(SCRIPT.is_file())
        self.assertFalse((SCRIPT.parent / "session-context.py").exists())

    def test_contract_example_validates_with_its_host_coverage_helper(self):
        specification = importlib.util.spec_from_file_location("host_coverage", SCRIPT)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        result = module.validate_documents([SKILL], "plan")
        self.assertTrue(result["valid"], result["errors"])


if __name__ == "__main__":
    unittest.main()
