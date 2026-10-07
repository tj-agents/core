#!/usr/bin/env python3
"""Copy a drafted file onto the system clipboard, verifying off the live clipboard afterwards.

Run as `python3 copy_draft.py --path <file> [--plain-only]` (`python` on Windows); the shebang and
exec bit are not relied on.

On Windows, without `--plain-only`, this writes BOTH an `HTML Format` flavour (CF_HTML, with single
backtick spans rendered as monospace `<code>`) and a plain Unicode text flavour (backticks unwrapped),
then verifies both off the live clipboard. `--plain-only` writes only the literal text, unchanged, as
CF_UNICODETEXT.

On Linux and macOS, standard clipboard tools hold one flavour per copy, so this always copies one plain
text flavour: the raw text with backticks intact, because Teams renders markdown typed or pasted into
its compose box. `--plain-only` makes no difference there; it exists for the Windows HTML/plain choice.

The pure text transforms (normalising, backtick unwrapping, HTML escaping, CF_HTML construction, code
span counting) are plain functions, testable on any OS. The clipboard backends are small, platform- or
environment-selected functions that take `run`/`which`/`environ` as arguments so tests can inject stubs
without ever touching a real clipboard.
"""

import argparse
import ctypes
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

IS_WINDOWS = os.name == 'nt'

GMEM_MOVEABLE = 0x0002
CF_UNICODETEXT = 13


class ClipboardError(Exception):
    """A copy or verification step failed; the message is the whole report."""


# --- pure text transforms -----------------------------------------------------------------------

_BACKTICK_SPAN = re.compile(r'`([^`]+)`')
_TRAILING_WHITESPACE = re.compile(r'\s+\Z')


def normalise_draft(raw):
    """CRLF -> LF, then whitespace trimmed off only the very end of the text (not per line)."""
    text = raw.replace('\r\n', '\n')
    return _TRAILING_WHITESPACE.sub('', text)


def read_draft_file(path):
    """The normalised draft text, or a ClipboardError naming a missing file or an empty draft."""
    resolved = Path(path)
    if not resolved.is_file():
        raise ClipboardError(f'Draft file not found: {path}')
    raw = resolved.read_text(encoding='utf-8')
    text = normalise_draft(raw)
    if not text.strip():
        raise ClipboardError(f'Draft file is empty: {path}')
    return text


def unwrap_backtick_spans(text):
    """Backticks are markup, not content. The plain flavour an app without HTML receives has them removed."""
    return _BACKTICK_SPAN.sub(lambda m: m.group(1), text)


