r"""PreToolUse hook: no `gh pr merge` without a current, clean code-review.

Blocks a Bash tool call that would merge / enable auto-merge on a PR unless a
review work-order exists for the current branch, is stamped at the exact commit
being merged, and has zero open `- [ ]` findings. This is the *enforced* form of
the AGENTS.md rule "do a code-review before you merge" — advisory prose was
ignored once; a hook cannot be.

Scope: only fires on commands containing `gh pr merge`. `--disable-auto` (turning
a merge OFF) is always allowed — it is the safe direction. Every other merge form
(`--auto`, `--admin`, `--merge`, `--squash`, `--rebase`, bare) must pass the gate.

Contract: exit 0 = allow; exit 2 = block (stderr is fed back to the agent). For a
merge command the hook fails CLOSED — any doubt (missing/stale/unclean review, or
even an internal error) blocks, because letting an unreviewed merge through is the
exact failure this guard exists to prevent. Non-merge commands always exit 0.

The review file is what `review` / `docs-review` write:
`reviews/<branch-with-slashes-as-dashes>.md`, carrying a top-of-file
`**Reviewed up to commit:** \`<sha>\`` marker and `- [ ]` / `- [x]` findings.

Security layer: when the head being merged touches security-sensitive paths, the merge
also requires a current `**Security-reviewed up to commit:** \`<sha>\`` marker —
stamped by `review` Step 1d after it runs `/security-review`.

A repo opts in by carrying `.agents/merge-gate.json`; without one the review check exits 0
and claims no jurisdiction. Codex is the exception at the target-proof boundary: its hook
payload omits an `exec_command` workdir override, so every Codex merge must use the narrow
`pushd "<absolute-checkout>" && gh pr merge <number> ...` form below. An ambiguous Codex
merge is rejected before repository jurisdiction because there is no safe directory in
which to ask the opt-in question. Claude uses the same canonical target when present,
while retaining its legacy `cd`/payload-cwd fallback. A `--repo
<owner>/<name>` naming some other repository is likewise not this gate's business for
Claude, for the same reason a `cd <other-repo> && merge` is not. The config file also names
the repo's own security-sensitive paths, which are its inventory rather than this
mechanism's — the generic patterns below (workflows, auth/secret vocabulary) apply
everywhere and stay here.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

from hook_runtime import claim_invocation, grant, is_trusted_checkout

# This message is what the agent acts on, and Windows defaults these streams to cp1252,
# which turns the punctuation in it into mojibake.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


_GIT_CWD = ["."]


def git(*args):
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True, cwd=_GIT_CWD[0]
    ).stdout.strip()


_ENABLE_TOKENS = ("--auto", "--admin", "--merge", "--squash", "--rebase")

CONFIG_FILE = ".agents/merge-gate.json"

# Lowercased, and the hook's whole vocabulary: a harness whose shell tool is not named here
# cannot be wired to this gate, because a matcher the hook ignores is enforcement that is inert
# while looking wired. Codex's shell tool name is not established yet, so it carries no entry.
SHELL_TOOLS = {"bash", "powershell"}

# Paths whose change makes a diff security-sensitive — a merge touching any of
# these needs a current `Security-reviewed up to commit:` marker too. Kept
# targeted (concrete high-value areas) so unrelated merges are never blocked.
# These hold in any repo; a repo's own service and project names go in its
# CONFIG_FILE under `security_paths`.
_SECURITY_PATTERNS = (
    re.compile(r"^\.github/workflows/"),
    re.compile(r"(?i)(authoriz|authentic|credential|\bsecret|password|apikey|api_key)"),
)


class ConfigUnusable(Exception):
    """The repo opted into the gate and the table cannot be read. Never silently ignored."""


def find_config(cwd):
    """The opted-in repo root at or above `cwd`, or None. Walking up rather than asking git
    keeps a worktree, a submodule and a plain checkout on the same answer."""
    try:
        base = Path(cwd).resolve()
    except OSError:
        return None
    for candidate in (base, *base.parents):
        if (candidate / CONFIG_FILE).is_file():
            return candidate / CONFIG_FILE
    return None


def security_patterns(config_path):
    """The generic patterns plus the repo's own. A present but broken table is a loud stop:
    failing open here would leave the gate inert while looking wired."""
    patterns = list(_SECURITY_PATTERNS)
    try:
        parsed = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ConfigUnusable(f"{CONFIG_FILE} exists but could not be read: {error}") from error
    declared = parsed.get("security_paths", [])
    if not isinstance(declared, list):
        raise ConfigUnusable(f"{CONFIG_FILE} `security_paths` must be a list.")
    for entry in declared:
        try:
            patterns.append(re.compile(entry))
        except (TypeError, re.error) as error:
            raise ConfigUnusable(f"{CONFIG_FILE} `security_paths` entry {entry!r}: {error}") from error
    return patterns


def touches_security(changed_paths, patterns=_SECURITY_PATTERNS):
    for path in changed_paths:
        for pat in patterns:
            if pat.search(path):
                return path
    return None


_INVOCATION_RE = re.compile(r"(?:^|[;&|\n]|&&|\|\|)\s*(?:[A-Za-z_][\w]*=\S+\s+)*gh\s+pr\s+merge\b")


def invokes_merge(command):
    """True only when the command actually RUNS the merge, not merely mentions it.

    A substring test blocked any command quoting the string — including edits to this
    file and the PR body describing them.
    """
    return _INVOCATION_RE.search(command) is not None


def is_merge_enable(command):
    if not invokes_merge(command):
        return False
    # An enabling form anywhere gates — even in a compound that disables
    # auto-merge FIRST (`--disable-auto && ... --auto`, the documented re-assert
    # remedy). A whole-command "--disable-auto is present" test would fail open
    # on exactly that compound, so check for an enabling token independently.
    # Strip --disable-auto FIRST: "--auto" is a substring of it, so a naive token scan
    # matched every disable and made the "safe direction" branch below unreachable.
    scanned = command.replace("--disable-auto", " ")
    if any(tok in scanned for tok in _ENABLE_TOKENS):
        return True
    # A pure --disable-auto (no enabling token) is the safe direction — allow.
    if "--disable-auto" in command:
        return False
    # Bare `gh pr merge` with neither is still a merge attempt — gate it.
    return True


def pr_number(command):
    """The PR number the command targets, when it names one explicitly."""
    m = re.search(r"gh\s+pr\s+merge\s+(\d+)", command)
    return m.group(1) if m else None


_SLUG_RE = re.compile(r"[:/]?([^/:]+)/([^/:]+?)(?:\.git)?/?$")
_REPO_FLAG_RE = re.compile(r"(?:--repo|-R)(?:\s+|=)((?:\"[^\"]*\")|(?:\'[^\']*\')|(?:\S+))")


def normalize_slug(value):
    """`owner/name`, lowercased, from a slug, an SSH remote or an HTTPS URL."""
    m = _SLUG_RE.search(value.strip())
    return (m.group(1) + "/" + m.group(2)).lower() if m else None


def repo_flag(command):
    """The repository `--repo`/`-R` names, or None.

    A command that names another repository is that repository's merge. Resolving its PR
    number against this checkout gated it on an unrelated local branch — which blocks a
    legitimate sibling merge and, worse, passes one whenever the local PR of the same
    number happens to carry a clean review.
    """
    m = _REPO_FLAG_RE.search(command)
    if not m:
        return None
    value = m.group(1)
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return normalize_slug(value)


def local_repo_slug():
    """`owner/name` for the checkout the merge runs in, or None when origin is unreadable."""
    try:
        return normalize_slug(git("remote", "get-url", "origin"))
    except Exception:  # noqa: BLE001 - no origin / broken remote; the caller fails closed
        return None


_CD_RE = re.compile(r"(?:^|[;&|]|&&)\s*cd\s+((?:\"[^\"]*\")|(?:\'[^\']*\')|(?:[^\s;&|]+))")

# Deliberately a contract, not a shell parser. Codex does not report an exec_command
# workdir to hooks, and trying to infer one from arbitrary cmd/PowerShell/Bash text means
# reimplementing three shells. The shared `pushd` + `&&` envelope works in all three;
# restricting the tail to gh's valueless merge switches keeps the target proof exact.
_CANONICAL_MERGE_RE = re.compile(
    r'\Apushd "(?P<target>[^"\r\n]+)" && gh pr merge (?P<pr>[1-9]\d*)'
    r'(?P<options>(?: --(?:auto|admin|merge|squash|rebase|delete-branch))*)\Z'
)
_PUSHD_TOKEN_RE = re.compile(r"\bpushd\b", re.IGNORECASE)
_CANONICAL_UNSAFE_TARGET_CHARS = frozenset('$%!`&|;<>^\r\n')


def is_codex_invocation(data):
    """Codex hook payloads carry a turn id; Claude hook payloads do not."""
    return "turn_id" in data or "turnId" in data


def canonical_merge_target_dir(command):
    """Return the proven checkout from the shared cross-harness merge envelope."""
    match = _CANONICAL_MERGE_RE.fullmatch(command)
    if match is None:
        return None

    raw = match.group("target")
    if raw.endswith("\\") or any(char in raw for char in _CANONICAL_UNSAFE_TARGET_CHARS):
        return None
    target = Path(raw)
    if not target.is_absolute() or not target.is_dir():
        return None
    try:
        return str(target.resolve(strict=True))
    except OSError:
        return None


def invokes_pushd_before_merge(command):
    """Whether a merge command attempts to select its checkout with ``pushd``.

    This is deliberately lexical, not a partial Bash parser. Any standalone ``pushd`` word
    before the last detected merge is treated as an attempted target, including a word inside
    an exotic quoted mention. Looking through the last merge matters for the documented
    ``--disable-auto && pushd ... && --auto`` re-assert compound: the first merge is safe, but
    the later enabling merge changes checkout. That conservative false positive is preferable
    to falling back to another checkout when Bash could execute a form the detector does not
    understand.
    """
    merge_start = None
    for merge in _INVOCATION_RE.finditer(command):
        merge_start = merge.start()
    return merge_start is not None and _PUSHD_TOKEN_RE.search(command, 0, merge_start) is not None


def merge_target_dir(command, data):
    """The directory the merge actually runs in: the last `cd` before it, else the tool cwd.

    Adopted from PR #495. Without it a `cd <worktree> && merge` was still judged against
    the pinned project dir, so a merge with no PR number read the wrong branch's review.
    """
    pos = command.find("gh pr " "merge")
    prefix = command if pos < 0 else command[:pos]
    target = None
    for m in _CD_RE.finditer(prefix):
        target = m.group(1)
        if len(target) >= 2 and target[0] == target[-1] and target[0] in "\"'":
            target = target[1:-1]
    return target or data.get("cwd") or "."


def gh_json(*args):
    """Runs where the merge runs. `git` was already cwd-aware and this was not, so a
    `cd <other-repo> && gh pr merge <n>` resolved <n> against THIS repo - gating an
    unrelated repo's merge against a Concertable PR that merely shares the number."""
    return subprocess.run(
        ["gh", *args], capture_output=True, text=True, check=True, cwd=_GIT_CWD[0]
    ).stdout.strip()


