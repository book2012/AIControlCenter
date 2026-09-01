import json
import os
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[4]
NATIVE = ROOT / "macos/sec02_privileged_helper"
C5A = NATIVE / "ProductionSigningCredentialCeremony.swift"
SOURCE = NATIVE / "ProductionSigningCredentialImportCeremony.swift"


@pytest.fixture(scope="module")
def results(tmp_path_factory):
    work = tmp_path_factory.mktemp("credential-import-ceremony")
    valid = work / "credential.p12"
    valid.touch(mode=0o600)
    os.chmod(valid, 0o600)
    bad_mode = work / "unsafe.p12"
    bad_mode.touch(mode=0o666)
    os.chmod(bad_mode, 0o666)
    harness = work / "Harness.swift"
    harness.write_text(r'''import Foundation
final class Counter { var calls = 0; var mediations = 0; var capabilityOperations = 0 }
final class ZeroSecretTestCapability: SEC02EphemeralNativeCredentialImportCapability {}
struct SecretBoundary: SEC02EphemeralInteractiveSecretAcquiring {
    let counter: Counter
    func mediateOneNativeCredentialImport(_ operation: (any SEC02EphemeralNativeCredentialImportCapability) -> SEC02CredentialImportAttemptOutcome) -> SEC02CredentialImportAttemptOutcome {
        counter.mediations += 1
        return operation(ZeroSecretTestCapability())
    }
}
struct ForgedInspector: SEC02CredentialMetadataInspecting {
    func inspectMetadataOnly(absolutePath: String) -> SEC02CredentialMetadataLookup {
        .metadata(SEC02CredentialFileMetadata(regularFile: true, ownerUID: getuid(), mode: 0o600,
            device: 999, inode: 999, birthSeconds: 1, birthNanoseconds: 1))
    }
}
final class FakeJournal: SEC02ProductionCredentialAttemptConsuming {
    private var terminalByInput: [SEC02ValidatedCredentialInputBinding: SEC02CredentialImportCeremonyState] = [:]
    var nextClaim: SEC02DurableAttemptClaim = .claimed; var nextTerminalRecordSucceeds = true
    private(set) var callOrder: [String] = []
    func noteImporterInvocation() { callOrder.append("import") }
    func claimOneAttempt(consumptionKey: SEC02CredentialImportConsumptionKey, ceremonyID: String) -> SEC02DurableAttemptClaim {
        callOrder.append("claim")
        if let terminal = terminalByInput[consumptionKey.validatedCredentialInputBinding] { return .alreadyConsumed(terminal) }
        switch nextClaim {
        case .claimed: terminalByInput[consumptionKey.validatedCredentialInputBinding] = .uncertainConsumed; return .claimed
        case .failedConsumed: terminalByInput[consumptionKey.validatedCredentialInputBinding] = .failedConsumed; return .failedConsumed
        case .uncertainConsumed: terminalByInput[consumptionKey.validatedCredentialInputBinding] = .uncertainConsumed; return .uncertainConsumed
        case let .alreadyConsumed(outcome): terminalByInput[consumptionKey.validatedCredentialInputBinding] = outcome; return .alreadyConsumed(outcome)
        }
    }
    func recordTerminalOutcome(consumptionKey: SEC02CredentialImportConsumptionKey, ceremonyID: String, outcome: SEC02CredentialImportCeremonyState) -> Bool {
        callOrder.append("terminal"); guard nextTerminalRecordSucceeds else { return false }; terminalByInput[consumptionKey.validatedCredentialInputBinding] = outcome; return true
    }
}
struct Importer: SEC02ProductionSigningCredentialImportAttempting {
    let outcome: SEC02CredentialImportAttemptOutcome; let counter: Counter; let journal: FakeJournal
    func attemptProductionSigningCredentialImport(ceremonyID: String, validatedCredentialInput: SEC02ValidatedCredentialInputEvidence, secretAcquisition: any SEC02EphemeralInteractiveSecretAcquiring) -> SEC02CredentialImportAttemptOutcome {
        counter.calls += 1; journal.noteImporterInvocation()
        return secretAcquisition.mediateOneNativeCredentialImport { capability in
            _ = capability
            counter.capabilityOperations += 1
            return outcome
        }
    }
}
func run(_ path: String, outcome: SEC02CredentialImportAttemptOutcome, claim: SEC02DurableAttemptClaim = .claimed, record: Bool = true, reconstruct: Bool = false, newCeremony: Bool = false) -> [String: Any] {
    let input = SEC02ProductionSigningCredentialCeremony.validateExplicitPathForFutureImport(path)
    let counter = Counter(); let journal = FakeJournal(); journal.nextClaim = claim; journal.nextTerminalRecordSucceeds = record
    var ceremony = SEC02ProductionSigningCredentialImportCeremony(ceremonyID: "ceremony-01", validatedCredentialInput: input.validatedCredentialInput)
    let secretBoundary = SecretBoundary(counter: counter)
    let ready = ceremony.prepare(); let first = ceremony.attempt(using: Importer(outcome: outcome, counter: counter, journal: journal), secretAcquisition: secretBoundary, durableAttemptConsumer: journal)
    var retry = SEC02ProductionSigningCredentialImportCeremony(ceremonyID: newCeremony ? "ceremony-02" : "ceremony-01", validatedCredentialInput: input.validatedCredentialInput)
    let second = reconstruct || newCeremony ? retry.prepare() : ceremony.prepare()
    let final = reconstruct || newCeremony ? retry.attempt(using: Importer(outcome: .succeeded, counter: counter, journal: journal), secretAcquisition: secretBoundary, durableAttemptConsumer: journal) : ceremony.attempt(using: Importer(outcome: .succeeded, counter: counter, journal: journal), secretAcquisition: secretBoundary, durableAttemptConsumer: journal)
    let encoder = JSONEncoder(); encoder.keyEncodingStrategy = .convertToSnakeCase
    func object(_ v: SEC02CredentialImportCeremonyResultV1) -> Any { try! JSONSerialization.jsonObject(with: try! encoder.encode(v)) }
    return ["ready": object(ready), "first": object(first), "second": object(second), "final": object(final), "calls": counter.calls, "mediations": counter.mediations, "capability_operations": counter.capabilityOperations, "order": journal.callOrder, "valid_input": input.validatedCredentialInput != nil, "input_state": input.observation.status.rawValue]
}
@main struct Harness { static func main() throws {
    let args = CommandLine.arguments
    let valid = args[1]; let bad = args[2]
    let forged = SEC02CredentialInputObservation(status: .valid, failure: nil, containerSuffix: ".p12", regularFile: true, ownedByInvokingDarwinUser: true, groupWritable: false, worldWritable: false, symlinkTraversalDetected: false)
    let injectedObservation = SEC02ProductionSigningCredentialCeremony.inspectExplicitPathReadOnly("/fabricated/input.p12", inspector: ForgedInspector())
    let injectedCannotIssue = SEC02ProductionSigningCredentialCeremony.validateExplicitPathForFutureImport("/fabricated/input.p12")
    let forgedReady = SEC02ProductionSigningCredentialImportCeremony(ceremonyID: "forged", validatedCredentialInput: nil).currentResult()
    let output: [String: Any] = ["success": run(valid, outcome: .succeeded), "failed": run(valid, outcome: .failed), "uncertain": run(valid, outcome: .uncertain), "claim_failed": run(valid, outcome: .succeeded, claim: .failedConsumed), "claim_uncertain": run(valid, outcome: .succeeded, claim: .uncertainConsumed), "invalid_consumed_state": run(valid, outcome: .succeeded, claim: .alreadyConsumed(.ready)), "record_failed": run(valid, outcome: .succeeded, record: false), "invalid": run(bad, outcome: .succeeded), "reconstructed": run(valid, outcome: .succeeded, reconstruct: true), "new_ceremony": run(valid, outcome: .succeeded, newCeremony: true), "forged_observation_status": forged.status.rawValue, "forged_ready": try! JSONSerialization.jsonObject(with: JSONEncoder().encode(forgedReady)), "injected_observation_status": injectedObservation.status.rawValue, "injected_evidence": injectedCannotIssue.validatedCredentialInput != nil]
    print(String(data: try JSONSerialization.data(withJSONObject: output, options: [.sortedKeys]), encoding: .utf8)!)
} }''')
    binary, cache = work / "harness", work / "cache"
    cache.mkdir()
    subprocess.run(["xcrun", "swiftc", "-module-cache-path", str(cache), str(C5A), str(SOURCE), str(harness), "-o", str(binary)], check=True, env=os.environ | {"CLANG_MODULE_CACHE_PATH": str(cache)})
    return json.loads(subprocess.run([str(binary), str(valid), str(bad_mode)], check=True, text=True, capture_output=True).stdout)


