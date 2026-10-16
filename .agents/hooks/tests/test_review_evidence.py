import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".agents" / "workflows"))
sys.path.insert(0, str(ROOT / ".agents" / "hooks"))
import review_evidence as evidence
import workflow_ops as ops
import auto_merge
import merge_review_gate as gate


HEAD = "a" * 40
BRANCH = "Fix/PrivateReview"


class PrivateReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / ".git").mkdir()
        (self.root / ".agents").mkdir()
        (self.root / ".agents" / "merge-gate.json").write_text('{"security_paths": []}', encoding="utf-8")
        self.path = evidence.prepare_path(self.root, BRANCH)
        self.body = (
            "**Review status:** `complete`\n**Judgment:** `approved`\n"
            f"**Reviewed up to commit:** `{HEAD}`\n"
        )
        self.path.write_text(self.body, encoding="utf-8")
        self.record()

    def record(self):
        return evidence.record(self.root, BRANCH, HEAD, "b" * 64, self.path, self.path.read_bytes())

    def test_private_body_is_outside_authored_tree_and_recovers_without_a_bundle(self):
        self.assertIn("agent-workflow", self.path.parts)
        self.assertTrue(self.path.is_relative_to(self.root / ".git"))
        result = evidence.resolve(self.root, BRANCH, HEAD)
        self.assertTrue(result["private"])
        self.assertEqual(self.body.splitlines(), result["body"].splitlines())
        self.assertEqual(self.path, evidence.work_order_path(self.root, BRANCH))

    def test_changed_body_missing_receipt_and_stale_head_fail_closed(self):
        legacy = evidence.legacy_path(self.root, BRANCH)
        legacy.parent.mkdir()
        legacy.write_text(self.body, encoding="utf-8")
        self.path.write_text(self.body + "- [ ] changed\n", encoding="utf-8")
        with self.assertRaisesRegex(evidence.ReviewEvidenceError, "changed"):
            evidence.resolve(self.root, BRANCH, HEAD)
        self.path.write_text(self.body, encoding="utf-8")
        with self.assertRaisesRegex(evidence.ReviewEvidenceError, "stale"):
            evidence.resolve(self.root, BRANCH, "c" * 40)
        evidence.private_paths(self.root, BRANCH)["receipt"].unlink()
        with self.assertRaisesRegex(evidence.ReviewEvidenceError, "missing"):
            evidence.resolve(self.root, BRANCH, HEAD)

    def test_copied_proof_rejects_other_checkout_and_branch(self):
        for root, branch in ((self.root / "other", BRANCH), (self.root, "Fix-PrivateReview")):
            with self.subTest(root=root, branch=branch):
                (root / ".git").mkdir(parents=True, exist_ok=True)
                target = evidence.prepare_path(root, branch)
                target.write_bytes(self.path.read_bytes())
                shutil.copyfile(evidence.private_paths(self.root, BRANCH)["receipt"],
                                evidence.private_paths(root, branch)["receipt"])
                with self.assertRaisesRegex(evidence.ReviewEvidenceError, "another"):
                    evidence.resolve(root, branch, HEAD)

    def test_malformed_receipt_and_descriptor_identity_are_rejected(self):
        receipt = evidence.private_paths(self.root, BRANCH)["receipt"]
        proof = json.loads(receipt.read_text(encoding="utf-8"))
        for value in ([], {**proof, "extra": True}, {**proof, "descriptor_id": "invalid"}):
            with self.subTest(value=value):
                receipt.write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaises(evidence.ReviewEvidenceError):
                    evidence.resolve(self.root, BRANCH, HEAD)

    def test_receipt_hashes_validated_bytes_even_if_body_changes_before_publication(self):
        raw = self.path.read_bytes()
        self.path.write_text(self.body + "- [ ] raced\n", encoding="utf-8")
        evidence.record(self.root, BRANCH, HEAD, "b" * 64, self.path, raw)
        with self.assertRaisesRegex(evidence.ReviewEvidenceError, "changed"):
            evidence.resolve(self.root, BRANCH, HEAD)

    def test_staged_promotion_preserves_the_body_and_retires_private_proof(self):
        path = evidence.prepare_path(self.root, BRANCH, durable=True)
        self.assertEqual(evidence.legacy_path(self.root, BRANCH), path)
        self.assertEqual(self.body, path.read_text(encoding="utf-8"))
        self.assertFalse(self.path.exists())
        self.assertFalse(evidence.private_paths(self.root, BRANCH)["receipt"].exists())
        with patch.object(evidence, "git_text", side_effect=subprocess.SubprocessError()):
            self.assertFalse(evidence.resolve(self.root, BRANCH, HEAD)["private"])

    def test_redirected_body_is_rejected(self):
        outside = self.root / "outside.md"
        outside.write_text(self.body, encoding="utf-8")
        self.path.unlink()
        try:
            self.path.symlink_to(outside)
        except OSError:
            self.skipTest("symlink creation is unavailable")
        with self.assertRaisesRegex(evidence.ReviewEvidenceError, "redirected"):
            evidence.resolve(self.root, BRANCH, HEAD)

    def test_binding_and_auto_merge_consume_identical_private_evidence(self):
        binding = {"branch": BRANCH, "remote_head_sha": HEAD}
        with patch.object(ops, "resolved_commit", return_value=HEAD):
            self.assertEqual(HEAD, ops.review_binding(self.root, BRANCH, HEAD)["reviewed_sha"])
        auto_merge.current_review(self.root, binding, [])
        self.path.write_text(self.body + "- [ ] changed\n", encoding="utf-8")
        with patch.object(ops, "resolved_commit", return_value=HEAD):
            self.assertIsNone(ops.review_binding(self.root, BRANCH, HEAD)["reviewed_sha"])
        with self.assertRaisesRegex(auto_merge.AutoMergeError, "changed"):
            auto_merge.current_review(self.root, binding, [])

    def test_private_evidence_preserves_finding_completion_and_security_gates(self):
        binding = {"branch": BRANCH, "remote_head_sha": HEAD}
        for body, paths, message in (
            (self.body + "- [ ] finding\n", [], "unresolved"),
            (self.body.replace("`complete`", "`in-progress`"), [], "incomplete"),
            (self.body, ["authorization/token.py"], "security"),
        ):
            with self.subTest(message=message):
                self.path.write_text(body, encoding="utf-8")
                self.record()
                with self.assertRaisesRegex(auto_merge.AutoMergeError, message):
                    auto_merge.current_review(self.root, binding, paths)

    def test_merge_hook_accepts_private_proof_and_blocks_edited_body(self):
        payload = {"tool_name": "Bash", "cwd": str(self.root), "tool_input": {"command": "gh pr merge --merge"}}

        def git(*args):
            if args == ("rev-parse", "--show-toplevel"):
                return str(self.root)
            if args == ("rev-parse", "--abbrev-ref", "HEAD"):
                return BRANCH
            return HEAD

        for edited, expected in ((False, 0), (True, 2)):
            if edited:
                self.path.write_text(self.body + "changed\n", encoding="utf-8")
            with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), \
                    patch.object(gate, "git", side_effect=git), \
                    patch.object(gate, "claim_invocation", return_value=True), \
                    patch.object(gate, "changed_against_main", return_value=[]), \
                    patch.object(gate, "grant_if_trusted"), \
                    self.assertRaises(SystemExit) as result:
                gate.main()
            self.assertEqual(expected, result.exception.code)

    def test_work_item_findings_include_in_progress_private_body(self):
        self.path.write_text(self.body + "- [~] **R1 — HIGH**\n", encoding="utf-8")
        with patch.object(ops.workflow_runtime, "_read_only_git", return_value=BRANCH):
            findings = ops.workflow_runtime._open_review_findings(self.root, [])
        self.assertEqual([f"{self.path}#R1"], findings)

    def test_parent_completion_validates_descriptor_head_branch_and_canonical_path(self):
        descriptor = {"head": HEAD, "branch": BRANCH, "descriptor_id": "b" * 64, "paths": ["src/value.py"]}
        with patch.object(ops, "load_descriptor", return_value=descriptor), \
                patch.object(ops, "git", return_value=BRANCH):
            result = ops.review_record(self.root, "completion", "descriptor.json", str(self.path))
            self.assertTrue(result["private"])
            with self.assertRaisesRegex(ops.WorkflowOperationError, "canonical"):
                ops.review_record(self.root, "completion", "descriptor.json", str(self.root / "other.md"))
            self.path.write_text(self.body.replace(HEAD, "c" * 40), encoding="utf-8")
            with self.assertRaisesRegex(ops.WorkflowOperationError, "frozen"):
                ops.review_record(self.root, "completion", "descriptor.json", str(self.path))
        with patch.object(ops, "load_descriptor", return_value=descriptor), \
                patch.object(ops, "git", return_value="Fix/Other"):
            with self.assertRaisesRegex(ops.WorkflowOperationError, "branch"):
                ops.review_record(self.root, "completion", "descriptor.json", str(self.path))

    def test_parent_completion_rejects_incomplete_and_invalid_host_coverage(self):
        descriptor = {"head": HEAD, "branch": BRANCH, "descriptor_id": "b" * 64, "paths": [".agents/workflows/runtime.py"]}
        with patch.object(ops, "load_descriptor", return_value=descriptor), \
                patch.object(ops, "git", return_value=BRANCH):
            with self.assertRaisesRegex(ops.WorkflowOperationError, "host coverage"):
                ops.review_record(self.root, "completion", "descriptor.json", str(self.path))
            self.path.write_text(self.body.replace("`complete`", "`in-progress`"), encoding="utf-8")
            with self.assertRaisesRegex(ops.WorkflowOperationError, "incomplete"):
                ops.review_record(self.root, "completion", "descriptor.json", str(self.path))