def review_only(base, head):
    """True when everything between base and head touched reviews/ alone.

    Stamping the marker is itself a commit, so a review can never be stamped AT the
    commit that contains it. Demanding marker == head therefore blocks every honestly
    reviewed PR, which is why this gate could not be satisfied from any checkout.
    Nothing reviewable changed, so the review is still current.
    """
    try:
        changed = git("diff", "--name-only", base + ".." + head).splitlines()
    except Exception:  # noqa: BLE001 - unresolvable range -> treat as stale, fail closed
        return False
    return bool(changed) and all(x.startswith("reviews/") for x in changed)


def work_order_metadata_lines(review):
    fence = None
    for line in review.splitlines():
        spaces = len(line) - len(line.lstrip(" "))
        stripped = line[spaces:]
        marker_match = re.match(r"(`{3,}|~{3,})", stripped) if spaces <= 3 else None
        if marker_match:
            marker = marker_match.group(1)
            suffix = stripped[len(marker):]
            if fence is None:
                fence = (marker[0], len(marker))
            elif (
                marker[0] == fence[0]
                and len(marker) >= fence[1]
                and not suffix.strip()
            ):
                fence = None
            continue
        if fence is None and spaces < 4 and not line.startswith("\t"):
            yield line


def work_order_field(review, label):
    prefix = f"**{label}:**"
    lines = [
        line
        for line in work_order_metadata_lines(review)
        if line.lstrip().startswith(prefix)
    ]
    if not lines:
        return None
    if len(lines) != 1:
        return "invalid"
    match = re.fullmatch(re.escape(prefix) + r"\s*`([^`]+)`\s*", lines[0])
    return match.group(1).casefold() if match else "invalid"


