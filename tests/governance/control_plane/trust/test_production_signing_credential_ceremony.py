import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[4]
NATIVE = ROOT / "macos/sec02_privileged_helper"
SOURCE = NATIVE / "ProductionSigningCredentialCeremony.swift"
MAIN = NATIVE / "ProductionSigningCredentialCeremonyMain.swift"


def _build(tmp_path, *sources):
    binary, cache = tmp_path / "ceremony", tmp_path / "cache"
    cache.mkdir()
    env = os.environ | {"CLANG_MODULE_CACHE_PATH": str(cache)}
    subprocess.run(
        ["xcrun", "swiftc", "-module-cache-path", str(cache), *map(str, sources), "-o", str(binary)],
        check=True,
        env=env,
    )
    return binary


@pytest.fixture(scope="module")
def synthetic_results(tmp_path_factory):
    path = tmp_path_factory.mktemp("ceremony-harness")
    harness = path / "Harness.swift"
    harness.write_text(
        '''import Foundation
struct Fake: SEC02CredentialMetadataInspecting {
    let value: SEC02CredentialMetadataLookup
    func inspectMetadataOnly(absolutePath: String) -> SEC02CredentialMetadataLookup { value }
}
func result(_ path: String?, _ lookup: SEC02CredentialMetadataLookup = .metadata(
    SEC02CredentialFileMetadata(regularFile: true, ownerUID: getuid(), mode: 0o600)
)) -> SEC02ProductionSigningCredentialCeremonyResultV1 {
    SEC02ProductionSigningCredentialCeremony.evaluateLocalInputOnly(
        SEC02ProductionSigningCredentialCeremony.inspectExplicitPathReadOnly(path, inspector: Fake(value: lookup)))
}
@main struct Harness {
    static func main() throws {
        let values = [
            "absent": result(nil), "empty": result(""),
            "p12": result("/x/a.p12"), "pfx": result("/x/a.pfx"),
            "upper_p12": result("/x/a.P12"), "upper_pfx": result("/x/a.PFX"),
            "mixed": result("/x/a.pFx"), "relative": result("a.p12"),
            "dot": result("/x/./a.p12"), "dotdot": result("/x/../a.p12"),
            "suffix": result("/x/a.pem"), "missing": result("/x/a.p12", .pathDoesNotExist),
            "symlink": result("/x/a.p12", .symlinkTraversalRejected),
            "nonregular": result("/x/a.p12", .metadata(SEC02CredentialFileMetadata(
                regularFile: false, ownerUID: getuid(), mode: 0o755))),
            "owner": result("/x/a.p12", .metadata(SEC02CredentialFileMetadata(
                regularFile: true, ownerUID: getuid() + 1, mode: 0o600))),
            "group": result("/x/a.p12", .metadata(SEC02CredentialFileMetadata(
                regularFile: true, ownerUID: getuid(), mode: 0o620))),
            "world": result("/x/a.p12", .metadata(SEC02CredentialFileMetadata(
                regularFile: true, ownerUID: getuid(), mode: 0o602)))
        ]
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.outputFormatting = [.sortedKeys]
        print(String(data: try encoder.encode(values), encoding: .utf8)!)
    }
}
'''
    )
    binary = _build(path, SOURCE, harness)
    output = subprocess.run([str(binary)], check=True, text=True, capture_output=True).stdout
    return json.loads(output)


def _run(binary, path):
    completed = subprocess.run([str(binary), str(path)], check=True, text=True, capture_output=True)
    return completed.stdout, json.loads(completed.stdout)


def _no_authority(value):
    for key in (
        "credential_imported", "production_signing_identity_verified", "package_signed",
        "sm_app_service_registered", "production_remediation_authorized", "signing_performed",
        "notarization_performed", "production_mutation_performed",
    ):
        assert value[key] is False
    assert value["authoritative_team_id"] is None
    assert value["ceremony_state"] != "LIVE_IDENTITY_READY"


def test_state_model_metadata_rules_and_authority(synthetic_results):
    absent = synthetic_results["absent"]
    assert absent["ceremony_state"] == "LOCAL_CREDENTIAL_INPUT_ABSENT"
    assert absent["readiness"] == "EXTERNAL_CREDENTIAL_REQUIRED"
    empty = synthetic_results["empty"]
    assert empty["ceremony_state"] == "LOCAL_CREDENTIAL_INPUT_ABSENT"
    assert empty["readiness"] == "EXTERNAL_CREDENTIAL_REQUIRED"
    assert empty["credential_input"]["failure"] == "EXPLICIT_PATH_REQUIRED"
    for name in ("p12", "pfx"):
        value = synthetic_results[name]
        assert value["ceremony_state"] == "LOCAL_CREDENTIAL_INPUT_READY"
        assert value["readiness"] == "READY_FOR_SEPARATE_IMPORT_CEREMONY"
        _no_authority(value)
    expected = {
        "upper_p12": "UNSUPPORTED_CONTAINER_SUFFIX", "upper_pfx": "UNSUPPORTED_CONTAINER_SUFFIX",
        "mixed": "UNSUPPORTED_CONTAINER_SUFFIX",
        "relative": "PATH_MUST_BE_ABSOLUTE", "dot": "PATH_COMPONENT_REJECTED",
        "dotdot": "PATH_COMPONENT_REJECTED", "suffix": "UNSUPPORTED_CONTAINER_SUFFIX",
        "missing": "PATH_DOES_NOT_EXIST", "symlink": "SYMLINK_TRAVERSAL_REJECTED",
        "nonregular": "REGULAR_FILE_REQUIRED", "owner": "INVOKING_DARWIN_USER_MUST_OWN_FILE",
        "group": "GROUP_WRITABLE", "world": "WORLD_WRITABLE",
    }
    for name, failure in expected.items():
        value = synthetic_results[name]
        assert value["ceremony_state"] == value["readiness"] == "NOT_READY"
        assert value["credential_input"]["failure"] == failure
        _no_authority(value)


