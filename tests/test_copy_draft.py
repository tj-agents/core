"""copy_draft.py: pure text transforms, POSIX backend selection/argv, and (Windows-only) a real ctypes round trip.

Never writes to this machine's real clipboard: this machine has a live Wayland session, so the POSIX
backend tests inject a fake `run`/`which`/`environ` rather than calling wl-copy/wl-paste for real.
"""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / '.agents/machine/utility/clip/scripts/copy_draft.py'
SPEC = importlib.util.spec_from_file_location('copy_draft', SCRIPT)
COPY_DRAFT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = COPY_DRAFT
SPEC.loader.exec_module(COPY_DRAFT)


class NormaliseDraftTests(unittest.TestCase):
    def test_crlf_becomes_lf(self):
        self.assertEqual(COPY_DRAFT.normalise_draft('a\r\nb\r\n'), 'a\nb')

    def test_trailing_whitespace_is_trimmed_from_the_very_end_only(self):
        # The blank line between paragraphs is NOT trailing whitespace and must survive; only whitespace
        # at the absolute end of the text is removed, matching copy-draft.ps1's non-multiline '\s+$'.
        self.assertEqual(COPY_DRAFT.normalise_draft('line1\n\nline2\n   '), 'line1\n\nline2')

    def test_a_blank_text_normalises_to_empty(self):
        self.assertEqual(COPY_DRAFT.normalise_draft('   \n\n  '), '')


class ReadDraftFileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='copy draft ')
        self.addCleanup(self.temp.cleanup)

    def test_a_missing_file_is_an_error(self):
        missing = str(Path(self.temp.name) / 'nope.txt')
        with self.assertRaisesRegex(COPY_DRAFT.ClipboardError, 'not found'):
            COPY_DRAFT.read_draft_file(missing)

    def test_an_empty_file_is_an_error(self):
        path = Path(self.temp.name) / 'empty.txt'
        path.write_text('   \n\n  ', encoding='utf-8')
        with self.assertRaisesRegex(COPY_DRAFT.ClipboardError, 'empty'):
            COPY_DRAFT.read_draft_file(str(path))

    def test_a_real_file_is_read_as_utf8_and_normalised(self):
        path = Path(self.temp.name) / 'draft.txt'
        path.write_bytes('café é\r\nsecond line\r\n'.encode('utf-8'))
        self.assertEqual(COPY_DRAFT.read_draft_file(str(path)), 'café é\nsecond line')


class UnwrapBacktickSpansTests(unittest.TestCase):
    def test_a_single_span_is_unwrapped(self):
        self.assertEqual(COPY_DRAFT.unwrap_backtick_spans('run `az login` now'), 'run az login now')

    def test_multiple_spans_are_each_unwrapped(self):
        self.assertEqual(
            COPY_DRAFT.unwrap_backtick_spans('`a` and `b` and `c`'),
            'a and b and c',
        )

    def test_text_without_backticks_is_unchanged(self):
        self.assertEqual(COPY_DRAFT.unwrap_backtick_spans('plain text'), 'plain text')


class EscapeHtmlTests(unittest.TestCase):
    def test_ampersand_lt_gt_are_escaped_in_that_order(self):
        self.assertEqual(COPY_DRAFT.escape_html('a < b & c > d'), 'a &lt; b &amp; c &gt; d')


