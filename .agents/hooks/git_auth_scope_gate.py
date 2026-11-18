r"""PreToolUse hook: an agent never widens the account's credential.

The mistake this exists to make impossible: a `gh api` call is refused for lack of
permission, and the agent reaches for `gh auth refresh -h github.com -s admin:org`
to clear it. Classic OAuth scopes are **account-wide**. That command does not grant
"admin on the organization being worked on" — it grants organization administration
across every organization the account belongs to, employers' included, to read one
setting in one of them. It is the widest possible answer to the narrowest possible
question, and it is irreversible from the agent's side: only the human can revoke it.

So the whole command family is refused, not just the scope flags. There is no
legitimate reason for an agent to authenticate on the human's behalf, and matching on
`-s` / `--scopes` would miss scopes that arrive through a variable or a heredoc.
Authentication is the human's action; the agent's job is to ask for the narrow
credential and say exactly what it needs. The `git-auth` skill is the procedure.

What is allowed, so ordinary work is never in the way: every other `gh auth`
subcommand — `status`, `token`, `setup-git`, `switch` — reads or selects a credential
that already exists and widens nothing. `gh auth login --help`, which executes nothing.
Every non-`gh` command. Every `gh api` call, including the one that was refused: a 403
is a finding to report, not a thing to escalate around.

Two failure directions, deliberately different:

* **Recognising** the command fails OPEN. An unparseable payload, an unknown shape, a
  tool this gate does not understand — allow, because a credential gate that wedges
  unrelated shell calls gets switched off, and then it protects nothing.
* **Refusing** a command already identified fails CLOSED. Once the pattern matches, no
  later exception may turn a confirmed `gh auth refresh -s admin:org` into a silent
  allow. This gate's failure mode is the only irreversible one here, so the two stages
  do not share an exception handler.

Residual risk this cannot see, stated rather than implied. A shell can hide the token
pair from any regex: `gh auth $(echo refresh)`, or `powershell -EncodedCommand <base64>`,
which arrives already opaque. And the credential can be installed without `gh auth` at
all, by writing `~/.config/gh/hosts.yml` (`%APPDATA%\GitHub CLI\hosts.yml`) directly —
this gate wires only to shell tools, never to `Write`/`Edit`, so that path is outside its
jurisdiction entirely. None of these is what a careless agent reaches for, which is what
this gate is for; a determined one was never going to be stopped by a matcher.

Wired for BOTH harnesses. Claude's matcher is ``Bash|PowerShell``; Codex's is
``exec_command|unified_exec|local_shell|shell``. A ``command`` arriving as an argv
list (``["bash","-lc",...]``), or under ``cmd`` / ``script`` / ``input`` /
``action.command``, is unwrapped.

No opt-in file. Every other gate here is per-repo policy a repo may reasonably decline;
this one is a property of the human's account, identical in every repo, and a repo that
had forgotten to opt in is exactly where the mistake would land.

Contract: exit 0 = allow; exit 2 = block (stderr is fed back to the agent).
"""

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from hook_runtime import claim_invocation

# This message is what the agent acts on, and Windows defaults these streams to cp1252.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

HOOK_NAME = "git-auth-scope-gate"

# Lowercased. A shell tool not named here cannot be wired to this gate, because a matcher the
# hook ignores is enforcement that is inert while looking wired.
SHELL_TOOLS = {"bash", "powershell", "shell", "exec_command", "unified_exec", "local_shell"}

