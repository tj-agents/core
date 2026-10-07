#!/usr/bin/env python3
"""Copy a drafted file onto the system clipboard, verifying off the live clipboard afterwards.

Run as `python3 copy_draft.py --path <file> [--plain-only]` (`python` on Windows); the shebang and
exec bit are not relied on.

On Windows, without `--plain-only`, this writes BOTH an `HTML Format` flavour (CF_HTML, with single
backtick spans rendered as monospace `<code>`) and a plain Unicode text flavour (backticks unwrapped),
then verifies both off the live clipboard. `--plain-only` writes only the literal text, unchanged, as
CF_UNICODETEXT, and that is still verified by reading it back.

On Linux, `wl-copy`/`xclip` can each set only one clipboard MIME type per invocation, so this is a choice,
not a combination: default mode copies one `text/html` flavour built from the same escaped-and-code-spanned
fragment Windows uses, so a paste into Teams still renders backtick spans as monospace -- but a plain-text
target (a terminal, a plain text field) reads nothing useful from it. `--plain-only` copies the literal
text as plain instead, everywhere, for exactly that case. `xsel` cannot set an explicit MIME type, so with
only `xsel` available (no `xclip`, no Wayland) default mode falls back to plain text with the markdown left
intact and says so. macOS's `pbcopy` has no HTML flavour either, so macOS always copies plain text with the
markdown intact, and says so.

The pure text transforms (normalising, backtick unwrapping, HTML escaping, HTML fragment/document
construction, CF_HTML offset construction, code span counting) are plain functions, testable on any OS.
The clipboard backends are small, platform- or environment-selected functions that take
`run`/`which`/`environ` as arguments so tests can inject stubs without ever touching a real clipboard.
"""

import argparse
from collections import namedtuple
import ctypes
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

IS_WINDOWS = os.name == 'nt'

GMEM_MOVEABLE = 0x0002
CF_UNICODETEXT = 13
HWND_MESSAGE = -3


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
    """The normalised draft text, or a ClipboardError naming a missing, non-UTF-8 or empty draft.

    Read as `utf-8-sig` rather than `utf-8` so a leading BOM -- common from Windows editors -- is
    dropped instead of landing on the clipboard as a stray character.
    """
    resolved = Path(path)
    if not resolved.is_file():
        raise ClipboardError(f'Draft file not found: {path}')
    try:
        raw = resolved.read_text(encoding='utf-8-sig')
    except UnicodeDecodeError:
        raise ClipboardError(f'Draft file is not valid UTF-8: {path}') from None
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


def build_full_html(fragment):
    """A minimal standalone HTML document carrying `fragment`, for the Linux `text/html` MIME flavour.

    Unlike CF_HTML there is no fragment-offset header to construct: `wl-copy`/`xclip` set the bytes given
    as the whole `text/html` value, so this -- not a CF_HTML payload -- is what a paste target receives.
    """
    return f'<html><head><meta charset="utf-8"></head><body>{fragment}</body></html>'


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


def _no_env_override(environ):
    return None


def _pbcopy_env_override(environ):
    # pbcopy/pbpaste pick their text encoding from the locale; forcing a UTF-8 one here is what keeps
    # non-ASCII draft text (accents, emoji) intact rather than silently mangled on some machines.
    env = dict(environ)
    env['LANG'] = 'en_US.UTF-8'
    env['LC_CTYPE'] = 'en_US.UTF-8'
    return env


# html_copy_argv/html_paste_argv are None for a tool that cannot set an explicit MIME type (xsel) or has
# no HTML concept at all (pbcopy); copy_posix falls back to the plain flavour for those, using
# no_html_reason (also None when the tool does support HTML) to say why in the success line.
PosixTool = namedtuple(
    'PosixTool',
    'label copy_argv paste_argv html_copy_argv html_paste_argv env_override no_html_reason',
)

