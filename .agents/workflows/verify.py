import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from workflow_runtime import WorkflowContract, select_state_provider


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    workflow_root = Path(__file__).resolve().parent
    contract = WorkflowContract(workflow_root, repository_root=arguments.root.resolve())
    summary = contract.verify_bundle()
    probe = select_state_provider(arguments.root.resolve(), contract).probe()
    if probe["status"] != "available" or probe["provider_id"] != "repository":
        raise SystemExit("repository workflow state must remain available")
    print("workflow contracts: " + json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
