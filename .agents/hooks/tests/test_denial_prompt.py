import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).resolve().parents[1] / "denial_prompt.py"


class DenialPromptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.env = dict(os.environ, TMP=self.temp.name, TEMP=self.temp.name, TMPDIR=self.temp.name)

    def run_hook(self, event, command="git merge origin/main", session="s1", **extra):
        payload = {
            "hook_event_name": event,
            "session_id": session,
            "tool_name": "Bash",
            "tool_input": {"command": command},
            **extra,
        }
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=self.env,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)["hookSpecificOutput"] if result.stdout else None

    def records(self):
        return list(Path(self.temp.name).glob("agents-denial-*.json"))

    def test_a_denial_asks_for_a_retry_and_records_the_call(self):
        output = self.run_hook("PermissionDenied")

        self.assertEqual({"hookEventName": "PermissionDenied", "retry": True}, output)
        self.assertEqual(1, len(self.records()))

    def test_retrying_the_denied_call_asks_the_user_once(self):
        self.run_hook("PermissionDenied")

        first = self.run_hook("PreToolUse")
        second = self.run_hook("PreToolUse")

        self.assertEqual("ask", first["permissionDecision"])
        self.assertIsNone(second)
        self.assertEqual([], self.records())

    def test_a_different_call_or_session_is_not_asked(self):
        self.run_hook("PermissionDenied")

        self.assertIsNone(self.run_hook("PreToolUse", command="git status"))
        self.assertIsNone(self.run_hook("PreToolUse", session="s2"))
        self.assertEqual(1, len(self.records()))

    def test_an_expired_record_is_consumed_without_asking(self):
        self.run_hook("PermissionDenied")
        record = self.records()[0]
        record.write_text(json.dumps({"denied_at": 0}), encoding="utf-8")

        self.assertIsNone(self.run_hook("PreToolUse"))
        self.assertEqual([], self.records())

    def test_a_call_that_was_never_denied_is_left_alone(self):
        self.assertIsNone(self.run_hook("PreToolUse"))

    def test_codex_and_unknown_events_are_ignored(self):
        self.assertIsNone(self.run_hook("PermissionDenied", turn_id="t1"))
        self.assertIsNone(self.run_hook("PostToolUse"))
        self.assertEqual([], self.records())


if __name__ == "__main__":
    unittest.main()
