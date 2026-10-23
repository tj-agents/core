"""Canonical marketplace identity for TJ Agents consumers and native refresh."""

from __future__ import annotations

MARKETPLACE_NAME = "tj-agents"
MARKETPLACE_REPOSITORY = "tj-agents/marketplace"


def producer_repository(repository: object) -> bool:
    return (isinstance(repository, str) and repository.casefold().startswith("tj-agents/")
            and repository.casefold() != MARKETPLACE_REPOSITORY)


def marketplace_error(name: str, repository: object) -> str | None:
    if (name == MARKETPLACE_NAME) != (repository == MARKETPLACE_REPOSITORY):
        return f"The {MARKETPLACE_NAME} marketplace must be {MARKETPLACE_REPOSITORY} and nothing else may use that name"
    if producer_repository(repository):
        return f"{repository} is published through the {MARKETPLACE_NAME} marketplace; select {MARKETPLACE_REPOSITORY}"
    return None
