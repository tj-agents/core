import json
import subprocess
import sys
import unittest
import uuid

import test_skill_router


ADVISORY = "SKILL ROUTER - conditional standards"


class RequiredAndConditionalTierTests(unittest.TestCase):
    """A route's `skills` block; its `conditional` entries are named once and never block."""

    setUp = test_skill_router.SkillRouterTests.setUp
    routes = test_skill_router.SkillRouterTests.routes
    environment = test_skill_router.SkillRouterTests.environment
    run_router = test_skill_router.SkillRouterTests.run_router

    def add_skill(self, name, description):
        skill = self.plugin / "skills" / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: {description}\nkind: contract\n---\n\n# {name}\n",
            encoding="utf-8",
        )

    def transcript(self, *loaded):
        path = self.base / f"transcript-{uuid.uuid4()}.jsonl"
        lines = []
        for index, name in enumerate(loaded):
            tool_id = f"toolu_{index}"
            lines.append({"message": {"content": [
                {"type": "tool_use", "name": "Skill", "id": tool_id, "input": {"skill": name}}
            ]}})
            lines.append({"message": {"content": [{"type": "tool_result", "tool_use_id": tool_id}]}})
        path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")
        return str(path)

    def write(self, session, transcript=None, tool_name="Write", **extra):
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_use_id": str(uuid.uuid4()),
            "session_id": session,
            "cwd": str(self.repo),
            "tool_name": tool_name,
            "tool_input": {"file_path": "src/item.py", "content": "value = 2\n"},
        }
        if transcript is not None:
            payload["transcript_path"] = transcript
        payload.update(extra)
        return self.run_router(payload=payload)

    def mixed(self):
        self.add_skill("mixins", "Compose behavior through mixins and CRTP providers.")
        self.routes({"routes": [{
            "path": "^src/",
            "skills": ["feature"],
            "conditional": [{"skill": "mixins", "when": "composing or changing mixins"}],
        }]})

    def test_legacy_skills_only_route_still_blocks_every_listed_skill(self):
        self.add_skill("style", "Name and format code.")
        self.routes({"routes": [{"path": "^src/", "skills": ["feature", "style"]}]})

        result = self.write(str(uuid.uuid4()), self.transcript("feature"))

        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("* style", result.stderr)
        self.assertNotIn(ADVISORY, result.stderr)

    def test_required_only_route_allows_once_proven_without_advice(self):
        result = self.write(str(uuid.uuid4()), self.transcript("feature"))

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def test_conditional_only_route_never_blocks_and_advises_once(self):
        self.add_skill("mixins", "Compose behavior through mixins and CRTP providers.")
        self.routes({"routes": [{
            "path": "^src/",
            "conditional": [{"skill": "mixins", "when": "composing or changing mixins"}],
        }]})
        session = str(uuid.uuid4())

        first = self.write(session)
        second = self.write(session)

        self.assertEqual(0, first.returncode, first.stderr)
        context = json.loads(first.stdout)["hookSpecificOutput"]
        self.assertEqual("PreToolUse", context["hookEventName"])
        self.assertIn("* mixins", context["additionalContext"])
        self.assertIn("Compose behavior through mixins", context["additionalContext"])
        self.assertIn("WHEN: composing or changing mixins", context["additionalContext"])
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertEqual("", second.stdout)

    def test_mixed_route_blocks_only_on_the_required_subset(self):
        self.mixed()

        result = self.write(str(uuid.uuid4()))

        self.assertEqual(2, result.returncode, result.stderr)
        required, _, advice = result.stderr.partition(ADVISORY)
        self.assertIn("* feature", required)
        self.assertNotIn("mixins", required)
        self.assertIn("* mixins", advice)
        self.assertIn("WHEN: composing or changing mixins", advice)

    def test_mixed_route_allows_when_only_the_required_skill_is_loaded(self):
        self.mixed()

        result = self.write(str(uuid.uuid4()), self.transcript("feature"))

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("* mixins", json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"])

    def test_advice_already_shown_in_a_block_is_not_repeated(self):
        self.mixed()
        session = str(uuid.uuid4())

        self.write(session)
        blocked_again = self.write(session)
        allowed = self.write(session, self.transcript("feature"))

        self.assertEqual(2, blocked_again.returncode)
        self.assertNotIn(ADVISORY, blocked_again.stderr)
        self.assertEqual(0, allowed.returncode, allowed.stderr)
        self.assertEqual("", allowed.stdout)

    def test_a_loaded_conditional_skill_is_not_advised(self):
        self.mixed()

        result = self.write(str(uuid.uuid4()), self.transcript("feature", "mixins"))

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def test_codex_receives_no_structured_advice_on_an_allowed_write(self):
        self.add_skill("mixins", "Compose behavior through mixins and CRTP providers.")
        self.routes({"routes": [{
            "path": "^src/",
            "conditional": [{"skill": "mixins", "when": "composing or changing mixins"}],
        }]})

        result = self.write(
            str(uuid.uuid4()),
            tool_name="apply_patch",
            tool_input={"patch": "*** Begin Patch\n*** Update File: src/item.py\n+value = 2\n*** End Patch"},
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def test_codex_keeps_undelivered_advice_for_its_next_block(self):
        self.add_skill("mixins", "Compose behavior through mixins and CRTP providers.")
        self.routes({"routes": [
            {"path": "^src/", "conditional": [{"skill": "mixins", "when": "composing mixins"}]},
            {"path": "^src/.*\\.hpp$", "skills": ["feature"]},
        ]})
        session = str(uuid.uuid4())
        patch = "*** Begin Patch\n*** Update File: src/{0}\n+value = 2\n*** End Patch"

        allowed = self.write(session, tool_name="apply_patch", tool_input={"patch": patch.format("item.py")})
        blocked = self.write(session, tool_name="apply_patch", tool_input={"patch": patch.format("item.hpp")})

        self.assertEqual(0, allowed.returncode, allowed.stderr)
        self.assertEqual(2, blocked.returncode, blocked.stderr)
        self.assertIn("WHEN: composing mixins", blocked.stderr)

    def test_an_uninstalled_conditional_skill_never_blocks(self):
        self.routes({"routes": [{
            "path": "^src/",
            "conditional": [{"skill": "missing-marketplace:never-shipped", "when": "never"}],
        }]})

        result = self.write(str(uuid.uuid4()))
        verify = self.run_router(["--verify-install", "claude"])

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("NOT INSTALLED FOR CLAUDE", result.stdout)
        self.assertEqual(0, verify.returncode, verify.stdout)
        self.assertIn("missing-marketplace:never-shipped", verify.stdout)

    def test_malformed_conditional_entry_stops_like_any_unusable_table(self):
        for entry in ({"skill": "mixins"}, {"when": "always"}, "mixins", {"skill": "", "when": "x"}):
            with self.subTest(entry=entry):
                self.routes({"routes": [{"path": "^src/", "skills": [], "conditional": [entry]}]})

                result = self.write(str(uuid.uuid4()))

                self.assertEqual(2, result.returncode, result.stderr)
                self.assertIn("routing table itself is broken", result.stderr)
                self.assertIn("conditional entry", result.stderr)

    def test_query_reports_the_two_tiers_separately(self):
        self.mixed()

        result = subprocess.run(
            [sys.executable, "-B", str(self.router), "--skills-for", "--json"],
            cwd=self.repo, input="src/item.py\n", capture_output=True, text=True,
            encoding="utf-8", env=self.environment(), timeout=20,
        )

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual({"feature": ["src/item.py"]}, report["skills"])
        self.assertEqual(
            {"mixins": {"when": ["composing or changing mixins"], "files": ["src/item.py"]}},
            report["conditional"],
        )


if __name__ == "__main__":
    unittest.main()
