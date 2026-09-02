import json
import os
import re
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[4]
NATIVE = ROOT / "macos/sec02_privileged_helper"
C5A = NATIVE / "ProductionSigningCredentialCeremony.swift"
C5B = NATIVE / "ProductionSigningCredentialImportCeremony.swift"
C4 = NATIVE / "ProductionSigningIdentityVerifier.swift"
SOURCE = NATIVE / "ProductionSigningCredentialAvailabilityObserver.swift"


@pytest.fixture(scope="module")
def results(tmp_path_factory):
    work = tmp_path_factory.mktemp("credential-availability")
    credential = work / "credential.p12"
    credential.touch(mode=0o600)
    credential.chmod(0o600)
    harness = work / "Harness.swift"
    harness.write_text(r'''import Foundation
final class Journal: SEC02ProductionCredentialAttemptConsuming {
    let claim: SEC02DurableAttemptClaim
    init(_ claim: SEC02DurableAttemptClaim = .claimed) { self.claim = claim }
    func claimOneAttempt(consumptionKey: SEC02CredentialImportConsumptionKey, ceremonyID: String) -> SEC02DurableAttemptClaim { claim }
    func recordTerminalOutcome(consumptionKey: SEC02CredentialImportConsumptionKey, ceremonyID: String, outcome: SEC02CredentialImportCeremonyState) -> Bool { true }
}
final class Capability: SEC02EphemeralNativeCredentialImportCapability {}
struct SecretBoundary: SEC02EphemeralInteractiveSecretAcquiring {
    func mediateOneNativeCredentialImport(_ operation: (any SEC02EphemeralNativeCredentialImportCapability) -> SEC02CredentialImportAttemptOutcome) -> SEC02CredentialImportAttemptOutcome { operation(Capability()) }
}
struct Importer: SEC02ProductionSigningCredentialImportAttempting {
    let outcome: SEC02CredentialImportAttemptOutcome
    func attemptProductionSigningCredentialImport(ceremonyID: String, validatedCredentialInput: SEC02ValidatedCredentialInputEvidence, secretAcquisition: any SEC02EphemeralInteractiveSecretAcquiring) -> SEC02CredentialImportAttemptOutcome { secretAcquisition.mediateOneNativeCredentialImport { _ in outcome } }
}
@main struct Harness {
  static func main() throws {
    let validation = SEC02ProductionSigningCredentialCeremony.validateExplicitPathForFutureImport(CommandLine.arguments[1])
    let evidence = validation.validatedCredentialInput
    var prepared = SEC02ProductionSigningCredentialImportCeremony(ceremonyID: "c6a", validatedCredentialInput: evidence)
    let ready = prepared.prepare()
    func terminal(_ outcome: SEC02CredentialImportAttemptOutcome) -> SEC02CredentialImportCeremonyResultV1 {
      var ceremony = SEC02ProductionSigningCredentialImportCeremony(ceremonyID: "c6a", validatedCredentialInput: evidence)
      _ = ceremony.prepare()
      return ceremony.attempt(using: Importer(outcome: outcome), secretAcquisition: SecretBoundary(), durableAttemptConsumer: Journal())
    }
    let cases = [
      "external": SEC02ProductionSigningCredentialAvailabilityObserver.inspectReadOnly(validatedCredentialInput: nil, importCeremonyResult: nil),
      "metadata": SEC02ProductionSigningCredentialAvailabilityObserver.inspectReadOnly(validatedCredentialInput: evidence, importCeremonyResult: nil),
      "import": SEC02ProductionSigningCredentialAvailabilityObserver.inspectReadOnly(validatedCredentialInput: evidence, importCeremonyResult: ready),
      "success": SEC02ProductionSigningCredentialAvailabilityObserver.inspectReadOnly(validatedCredentialInput: evidence, importCeremonyResult: terminal(.succeeded)),
      "failed": SEC02ProductionSigningCredentialAvailabilityObserver.inspectReadOnly(validatedCredentialInput: evidence, importCeremonyResult: terminal(.failed)),
      "uncertain": SEC02ProductionSigningCredentialAvailabilityObserver.inspectReadOnly(validatedCredentialInput: evidence, importCeremonyResult: terminal(.uncertain)),
    ]
    let encoder = JSONEncoder(); encoder.keyEncodingStrategy = .convertToSnakeCase
    var output: [String: Any] = [:]
    for (name, value) in cases { output[name] = try JSONSerialization.jsonObject(with: encoder.encode(value)) }
    print(String(data: try JSONSerialization.data(withJSONObject: output, options: [.sortedKeys]), encoding: .utf8)!)
  }
}''')
    binary = work / "harness"
    cache = work / "cache"
    cache.mkdir()
    environment = os.environ | {"CLANG_MODULE_CACHE_PATH": str(cache)}
    subprocess.run(
        ["xcrun", "swiftc", "-module-cache-path", str(cache), str(C5A), str(C5B),
         str(C4), str(SOURCE), str(harness), "-o", str(binary)],
        check=True, env=environment,
    )
    return json.loads(subprocess.run(
        [str(binary), str(credential)], check=True, text=True, capture_output=True,
    ).stdout)


