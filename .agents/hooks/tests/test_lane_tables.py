"""The lane ladder is the repo's only model decision, so everything that could let it drift is asserted
here: the two harness tables agreeing rung-for-rung, every declared lane existing, the generated agents
carrying the resolved values, and the workflow contract's own stage pins still matching the ladder they
were derived from.
"""

import json
import re
import subprocess
import sys
import tomllib
import unittest
from fnmatch import fnmatch
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LANES = ROOT / ".agents" / "lanes"
HOSTS = ROOT / ".agents" / "workflows" / "hosts"

HOST_IDS = ("claude", "codex")
EFFORTS = ("low", "medium", "high", "xhigh", "max")

# The stage vocabulary predates the ladder and stays pinned under the workflow contract's own version.
# These are the rungs each stage was derived from; the pins must keep agreeing with the ladder.
STAGE_LANES = {
    "critical": "L1",
    "strategic": "L2",
    "implementation": "L3",
    "review": "L3",
    "mechanical": "L4",
}

# Capability order per vendor, most capable first. A rung may never sit above the rung before it.
FAMILY_ORDER = {
    "claude": ("claude-fable-5-1", "claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5"),
    "codex": ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"),
}


def table(host):
    return json.loads((LANES / f"{host}.json").read_text(encoding="utf-8-sig"))


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


class LaneTableTests(unittest.TestCase):
    def test_both_hosts_declare_the_same_rungs_in_order(self):
        rungs = [list(table(host)["lanes"]) for host in HOST_IDS]
        self.assertEqual(rungs[0], rungs[1], "the two ladders must pair rung for rung")
        self.assertEqual(rungs[0], sorted(rungs[0]), "rungs must be authored in order, L1 first")
        self.assertEqual(rungs[0][0], "L1")

    def test_every_rung_declares_a_model_and_a_yaml_safe_summary(self):
        for host in HOST_IDS:
            for lane, rung in table(host)["lanes"].items():
                with self.subTest(host=host, lane=lane):
                    self.assertTrue(rung.get("model"), "a rung with no model prices nothing")
                    summary = rung.get("summary", "")
                    self.assertTrue(summary)
                    # The generator renders this into an unquoted YAML scalar in an agent description.
                    self.assertNotRegex(summary, r":\s", "a colon-space truncates the scalar")

    def test_no_rung_is_more_capable_than_the_rung_above_it(self):
        for host in HOST_IDS:
            order = FAMILY_ORDER[host]
            seen = -1
            for lane, rung in table(host)["lanes"].items():
                with self.subTest(host=host, lane=lane):
                    self.assertIn(rung["model"], order, "model is not in the declared capability order")
                    rank = order.index(rung["model"])
                    self.assertGreaterEqual(rank, seen, "a lower rung names a more capable model")
                    seen = rank

    def test_effort_is_declared_under_each_host_own_key_and_from_the_known_vocabulary(self):
        for host in HOST_IDS:
            data = table(host)
            key = data["effort_key"]
            for lane, rung in data["lanes"].items():
                with self.subTest(host=host, lane=lane):
                    if key in rung:
                        self.assertIn(rung[key], EFFORTS)
                    else:
                        # The only rung allowed to omit effort is one whose model rejects the parameter,
                        # and it must say so rather than leaving the omission to look like an oversight.
                        self.assertTrue(rung.get("no_effort_reason"))

    def test_each_host_declares_whether_a_skill_can_carry_effort(self):
        # The generator reads this flag instead of testing a host name. An absent flag is falsy, so a table
        # that forgot it would silently stop stamping effort rather than failing - assert it is declared.
        for host in HOST_IDS:
            data = table(host)
            with self.subTest(host=host):
                self.assertIn("skill_supports_effort", data)
                self.assertIsInstance(data["skill_supports_effort"], bool)
        # Codex has no per-skill effort key; if that ever changes, this is the line to change with it.
        self.assertTrue(table("claude")["skill_supports_effort"])
        self.assertFalse(table("codex")["skill_supports_effort"])

    def test_claude_records_a_context_ceiling_and_its_cheapest_rung_is_smaller(self):
        lanes = table("claude")["lanes"]
        ceilings = [rung["context_ceiling"] for rung in lanes.values()]
        self.assertTrue(all(isinstance(c, int) and c > 0 for c in ceilings))
        self.assertLess(
            ceilings[-1],
            ceilings[0],
            "L5 dropping a family is a context step too; if that stops being true, say so here",
        )


