# Code conventions

Read these conventions before changing runtime scripts, hook wiring, or launchers.

Use the language and runtime appropriate to the repository and host; for this repository's shipped code,
that is set by [Supported platforms](#supported-platforms). Assess the execution mechanism,
inputs and trust boundary when choosing a safe implementation.

Prefer ordinary function calls, imports, script files and structured APIs over executing source-code
strings with `exec`, `eval` or `Invoke-Expression`. Use dynamic execution only when a documented requirement
cannot reasonably be met through those alternatives. Never execute untrusted input as source code.

Launch processes with an argument list and without a shell where the platform supports it. Use a shell
only when required shell behavior cannot be expressed through ordinary process or filesystem APIs.
Do not encode executable source as Base64 to work around quoting or command limits.

Keep launch commands readable and their trust boundaries explicit. Trusting a command does not necessarily
authenticate the file it references. Validate inputs and authenticate executable dependencies where the
required integrity boundary depends on them; fail clearly when verification fails.

Use standard libraries and explicit prerequisites. Resolve repository-owned dependencies relative to the
installed package. Do not rely on an unshipped machine-local helper.

## Supported platforms

Everything this repository ships runs on Windows and Linux: skill scripts, hooks, launchers, and the
tests that cover them. macOS is best effort. A change that works on only one of Windows and Linux is
incomplete.

- New shipped runtime code is Python using the standard library. Do not add a PowerShell script for
  shipped behaviour. The one exception is behaviour that exists only on Windows, such as Windows
  Terminal UI Automation. Run it through Windows' built-in `powershell.exe`, called from a Python entry
  point that has its own Linux path.
- Existing shipped PowerShell scripts are being ported; see
  [`plans/linux-port/LINUX_PORT_PLAN.md`](plans/linux-port/LINUX_PORT_PLAN.md). Do not add behaviour
  to one. Port it, or add the behaviour to its Python replacement. Until a skill is ported, its SKILL.md
  states that it is Windows-only, and its Windows commands are not presented as universal.
- Skill and workflow instructions name the interpreter per platform: `python3` on Linux and macOS,
  `python` on Windows, where `python3` is usually the Microsoft Store alias stub. Never tell an agent
  to run `powershell.exe`, `pwsh` or `wt.exe` without saying which platform the instruction is for.
- Open terminal tabs through `agent_cli.launch_tab` (Windows Terminal, tmux, kitty, Konsole), never by
  calling a terminal program directly.
- Find the home directory with `Path.home()`. Gate Windows-only locations such as `LOCALAPPDATA` behind
  a platform check. POSIX executables have no `.exe`.
- CI runs `verify-windows` on Windows and `verify-linux` on Linux. A test that only one platform can run gives
  a skip reason, and the behaviour it covers also has a test on the other platform. Tests whose
  behaviour differs by platform pin the platform explicitly.

Repository tooling (`.agents/sync-generated.ps1`, `.codex/install-workflow-agents.ps1`) may use PowerShell 7
(`pwsh`), but it must run under `pwsh` on Linux as well as on Windows. `shell/`, `install.ps1` and
`cli-session-recovery/` are the Windows PowerShell profile and its tools, and are Windows-only by
design.

## Python and portability

Follow [PEP 8](https://peps.python.org/pep-0008/) with clear names and small, cohesive functions. Declare the
minimum supported Python version for each utility and fail with an actionable message when it is unavailable.

Use `pathlib` or `os.path` to compose filesystem paths. Resolve shipped resources relative to the script or
an explicit package root. Avoid hardcoded drive letters, usernames, separators and assumptions about the
caller's working directory.

Specify encodings for text files and subprocess output; use UTF-8 for repository-owned text. Choose newline
handling deliberately when editing existing files or computing integrity hashes.

Use `subprocess` argument lists with `shell=False` for ordinary process launches. Use `sys.executable` when
starting another Python process that should use the same interpreter. Check exit status and set timeouts
where a stalled child would block the caller indefinitely. Keep shell invocation limited to an actual host
integration requirement.

Keep platform-specific APIs behind explicit platform checks and import them only on supported platforms.
Do not assume PowerShell, cmd.exe, Bash, Windows registry APIs or executable filename extensions exist on
every host. Verify shared runtime behavior on Windows and Linux, including paths containing spaces and
non-ASCII text; use disposable directories for filesystem and configuration tests.

## Security controls and comments

Do not bypass security controls to make code run. Investigate a blocked command and validate its replacement;
source tests do not establish antivirus acceptance.

Default to no code comments. Names express behavior; commit messages carry design decisions. Add a
comment only for a non-obvious invariant, upstream workaround, or legacy constraint needed at that line.

References: [Python dynamic execution](https://docs.python.org/3/library/functions.html#exec),
[Python process security](https://docs.python.org/3/library/subprocess.html#security-considerations),
and [PowerShell's AvoidUsingInvokeExpression rule](https://learn.microsoft.com/en-us/powershell/utility-modules/psscriptanalyzer/rules/avoidusinginvokeexpression).