BASH_SHORT_FLAGS = frozenset("abefhikmnprtuvxBCEHPTlsD")
BASH_O_OPTIONS = frozenset(
    "allexport braceexpand emacs errexit errtrace functrace hashall histexpand history "
    "ignoreeof interactive-comments keyword monitor noclobber noexec noglob nolog notify "
    "nounset onecmd physical pipefail posix privileged verbose vi xtrace igncr".split()
)
BASH_O_CAP_OPTIONS = frozenset(
    "autocd assoc_expand_once cdable_vars cdspell checkhash checkjobs checkwinsize cmdhist "
    "compat31 compat32 compat40 compat41 compat42 compat43 compat44 completion_strip_exe "
    "complete_fullquote direxpand dirspell dotglob execfail expand_aliases extdebug extglob "
    "extquote failglob force_fignore globasciiranges globskipdots globstar gnu_errfmt histappend "
    "histreedit histverify hostcomplete huponexit inherit_errexit interactive_comments lastpipe "
    "lithist localvar_inherit localvar_unset login_shell mailwarn no_empty_cmd_completion nocaseglob "
    "nocasematch noexpand_translation nullglob patsub_replacement progcomp progcomp_alias promptvars "
    "restricted_shell shift_verbose sourcepath varredir_close xpg_echo".split()
)
BASH_LONG_FLAGS = frozenset(
    "debug debugger dump-po-strings dump-strings login noediting noprofile norc posix pretty-print "
    "protected restricted verbose wordexp".split()
)
BASH_LONG_EXIT_FLAGS = frozenset(("help", "version"))
BASH_LONG_VALUE_FLAGS = frozenset(("init-file", "rcfile"))
DASH_SHORT_FLAGS = frozenset("efIimnsxvVECabupl")
DASH_O_OPTIONS = frozenset(
    "errexit noglob ignoreeof interactive monitor noexec stdin xtrace verbose vi emacs noclobber "
    "allexport notify nounset nolog pipefail debug priv".split()
)
ZSH_NAMES = frozenset(
    "aliases aliasfuncdef allexport alwayslastprompt alwaystoend appendcreate appendhistory autocd "
    "autocontinue autolist automenu autonamedirs autoparamkeys autoparamslash autopushd autoremoveslash "
    "autoresume badpattern banghist bareglobqual bashautolist bashrematch beep bgnice braceccl bsdecho "
    "caseglob casematch casepaths cbases cprecedences cdablevars cdsilent chasedots chaselinks checkjobs "
    "checkrunningjobs clobber clobberempty combiningchars completealiases completeinword continueonerror "
    "correct correctall cshjunkiehistory cshjunkieloops cshjunkiequotes cshnullcmd cshnullglob debugbeforecmd "
    "emacs equals errexit errreturn exec extendedglob extendedhistory evallineno flowcontrol forcefloat "
    "functionargzero glob globalexport globalrcs globassign globcomplete globdots globstarshort globsubst "
    "hashcmds hashdirs hashexecutablesonly hashlistall histallowclobber histbeep histexpiredupsfirst "
    "histfcntllock histfindnodups histignorealldups histignoredups histignorespace histlexwords histnofunctions "
    "histnostore histsubstpattern histreduceblanks histsavebycopy histsavenodups histverify hup ignorebraces "
    "ignoreclosebraces ignoreeof incappendhistory incappendhistorytime interactive interactivecomments ksharrays "
    "kshautoload kshglob kshoptionprint kshtypeset kshzerosubscript listambiguous listbeep listpacked "
    "listrowsfirst listtypes localoptions localloops localpatterns localtraps login longlistjobs magicequalsubst "
    "mailwarning markdirs menucomplete monitor multibyte multifuncdef multios nomatch notify nullglob "
    "numericglobsort octalzeroes overstrike pathdirs pathscript pipefail posixaliases posixargzero posixbuiltins "
    "posixcd posixidentifiers posixjobs posixstrings posixtraps printeightbit printexitvalue privileged promptbang "
    "promptcr promptpercent promptsp promptsubst pushdignoredups pushdminus pushdsilent pushdtohome rcexpandparam "
    "rcquotes rcs recexact rematchpcre restricted rmstarsilent rmstarwait sharehistory shfileexpansion shglob "
    "shinstdin shnullcmd shoptionletters shortloops shortrepeat shwordsplit singlecommand singlelinezle sourcetrace "
    "sunkeyboardhack transientrprompt trapsasync typesetsilent typesettounset unset verbose vi warncreateglobal "
    "warnnestedvar xtrace zle braceexpand dotglob hashall histappend histexpand log mailwarn onecmd physical "
    "promptvars stdin trackall dvorak".split()
)
ZSH_LETTERS = frozenset("0123456789BCDEFGHIJKLMNOPQRSTUVWXYZadefghiklmnprstuvwxyz")
ZSH_KSH_LETTERS = frozenset("CTXa befilmnprstuvx".replace(" ", ""))
POWER_ENUMS = {
    "executionpolicy": frozenset("default remotesigned bypass allsigned restricted unrestricted undefined".split()),
    "inputformat": frozenset(("text", "xml")),
    "outputformat": frozenset(("text", "xml")),
    "windowstyle": frozenset("normal minimized maximized hidden".split()),
}


@dataclass(frozen=True)
class ScriptResult:
    kind: str
    index: int = -1
    script: str = ""
    reason: str = ""


