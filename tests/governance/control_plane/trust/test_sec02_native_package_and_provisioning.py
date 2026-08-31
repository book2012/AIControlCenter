from dataclasses import fields
import hashlib
import json
from pathlib import Path
import re
import plistlib

from core.governance.control_plane.trust.governance_privileged_helper import (
    CLIENT_CODE_SIGNING_REQUIREMENT, HELPER_CODE_SIGNING_REQUIREMENT,
    NativeReadiness, PeerSigningPolicy,
)
from core.governance.control_plane.trust.governance_remediation_authorization import (
    RemediationAuthorizationPurpose,
)
from core.governance.control_plane.trust.pre_bootstrap_journal_provisioning import (
    JournalProvisioningAuthorization, JournalProvisioningEligibility,
    JournalProvisioningPlan, JournalProvisioningPurpose,
    JournalProvisioningAction, JournalProvisioningReceipt, JournalTargetState,
    JournalProvisioningTerminalState,
    authorize_journal_provisioning, decide_journal_provisioning,
    validate_journal_provisioning_plan,
)
from macos.sec02_privileged_helper.validate_package import (
    EXPECTED, PackageContractError, build, load_contract, signing_readiness,
    validate_templates,
)
from macos.sec02_privileged_helper.build_native_package import (
    APP_EXECUTABLE as NATIVE_APP_EXECUTABLE,
    EXPECTED_FILES as NATIVE_EXPECTED_FILES,
    HELPER_EXECUTABLE as NATIVE_HELPER_EXECUTABLE,
    HELPER_INFO_PLIST,
    _inspect_thin_macho,
    _validate_exact_layout,
    build_native,
)
from core.governance.control_plane.trust.pre_bootstrap_remediation_journal import (
    AuthorizationReplayKey, FUTURE_PRODUCTION_JOURNAL_PATH,
)

ROOT = Path(__file__).parents[4]


def test_package_contract_is_repository_only_and_identity_fail_closed():
    contract = json.loads((ROOT / "macos/sec02_privileged_helper/package-contract.json").read_text())
    assert contract["authoritative_namespace"] == "com.aicontrolcenter"
    assert contract["registration_permitted"] is False
    assert contract["app_bundle_identifier"] == "com.aicontrolcenter.app"
    assert contract["helper_bundle_identifier"] == "com.aicontrolcenter.sec02-remediation-helper"
    assert contract["mach_service_identifier"] == "com.aicontrolcenter.sec02-remediation-helper"
    for key in ("team_identifier", "release_signing_identity",
                "client_code_signing_requirement", "helper_code_signing_requirement"):
        assert contract[key] is None
    assert CLIENT_CODE_SIGNING_REQUIREMENT is None
    assert HELPER_CODE_SIGNING_REQUIREMENT is None


def test_plist_templates_have_exact_non_caller_selected_values():
    templates = ROOT / "macos/sec02_privileged_helper/templates"
    app = plistlib.loads((templates / "App-Info.plist").read_bytes())
    helper = plistlib.loads((templates / "Helper-Info.plist").read_bytes())
    daemon = plistlib.loads((templates / "LaunchDaemon.plist").read_bytes())
    assert app["CFBundleIdentifier"] == EXPECTED["app_bundle_identifier"]
    assert helper["CFBundleIdentifier"] == EXPECTED["helper_bundle_identifier"]
    assert daemon["Label"] == EXPECTED["helper_bundle_identifier"]
    assert daemon["MachServices"] == {EXPECTED["mach_service_identifier"]: True}
    assert daemon["BundleProgram"] == "Contents/MacOS/SEC02GovernanceRemediationHelper"
    text = "\n".join(path.read_text() for path in templates.iterdir())
    assert "ProgramArguments" not in text
    assert "/Library" not in text
    assert "${" not in text