class LaneDeclarationTests(unittest.TestCase):
    def skills(self):
        return sorted(path for scope in ("base", "engineering", "machine") for path in (ROOT / ".agents" / scope).rglob("SKILL.md"))

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
        models = {rung["model"] for host in HOST_IDS for rung in table(host)["lanes"].values()}
        for skill in self.skills():
            text = skill.read_text(encoding="utf-8-sig")
            for model in models:
                with self.subTest(skill=skill.parent.name, model=model):
                    self.assertNotIn(model, text, "declare a lane instead of naming a model")


class GeneratedLaneAgentTests(unittest.TestCase):
    def test_claude_agents_carry_the_resolved_rung(self):
        lanes = table("claude")["lanes"]
        for lane, rung in lanes.items():
            path = ROOT / "plugins" / "engineering" / "agents" / f"lane-{lane.lower()}.md"
            with self.subTest(lane=lane):
                self.assertTrue(path.is_file(), f"{path.name} is not generated")
                fields = front_matter(path)
                self.assertEqual(f"lane-{lane.lower()}", fields["name"])
                self.assertEqual(rung["model"], fields["model"])
                self.assertEqual(rung.get("effort"), fields.get("effort"))
                self.assertEqual("Agent", fields["disallowedTools"])

    def test_codex_agents_carry_the_resolved_rung_including_effort(self):
        for lane, rung in table("codex")["lanes"].items():
            path = ROOT / "plugins" / "engineering" / "codex-agents" / f"lane-{lane.lower()}.toml"
            with self.subTest(lane=lane):
                self.assertTrue(path.is_file(), f"{path.name} is not generated")
                agent = tomllib.loads(path.read_text(encoding="utf-8-sig"))
                self.assertEqual(f"lane_{lane.lower()}", agent["name"])
                self.assertEqual(rung["model"], agent["model"])
                # Codex has no per-skill effort key, so the agent is the ONLY place its effort lands.
                self.assertEqual(rung["reasoning_effort"], agent["model_reasoning_effort"])

    def test_both_harnesses_generate_an_agent_for_every_rung_and_no_others(self):
        expected = {f"lane-{lane.lower()}" for lane in table("claude")["lanes"]}
        claude = {p.stem for p in (ROOT / "plugins" / "engineering" / "agents").glob("lane-*.md")}
        codex = {p.stem for p in (ROOT / "plugins" / "engineering" / "codex-agents").glob("lane-*.toml")}
        self.assertEqual(expected, claude)
        self.assertEqual(expected, codex)


