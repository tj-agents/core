"""Shared launch primitives for the native agent CLIs, on Windows and POSIX.

Imported by handoff-claude, handoff-codex and open-claude so the environment scrub, executable discovery,
standards sync, lane lookup and terminal argument escaping have one owner. Not runnable on its own.
"""

import glob
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
IS_WINDOWS = os.name == 'nt'

# Session state a Claude Code parent exports into anything it spawns. NO_COLOR=1 alone makes the child
# black and white; the CLAUDE_CODE_* set binds it to the parent's messaging pipe and makes it behave as a
# managed nested child rather than the independent session the caller asked for. CLAUDE_CODE_GIT_BASH_PATH
# is machine configuration rather than session state and is deliberately absent from this list.
SESSION_ENVIRONMENT = (
    'NO_COLOR',
    'CLAUDECODE',
    'CLAUDE_CODE_CHILD_SESSION',
    'CLAUDE_CODE_ENTRYPOINT',
    'CLAUDE_CODE_SESSION_ID',
    'CLAUDE_CODE_MESSAGING_SOCKET',
    'CLAUDE_CODE_MESSAGING_TOKEN',
    'CLAUDE_PID',
    'WORKBOARD_LAUNCH_TOKEN',
    'WORKBOARD_WORKFLOW_TOKEN',
)


class LaunchError(Exception):
    """A launch precondition failed; the message is the whole report."""


def launch_environment(clear=(), force=None):
    """The environment changes a launched CLI needs: names to remove and values to set.

    Returned rather than applied, because on POSIX they travel inside the launched command line: a tab
    handler starts the command from an already-running terminal process that never sees ours.
    """
    cleared = list(dict.fromkeys((*SESSION_ENVIRONMENT, *clear)))
    forced = dict(force or {})
    return [name for name in cleared if name not in forced], forced


def _is_script(path):
    try:
        with open(path, 'rb') as f:
            return f.read(2) == b'#!'
    except OSError:
        return True


# The native executable, never the npm shim: a shim launches the TUI through an extra node process and
# degrades it to monochrome and non-interactive, the failure handoff-codex first recorded. On Windows
# `claude` on PATH resolves to that shim (claude.ps1/claude.cmd), so PATH is consulted only for a real
# claude.exe; on POSIX the shim is a `#!` script, and npm with its prefix at ~/.local puts one at the native
# install's own path, so any candidate that is one is refused.
def resolve_claude_executable(home=None, which=shutil.which):
    home = Path(home) if home else Path.home()
    name = 'claude.exe' if IS_WINDOWS else 'claude'
    local = home / '.local' / 'bin' / name
    found = which(name)
    for candidate in (str(local), found):
        if candidate and os.path.isfile(candidate) and (IS_WINDOWS or not _is_script(os.path.realpath(candidate))):
            return candidate

    raise LaunchError(f'The native Claude Code executable was not found. Looked for {local} and a native {name} on PATH.')


_CODEX_VERSION = re.compile(r'(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?')


def parse_codex_version(text):
    match = _CODEX_VERSION.search(text or '')
    if not match:
        return None
    return {
        'core': tuple(int(match.group(i)) for i in (1, 2, 3)),
        'prerelease': match.group(4) or '',
        'text': match.group(0),
    }


def compare_codex_version(left, right):
    if left['core'] != right['core']:
        return -1 if left['core'] < right['core'] else 1
    # A prerelease ranks BELOW the release it precedes, so 0.151.0-alpha.7.1 loses to 0.151.0. Ranking by
    # file date instead is what silently selected a three-versions-stale alpha over the current CLI.
    if bool(left['prerelease']) != bool(right['prerelease']):
        return -1 if left['prerelease'] else 1
    if not left['prerelease']:
        return 0

    left_parts, right_parts = left['prerelease'].split('.'), right['prerelease'].split('.')
    for i in range(max(len(left_parts), len(right_parts))):
        if i >= len(left_parts):
            return -1
        if i >= len(right_parts):
            return 1
        a, b = left_parts[i], right_parts[i]
        if a.isdigit() and b.isdigit():
            a, b = int(a), int(b)
        if a != b:
            return -1 if a < b else 1
    return 0


