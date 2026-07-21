import ast
from pathlib import Path


APPLICATION_ROOT = Path(
    "core/governance/operations/application"
)


def sources():
    return sorted(APPLICATION_ROOT.glob("*.py"))


def test_application_has_no_infrastructure_dependencies():
    forbidden = {
        "fastapi",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
    }
    imported = set()

    for path in sources():
        tree = ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(
                    alias.name.split(".", 1)[0]
                    for alias in node.names
                )
            elif (
                isinstance(node, ast.ImportFrom)
                and node.module
            ):
                imported.add(
                    node.module.split(".", 1)[0]
                )

    assert not imported.intersection(forbidden)


def test_application_defines_no_model_write_or_remediation_action():
    forbidden_names = {
        "copy_model",
        "create_model",
        "delete_model",
        "pull_model",
        "remediate",
        "restore",
        "retry",
    }
    function_names = set()

    for path in sources():
        tree = ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
        )

        function_names.update(
            node.name.lower()
            for node in ast.walk(tree)
            if isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
        )

    assert not function_names.intersection(
        forbidden_names
    )


def test_scheduler_adapter_has_no_execution_dependency():
    path = APPLICATION_ROOT / "scheduler.py"
    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )

    imported_modules = set()
    function_names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(
                alias.name.lower()
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imported_modules.add(
                ("." * node.level + module).lower()
            )
        elif isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            function_names.add(node.name.lower())

    forbidden_import_fragments = {
        "adapters",
        "repository",
        "service",
        "sqlite3",
    }
    forbidden_execution_methods = {
        "append",
        "execute",
        "verify",
    }

    assert not any(
        fragment in module
        for module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert not function_names.intersection(
        forbidden_execution_methods
    )