class BuildHtmlFragmentTests(unittest.TestCase):
    def test_a_backtick_span_becomes_a_monospace_code_element(self):
        fragment = COPY_DRAFT.build_html_fragment('run `az login` now')
        self.assertEqual(
            fragment,
            'run <code style="font-family:Consolas,\'Courier New\',monospace;">az login</code> now',
        )

    def test_html_special_characters_are_escaped_outside_and_inside_spans(self):
        fragment = COPY_DRAFT.build_html_fragment('a & b `<tag>`')
        self.assertIn('a &amp; b', fragment)
        self.assertIn('<code style="font-family:Consolas,\'Courier New\',monospace;">&lt;tag&gt;</code>', fragment)

    def test_a_single_newline_within_a_paragraph_becomes_one_br(self):
        fragment = COPY_DRAFT.build_html_fragment('line one\nline two')
        self.assertEqual(fragment, 'line one<br>line two')

    def test_a_blank_line_between_paragraphs_becomes_a_double_br(self):
        fragment = COPY_DRAFT.build_html_fragment('first paragraph\n\nsecond paragraph')
        self.assertEqual(fragment, 'first paragraph<br><br>second paragraph')

    def test_no_block_elements_are_introduced(self):
        fragment = COPY_DRAFT.build_html_fragment('a\n\nb')
        self.assertNotIn('<p>', fragment)
        self.assertNotIn('<div>', fragment)


class CountCodeSpansTests(unittest.TestCase):
    def test_counts_every_opening_code_tag(self):
        fragment = COPY_DRAFT.build_html_fragment('`a` `b` `c`')
        self.assertEqual(COPY_DRAFT.count_code_spans(fragment), 3)

    def test_zero_when_there_are_no_spans(self):
        self.assertEqual(COPY_DRAFT.count_code_spans('plain'), 0)


class BuildCfHtmlTests(unittest.TestCase):
    def _assert_offsets_are_exact(self, fragment):
        text, start_html, end_html, start_fragment, end_fragment = COPY_DRAFT.build_cf_html(fragment)
        raw = text.encode('utf-8')
        self.assertEqual(raw[start_fragment:end_fragment], fragment.encode('utf-8'))
        self.assertEqual(
            raw[start_html:end_html],
            (COPY_DRAFT._CF_HTML_PRE + fragment + COPY_DRAFT._CF_HTML_POST).encode('utf-8'),
        )
        # The header itself is ASCII, so its own length in characters equals its length in bytes.
        self.assertEqual(text[:start_html].encode('utf-8'), text[:start_html].encode('ascii'))

    def test_offsets_are_exact_for_ascii_text(self):
        self._assert_offsets_are_exact('plain fragment text')

    def test_offsets_are_exact_for_non_ascii_text(self):
        self._assert_offsets_are_exact('café <code style="font-family:Consolas,\'Courier New\',monospace;">é</code> 日本語 emoji 🎉')

    def test_header_fields_are_present_and_fixed_width(self):
        text, *_ = COPY_DRAFT.build_cf_html('x')
        self.assertTrue(text.startswith('Version:0.9\r\n'))
        for field in ('StartHTML:', 'EndHTML:', 'StartFragment:', 'EndFragment:'):
            self.assertIn(field, text)