def _literal(parts, index, script=None):
    return ScriptResult("literal", index, parts[index] if script is None else script)


def _result_after_options(parts, index, command_requested, input_kind):
    if command_requested:
        return _literal(parts, index) if index < len(parts) else ScriptResult("reject", reason="missing-script")
    return ScriptResult(input_kind)


def _indeterminate(reason="unsupported-option"):
    return ScriptResult("indeterminate", reason=reason)


def _bash_result(parts):
    index = 1
    command_requested = False
    short_phase = False
    while index < len(parts):
        token = parts[index]
        if token in ("-", "--"):
            return _result_after_options(parts, index + 1, command_requested, "stdin")
        if token == "+":
            index += 1
            continue
        if not short_phase and token.startswith("-") and token != "-":
            name = token[2:] if token.startswith("--") else token[1:]
            if name in BASH_LONG_EXIT_FLAGS:
                return ScriptResult("exit")
            if name in BASH_LONG_FLAGS:
                index += 1
                continue
            if name in BASH_LONG_VALUE_FLAGS:
                if index + 1 >= len(parts):
                    return ScriptResult("reject", reason="missing-option-value")
                index += 2
                continue
            if token.startswith("--") or "=" in name:
                return _indeterminate()
        if token[:1] not in ("-", "+") or len(token) == 1:
            return _result_after_options(parts, index, command_requested, "file")
        short_phase = True
        cursor = index + 1
        for flag in token[1:]:
            if flag == "-":
                return _indeterminate()
            if flag in ("c", "l", "s"):
                command_requested = True
                continue
            if flag in BASH_SHORT_FLAGS:
                continue
            if flag in ("o", "O"):
                if cursor >= len(parts):
                    continue
                value = parts[cursor]
                if value not in (BASH_O_OPTIONS if flag == "o" else BASH_O_CAP_OPTIONS):
                    return _indeterminate("unsupported-option-value")
                cursor += 1
                continue
            return _indeterminate()
        index = cursor
    return ScriptResult("reject", reason="missing-script") if command_requested else ScriptResult("file")


def _dash_result(parts):
    index = 1
    command_requested = False
    while index < len(parts):
        token = parts[index]
        if token in ("-", "--"):
            return _result_after_options(parts, index + 1, command_requested, "stdin")
        if token == "+":
            index += 1
            continue
        if token[:1] not in ("-", "+") or len(token) == 1:
            return _result_after_options(parts, index, command_requested, "file")
        cursor = index + 1
        for flag in token[1:]:
            if flag == "-":
                return _indeterminate()
            if flag in ("c", "l"):
                command_requested = True
            elif flag in DASH_SHORT_FLAGS:
                continue
            elif flag == "o":
                if cursor >= len(parts):
                    continue
                if parts[cursor] not in DASH_O_OPTIONS:
                    return _indeterminate("unsupported-option-value")
                cursor += 1
            else:
                return _indeterminate()
        index = cursor
    return ScriptResult("reject", reason="missing-script") if command_requested else ScriptResult("file")


def _zsh_name(value, long_form=False):
    name = value.replace("_", "").casefold()
    if long_form:
        name = name.replace("-", "")
    negative = name.startswith("no") and name[2:] in ZSH_NAMES
    return name[2:] if negative else name


