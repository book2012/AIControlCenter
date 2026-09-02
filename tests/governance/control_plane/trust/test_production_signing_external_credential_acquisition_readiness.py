import json
import os
import re
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[4]
SOURCE = ROOT / "macos/sec02_privileged_helper/ProductionSigningExternalCredentialAcquisitionReadiness.swift"


@pytest.fixture(scope="module")
def results(tmp_path_factory):
    work = tmp_path_factory.mktemp("external-credential-readiness")
    harness = work / "Harness.swift"
    harness.write_text(r'''import Foundation
@main struct Harness {
  static func main() throws {
    func inspect(_ credentialClass: SEC02ExternalCredentialClass,
                 _ key: Bool = true,
                 _ authority: SEC02ExternalCredentialAuthorityClaim = .c4VerificationRequired)
      -> SEC02ExternalCredentialAcquisitionReadinessResultV1 {
      SEC02ProductionSigningExternalCredentialAcquisitionReadiness.inspectReadOnly(
        SEC02ExternalCredentialCandidateObservation(
          credentialClass: credentialClass, matchingPrivateKeyRepresented: key,
          authorityClaim: authority))
    }
    let cases = [
      "absent": SEC02ProductionSigningExternalCredentialAcquisitionReadiness.inspectReadOnly(nil),
      "acceptable": inspect(.developerIDApplication),
      "missing_key": inspect(.developerIDApplication, false),
      "development": inspect(.appleDevelopment),
      "adhoc": inspect(.adHoc),
      "self_signed": inspect(.selfSigned),
      "installer": inspect(.developerIDInstaller),
      "unsupported": inspect(.unsupported),
      "invented_team": inspect(.developerIDApplication, true, .inventedTeamID),
      "xcode": inspect(.developerIDApplication, true, .xcodeDerived),
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
    subprocess.run(["xcrun", "swiftc", "-module-cache-path", str(cache), str(SOURCE),
                    str(harness), "-o", str(binary)], check=True, env=environment)
    return json.loads(subprocess.run([str(binary)], check=True, text=True,
                                     capture_output=True).stdout)


def test_only_developer_id_application_with_matching_private_key_is_acceptable(results):
    acceptable = results["acceptable"]
    assert acceptable["readiness"] == "ACCEPTABLE_CANDIDATE_REPRESENTED"
    assert acceptable["credential_class"] == "APPLE_DEVELOPER_ID_APPLICATION"
    assert acceptable["matching_private_key_represented"] is True
    assert acceptable["c5_a_ceremony_may_eventually_proceed"] is True
    assert acceptable["c5_b_ceremony_may_eventually_proceed"] is True
    assert results["missing_key"]["readiness"] == "MATCHING_PRIVATE_KEY_REQUIRED"
    assert results["missing_key"]["c5_a_ceremony_may_eventually_proceed"] is False


def test_unsupported_credential_classes_and_authority_claims_are_rejected(results):
    for name in ("development", "adhoc", "self_signed", "installer", "unsupported"):
        assert results[name]["readiness"] == "REJECTED_CREDENTIAL_CLASS"
    for name in ("invented_team", "xcode"):
        assert results[name]["readiness"] == "REJECTED_AUTHORITY_CLAIM"
        assert results[name]["c5_b_ceremony_may_eventually_proceed"] is False


def test_json_is_deterministic_non_authorizing_and_team_id_stays_null(results):
    assert results["absent"]["readiness"] == "CANDIDATE_ABSENT"
    for value in results.values():
        assert value["schema_version"] == 1
        assert value["authoritative_team_id"] is None
        assert value["platform"] == "MAC_ONLY"
        assert value["repository_only"] is True
        assert value["inspection_read_only"] is True
        assert value["c4_verification_required_after_future_import"] is True
        for key in ("credential_acquired", "credential_downloaded", "credential_contents_read",
                    "passphrase_handled", "credential_imported", "keychain_mutation_performed",
                    "signing_performed", "notarization_performed",
                    "sm_app_service_registration_performed", "production_mutation_performed",
                    "production_authority_granted", "ubuntu_authority_granted"):
            assert value[key] is False


def test_source_has_no_secret_mutation_runtime_or_team_id_authority_surface():
    source = SOURCE.read_text()
    forbidden = ("Darwin", "Security", "LocalAuthentication", "UbuntuWorkerClient",
                 "Data(contentsOf:", "FileHandle", "Process(", "CommandLine", "getenv(",
                 "ProcessInfo.processInfo.environment", "SecPKCS12Import", "SecItemAdd",
                 "SecItemUpdate", "SecItemDelete", "codesign", "notarytool", "SMAppService",
                 ".register(", ".unregister(")
    for token in forbidden:
        assert token not in source
    assert re.search(r"\b(?:passphrase|password)\b\s*[:=]", source, re.IGNORECASE) is None
    assert "credentialTeamID" not in source and "teamID:" not in source
    assert "authoritativeTeamID: String? = nil" in source
