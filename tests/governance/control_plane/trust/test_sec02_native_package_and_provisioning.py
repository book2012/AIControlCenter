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
    authorize_journal_provisioning, decide_journal_provisioning,
    validate_journal_provisioning_plan,
)
from macos.sec02_privileged_helper.validate_package import (
    EXPECTED, PackageContractError, build, load_contract, signing_readiness,
    validate_templates,
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
                                         "a" * 64, "COMPLETED")
    assert decide_journal_provisioning(JournalTargetState.ABSENT) is JournalProvisioningAction.CREATE_ONCE
    assert decide_journal_provisioning(JournalTargetState.SAFE_EXISTING, receipt) is JournalProvisioningAction.RECOGNIZE_READ_ONLY
    assert decide_journal_provisioning(JournalTargetState.UNSAFE_EXISTING, receipt) is JournalProvisioningAction.FAIL_CLOSED
    assert decide_journal_provisioning(JournalTargetState.AMBIGUOUS) is JournalProvisioningAction.FAIL_CLOSED
