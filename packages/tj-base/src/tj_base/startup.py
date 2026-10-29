"""Acknowledge every required participant in one managed native startup."""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

_DIRECTORY = "TJ_AGENTS_STARTUP_ACK_DIRECTORY"
_TOKEN = "TJ_AGENTS_STARTUP_ACK_TOKEN"
_REQUIRED = "TJ_AGENTS_STARTUP_REQUIRED_HOOKS"


class ProtocolError(ValueError):
    pass


class State(StrEnum):
    UNMANAGED = "unmanaged"
    WAITING = "waiting"
    CONFIRMED = "confirmed"
    FAILED = "failed"


@dataclass(frozen=True)
class Request:
    directory: Path
    token: str
    participants: tuple[str, ...]


@dataclass(frozen=True)
class Outcome:
    state: State
    detail: str | None = None


def _location(environment: Mapping[str, str]) -> tuple[Path, str]:
    directory = environment.get(_DIRECTORY, "")
    token = environment.get(_TOKEN, "")
    if not directory or not Path(directory).is_absolute():
        raise ProtocolError(
            "Managed startup requires an absolute acknowledgement directory"
        )
    if re.fullmatch(r"[A-Za-z0-9_-]{32,128}", token) is None:
        raise ProtocolError("Managed startup requires a safe acknowledgement token")
    return Path(directory), token


def request(environment: Mapping[str, str]) -> Request | None:
    if not any(name in environment for name in (_DIRECTORY, _TOKEN, _REQUIRED)):
        return None
    directory, token = _location(environment)
    try:
        participants = json.loads(environment.get(_REQUIRED, ""))
    except ValueError as error:
        raise ProtocolError(
            "Managed startup requires a valid participant roster"
        ) from error
    if (
        not isinstance(participants, list)
        or not participants
        or any(
            not isinstance(identity, str)
            or re.fullmatch(r"[a-z0-9][a-z0-9-]*@[a-z0-9][a-z0-9-]*", identity) is None
            for identity in participants
        )
        or len(set(participants)) != len(participants)
    ):
        raise ProtocolError(
            "Managed startup requires nonempty, unique plugin participants"
        )
    return Request(directory, token, tuple(participants))


def _write(path: Path, value: str) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".startup-",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(value)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _receipt(selected: Request, identity: str) -> Path:
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return selected.directory / (selected.token + "." + digest)


def _matches(path: Path, token: str) -> bool:
    try:
        return path.read_text(encoding="utf-8") == token
    except FileNotFoundError:
        return False


def _failure(selected: Request) -> str | None:
    try:
        detail = (selected.directory / (selected.token + ".failed")).read_text(
            encoding="utf-8"
        )
    except FileNotFoundError:
        return None
    return detail or "Required startup hook failed"


def acknowledge(
    environment: Mapping[str, str], identity: str, *, succeeded: bool, detail: str = ""
) -> None:
    try:
        selected = request(environment)
    except ProtocolError as error:
        directory, token = _location(environment)
        _write(directory / (token + ".failed"), str(error))
        raise
    if selected is None or identity not in selected.participants:
        return
    if not succeeded:
        _write(
            selected.directory / (selected.token + ".failed"),
            f"Required startup hook {identity} failed: {detail}",
        )
        return
    _write(_receipt(selected, identity), selected.token)
    if all(
        _matches(_receipt(selected, participant), selected.token)
        for participant in selected.participants
    ) and _failure(selected) is None:
        _write(selected.directory / selected.token, selected.token)


def outcome(environment: Mapping[str, str]) -> Outcome:
    selected = request(environment)
    if selected is None:
        return Outcome(State.UNMANAGED)
    try:
        if failure := _failure(selected):
            return Outcome(State.FAILED, failure)
        complete = _matches(
            selected.directory / selected.token, selected.token
        ) and all(
            _matches(_receipt(selected, participant), selected.token)
            for participant in selected.participants
        )
        if failure := _failure(selected):
            return Outcome(State.FAILED, failure)
    except OSError as error:
        return Outcome(
            State.FAILED, f"Cannot read required startup acknowledgements: {error}"
        )
    return Outcome(State.CONFIRMED if complete else State.WAITING)
