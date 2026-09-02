import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path


HOOK = Path(__file__).resolve().parents[1] / "skill_router.py"
sys.path.insert(0, str(HOOK.parent))

import skill_router  # noqa: E402 - the path above is what makes this importable

# The router is the mechanism; a repo's own table is its data. These tests own a fixture table so a
# route added downstream can never change what the mechanism is asserted to do.
ROUTES = {
    "routes": [
        {
            "path": r"\.UnitTests/.*\.cs$",
            "skills": ["unit-testing"],
            "deny": [
                {
                    "pattern": "WebApplicationFactory|TestServer",
                    "reason": "This boots a host, which makes it an integration test.",
                }
            ],
        },
        {
            "path": r"\.csproj$",
            "content_requires": r"<IsTestProject>\s*true",
            "skills": ["unit-testing", "integration-testing"],
            "note": "Creating a test project is the classification moment.",
        },
        {"path": r"^app/.*/api/[^/]*\.ts$", "skills": ["no-such-skill-here"]},
    ]
}


class SkillRouterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        (self.root / ".git").mkdir()
        (self.root / ".agents").mkdir()
        self.write_routes(ROUTES)
        self.session = str(uuid.uuid4())

    def tearDown(self):
        self.temp.cleanup()

    def write_routes(self, routes):
        body = routes if isinstance(routes, str) else json.dumps(routes)
        (self.root / ".agents" / "skill-routes.json").write_text(body, encoding="utf-8")

    def run_hook(
        self,
        tool="Write",
        path="x.cs",
        content="",
        session=None,
        root=None,
        extra=None,
        env=None,
        hook=HOOK,
        transcript_path=None,
    ):
        target = root or self.root
        tool_input = {"file_path": str(target / path), "content": content}
        tool_input.update(extra or {})
        payload = {
            "tool_name": tool,
            "session_id": session or self.session,
            "cwd": str(target),
            "tool_input": tool_input,
        }
        if transcript_path is not None:
            payload["transcript_path"] = str(transcript_path)
        return subprocess.run(
            [sys.executable, str(hook)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env={**os.environ, **env} if env else None,
        )

    def write_transcript(self, entries):
        """A minimal JSONL transcript: one `Skill` tool_use per entry, paired with its tool_result.

        `entries` is a list of `(skill_name, is_error)` pairs, in invocation order - exactly the shape
        `transcript_skill_outcomes` reads: a `tool_use` naming the skill, then the `tool_result` carrying
        (or not) `is_error` for that same `tool_use_id`.
        """
        fd, raw_path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)  # Windows keeps an open handle locked; the write below reopens by path.
        path = Path(raw_path)
        lines = []
        for index, (name, is_error) in enumerate(entries):
            tool_id = f"toolu_{index}"
            lines.append(json.dumps({
                "message": {"content": [{"type": "tool_use", "id": tool_id, "name": "Skill",
                                          "input": {"skill": name}}]}
            }))
            lines.append(json.dumps({
                "message": {"content": [{"type": "tool_result", "tool_use_id": tool_id,
                                          "is_error": is_error, "content": "..."}]}
            }))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.addCleanup(path.unlink, missing_ok=True)
        return path

    def fake_home(self):
        """A home the hook will believe. Windows resolves ~ from USERPROFILE, POSIX from HOME."""
        home = self.root / "home"
        home.mkdir(exist_ok=True)
        return home, {"USERPROFILE": str(home), "HOME": str(home)}

    def plant_skill(self, skills_dir, name, description):
        target = skills_dir / name
        target.mkdir(parents=True, exist_ok=True)
        (target / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n", encoding="utf-8"
        )

    def route_to(self, skill):
        self.write_routes({"routes": [{"path": r"\.cs$", "skills": [skill]}]})

    def run_codex_patch(self, body, tool="apply_patch", session=None, env=None):
        """Codex's shape: one lowercase tool name, no file_path, every path inside the patch body."""
        payload = {
            "tool_name": tool,
            "session_id": session or self.session,
            "cwd": str(self.root),
            "tool_input": {"input": body},
        }
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env={**os.environ, **env} if env else None,
        )

    def test_non_write_tool_is_ignored(self):
        self.assertEqual(0, self.run_hook(tool="Bash").returncode)

    def test_a_codex_apply_patch_routes_on_the_path_inside_the_patch_body(self):
        # The defect this covers: the hook was wired for apply_patch but only knew Claude's tool names
        # and file_path key, so every Codex write was allowed while the wiring looked complete.
        result = self.run_codex_patch(
            "*** Begin Patch\n"
            "*** Add File: api/Svc.UnitTests/SomeTests.cs\n"
            "+public class SomeTests { }\n"
            "*** End Patch\n"
        )

        self.assertEqual(2, result.returncode)
        self.assertIn("unit-testing", result.stderr)
        self.assertIn("api/Svc.UnitTests/SomeTests.cs", result.stderr.replace("\\", "/"))

    def test_a_codex_apply_patch_deny_pattern_blocks_on_added_lines(self):
        result = self.run_codex_patch(
            "*** Begin Patch\n"
            "*** Update File: api/Svc.UnitTests/SomeTests.cs\n"
            "@@\n"
            "+var f = new WebApplicationFactory<Program>();\n"
            "*** End Patch\n"
        )

        self.assertEqual(2, result.returncode)
        self.assertIn("rule violation", result.stderr)

    def test_a_codex_patch_removing_a_violation_is_not_blocked_by_it(self):
        # Matching the patch blob whole would block the very edit that deletes the banned symbol.
        self.run_codex_patch(
            "*** Begin Patch\n*** Add File: api/Svc.UnitTests/A.cs\n+class A { }\n*** End Patch\n"
        )

        result = self.run_codex_patch(
            "*** Begin Patch\n"
            "*** Update File: api/Svc.UnitTests/A.cs\n"
            "@@\n"
            "-var f = new WebApplicationFactory<Program>();\n"
            "+var sut = new Thing();\n"
            "*** End Patch\n"
        )

        self.assertEqual(0, result.returncode)

    def test_a_codex_patch_routes_every_file_it_touches(self):
        result = self.run_codex_patch(
            "*** Begin Patch\n"
            "*** Update File: src/Whatever.cs\n"
            "@@\n"
            "+class Whatever { }\n"
            "*** Update File: api/Svc.UnitTests/SomeTests.cs\n"
            "@@\n"
            "+class SomeTests { }\n"
            "*** End Patch\n"
        )

        self.assertEqual(2, result.returncode)
        self.assertIn("unit-testing", result.stderr)

    def test_a_lowercase_write_tool_name_is_still_a_write(self):
        payload_result = self.run_hook(tool="write", path="api/Svc.UnitTests/SomeTests.cs", content="x")

        self.assertEqual(2, payload_result.returncode)

    def test_a_codex_patch_touching_nothing_routed_is_allowed(self):
        result = self.run_codex_patch(
            "*** Begin Patch\n*** Update File: src/Whatever.cs\n@@\n+class Whatever { }\n*** End Patch\n"
        )

        self.assertEqual(0, result.returncode)

    def test_unrouted_path_is_allowed(self):
        self.assertEqual(0, self.run_hook(path="src/Whatever.cs").returncode)

    def test_first_write_to_a_routed_path_blocks_and_names_the_skill(self):
        result = self.run_hook(path="api/Svc.UnitTests/SomeTests.cs", content="public class X { }")

        self.assertEqual(2, result.returncode)
        self.assertIn("unit-testing", result.stderr)
        self.assertIn("NOT written", result.stderr)

    def test_second_write_to_the_same_route_is_allowed(self):
        self.run_hook(path="api/Svc.UnitTests/A.cs", content="class A { }")

        result = self.run_hook(path="api/Svc.UnitTests/B.cs", content="class B { }")

        self.assertEqual(0, result.returncode)

    def test_a_missing_skill_keeps_the_route_blocked(self):
        first = self.run_hook(path="app/web/features/deal/api/dealApi.ts", content="export const x = 1")
        second = self.run_hook(path="app/web/features/deal/api/otherApi.ts", content="export const y = 2")

        self.assertEqual(2, first.returncode)
        self.assertEqual(2, second.returncode)
        self.assertIn("remains blocked on every attempt", second.stderr)

    def test_a_transcript_with_no_attempt_yet_stays_blocked_on_the_second_write(self):
        # With a transcript present but empty of any Skill invocation, proof was checked and found
        # nothing - unlike the no-transcript-at-all fallback, this route must NOT be trusted after one
        # nag, because the mechanism that could prove it was available and simply found no evidence.
        transcript = self.write_transcript([])
        self.run_hook(path="api/Svc.UnitTests/A.cs", content="class A { }", transcript_path=transcript)

        result = self.run_hook(
            path="api/Svc.UnitTests/B.cs", content="class B { }", transcript_path=transcript
        )

        self.assertEqual(2, result.returncode)
        self.assertIn("not merely attempted once", result.stderr)

    def test_a_proven_invocation_in_the_transcript_unblocks_the_route(self):
        transcript = self.write_transcript([("unit-testing", False)])

        result = self.run_hook(
            path="api/Svc.UnitTests/A.cs", content="class A { }", transcript_path=transcript
        )

        self.assertEqual(0, result.returncode, result.stderr)

    def test_a_proven_invocation_stays_proven_on_a_later_write_with_no_fresh_evidence(self):
        # The transcript at the second write no longer needs to repeat the proof - the router's own
        # `seen` cache remembers it, exactly like the pre-existing nag-once cache did.
        transcript = self.write_transcript([("unit-testing", False)])
        self.run_hook(path="api/Svc.UnitTests/A.cs", content="class A { }", transcript_path=transcript)

        empty_transcript = self.write_transcript([])
        result = self.run_hook(
            path="api/Svc.UnitTests/B.cs", content="class B { }", transcript_path=empty_transcript
        )

        self.assertEqual(0, result.returncode, result.stderr)

    def test_a_rejected_invocation_in_the_transcript_blocks_with_a_restart_message(self):
        # The exact incident this closes: the skill's SKILL.md is present on disk (skill_description
        # finds it), but the harness itself returned `Unknown skill` when it was actually invoked this
        # session - a stale plugin registry, proven from the transcript, not guessed at.
        transcript = self.write_transcript([("unit-testing", True)])

        result = self.run_hook(
            path="api/Svc.UnitTests/A.cs", content="class A { }", transcript_path=transcript
        )

        self.assertEqual(2, result.returncode)
        self.assertIn("REJECTED THIS SESSION", result.stderr)
        self.assertIn("Restart the session", result.stderr)
        self.assertNotIn("NOT INSTALLED", result.stderr)

    def test_a_rejected_invocation_keeps_blocking_even_on_a_later_write(self):
        transcript = self.write_transcript([("unit-testing", True)])
        self.run_hook(path="api/Svc.UnitTests/A.cs", content="class A { }", transcript_path=transcript)

        result = self.run_hook(
            path="api/Svc.UnitTests/B.cs", content="class B { }", transcript_path=transcript
        )

        self.assertEqual(2, result.returncode)
        self.assertIn("REJECTED THIS SESSION", result.stderr)

    def test_a_later_success_after_a_rejection_recovers_the_route(self):
        # A restarted-and-resumed session can retry the same name and have it resolve the second time -
        # the later success must win, not the earlier failure.
        first = self.write_transcript([("unit-testing", True)])
        self.run_hook(path="api/Svc.UnitTests/A.cs", content="class A { }", transcript_path=first)

        recovered = self.write_transcript([("unit-testing", True), ("unit-testing", False)])
        result = self.run_hook(
            path="api/Svc.UnitTests/B.cs", content="class B { }", transcript_path=recovered
        )

        self.assertEqual(0, result.returncode, result.stderr)

    def test_a_missing_skill_is_reported_as_missing_not_rejected_even_with_a_transcript(self):
        # An uninstalled skill is a deployment fault, independent of anything the transcript shows -
        # the two failure modes must stay visibly distinct so the fix each one names is the right one.
        transcript = self.write_transcript([("no-such-skill-here", True)])
        self.write_routes({"routes": [{"path": r"\.cs$", "skills": ["no-such-skill-here"]}]})

        result = self.run_hook(path="a.cs", content="class A { }", transcript_path=transcript)

        self.assertEqual(2, result.returncode)
        self.assertIn("NOT INSTALLED", result.stderr)
        self.assertNotIn("REJECTED THIS SESSION", result.stderr)

    def test_an_unreadable_transcript_path_falls_back_to_nag_once_then_trust(self):
        self.run_hook(
            path="api/Svc.UnitTests/A.cs",
            content="class A { }",
            transcript_path=self.root / "does-not-exist.jsonl",
        )

        result = self.run_hook(
            path="api/Svc.UnitTests/B.cs",
            content="class B { }",
            transcript_path=self.root / "does-not-exist.jsonl",
        )

        self.assertEqual(0, result.returncode, result.stderr)

    def test_a_new_session_is_reminded_again(self):
        self.run_hook(path="api/Svc.UnitTests/A.cs", content="class A { }")

        # A fresh uuid every run: the router keys its state file by session id, and those files
        # outlive the test, so a literal id passes once and then fails for ever.
        result = self.run_hook(
            path="api/Svc.UnitTests/B.cs", content="class B { }", session=str(uuid.uuid4())
        )

        self.assertEqual(2, result.returncode)

    def test_a_deny_pattern_blocks_even_after_the_route_is_seen(self):
        self.run_hook(path="api/Svc.UnitTests/A.cs", content="class A { }")

        result = self.run_hook(
            path="api/Svc.UnitTests/B.cs",
            content="var f = new WebApplicationFactory<Program>();",
        )

        self.assertEqual(2, result.returncode)
        self.assertIn("rule violation", result.stderr)
        self.assertIn("integration test", result.stderr)

    def test_a_deny_pattern_reads_an_edit_replacement_not_only_a_write(self):
        self.run_hook(path="api/Svc.UnitTests/A.cs", content="class A { }")

        result = self.run_hook(
            tool="Edit",
            path="api/Svc.UnitTests/A.cs",
            extra={"new_string": "var server = new TestServer(builder);"},
        )

        self.assertEqual(2, result.returncode)
        self.assertIn("rule violation", result.stderr)

    def test_content_requires_gates_the_route(self):
        blocked = self.run_hook(
            path="svc/tests/Svc.Tests/Svc.Tests.csproj",
            content="<Project><PropertyGroup><IsTestProject>true</IsTestProject></PropertyGroup></Project>",
        )
        allowed = self.run_hook(
            path="svc/Svc.csproj",
            content="<Project><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>",
        )

        self.assertEqual(2, blocked.returncode)
        self.assertEqual(0, allowed.returncode)

    def test_a_route_names_every_owning_skill_and_its_note(self):
        result = self.run_hook(
            path="svc/tests/Svc.Tests/Svc.Tests.csproj",
            content="<Project><PropertyGroup><IsTestProject>true</IsTestProject></PropertyGroup></Project>",
        )

        self.assertIn("unit-testing", result.stderr)
        self.assertIn("integration-testing", result.stderr)
        self.assertIn("classification moment", result.stderr)

    def test_a_route_pointing_at_an_uninstalled_skill_says_so(self):
        result = self.run_hook(path="app/web/features/deal/api/dealApi.ts", content="export const x = 1")

        self.assertEqual(2, result.returncode)
        self.assertIn("NOT INSTALLED", result.stderr)

    def test_an_unrouted_write_is_blocked_when_the_corpus_is_absent(self):
        # Not one routed skill resolves, so the plugin did not load. An un-routed path is the last
        # unguarded way to write code against absent standards, so it must be blocked too.
        home, env = self.fake_home()
        self.write_routes({"routes": [{"path": r"\.cs$", "skills": ["no-such-skill-zzz"]}]})

        result = self.run_hook(path="notes.txt", content="anything", env=env)

        self.assertEqual(2, result.returncode, result.stdout)
        self.assertIn("standards corpus is not loaded", result.stderr)

    def test_an_unrouted_write_passes_when_a_routed_skill_resolves(self):
        # A resolvable routed skill proves the corpus is loaded; an un-routed path is then unowned and
        # allowed exactly as before, so a present corpus never blocks an unowned file.
        self.write_routes({"routes": [{"path": r"\.cs$", "skills": ["committing"]}]})

        result = self.run_hook(path="notes.txt", content="anything")

        self.assertEqual(0, result.returncode, result.stderr)

    def test_a_skill_in_the_hooks_own_plugin_resolves(self):
        # A plugin copies its payload, so an installed hook sits beside the skills it names. Resolving
        # only ~/.agents and ~/.claude reported every plugin-delivered skill as NOT INSTALLED - in the
        # delivery mode that is meant to become primary.
        home, env = self.fake_home()
        plugin = self.root / "plugin"
        self.plant_skill(plugin / "skills", "planted-standard", "Planted by the own-plugin test.")
        plugin_hook = plugin / "hooks" / "skill_router.py"
        plugin_hook.parent.mkdir()
        shutil.copy2(HOOK, plugin_hook)
        shutil.copy2(HOOK.parent / "hook_runtime.py", plugin_hook.parent / "hook_runtime.py")
        env["CLAUDE_PLUGIN_ROOT"] = str(plugin)
        self.route_to("planted-standard")

        result = self.run_hook(path="a.cs", content="class A { }", env=env, hook=plugin_hook)

        self.assertEqual(2, result.returncode)
        self.assertIn("Planted by the own-plugin test.", result.stderr)
        self.assertNotIn("NOT INSTALLED", result.stderr)

    def test_a_workspace_root_variable_does_not_redirect_vendored_skill_lookup(self):
        home, env = self.fake_home()
        self.plant_skill(
            self.root / ".agents" / "skills",
            "planted-standard",
            "Planted beside the vendored hook.",
        )
        vendored_hook = self.root / ".agents" / "hooks" / "skill_router.py"
        vendored_hook.parent.mkdir()
        shutil.copy2(HOOK, vendored_hook)
        shutil.copy2(HOOK.parent / "hook_runtime.py", vendored_hook.parent / "hook_runtime.py")
        env["PLUGIN_ROOT"] = str(self.root)
        self.route_to("planted-standard")

        result = self.run_hook(path="a.cs", content="class A { }", env=env, hook=vendored_hook)

        self.assertEqual(2, result.returncode)
        self.assertIn("Planted beside the vendored hook.", result.stderr)
        self.assertNotIn("NOT INSTALLED", result.stderr)

    def write_claude_manifest(self, home, install_paths):
        manifest = home / ".claude/plugins/installed_plugins.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(
            json.dumps({
                "version": 2,
                "plugins": {
                    f"p{i}@m": [{"scope": "user", "installPath": str(path)}]
                    for i, path in enumerate(install_paths)
                },
            }),
            encoding="utf-8",
        )

    def test_a_skill_in_another_installed_claude_plugin_resolves(self):
        home, env = self.fake_home()
        cache = home / ".claude/plugins/cache/some-marketplace/some-plugin/1.0.0"
        self.plant_skill(cache / "skills", "planted-standard", "Planted in the Claude plugin cache.")
        self.write_claude_manifest(home, [cache])
        self.route_to("planted-standard")

        result = self.run_hook(path="a.cs", content="class A { }", env=env)

        self.assertEqual(2, result.returncode)
        self.assertIn("Planted in the Claude plugin cache.", result.stderr)

    def test_a_claude_payload_left_in_the_cache_after_uninstall_is_not_resolved(self):
        # The real case: removing a marketplace dropped its plugins from the manifest and left 90 files
        # in the cache with NO .orphaned_at marker. A cache directory proves a plugin WAS installed,
        # never that it still is - so the manifest is the authority, not the directory layout.
        home, env = self.fake_home()
        cache = home / ".claude/plugins/cache/gone-marketplace/gone-plugin/1.0.0"
        self.plant_skill(cache / "skills", "planted-standard", "Left in the cache by an uninstall.")
        self.write_claude_manifest(home, [])
        self.route_to("planted-standard")

        result = self.run_hook(path="a.cs", content="class A { }", env=env)

        self.assertEqual(2, result.returncode)
        self.assertNotIn("Left in the cache by an uninstall.", result.stderr)
        self.assertIn("NOT INSTALLED", result.stderr)

    def test_a_skill_in_an_installed_codex_plugin_resolves(self):
        home, env = self.fake_home()
        cache = home / ".codex/plugins/cache/some-marketplace/some-plugin/1.0.0"
        self.plant_skill(cache / "skills", "planted-standard", "Planted in the Codex plugin cache.")
        self.route_to("planted-standard")

        result = self.run_codex_patch(
            "*** Begin Patch\n*** Add File: a.cs\n+class A { }\n*** End Patch\n", env=env
        )

        self.assertEqual(2, result.returncode)
        self.assertIn("Planted in the Codex plugin cache.", result.stderr)

    def test_a_codex_write_does_not_resolve_from_claudes_plugin_cache(self):
        home, env = self.fake_home()
        cache = home / ".claude/plugins/cache/some-marketplace/some-plugin/1.0.0"
        self.plant_skill(cache / "skills", "planted-standard", "Claude only.")
        self.write_claude_manifest(home, [cache])
        self.route_to("planted-standard")

        result = self.run_codex_patch(
            "*** Begin Patch\n*** Add File: a.cs\n+class A { }\n*** End Patch\n", env=env
        )

        self.assertEqual(2, result.returncode)
        self.assertNotIn("Claude only.", result.stderr)
        self.assertIn("NOT INSTALLED FOR CODEX", result.stderr)

    def test_a_claude_write_does_not_resolve_from_codexs_plugin_cache(self):
        home, env = self.fake_home()
        cache = home / ".codex/plugins/cache/some-marketplace/some-plugin/1.0.0"
        self.plant_skill(cache / "skills", "planted-standard", "Codex only.")
        self.write_claude_manifest(home, [])
        self.route_to("planted-standard")

        result = self.run_hook(path="a.cs", content="class A { }", env=env)

        self.assertEqual(2, result.returncode)
        self.assertNotIn("Codex only.", result.stderr)
        self.assertIn("NOT INSTALLED FOR CLAUDE", result.stderr)

    def test_an_orphaned_plugin_cache_is_not_treated_as_installed(self):
        # Uninstalling leaves the cache directory behind with this marker; one was found in the wild.
        # Reading a description out of it would announce a skill the session cannot load.
        home, env = self.fake_home()
        cache = home / ".claude/plugins/cache/some-marketplace/some-plugin/1.0.0"
        self.plant_skill(cache / "skills", "planted-standard", "Left behind by an uninstall.")
        (cache / ".orphaned_at").write_text("2026-08-18", encoding="utf-8")
        self.route_to("planted-standard")

        result = self.run_hook(path="a.cs", content="class A { }", env=env)

        self.assertEqual(2, result.returncode)
        self.assertNotIn("Left behind by an uninstall.", result.stderr)
        self.assertIn("NOT INSTALLED", result.stderr)

    def test_a_repo_anchored_route_matches_the_repo_relative_path_only(self):
        # The route is anchored with ^, so it can only match once the absolute prefix is stripped -
        # and must not match the same tail sitting deeper in the tree.
        inside = self.run_hook(path="app/web/api/dealApi.ts", content="export const x = 1")
        deeper = self.run_hook(path="vendor/app/web/api/dealApi.ts", content="export const x = 1")

        self.assertEqual(2, inside.returncode)
        self.assertEqual(0, deeper.returncode)

    def test_a_malformed_routes_file_blocks_instead_of_failing_open(self):
        """Opting in and then breaking the table is the ENF1 failure: inert while looking wired."""
        self.write_routes("{ not json")

        result = self.run_hook(path="api/Svc.UnitTests/A.cs", content="class A { }")

        self.assertEqual(2, result.returncode)
        self.assertIn("not valid JSON", result.stderr)

    def test_a_routes_file_without_a_routes_key_blocks(self):
        self.write_routes({"rules": []})

        result = self.run_hook(path="api/Svc.UnitTests/A.cs", content="class A { }")

        self.assertEqual(2, result.returncode)
        self.assertIn("no `routes` key", result.stderr)

    def test_a_routes_key_of_the_wrong_type_blocks(self):
        self.write_routes({"routes": {"path": "x"}})

        result = self.run_hook(path="api/Svc.UnitTests/A.cs", content="class A { }")

        self.assertEqual(2, result.returncode)
        self.assertIn("must be a list", result.stderr)

    def test_an_empty_routes_list_is_allowed(self):
        """A table that parses and declares no routes is a real, valid opt-out."""
        self.write_routes({"routes": []})

        result = self.run_hook(path="api/Svc.UnitTests/A.cs", content="class A { }")

        self.assertEqual(0, result.returncode)

    def test_a_repo_without_the_routes_file_is_ignored(self):
        other = Path(tempfile.mkdtemp()).resolve()
        (other / ".git").mkdir()

        result = self.run_hook(path="api/Svc.UnitTests/A.cs", content="class A { }", root=other)

        self.assertEqual(0, result.returncode)

    def run_query(self, *paths, stdin="", root=None, json_output=False):
        argv = [sys.executable, str(HOOK), "--skills-for"]
        if json_output:
            argv.append("--json")
        return subprocess.run(
            argv + list(paths),
            input=stdin,
            capture_output=True,
            text=True,
            cwd=str(root or self.root),
        )

    def run_verify(self, harness, env=None):
        return subprocess.run(
            [sys.executable, str(HOOK), "--verify-install", harness],
            capture_output=True,
            text=True,
            cwd=str(self.root),
            env={**os.environ, **env} if env else None,
        )

    def test_install_verification_fails_when_any_routed_skill_is_missing(self):
        self.write_routes({"routes": [{"path": r"\.cs$", "skills": ["no-such-skill-here"]}]})

        result = self.run_verify("codex")

        self.assertEqual(2, result.returncode)
        self.assertIn("no-such-skill-here", result.stdout)

    def test_install_verification_uses_only_the_selected_harness(self):
        home, env = self.fake_home()
        cache = home / ".claude/plugins/cache/some-marketplace/some-plugin/1.0.0"
        self.plant_skill(cache / "skills", "planted-standard", "Claude only.")
        self.write_claude_manifest(home, [cache])
        self.write_routes({"routes": [{"path": r"\.cs$", "skills": ["planted-standard"]}]})

        claude = self.run_verify("claude", env=env)
        codex = self.run_verify("codex", env=env)

        self.assertEqual(0, claude.returncode)
        self.assertEqual(2, codex.returncode)

    def write_file(self, path, content):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def test_the_query_names_the_skill_owing_each_changed_path(self):
        self.write_file("api/Svc.UnitTests/A.cs", "class A { }")

        result = self.run_query("api/Svc.UnitTests/A.cs", json_output=True)

        self.assertEqual(0, result.returncode)
        self.assertEqual(
            ["api/Svc.UnitTests/A.cs"], json.loads(result.stdout)["skills"]["unit-testing"]
        )

    def test_the_query_deduplicates_a_skill_added_by_overlapping_routes(self):
        self.write_routes(
            {
                "routes": [
                    {"path": r"\.cs$", "skills": ["unit-testing"]},
                    {"path": r"UnitTests/", "skills": ["unit-testing"]},
                ]
            }
        )
        self.write_file("api/Svc.UnitTests/A.cs", "class A { }")

        result = self.run_query("api/Svc.UnitTests/A.cs", json_output=True)

        self.assertEqual(
            ["api/Svc.UnitTests/A.cs"], json.loads(result.stdout)["skills"]["unit-testing"]
        )

    def test_the_query_reads_paths_from_stdin(self):
        self.write_file("api/Svc.UnitTests/A.cs", "class A { }")

        result = self.run_query(stdin="api/Svc.UnitTests/A.cs\nsrc/Whatever.cs\n")

        self.assertIn("unit-testing", result.stdout)
        self.assertNotIn("Whatever", result.stdout)

    def test_the_query_owes_nothing_for_unrouted_paths(self):
        result = self.run_query("src/Whatever.cs")

        self.assertEqual(0, result.returncode)
        self.assertIn("no skill is owed", result.stdout)

    def test_the_query_gates_a_content_route_on_the_file_on_disk(self):
        self.write_file(
            "svc/tests/Svc.Tests/Svc.Tests.csproj",
            "<Project><PropertyGroup><IsTestProject>true</IsTestProject></PropertyGroup></Project>",
        )
        self.write_file("svc/Svc.csproj", "<Project></Project>")

        result = self.run_query(
            "svc/tests/Svc.Tests/Svc.Tests.csproj", "svc/Svc.csproj", json_output=True
        )

        self.assertEqual(
            ["svc/tests/Svc.Tests/Svc.Tests.csproj"],
            json.loads(result.stdout)["skills"]["integration-testing"],
        )

    def test_the_query_reports_a_deny_pattern_already_in_the_tree(self):
        self.write_file("api/Svc.UnitTests/A.cs", "var f = new WebApplicationFactory<Program>();")

        result = self.run_query("api/Svc.UnitTests/A.cs")

        self.assertEqual(0, result.returncode)  # a query reports; the write-time hook is what blocks
        self.assertIn("DENY PATTERN HIT", result.stdout)
        self.assertIn("integration test", result.stdout)

    def test_the_query_still_routes_a_deleted_path(self):
        result = self.run_query("api/Svc.UnitTests/Gone.cs")

        self.assertIn("unit-testing", result.stdout)

    def test_the_query_says_so_when_no_table_is_reachable(self):
        other = Path(tempfile.mkdtemp()).resolve()
        (other / ".git").mkdir()

        result = self.run_query("api/Svc.UnitTests/A.cs", root=other)

        self.assertEqual(0, result.returncode)
        self.assertIn("no skill is owed", result.stdout)