def work_order_sha_field(review, label):
    prefix = f"**{label}:**"
    lines = [
        line
        for line in work_order_metadata_lines(review)
        if line.lstrip().startswith(prefix)
    ]
    if not lines:
        return None
    if len(lines) != 1:
        return "invalid"
    match = re.fullmatch(
        re.escape(prefix) + r"\s*`([0-9a-fA-F]{7,40})`(?:\s+.*)?",
        lines[0],
    )
    return match.group(1).lower() if match else "invalid"


def review_status(review):
    return work_order_field(review, "Review status")


def review_judgment(review):
    return work_order_field(review, "Judgment")


def staged_work_order(review):
    headings = {
        "## Coverage",
        "## Rules manifest",
        "## Cross-area notes",
        "## Parent finalization",
    }
    for line in work_order_metadata_lines(review):
        stripped = line.strip()
        if stripped in headings or re.match(
            r"^## Review pass\b.*\bstaged(?::|$)", stripped
        ):
            return True
    return False


def review_completion_problem(review):
    status = review_status(review)
    judgment = review_judgment(review)
    notes_status = work_order_field(review, "Cross-area notes status")
    summary_status = work_order_field(review, "Parent summary status")
    if status is None:
        if any(value is not None for value in (judgment, notes_status, summary_status)):
            return "uses new-format review fields but has no `Review status`"
        return None
    if status != "complete":
        return "has review status '" + status + "'"
    if judgment not in ("approved", "changes-requested"):
        return "has no valid final parent judgment"
    if staged_work_order(review) or notes_status is not None or summary_status is not None:
        if notes_status != "complete" or summary_status != "complete":
            return "has incomplete parent finalization state"
    return None


