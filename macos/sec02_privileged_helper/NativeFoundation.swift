import Foundation
import CryptoKit
import Security
import ServiceManagement

// Source-only foundation. No top-level code registers a service, creates a key,
// authenticates a human, opens XPC, or performs either privileged mutation.

public enum SEC02Identity {
    public static let appBundleID = "com.aicontrolcenter.app"
    public static let helperBundleID = "com.aicontrolcenter.sec02-remediation-helper"
    public static let machService = "com.aicontrolcenter.sec02-remediation-helper"
    public static let launchDaemonPlist = "com.aicontrolcenter.sec02-remediation-helper.plist"
    public static let keyTag = Data("com.aicontrolcenter.sec02.fresh-human-presence.p256.v1".utf8)
}

@objc public enum SEC02HelperStatus: Int { case success, denied, unsafeExisting, ambiguous, failed }

@objc public protocol SEC02PrivilegedHelperXPC {
    func provisionPreBootstrapRemediationJournal(reply: @escaping (SEC02HelperStatus) -> Void)
    func restrictGovernanceDirectoryMode0755To0700(reply: @escaping (SEC02HelperStatus) -> Void)
}

public enum SEC02NativeReadiness: String { case ready = "READY", notReady = "NOT_READY", mismatch = "MISMATCH" }

public struct SEC02ResolvedSigningRequirement {
    public enum Role { case client, helper }
    fileprivate let expression: String
    fileprivate let role: Role
    fileprivate let teamID: String
}

public enum SEC02SigningResolverError: Error { case unsigned, invalidSignature, adhoc, identityMismatch, malformedRequirement }

public struct SEC02NativeSigningResolver {
    private static func resolve(_ artifact: URL, expectedBundleID: String,
                                expectedTeamID: String,
                                role: SEC02ResolvedSigningRequirement.Role) throws -> SEC02ResolvedSigningRequirement {
        guard !expectedTeamID.isEmpty, !expectedTeamID.contains("*") else { throw SEC02SigningResolverError.identityMismatch }
        var code: SecStaticCode?
        guard SecStaticCodeCreateWithPath(artifact as CFURL, [], &code) == errSecSuccess,
              let code else { throw SEC02SigningResolverError.unsigned }
        // Signing metadata is untrusted until Security.framework validates the
        // complete static artifact, including every architecture in a universal binary.
        guard SecStaticCodeCheckValidity(code, SecCSFlags(rawValue: kSecCSCheckAllArchitectures), nil)
                == errSecSuccess else { throw SEC02SigningResolverError.invalidSignature }
        var info: CFDictionary?
        guard SecCodeCopySigningInformation(code, SecCSFlags(rawValue: kSecCSSigningInformation), &info) == errSecSuccess,
              let values = info as? [String: Any],
              values[kSecCodeInfoIdentifier as String] as? String == expectedBundleID,
              values[kSecCodeInfoTeamIdentifier as String] as? String == expectedTeamID else {
            throw SEC02SigningResolverError.identityMismatch
        }
        if (values[kSecCodeInfoFlags as String] as? UInt32).map({ $0 & UInt32(kSecCodeSignatureAdhoc) != 0 }) == true {
            throw SEC02SigningResolverError.adhoc
        }
        var requirement: SecRequirement?
        guard SecCodeCopyDesignatedRequirement(code, [], &requirement) == errSecSuccess,
              let requirement else { throw SEC02SigningResolverError.malformedRequirement }
        var text: CFString?
        guard SecRequirementCopyString(requirement, [], &text) == errSecSuccess,
              let expression = text as String?, !expression.contains("*") else {
            throw SEC02SigningResolverError.malformedRequirement
        }
        return SEC02ResolvedSigningRequirement(expression: expression, role: role, teamID: expectedTeamID)
    }

    public static func resolveClient(app: URL, authoritativeTeamID: String) throws -> SEC02ResolvedSigningRequirement {
        try resolve(app, expectedBundleID: SEC02Identity.appBundleID, expectedTeamID: authoritativeTeamID, role: .client)
    }
    public static func resolveHelper(helper: URL, authoritativeTeamID: String) throws -> SEC02ResolvedSigningRequirement {
        try resolve(helper, expectedBundleID: SEC02Identity.helperBundleID, expectedTeamID: authoritativeTeamID, role: .helper)
    }
}

