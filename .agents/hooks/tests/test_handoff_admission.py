import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / ".agents/engineering/workflow/handoff/scripts"
sys.path.insert(0, str(SCRIPTS))
from admission import dependency_transition, process_started_at, rank_eligible, registry_owner, validate


class HandoffAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="handoff admission ")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.primary = self.base / "primary"
        self.feature = self.base / "feature"
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.primary)], check=True)
        for key, value in (("user.name", "Admission test"), ("user.email", "admission@example.invalid")):
            subprocess.run(["git", "-C", str(self.primary), "config", key, value], check=True)
        (self.primary / "README.md").write_text("fixture\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.primary), "add", "README.md"], check=True)
        subprocess.run(["git", "-C", str(self.primary), "commit", "-q", "-m", "fixture"], check=True)
        subprocess.run(["git", "-C", str(self.primary), "worktree", "add", "-q", "-b", "repair", str(self.feature)], check=True)
        self.record = self.primary / "BUGS.md"
        self.goal = self.feature / "GOAL.md"
        self.target = self.base / "missing-capability"
        self.evidence = self.base / "read-failure.txt"
        self.evidence.write_text("read failed", encoding="utf-8")
        self.session = "native-session"
        self.prompt = hashlib.sha256(b"called out").hexdigest()
        self.callout = "callout-1"
        self.record_id = "B014"
        self.goal.write_text(
            ("# Repair\\n\\n## Authorization\\n\\nstandards-defect repair\\n\\n"
            "Source owner: engineering/handoff\\n"
            f"Required read capability: {self.target}\\n"
            f"Problem record: {self.record}#{self.record_id}\\n").replace("\\n", "\n"),
            encoding="utf-8",
        )

    def disposition(self, blocker="capability"):
        return {
            "schema_version": 1,
            "record_id": self.record_id,
            "kind": "bug",
            "state": "deferred",
            "callout": {
                "session_id": self.session,
                "callout_id": self.callout,
                "prompt_sha256": self.prompt,
            },
            "source_owner": "engineering/handoff",
            "repair_goal": str(self.goal),
            "disposition": "deferred",
            "reason": "required work cannot proceed",
            "blocked_by": blocker,
            "resolver": "environment owner",
            "resume_condition": "the required capability reports success",
            "next_action": "rerun the admission check",
            "evidence": {
                "kind": "read-failure",
                "path": str(self.evidence),
                "sha256": hashlib.sha256(self.evidence.read_bytes()).hexdigest(),
                "target": str(self.target),
                "operation": "read required capability",
                "error": "missing",
            },
        }

    def write_record(self, value):
        fence = chr(96) * 3
        self.record.write_text(
            ("# Bugs\\n\\n## B014\\n\\n" + fence + "agent-handoff-disposition\\n"
            + json.dumps(value, indent=2)
            + "\\n" + fence + "\\n").replace("\\n", "\n"),
            encoding="utf-8",
        )

    def check(self):
        return validate(str(self.record), self.record_id, self.session, self.prompt, self.callout)

    def test_remote_admission_revalidates_source_kind_and_current_evidence(self):
        self.write_record(self.disposition())
        reference = "https://example.invalid/source/issues/14"
        self.goal.write_text(self.goal.read_text(encoding="utf-8").replace(str(self.record), reference), encoding="utf-8")
        (self.primary / ".problem-records.json").write_text(json.dumps({"schema_version": 1, "provider": "optional:manage"}), encoding="utf-8")
        body = self.record.read_text(encoding="utf-8")
        value = {"record": reference, "kind": "bug", "state": "open", "body": body}
        for host in ("codex", "claude"):
            with self.subTest(host=host), patch("admission.read_record", return_value=value) as read:
                result = validate(reference, self.record_id, self.session, self.prompt, self.callout, str(self.feature), host)
                self.assertTrue(result["valid"], result)
                self.assertEqual(reference, result["record"])
                read.assert_called_once_with(self.primary.resolve(), reference, host)
        self.assertFalse(self.check()["valid"])
        with patch("admission.read_record", return_value={**value, "kind": "mistake"}):
            self.assertFalse(validate(reference, self.record_id, self.session, self.prompt, self.callout, str(self.primary), "codex")["valid"])
        self.target.write_text("recovered", encoding="utf-8")
        with patch("admission.read_record", return_value=value):
            self.assertFalse(validate(reference, self.record_id, self.session, self.prompt, self.callout, str(self.primary), "codex")["valid"])
        self.assertFalse(validate(reference, self.record_id, self.session, self.prompt, self.callout)["valid"])

    def test_shipped_helper_precedes_unrelated_pythonpath_modules(self):
        shadow = self.base / "shadow"
        shadow.mkdir()
        (shadow / "problem_records.py").write_text("raise RuntimeError('unrelated module')", encoding="utf-8")
        result = subprocess.run([sys.executable, "-B", str(SCRIPTS / "admission.py"), "--help"], capture_output=True,
                                text=True, encoding="utf-8", timeout=15, env=dict(os.environ, PYTHONPATH=str(shadow)))
        self.assertEqual(0, result.returncode, result.stderr)

    def test_missing_read_capability_admits_a_linked_deferred_record(self):
        self.write_record(self.disposition())
        self.assertTrue(self.check()["valid"])

    def test_record_must_be_in_the_source_primary_register(self):
        self.write_record(self.disposition())
        self.assertTrue(self.check()["valid"])
        for record in (self.feature / "BUGS.md", self.base / "temporary" / "BUGS.md", self.primary / "area" / "BUGS.md"):
            with self.subTest(record=record):
                record.parent.mkdir(parents=True, exist_ok=True)
                original = self.record
                self.record = record
                self.goal.write_text(
                    self.goal.read_text(encoding="utf-8").replace(str(original), str(record)),
                    encoding="utf-8",
                )
                self.write_record(self.disposition())
                self.assertFalse(self.check()["valid"])
                self.goal.write_text(
                    self.goal.read_text(encoding="utf-8").replace(str(record), str(original)),
                    encoding="utf-8",
                )
                self.record = original

    def test_area_debt_register_must_be_a_tracked_primary_register(self):
        original = self.record
        record = self.primary / "area" / "TECH_DEBT.md"
        record.parent.mkdir()
        record.write_text("# Technical debt\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.primary), "add", "area/TECH_DEBT.md"], check=True)
        subprocess.run(["git", "-C", str(self.primary), "commit", "-q", "-m", "tracked debt register"], check=True)
        self.record = record
        self.goal.write_text(
            self.goal.read_text(encoding="utf-8").replace(str(original), str(record)),
            encoding="utf-8",
        )
        value = self.disposition()
        value["kind"] = "debt"
        self.write_record(value)
        self.assertTrue(self.check()["valid"])
        fabricated = self.primary / "fabricated" / "TECH_DEBT.md"
        fabricated.parent.mkdir()
        self.goal.write_text(
            self.goal.read_text(encoding="utf-8").replace(str(record), str(fabricated)),
            encoding="utf-8",
        )
        self.record = fabricated
        self.write_record(value)
        self.assertFalse(self.check()["valid"])

    def test_stale_unrelated_and_duplicate_records_fail_closed(self):
        for field, value in (
            ("callout_id", "old"),
            ("prompt_sha256", "old"),
            ("session_id", "other-session"),
        ):
            with self.subTest(field=field):
                disposition = self.disposition()
                disposition["callout"][field] = value
                self.write_record(disposition)
                self.assertFalse(self.check()["valid"])
        other = self.disposition()
        other["record_id"] = "B015"
        self.write_record(other)
        self.assertFalse(self.check()["valid"])
        value = self.disposition()
        fence = chr(96) * 3
        self.record.write_text(
            fence + "agent-handoff-disposition\\n" + json.dumps(value) + "\\n" + fence + "\\n"
            + fence + "agent-handoff-disposition\\n" + json.dumps(value) + "\\n" + fence + "\\n",
            encoding="utf-8",
        )
        self.assertFalse(self.check()["valid"])

    def test_forged_hash_and_recovered_read_target_fail_closed(self):
        self.write_record(self.disposition())
        self.evidence.write_text("forged", encoding="utf-8")
        self.assertFalse(self.check()["valid"])
        self.evidence.write_text("read failed", encoding="utf-8")
        self.target.write_text("available", encoding="utf-8")
        self.assertFalse(self.check()["valid"])

    def test_evidence_requires_declared_prerequisite_source_owner_and_authorization(self):
        self.write_record(self.disposition())
        self.assertTrue(self.check()["valid"])
        self.goal.write_text(
            self.goal.read_text(encoding="utf-8").replace(str(self.target), str(self.base / "unrelated")),
            encoding="utf-8",
        )
        self.assertFalse(self.check()["valid"])
        self.goal.write_text(
            self.goal.read_text(encoding="utf-8").replace(str(self.base / "unrelated"), str(self.target)),
            encoding="utf-8",
        )
        self.goal.write_text(
            self.goal.read_text(encoding="utf-8").replace("engineering/handoff", "engineering/other"),
            encoding="utf-8",
        )
        self.assertFalse(self.check()["valid"])
        self.goal.write_text(
            self.goal.read_text(encoding="utf-8").replace("engineering/other", "engineering/handoff"),
            encoding="utf-8",
        )
        self.goal.write_text(
            self.goal.read_text(encoding="utf-8").replace(
                "standards-defect repair", "review product code"
            ) + "\n## History\n\nstandards-defect repair\n",
            encoding="utf-8",
        )
        self.assertFalse(self.check()["valid"])

    def test_declared_executable_and_dependency_prerequisites_admit_current_evidence(self):
        executable = "missing-handoff-executable"
        value = self.disposition()
        value["evidence"] = {
            "kind": "executable-failure",
            "path": str(self.evidence),
            "sha256": hashlib.sha256(self.evidence.read_bytes()).hexdigest(),
            "executable": executable,
        }
        self.goal.write_text(
            self.goal.read_text(encoding="utf-8").replace(
                f"Required read capability: {self.target}", f"Required executable: {executable}"
            ),
            encoding="utf-8",
        )
        self.write_record(value)
        self.assertTrue(self.check()["valid"])
        required = "0" * 64
        value["blocked_by"] = "dependency"
        value["evidence"] = {
            "kind": "dependency-artifact",
            "path": str(self.evidence),
            "sha256": hashlib.sha256(self.evidence.read_bytes()).hexdigest(),
            "artifact_id": "handoff-policy",
            "required_sha256": required,
        }
        self.goal.write_text(
            self.goal.read_text(encoding="utf-8").replace(
                f"Required executable: {executable}", f"Required dependency: handoff-policy sha256:{required}"
            ),
            encoding="utf-8",
        )
        self.write_record(value)
        self.assertTrue(self.check()["valid"])

    def test_wrong_blocker_evidence_kind_fails_closed(self):
        value = self.disposition("dependency")
        self.write_record(value)
        self.assertFalse(self.check()["valid"])

    def test_ranking_filters_before_priority_and_dependency_transitions_once(self):
        ranked = rank_eligible([
            {"record_id": "B1", "eligible": False, "priority": "P0", "unblocks": 9, "observed_at": "2026-10-01"},
            {"record_id": "B2", "eligible": True, "priority": "P2", "unblocks": 4, "observed_at": "2026-10-02"},
            {"record_id": "B3", "eligible": True, "priority": "P1", "unblocks": 1, "observed_at": "2026-10-03"},
        ])
        self.assertEqual(["B3", "B2"], [item["record_id"] for item in ranked])
        self.assertTrue(dependency_transition("old", "new", "old"))
        self.assertFalse(dependency_transition("old", "old", "old"))
        self.assertFalse(dependency_transition("old", "new", "new"))

    def test_current_process_start_is_observable(self):
        self.assertIsNotNone(process_started_at(os.getpid()))

    def test_registry_owner_matches_a_session_anywhere_inside_its_worktree(self):
        registry = self.base / "state" / "cli-sessions"
        registry.mkdir(parents=True)
        owner = {"session_id": "owner-session", "harness": "claude", "worktree": str(self.feature)}
        sibling = self.base / "feature-sibling"
        sibling.mkdir()
        entry = registry / "owner-session.json"
        cases = ((self.feature, True), (self.feature / "tests", True), (self.primary, False), (sibling, False))
        with patch.dict(os.environ, {"AGENT_STATE_DIRECTORY": str(self.base / "state")}):
            for cwd, matched in cases:
                with self.subTest(cwd=cwd.name):
                    entry.write_text(json.dumps({
                        "session_id": "owner-session", "host": "claude", "cwd": str(cwd),
                        "pid": os.getpid(), "pid_started_at": process_started_at(os.getpid()),
                    }), encoding="utf-8")
                    observed, path = registry_owner(owner)
                    self.assertEqual(matched, path == entry)

    def test_registered_existing_owner_and_capacity_use_current_process_identity(self):
        state = self.base / "state"
        registry = state / "cli-sessions"
        registry.mkdir(parents=True)
        old_state = os.environ.get("AGENT_STATE_DIRECTORY")
        self.addCleanup(
            lambda: os.environ.__setitem__("AGENT_STATE_DIRECTORY", old_state)
            if old_state is not None else os.environ.pop("AGENT_STATE_DIRECTORY", None)
        )
        os.environ["AGENT_STATE_DIRECTORY"] = str(state)
        owner_goal = self.goal
        owner_goal.write_text(
            self.goal.read_text(encoding="utf-8") + "Native owner: owner-session\n",
            encoding="utf-8",
        )
        owner = {
            "session_id": "owner-session",
            "harness": "codex",
            "worktree": str(self.feature),
            "goal": str(owner_goal),
        }
        registry_path = registry / "owner.json"
        registry_path.write_text(json.dumps({
            "session_id": "owner-session", "host": "codex", "cwd": str(self.feature),
            "pid": os.getpid(), "pid_started_at": process_started_at(os.getpid()),
            "started_at": "2026-10-11T20:00:00Z",
        }), encoding="utf-8")
        value = self.disposition()
        value.update(
            state="in-progress", disposition="existing-owner", owner=owner,
            evidence={
                "kind": "native-observer", "path": str(registry_path),
                "sha256": hashlib.sha256(registry_path.read_bytes()).hexdigest(),
                "registry_session_id": "owner-session",
            },
        )
        value.pop("blocked_by")
        self.write_record(value)
        self.assertTrue(self.check()["valid"])
        value["evidence"] = None
        self.write_record(value)
        self.assertFalse(self.check()["valid"])
        value["evidence"] = self.disposition()["evidence"]
        self.write_record(value)
        self.assertFalse(self.check()["valid"])
        value["evidence"] = {
            "kind": "native-observer", "path": str(registry_path),
            "sha256": hashlib.sha256(registry_path.read_bytes()).hexdigest(),
            "registry_session_id": "owner-session",
        }
        value.update(state="deferred", disposition="deferred", blocked_by="capacity", occupied_owners=[owner])
        self.goal.write_text(
            self.goal.read_text(encoding="utf-8") + "Writer budget: 1\n", encoding="utf-8"
        )
        self.write_record(value)
        self.assertTrue(self.check()["valid"])
        value["occupied_owners"] = [owner, owner]
        self.write_record(value)
        self.assertFalse(self.check()["valid"])
        unrelated_goal = self.base / "unrelated-goal.md"
        unrelated_goal.write_text("Native owner: unrelated-session\n", encoding="utf-8")
        unrelated = {
            "session_id": "unrelated-session",
            "harness": "codex",
            "worktree": str(self.feature),
            "goal": str(unrelated_goal),
        }
        unrelated_registry = registry / "unrelated.json"
        unrelated_registry.write_text(json.dumps({
            "session_id": "unrelated-session", "host": "codex", "cwd": str(self.feature),
            "pid": os.getpid(), "pid_started_at": process_started_at(os.getpid()),
            "started_at": "2026-10-11T20:00:00Z",
        }), encoding="utf-8")
        self.goal.write_text(
            self.goal.read_text(encoding="utf-8").replace("Writer budget: 1", "Writer budget: 2"),
            encoding="utf-8",
        )
        value["occupied_owners"] = [owner, unrelated]
        self.write_record(value)
        self.assertFalse(self.check()["valid"])

    def test_conflict_requires_an_absolute_asset_declared_by_both_goals(self):
        state = self.base / "state"
        registry = state / "cli-sessions"
        registry.mkdir(parents=True)
        old_state = os.environ.get("AGENT_STATE_DIRECTORY")
        self.addCleanup(
            lambda: os.environ.__setitem__("AGENT_STATE_DIRECTORY", old_state)
            if old_state is not None else os.environ.pop("AGENT_STATE_DIRECTORY", None)
        )
        os.environ["AGENT_STATE_DIRECTORY"] = str(state)
        shared = str((self.base / "shared.py").resolve())
        owner_goal = self.base / "conflict-goal.md"
        owner_goal.write_text(
            f"Native owner: conflict-session\nProblem record: {self.record}#{self.record_id}\n"
            f"Owned paths: {shared}\n",
            encoding="utf-8",
        )
        self.goal.write_text(
            self.goal.read_text(encoding="utf-8") + f"Owned paths: {shared}\n",
            encoding="utf-8",
        )
        owner = {
            "session_id": "conflict-session",
            "harness": "codex",
            "worktree": str(self.feature),
            "goal": str(owner_goal),
        }
        registry_path = registry / "conflict.json"
        registry_path.write_text(json.dumps({
            "session_id": "conflict-session", "host": "codex", "cwd": str(self.feature),
            "pid": os.getpid(), "pid_started_at": process_started_at(os.getpid()),
            "started_at": "2026-10-11T20:00:00Z",
        }), encoding="utf-8")
        value = self.disposition("conflict")
        value.update(
            owner=owner,
            evidence={
                "kind": "native-observer", "path": str(registry_path),
                "sha256": hashlib.sha256(registry_path.read_bytes()).hexdigest(),
                "registry_session_id": "conflict-session",
            },
        )
        self.write_record(value)
        self.assertTrue(self.check()["valid"])
        self.goal.write_text(
            self.goal.read_text(encoding="utf-8").replace(shared, str((self.base / "unrelated.py").resolve())),
            encoding="utf-8",
        )
        self.assertFalse(self.check()["valid"])
        self.goal.write_text(self.goal.read_text(encoding="utf-8").replace(
            str((self.base / "unrelated.py").resolve()), shared
        ), encoding="utf-8")
        owner_goal.write_text(
            owner_goal.read_text(encoding="utf-8").replace(shared, str((self.base / "other.py").resolve())),
            encoding="utf-8",
        )
        self.assertFalse(self.check()["valid"])


if __name__ == "__main__":
    unittest.main()
