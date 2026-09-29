import codecs
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / '.agents/machine/scripts'
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('codex_terminal_profile', SCRIPTS / 'codex_terminal_profile.py')
PROFILE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROFILE)


class CodexTerminalProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='codex terminal profile ')
        self.addCleanup(self.temp.cleanup)
        self.documents = Path(self.temp.name) / 'Documents'
        self.paths = PROFILE.profile_paths(self.documents)
        prior = os.environ.pop(PROFILE.OPT_OUT_ENV, None)
        if prior is not None:
            self.addCleanup(os.environ.__setitem__, PROFILE.OPT_OUT_ENV, prior)

    def test_writes_both_editions_once(self):
        self.assertEqual(PROFILE.main(['--documents', str(self.documents)]), 0)
        for path in self.paths:
            self.assertEqual(path.read_bytes().decode('utf-8'), PROFILE.BLOCK + '\r\n')
        self.assertEqual(PROFILE.main(['--documents', str(self.documents)]), 0)

    def test_existing_profile_and_encoding_are_preserved(self):
        self.paths[0].parent.mkdir(parents=True)
        existing = '# existing\r\nfunction codex { "old" }\r\n'
        self.paths[0].write_bytes(codecs.BOM_UTF8 + existing.encode('utf-8'))
        PROFILE.main(['--documents', str(self.documents)])
        raw = self.paths[0].read_bytes()
        self.assertTrue(raw.startswith(codecs.BOM_UTF8))
        text = raw[len(codecs.BOM_UTF8):].decode('utf-8')
        self.assertTrue(text.startswith(existing.rstrip()))
        self.assertTrue(text.rstrip().endswith(PROFILE.END))

    def test_malformed_block_is_left_unchanged(self):
        self.paths[0].parent.mkdir(parents=True)
        original = f'{PROFILE.START}\nunterminated\n'
        self.paths[0].write_text(original, encoding='utf-8')
        self.assertEqual(PROFILE.main(['--documents', str(self.documents)]), 0)
        self.assertEqual(self.paths[0].read_text(encoding='utf-8'), original)

    def test_opt_out_writes_nothing(self):
        os.environ[PROFILE.OPT_OUT_ENV] = 'off'
        self.addCleanup(os.environ.pop, PROFILE.OPT_OUT_ENV, None)
        self.assertEqual(PROFILE.main(['--documents', str(self.documents)]), 0)
        self.assertFalse(any(path.exists() for path in self.paths))


if __name__ == '__main__':
    unittest.main()