def test_package_builder_validates_exact_layout_and_signing_fails_closed(tmp_path):
    validate_templates()
    assert load_contract()["launchdaemon_plist_name"] == EXPECTED["launchdaemon_plist_name"]
    bundle = build((tmp_path / "AIControlCenter.app").resolve())
    assert (bundle / "Contents/MacOS/AIControlCenter").exists()
    assert not signing_readiness("TEAM", "raw-client", "raw-helper")
    try:
        build((tmp_path / "CallerSelected.app").resolve())
    except PackageContractError:
        pass
    else:
        raise AssertionError("caller-selected bundle path accepted")


def test_signing_policy_rejects_wildcards_permissive_and_swapped_roles():
    for value in ("*", "always true", "adhoc"):
        assert PeerSigningPolicy(value, "helper").readiness is NativeReadiness.NOT_READY
    assert PeerSigningPolicy("client", "helper").readiness is NativeReadiness.NOT_READY
    assert PeerSigningPolicy("concrete-client", "concrete-helper").readiness is NativeReadiness.NOT_READY


def test_raw_strings_cannot_create_production_xpc_signing_readiness():
    for client, helper in (("client", "helper"), ("anchor apple", "identifier helper")):
        assert PeerSigningPolicy(client, helper).readiness is NativeReadiness.NOT_READY


def test_native_replay_separator_and_digest_match_python_contract():
    python_source = (ROOT / "core/governance/control_plane/trust/pre_bootstrap_remediation_journal.py").read_text()
    swift_source = (ROOT / "macos/sec02_privileged_helper/NativeFoundation.swift").read_text()
    separator = re.search(r'_REPLAY_DOMAIN = b"([^"\\]*(?:\\.[^"\\]*)*)"', python_source)
    assert separator
    domain = separator.group(1).encode().decode("unicode_escape").encode("latin1")
    assert domain == b"AIControlCenter/SEC02/pre-bootstrap-remediation/replay/v1\0"
    assert 'AIControlCenter/SEC02/pre-bootstrap-remediation/replay/v1\\0' in swift_source
    raw = b"synthetic-external-form"
    value = AuthorizationReplayKey.derive_from_ephemeral_capability(raw).value
    assert value == hashlib.sha256(domain + raw).hexdigest()
    assert re.fullmatch(r"[0-9a-f]{64}", value)


def test_native_freshness_contract_has_no_reusable_authentication_context():
    swift_source = (ROOT / "macos/sec02_privileged_helper/NativeFoundation.swift").read_text()
    forbidden = ("kSecUseAuthenticationContext", "touchIDAuthenticationAllowableReuseDuration",
                 "evaluatePolicy(", "kSecAttrApplicationPassword", "softwareFallback",
                 "SecKeyCopyExternalRepresentation(key")
    assert all(token not in swift_source for token in forbidden)
    assert 'com.aicontrolcenter.sec02.fresh-human-presence.p256.v1' in swift_source
    assert "kSecAttrTokenIDSecureEnclave" in swift_source
    assert "[.userPresence, .privateKeyUsage]" in swift_source


def test_native_signing_metadata_is_used_only_after_static_validity_check():
    source = (ROOT / "macos/sec02_privileged_helper/NativeFoundation.swift").read_text()
    create = source.index("SecStaticCodeCreateWithPath")
    validity = source.index("SecStaticCodeCheckValidity", create)
    signing_info = source.index("SecCodeCopySigningInformation", create)
    assert create < validity < signing_info
    assert "kSecCSCheckAllArchitectures" in source
    assert "invalidSignature" in source
    for token in ("kSecCodeInfoIdentifier", "kSecCodeInfoTeamIdentifier",
                  "SecCodeSignatureFlags.adhoc.rawValue", "SecCodeCopyDesignatedRequirement"):
        assert source.index(token, create) > validity


