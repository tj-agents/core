#!/usr/bin/env python3
"""Run the refresh utility shipped in this machine package (Python 3.9+)."""

from pathlib import Path
import runpy

HERE = Path(__file__).resolve()
TARGET = next(path for path in (
    HERE.parents[3] / "scripts" / "reload_plugins.py",
    HERE.parents[3] / "resources" / "machine" / "scripts" / "reload_plugins.py",
    HERE.parents[5] / "resources" / "machine" / "scripts" / "reload_plugins.py",
) if path.is_file())

if __name__ == "__main__":
    runpy.run_path(str(TARGET), run_name="__main__")