def unresolved_review_items(review):
    return [
        line.strip()
        for line in review.splitlines()
        if re.match(r"^\s*-\s*\[(?:\s|~)\]", line)
    ]


def changed_against_main(head):
    """Paths `head` changes relative to main. Unresolvable -> empty, the caller fails open.

    Every ref here must be the head being MERGED, never the literal HEAD: the gate resolves a PR's
    own head so a worktree PR merges correctly from any checkout, and a security classification that
    reads the session's branch instead answered for whatever that checkout happened to be sitting on.
    """
    try:
        try:
            # origin/main not local main: local main drifts stale and would false-positive the
            # security check by dragging unrelated commits into the range.
            base = git("merge-base", "origin/main", head)
        except Exception:  # noqa: BLE001
            base = git("merge-base", "main", head)
        return git("diff", "--name-only", base + ".." + head).splitlines()
    except Exception:  # noqa: BLE001
        return []


def security_no_longer_covered(marker, head, patterns, work_order=None):
    """True when a security-sensitive path changed between the security marker and head.

    Asking instead whether ANY commit landed leaves the gate with no legal exit: an ordinary doc or
    ledger commit makes the marker stale, while the review procedure runs its security layer only for
    a security-sensitive range and so never re-stamps it. Sensitive paths untouched since the security
    review are still covered by it.

    `work_order` — this branch's own `reviews/<slug>.md` and nothing else — is excluded for the same
    reason `review_only` exists one layer up, and the self-reference bites harder here. That path is
    derived from the branch slug, so a branch named for the thing it fixes — Fix/CredentialScoping,
    Fix/AuthenticationRetry — writes `credential` or `authentic` into the artifact's own path, where
    the generic vocabulary matches it. Stamping the marker is itself a commit to that path, so
    stamping restales the marker, and the branch cannot be merged from any checkout. A review
    artifact is the evidence of a review, never the subject of one.

    Exactly that one path, never the `reviews/` directory: a prefix match would also excuse
    `reviews/rotate-credentials.py`, or another branch's work order arriving on a merge from main,
    and would put anything a writer chose to place under `reviews/` permanently beyond staleness
    detection once a first marker existed.
    """
    try:
        changed = git("diff", "--name-only", marker + ".." + head).splitlines()
    except Exception:  # noqa: BLE001 - unresolvable range -> fail closed
        return True
    reviewable = [path for path in changed if path != work_order]
    return touches_security(reviewable, patterns) is not None