class LinkedWorktreeTests(unittest.TestCase):
    def test_linked_checkouts_use_common_git_state_with_distinct_identities(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve() / "repo"
            linked = root.parent / "linked"
            def git(*args):
                return evidence.git_text(root, *args)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            git("-c", "user.email=test@example.test", "-c", "user.name=Fixture", "commit", "--allow-empty", "-qm", "base")
            git("worktree", "add", "-qb", "Fix/Linked", str(linked))
            primary = evidence.private_paths(root, BRANCH)
            other = evidence.private_paths(linked, "Fix/Linked")
            self.assertEqual(primary["identity"]["repository"], other["identity"]["repository"])
            self.assertNotEqual(primary["body"], other["body"])
            self.assertTrue(other["body"].is_relative_to(root / ".git"))
            base = git("rev-parse", "HEAD")
            git("remote", "add", "origin", "https://github.com/example/private-proof.git")
            git("update-ref", "refs/remotes/origin/main", base)
            (linked / "value.txt").write_text("candidate\n", encoding="utf-8")
            evidence.git_text(linked, "add", "value.txt")
            evidence.git_text(linked, "-c", "user.email=test@example.test", "-c", "user.name=Fixture", "commit", "-qm", "candidate")
            descriptor = ops.review_prepare(linked, "private", "origin/main", "HEAD", False)
            bundle = Path(descriptor["bundle"]["directory"])
            self.assertTrue(bundle.resolve().is_relative_to((Path(tempfile.gettempdir()) / "review").resolve()))
            self.addCleanup(shutil.rmtree, bundle)
            path = evidence.prepare_path(linked, "Fix/Linked")
            path.write_text(
                "**Review status:** `complete`\n**Judgment:** `approved`\n"
                f"**Reviewed up to commit:** `{descriptor['head']}`\n", encoding="utf-8",
            )
            recorded = ops.review_record(linked, "private", descriptor["artifact"], str(path))
            self.assertTrue(recorded["private"])
            self.assertEqual(descriptor["head"], ops.review_binding(linked, "Fix/Linked", descriptor["head"])["reviewed_sha"])


if __name__ == "__main__":
    unittest.main()
