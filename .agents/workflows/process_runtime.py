"""Load process execution from this workflow package's delivered CLI runtime."""

import sys
from pathlib import Path

if sys.version_info < (3, 12):  # noqa: UP036
    raise RuntimeError("Workflow process execution requires Python 3.12 or later")

sys.dont_write_bytecode = True
package = Path(__file__).resolve().parent.parent
if package.name == ".agents" and (package / "plugins/sources.json").is_file():
    runtime = package / "dependencies/cli/.agents/cli/runtime"
    if not (package / "dependencies/cli/source.json").is_file():
        raise RuntimeError(
            f"The shipped CLI process runtime is unavailable at {runtime}; "
            "restage the declared CLI source or reinstall this package"
        )
elif any(
    (package / marker).is_file()
    for marker in (".codex-plugin/plugin.json", ".claude-plugin/plugin.json")
):
    runtime = package / "hooks"
else:
    raise RuntimeError(
        "The workflow package root is unavailable; "
        "restore its source or installed package layout"
    )
if not (runtime / "tj_cli/process/__init__.py").is_file():
    raise RuntimeError(
        f"The shipped CLI process runtime is unavailable at {runtime}; "
        "restage the declared CLI source or reinstall this package"
    )
sys.path.insert(0, str(runtime))

from tj_cli import process  # noqa: E402

__all__ = ["process"]