def _assert_no_mutation_or_authority(value):
    for key in (
        "automatic_retry_performed", "credential_contents_read", "passphrase_handled",
        "credential_import_performed", "keychain_mutation_performed", "signing_performed",
        "notarization_performed", "sm_app_service_registration_performed",
        "production_mutation_performed", "production_authority_granted",
    ):
        assert value[key] is False


def test_distinct_readiness_states_and_c4_progression(results):
    assert results["external"]["availability"] == "EXTERNAL_CREDENTIAL_REQUIRED"
    assert results["metadata"]["availability"] == "LOCAL_INPUT_METADATA_READY"
    assert results["import"]["availability"] == "IMPORT_REQUIRED"
    assert results["success"]["availability"] in {
        "IDENTITY_VERIFICATION_REQUIRED", "PRODUCTION_SIGNING_IDENTITY_VERIFIED"
    }
    assert results["success"]["c4_verification_performed"] is True
    if results["success"]["availability"] == "PRODUCTION_SIGNING_IDENTITY_VERIFIED":
        assert results["success"]["production_signing_identity_verified"] is True
        assert re.fullmatch(r"[A-Z0-9]{10}", results["success"]["authoritative_team_id"])
    else:
        assert results["success"]["production_signing_identity_verified"] is False
        assert results["success"]["authoritative_team_id"] is None


def test_terminal_or_uncertain_input_never_opens_c4_or_retry(results):
    for name in ("failed", "uncertain"):
        assert results[name]["availability"] == "EXTERNAL_CREDENTIAL_REQUIRED"
        assert results[name]["c4_verification_performed"] is False
        assert results[name]["automatic_retry_performed"] is False
        assert results[name]["production_signing_identity_verified"] is False
        assert results[name]["authoritative_team_id"] is None


def test_all_observations_remain_read_only_and_non_authorizing(results):
    for value in results.values():
        assert value["inspection_read_only"] is True
        _assert_no_mutation_or_authority(value)


def test_security_surface_has_no_injected_authority_or_secret_and_mutation_apis():
    source = SOURCE.read_text()
    assert "inspectLocalKeychainReadOnly()" in source
    assert "resultFromAuthoritativeC4" in source
    assert "SEC02SigningIdentityObservation" not in source
    assert "SEC02CredentialMetadataInspecting" not in source
    assert "SEC02ProductionSigningIdentityResultV1?" not in source
    forbidden = (
        "Data(contentsOf:", "FileHandle", "SecPKCS12Import", "SecItemAdd", "SecItemUpdate",
        "SecItemDelete", "security import", "codesign", "notarytool", "SMAppService",
        ".register(", ".unregister(", "UbuntuWorkerClient", "getenv(",
        "ProcessInfo.processInfo.environment", "Process(", "CommandLine",
    )
    for token in forbidden:
        assert token not in source
    assert re.search(r"\b(?:passphrase|password)\b\s*[:=]", source, re.IGNORECASE) is None