def test_real_explicit_path_validation_uses_only_empty_synthetic_files(tmp_path):
    binary = _build(tmp_path, SOURCE, MAIN)
    fixture = tmp_path / "empty.p12"
    fixture.touch()
    fixture.chmod(0o600)
    first_output, value = _run(binary, fixture)
    second_output, _ = _run(binary, fixture)
    assert first_output == second_output
    assert list(value) == sorted(value)
    assert value["credential_input"]["container_suffix"] == ".p12"
    assert value["credential_contents_read"] is False
    _no_authority(value)

    missing = tmp_path / "missing.p12"
    assert _run(binary, missing)[1]["credential_input"]["failure"] == "PATH_DOES_NOT_EXIST"
    directory = tmp_path / "directory.p12"
    directory.mkdir()
    assert _run(binary, directory)[1]["credential_input"]["failure"] == "REGULAR_FILE_REQUIRED"
    leaf_link = tmp_path / "leaf.p12"
    leaf_link.symlink_to(fixture)
    assert _run(binary, leaf_link)[1]["credential_input"]["failure"] == "SYMLINK_TRAVERSAL_REJECTED"
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    parent_file = real_parent / "empty.p12"
    parent_file.touch()
    parent_link = tmp_path / "linked-parent"
    parent_link.symlink_to(real_parent, target_is_directory=True)
    assert _run(binary, parent_link / "empty.p12")[1]["credential_input"]["failure"] == "SYMLINK_TRAVERSAL_REJECTED"


def test_future_import_contract_and_security_surface(tmp_path):
    binary = _build(tmp_path, SOURCE, MAIN)
    fixture = tmp_path / "empty.pfx"
    fixture.touch()
    fixture.chmod(0o600)
    value = _run(binary, fixture)[1]
    contract = value["future_import_contract"]
    assert contract["platform"] == "MAC_ONLY"
    assert contract["requires_separate_explicit_human_security_ceremony"] is True
    assert contract["bounded_credential_import_attempts"] == 1
    assert contract["automatic_retry_allowed"] is False
    assert contract["failed_or_uncertain_import_requires_new_ceremony"] is True
    assert contract["credential_reuse_allowed_after_failed_or_uncertain_import"] is False
    assert contract["production_runtime_mutation_authority"] is False
    assert contract["import_success_establishes_production_signing_identity_verified"] is False
    assert contract["subsequent_c4_production_signing_identity_verifier_required"] is True
    assert contract["authoritative_team_id_source"] == "C4_PRODUCTION_SIGNING_IDENTITY_VERIFIER_ONLY"
    for key in (
        "passphrase_stored_in_repository", "passphrase_logged", "passphrase_persisted",
        "passphrase_accepted_as_command_line_argument", "passphrase_accepted_through_environment_variable",
    ):
        assert contract[key] is False

    for args in ([], ["--password", "x"], ["--passphrase", "x"], ["/x.p12", "--team-id", "X"]):
        assert subprocess.run([str(binary), *args], text=True, capture_output=True).returncode != 0
    source = SOURCE.read_text() + MAIN.read_text()
    forbidden = (
        "FileManager.default.urls", "homeDirectoryForCurrentUser", "enumerator(", "Data(contentsOf:",
        "readDataToEndOfFile", "SecPKCS12Import", "SecItemAdd", "SecItemUpdate", "SecItemDelete",
        "Process(", "security import", "codesign", "notarytool", "SMAppService", ".register(",
        ".unregister(", "c4IdentityResult", "teamID:", "--password", "--passphrase", "getenv(",
        "ProcessInfo.processInfo.environment", "UbuntuWorkerClient", "productionMutationPerformed = true",
    )
    for token in forbidden:
        assert token not in source
    assert "ProductionSigningIdentityVerifier" in SOURCE.read_text()
    assert "public protocol SEC02CredentialMetadataInspecting" not in source
    assert "public enum SEC02CredentialMetadataLookup" not in source
    assert "public struct SEC02CredentialFileMetadata" not in source