def _zsh_result(parts):
    index = 1
    command_requested = False
    optionbreak = False
    emulate_required = True
    sh_option_letters = False
    requested_mode = "z"

    def initialize_emulation():
        nonlocal emulate_required, sh_option_letters
        if emulate_required:
            sh_option_letters = requested_mode in ("s", "b", "k")
            emulate_required = False

    while index < len(parts):
        token = parts[index]
        if token in ("-", "+", "--", "+-"):
            return _result_after_options(parts, index + 1, command_requested, "stdin")
        if token.startswith(("--", "+-")):
            name = token[2:]
            if name in ("help", "version"):
                return ScriptResult("exit")
            if name == "emulate":
                if index + 1 >= len(parts):
                    return ScriptResult("reject", reason="missing-option-value")
                if not emulate_required:
                    return ScriptResult("reject", reason="late-emulate")
                requested_mode = parts[index + 1].lstrip("r").casefold()[:1]
                index += 2
                continue
            if "=" in name or _zsh_name(name, long_form=True) not in ZSH_NAMES:
                return _indeterminate("unsupported-option-value" if "=" in name else "unsupported-option")
            normalized = _zsh_name(name, long_form=True)
            initialize_emulation()
            if normalized == "shoptionletters":
                sh_option_letters = not name.casefold().startswith("no")
            emulate_required = False
            index += 1
            continue
        if token[:1] not in ("-", "+") or len(token) == 1:
            return _result_after_options(parts, index, command_requested, "file")
        letters = token[1:]
        cursor = index + 1
        position = 0
        while position < len(letters):
            flag = letters[position]
            if flag == "-":
                if position != len(letters) - 1:
                    return ScriptResult("reject", reason="malformed-group")
                return _result_after_options(parts, cursor, command_requested, "stdin")
            if flag == "b" and not sh_option_letters:
                emulate_required = False
                optionbreak = True
                position += 1
                continue
            if flag == "c":
                initialize_emulation()
                command_requested = True
                position += 1
                continue
            if flag == "o":
                value = letters[position + 1:] or (parts[cursor] if cursor < len(parts) else "")
                if not value:
                    return ScriptResult("reject", reason="missing-option-value")
                initialize_emulation()
                normalized = _zsh_name(value)
                if normalized not in ZSH_NAMES:
                    return _indeterminate("unsupported-option-value")
                if normalized == "shoptionletters":
                    sh_option_letters = not value.casefold().startswith("no")
                emulate_required = False
                if position + 1 == len(letters):
                    cursor += 1
                position = len(letters)
                continue
            known = ZSH_KSH_LETTERS if sh_option_letters else ZSH_LETTERS
            if flag not in known:
                return _indeterminate()
            initialize_emulation()
            position += 1
        index = cursor
        if optionbreak:
            return _result_after_options(parts, index, command_requested, "file")
    return ScriptResult("reject", reason="missing-script") if command_requested else ScriptResult("file")


def _sh_result(parts):
    results = (_bash_result(parts), _dash_result(parts), _zsh_result(parts))
    if any(result.kind == "indeterminate" for result in results):
        return _indeterminate("unresolved-profile")
    viable = [result for result in results if result.kind != "reject"]
    literals = [result for result in viable if result.kind == "literal"]
    if not literals:
        return ScriptResult("file")
    first = literals[0]
    if (
        len(literals) != len(viable)
        or any((result.index, result.script) != (first.index, first.script) for result in literals)
    ):
        return ScriptResult("ambiguous")
    return first


def _option_name(token, shell):
    if token.startswith("--"):
        return token[2:].casefold()
    if token.startswith(("-", "/")):
        return token[1:].casefold()
    return ""


def _descriptor(canonical, minimum, kind, aliases=()):
    return canonical, minimum, kind, frozenset(aliases)


COMMON_DESCRIPTORS = (
    _descriptor("noexit", "noe", "boolean"),
    _descriptor("noprofile", "nop", "boolean"),
    _descriptor("nologo", "nol", "boolean"),
    _descriptor("noninteractive", "noni", "boolean"),
    _descriptor("configurationname", "config", "value"),
    _descriptor("windowstyle", "w", "enum:windowstyle"),
    _descriptor("outputformat", "o", "enum:outputformat", ("of",)),
    _descriptor("inputformat", "inp", "enum:inputformat", ("if",)),
    _descriptor("executionpolicy", "ex", "enum:executionpolicy", ("ep",)),
    _descriptor("encodedarguments", "encodeda", "value", ("ea",)),
    _descriptor("sta", "sta", "boolean"),
    _descriptor("mta", "mta", "boolean"),
)
PWSH_DESCRIPTORS = (
    _descriptor("version", "v", "exit"),
    _descriptor("help", "h", "exit", ("?",)),
    _descriptor("login", "l", "boolean"),
    *COMMON_DESCRIPTORS[:4],
    _descriptor("socketservermode", "so", "stdin"),
    _descriptor("v2socketservermode", "v2so", "stdin"),
    _descriptor("servermode", "s", "stdin"),
    _descriptor("namedpipeservermode", "nam", "stdin"),
    _descriptor("sshservermode", "sshs", "stdin"),
    _descriptor("noprofileloadtime", "noprofileloadtime", "boolean"),
    _descriptor("interactive", "i", "boolean"),
    _descriptor("configurationfile", "configurationfile", "value"),
    COMMON_DESCRIPTORS[4],
    _descriptor("custompipename", "cus", "value"),
    _descriptor("commandwithargs", "commandwithargs", "cwa", ("cwa",)),
    _descriptor("command", "c", "command"),
    COMMON_DESCRIPTORS[5],
    _descriptor("file", "f", "file"),
    _descriptor("isswait", "isswait", "boolean"),
    *COMMON_DESCRIPTORS[6:9],
    _descriptor("encodedcommand", "e", "opaque", ("ec",)),
    COMMON_DESCRIPTORS[9],
    _descriptor("settingsfile", "settings", "value"),
    *COMMON_DESCRIPTORS[10:],
    _descriptor("workingdirectory", "wo", "value", ("wd",)),
    _descriptor("removeworkingdirectorytrailingcharacter", "removeworkingdirectorytrailingcharacter", "boolean"),
    _descriptor("token", "to", "value"),
    _descriptor("utctimestamp", "utc", "value"),
)
WINDOWS_DESCRIPTORS = (
    _descriptor("help", "h", "exit", ("?",)),
    *COMMON_DESCRIPTORS[:4],
    COMMON_DESCRIPTORS[4],
    _descriptor("psconsolefile", "psconsolefile", "value"),
    _descriptor("version", "v", "value"),
    _descriptor("command", "c", "command"),
    COMMON_DESCRIPTORS[5],
    _descriptor("file", "f", "file"),
    *COMMON_DESCRIPTORS[6:],
    _descriptor("encodedcommand", "e", "opaque", ("ec",)),
)


