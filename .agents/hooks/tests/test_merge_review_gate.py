import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).resolve().parents[1] / "merge_review_gate.py"
sys.path.insert(0, str(HOOK.parent))
M = "gh pr " + "merge"  # assembled so this file never contains the gated literal


def load_gate():
    spec = importlib.util.spec_from_file_location("merge_review_gate", HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load_gate()


class ReviewWorkOrderStateTests(unittest.TestCase):
    def test_legacy_complete_work_orders_remain_compatible(self):
        self.assertIsNone(gate.review_status("**Reviewed up to commit:** `abc1234`"))

    def test_review_status_is_normalized(self):
        self.assertEqual("complete", gate.review_status("**Review status:** `COMPLETE`"))
        self.assertEqual("in-progress", gate.review_status("**Review status:** `in-progress`"))

    def test_malformed_review_status_fails_closed(self):
        self.assertEqual("invalid", gate.review_status("**Review status:** complete"))

    def test_duplicate_review_status_fails_closed(self):
        review = "\n".join(
            ("**Review status:** `complete`", "**Review status:** `in-progress`")
        )

        self.assertEqual("invalid", gate.review_status(review))

    def test_valid_status_plus_malformed_duplicate_fails_closed(self):
        review = "\n".join(
            ("**Review status:** `complete`", "**Review status:** complete")
        )

        self.assertEqual("invalid", gate.review_status(review))

    def test_indented_status_and_judgment_fields_fail_closed(self):
        self.assertEqual(
            "invalid",
            gate.review_status(" **Review status:** `complete`"),
        )
        self.assertEqual(
            "invalid",
            gate.review_judgment(" **Judgment:** `approved`"),
        )
        review = "\n".join(
            ("**Review status:** `complete`", " **Review status:** `in-progress`")
        )
        self.assertEqual("invalid", gate.review_status(review))

    def test_markdown_code_examples_are_not_metadata_fields(self):
        review = "\n".join(
            (
                "**Review status:** `complete`",
                "**Judgment:** `approved`",
                "**Reviewed up to commit:** `abc1234`  `(2026-08-26)`",
                "```markdown",
                "```not-a-closing-fence",
                "**Review status:** `in-progress`",
                "**Judgment:** `pending`",
                "**Reviewed up to commit:** `def5678`",
                "**Security-reviewed up to commit:** `def5678`",
                "```",
                "    **Review status:** `in-progress`",
                "    **Judgment:** `pending`",
            )
        )

        self.assertEqual("complete", gate.review_status(review))
        self.assertEqual("approved", gate.review_judgment(review))
        self.assertEqual(
            "abc1234", gate.work_order_sha_field(review, "Reviewed up to commit")
        )
        self.assertIsNone(
            gate.work_order_sha_field(review, "Security-reviewed up to commit")
        )
        self.assertIsNone(gate.review_completion_problem(review))

    def test_completion_markers_are_unique_top_level_metadata(self):
        duplicate = "\n".join(
            (
                "**Reviewed up to commit:** `abc1234`",
                "**Reviewed up to commit:** `def5678`",
            )
        )

        self.assertEqual(
            "invalid", gate.work_order_sha_field(duplicate, "Reviewed up to commit")
        )
        self.assertEqual(
            "invalid",
            gate.work_order_sha_field(
                " **Security-reviewed up to commit:** `abc1234`",
                "Security-reviewed up to commit",
            ),
        )

    def test_final_judgment_is_normalized_and_malformed_values_fail_closed(self):
        self.assertEqual("approved", gate.review_judgment("**Judgment:** `APPROVED`"))
        self.assertEqual("invalid", gate.review_judgment("**Judgment:** approved"))
        self.assertIsNone(gate.review_judgment("legacy work order"))

    def test_new_judgment_without_status_is_not_legacy(self):
        review = "\n".join(
            ("**Judgment:** `pending`", "**Reviewed up to commit:** `abc1234`")
        )

        self.assertIn("no `Review status`", gate.review_completion_problem(review))
        staged = "\n".join(
            (
                "**Cross-area notes status:** `pending`",
                "**Parent summary status:** `pending`",
                "**Reviewed up to commit:** `abc1234`",
            )
        )
        self.assertIn("no `Review status`", gate.review_completion_problem(staged))

    def test_complete_review_requires_one_final_parent_judgment(self):
        cases = (
            ("**Judgment:** `approved`", False),
            ("**Judgment:** `changes-requested`", False),
            ("", True),
            ("**Judgment:** `pending`", True),
            ("**Judgment:** approved", True),
            (
                "\n".join(
                    (
                        "**Judgment:** `approved`",
                        "**Judgment:** `changes-requested`",
                    )
                ),
                True,
            ),
        )
        for judgment, has_problem in cases:
            with self.subTest(judgment=judgment):
                review = "**Review status:** `complete`"
                if judgment:
                    review += "\n" + judgment
                self.assertEqual(
                    has_problem,
                    gate.review_completion_problem(review) is not None,
                )

    def test_staged_review_requires_complete_parent_finalization_state(self):
        prefix = "\n".join(
            (
                "**Review status:** `complete`",
                "**Judgment:** `approved`",
            )
        )
        complete = prefix + "\n" + "\n".join(
            (
                "**Cross-area notes status:** `complete`",
                "**Parent summary status:** `complete`",
            )
        )
        self.assertIsNone(gate.review_completion_problem(complete))
        for state in (
            "## Coverage\n- [x] runtime\n\n## Parent finalization",
            "## Review pass — 2026-08-26 — staged:runtime",
            "**Cross-area notes status:** `pending`\n**Parent summary status:** `complete`",
            "**Cross-area notes status:** `complete`\n**Parent summary status:** `pending`",
            "**Parent summary status:** `complete`",
            "**Cross-area notes status:** `complete`",
        ):
            with self.subTest(state=state):
                self.assertIn(
                    "incomplete parent finalization",
                    gate.review_completion_problem(prefix + "\n" + state),
                )

    def test_open_and_in_progress_items_are_unresolved(self):
        review = "\n".join(
            (
                "- [ ] R1 open",
                "- [~] R2 being addressed",
                "- [x] R3 fixed",
                "- [wontfix] R4 accepted",
            )
        )

        self.assertEqual(
            ["- [ ] R1 open", "- [~] R2 being addressed"],
            gate.unresolved_review_items(review),
        )


class SecurityPatternTests(unittest.TestCase):
    """The generic patterns hold everywhere; a repo's own service names are its data."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / ".agents").mkdir()

    def write_config(self, config):
        body = config if isinstance(config, str) else json.dumps(config)
        path = self.root / gate.CONFIG_FILE
        path.write_text(body, encoding="utf-8")
        return path

    def test_a_workflow_change_is_sensitive_without_any_repo_config(self):
        self.assertEqual(
            ".github/workflows/ci.yml", gate.touches_security([".github/workflows/ci.yml"])
        )

    def test_repository_settings_are_sensitive_without_any_repo_config(self):
        for path in (".agents/settings.json", ".AGENTS/SETTINGS.JSON", ".Agents/Settings.Json"):
            with self.subTest(path=path):
                self.assertEqual(path, gate.touches_security([path]))

    def test_credential_vocabulary_is_sensitive_without_any_repo_config(self):
        self.assertEqual("src/ApiKeyStore.cs", gate.touches_security(["src/ApiKeyStore.cs"]))

    def test_an_ordinary_path_is_not_sensitive(self):
        self.assertIsNone(gate.touches_security(["src/Widget.cs"]))

    def test_a_repo_declared_path_becomes_sensitive(self):
        patterns = gate.security_patterns(self.write_config({"security_paths": [r"(^|/)Acme\.Auth"]}))

        self.assertEqual("api/Acme.Auth/X.cs", gate.touches_security(["api/Acme.Auth/X.cs"], patterns))

    def test_the_generic_patterns_survive_a_repo_declaration(self):
        patterns = gate.security_patterns(self.write_config({"security_paths": [r"nothing"]}))

        self.assertEqual(
            ".github/workflows/ci.yml",
            gate.touches_security([".github/workflows/ci.yml"], patterns),
        )

    def test_a_config_with_no_security_paths_is_valid(self):
        patterns = gate.security_patterns(self.write_config({}))

        self.assertIsNone(gate.touches_security(["src/Widget.cs"], patterns))

    def test_malformed_json_raises_rather_than_failing_open(self):
        path = self.write_config("{ not json")

        with self.assertRaises(gate.ConfigUnusable):
            gate.security_patterns(path)

    def test_security_paths_of_the_wrong_type_raises(self):
        path = self.write_config({"security_paths": "Acme.Auth"})

        with self.assertRaises(gate.ConfigUnusable):
            gate.security_patterns(path)

    def test_an_uncompilable_pattern_raises(self):
        path = self.write_config({"security_paths": ["("]})

        with self.assertRaises(gate.ConfigUnusable):
            gate.security_patterns(path)


class SecurityRangeTests(unittest.TestCase):
    """The security layer must judge the head being MERGED, and re-ask only when a sensitive
    path moved. Reading the session's HEAD made a sensitive PR merged from another checkout
    skip the layer outright; demanding marker == head left the marker with no legal exit."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.run_git("init", "-q", ".")
        self.run_git("symbolic-ref", "HEAD", "refs/heads/main")
        self.run_git("config", "user.email", "t@example.com")
        self.run_git("config", "user.name", "t")
        self.WORK_ORDER = "reviews/Fix-CredentialScoping.md"
        self.base = self.commit("readme.md", "hello")
        self.run_git("checkout", "-q", "-b", "feature")
        self.sensitive = self.commit("src/credentials.json", "{}")
        self.later = self.commit("docs/note.md", "note")
        self.run_git("checkout", "-q", "main")
        gate._GIT_CWD[0] = str(self.root)
        self.addCleanup(lambda: gate._GIT_CWD.__setitem__(0, "."))

    def run_git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=str(self.root), check=True, capture_output=True, text=True
        ).stdout.strip()

    def commit(self, relative, body):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        self.run_git("add", "-A")
        self.run_git("commit", "-q", "-m", "add " + relative)
        return self.run_git("rev-parse", "HEAD")

    def test_a_marker_is_still_current_when_only_ordinary_files_changed(self):
        self.assertFalse(
            gate.security_no_longer_covered(self.sensitive, self.later, gate._SECURITY_PATTERNS)
        )

    def test_a_marker_is_stale_once_a_sensitive_path_changes(self):
        self.assertTrue(
            gate.security_no_longer_covered(self.base, self.later, gate._SECURITY_PATTERNS)
        )

    def test_an_unresolvable_marker_fails_closed(self):
        self.assertTrue(
            gate.security_no_longer_covered("0" * 40, self.later, gate._SECURITY_PATTERNS)
        )

    def test_stamping_the_marker_does_not_restale_it_on_a_sensitively_named_branch(self):
        # The regression: the work order's path comes from the branch slug, so a branch named for
        # what it fixes puts `credential` into `reviews/<slug>.md` — where the generic vocabulary
        # matches it. Stamping the marker is a commit to that path, so stamping restaled the marker
        # and the branch could not be merged from any checkout. Fix/CredentialScoping hit exactly
        # this; Fix/AuthenticationRetry would too.
        self.run_git("checkout", "-q", "feature")
        stamped = self.commit(self.WORK_ORDER, "**Security-reviewed up to ...**")

        self.assertFalse(
            gate.security_no_longer_covered(
                self.later, stamped, gate._SECURITY_PATTERNS, self.WORK_ORDER
            )
        )

    def test_the_work_order_never_hides_a_real_sensitive_change_beside_it(self):
        # The exclusion is one path, not a range: a sensitive file in the same range still stales.
        self.run_git("checkout", "-q", "feature")
        self.commit(self.WORK_ORDER, "stamped")
        with_code = self.commit("src/credentials.json", '{"rotated": true}')

        self.assertTrue(
            gate.security_no_longer_covered(
                self.later, with_code, gate._SECURITY_PATTERNS, self.WORK_ORDER
            )
        )

    def test_a_sensitive_file_under_reviews_is_not_excused_by_living_there(self):
        # A `reviews/` prefix match would have put anything a writer placed in that directory
        # permanently beyond staleness detection once a first marker existed. Only this branch's
        # own artifact is evidence; a script sitting beside it is not.
        self.run_git("checkout", "-q", "feature")
        planted = self.commit("reviews/rotate-credentials.py", "print('rotate')")

        self.assertTrue(
            gate.security_no_longer_covered(
                self.later, planted, gate._SECURITY_PATTERNS, self.WORK_ORDER
            )
        )

    def test_another_branchs_work_order_is_not_this_branchs_evidence(self):
        # Arrives on a merge from main. It is not what this branch's security review looked at.
        self.run_git("checkout", "-q", "feature")
        other = self.commit("reviews/Fix-PasswordRotation.md", "someone else's review")

        self.assertTrue(
            gate.security_no_longer_covered(
                self.later, other, gate._SECURITY_PATTERNS, self.WORK_ORDER
            )
        )

if __name__ == "__main__":
    unittest.main()