@available(macOS 13.0, *)
public struct SEC02PeerSigningPolicy {
    public let clientRequirement: SEC02ResolvedSigningRequirement?
    public let helperRequirement: SEC02ResolvedSigningRequirement?
    public var readiness: SEC02NativeReadiness {
        guard let clientRequirement, clientRequirement.role == .client,
              let helperRequirement, helperRequirement.role == .helper,
              clientRequirement.teamID == helperRequirement.teamID else { return .notReady }
        return clientRequirement.expression == helperRequirement.expression ? .mismatch : .ready
    }
    public func secureIncomingConnections(on listener: NSXPCListener) -> Bool {
        guard readiness == .ready, let value = clientRequirement else { return false }
        listener.setConnectionCodeSigningRequirement(value.expression); return true
    }
    public func secureHelperConnection(_ connection: NSXPCConnection) -> Bool {
        guard readiness == .ready, let value = helperRequirement else { return false }
        connection.setCodeSigningRequirement(value.expression); return true
    }
}

@available(macOS 13.0, *)
public struct SEC02SMAppServiceAdapter {
    public let service = SMAppService.daemon(plistName: SEC02Identity.launchDaemonPlist)
    public static let registrationOperational = false
    public var status: SMAppService.Status { service.status }
    // Registration and unregistration are deliberately not represented.
}

public struct SEC02FreshHumanEvidenceOutputV1 {
    public let challengeBytes: Data
    public let signature: Data
    public let publicKeyFingerprint: String
    public let algorithm: String
}

public enum SEC02SecureEnclaveKeyState { case absent, exactOne(SecKey), ambiguous, unsafe }
public enum SEC02SecureEnclaveError: Error {
    case accessControl, keyCreation, keyNotFound, ambiguous, unsafeExisting,
         publicKey, representation, signing
}

public struct SEC02SecureEnclaveProvisioner {
    private static let accessFlags: SecAccessControlCreateFlags = [.userPresence, .privateKeyUsage]
    private static func exactAccessControl() throws -> SecAccessControl {
        var error: Unmanaged<CFError>?
        guard let access = SecAccessControlCreateWithFlags(
            nil, kSecAttrAccessibleWhenUnlockedThisDeviceOnly, accessFlags, &error
        ) else { throw SEC02SecureEnclaveError.accessControl }
        return access
    }

    private static func allTaggedPrivateKeysQuery() -> [String: Any] {[
        kSecClass as String: kSecClassKey,
        kSecAttrApplicationTag as String: SEC02Identity.keyTag,
        kSecReturnRef as String: true,
        kSecReturnAttributes as String: true,
        kSecMatchLimit as String: kSecMatchLimitAll
    ]}

    public static func inspect_exact_fresh_human_key_state() throws -> SEC02SecureEnclaveKeyState {
        var result: CFTypeRef?
        let status = SecItemCopyMatching(allTaggedPrivateKeysQuery() as CFDictionary, &result)
        if status == errSecItemNotFound { return .absent }
        guard status == errSecSuccess, let rows = result as? [[String: Any]], !rows.isEmpty
        else { return .unsafe }
        // More than one object with the fixed tag is ambiguous regardless of quality.
        if rows.count > 1 { return .ambiguous }

        let requiredAccess = try exactAccessControl()
        var exact: [SecKey] = []
        var unsafe = false
        for row in rows {
            guard let key = row[kSecValueRef as String] as! SecKey?,
                  row[kSecAttrKeyClass as String] as? String == kSecAttrKeyClassPrivate as String,
                  row[kSecAttrKeyType as String] as? String == kSecAttrKeyTypeECSECPrimeRandom as String,
                  (row[kSecAttrKeySizeInBits as String] as? NSNumber)?.intValue == 256,
                  row[kSecAttrTokenID as String] as? String == kSecAttrTokenIDSecureEnclave as String,
                  (row[kSecAttrIsPermanent as String] as? NSNumber)?.boolValue == true,
                  let access = row[kSecAttrAccessControl as String] as! SecAccessControl?,
                  CFEqual(access, requiredAccess)
            else { unsafe = true; continue }
            exact.append(key)
        }
        if unsafe { return .unsafe }
        guard let key = exact.first else { return .unsafe }
        return .exactOne(key)
    }