def codex_candidate_paths(which=shutil.which, local_app_data=None):
    name = 'codex.exe' if IS_WINDOWS else 'codex'
    candidates = []

    # The npm package is a JavaScript entry point over a vendored native binary per platform, and the entry
    # point is what lands on PATH. Launching that shim is the path that degrades the TUI to monochrome and
    # non-interactive, so the vendored executable underneath it is launched instead - identical bits,
    # without the node process in front. Windows npm puts the shim beside node_modules; POSIX npm symlinks
    # bin/codex to the package's own bin/codex.js, two levels below the package root.
    shim = which('codex')
    if shim:
        roots = [
            Path(shim).parent / 'node_modules' / '@openai' / 'codex',
            Path(os.path.realpath(shim)).parent.parent,
        ]
        for root in dict.fromkeys(roots):
            pattern = str(root / 'node_modules' / '@openai' / 'codex-*' / 'vendor' / '*' / 'bin' / name)
            candidates.extend(sorted(glob.glob(pattern)))

    # The Windows desktop app caches each downloaded runtime in its own hash-named directory and adds rather
    # than replaces, so this folder accumulates stale payloads instead of holding only the current build.
    # There is no desktop app cache anywhere else.
    if IS_WINDOWS:
        local_app_data = local_app_data or os.environ.get('LOCALAPPDATA')
        if local_app_data:
            desktop = Path(local_app_data) / 'OpenAI' / 'Codex' / 'bin'
            candidates.extend(sorted(str(p) for p in desktop.rglob('codex.exe') if p.is_file()))

    return list(dict.fromkeys(candidates))


def resolve_codex_executable(minimum='0.154.0', candidates=None):
    """The newest native Codex executable that answers --version, as (path, version)."""
    paths = codex_candidate_paths() if candidates is None else candidates
    found = []
    for path in paths:
        try:
            result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            continue
        version = parse_codex_version(result.stdout + result.stderr)
        if version:
            found.append((path, version))

    if not found:
        raise LaunchError(
            'No native Codex executable answered --version. Looked beside the `codex` shim on PATH for the npm '
            "package's vendored binary" + (', and under the desktop app cache.' if IS_WINDOWS else '.')
        )

    best = found[0]
    for candidate in found[1:]:
        if compare_codex_version(candidate[1], best[1]) > 0:
            best = candidate

    floor = parse_codex_version(minimum)
    if floor is None:
        raise LaunchError(f'The minimum Codex version is not a version: {minimum}')
    if compare_codex_version(best[1], floor) < 0:
        inventory = '\n'.join(f'  {version["text"]}\t{path}' for path, version in found)
        raise LaunchError(
            f'The newest native Codex executable found is {best[1]["text"]}, below the required {minimum}.\n'
            'The model roster is gated on the CLI version, so launching this build would silently drop newer models.\n'
            'Update with: npm install -g @openai/codex@latest\n'
            f'Found:\n{inventory}'
        )
    return best


def claude_config_dir():
    configured = os.environ.get('CLAUDE_CONFIG_DIR')
    return Path(configured) if configured else Path.home() / '.claude'


def standards_sync_script():
    """The user-installed machine plugin's sync script, else the copy beside this file."""
    plugins = os.environ.get('CLAUDE_CODE_PLUGIN_CACHE_DIR')
    plugins = Path(plugins) if plugins else claude_config_dir() / 'plugins'
    candidates = []
    try:
        with open(plugins / 'installed_plugins.json', encoding='utf-8-sig') as f:
            registry = json.load(f)
        for entry in (registry.get('plugins') or {}).get('machine@base-agents') or []:
            if entry.get('scope') == 'user' and entry.get('installPath'):
                candidates.append(Path(entry['installPath']) / 'resources' / 'machine' / 'scripts' / 'claude_standards_sync.py')
    except (OSError, ValueError, AttributeError):
        pass
    candidates.append(HERE / 'claude_standards_sync.py')
    return next((path for path in candidates if path.is_file()), None)


