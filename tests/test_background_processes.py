import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCOPES = (".agents/hooks", ".agents/workflows", ".codex/runtime")
RAW_CALLS = {"Popen", "run", "call", "check_call", "check_output"}
SUPERVISED_HOST = (".codex/runtime/continuation/continuation_runtime.py", "child")


def test_background_entry_points_use_shared_process_execution() -> None:
    violations = []
    supervised = []
    for scope in SCOPES:
        for path in (ROOT / scope).rglob("*.py"):
            relative = path.relative_to(ROOT).as_posix()
            if "tests" in path.relative_to(ROOT).parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
            modules = {"subprocess"}
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules.update(
                        alias.asname or alias.name
                        for alias in node.names
                        if alias.name == "subprocess"
                    )
                elif isinstance(node, ast.ImportFrom) and node.module == "subprocess":
                    imported.update(
                        alias.asname or alias.name
                        for alias in node.names
                        if alias.name in RAW_CALLS
                    )
            parents = {
                child: node
                for node in ast.walk(tree)
                for child in ast.iter_child_nodes(node)
            }
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                target = node.func
                raw = (isinstance(target, ast.Name) and target.id in imported) or (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id in modules
                    and target.attr in RAW_CALLS
                )
                if not raw:
                    continue
                owner = parents.get(node)
                while owner is not None and not isinstance(
                    owner, (ast.FunctionDef, ast.AsyncFunctionDef)
                ):
                    owner = parents.get(owner)
                function = owner.name if owner is not None else "<module>"
                if (
                    (relative, function) == SUPERVISED_HOST
                    and isinstance(target, ast.Attribute)
                    and target.attr == "Popen"
                ):
                    supervised.append(relative)
                else:
                    violations.append(f"{relative}:{node.lineno} ({function})")
    assert not violations, "Background launches must use tj_cli.process: " + ", ".join(
        violations
    )
    assert supervised == [SUPERVISED_HOST[0]], (
        "Keep the suspended host/job admission boundary explicit"
    )
