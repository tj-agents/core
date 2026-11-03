import runpy
import sys
from pathlib import Path

root = next(
    root
    for root in Path(__file__).resolve().parents
    if (root / "harness.json").is_file()
)
script = root / "dependencies/agent/.agents/agent/runtime/managed_admission.py"
sys.path.insert(0, str(script.parent))
sys.argv[0] = str(script)
runpy.run_path(str(script), run_name="__main__")