if __name__ == "__main__":
    unittest.main()


class RegisteredRepoTests(unittest.TestCase):
    """A carved service repo carries no table: the registry inside the plugin says which one it gets."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.shipped = self.root / "shipped"
        self.shipped.mkdir()
        self.repo = self.root / "repo"
        (self.repo / ".git").mkdir(parents=True)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(setattr, skill_router, "SHIPPED_ROUTES_DIR", skill_router.SHIPPED_ROUTES_DIR)
        skill_router.SHIPPED_ROUTES_DIR = self.shipped

    def write_registry(self, repos):
        (self.shipped / "registry.json").write_text(json.dumps({"repos": repos}), encoding="utf-8")

    def write_table(self, kind, skills):
        table = {"routes": [{"path": "[.]cs$", "skills": skills}]}
        (self.shipped / (kind + ".json")).write_text(json.dumps(table), encoding="utf-8")

    def set_origin(self, url):
        config = chr(10).join(
            ["[remote " + chr(34) + "origin" + chr(34) + "]", "    url = " + url, "    fetch = +refs/heads/*", ""]
        )
        (self.repo / ".git" / "config").write_text(config, encoding="utf-8")

    def test_identity_comes_from_the_origin_remote_in_every_url_form(self):
        for url, expected in (
            ("https://github.com/Example/payment.git", "example/payment"),
            ("https://github.com/Example/Payment", "example/payment"),
            ("git@github.com:Example/payment.git", "example/payment"),
            ("ssh://git@github.com/Example/payment", "example/payment"),
        ):
            with self.subTest(url=url):
                self.set_origin(url)
                self.assertEqual(expected, skill_router.repo_identity(self.repo))

    def test_a_registered_repo_with_no_table_of_its_own_gets_the_shipped_one(self):
        self.set_origin("https://github.com/Example/payment.git")
        self.write_registry({"example/payment": "dotnet-service"})
        self.write_table("dotnet-service", ["csharp-style"])
        routes = skill_router.load_routes(self.repo)
        self.assertEqual([["csharp-style"]], [route["skills"] for route in routes])

    def test_the_repos_own_table_wins_over_the_registry(self):
        self.set_origin("https://github.com/Example/payment.git")
        self.write_registry({"example/payment": "dotnet-service"})
        self.write_table("dotnet-service", ["csharp-style"])
        (self.repo / ".agents").mkdir()
        (self.repo / ".agents" / "skill-routes.json").write_text(
            json.dumps({"routes": [{"path": "[.]cs$", "skills": ["local-override"]}]}), encoding="utf-8"
        )
        routes = skill_router.load_routes(self.repo)
        self.assertEqual([["local-override"]], [route["skills"] for route in routes])

    def test_an_unregistered_repo_is_not_routed(self):
        self.set_origin("https://github.com/someone/else.git")
        self.write_registry({"example/payment": "dotnet-service"})
        self.write_table("dotnet-service", ["csharp-style"])
        self.assertIsNone(skill_router.load_routes(self.repo))

    def test_no_origin_remote_is_not_routed_rather_than_a_crash(self):
        self.write_registry({"example/payment": "dotnet-service"})
        self.write_table("dotnet-service", ["csharp-style"])
        self.assertIsNone(skill_router.load_routes(self.repo))

    def test_a_registered_kind_with_no_shipped_table_is_loud(self):
        self.set_origin("https://github.com/Example/payment.git")
        self.write_registry({"example/payment": "dotnet-service"})
        with self.assertRaises(skill_router.RoutesUnusable):
            skill_router.load_routes(self.repo)

    def search_dirs(self, *directories):
        """Pin the search to these directories, so a plugin installed on the machine cannot answer."""
        self.addCleanup(setattr, skill_router, "routes_search_dirs", skill_router.routes_search_dirs)
        skill_router.routes_search_dirs = lambda: iter(directories)

    def test_the_registry_is_found_in_another_plugin_not_only_beside_this_hook(self):
        """The mechanism and the registry ship from different repos, so they install as different plugins."""
        other = self.root / "other-plugin-routes"
        other.mkdir()
        (other / "registry.json").write_text(
            json.dumps({"repos": {"example/payment": "dotnet-service"}}), encoding="utf-8"
        )
        (other / "dotnet-service.json").write_text(
            json.dumps({"routes": [{"path": "[.]cs$", "skills": ["csharp-style"]}]}), encoding="utf-8"
        )
        self.search_dirs(self.shipped, other)
        self.set_origin("https://github.com/Example/payment.git")

        routes = skill_router.load_routes(self.repo)

        self.assertEqual([["csharp-style"]], [route["skills"] for route in routes])

    def test_a_registry_silent_about_this_repo_does_not_stop_the_search(self):
        """Most installed plugins ship no registry, and an org's registry says nothing about other orgs."""
        silent = self.root / "silent-plugin-routes"
        silent.mkdir()
        (silent / "registry.json").write_text(
            json.dumps({"repos": {"someone-else/thing": "monorepo"}}), encoding="utf-8"
        )
        self.search_dirs(silent, self.shipped)
        self.set_origin("https://github.com/Example/payment.git")
        self.write_registry({"example/payment": "dotnet-service"})
        self.write_table("dotnet-service", ["csharp-style"])

        routes = skill_router.load_routes(self.repo)

        self.assertEqual([["csharp-style"]], [route["skills"] for route in routes])

    def test_the_hooks_own_payload_is_searched_before_any_other_plugin(self):
        self.set_origin("https://github.com/Example/payment.git")
        self.write_registry({"example/payment": "dotnet-service"})
        self.write_table("dotnet-service", ["from-own-payload"])
        later = self.root / "later-plugin-routes"
        later.mkdir()
        (later / "registry.json").write_text(
            json.dumps({"repos": {"example/payment": "dotnet-service"}}), encoding="utf-8"
        )
        (later / "dotnet-service.json").write_text(
            json.dumps({"routes": [{"path": "[.]cs$", "skills": ["from-another-plugin"]}]}), encoding="utf-8"
        )
        self.search_dirs(self.shipped, later)

        routes = skill_router.load_routes(self.repo)

        self.assertEqual([["from-own-payload"]], [route["skills"] for route in routes])

    def test_a_worktree_checkout_resolves_through_its_gitdir_pointer(self):
        self.set_origin("https://github.com/Example/payment.git")
        worktree_dir = self.repo / ".git" / "worktrees" / "branch"
        worktree_dir.mkdir(parents=True)
        (worktree_dir / "commondir").write_text("../..", encoding="utf-8")
        checkout = self.root / "checkout"
        checkout.mkdir()
        (checkout / ".git").write_text("gitdir: " + str(worktree_dir), encoding="utf-8")
        self.assertEqual("example/payment", skill_router.repo_identity(checkout))

    def test_find_repo_root_falls_back_to_the_git_root(self):
        nested = self.repo / "src" / "Example.Payment.Api"
        nested.mkdir(parents=True)
        self.assertEqual(self.repo, skill_router.find_repo_root(nested))


