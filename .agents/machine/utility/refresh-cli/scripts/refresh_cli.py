#!/usr/bin/env python3
"""Run the refresh utility shipped in this machine package (Python 3.9+)."""

from pathlib import Path
import runpy

HERE = Path(__file__).resolve()
TARGET = next(path for path in (
    HERE.parents[3] / "scripts" / "refresh_cli.py",
    HERE.parents[3] / "resources" / "machine" / "scripts" / "refresh_cli.py",
    HERE.parents[5] / "resources" / "machine" / "scripts" / "refresh_cli.py",
) if path.is_file())

if __name__ == "__main__":
    runpy.run_path(str(TARGET), run_name="__main__")