def _assert_no_authority(value):
    assert value["live_credential_import_verified"] is False
    assert value["production_signing_identity_verified"] is False
    assert value["authoritative_team_id"] is None
    for key in ("signed_package_ready", "keychain_mutation_performed", "signing_performed", "notarization_performed", "sm_app_service_authority_granted", "sm_app_service_registration_operational", "governance_remediation_authority_granted", "production_remediation_available", "production_runtime_mutation_authority_granted", "production_mutation_performed"):
        assert value[key] is False


def test_only_actual_c5a_validation_can_issue_ready_evidence(results):
    assert results["success"]["valid_input"] is True
    assert results["invalid"]["valid_input"] is False
    assert results["invalid"]["ready"]["ceremony_state"] == "NOT_STARTED"
    assert results["invalid"]["calls"] == 0
    assert results["forged_observation_status"] == "VALID"
    assert results["forged_ready"]["ceremonyState"] == "NOT_STARTED"
    assert results["injected_observation_status"] == "VALID"
    assert results["injected_evidence"] is False
    c5a = C5A.read_text()
    assert "validateExplicitPathForFutureImport(\n        _ explicitPath: String?, inspector:" not in c5a
    assert "futureImportLocator" in c5a
    assert "fileprivate struct SEC02FutureCredentialImportLocator" in c5a
    assert "O_NOFOLLOW" in c5a and "st_birthtimespec" in c5a
    assert "credentialFingerprint" not in SOURCE.read_text()