_WL_COPY = PosixTool(
    'wl-copy',
    ['wl-copy'], ['wl-paste', '--no-newline'],
    ['wl-copy', '--type', 'text/html'], ['wl-paste', '--type', 'text/html'],
    _no_env_override, None,
)
_XCLIP = PosixTool(
    'xclip',
    ['xclip', '-selection', 'clipboard'], ['xclip', '-selection', 'clipboard', '-o'],
    ['xclip', '-selection', 'clipboard', '-t', 'text/html'],
    ['xclip', '-selection', 'clipboard', '-t', 'text/html', '-o'],
    _no_env_override, None,
)
_XSEL = PosixTool(
    'xsel', ['xsel', '--clipboard', '--input'], ['xsel', '--clipboard', '--output'], None, None,
    _no_env_override, 'xsel cannot set an HTML flavour',
)
_PBCOPY = PosixTool(
    'pbcopy', ['pbcopy'], ['pbpaste'], None, None,
    _pbcopy_env_override, 'pbcopy has no HTML flavour',
)


def posix_clipboard_tool(environ, which):
    """The PosixTool this environment selects, or a ClipboardError naming what to install.

    Wayland is checked first because a Wayland session under XWayland can still have DISPLAY set.
    Without wl-copy/wl-paste on PATH, a Wayland session that also has DISPLAY set falls back to the X11
    tools rather than failing outright. When nothing at all works in a Wayland session, the error
    recommends wl-clipboard first regardless of whether DISPLAY happens to be set too, since that is the
    native tool for the session actually running; xclip/xsel are named only as the XWayland fallback.
    """
    wayland = bool(environ.get('WAYLAND_DISPLAY'))
    x11 = bool(environ.get('DISPLAY'))

    if wayland and which('wl-copy') and which('wl-paste'):
        return _WL_COPY

    if x11:
        if which('xclip'):
            return _XCLIP
        if which('xsel'):
            return _XSEL
        if wayland:
            raise ClipboardError(
                'No clipboard tool was found on PATH. Install wl-clipboard (provides wl-copy/wl-paste) for '
                'this Wayland session, or xclip/xsel as an XWayland fallback.'
            )
        raise ClipboardError('No X11 clipboard tool was found on PATH. Install xclip or xsel.')

    if wayland:
        raise ClipboardError(
            'No Wayland clipboard tool was found on PATH. Install wl-clipboard (provides wl-copy/wl-paste).'
        )

    if sys.platform == 'darwin':
        if which('pbcopy') and which('pbpaste'):
            return _PBCOPY
        raise ClipboardError('pbcopy/pbpaste was not found on PATH.')

    raise ClipboardError(
        'No supported clipboard session was detected: neither WAYLAND_DISPLAY nor DISPLAY is set, and this is not macOS.'
    )


def _clipboard_failure(label, returncode, stderr):
    detail = (stderr or '').strip()
    message = f'{label} failed (exit {returncode})'
    return ClipboardError(f'{message}: {detail}' if detail else f'{message}.')


def _run_clipboard_process(run, argv, label, env=None, timeout=10, input_text=None, capture_stdout=False):
    """Runs one clipboard tool invocation; returns (returncode, stdout_text, stderr_text).

    Never raises for a nonzero exit -- a read-back's nonzero exit (wl-paste's "Nothing is copied", xclip's
    "target not available") is routine while a just-started owner is still taking over, not necessarily a
    real failure, so the retry loop around a read-back needs the chance to try again. Only a process that
    could not even be started or answer within the timeout becomes a ClipboardError here.

    stdout is discarded (DEVNULL) unless `capture_stdout` -- a copy command's stdout is never read. stderr
    always goes to a private temporary file rather than a PIPE: wl-copy, xclip and xsel each fork a
    long-lived background process that goes on serving the selection after this call returns, and that
    fork inherits this call's stdio. A PIPE stays open (and communicate() keeps waiting on it) until every
    process holding it exits, so a copy that actually succeeded immediately would hang until the timeout. A
    plain file has no such problem, so the failing tool's own stderr can still be reported.

    Both streams are decoded explicitly as UTF-8 with decoding errors replaced, rather than left to the
    process's locale -- the locale is exactly what forcing LANG/LC_CTYPE for pbcopy/pbpaste routes around.
    """
    kwargs = dict(timeout=timeout, encoding='utf-8', errors='replace')
    if input_text is None:
        kwargs['stdin'] = subprocess.DEVNULL
    else:
        kwargs['input'] = input_text
    kwargs['stdout'] = subprocess.PIPE if capture_stdout else subprocess.DEVNULL
    if env is not None:
        kwargs['env'] = env

    with tempfile.TemporaryFile(mode='w+', encoding='utf-8', errors='replace') as stderr_file:
        try:
            result = run(argv, stderr=stderr_file, **kwargs)
        except subprocess.TimeoutExpired:
            raise ClipboardError(f'{label} did not answer within {timeout} seconds.') from None
        except OSError as exc:
            raise ClipboardError(f'{label} could not be run: {exc}') from None
        stderr_file.seek(0)
        stderr_text = stderr_file.read()

    stdout_text = result.stdout if capture_stdout else ''
    return result.returncode, (stdout_text or ''), stderr_text


