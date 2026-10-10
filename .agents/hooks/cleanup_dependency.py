import json
import subprocess


FORGE_TIMEOUT_SECONDS = 20
PR_FIELDS = "number,headRefName,headRefOid"


class EvidenceError(RuntimeError):
    pass


def _validate_records(value, relation):
    if not isinstance(value, list):
        raise EvidenceError(f"open {relation} PR evidence is not a JSON list")
    records = []
    for value in value:
        if not isinstance(value, dict) or set(value) != {"number", "headRefName", "headRefOid"}:
            raise EvidenceError(f"open {relation} PR evidence has an invalid record")
        number = value["number"]
        name = value["headRefName"]
        oid = value["headRefOid"]
        if (not isinstance(number, int) or isinstance(number, bool) or number < 1
                or not isinstance(name, str) or not name
                or not isinstance(oid, str) or not oid):
            raise EvidenceError(f"open {relation} PR evidence has an invalid identity")
        records.append({"number": number, "head_ref_name": name, "head_ref_oid": oid})
    return records


def _fixture_records(fixture, key, relation):
    if not isinstance(fixture, dict) or key not in fixture:
        raise EvidenceError(f"forge fixture has no open {relation} PR evidence")
    return _validate_records(fixture[key], relation)


def _query_records(branch, relation, repo, cwd):
    option = "--head" if relation == "head" else "--base"
    command = ["gh", "pr", "list", "--state", "open", option, branch, "--json", PR_FIELDS]
    if repo:
        command += ["--repo", repo]
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd) if cwd is not None else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=FORGE_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as error:
        raise EvidenceError("the gh CLI is required for open PR evidence") from error
    except (OSError, subprocess.SubprocessError) as error:
        raise EvidenceError(f"gh pr list for open {relation} PRs failed: {error}") from error
    if result.returncode != 0:
        raise EvidenceError(
            f"gh pr list for open {relation} PRs failed: {result.stderr.strip()}"
        )
    try:
        data = json.loads(result.stdout)
    except ValueError as error:
        raise EvidenceError(f"gh pr list for open {relation} PRs returned invalid JSON: {error}") from error
    return _validate_records(data, relation)


def observe_open_prs(branch, repo=None, cwd=None, fixture=None):
    if not isinstance(branch, str) or not branch:
        raise EvidenceError("branch is required for open PR evidence")
    if fixture is not None:
        return {
            "head": _fixture_records(fixture, "open_head_prs", "head"),
            "base": _fixture_records(fixture, "open_base_prs", "base"),
        }
    return {
        "head": _query_records(branch, "head", repo, cwd),
        "base": _query_records(branch, "base", repo, cwd),
    }
