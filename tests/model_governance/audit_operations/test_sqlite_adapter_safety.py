import ast
from pathlib import Path


ADAPTER_ROOT = Path(
    "core/governance/operations/adapters/sqlite"
)


def sources():
    return sorted(ADAPTER_ROOT.glob("*.py"))


def test_adapter_has_no_network_or_process_dependencies():
    forbidden = {
        "httpx",
        "requests",
        "socket",
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


def test_adapter_defines_no_automatic_repair_or_model_write():
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


def test_adapter_does_not_hardcode_production_path():
    content = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sources()
    )

    assert "Application Support" not in content
    assert "model-governance-audit.sqlite3" not in content
    assert "ubuntu" not in content.lower()
