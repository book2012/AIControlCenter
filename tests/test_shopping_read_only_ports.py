from __future__ import annotations

import ast
import importlib
import inspect
import os
import subprocess
import sys
import typing
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PORT_SPECS = {
    "core.shopping.ports.commerce": (
        "CommerceReadPort",
        {"get_product", "list_products", "get_order_summary"},
    ),
    "core.shopping.ports.cms": (
        "CmsReadPort",
        {"get_content", "list_content"},
    ),
    "core.shopping.ports.health": (
        "AdapterHealthPort",
        {"get_health"},
    ),
    "core.shopping.ports.schema": (
        "SchemaDiscoveryPort",
        {"discover_schema"},
    ),
    "core.shopping.ports.snapshots": (
        "SnapshotRepositoryPort",
        {"get_latest_snapshot", "list_snapshots"},
    ),
    "core.shopping.ports.policy": (
        "PolicyDecisionPort",
        {"evaluate_read"},
    ),
    "core.shopping.ports.audit": (
        "AuditPort",
        {"get_event", "list_events"},
    ),
}

CONTRACT_NAMES = {
    "AdapterHealth",
    "AuditEvent",
    "AuditEventPage",
    "ContentSnapshot",
    "ContentSnapshotPage",
    "OrderSummary",
    "PageRequest",
    "PolicyDecision",
    "ProductSnapshot",
    "ProductSnapshotPage",
    "ReadContext",
    "ReadPolicyRequest",
    "SchemaDiscoveryResult",
    "SnapshotEnvelope",
    "SnapshotEnvelopePage",
}

FORBIDDEN_PORTS = {
    "CommerceWritePort",
    "CmsWritePort",
    "ProductionWebhookWritePort",
}

FORBIDDEN_METHOD_TOKENS = {
    "append",
    "create",
    "delete",
    "mutate",
    "patch",
    "post",
    "publish",
    "put",
    "save",
    "send",
    "update",
    "upsert",
    "write",
}

MODULES = [
    "core.shopping",
    "core.shopping.application",
    "core.shopping.contracts",
    "core.shopping.contracts.provisional",
    "core.shopping.domain",
    "core.shopping.governance",
    "core.shopping.observability",
    "core.shopping.ports",
    *sorted(PORT_SPECS),
]


def test_all_shopping_modules_import() -> None:
    for module_name in MODULES:
        module = importlib.import_module(module_name)
        assert module.__file__ is not None


def test_protocols_are_async_keyword_only_and_typed() -> None:
    for module_name, (class_name, expected_methods) in PORT_SPECS.items():
        module = importlib.import_module(module_name)
        protocol_class = getattr(module, class_name)

        assert getattr(protocol_class, "_is_protocol", False) is True

        actual_methods = {
            name
            for name, value in vars(protocol_class).items()
            if inspect.isfunction(value)
            and not name.startswith("_")
        }

        assert actual_methods == expected_methods

        for method_name in expected_methods:
            method = getattr(protocol_class, method_name)
            signature = inspect.signature(method)
            parameters = list(signature.parameters.values())

            assert inspect.iscoroutinefunction(method)
            assert parameters[0].name == "self"
            assert all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for parameter in parameters[1:]
            )

            hints = typing.get_type_hints(
                method,
                globalns=vars(module),
                localns=vars(module),
            )
            assert "return" in hints


def test_legacy_commerce_catalog_port_is_preserved() -> None:
    module = importlib.import_module("core.shopping.ports")
    symbol = getattr(module, "CommerceCatalogPort")

    assert symbol.__name__ == "CommerceCatalogPort"
    assert symbol.__module__ == "core.shopping.ports"
    assert Path(module.__file__).name == "__init__.py"


def test_provisional_contracts_are_exported() -> None:
    module = importlib.import_module(
        "core.shopping.contracts.provisional"
    )

    assert CONTRACT_NAMES <= set(module.__all__)

    for contract_name in CONTRACT_NAMES:
        assert hasattr(module, contract_name)


def test_no_write_capability_is_declared() -> None:
    for module_name in PORT_SPECS:
        file_name = module_name.rsplit(".", 1)[-1] + ".py"
        path = ROOT / "core" / "shopping" / "ports" / file_name
        content = path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(path))

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                assert node.name not in FORBIDDEN_PORTS

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                parts = set(node.name.lower().split("_"))
                assert not (parts & FORBIDDEN_METHOD_TOKENS)


def test_imports_have_no_external_side_effects() -> None:
    code = "\n".join([
        "import importlib",
        "import pathlib",
        "import socket",
        "import sqlite3",
        "import subprocess",
        "import urllib.request",
        "def blocked(*args, **kwargs):",
        "    raise RuntimeError(\"external side effect blocked\")",
        "socket.create_connection = blocked",
        "sqlite3.connect = blocked",
        "subprocess.Popen = blocked",
        "urllib.request.urlopen = blocked",
        "pathlib.Path.write_text = blocked",
        "pathlib.Path.write_bytes = blocked",
        "modules = " + repr(MODULES),
        "for name in modules:",
        "    importlib.import_module(name)",
    ])

    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, (
        result.stdout + "\n" + result.stderr
    )