def test_native_and_python_fresh_human_algorithm_identifiers_match_exactly():
    python_source = (ROOT / "core/governance/control_plane/trust/fresh_human_evidence.py").read_text()
    swift_source = (ROOT / "macos/sec02_privileged_helper/NativeFoundation.swift").read_text()
    algorithm = re.search(r'^ALGORITHM = "([^"]+)"$', python_source, re.MULTILINE)
    assert algorithm
    assert f'algorithm: "{algorithm.group(1)}"' in swift_source
    assert "ECDSA_P256_SHA256_X962" not in swift_source


def test_secure_enclave_lookup_is_all_results_exact_and_create_preflighted():
    source = (ROOT / "macos/sec02_privileged_helper/NativeFoundation.swift").read_text()
    assert "kSecMatchLimitAll" in source and "kSecReturnAttributes" in source
    assert "row[kSecAttrTokenID as String]" in source
    assert "kSecAttrTokenIDSecureEnclave" in source
    assert "case absent, exactOne(SecKey), ambiguous, unsafe" in source
    assert "if unsafe { return .unsafe }" in source
    assert "if rows.count > 1 { return .ambiguous }" in source
    provision = source[source.index("func provision_exact_fresh_human_key"):
                       source.index("func load_exact_public_key_identity")]
    assert provision.index("case .absent") < provision.index("SecKeyCreateRandomKey")
    assert all(token not in provision for token in ("SecItemDelete", "while ", "for "))


def test_public_fingerprint_is_only_x963_public_key_sha256_lowercase_hex():
    source = (ROOT / "macos/sec02_privileged_helper/NativeFoundation.swift").read_text()
    assert "SecKeyCopyPublicKey" in source
    assert "bytes.count == 65, bytes.first == 0x04" in source
    assert "SHA256.hash(data: bytes)" in source
    assert 'String(format: "%02x", $0)' in source
    assert "SecKeyCopyExternalRepresentation(key" not in source


def test_native_service_and_xpc_surface_is_fixed_and_non_operational():
    source = (ROOT / "macos/sec02_privileged_helper/NativeFoundation.swift").read_text()
    assert "SMAppService.daemon(plistName: SEC02Identity.launchDaemonPlist)" in source
    assert ".register()" not in source and ".unregister()" not in source
    assert source.count("func provisionPreBootstrapRemediationJournal(") == 1
    assert source.count("func restrictGovernanceDirectoryMode0755To0700(") == 1
    for token in ("operation:", "command:", "path:", "mode:", "uid:", "gid:"):
        assert token not in source


def test_provisioning_is_exact_create_only_and_separate_from_remediation():
    plan = JournalProvisioningPlan()
    authorization = JournalProvisioningAuthorization(plan.purpose, "request-1")
    assert authorize_journal_provisioning(plan, authorization) is JournalProvisioningEligibility.ELIGIBLE
    assert validate_journal_provisioning_plan(plan, observed_target=Path("/tmp/wrong")) is JournalProvisioningEligibility.DENIED
    assert authorize_journal_provisioning(plan, object()) is JournalProvisioningEligibility.DENIED
    assert not isinstance(plan.purpose, RemediationAuthorizationPurpose)
    forbidden = {"path", "chmod", "chown", "delete", "reset", "retry", "remediate",
                 "command", "argv", "mode", "uid", "gid"}
    assert forbidden.isdisjoint(field.name for field in fields(JournalProvisioningPlan))
    assert str(FUTURE_PRODUCTION_JOURNAL_PATH) == "/Library/Application Support/AIControlCenter/Security/PreBootstrapRemediation/attempt-journal.sqlite3"


def test_journal_provisioning_receipt_recognizes_only_exact_completed_state():
    receipt = JournalProvisioningReceipt(1, JournalProvisioningPurpose.CREATE_PRE_BOOTSTRAP_REMEDIATION_JOURNAL,
                                         "a" * 64, JournalProvisioningTerminalState.COMPLETED)
    assert decide_journal_provisioning(JournalTargetState.ABSENT) is JournalProvisioningAction.CREATE_ONCE
    assert decide_journal_provisioning(JournalTargetState.SAFE_EXISTING, receipt) is JournalProvisioningAction.RECOGNIZE_READ_ONLY
    assert decide_journal_provisioning(JournalTargetState.UNSAFE_EXISTING, receipt) is JournalProvisioningAction.FAIL_CLOSED
    assert decide_journal_provisioning(JournalTargetState.AMBIGUOUS) is JournalProvisioningAction.FAIL_CLOSED


