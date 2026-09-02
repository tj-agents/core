from pathlib import PurePosixPath


LIVE_VALIDATION = {"queued", "in_progress", "success"}
META_ROOTS = {".agents", ".claude", ".codex", "docs", "plans"}
META_FILES = {"AGENTS.md", "CLAUDE.md"}


def is_metadata_path(value):
    path = PurePosixPath(value.replace("\\", "/"))
    if path.name.endswith(".md") or path.name.startswith("README"):
        return True
    if path.parts and path.parts[0] in META_ROOTS:
        return True
    return str(path) in META_FILES


def classify_validation(
    event_name,
    event_action,
    changed_paths,
    previous_executable_tree,
    current_executable_tree,
    prior_validation,
):
    paths = tuple(changed_paths)
    if event_name != "pull_request" or event_action != "synchronize":
        return "full"
    if not paths or any(not is_metadata_path(path) for path in paths):
        return "full"
    if not previous_executable_tree or not current_executable_tree:
        return "full"
    if previous_executable_tree != current_executable_tree:
        return "full"
    if prior_validation not in LIVE_VALIDATION:
        return "full"
    return "metadata-only"


def may_cancel_prior_validation(classification):
    return classification == "full"
