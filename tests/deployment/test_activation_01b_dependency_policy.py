from __future__ import annotations

from pathlib import Path
import ast
import json

from core.deployment.policy import (
    dependency_boundaries as dependency,
)

from core.deployment.policy import (
    validate_dependency_boundaries,
)


ROOT = Path(__file__).parents[2]

POLICY = (
    ROOT
    / "config/deployment/dependency-boundaries.json"
)


def test_package_relative_import_resolution():
    tree = ast.parse(
        "from .ports import HttpProbeRequest\n"
    )

    modules = {
        imported
        for imported, _, _ in dependency._imports(
            tree,
            "core.deployment.activation_inspector.__init__",
        )
    }

    assert (
        "core.deployment.activation_inspector.ports"
        in modules
    )

    assert "core.deployment.ports" not in modules


def test_ports_package_relative_import_resolution():
    tree = ast.parse(
        "from .audit import AuditEvidencePort\n"
    )

    modules = {
        imported
        for imported, _, _ in dependency._imports(
            tree,
            "core.deployment.ports.__init__",
        )
    }

    assert "core.deployment.ports.audit" in modules
    assert "core.deployment.audit" not in modules


def test_global_dependency_policy_passes():
    report = validate_dependency_boundaries(
        repository_root=ROOT
    )

    assert report["violations"] == []
    assert report["overall_result"] == "PASS"


def test_activation_inspector_dependency_zone():
    policy = json.loads(
        POLICY.read_text(encoding="utf-8")
    )

    directions = {
        item["from_zone"]: set(
            item["to_zones"]
        )
        for item in policy[
            "allowed_dependency_directions"
        ]
    }

    assert directions[
        "activation_inspector"
    ] == {
        "activation_inspector",
        "contracts",
        "git_readonly_evidence",
    }

    assert directions[
        "read_ports"
    ] == {
        "contracts",
        "read_ports",
        "audit_evidence",
    }