def test_journal_receipt_rejects_malformed_fingerprint_and_wrong_terminal_state():
    purpose = JournalProvisioningPurpose.CREATE_PRE_BOOTSTRAP_REMEDIATION_JOURNAL
    for value in ("", "a" * 63, "A" * 64, "g" * 64):
        receipt = JournalProvisioningReceipt(
            1, purpose, value, JournalProvisioningTerminalState.COMPLETED
        )
        assert decide_journal_provisioning(
            JournalTargetState.SAFE_EXISTING, receipt
        ) is JournalProvisioningAction.FAIL_CLOSED
    wrong_state = JournalProvisioningReceipt(1, purpose, "a" * 64, "COMPLETED")
    assert decide_journal_provisioning(
        JournalTargetState.SAFE_EXISTING, wrong_state
    ) is JournalProvisioningAction.FAIL_CLOSED


def test_temporary_package_layout_does_not_claim_native_or_signed_readiness():
    from macos.sec02_privileged_helper import validate_package

    source = Path(validate_package.__file__).read_text()
    assert 'print("TEMPORARY_PACKAGE_LAYOUT_VALIDATED=YES")' in source
    assert "SIGNED_PACKAGE_READY" not in source
    assert "NATIVE_EXECUTABLE_BUILD_VALIDATED" not in source


def test_native_process_entrypoints_and_foundation_are_separate_and_inert():
    native = ROOT / "macos/sec02_privileged_helper"
    foundation = (native / "NativeFoundation.swift").read_text()
    app = (native / "AppMain.swift").read_text()
    helper_main = (native / "HelperMain.swift").read_text()
    all_process_source = app + helper_main
    assert "@main" not in foundation
    assert "@main" in app and "struct AIControlCenterMain" in app
    assert "@main" in helper_main and "struct SEC02GovernanceRemediationHelperMain" in helper_main
    assert "NSXPCListener(machServiceName: SEC02Identity.machService)" in helper_main
    assert "NSXPCInterface(with: SEC02PrivilegedHelperXPC.self)" in helper_main
    assert "guard signingPolicy.secureIncomingConnection(connection)" in helper_main
    policy_guard = helper_main.index("guard signingPolicy.secureIncomingConnection(connection)")
    resume = helper_main.index("connection.resume()")
    assert policy_guard < resume
    assert "clientRequirement: nil" in helper_main
    assert "helperRequirement: nil" in helper_main
    for token in (".register()", ".unregister()", "SecKeyCreateRandomKey",
                  "AuthorizationCreate", "provisionPreBootstrapRemediationJournal()",
                  "restrictGovernanceDirectoryMode0755To0700()"):
        assert token not in all_process_source


def test_helper_listener_delegate_has_explicit_strong_runtime_owner():
    source = (ROOT / "macos/sec02_privileged_helper/HelperMain.swift").read_text()
    runtime = source[source.index("private final class SEC02HelperRuntime"):
                     source.index("@main")]
    assert "private let listener: NSXPCListener" in runtime
    assert "private let delegate: SEC02HelperListenerDelegate" in runtime
    assert "listener.delegate = delegate" in runtime
    main = source[source.index("@main"):]
    assert "let runtime = SEC02HelperRuntime(signingPolicy: policy)" in main
    assert "runtime.run()" in main
    assert "let delegate = SEC02HelperListenerDelegate" not in main