class PosixClipboardArgvTests(unittest.TestCase):
    def which_only(self, *names):
        allowed = set(names)
        return lambda name: f'/usr/bin/{name}' if name in allowed else None

    def test_wayland_session_selects_wl_copy(self):
        copy_argv, paste_argv, label = COPY_DRAFT.posix_clipboard_argv(
            {'WAYLAND_DISPLAY': 'wayland-0'}, self.which_only('wl-copy', 'wl-paste')
        )
        self.assertEqual(copy_argv, ['wl-copy'])
        self.assertEqual(paste_argv, ['wl-paste', '--no-newline'])
        self.assertEqual(label, 'wl-copy')

    def test_wayland_session_without_wl_clipboard_is_an_error_naming_the_package(self):
        with self.assertRaisesRegex(COPY_DRAFT.ClipboardError, 'wl-clipboard'):
            COPY_DRAFT.posix_clipboard_argv({'WAYLAND_DISPLAY': 'wayland-0'}, self.which_only())

    def test_x11_session_prefers_xclip(self):
        copy_argv, paste_argv, label = COPY_DRAFT.posix_clipboard_argv(
            {'DISPLAY': ':0'}, self.which_only('xclip', 'xsel')
        )
        self.assertEqual(copy_argv, ['xclip', '-selection', 'clipboard'])
        self.assertEqual(paste_argv, ['xclip', '-selection', 'clipboard', '-o'])
        self.assertEqual(label, 'xclip')

    def test_x11_session_falls_back_to_xsel(self):
        copy_argv, paste_argv, label = COPY_DRAFT.posix_clipboard_argv(
            {'DISPLAY': ':0'}, self.which_only('xsel')
        )
        self.assertEqual(copy_argv, ['xsel', '--clipboard', '--input'])
        self.assertEqual(paste_argv, ['xsel', '--clipboard', '--output'])
        self.assertEqual(label, 'xsel')

    def test_x11_session_without_either_tool_is_an_error(self):
        with self.assertRaisesRegex(COPY_DRAFT.ClipboardError, 'xclip or xsel'):
            COPY_DRAFT.posix_clipboard_argv({'DISPLAY': ':0'}, self.which_only())

    def test_darwin_selects_pbcopy(self):
        real_platform = COPY_DRAFT.sys.platform
        COPY_DRAFT.sys.platform = 'darwin'
        try:
            copy_argv, paste_argv, label = COPY_DRAFT.posix_clipboard_argv({}, self.which_only('pbcopy', 'pbpaste'))
        finally:
            COPY_DRAFT.sys.platform = real_platform
        self.assertEqual(copy_argv, ['pbcopy'])
        self.assertEqual(paste_argv, ['pbpaste'])
        self.assertEqual(label, 'pbcopy')

    def test_no_session_detected_is_an_error(self):
        real_platform = COPY_DRAFT.sys.platform
        COPY_DRAFT.sys.platform = 'linux'
        try:
            with self.assertRaisesRegex(COPY_DRAFT.ClipboardError, 'No supported clipboard session'):
                COPY_DRAFT.posix_clipboard_argv({}, self.which_only('wl-copy', 'xclip', 'pbcopy'))
        finally:
            COPY_DRAFT.sys.platform = real_platform


class FakeResult:
    def __init__(self, returncode=0, stdout='', stderr=''):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def make_run(results):
    calls = []

    def run(argv, **kwargs):
        calls.append((list(argv), kwargs))
        return results[len(calls) - 1]

    run.calls = calls
    return run


