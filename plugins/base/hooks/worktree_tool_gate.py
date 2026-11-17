import os
import sys
import time
from collections.abc import Mapping
from pathlib import Path

sys.path[:0] = [
    str(Path(__file__).resolve().parent),
    str(Path(__file__).resolve().parent / "worktrees"),
]

import tier_gate
import worktree_gate


def main() -> int:
    state = Path(
        os.environ.get(tier_gate.STATE_DIRECTORY_VARIABLE)
        or Path.home() / ".agents-state"
    )

    def boundary(payload: Mapping[str, object]) -> str:
        if payload.get("tool_name") == "Bash":
            tier_gate.record_command(payload, state, time.time())
        return tier_gate.boundary_gate(payload, state)

    return worktree_gate.main(boundary)


if __name__ == "__main__":
    raise SystemExit(main())