def _run_copy(run, argv, text, label, env=None, timeout=10):
    returncode, _, stderr = _run_clipboard_process(
        run, argv, label, env=env, timeout=timeout, input_text=text, capture_stdout=False,
    )
    if returncode != 0:
        raise _clipboard_failure(label, returncode, stderr)


def _read_back_with_retry(run, argv, label, is_ok, env=None, attempts=5, total_timeout=1.0):
    """Reads back up to `attempts` times, pausing between tries, until `is_ok` accepts the output.

    wl-copy hands the selection to a forked server and returns before that server is necessarily ready to
    answer a read; an immediate read-back can see the previous (or empty) selection, or the tool can exit
    nonzero rather than return anything at all (wl-paste's "Nothing is copied", xclip's "target not
    available") while that handoff is still in flight. The same latency has been seen from xclip/xsel.
    Retrying for up to `total_timeout` seconds rides that out instead of failing a copy that would read
    back correctly a moment later. Only once every attempt has exited nonzero does this raise, carrying the
    last attempt's stderr; a zero-exit mismatch is left for the caller, which knows what the right message
    for that content mismatch is.
    """
    delay = total_timeout / attempts
    returncode, output, stderr = 1, '', ''
    for attempt in range(attempts):
        returncode, output, stderr = _run_clipboard_process(run, argv, label, env=env, capture_stdout=True)
        if returncode == 0 and is_ok(output):
            return output
        if attempt < attempts - 1:
            time.sleep(delay)
    if returncode != 0:
        raise _clipboard_failure(label, returncode, stderr)
    return output


def copy_posix(text, plain_only, environ=None, which=shutil.which, run=subprocess.run):
    """Copy `text` through the clipboard tool this environment selects, and verify it round-trips.

    Default mode copies an HTML flavour (so Teams renders backtick spans as monospace) when the selected
    tool supports setting one; otherwise -- xsel, or macOS's pbcopy -- it falls back to the plain flavour
    with the markdown left intact, and the returned message says so. `--plain-only` always copies the
    literal text as plain, on every tool. wl-copy/xclip can only set one MIME type per copy, so default
    mode is HTML-only even on tools that support it: nothing a plain-text paste target can read (see
    `.agents/machine/TECH_DEBT.md`, "clip offers one clipboard flavour per copy on Linux").
    """
    environ = os.environ if environ is None else environ
    tool = posix_clipboard_tool(environ, which)
    env = tool.env_override(environ)

    if not plain_only and tool.html_copy_argv:
        fragment = build_html_fragment(text)
        spans = count_code_spans(fragment)
        html_document = build_full_html(fragment)
        _run_copy(run, tool.html_copy_argv, html_document, f'{tool.label} copy', env=env)

        def html_ok(output):
            return _TRAILING_WHITESPACE.sub('', output) == html_document

        landed_html = _read_back_with_retry(run, tool.html_paste_argv, f'{tool.label} paste', html_ok, env=env)
        if not html_ok(landed_html):
            raise ClipboardError(
                f'Clipboard verification failed: {tool.label} did not read back the HTML flavour that was copied.'
            )
        return f'Copied {len(text)} chars, {spans} code spans, HTML verified on the clipboard.'

    plain = text
    _run_copy(run, tool.copy_argv, plain, f'{tool.label} copy', env=env)

    def plain_ok(output):
        return _TRAILING_WHITESPACE.sub('', output) == plain

    landed_plain = _read_back_with_retry(run, tool.paste_argv, f'{tool.label} paste', plain_ok, env=env)
    if not plain_ok(landed_plain):
        raise ClipboardError(f'Clipboard verification failed: {tool.label} did not read back what was copied.')

    if plain_only:
        return f'Copied {len(plain)} chars (plain text only).'
    if tool.no_html_reason:
        return f'Copied {len(plain)} chars (plain text; markdown kept for the paste target; {tool.no_html_reason}).'
    return f'Copied {len(plain)} chars (plain text; markdown kept for the paste target).'