def _match_descriptor(name, descriptors):
    for canonical, minimum, kind, aliases in descriptors:
        if name in aliases or (len(name) >= len(minimum) and canonical.startswith(name)):
            return kind
    return None


def _powershell_result(parts, shell):
    index = 1
    descriptors = PWSH_DESCRIPTORS if shell == "pwsh" else WINDOWS_DESCRIPTORS
    while index < len(parts):
        token = parts[index]
        name = _option_name(token, shell)
        if not name:
            return ScriptResult("file") if shell == "pwsh" else _literal(parts, index, " ".join(parts[index:]))
        kind = _match_descriptor(name, descriptors)
        if kind is None:
            return _indeterminate()
        if kind == "exit":
            return ScriptResult("exit")
        if kind in ("file", "stdin"):
            return ScriptResult("stdin") if index + 1 < len(parts) and parts[index + 1] == "-" else ScriptResult("file")
        if kind == "opaque":
            if index + 1 >= len(parts):
                return ScriptResult("reject", reason="missing-option-value")
            return ScriptResult("opaque")
        if kind == "command":
            if index + 1 >= len(parts):
                return ScriptResult("reject", reason="missing-script")
            if parts[index + 1] == "-":
                return ScriptResult("stdin")
            return _literal(parts, index + 1, " ".join(parts[index + 1:]))
        if kind == "cwa":
            if index + 1 >= len(parts):
                return ScriptResult("reject", reason="missing-script")
            if parts[index + 1] == "-":
                return ScriptResult("stdin")
            return _literal(parts, index + 1)
        if kind.startswith("enum:"):
            if index + 1 >= len(parts):
                return ScriptResult("reject", reason="missing-option-value")
            enum = kind.split(":", 1)[1]
            if parts[index + 1].casefold() not in POWER_ENUMS[enum]:
                return _indeterminate("unsupported-option-value")
            index += 2
            continue
        if kind == "value":
            if index + 1 >= len(parts):
                return ScriptResult("reject", reason="missing-option-value")
            index += 2
            continue
        index += 1
    return ScriptResult("file")


def _script_result(parts):
    shell = Path(parts[0].replace("\\", "/")).stem.casefold()
    if shell == "bash":
        return _bash_result(parts)
    if shell == "dash":
        return _dash_result(parts)
    if shell == "zsh":
        return _zsh_result(parts)
    if shell == "sh":
        return _sh_result(parts)
    if shell in ("pwsh", "powershell"):
        return _powershell_result(parts, shell)
    return None


def _shell_script_from_list(parts):
    cleaned = [str(part) for part in parts if isinstance(part, (str, int, float))]
    if not cleaned:
        return None
    result = _script_result(cleaned)
    if result is None:
        return " ".join(cleaned)
    if result.kind in ("ambiguous", "indeterminate"):
        detail = "ambiguous launcher profiles" if result.kind == "ambiguous" else result.reason
        sys.stderr.write(f"SHELL EXTRACTION GATE: refused {detail}; use an explicitly supported literal launcher invocation.\n")
        raise SystemExit(2)
    return result.script if result.kind == "literal" else None

