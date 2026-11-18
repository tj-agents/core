"""Agent owns the lane ladder, its tables and the lane agents, and tests them. Core asserts only what it
owns against that ladder, read from Agent's tables through the staged dependency: its skills' lane
declarations, its workflow roles' model pins, and the role agents Core itself generates and delivers.
"""

import json
import re
import unittest
from fnmatch import fnmatch
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LANES = ROOT / ".agents" / "dependencies" / "agent" / ".agents" / "agent" / "resources" / "lanes"
HOSTS = ROOT / ".agents" / "workflows" / "hosts"

HOST_IDS = ("claude", "codex")
EFFORTS = ("low", "medium", "high", "xhigh", "max")
FABLE = "claude-fable-5"

# A role may pin a specialist model for the kind of work it does instead of a ladder rung. Each such
# deviation is declared here rather than just appearing in a host manifest.
ROLE_SPECIALISTS = {("codex", "review-lens"): "gpt-5.3-codex-spark"}


def table(host):
    return json.loads((LANES / f"{host}.json").read_text(encoding="utf-8-sig"))


def manifest(host):
    return json.loads((HOSTS / f"{host}.json").read_text(encoding="utf-8-sig"))


def front_matter(path):
    text = path.read_text(encoding="utf-8-sig")
    match = re.match(r"(?s)\A---\n(.*?)\n---\n", text)
    if not match:
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        key = re.match(r"^([A-Za-z_-]+):[ \t]*(.*)$", line)
        if key:
            fields[key.group(1)] = key.group(2).strip()
    return fields


class LaneDeclarationTests(unittest.TestCase):
    def skills(self):
        return sorted(path for scope in ("base", "engineering", "workflow") for path in (ROOT / ".agents" / scope).rglob("SKILL.md"))

    def test_every_declared_lane_exists_on_both_hosts(self):
        rungs = {host: set(table(host)["lanes"]) for host in HOST_IDS}
        declared = 0
        for skill in self.skills():
            lane = front_matter(skill).get("lane")
            if not lane:
                continue
            declared += 1
            for host in HOST_IDS:
                with self.subTest(skill=skill.parent.name, host=host):
                    self.assertIn(lane, rungs[host])
        self.assertGreater(declared, 0, "no skill declares a lane, so the ladder governs nothing")

    def test_only_one_shape_leaf_tasks_declare_a_lane(self):
        # A lane in skill front matter re-points the whole session when the skill is invoked, and the
        # switch outlives the skill. A lifecycle or orchestrating skill spans phases of varying shape, so
        # it must inherit the session's model and route each bounded phase down the ladder instead. Only
        # a leaf task that is one unvarying shape may pin: the clerical operations. Planning may span
        # multiple lanes, so plan inherits and routes its phases. Adding a lane is a deliberate
        # declaration that a skill is such a leaf; declare it here too.
        expected = {
            "commit": "L7",
            "commit-all": "L7",
            "push": "L7",
            "pull": "L7",
            "sync-checkout": "L7",
            "open-worktree": "L7",
        }
        declared = {}
        for skill in self.skills():
            lane = front_matter(skill).get("lane")
            if lane:
                declared[skill.parent.name] = lane
        self.assertEqual(expected, declared)

    def test_no_routed_standard_declares_a_lane(self):
        # A routed standard is consulted DURING other work; a lane on one would re-point that task's
        # model. The generator refuses this too - asserted here so the rule survives a generator rewrite.
        for skill in self.skills():
            text = skill.read_text(encoding="utf-8-sig")
            routed = re.search(r"The standard is `(standards/[^`]+\.md)`", text)
            if routed:
                with self.subTest(skill=skill.parent.name):
                    self.assertNotIn("lane", front_matter(skill))

    def test_no_skill_names_a_model_directly(self):
        models = {FABLE, *ROLE_SPECIALISTS.values()}
        for host in HOST_IDS:
            models.update(rung["model"] for rung in table(host)["lanes"].values())
            models.update(role["model"] for role in manifest(host)["roles"].values())
        for skill in self.skills():
            text = skill.read_text(encoding="utf-8-sig")
            for model in models:
                with self.subTest(skill=skill.parent.name, model=model):
                    self.assertNotIn(model, text, "declare a lane instead of naming a model")


class RolePinTests(unittest.TestCase):
    """Each workflow role pins its model in the host manifest. A pin off the ladder must be a declared
    specialist, so the ladder stays the one answer to which model a role runs."""

    def test_every_role_resolves_to_a_rung_or_a_declared_specialist(self):
        for host in HOST_IDS:
            rungs = {rung["model"] for rung in table(host)["lanes"].values()}
            for capability, role in manifest(host)["roles"].items():
                with self.subTest(host=host, capability=capability):
                    specialist = ROLE_SPECIALISTS.get((host, capability))
                    if specialist:
                        self.assertEqual(specialist, role["model"])
                    else:
                        self.assertIn(role["model"], rungs)
                    effort = role.get("effort", role.get("reasoning_effort"))
                    self.assertIn(effort, EFFORTS)

    def test_workflow_pins_never_select_claude_fable(self):
        for capability, role in manifest("claude")["roles"].items():
            with self.subTest(capability=capability):
                self.assertNotEqual(FABLE, role["model"])


class RoleAgentDeliveryTests(unittest.TestCase):
    """Core generates and delivers only its workflow role agents; Agent publishes the lane agents."""

    PLUGIN = ROOT / "plugins" / "engineering"

    def test_core_generates_exactly_its_workflow_role_agents(self):
        for host in HOST_IDS:
            delivery = manifest(host)["delivery"]
            with self.subTest(host=host):
                generated = {path.name for path in (self.PLUGIN / delivery["plugin_directory"]).glob("*" + delivery["extension"])}
                self.assertEqual({role["filename"] for role in manifest(host)["roles"].values()}, generated)

    def test_the_codex_installer_covers_every_generated_agent_family(self):
        # Codex cannot load an agent from a plugin, so the profile installer is the only supported route
        # from the generated payload to ~/.codex/agents. A family it does not glob is silently omitted.
        delivery = json.loads(
            (ROOT / ".codex" / "agent-delivery.json").read_text(
                encoding="utf-8-sig"
            )
        )
        patterns = delivery["generated_agent_patterns"]
        self.assertNotIn("*.toml", patterns, "the installer must not clobber a consumer's own agents")

        emitted = sorted(p.name for p in (self.PLUGIN / "codex-agents").glob("*.toml"))
        self.assertTrue(emitted)
        for name in emitted:
            with self.subTest(agent=name):
                self.assertTrue(
                    any(fnmatch(name, pattern) for pattern in patterns),
                    f"{name} is generated but no installer pattern in {patterns} installs it",
                )

    def test_hosts_deliberately_use_different_agent_delivery_surfaces(self):
        manifests = {host: manifest(host) for host in HOST_IDS}
        codex = manifests["codex"]["delivery"]
        claude = manifests["claude"]["delivery"]

        self.assertEqual("agents", codex["profile_directory"])
        self.assertEqual("CODEX_HOME", codex["profile_environment"])
        self.assertEqual("unsupported-use-profile-installer", codex["plugin_loading"])
        self.assertNotIn("project_installer", codex)
        self.assertEqual("supported", claude["plugin_loading"])
        self.assertEqual("agents", claude["plugin_directory"])
        self.assertFalse((ROOT / ".claude" / "agents").exists())


if __name__ == "__main__":
    unittest.main()
