"""Synthetic transcripts only; no normal-profile history access."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('history', ROOT / '.agents/machine/scripts/history.py')
HISTORY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HISTORY)


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic history ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cwd = self.root / 'project with spaces'
        self.cwd.mkdir()

    def write(self, relative, events):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('\n'.join(json.dumps(e) for e in events) + '\npartial{', encoding='utf-8')
        return path

    def test_codex_metadata_messages_and_resume(self):
        self.write('codex/2026/rollout.jsonl', [
            dict(type='session_meta', payload=dict(id='codex-id', cwd=str(self.cwd), source='cli', git={'branch':'feature/test'})),
            dict(type='response_item', payload=dict(type='message', role='user', content=[dict(type='input_text', text='Discuss a.b')]))])
        self.write('codex/2026/worker.jsonl', [
            dict(type='session_meta', payload=dict(id='worker', cwd=str(self.cwd), source={'subagent':{}})),
            dict(type='response_item', payload=dict(type='message', role='user', content='worker data'))])
        result = HISTORY.query(self.root / 'codex', 'codex', cwd=self.cwd)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['resume'], 'codex resume codex-id')
        self.assertEqual(result[0]['branch'], 'feature/test')
        self.assertEqual(HISTORY.query(self.root / 'codex', 'codex', pattern='a.b')[0]['hits'], 1)
        self.assertEqual(HISTORY.query(self.root / 'codex', 'codex', pattern='a.b', cwd=self.root), [])

    def test_claude_format_and_literal_search(self):
        self.write('claude/project/session-id.jsonl', [
            dict(type='user', sessionId='session-id', cwd=str(self.cwd), message={'content':'Discuss axb'}),
            dict(type='assistant', message={'content':[dict(type='text', text='answer')]}),
            dict(type='user', isSidechain=True, message={'content':'a.b hidden'})])
        self.write('claude/project/subagents/ignored.jsonl', [dict(type='user', message={'content':'a.b'})])
        self.assertEqual(HISTORY.query(self.root / 'claude', 'claude', pattern='a.b'), [])
        result = HISTORY.query(self.root / 'claude', 'claude', pattern='a.b', regex=True, show_lines=True)
        self.assertEqual(result[0]['resume'], 'claude --resume session-id')
        self.assertEqual(result[0]['matches'][0]['text'], 'Discuss axb')

    def test_packaged_cli_missing_root_and_invalid_pattern_are_clear(self):
        package = self.root / 'isolated package'
        shutil.copytree(ROOT / 'plugins/machine', package)
        script = package / 'resources/machine/scripts/history.py'
        result = subprocess.run([sys.executable, '-B', str(script), 'recent', '--host', 'codex',
                                 '--history-root', str(self.root / 'missing')], cwd=self.cwd,
                                text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('No codex history directory', result.stderr)
        with self.assertRaisesRegex(ValueError, 'positive'):
            HISTORY.query(self.root, 'codex', count=0)


if __name__ == '__main__':
    unittest.main()