def block(reason):
    sys.stderr.write(reason)
    sys.exit(2)


def grant_if_trusted(data, canonical_target):
    """Approve a merge that passed every check, but only the exact Claude envelope.

    A PreToolUse allow covers the whole tool call, so anything but the single-command envelope
    could carry an unrelated command through on the review's approval.
    """
    if canonical_target is None or is_codex_invocation(data):
        return
    if is_trusted_checkout(__file__, canonical_target):
        grant("merge-review-gate: the review is current and clean in a trusted repository.")


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)  # not our JSON — don't interfere

    if str(data.get("tool_name", "")).lower() not in SHELL_TOOLS:
        sys.exit(0)

    command = (data.get("tool_input") or {}).get("command", "")
    if not isinstance(command, str) or not is_merge_enable(command):
        sys.exit(0)

    # Both harnesses prefer the canonical target, so the review gate judges the checkout
    # where the documented command actually merges. Codex requires that proof because its
    # hook input omits exec_command's workdir; Claude keeps its established cd/payload-cwd
    # fallback for older callers that do not yet use the envelope.
    canonical_target = canonical_merge_target_dir(command)
    if is_codex_invocation(data):
        if canonical_target is None:
            if not claim_invocation(data, "merge-review-gate"):
                sys.exit(0)
            block(
                "MERGE GATE: Codex cannot prove this merge's checkout because hooks do not "
                "receive an exec_command workdir. Use exactly `pushd \"<absolute-checkout>\" "
                "&& gh pr merge <number> [--merge|--squash|--rebase] [--auto]`, with no "
                "additional shell commands, then retry."
            )
        _GIT_CWD[0] = canonical_target
    else:
        if canonical_target is not None:
            _GIT_CWD[0] = canonical_target
        elif invokes_pushd_before_merge(command):
            if not claim_invocation(data, "merge-review-gate"):
                sys.exit(0)
            block(
                "MERGE GATE: Claude cannot prove this merge's pushd checkout. Use exactly "
                "`pushd \"<absolute-checkout>\" && gh pr merge <number> "
                "[--merge|--squash|--rebase] [--auto]`, with no additional shell commands, "
                "then retry."
            )
        else:
            # Run every git query where the merge runs, not where the hook process happens to sit.
            _GIT_CWD[0] = merge_target_dir(command, data)

    # From here on the command WOULD merge — fail closed on anything unproven.
    try:
        toplevel = git("rev-parse", "--show-toplevel")
    except Exception as exc:  # noqa: BLE001 — a merge with a broken check must not slip through
        block("MERGE GATE: cannot resolve git state (" + str(exc) + "); refusing "
              "`gh pr merge` until a code-review can be verified.")

    named = repo_flag(command)
    if named is not None:
        local = local_repo_slug()
        if local is None:
            block("MERGE GATE: `--repo " + named + "` names a repository and this checkout's "
                  "origin cannot be read, so the gate cannot tell whether the merge is its own; "
                  "refusing until it can.")
        if local != named:
            sys.exit(0)

    # Only an opted-in repository's merges. `reviews/<branch>.md` is a convention a repo
    # adopts, and a sibling repo merged from this session has its own rules - gating it here
    # demanded a review file that repo never had. The question is asked of the directory the
    # merge RUNS in, so a `cd <other-repo> && merge` is judged by that repo's opt-in.
    config_path = find_config(_GIT_CWD[0])
    if config_path is None:
        sys.exit(0)
    if not claim_invocation(data, "merge-review-gate"):
        sys.exit(0)
    try:
        patterns = security_patterns(config_path)
    except ConfigUnusable as exc:
        block("MERGE GATE: " + str(exc))

    # Gate the branch being MERGED, not the branch this session happens to sit on.
    # Resolving the session's checkout meant a worktree PR merged from a main-rooted
    # session looked for reviews/main.md and blocked, however clean its own review was.
    target = pr_number(command)
    if target:
        try:
            branch = gh_json("pr", "view", target, "--json", "headRefName", "--jq", ".headRefName")
            head = gh_json("pr", "view", target, "--json", "headRefOid", "--jq", ".headRefOid")
        except Exception as exc:  # noqa: BLE001
            block("MERGE GATE: cannot resolve PR #" + target + " (" + str(exc) + "); refusing to "
                  "merge until its review can be verified.")
    else:
        try:
            branch = git("rev-parse", "--abbrev-ref", "HEAD")
            head = git("rev-parse", "HEAD")
        except Exception as exc:  # noqa: BLE001
            block("MERGE GATE: cannot resolve git state (" + str(exc) + "); refusing to merge "
                  "until a code-review can be verified.")

    slug = branch.replace("/", "-")
    review_path = toplevel + "/reviews/" + slug + ".md"

    review = None
    if target:
        for ref in (branch, head):
            try:
                git("fetch", "origin", ref)
                break
            except Exception:  # noqa: BLE001 - deleted branch / unfetchable oid; try the next
                continue
        try:
            review = git("show", head + ":reviews/" + slug + ".md")
        except Exception:  # noqa: BLE001 - fall through to the working tree
            review = None
    if review is None:
        try:
            with open(review_path, encoding="utf-8") as fh:
                review = fh.read()
        except OSError:
            review = None
    if review is None:
        block(
            "MERGE GATE (AGENTS.md — review before merge): no review file for "
            "branch '" + branch + "' at reviews/" + slug + ".md. Run /review "
            "(or /docs-review for a docs-only branch) and address findings, THEN "
            "merge. Do NOT merge unreviewed."
        )

    completion_problem = review_completion_problem(review)
    if completion_problem:
        block(
            "MERGE GATE: reviews/" + slug + ".md " + completion_problem + ". "
            "Complete the frozen review pass and its parent judgment before merging."
        )

    reviewed = work_order_sha_field(review, "Reviewed up to commit")
    if reviewed in (None, "invalid"):
        block("MERGE GATE: reviews/" + slug + ".md has no unique valid "
              "`Reviewed up to commit:` marker. Re-run /review to stamp it, then merge.")

    if not (head.lower().startswith(reviewed) or reviewed.startswith(head.lower())) \
            and not review_only(reviewed, head):
        block(
            "MERGE GATE: review is STALE — reviews/" + slug + ".md is stamped at "
            + reviewed + " but HEAD is " + head[:12] + ". Commits landed since the "
            "review. Re-run /incremental-review (or /review), then merge."
        )

    open_findings = unresolved_review_items(review)
    if open_findings:
        block(
            "MERGE GATE: review has " + str(len(open_findings)) + " unresolved item(s) "
            "in reviews/" + slug + ".md. Address (or explicitly [wontfix]) every "
            "`- [ ]` or `- [~]` item, then merge. First: " + open_findings[0][:120]
        )

    # Security layer: a security-sensitive head also needs a current security marker.
    # Detection failure fails OPEN (the primary review gate already fired) so an
    # unresolvable base can't wedge every merge; a resolvable sensitive path fails CLOSED.
    sensitive = touches_security(changed_against_main(head), patterns)
    if sensitive:
        sreviewed = work_order_sha_field(review, "Security-reviewed up to commit")
        if sreviewed in (None, "invalid"):
            block(
                "MERGE GATE (security layer): '" + sensitive + "' is security-sensitive but "
                "reviews/" + slug + ".md has no unique valid "
                "`Security-reviewed up to commit:` marker. Run "
                "/security-review (or re-run /review, which runs it on sensitive paths and "
                "stamps the marker), THEN merge."
            )
        if not (head.lower().startswith(sreviewed) or sreviewed.startswith(head.lower())) \
                and security_no_longer_covered(
                    sreviewed, head, patterns, "reviews/" + slug + ".md"
                ):
            block(
                "MERGE GATE (security layer): security review is STALE — reviews/" + slug + ".md "
                "security marker is at " + sreviewed + " but a security-sensitive path changed "
                "since it, up to " + head[:12] + ". Re-run /security-review, then merge."
            )

    grant_if_trusted(data, canonical_target)
    grant_if_trusted(data, canonical_target)
    sys.exit(0)  # reviewed, current, clean → allow the merge


if __name__ == "__main__":
    main()
