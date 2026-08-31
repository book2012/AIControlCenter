import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[4]
NATIVE = ROOT / "macos/sec02_privileged_helper"
SOURCE = NATIVE / "ProductionSigningIdentityVerifier.swift"
MAIN = NATIVE / "ProductionSigningIdentityVerifierMain.swift"


def _compile_and_run(tmp_path: Path, body: str) -> dict:
    tmp_path.mkdir(parents=True, exist_ok=True)
    harness = tmp_path / "Harness.swift"
    harness.write_text(
        """import Foundation
@main struct Harness {
  static func main() throws {
    let result = %s
    let encoder = JSONEncoder()
    encoder.keyEncodingStrategy = .convertToSnakeCase
    encoder.outputFormatting = [.sortedKeys]
    print(String(data: try encoder.encode(result), encoding: .utf8)!)
  }
}
""" % body
    )
    binary = tmp_path / "verifier-tests"
    cache = tmp_path / "module-cache"
    cache.mkdir()
    environment = os.environ.copy()
    environment["CLANG_MODULE_CACHE_PATH"] = str(cache)
    subprocess.run(["xcrun", "swiftc", "-module-cache-path", str(cache),
                    str(SOURCE), str(harness), "-o", str(binary)],
                   check=True, env=environment)
    return json.loads(subprocess.run([str(binary)], check=True, text=True, capture_output=True).stdout)


def _observation(kind="app", valid=True, trust=True, key=True, team='"ABCDE12345"'):
    return (
        "SEC02SigningIdentityObservation("
        f'isDeveloperIDApplication: {str(kind == "app").lower()}, '
        f'certificateValid: {str(valid).lower()}, trustValid: {str(trust).lower()}, '
        f'privateKeyUsable: {str(key).lower()}, credentialTeamID: {team})'
    )


def test_no_candidate_is_absent_and_not_ready(tmp_path):
    value = _compile_and_run(tmp_path, "SEC02ProductionSigningIdentityVerifier.evaluate([])")
    assert value["candidate_state"] == "ABSENT"
    assert value["readiness"] == "NOT_READY"
    assert value["authoritative_team_id"] is None


def test_wrong_identity_types_and_self_signed_cannot_become_ready(tmp_path):
    # Installer, Apple Development, ad-hoc and arbitrary/self-signed evidence are
    # all non-Developer-ID-Application observations at the decision boundary.
    value = _compile_and_run(tmp_path, f"SEC02ProductionSigningIdentityVerifier.evaluate([{_observation(kind='other')}])")
    assert value["candidate_state"] == "INVALID"
    assert value["readiness"] == "NOT_READY"
    assert value["authoritative_team_id"] is None


def test_only_expired_untrusted_and_missing_private_key_fail_closed(tmp_path):
    expressions = [
        _observation(valid=False),
        _observation(trust=False),
        _observation(key=False),
    ]
    expected = ["INVALID", "UNTRUSTED", "PRIVATE_KEY_UNAVAILABLE"]
    for index, expression in enumerate(expressions):
        value = _compile_and_run(tmp_path / str(index), f"SEC02ProductionSigningIdentityVerifier.evaluate([{expression}])")
        assert value["candidate_state"] == expected[index]
        assert value["readiness"] == "NOT_READY"
        assert value["authoritative_team_id"] is None


def test_multiple_acceptable_candidates_are_ambiguous(tmp_path):
    candidate = _observation()
    value = _compile_and_run(tmp_path, f"SEC02ProductionSigningIdentityVerifier.evaluate([{candidate}, {candidate}])")
    assert value["candidate_state"] == "AMBIGUOUS"
    assert value["readiness"] == "NOT_READY"
    assert value["authoritative_team_id"] is None


def test_invalid_developer_id_observations_do_not_make_valid_candidate_ambiguous(tmp_path):
    candidate = _observation()
    cases = [
        ("expired", _observation(valid=False)),
        ("untrusted", _observation(trust=False)),
    ]
    for name, rejected in cases:
        value = _compile_and_run(
            tmp_path / name,
            f"SEC02ProductionSigningIdentityVerifier.evaluate([{candidate}, {rejected}])",
        )
        assert value["candidate_state"] == "EXACT_VALID_DEVELOPER_ID_APPLICATION"
        assert value["readiness"] == "READY"
        assert value["authoritative_team_id"] == "ABCDE12345"


def test_team_id_only_comes_from_fully_verified_credential(tmp_path):
    bad = _compile_and_run(tmp_path / "bad", f"SEC02ProductionSigningIdentityVerifier.evaluate([{_observation(team='\"caller-team\"')}])")
    good = _compile_and_run(tmp_path / "good", f"SEC02ProductionSigningIdentityVerifier.evaluate([{_observation()}])")
    assert bad["readiness"] == "NOT_READY" and bad["authoritative_team_id"] is None
    assert good["candidate_state"] == "EXACT_VALID_DEVELOPER_ID_APPLICATION"
    assert good["readiness"] == "READY" and good["authoritative_team_id"] == "ABCDE12345"


def test_json_and_native_surface_are_read_only_and_secret_free(tmp_path):
    value = _compile_and_run(tmp_path, f"SEC02ProductionSigningIdentityVerifier.evaluate([{_observation()}])")
    assert value["schema_version"] == 1
    assert value["production_mutation_performed"] is False
    assert value["keychain_mutation_performed"] is False
    assert value["signing_performed"] is False
    serialized = json.dumps(value).lower()
    for forbidden in ("private_key_material", "password", "credential_material", "apple_account", "authorization"):
        assert forbidden not in serialized
    source = SOURCE.read_text()
    for forbidden in ("SecItemAdd", "SecItemUpdate", "SecItemDelete", "SecKeyCreateSignature",
                      "SecKeyCreateRandomKey", "/usr/bin/codesign", ".register()", ".unregister()"):
        assert forbidden not in source
    assert "kSecUseAuthenticationUIFail" not in source
    assert "kSecUseAuthenticationUI" not in source
    assert "LAContext()" in source
    assert "interactionNotAllowed = true" in source
    assert "kSecUseAuthenticationContext" in source
    assert "evaluatePolicy(" not in source
    assert "SecKeyIsAlgorithmSupported" in source
    assert "CommandLine.arguments" not in source
    assert 'lines == ["0 valid identities found"]' in source
    assert "can never produce a candidate, Team ID, or READY result" in source


def test_cli_has_no_caller_selected_team_or_identity(tmp_path):
    binary = tmp_path / "production-signing-identity-verifier"
    cache = tmp_path / "module-cache"
    cache.mkdir()
    environment = os.environ.copy()
    environment["CLANG_MODULE_CACHE_PATH"] = str(cache)
    subprocess.run(["xcrun", "swiftc", "-module-cache-path", str(cache),
                    str(SOURCE), str(MAIN), "-o", str(binary)],
                   check=True, env=environment)
    result = subprocess.run([str(binary), "CALLERTEAM"], text=True, capture_output=True)
    assert result.returncode != 0
    assert result.stdout == ""