# A line continuation is whitespace to the shell and is not whitespace to `\s`: PowerShell's
# backtick and sh's backslash both bridge `gh auth` on one line to `refresh` on the next, and
# without collapsing them first the pattern below simply does not match a command that runs.
CONTINUATION = re.compile(r"[`\\][ \t]*\r?\n[ \t]*")

# Only the two subcommands that mint or widen a credential. `gh auth status|token|setup-git|switch`
# read or select what already exists, so they are deliberately absent.
#
# `gh` arrives as a bare name, an absolute path, or `gh.exe` — and on Windows, where this runs, the
# `.exe` form is exactly what a quoted Program Files path produces. Demanding whitespace straight
# after `gh` let every one of those through, so the optional extension and a closing quote are part
# of the pattern, case-insensitively for `GH.EXE`.
BLOCKED = re.compile(r"""\bgh(?:\.exe)?["']?\s+auth\s+(refresh|login)\b""", re.IGNORECASE)

# Where one command ends and the next begins, so `--help` is only read from the invocation it
# belongs to and never borrowed from a later one.
SEPARATOR = re.compile(r"[;&|\r\n]")

MESSAGE = """GIT-AUTH GATE: `gh auth {subcommand}` is refused — an agent does not authenticate on the human's behalf.

Classic OAuth scopes are account-wide. A scope requested here is granted across EVERY organization this account belongs to, including employers', not just the one being worked on. Only the human can revoke it afterwards.

Do this instead:
  1. Ask for a FINE-GRAINED personal access token whose resource owner is the single organization that owns this repository, carrying only the permission the refused call needs.
  2. Use it for that one call: GH_TOKEN=<token> gh api <endpoint>
  3. Name three things when asking: the organization, the exact permission, and the single call it is for.

If that credential is not available, record the check as unavailable, say what it would have told you, and continue with what can be established without it. A broader credential is never the fallback, and a refused check is never a reason to guess and present the guess as a finding.

The `git-auth` skill is the full procedure."""

# Used when the refusal path itself throws. It must need nothing but a literal, because whatever
# broke may be the formatting, the claim store, or anything else the normal path depends on.
FALLBACK_MESSAGE = (
    "GIT-AUTH GATE: refused. This command authenticates on the human's behalf and would widen "
    "the credential across every organization the account belongs to. The gate could not build "
    "its full message, so it is refusing on the match alone. See the `git-auth` skill."
)


def extract_command(tool_name, tool_input):
    """The shell text a Claude Bash/PowerShell or Codex exec/unified-exec call would run, or None."""
    if not isinstance(tool_input, dict):
        return None
    if str(tool_name).lower() not in SHELL_TOOLS:
        return None
    for key in ("command", "cmd", "script", "input"):
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(value, list):
            joined = _shell_script_from_list(value)
            if joined and joined.strip():
                return joined
    action = tool_input.get("action")
    if isinstance(action, dict):
        value = action.get("command") or action.get("cmd")
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(value, list):
            joined = _shell_script_from_list(value)
            if joined and joined.strip():
                return joined
    return None


def find_violation(command):
    """The blocked subcommand name, or None when this command mints no credential."""
    joined = CONTINUATION.sub(" ", command or "")
    match = BLOCKED.search(joined)
    if match is None:
        return None
    # `--help` prints flags and executes nothing, and an agent may legitimately need to read them
    # to build the request the skill asks for. Read it only from this invocation, not a later one.
    rest = SEPARATOR.split(joined[match.end():], 1)[0]
    if "--help" in rest:
        return None
    return match.group(1)


def main():
    try:
        data = json.load(sys.stdin)
        command = extract_command(data.get("tool_name", ""), data.get("tool_input") or {})
        subcommand = find_violation(command) if command else None
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001 - recognition fails open; see the module docstring
        sys.exit(0)

    if subcommand is None:
        sys.exit(0)

    # Past here the command is known to authenticate on the human's behalf. Nothing below may
    # downgrade that to an allow, so its failures are absorbed into the refusal rather than
    # escaping to the recognition stage's handler.
    try:
        if not claim_invocation(data, HOOK_NAME):
            sys.exit(0)
        sys.stderr.write(MESSAGE.format(subcommand=subcommand))
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001 - a confirmed match is never allowed through by a later fault
        sys.stderr.write(FALLBACK_MESSAGE)
    sys.exit(2)


if __name__ == "__main__":
    main()