class PluginWiringTests(unittest.TestCase):
    """The wiring the plugin ships must fire for every tool the hook itself acts on.

    The plugin shipped a matcher without `apply_patch` while the router handled it, so the whole
    plugin was inert for every Codex write. The pre-existing drift check could not see it: it
    compared hook *filenames* across wiring files, which stayed identical throughout.
    """

    REPO = Path(__file__).resolve().parents[3]
    # hooks.json is Claude-only (authored under .claude/), codex-hooks.json is Codex-only (under
    # .codex/) - only the shared .py mechanisms they both wire live under .agents/hooks/.
    CANONICAL = REPO / ".claude" / "hooks" / "hooks.json"
    CODEX_CANONICAL = REPO / ".codex" / "hooks" / "codex-hooks.json"
    GENERATED = REPO / "plugins" / "process-standards" / "hooks" / "hooks.json"
    CODEX_GENERATED = REPO / "plugins" / "process-standards" / "hooks" / "codex-hooks.json"
    ROUTER_MANIFESTS = (CANONICAL,)

    def matcher(self, path):
        wiring = json.loads(path.read_text(encoding="utf-8"))
        entries = [
            entry
            for entry in wiring["hooks"]["PreToolUse"]
            if any(
                "skill_router.py" in " ".join(
                    [inner.get("command", ""), *inner.get("args", [])]
                )
                for inner in entry["hooks"]
            )
        ]
        self.assertEqual(1, len(entries), "one PreToolUse entry should run the router")
        return entries[0]["matcher"]

    def router_write_tools(self):
        source = (self.REPO / ".agents" / "hooks" / "skill_router.py").read_text(encoding="utf-8")
        blocks = re.findall(r"(?:CLAUDE|CODEX)_WRITE_TOOLS = \{(.*?)\}", source, re.S)
        return {
            line.strip().strip('",')
            for block in blocks
            for line in block.splitlines()
            if line.strip()
        }

    def test_the_matcher_covers_every_tool_the_router_acts_on(self):
        for manifest in self.ROUTER_MANIFESTS:
            wired = {name.lower() for name in self.matcher(manifest).split("|")}
            missing = self.router_write_tools() - wired
            self.assertEqual(
                set(), missing, f"{manifest.name}: router handles tools the matcher misses: {missing}"
            )

    def test_every_wired_tool_name_is_one_the_router_acts_on(self):
        for manifest in self.ROUTER_MANIFESTS:
            wired = {name.lower() for name in self.matcher(manifest).split("|")}
            unknown = wired - self.router_write_tools()
            self.assertEqual(
                set(), unknown, f"{manifest.name}: matcher fires for unknown tools: {unknown}"
            )

    def test_codex_manifest_does_not_restore_the_removed_pretool_router(self):
        for manifest in (self.CODEX_CANONICAL, self.CODEX_GENERATED):
            wiring = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertNotIn("PreToolUse", wiring["hooks"])

    def test_the_generated_plugin_wiring_matches_the_canonical_one(self):
        self.assertEqual(
            json.loads(self.CANONICAL.read_text(encoding="utf-8")),
            json.loads(self.GENERATED.read_text(encoding="utf-8")),
            "run .agents/sync-generated.ps1 - the plugin payload has drifted from .agents/",
        )
        self.assertEqual(
            json.loads(self.CODEX_CANONICAL.read_text(encoding="utf-8")),
            json.loads(self.CODEX_GENERATED.read_text(encoding="utf-8")),
            "run .agents/sync-generated.ps1 - the Codex hook payload has drifted from .agents/",
        )