class PluginDeliveryTests(unittest.TestCase):
    """A consumer installs only the plugin subtree, so anything the shipped skill names has to be inside
    it. The payloads already carry resolved models; the tables travel for the skill that documents them."""

    PLUGIN = ROOT / "plugins" / "engineering"

    def test_the_plugin_ships_the_tables_and_the_resolver(self):
        for name in ("claude.json", "codex.json", "resolve.py", "agent-body.md"):
            with self.subTest(name=name):
                shipped = self.PLUGIN / ".agents" / "lanes" / name
                self.assertTrue(shipped.is_file(), f"plugins/engineering/.agents/lanes/{name} is not shipped")
                self.assertEqual(
                    (LANES / name).read_text(encoding="utf-8-sig"),
                    shipped.read_text(encoding="utf-8-sig"),
                )

    def test_the_codex_installer_covers_every_generated_agent_family(self):
        # Codex cannot load an agent from a plugin (plugin_loading is unsupported-use-project-installer),
        # so this script is the ONLY thing that puts a Codex agent on disk. A family it does not glob is
        # generated and then silently never installed.
        delivery = json.loads(
            (ROOT / ".codex" / "agent-delivery.json").read_text(
                encoding="utf-8-sig"
            )
        )
        patterns = delivery["generated_agent_patterns"]
        self.assertNotIn("*.toml", patterns, "the installer must not clobber a consumer's own agents")

        emitted = sorted(p.name for p in (ROOT / "plugins" / "engineering" / "codex-agents").glob("*.toml"))
        self.assertTrue(emitted)
        for name in emitted:
            with self.subTest(agent=name):
                self.assertTrue(
                    any(fnmatch(name, pattern) for pattern in patterns),
                    f"{name} is generated but no installer pattern in {patterns} installs it",
                )

    def test_the_shipped_skill_names_locations_that_exist_in_each_layout(self):
        canonical = self.PLUGIN / ".agents/engineering/contract/lanes/SKILL.md"
        body = canonical.read_text(encoding="utf-8-sig")
        self.assertIn(".agents/lanes/", body)
        self.assertIn("../../.agents/lanes/", body)
        self.assertIn("../../../lanes/", body)
        self.assertTrue((self.PLUGIN / ".agents/lanes").is_dir())
        self.assertTrue((canonical.parent / "../../../lanes").resolve().is_dir())



class StagePinTests(unittest.TestCase):
    """The workflow contract pins its own stage models under its version. It may not drift from the ladder
    those pins came from -- that would leave two disagreeing answers to one question."""

    def test_every_semantic_stage_still_resolves_to_its_lane(self):
        for host in HOST_IDS:
            data = table(host)
            manifest = json.loads((HOSTS / f"{host}.json").read_text(encoding="utf-8-sig"))
            key = data["effort_key"]
            self.assertEqual(set(STAGE_LANES), set(manifest["semantic_stages"]))
            for stage, lane in STAGE_LANES.items():
                pinned = manifest["semantic_stages"][stage]
                rung = data["lanes"][lane]
                with self.subTest(host=host, stage=stage):
                    # A stage may name a specialist model for the KIND of work (Codex review), which is a
                    # second axis rather than a rung. It then owns its effort too -- the right setting for
                    # a specialist is a property of that model, not of the rung it sits beside. All the
                    # ladder requires is that the deviation is declared instead of just appearing.
                    if pinned.get("specialist"):
                        self.assertEqual(pinned["model"], pinned["specialist"])
                        self.assertIn(pinned[key], EFFORTS)
                    else:
                        self.assertEqual(rung["model"], pinned["model"])
                        self.assertEqual(rung.get(key), pinned.get(key))

    def test_every_role_still_resolves_to_a_rung(self):
        for host in HOST_IDS:
            data = table(host)
            manifest = json.loads((HOSTS / f"{host}.json").read_text(encoding="utf-8-sig"))
            for capability, role in manifest["roles"].items():
                lane = STAGE_LANES[role["default_stage"]]
                rung = data["lanes"][lane]
                with self.subTest(host=host, capability=capability):
                    stage = manifest["semantic_stages"][role["default_stage"]]
                    expected = stage.get("specialist") or rung["model"]
                    self.assertEqual(expected, role["model"])


class ResolverTests(unittest.TestCase):
    def resolve(self, *args):
        return subprocess.run(
            [sys.executable, str(LANES / "resolve.py"), *args],
            capture_output=True,
            text=True,
        )

    def test_resolves_a_lane_to_its_host_model(self):
        done = self.resolve("--host", "claude", "--lane", "L4")
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertEqual(
            table("claude")["lanes"]["L4"]["model"], json.loads(done.stdout)["model"]
        )

    def test_an_unknown_lane_or_host_fails_rather_than_falling_back(self):
        for args in (("--host", "claude", "--lane", "L99"), ("--host", "nope", "--lane", "L1")):
            with self.subTest(args=args):
                done = self.resolve(*args)
                self.assertNotEqual(0, done.returncode)
                self.assertNotIn("model", done.stdout)


if __name__ == "__main__":
    unittest.main()