    public static func provision_exact_fresh_human_key() throws -> String {
        // This authority is create-only: no replacement, deletion, rotation, or retry.
        guard case .absent = try inspect_exact_fresh_human_key_state()
        else { throw SEC02SecureEnclaveError.unsafeExisting }
        var error: Unmanaged<CFError>?
        let access = try exactAccessControl()
        let attributes: [String: Any] = [
            kSecAttrKeyType as String: kSecAttrKeyTypeECSECPrimeRandom,
            kSecAttrKeySizeInBits as String: 256,
            kSecAttrTokenID as String: kSecAttrTokenIDSecureEnclave,
            kSecPrivateKeyAttrs as String: [kSecAttrIsPermanent as String: true,
                kSecAttrApplicationTag as String: SEC02Identity.keyTag,
                kSecAttrAccessControl as String: access]
        ]
        guard let key = SecKeyCreateRandomKey(attributes as CFDictionary, &error) else { throw SEC02SecureEnclaveError.keyCreation }
        return try fingerprint(publicKey(for: key))
    }

    public static func load_exact_public_key_identity() throws -> String {
        guard case let .exactOne(key) = try inspect_exact_fresh_human_key_state()
        else { throw SEC02SecureEnclaveError.keyNotFound }
        return try fingerprint(publicKey(for: key))
    }

    public static func sign_exact_fresh_human_challenge(_ challenge: Data) throws -> SEC02FreshHumanEvidenceOutputV1 {
        guard !challenge.isEmpty,
              case let .exactOne(key) = try inspect_exact_fresh_human_key_state()
        else { throw SEC02SecureEnclaveError.keyNotFound }
        var error: Unmanaged<CFError>?
        guard let signature = SecKeyCreateSignature(key, .ecdsaSignatureMessageX962SHA256, challenge as CFData, &error) as Data? else { throw SEC02SecureEnclaveError.signing }
        return SEC02FreshHumanEvidenceOutputV1(challengeBytes: challenge, signature: signature,
            publicKeyFingerprint: try fingerprint(publicKey(for: key)),
            algorithm: "SECURE_ENCLAVE_P256_SHA256_USER_PRESENCE_V1")
    }

    private static func publicKey(for key: SecKey) throws -> SecKey {
        guard let value = SecKeyCopyPublicKey(key) else { throw SEC02SecureEnclaveError.publicKey }; return value
    }
    private static func fingerprint(_ publicKey: SecKey) throws -> String {
        var error: Unmanaged<CFError>?
        guard let bytes = SecKeyCopyExternalRepresentation(publicKey, &error) as Data? else { throw SEC02SecureEnclaveError.representation }
        // P-256 public external form is ANSI X9.63 uncompressed: 0x04 || X || Y.
        guard bytes.count == 65, bytes.first == 0x04 else { throw SEC02SecureEnclaveError.representation }
        return SHA256.hash(data: bytes).map { String(format: "%02x", $0) }.joined()
    }
}

public enum SEC02ReplayFingerprint {
    public static let domain = Data("AIControlCenter/SEC02/pre-bootstrap-remediation/replay/v1\0".utf8)
    public static func derive(ephemeralExternalForm: Data) -> String? {
        guard !ephemeralExternalForm.isEmpty else { return nil }
        return SHA256.hash(data: domain + ephemeralExternalForm).map { String(format: "%02x", $0) }.joined()
    }
}

public enum SEC02JournalProvisioningState: String { case absent, safeExisting, unsafeExisting, ambiguous }
public enum SEC02JournalProvisioningTerminalState: String, Codable { case completed = "COMPLETED" }
public struct SEC02JournalProvisioningReceipt: Codable {
    public let schemaVersion: Int
    public let purpose: String
    public let provisioningReplayFingerprint: String
    public let terminalProvisioningState: SEC02JournalProvisioningTerminalState
}
