import ast
from pathlib import Path

DOMAIN_ROOT = Path(
    "core/governance/operations/domain"
)

FORBIDDEN_IMPORT_ROOTS = {
    "fastapi",
    "flask",
    "requests",
    "sqlite3",
    "subprocess",
}

FORBIDDEN_ACTION_NAMES = {
    "copy",
    "create",
    "delete",
    "pull",
    "remediate",
    "retry",
}


def python_sources() -> list[Path]:
    return sorted(DOMAIN_ROOT.glob("*.py"))


def test_domain_has_no_infrastructure_or_web_dependencies():
    imports: set[str] = set()

    for path in python_sources():
        tree = ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(
                    alias.name.split(".", 1)[0]
                    for alias in node.names
                )
            elif (
                isinstance(node, ast.ImportFrom)
                and node.module
            ):
                imports.add(
                    node.module.split(".", 1)[0]
                )

    assert not imports.intersection(
        FORBIDDEN_IMPORT_ROOTS
    )


def test_domain_defines_no_model_write_or_remediation_action():
    names: set[str] = set()

    for path in python_sources():
        tree = ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
        )

        names.update(
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

    assert not names.intersection(
        FORBIDDEN_ACTION_NAMES
    )


def test_domain_contains_no_ubuntu_ownership_module():
    assert all(
        "ubuntu" not in path.name.lower()
        for path in python_sources()
    )
