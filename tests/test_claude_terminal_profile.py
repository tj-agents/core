"""Synthetic Documents folders only; no real PowerShell profile is read or written."""
import codecs
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'claude_terminal_profile', ROOT / '.agents/machine/scripts/claude_terminal_profile.py'
)
PROFILE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROFILE
SPEC.loader.exec_module(PROFILE)


class TerminalProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='claude terminal profile ')
        self.addCleanup(self.temp.cleanup)
        self.documents = Path(self.temp.name) / 'Documents'
        self.paths = PROFILE.profile_paths(self.documents)
        previous = os.environ.pop(PROFILE.OPT_OUT_ENV, None)
        if previous is not None:
            self.addCleanup(os.environ.__setitem__, PROFILE.OPT_OUT_ENV, previous)

    def run_hook(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = PROFILE.main(['--documents', str(self.documents)])
        return code, out.getvalue()

    def test_both_editions_get_the_block_once(self):
        code, output = self.run_hook()
        self.assertEqual(code, 0)
        self.assertIn('new PowerShell terminals now refresh Claude plugins', output)
        for path in self.paths:
            self.assertEqual(path.read_bytes().decode('utf-8'), PROFILE.BLOCK + '\r\n')
        self.assertEqual(self.run_hook(), (0, ''))

    def test_existing_profile_is_kept_and_the_block_loads_after_it(self):
        self.paths[0].parent.mkdir(parents=True)
        existing = '# >>> base-agents >>>\r\n. old-checkout\r\n# <<< base-agents <<<\r\n'
        self.paths[0].write_bytes(codecs.BOM_UTF8 + existing.encode('utf-8'))
        self.run_hook()
        raw = self.paths[0].read_bytes()
        self.assertTrue(raw.startswith(codecs.BOM_UTF8))
        text = raw[len(codecs.BOM_UTF8):].decode('utf-8')
        self.assertTrue(text.startswith(existing.rstrip()))
        self.assertTrue(text.rstrip().endswith(PROFILE.END))

    def test_a_changed_block_is_replaced_in_place(self):
        self.paths[1].parent.mkdir(parents=True)
        stale = f'before\n{PROFILE.START}\n. old-launcher\n{PROFILE.END}\nafter\n'
        self.paths[1].write_bytes(stale.encode('utf-8'))
        self.run_hook()
        text = self.paths[1].read_bytes().decode('utf-8')
        self.assertEqual(text, 'before\n' + PROFILE.BLOCK + '\nafter\n')
        self.assertNotIn('old-launcher', text)

    def test_a_malformed_block_is_reported_and_left_alone(self):
        self.paths[0].parent.mkdir(parents=True)
        self.paths[0].write_text(f'{PROFILE.START}\nunterminated\n', encoding='utf-8')
        code, output = self.run_hook()
        self.assertEqual(code, 0)
        self.assertIn('was not installed', output)
        self.assertEqual(self.paths[0].read_text(encoding='utf-8'), f'{PROFILE.START}\nunterminated\n')

    def test_utf16_and_ansi_profiles_keep_their_encoding(self):
        for path in self.paths:
            path.parent.mkdir(parents=True)
        self.paths[0].write_bytes('Write-Host "héllo"\r\n'.encode('utf-16'))
        self.paths[1].write_bytes(b'Write-Host "caf\xe9"\r\n')
        code, output = self.run_hook()
        self.assertEqual(code, 0)
        self.assertNotIn('was not installed', output)
        first = self.paths[0].read_bytes()
        self.assertTrue(first.startswith(codecs.BOM_UTF16_LE))
        self.assertIn(PROFILE.BLOCK, first.decode('utf-16'))
        second = self.paths[1].read_bytes()
        self.assertTrue(second.startswith(b'Write-Host "caf\xe9"'))
        self.assertIn(PROFILE.BLOCK.encode('ascii'), second)

    def test_one_unusable_profile_does_not_block_the_other(self):
        self.paths[0].parent.mkdir(parents=True)
        self.paths[0].write_bytes(f'{PROFILE.END}\r\n{PROFILE.START}\r\n'.encode('utf-8'))
        code, output = self.run_hook()
        self.assertEqual(code, 0)
        self.assertIn(f'was not installed in {self.paths[0]}', output)
        self.assertEqual(self.paths[1].read_bytes().decode('utf-8'), PROFILE.BLOCK + '\r\n')

    def test_opt_out_writes_nothing(self):
        os.environ[PROFILE.OPT_OUT_ENV] = 'off'
        self.addCleanup(os.environ.pop, PROFILE.OPT_OUT_ENV, None)
        self.assertEqual(self.run_hook(), (0, ''))
        self.assertFalse(any(path.exists() for path in self.paths))


if __name__ == '__main__':
    unittest.main()