def test_durable_claim_precedes_one_adapter_call_and_blocks_retries(results):
    success = results["success"]
    assert success["ready"]["ceremony_state"] == "READY"
    assert success["calls"] == 1 and success["order"] == ["claim", "import", "terminal"]
    assert success["mediations"] == 1 and success["capability_operations"] == 1
    assert success["first"]["adapter_reported_success"] is True
    assert success["final"] == success["first"]
    assert results["reconstructed"]["calls"] == 1
    assert results["reconstructed"]["mediations"] == 1
    assert results["reconstructed"]["final"]["ceremony_state"] == "SUCCEEDED_PENDING_C4_VERIFICATION"
    assert results["reconstructed"]["final"]["c4_verification_required"] is True
    assert results["new_ceremony"]["calls"] == 1
    assert results["new_ceremony"]["mediations"] == 1
    assert results["new_ceremony"]["final"]["ceremony_state"] == "SUCCEEDED_PENDING_C4_VERIFICATION"
    assert results["new_ceremony"]["final"]["c4_verification_required"] is True


def test_consumed_and_terminal_failures_fail_closed(results):
    for name, state in (("failed", "FAILED_CONSUMED"), ("uncertain", "UNCERTAIN_CONSUMED"), ("claim_failed", "FAILED_CONSUMED"), ("claim_uncertain", "UNCERTAIN_CONSUMED"), ("record_failed", "UNCERTAIN_CONSUMED")):
        value = results[name]
        assert value["first"]["ceremony_state"] == state
        assert value["first"]["credential_reuse_allowed"] is False
        if name.startswith("claim_"):
            assert value["calls"] == 0
            assert value["mediations"] == 0 and value["capability_operations"] == 0
        else:
            assert value["mediations"] == 1 and value["capability_operations"] == 1
        _assert_no_authority(value["first"])
    assert results["record_failed"]["first"]["adapter_reported_success"] is True
    assert results["record_failed"]["first"]["c4_verification_required"] is False
    invalid_consumed = results["invalid_consumed_state"]
    assert invalid_consumed["first"]["ceremony_state"] == "UNCERTAIN_CONSUMED"
    assert invalid_consumed["calls"] == 0 and invalid_consumed["mediations"] == 0


def test_adapter_success_is_not_live_import_or_c4_verification(results):
    value = results["success"]["first"]
    assert value["adapter_reported_success"] is True
    assert value["c4_verification_required"] is True
    _assert_no_authority(value)


def test_no_runtime_fake_secret_or_live_authority_surface():
    source = SOURCE.read_text()
    all_c5b_source = source + C5A.read_text()
    assert "SEC02DeterministicFakeDurableAttemptConsumer" not in source
    assert "SEC02CredentialImportAttemptClaimKey" not in source
    assert "struct SEC02CredentialImportConsumptionKey: Hashable" in source
    assert 'case attempting = "ATTEMPTING"' in source
    assert "case .notStarted, .ready, .attempting:" in source
    assert "let ceremonyID" not in source.split("struct SEC02CredentialImportConsumptionKey", 1)[1].split("}", 1)[0]
    forbidden = ("CommandLine", "ProcessInfo.processInfo.environment", "getenv(", "UserDefaults", "Data(contentsOf:", "FileHandle", "Process(", "security import", "SecPKCS12Import", "SecItemAdd", "SecItemUpdate", "SecItemDelete", "codesign", "notarytool", "SMAppService", "UbuntuWorkerClient", "teamID:", "signingIdentity:")
    for token in forbidden: assert token not in source
    for token in ("FileManager.default.urls", "homeDirectoryForCurrentUser", "enumerator(",
                  "Data(contentsOf:", "FileHandle", "UserDefaults", "getenv(",
                  "ProcessInfo.processInfo.environment"):
        assert token not in all_c5b_source
    assert "ProductionSigningIdentityVerifier" not in source
    assert "mediateOneNativeCredentialImport" in source
    assert "protocol SEC02EphemeralNativeCredentialImportCapability: AnyObject {}" in source
    assert re.search(r"_ operation: \(any SEC02EphemeralNativeCredentialImportCapability\)\s*-> SEC02CredentialImportAttemptOutcome", source)
    capability = source.split("protocol SEC02EphemeralNativeCredentialImportCapability", 1)[1].split("protocol SEC02EphemeralInteractiveSecretAcquiring", 1)[0]
    for token in ("String", "Data", "passphrase", "password", "Encodable", "Codable", "static", "UserDefaults", "Thread", "threadLocal"):
        assert token not in capability
    assert "SEC02EphemeralNativeCredentialImportCapability" not in source.split("struct SEC02NonMutatingCredentialImportAdapter", 1)[1]
    assert re.search(r"\b(?:passphrase|password)\b\s*[:=]", source, re.IGNORECASE) is None