def escape_html(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def count_code_spans(fragment):
    return fragment.count('<code')


def build_html_fragment(text):
    """The HTML fragment for `text`: escaped, backtick spans as monospace `<code>`, no block elements.

    Teams gives `<p>` and `<div>` their own margins and indent on paste, so paragraphs (separated by a
    blank line) are joined with a double `<br>` instead, and a single newline within a paragraph becomes
    one `<br>`.
    """
    escaped = escape_html(text)
    with_code = _BACKTICK_SPAN.sub(
        lambda m: f'<code style="font-family:Consolas,\'Courier New\',monospace;">{m.group(1)}</code>',
        escaped,
    )
    paragraphs = re.split(r'\n{2,}', with_code)
    return '<br><br>'.join(paragraph.replace('\n', '<br>') for paragraph in paragraphs)


_CF_HTML_HEADER = (
    'Version:0.9\r\n'
    'StartHTML:{0:010d}\r\n'
    'EndHTML:{1:010d}\r\n'
    'StartFragment:{2:010d}\r\n'
    'EndFragment:{3:010d}\r\n'
)
_CF_HTML_PRE = '<html><body><!--StartFragment-->'
_CF_HTML_POST = '<!--EndFragment--></body></html>'


def build_cf_html(fragment):
    """The CF_HTML text for `fragment`, with its header's byte offsets into its own UTF-8 encoding.

    Returns (text, start_html, end_html, start_fragment, end_fragment). Offsets are UTF-8 byte offsets,
    so text.encode('utf-8')[start_fragment:end_fragment] is exactly `fragment`'s own UTF-8 bytes, and
    [start_html:end_html] is exactly the `<html>...</html>` bytes.
    """
    start_html = len(_CF_HTML_HEADER.format(0, 0, 0, 0).encode('utf-8'))
    start_fragment = start_html + len(_CF_HTML_PRE.encode('utf-8'))
    end_fragment = start_fragment + len(fragment.encode('utf-8'))
    end_html = end_fragment + len(_CF_HTML_POST.encode('utf-8'))
    header = _CF_HTML_HEADER.format(start_html, end_html, start_fragment, end_fragment)
    text = header + _CF_HTML_PRE + fragment + _CF_HTML_POST
    return text, start_html, end_html, start_fragment, end_fragment


# --- POSIX (Linux, macOS) backend ---------------------------------------------------------------


def posix_clipboard_argv(environ, which):
    """(copy_argv, paste_argv, label) for the clipboard tool this environment selects.

    Wayland is checked before X11 because a Wayland session under XWayland can still have DISPLAY set;
    WAYLAND_DISPLAY is the more specific signal. Raises ClipboardError naming what to install when no
    tool is found.
    """
    if environ.get('WAYLAND_DISPLAY'):
        if which('wl-copy') and which('wl-paste'):
            return ['wl-copy'], ['wl-paste', '--no-newline'], 'wl-copy'
        raise ClipboardError(
            'No Wayland clipboard tool was found on PATH. Install wl-clipboard (provides wl-copy/wl-paste).'
        )
    if environ.get('DISPLAY'):
        if which('xclip'):
            return ['xclip', '-selection', 'clipboard'], ['xclip', '-selection', 'clipboard', '-o'], 'xclip'
        if which('xsel'):
            return ['xsel', '--clipboard', '--input'], ['xsel', '--clipboard', '--output'], 'xsel'
        raise ClipboardError('No X11 clipboard tool was found on PATH. Install xclip or xsel.')
    if sys.platform == 'darwin':
        if which('pbcopy') and which('pbpaste'):
            return ['pbcopy'], ['pbpaste'], 'pbcopy'
        raise ClipboardError('pbcopy/pbpaste was not found on PATH.')
    raise ClipboardError(
        'No supported clipboard session was detected: neither WAYLAND_DISPLAY nor DISPLAY is set, and this is not macOS.'
    )


def _run_clipboard_tool(run, argv, label, text=None, timeout=10):
    kwargs = dict(stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
    if text is None:
        # No input to send: stdin is closed rather than inherited, so a read-back command can never block
        # on this process's own stdin.
        kwargs['stdin'] = subprocess.DEVNULL
    else:
        kwargs['input'] = text
    try:
        result = run(argv, **kwargs)
    except subprocess.TimeoutExpired:
        raise ClipboardError(f'{label} did not answer within {timeout} seconds.') from None
    except OSError as exc:
        raise ClipboardError(f'{label} could not be run: {exc}') from None
    if result.returncode != 0:
        raise ClipboardError(f'{label} failed (exit {result.returncode}): {(result.stderr or "").strip()}')
    return result.stdout


def copy_posix(text, environ=None, which=shutil.which, run=subprocess.run):
    """Copy `text` as one plain-text flavour (backticks intact) and verify it round-trips.

    `wl-copy` forks a background process to serve the selection and this call returns as soon as that
    fork happens, so it never hangs waiting for the selection to be requested.
    """
    environ = os.environ if environ is None else environ
    copy_argv, paste_argv, label = posix_clipboard_argv(environ, which)

    _run_clipboard_tool(run, copy_argv, f'{label} copy', text=text)
    back = _run_clipboard_tool(run, paste_argv, f'{label} paste')
    if _TRAILING_WHITESPACE.sub('', back) != text:
        raise ClipboardError(f'Clipboard verification failed: {label} did not read back what was copied.')

    return f'Copied {len(text)} chars (plain text; markdown kept for the paste target).'


# --- Windows backend -----------------------------------------------------------------------------


def _windows_api():
    # Imported and bound lazily: ctypes.windll only exists on Windows, and this module must still import
    # cleanly on Linux/macOS so the pure functions and the POSIX backend stay testable there.
    import ctypes.wintypes as wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    user32.GetClipboardData.restype = wintypes.HANDLE
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.RegisterClipboardFormatW.argtypes = [wintypes.LPCWSTR]
    user32.RegisterClipboardFormatW.restype = wintypes.UINT
    user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
    user32.IsClipboardFormatAvailable.restype = wintypes.BOOL

    # HANDLE/HGLOBAL are explicitly pointer-sized (wintypes.HANDLE is c_void_p) rather than a 32-bit DWORD,
    # so these calls stay correct on 64-bit Windows.
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HANDLE
    kernel32.GlobalLock.argtypes = [wintypes.HANDLE]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [wintypes.HANDLE]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.GlobalSize.argtypes = [wintypes.HANDLE]
    kernel32.GlobalSize.restype = ctypes.c_size_t

    return user32, kernel32


def _open_clipboard(user32, retries=10, delay=0.05):
    # Another process (often the previous clipboard owner tearing down) can hold the clipboard for a
    # moment; a short retry loop rides that out instead of failing a copy that would succeed a beat later.
    for _ in range(retries):
        if user32.OpenClipboard(None):
            return
        time.sleep(delay)
    raise ClipboardError('Could not open the clipboard; another process held it.')


def _set_clipboard_bytes(user32, kernel32, clipboard_format, data):
    size = len(data)
    handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, ctypes.c_size_t(size))
    if not handle:
        raise ClipboardError('GlobalAlloc failed while preparing clipboard data.')
    pointer = kernel32.GlobalLock(handle)
    if not pointer:
        raise ClipboardError('GlobalLock failed while preparing clipboard data.')
    try:
        ctypes.memmove(pointer, data, size)
    finally:
        kernel32.GlobalUnlock(handle)
    # Once SetClipboardData succeeds the system owns the handle; it must not be freed here.
    if not user32.SetClipboardData(clipboard_format, handle):
        raise ClipboardError('SetClipboardData failed.')


def _read_windows_clipboard(user32, kernel32, html_format):
    _open_clipboard(user32)
    try:
        html = None
        if user32.IsClipboardFormatAvailable(html_format):
            handle = user32.GetClipboardData(html_format)
            if handle:
                pointer = kernel32.GlobalLock(handle)
                if pointer:
                    try:
                        size = kernel32.GlobalSize(handle)
                        raw = ctypes.string_at(pointer, size)
                    finally:
                        kernel32.GlobalUnlock(handle)
                    html = raw.split(b'\x00', 1)[0].decode('utf-8', errors='replace')

        plain = None
        if user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            handle = user32.GetClipboardData(CF_UNICODETEXT)
            if handle:
                pointer = kernel32.GlobalLock(handle)
                if pointer:
                    try:
                        plain = ctypes.wstring_at(pointer)
                    finally:
                        kernel32.GlobalUnlock(handle)
        return html, plain
    finally:
        user32.CloseClipboard()


def copy_windows(text, plain_only):
    """Copy `text` on Windows via ctypes: CF_UNICODETEXT always, plus CF_HTML unless `plain_only`.

    Without `plain_only`, verifies both flavours off the live clipboard afterwards and raises
    ClipboardError on any mismatch, so a success message means it truly landed at that moment.
    """
    user32, kernel32 = _windows_api()
    html_format = user32.RegisterClipboardFormatW('HTML Format')

    plain = text if plain_only else unwrap_backtick_spans(text)
    unicode_bytes = plain.encode('utf-16-le') + b'\x00\x00'

    cf_html_bytes = None
    spans = 0
    if not plain_only:
        fragment = build_html_fragment(text)
        spans = count_code_spans(fragment)
        cf_html_text, *_ = build_cf_html(fragment)
        cf_html_bytes = cf_html_text.encode('utf-8') + b'\x00'

    _open_clipboard(user32)
    try:
        if not user32.EmptyClipboard():
            raise ClipboardError('EmptyClipboard failed.')
        _set_clipboard_bytes(user32, kernel32, CF_UNICODETEXT, unicode_bytes)
        if cf_html_bytes is not None:
            _set_clipboard_bytes(user32, kernel32, html_format, cf_html_bytes)
    finally:
        user32.CloseClipboard()

    if plain_only:
        return f'Copied {len(plain)} chars (plain text only).'

    # Verify BOTH flavours off the live clipboard. A plain-only round trip can pass while the HTML is
    # absent, which is exactly how a paste loses its code formatting.
    landed_html, landed_plain = _read_windows_clipboard(user32, kernel32, html_format)
    if landed_html is None:
        raise ClipboardError(
            'Clipboard verification failed: no HTML flavour present. Something overwrote the clipboard.'
        )
    if _TRAILING_WHITESPACE.sub('', landed_plain or '') != plain:
        raise ClipboardError('Clipboard verification failed: plain flavour did not round-trip.')
    landed_spans = count_code_spans(landed_html)
    if landed_spans != spans:
        raise ClipboardError(
            f'Clipboard verification failed: expected {spans} code spans, found {landed_spans} on the clipboard.'
        )

    return f'Copied {len(plain)} chars, {spans} code spans, HTML + plain verified on the clipboard.'


# --- CLI -------------------------------------------------------------------------------------------


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Copy a drafted file onto the system clipboard.')
    parser.add_argument('--path', required=True, help='Path to the UTF-8 draft file to copy.')
    parser.add_argument(
        '--plain-only', action='store_true',
        help='Copy the literal text only; no HTML flavour, backticks left exactly as typed.',
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        text = read_draft_file(args.path)
        message = copy_windows(text, args.plain_only) if IS_WINDOWS else copy_posix(text)
        print(message)
        return 0
    except ClipboardError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