def sync_claude_standards(working_directory, claude=None, out=print):
    """Refresh the registered standards before a Claude session opens. Never blocks the launch."""
    script = standards_sync_script()
    if script is None:
        out('standards: claude_standards_sync.py was not found; this session loads the installed plugins')
        return
    arguments = [sys.executable, '-B', str(script), '--project', str(working_directory)]
    if claude:
        arguments += ['--claude', str(claude)]
    result = subprocess.run(arguments, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in result.stdout.splitlines():
        out(line)


def _lanes_module():
    # .agents/lanes in the authored layout, resources/lanes in the packaged one: the same hop from here.
    path = HERE.parent.parent / 'lanes' / 'resolve.py'
    if not path.is_file():
        raise LaunchError(f'The lane resolver was not found at {path}.')
    spec = importlib.util.spec_from_file_location('agent_cli_lanes', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Lane -> model for a chosen harness, from the canonical lane tables, the repo's only model-name owner.
# Resolution never picks the lane: a caller that supplies neither a lane nor a model gets the CLI's own
# configured default, because guessing a lane from a prompt is how an expensive model ends up serving a
# rename. frontier resolves the tier above the ladder, which no lane resolves to: its selection is the
# user's explicit request, never task shape.
def resolve_lane_model(harness, lane=None, frontier=False):
    """(model, effort) for a lane or the frontier tier; effort is None when the table prices none."""
    if not lane and not frontier:
        raise LaunchError('resolve_lane_model needs a lane or frontier.')
    if lane and frontier:
        raise LaunchError('A lane and the frontier tier are mutually exclusive.')
    lanes = _lanes_module()
    try:
        entry = lanes.frontier(harness) if frontier else lanes.resolve(harness, lane)
    except SystemExit as exc:
        raise LaunchError(str(exc)) from None
    return entry['model'], entry.get('effort')


# Windows Terminal mangles argument values on the way to the tab process, and does it silently. It splits
# its own command line on `;` into subcommands, so an unescaped semicolon in a prompt truncates the prompt
# and turns the remainder into a bogus program; the tab still opens, which is what made the loss invisible.
# It then re-joins the remaining args into one child command line, quoting an arg only when that arg
# contains a space and escaping nothing inside it, and the tab process re-parses that string by
# CommandLineToArgvW rules. So a quote is eaten, and a trailing backslash in a spaced value escapes the
# closing quote and swallows the next argument whole.
def terminal_argument(value):
    # Windows Terminal quotes on a space and nothing else, so a line break or tab in a value with no space
    # is dropped outright and no escape can carry it. A refused launch beats a silently shortened prompt.
    if re.search(r'[\r\n\t]', value) and ' ' not in value:
        raise LaunchError(
            f'Windows Terminal cannot carry a line break or tab in an argument containing no space, and would drop it: {value}'
        )

    # An empty value has no space to be quoted for, so Windows Terminal drops it and every later argument
    # shifts into its place.
    if not value:
        raise LaunchError('Windows Terminal cannot carry an empty argument, and would shift the next one into its place.')

    quoted = ' ' in value
    parts = []
    backslashes = 0
    for character in value:
        if character == '\\':
            backslashes += 1
            continue
        if character == '"':
            parts.append('\\' * (2 * backslashes + 1) + '"')
        else:
            parts.append('\\' * backslashes + character)
        backslashes = 0
    parts.append('\\' * (2 * backslashes if quoted else backslashes))

    # Escaped last, because Windows Terminal strips exactly one backslash before a semicolon, so this must
    # be the outermost layer for a value that legitimately ends a run of backslashes at a semicolon.
    return ''.join(parts).replace(';', '\\;')


def posix_inner_command(directory, cleared, forced, executable, arguments):
    """The argv a POSIX tab handler starts: change into <directory>, scrub the environment, exec.

    Never a shell string built from the caller's values -- each piece travels as its own argv element, so a
    prompt with quotes, `;`, `$`, backslashes or a newline reaches the executable unparsed by any shell.
    """
    env_args = []
    for name in cleared:
        env_args += ['-u', name]
    env_args += [f'{name}={value}' for name, value in forced.items()]
    return ['sh', '-c', 'cd "$1" && shift && exec "$@"', 'sh', str(directory), 'env', *env_args, executable, *arguments]


def _launch_tmux(directory, executable, title, arguments, cleared, forced, environ, run, popen):
    inner = posix_inner_command(directory, cleared, forced, executable, arguments)
    # Passing several argv elements after `--` is what makes tmux 3.0+ exec them directly without an
    # intermediate shell; a single joined string would be re-split by tmux's own command parser.
    result = run(['tmux', 'new-window', '-d', '-n', title, '--', *inner],
                 stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise LaunchError(f'tmux new-window failed: {(result.stderr or result.stdout).strip()}')


def _launch_kitty(directory, executable, title, arguments, cleared, forced, environ, run, popen):
    listen_on = environ.get('KITTY_LISTEN_ON')
    if not listen_on:
        raise LaunchError(
            'kitty remote control is not reachable: KITTY_LISTEN_ON is not set. Add '
            "'allow_remote_control socket-only' and 'listen_on unix:/tmp/kitty-{kitty_pid}' to kitty.conf "
            'and restart kitty.'
        )
    window_id = environ.get('KITTY_WINDOW_ID', '')
    inner = posix_inner_command(directory, cleared, forced, executable, arguments)
    command = ['kitty', '@', '--to', listen_on, 'launch', '--type=tab', '--match', f'id:{window_id}',
               '--tab-title', title, *inner]
    result = run(command, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise LaunchError(f'kitty @ launch failed: {(result.stderr or result.stdout).strip()}')


def _konsole_qdbus():
    return shutil.which('qdbus6') or shutil.which('qdbus')


def _launch_konsole(directory, executable, title, arguments, cleared, forced, environ, run, popen):
    qdbus = _konsole_qdbus()
    if not qdbus:
        raise LaunchError('Neither qdbus6 nor qdbus was found on PATH to drive Konsole over D-Bus.')
    service = environ.get('KONSOLE_DBUS_SERVICE')
    window = environ.get('KONSOLE_DBUS_WINDOW')
    if not service or not window:
        raise LaunchError('KONSOLE_DBUS_SERVICE or KONSOLE_DBUS_WINDOW is not set.')

    def call(*args):
        result = run([qdbus, *args], stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise LaunchError(f'{qdbus} {" ".join(args)} failed: {(result.stderr or result.stdout).strip()}')
        return result.stdout.strip()

    session = call(service, window, 'newSession')
    call(service, f'/Sessions/{session}', 'setTitle', '1', title)

    # runCommand TYPES this text into the user's own interactive shell, which may not be sh (it may be
    # fish), so the inner command never travels as that text: it is written to a private sh script whose
    # first line deletes it, and the only thing typed is `exec sh '<path>'`.
    inner = posix_inner_command(directory, cleared, forced, executable, arguments)
    script_path = _write_posix_script(inner)
    call(service, f'/Sessions/{session}', 'runCommand', f'exec sh {shlex.quote(str(script_path))}')


def _write_posix_script(inner):
    temp_dir = tempfile.mkdtemp(prefix='agent-cli-tab-')
    script_path = Path(temp_dir) / 'launch.sh'
    script_path.write_text('rm -f "$0"\n' + shlex.join(inner) + '\n')
    script_path.chmod(0o700)
    return script_path


def _launch_windows_terminal(directory, executable, title, arguments, cleared, forced, environ, run, popen):
    terminal = shutil.which('wt.exe')
    if not terminal:
        raise LaunchError('wt.exe was not found on PATH.')

    # --window 0 is WT's documented sentinel for "the window that most recently had focus". This is not
    # the same as omitting the flag: windowingBehavior is unset by default, so no flag at all means
    # useNew -- always a separate OS window. Do not simplify this away, and do not swap it for
    # --window new, which forces the opposite of what it looks like it asks for.
    terminal_arguments = ['--window', '0', 'new-tab', '--startingDirectory', str(directory), '--title', title,
                           '--suppressApplicationTitle', executable, *arguments]
    escaped = [terminal_argument(value) for value in terminal_arguments]

    # The environment changes travel through the subprocess's own `env=`, never by mutating this
    # process's environment: wt.exe only relays the tab's command line, so the tab process never sees
    # anything set here, and the parent session must not be left mutated either way.
    env = dict(environ)
    for name in cleared:
        env.pop(name, None)
    env.update(forced)

    result = run([terminal, *escaped], env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise LaunchError(f'Windows Terminal exited with code {result.returncode}: {(result.stderr or result.stdout).strip()}')


# Checked in this order because it is the order a launcher process could be nested in another: tmux
# inside kitty inside Konsole inside Windows Terminal sees TMUX first, so the innermost multiplexer the
# caller is actually attached to wins over an outer terminal emulator it happens to also be running in.
_TAB_HANDLERS = (
    ('TMUX', _launch_tmux),
    ('KITTY_WINDOW_ID', _launch_kitty),
    ('KONSOLE_DBUS_WINDOW', _launch_konsole),
    ('WT_SESSION', _launch_windows_terminal),
)


def _launch_new_window(directory, executable, title, arguments, cleared, forced, environ, run, popen):
    print('warning: no terminal was detected; opening a new window instead of a tab', file=sys.stderr)

    if IS_WINDOWS:
        wt = shutil.which('wt.exe')
        if wt:
            return _launch_windows_terminal(directory, executable, title, arguments, cleared, forced, environ, run, popen)

        env = dict(environ)
        for name in cleared:
            env.pop(name, None)
        env.update(forced)
        try:
            popen([executable, *arguments], cwd=str(directory), env=env, creationflags=subprocess.CREATE_NEW_CONSOLE)
        except OSError as exc:
            raise LaunchError(f'Could not open a new console window: {exc}') from exc
        return

    inner = posix_inner_command(directory, cleared, forced, executable, arguments)
    candidates = []
    terminal_env = environ.get('TERMINAL')
    if terminal_env:
        candidates.append([terminal_env, '-e', *inner])
    candidates.append(['kitty', '--title', title, *inner])
    candidates.append(['konsole', '--workdir', str(directory), '-e', *inner])
    candidates.append(['xterm', '-e', *inner])

    for candidate in candidates:
        if not shutil.which(candidate[0]):
            continue
        try:
            popen(candidate, start_new_session=True,
                  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except OSError:
            continue

    raise LaunchError('No terminal was detected and no terminal emulator was found on PATH to open a new window.')


def launch_tab(working_directory, executable, title, arguments=(), clear=(), force=None,
               environ=os.environ, run=subprocess.run, popen=subprocess.Popen):
    """Open <executable> <arguments> as a new tab in the terminal this process is already running inside.

    Detects the terminal from its own environment variables and uses its native new-tab command. Only
    with no terminal detected does this open a new window, with a warning -- a tab is the contract every
    caller relies on. A detected handler that fails raises rather than falling back to a window: a silent
    new window is a worse surprise than a loud failure.
    """
    directory = Path(working_directory)
    if not directory.is_dir():
        raise LaunchError(f'Working directory is not a directory: {working_directory}')

    clear = list(clear)
    force = dict(force or {})
    if not IS_WINDOWS:
        # The terminal that starts the tab sets TERM for that session itself; forcing or clearing it here
        # would fight that.
        clear = [name for name in clear if name != 'TERM']
        force.pop('TERM', None)

    cleared, forced = launch_environment(clear=clear, force=force)
    # The tab title is the only name for this session the user can see on screen, so the session records
    # it at SessionStart and peer-cli resolves by it.
    forced = dict(forced)
    forced['AGENT_CLI_TAB_TITLE'] = title
    arguments = list(arguments)

    for name, handler in _TAB_HANDLERS:
        if environ.get(name):
            return handler(directory, executable, title, arguments, cleared, forced, environ, run, popen)

    return _launch_new_window(directory, executable, title, arguments, cleared, forced, environ, run, popen)