def test_incoming_signing_policy_binds_exact_requirement_to_connection():
    source = (ROOT / "macos/sec02_privileged_helper/NativeFoundation.swift").read_text()
    start = source.index("public func secureIncomingConnection(")
    end = source.index("public func secureHelperConnection(", start)
    method = source[start:end]
    assert "_ connection: NSXPCConnection" in method
    assert "guard readiness == .ready, let value = clientRequirement else { return false }" in method
    assert "connection.setCodeSigningRequirement(value.expression)" in method
    assert "NSXPCListener" not in method
    assert "secureIncomingConnections(on:" not in source


def test_native_helper_implements_only_fixed_fail_closed_xpc_operations():
    source = (ROOT / "macos/sec02_privileged_helper/SEC02HelperService.swift").read_text()
    assert "NSObject, SEC02PrivilegedHelperXPC" in source
    assert source.count("func provisionPreBootstrapRemediationJournal(") == 1
    assert source.count("func restrictGovernanceDirectoryMode0755To0700(") == 1
    assert source.count("reply(.denied)") == 2
    forbidden = ("operation:", "command:", "path:", "mode:", "uid:", "gid:",
                 "chmod", "chown", "mkdir", "removeItem", "write(", "/Library/")
    assert all(token not in source for token in forbidden)


def test_real_native_builder_produces_exact_unsigned_macho_bundle(tmp_path):
    bundle = (tmp_path / "AIControlCenter.app").resolve()
    evidence = build_native(bundle)
    assert evidence == {
        "app_executable": {"mach_o": True, "name": NATIVE_APP_EXECUTABLE, "non_empty": True},
        "bundle_layout_valid": True,
        "helper_executable": {"mach_o": True, "name": NATIVE_HELPER_EXECUTABLE, "non_empty": True},
        "native_executables_built": True,
        "production_mutation_performed": False,
        "registration_performed": False,
        "schema_version": 1,
        "signed": False,
    }
    actual = {str(path.relative_to(bundle)) for path in bundle.rglob("*") if path.is_file()}
    assert actual == NATIVE_EXPECTED_FILES
    for name in (NATIVE_APP_EXECUTABLE, NATIVE_HELPER_EXECUTABLE):
        executable = bundle / "Contents/MacOS" / name
        assert executable.stat().st_size > 0
        assert executable.read_bytes()[:4] in {
            b"\xfe\xed\xfa\xce", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xcf",
            b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca",
            b"\xca\xfe\xba\xbf", b"\xbf\xba\xfe\xca",
        }
        _, has_code_signature = _inspect_thin_macho(executable)
        assert has_code_signature is False
    helper = bundle / "Contents/MacOS" / NATIVE_HELPER_EXECUTABLE
    embedded_plist, _ = _inspect_thin_macho(helper)
    assert embedded_plist is not None
    assert plistlib.loads(embedded_plist) == {
        "CFBundleExecutable": "SEC02GovernanceRemediationHelper",
        "CFBundleIdentifier": "com.aicontrolcenter.sec02-remediation-helper",
        "CFBundlePackageType": "BNDL",
    }
    unexpected = bundle / "Contents" / "unexpected"
    unexpected.write_text("not allowed")
    try:
        _validate_exact_layout(bundle)
    except PackageContractError:
        pass
    else:
        raise AssertionError("unexpected native bundle file accepted")


def test_native_builder_explicitly_disables_adhoc_signing_and_has_no_signing_tool():
    source = (ROOT / "macos/sec02_privileged_helper/build_native_package.py").read_text()
    assert '"-Xlinker", "-no_adhoc_codesign"' in source
    assert '["codesign"' not in source
    assert "subprocess.run(['codesign'" not in source
    assert ".touch(" not in source
    assert '"-Xlinker", "-sectcreate"' in source
    assert '"-Xlinker", os.fspath(HELPER_INFO_PLIST)' in source
    assert HELPER_INFO_PLIST == ROOT / "macos/sec02_privileged_helper/templates/Helper-Info.plist"
