import ast
import copy
import inspect
import pickle

import pytest

from core.secrets import mariadb_continuity_protected_source_metadata as metadata_contract
from core.secrets.mariadb_continuity_evidence_concrete_source_location import (
    ProtectedExternalEvidenceConcreteSourceLocationIdentity as SourceIdentity,
)
from core.secrets.mariadb_continuity_protected_source_metadata import ProtectedSourceMetadataInspectionRequest
from core.secrets.mariadb_continuity_protected_source_metadata_port import ProtectedSourceMetadataInspectionCapability
from ops.macos.shopping import mariadb_continuity_protected_source_metadata_composition as composition


def test_production_composition_is_explicitly_unavailable() -> None:
    assert composition.OPERATIONAL_CANONICAL_PATH_ISSUER_IMPLEMENTED is False
    assert composition.PRODUCTION_OPERATIONAL_INSPECTION_AVAILABLE is False
    assert composition.OPERATIONAL_METADATA_EVIDENCE_ISSUER_IMPLEMENTED is False
    assert composition.compose_production_metadata_inspector() is None


def test_operational_metadata_evidence_issuer_fact_has_one_authoritative_definition() -> None:
    assert (
        composition.OPERATIONAL_METADATA_EVIDENCE_ISSUER_IMPLEMENTED
        is metadata_contract.OPERATIONAL_METADATA_EVIDENCE_ISSUER_IMPLEMENTED
    )
    tree = ast.parse(inspect.getsource(composition))
    imported_names = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module == "core.secrets.mariadb_continuity_protected_source_metadata"
        for alias in node.names
    }
    assigned_names = {
        target.id
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    assert "OPERATIONAL_METADATA_EVIDENCE_ISSUER_IMPLEMENTED" in imported_names
    assert "OPERATIONAL_METADATA_EVIDENCE_ISSUER_IMPLEMENTED" not in assigned_names


def test_inert_test_capability_is_nonserializable_noncopyable_and_one_shot() -> None:
    request = ProtectedSourceMetadataInspectionRequest.canonical(SourceIdentity.PYMYSQL_PROTECTED_EVIDENCE_LOCATION)
    capability = composition._issue_inert_test_inspection_capability(request)
    assert type(capability) is ProtectedSourceMetadataInspectionCapability
    for operation in (lambda: pickle.dumps(capability), lambda: copy.copy(capability), lambda: copy.deepcopy(capability)):
        with pytest.raises(TypeError): operation()
    assert capability._consume_then(request, lambda: "observed") == "observed"
    with pytest.raises(RuntimeError, match="already"):
        capability._consume_then(request, lambda: "retry")


def test_static_boundary_excludes_forbidden_operational_authorities() -> None:
    sources = "\n".join(inspect.getsource(module) for module in (
        composition,
        __import__("ops.macos.shopping.mariadb_continuity_protected_source_metadata_adapter", fromlist=["x"]),
    ))
    forbidden = ("ControlledExecutionPort", "PyMySQL", "pymysql", "subprocess", "docker", "colima", "UbuntuWorkerClient", "read_text", "read_bytes", "open(", "os.environ", "HOME", "argv", "socket", "SELECT ", "INSERT ", "UPDATE ")
    assert all(token not in sources for token in forbidden)
    assert all(token not in sources for token in ("glob(", "listdir(", "walk(", "iterdir("))
    assert "Protocol" not in sources
    assert "Callable" not in sources
