import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS = ROOT / ".agents" / "workflows"
FIXTURE = Path(__file__).parent / "fixtures" / "review_workflow_scenarios.json"
sys.path.insert(0, str(WORKFLOWS))

from host_runtime import HostAdapterRegistry, WriterLeaseRegistry
from fixtures.lane_expectations import authored_skill, packaged_adapter
from fixtures.review_workflow_harness import ReviewWorkflowHarness


class ReviewWorkflowAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def harness(self, host="codex"):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        repository = Path(temporary.name).resolve()
        harness = ReviewWorkflowHarness(
            ROOT,
            WORKFLOWS,
            repository,
            host,
            self.fixture,
            HostAdapterRegistry,
            WriterLeaseRegistry,
        )
        self.addCleanup(harness.cleanup)
        return harness

    def test_selection_matrix_covers_every_review_family_entry(self):
        cases = {case["id"]: case for case in self.fixture["selection_cases"]}

        self.assertEqual(
            {
                "review-current": "review",
                "review-pr": "review",
                "incremental": "incremental-review",
                "large": "big-review",
                "large-all": "big-review-all",
                "address": "address-review",
                "docs": "docs-review",
            },
            {key: value["expected_skill"] for key, value in cases.items()},
        )
        self.assertEqual(len(cases), len({case["request"] for case in cases.values()}))
        descriptions = {}
        for skill in {case["expected_skill"] for case in cases.values()}:
            body = authored_skill(skill).read_text(
                encoding="utf-8"
            )
            descriptions[skill] = next(
                line.removeprefix("description: ").strip()
                for line in body.splitlines()
                if line.startswith("description: ")
            )
        for case in cases.values():
            terms = [term.casefold() for term in case["description_terms"]]
            selected = descriptions[case["expected_skill"]].casefold()
            for term in terms:
                self.assertIn(term, selected, case["id"])
            for skill, description in descriptions.items():
                if skill != case["expected_skill"]:
                    self.assertFalse(
                        all(term in description.casefold() for term in terms),
                        f"{case['id']} also matches {skill}",
                    )

    def test_frozen_candidate_native_first_fresh_lenses_and_parent_synthesis(self):
        for host in self.fixture["hosts"]:
            with self.subTest(host=host):
                outcome = self.harness(host).review()
                candidate = outcome["candidate"]

                self.assertEqual("native-general", outcome["events"][0])
                self.assertEqual("parent-synthesis", outcome["events"][-1])
                self.assertEqual(outcome["native"]["artifacts"], self.harness_artifacts(candidate))
                self.assertEqual(2, outcome["peak_active"])
                self.assertEqual(2, outcome["peak_executing"])
                self.assertEqual([2], outcome["wave_sizes"])
                self.assertEqual(outcome["head_before"], outcome["head_after"])
                self.assertFalse(Path(candidate["bundle_path"]).exists())

                dispatches = [record["dispatch"] for record in outcome["records"]]
                self.assertEqual(len(dispatches), len({item["dispatch_id"] for item in dispatches}))
                self.assertEqual(len(dispatches), len({item["stage_id"] for item in dispatches}))
                for dispatch in dispatches:
                    self.assertEqual(self.harness_artifacts(candidate), dispatch["context"]["immutable_artifacts"])
                    self.assertEqual(
                        ["The parent retains severity and final judgment."],
                        dispatch["context"]["prior_decisions"],
                    )
                    self.assertFalse(dispatch["permissions"]["allow_subdispatch"])
                for record in outcome["records"]:
                    immutable = {
                        item["locator"]
                        for item in record["result"]["evidence"]
                        if item["kind"] == "immutable-artifact"
                    }
                    self.assertEqual(set(self.harness_artifacts(candidate)), immutable)

                self.assertEqual(2, len(outcome["synthesis"]["findings"]))
                self.assertEqual(
                    {"src/alpha.txt:1", "tests/test_alpha.txt:1"},
                    {finding["locator"] for finding in outcome["synthesis"]["findings"]},
                )
                self.assertEqual(
                    {"HIGH", "MEDIUM"},
                    {finding["severity"] for finding in outcome["synthesis"]["findings"]},
                )
                for record in outcome["records"]:
                    self.assertNotIn("severity", record["result"])

                work_order = outcome["work_order"].read_text(encoding="utf-8")
                self.assertIn("**Review status:** `complete`", work_order)
                self.assertIn(f"**Reviewed up to commit:** `{candidate['head']}`", work_order)
                self.assertIn(f"sha256:{candidate['path_digest']}", work_order)
                self.assertIn(f"**Candidate branch:** `{candidate['branch']}`", work_order)
                self.assertIn("**Candidate scope:** `all`", work_order)
                self.assertIn(f"**Candidate bundle:** `{candidate['bundle_path']}`", work_order)
                self.assertIn(
                    f"**Candidate bundle identity:** `sha256:{candidate['bundle_identity']}`",
                    work_order,
                )
                self.assertIn(
                    "**Work-order path:** `reviews/Feature-review-fixture.md`",
                    work_order,
                )
                self.assertIn("**Work-order mode:** `new`", work_order)
                self.assertIn("**Judgment:** `changes-requested`", work_order)
                self.assertIn("**Pass judgment:** `changes-requested`", work_order)

    def harness_artifacts(self, candidate):
        return [
            f"git-base:{candidate['base']}",
            f"git-head:{candidate['head']}",
            f"path-set-sha256:{candidate['path_digest']}",
            f"candidate-bundle:{candidate['bundle_path']}",
            f"candidate-bundle-sha256:{candidate['bundle_identity']}",
        ]

    def test_materialized_bundle_exports_the_exact_frozen_candidate(self):
        harness = self.harness()
        candidate = harness.freeze()
        bundle = Path(candidate["bundle_path"])
        paths_bytes = "\0".join(candidate["paths"]).encode("utf-8")
        patch_bytes = harness.git_bytes(
            "diff",
            "--binary",
            "--full-index",
            candidate["base"],
            candidate["head"],
        )

        self.assertTrue(bundle.is_dir())
        self.assertFalse(bundle.is_relative_to(harness.repository))
        self.assertEqual(
            paths_bytes,
            (bundle / "paths.nul").read_bytes(),
        )
        self.assertEqual(
            patch_bytes,
            (bundle / "candidate.patch").read_bytes(),
        )
        self.assertEqual("\n", (bundle / "tree" / "src" / "alpha.txt").read_text(encoding="utf-8"))
        identity_bytes = (bundle / "identity.json").read_bytes()
        identity = json.loads(identity_bytes)
        self.assertEqual(
            {
                "base": candidate["base"],
                "branch": candidate["branch"],
                "head": candidate["head"],
                "patch_sha256": hashlib.sha256(patch_bytes).hexdigest(),
                "path_count": candidate["path_count"],
                "path_digest": candidate["path_digest"],
                "paths_sha256": hashlib.sha256(paths_bytes).hexdigest(),
                "scope": candidate["scope"],
                "tree_oid": harness.git(
                    "rev-parse",
                    f"{candidate['head']}^{{tree}}",
                ),
                "work_order": candidate["work_order"],
                "work_order_mode": candidate["work_order_mode"],
            },
            identity,
        )
        self.assertEqual(
            candidate["bundle_identity"],
            hashlib.sha256(identity_bytes).hexdigest(),
        )

        harness.cleanup_bundle(candidate)
        self.assertFalse(bundle.exists())

    def test_lens_cannot_assign_severity_and_invalid_result_falls_back(self):
        harness = self.harness()
        fallback = harness.invalid_severity_result(harness.freeze())

        self.assertEqual("host-fallback", fallback["record_type"])
        self.assertEqual("invalid-result", fallback["reason_code"])
        self.assertEqual("fallback", fallback["parent_transition"])

    def test_parent_rejects_a_valid_envelope_citing_another_candidate(self):
        harness = self.harness()
        fallback = harness.mismatched_artifact_result(harness.freeze())

        self.assertEqual("host-fallback", fallback["record_type"])
        self.assertEqual("invalid-result", fallback["reason_code"])
        self.assertIn("immutable artifacts differ", fallback["detail"])

    def test_moving_head_cancels_obsolete_work_without_rewriting_identity(self):
        harness = self.harness()
        candidate = harness.freeze()
        outcome = harness.move_head_and_cancel(candidate)

        self.assertNotEqual(candidate["head"], outcome["later_head"])
        self.assertEqual(
            f"git-head:{candidate['head']}",
            outcome["dispatch"]["context"]["immutable_artifacts"][1],
        )
        self.assertEqual("host-cancel-request", outcome["request"]["record_type"])
        self.assertEqual("cancelled", outcome["terminal"]["reason_code"])
        self.assertEqual("cancel", outcome["terminal"]["parent_transition"])
        self.assertFalse(Path(outcome["bundle_path"]).exists())

    def test_explicit_review_and_fix_requires_a_new_incremental_watermark(self):
        harness = self.harness()
        reviewed = harness.review()
        addressed = harness.address_and_increment(reviewed)

        self.assertNotEqual(reviewed["candidate"]["head"], addressed["fixing_head"])
        self.assertEqual(["src/alpha.txt"], addressed["first_fixing_paths"])
        self.assertEqual(["tests/test_alpha.txt"], addressed["second_fixing_paths"])
        self.assertIn(f"**Reviewed up to commit:** `{addressed['fixing_head']}`", addressed["final"])
        self.assertIn(f"**Candidate base:** `{reviewed['candidate']['head']}`", addressed["final"])
        self.assertIn(f"**Candidate head:** `{addressed['fixing_head']}`", addressed["final"])
        self.assertIn("- [x] **R1 - HIGH - parent-verified**", addressed["final"])
        self.assertIn("**Judgment:** `approved`", addressed["final"])
        self.assertIn("**Pass judgment:** `changes-requested`", addressed["final"])
        self.assertIn("**Pass judgment:** `approved`", addressed["final"])
        self.assertIn("**Work-order mode:** `append`", addressed["final"])
        self.assertIn("The candidate removes the required alpha token.", addressed["final"])
        self.assertNotIn("- [ ]", addressed["final"])
        self.assertNotIn("- [~]", addressed["final"])

    def test_scoped_and_incremental_candidates_derive_paths_from_their_own_range(self):
        harness = self.harness()
        full = harness.freeze()
        scoped = harness.freeze(scope="src")
        baseline = harness.head
        harness.write("tests/new_case.txt", "new case\n")
        later = harness.commit("later test")
        incremental = harness.freeze(base=baseline, head=later)

        self.assertEqual(["src/alpha.txt", "src/beta.txt"], scoped["paths"])
        self.assertNotEqual(full["path_digest"], scoped["path_digest"])
        self.assertEqual(["tests/new_case.txt"], incremental["paths"])
        self.assertEqual(baseline, incremental["base"])
        self.assertEqual(later, incremental["head"])
        trailing_nul = hashlib.sha256(
            ("\0".join(full["paths"]) + "\0").encode("utf-8")
        ).hexdigest()
        self.assertNotEqual(full["path_digest"], trailing_nul)
        harness.write("src/é.txt", "unicode path\n")
        unicode_head = harness.commit("unicode path")
        unicode_candidate = harness.freeze(base=later, head=unicode_head)
        self.assertEqual(["src/é.txt"], unicode_candidate["paths"])
        self.assertEqual(
            hashlib.sha256("src/é.txt".encode("utf-8")).hexdigest(),
            unicode_candidate["path_digest"],
        )

    def test_parent_finalization_recovers_every_incomplete_parent_field(self):
        harness = self.harness()
        for case in self.fixture["staged_finalization_cases"]:
            with self.subTest(case=case["id"]):
                state = harness.staged_state(**case["overrides"])
                self.assertEqual("parent-finalization", harness.staged_transition(state))
                outcome = harness.finalize_staged(state)
                self.assertEqual(["parent-finalization"], outcome["events"])
                self.assertEqual("complete", outcome["transition"])
                self.assertNotIn("review-area", outcome["events"])

    def test_parent_finalization_requires_security_evidence_before_stamping(self):
        harness = self.harness()
        state = harness.staged_state(
            security_required=True,
            security_watermark=None,
            security_evidence=False,
        )
        blocked = harness.finalize_staged(state)
        self.assertEqual(["security-review"], blocked["events"])
        self.assertEqual("parent-finalization", blocked["transition"])
        self.assertIsNone(blocked["state"]["security_watermark"])
        completed = harness.finalize_staged({**state, "security_evidence": True})
        self.assertEqual("complete", completed["transition"])
        self.assertEqual(state["anchor"], completed["state"]["security_watermark"])

    def test_addressing_requires_final_watermarks(self):
        harness = self.harness()
        state = harness.staged_state()
        self.assertTrue(harness.addressing_ready(state))
        self.assertFalse(harness.addressing_ready({**state, "watermark": None}))
        self.assertFalse(
            harness.addressing_ready({**state, "notes_status": "pending"})
        )
        self.assertFalse(
            harness.addressing_ready({**state, "summary_status": "pending"})
        )
        self.assertFalse(
            harness.addressing_ready(
                {
                    **state,
                    "security_required": True,
                    "security_watermark": None,
                }
            )
        )
        self.assertTrue(
            harness.addressing_ready(
                {
                    **state,
                    "security_required": True,
                    "security_watermark": state["anchor"],
                }
            )
        )

    def test_review_family_has_one_artifact_owner_and_thin_selectors(self):
        lifecycle = authored_skill("review-lifecycle").read_text(encoding="utf-8")
        review = authored_skill("review").read_text(encoding="utf-8")
        incremental = authored_skill("incremental-review").read_text(encoding="utf-8")
        big = authored_skill("big-review").read_text(encoding="utf-8")
        big_all = authored_skill("big-review-all").read_text(encoding="utf-8")
        address = authored_skill("address-review").read_text(encoding="utf-8")
        docs = authored_skill("docs-review").read_text(encoding="utf-8")
        role = (ROOT / ".agents" / "workflows" / "roles" / "review-lens.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("The strong parent is the sole writer", lifecycle)
        self.assertIn("do not add a trailing NUL", lifecycle)
        self.assertIn("one severity vocabulary", lifecycle)
        self.assertIn("one `Pass judgment`", lifecycle)
        self.assertIn("nested `### Findings`", lifecycle)
        self.assertIn("**Candidate branch:**", lifecycle)
        self.assertIn("**Candidate scope:**", lifecycle)
        self.assertIn("**Work-order path:**", lifecycle)
        self.assertIn("**Work-order mode:**", lifecycle)
        self.assertIn("materialize a disposable candidate bundle", lifecycle)
        self.assertIn("parent-finalization", lifecycle)
        self.assertIn("**Parent summary status:**", lifecycle)
        self.assertIn("Use only `reviews/<branch-slug>.md`", review)
        self.assertIn("exported frozen tree, never the live checkout", review)
        self.assertIn("This changes only candidate resolution", incremental)
        self.assertIn("reject it unless it equals that derived canonical path exactly", incremental)
        self.assertIn("This partitions one frozen candidate", big)
        self.assertIn("`parent-finalization` resume state", big)
        self.assertIn("thin unattended driver", big_all)
        self.assertIn("or in `parent-finalization`", big_all)
        self.assertNotIn("reviews/BIG-", big)
        self.assertNotIn("reviews/BIG-", big_all)
        self.assertIn("Never overlap\nwriters", address)
        self.assertIn("Before setting any finding to `[~]`", address)
        self.assertIn("active `Pass judgment` to be non-pending", address)
        self.assertIn("marker must exist and equal the", address)
        self.assertIn("--root <candidate-bundle>/tree", docs)
        self.assertNotIn("--root <checkout>", docs)
        self.assertIn("only from the supplied materialized bundle", role)
        self.assertIn("do not recompute them from a live checkout", role)

    def test_review_family_keeps_one_canonical_body_and_thin_host_entries(self):
        skills = (
            "review",
            "review-lifecycle",
            "incremental-review",
            "big-review",
            "big-review-all",
            "address-review",
            "docs-review",
        )
        for skill in skills:
            canonical = authored_skill(skill)
            plugin_canonical = ROOT / "plugins" / "engineering" / canonical.relative_to(ROOT)
            self.assertEqual(
                canonical.read_text(encoding="utf-8"),
                plugin_canonical.read_text(encoding="utf-8"),
            )
            for host, tree in (("claude", "skills"), ("codex", "codex-skills")):
                with self.subTest(skill=skill, host=host):
                    packaged = (
                        ROOT / "plugins" / "engineering" / tree / skill / "SKILL.md"
                    ).read_text(encoding="utf-8")
                    self.assertEqual(packaged_adapter(ROOT, skill, host), packaged)


if __name__ == "__main__":
    unittest.main()