class CopyPosixTests(unittest.TestCase):
    """Exercises the exact argv/stdin copy_posix sends, with a fake `run` -- never the real clipboard."""

    def which_only(self, *names):
        allowed = set(names)
        return lambda name: f'/usr/bin/{name}' if name in allowed else None

    def test_wl_copy_is_called_with_stdin_text_and_wl_paste_reads_it_back(self):
        run = make_run([FakeResult(stdout=''), FakeResult(stdout='hello world')])
        message = COPY_DRAFT.copy_posix(
            'hello world',
            environ={'WAYLAND_DISPLAY': 'wayland-0'},
            which=self.which_only('wl-copy', 'wl-paste'),
            run=run,
        )
        (copy_argv, copy_kwargs), (paste_argv, paste_kwargs) = run.calls
        self.assertEqual(copy_argv, ['wl-copy'])
        self.assertEqual(copy_kwargs['input'], 'hello world')
        self.assertNotIn('stdin', copy_kwargs)
        self.assertEqual(paste_argv, ['wl-paste', '--no-newline'])
        self.assertEqual(paste_kwargs['stdin'], subprocess.DEVNULL)
        self.assertNotIn('input', paste_kwargs)
        self.assertIn('Copied 11 chars', message)
        self.assertIn('markdown kept for the paste target', message)

    def test_backticks_travel_intact_through_the_posix_backend(self):
        run = make_run([FakeResult(stdout=''), FakeResult(stdout='run `az login` now')])
        message = COPY_DRAFT.copy_posix(
            'run `az login` now',
            environ={'DISPLAY': ':0'},
            which=self.which_only('xclip'),
            run=run,
        )
        self.assertIn('Copied', message)
        copy_argv, copy_kwargs = run.calls[0]
        self.assertEqual(copy_kwargs['input'], 'run `az login` now')

    def test_a_readback_mismatch_is_an_error(self):
        run = make_run([FakeResult(stdout=''), FakeResult(stdout='something else')])
        with self.assertRaisesRegex(COPY_DRAFT.ClipboardError, 'did not read back'):
            COPY_DRAFT.copy_posix(
                'hello world',
                environ={'WAYLAND_DISPLAY': 'wayland-0'},
                which=self.which_only('wl-copy', 'wl-paste'),
                run=run,
            )

    def test_trailing_whitespace_in_the_readback_is_stripped_before_comparing(self):
        run = make_run([FakeResult(stdout=''), FakeResult(stdout='hello world   \n')])
        message = COPY_DRAFT.copy_posix(
            'hello world',
            environ={'WAYLAND_DISPLAY': 'wayland-0'},
            which=self.which_only('wl-copy', 'wl-paste'),
            run=run,
        )
        self.assertIn('Copied 11 chars', message)

    def test_a_nonzero_exit_from_the_copy_tool_is_an_error(self):
        run = make_run([FakeResult(returncode=1, stderr='no selection owner')])
        with self.assertRaisesRegex(COPY_DRAFT.ClipboardError, 'no selection owner'):
            COPY_DRAFT.copy_posix(
                'hello world',
                environ={'WAYLAND_DISPLAY': 'wayland-0'},
                which=self.which_only('wl-copy', 'wl-paste'),
                run=run,
            )

    def test_a_timeout_from_the_copy_tool_is_an_error(self):
        def run(argv, **kwargs):
            raise subprocess.TimeoutExpired(cmd=argv, timeout=10)

        with self.assertRaisesRegex(COPY_DRAFT.ClipboardError, 'did not answer within'):
            COPY_DRAFT.copy_posix(
                'hello world',
                environ={'WAYLAND_DISPLAY': 'wayland-0'},
                which=self.which_only('wl-copy', 'wl-paste'),
                run=run,
            )

    def test_no_clipboard_tool_found_is_an_error_naming_the_package(self):
        with self.assertRaisesRegex(COPY_DRAFT.ClipboardError, 'wl-clipboard'):
            COPY_DRAFT.copy_posix(
                'hello world',
                environ={'WAYLAND_DISPLAY': 'wayland-0'},
                which=self.which_only(),
                run=make_run([]),
            )


@unittest.skipUnless(os.name == 'nt', 'Exercises the real Windows clipboard via ctypes; Windows only.')
class WindowsCtypesRoundTripTests(unittest.TestCase):
    """Runs only on Windows. Writes to the real clipboard there -- never on this (Linux) machine."""

    def test_both_flavours_round_trip_through_the_real_clipboard(self):
        text = "run `az login` now\n\nsecond paragraph"
        message = COPY_DRAFT.copy_windows(text, plain_only=False)
        self.assertIn('HTML + plain verified', message)

        user32, kernel32 = COPY_DRAFT._windows_api()
        html_format = user32.RegisterClipboardFormatW('HTML Format')
        html, plain = COPY_DRAFT._read_windows_clipboard(user32, kernel32, html_format)
        self.assertIsNotNone(html)
        self.assertIn('<code', html)
        self.assertEqual(plain, COPY_DRAFT.unwrap_backtick_spans(text))

    def test_plain_only_writes_literal_text_with_no_html_flavour(self):
        text = 'a literal `command` to run'
        message = COPY_DRAFT.copy_windows(text, plain_only=True)
        self.assertIn('plain text only', message)

        user32, kernel32 = COPY_DRAFT._windows_api()
        html_format = user32.RegisterClipboardFormatW('HTML Format')
        html, plain = COPY_DRAFT._read_windows_clipboard(user32, kernel32, html_format)
        self.assertIsNone(html)
        self.assertEqual(plain, text)


if __name__ == '__main__':
    unittest.main()