class QualifiedSkillNameTests(unittest.TestCase):
    """A local roster and its generic counterpart share a skill name on purpose, so a route has to be
    able to say which one it means. Unqualified lookup returns whichever root is walked first, and the
    other is hidden with no error - the shadowing that once made one repo's doc answer for another's."""

    def setUp(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("skill_router_qualified", HOOK)
        self.router = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.router)

        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cache = Path(self.temp.name) / "cache"

        # Two plugins from two marketplaces, both owning a skill called `persistence`.
        for marketplace, plugin, blurb in (
            ("dotagents", "dotnet-standards", "the generic rule"),
            ("agent-standards", "dotnet", "this system's roster"),
        ):
            d = self.cache / marketplace / plugin / "1.0.0" / "skills" / "persistence"
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(
                f"---\nname: persistence\ndescription: {blurb}\n---\n\n# persistence\n",
                encoding="utf-8",
            )

        dirs = [
            self.cache / m / p / "1.0.0" / "skills"
            for m, p in (("dotagents", "dotnet-standards"), ("agent-standards", "dotnet"))
        ]
        self.router.skill_search_dirs = lambda harness: iter(dirs)

    def test_the_plugin_layout_resolves_to_its_plugin_name(self):
        d = self.cache / "agent-standards" / "dotnet" / "1.0.0" / "skills"

        self.assertEqual("dotnet", self.router.plugin_of(d))

    def test_a_linked_root_belongs_to_no_plugin(self):
        self.assertIsNone(self.router.plugin_of(Path.home() / ".claude" / "skills"))

    def test_a_qualified_name_resolves_inside_the_plugin_it_names(self):
        self.assertEqual(
            "this system's roster", self.router.skill_description("dotnet:persistence", "codex")
        )

    def test_the_other_half_of_the_pair_is_reachable_by_its_own_qualifier(self):
        self.assertEqual(
            "the generic rule",
            self.router.skill_description("dotnet-standards:persistence", "codex"),
        )

    def test_a_qualified_name_naming_no_installed_plugin_resolves_to_nothing(self):
        self.assertIsNone(self.router.skill_description("react:persistence", "codex"))

    def test_an_unqualified_name_still_resolves_for_a_skill_with_one_home(self):
        self.assertEqual("the generic rule", self.router.skill_description("persistence", "codex"))
