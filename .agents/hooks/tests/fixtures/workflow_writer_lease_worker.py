import sys
import time
from pathlib import Path


workflow_root = Path(sys.argv[1])
repository_root = Path(sys.argv[2])
control_root = Path(sys.argv[3])
worker_id = sys.argv[4]
sys.path.insert(0, str(workflow_root))

from host_runtime import WriterLeaseRegistry
from workflow_runtime import ContractViolation


registry = WriterLeaseRegistry.for_repository(repository_root)
dispatch = {
    "dispatch_id": f"dispatch-{worker_id}",
    "permissions": {
        "writer_lease": {
            "lease_id": f"lease-{worker_id}",
            "paths": [".agents/workflows/host_runtime.py"],
        }
    },
}
(control_root / f"ready-{worker_id}").write_text("", encoding="utf-8")
deadline = time.monotonic() + 10
while not (control_root / "go").exists():
    if time.monotonic() >= deadline:
        raise TimeoutError("writer barrier did not open")
    time.sleep(0.01)
try:
    registry.acquire(dispatch)
    outcome = "winner"
except ContractViolation:
    outcome = "rejected"
(control_root / f"attempted-{worker_id}").write_text("", encoding="utf-8")
if outcome == "winner":
    while len(list(control_root.glob("attempted-*"))) < 2:
        if time.monotonic() >= deadline:
            raise TimeoutError("writer attempts did not complete")
        time.sleep(0.01)
    registry.release(dispatch["dispatch_id"])
print(outcome)