# --- Windows backend -----------------------------------------------------------------------------


def _windows_api():
    # Imported and bound lazily: ctypes.windll only exists on Windows, and this module must still import
    # cleanly on Linux/macOS so the pure functions and the POSIX backend stay testable there.
    import ctypes.wintypes as wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    user32.CreateWindowExW.argtypes = [
        wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.HWND, wintypes.HANDLE, wintypes.HANDLE, wintypes.LPVOID,
    ]
    user32.CreateWindowExW.restype = wintypes.HWND
    user32.DestroyWindow.argtypes = [wintypes.HWND]
    user32.DestroyWindow.restype = wintypes.BOOL

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


def _create_message_window(user32):
    """A hidden message-only window, so SetClipboardData has a real owner to attach the data to.

    OpenClipboard(NULL) leaves the clipboard with no owning window at all; EmptyClipboard followed by
    SetClipboardData with no owner is exactly the shape that has been seen failing SetClipboardData, so a
    throwaway `STATIC`-class window parented to HWND_MESSAGE stands in as the owner instead.
    """
    import ctypes.wintypes as wintypes

    hwnd = user32.CreateWindowExW(0, 'STATIC', '', 0, 0, 0, 0, 0, wintypes.HWND(HWND_MESSAGE), None, None, None)
    if not hwnd:
        raise ClipboardError('CreateWindowExW failed while preparing a clipboard owner window.')
    return hwnd


def _acquire_clipboard_owner(user32):
    """The message window handle, or None when creating one failed -- OpenClipboard(NULL) still works.

    A window-less copy is worse (no real owner, see `_create_message_window`) but not worthless, so a
    failure to create the window falls back to the old OpenClipboard(NULL) behaviour instead of failing
    the whole copy over what is meant to be a belt-and-suspenders improvement.
    """
    try:
        return _create_message_window(user32)
    except ClipboardError:
        return None


def _open_clipboard(user32, hwnd, retries=10, delay=0.05):
    # Another process (often the previous clipboard owner tearing down) can hold the clipboard for a
    # moment; a short retry loop rides that out instead of failing a copy that would succeed a beat later.
    for _ in range(retries):
        if user32.OpenClipboard(hwnd):
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


def _read_windows_clipboard(user32, kernel32, html_format, hwnd):
    _open_clipboard(user32, hwnd)
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

    Always verifies off the live clipboard afterwards, including in `--plain-only` mode, and raises
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

    hwnd = _acquire_clipboard_owner(user32)
    try:
        _open_clipboard(user32, hwnd)
        try:
            if not user32.EmptyClipboard():
                raise ClipboardError('EmptyClipboard failed.')
            _set_clipboard_bytes(user32, kernel32, CF_UNICODETEXT, unicode_bytes)
            if cf_html_bytes is not None:
                _set_clipboard_bytes(user32, kernel32, html_format, cf_html_bytes)
        finally:
            user32.CloseClipboard()

        # Verify off the live clipboard, in every mode: a plain-only round trip can pass on its own, but
        # verifying nothing is what let a stale or empty clipboard pass for a successful plain-only copy.
        landed_html, landed_plain = _read_windows_clipboard(user32, kernel32, html_format, hwnd)
    finally:
        if hwnd:
            user32.DestroyWindow(hwnd)

    if _TRAILING_WHITESPACE.sub('', landed_plain or '') != plain:
        raise ClipboardError('Clipboard verification failed: plain flavour did not round-trip.')

    if plain_only:
        return f'Copied {len(plain)} chars (plain text only).'

    # Verify BOTH flavours off the live clipboard. A plain-only round trip can pass while the HTML is
    # absent, which is exactly how a paste loses its code formatting.
    if landed_html is None:
        raise ClipboardError(
            'Clipboard verification failed: no HTML flavour present. Something overwrote the clipboard.'
        )
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
        message = copy_windows(text, args.plain_only) if IS_WINDOWS else copy_posix(text, args.plain_only)
        print(message)
        return 0
    except ClipboardError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
