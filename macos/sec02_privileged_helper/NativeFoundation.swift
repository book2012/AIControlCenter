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

public enum SEC02SigningResolverError: Error { case unsigned, adhoc, identityMismatch, malformedRequirement }

public struct SEC02NativeSigningResolver {
    private static func resolve(_ artifact: URL, expectedBundleID: String,
                                expectedTeamID: String,
                                role: SEC02ResolvedSigningRequirement.Role) throws -> SEC02ResolvedSigningRequirement {
        guard !expectedTeamID.isEmpty, !expectedTeamID.contains("*") else { throw SEC02SigningResolverError.identityMismatch }
        var code: SecStaticCode?
        guard SecStaticCodeCreateWithPath(artifact as CFURL, [], &code) == errSecSuccess,
              let code else { throw SEC02SigningResolverError.unsigned }
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

public enum SEC02SecureEnclaveError: Error { case accessControl, keyCreation, keyNotFound, publicKey, representation, signing }

public struct SEC02SecureEnclaveProvisioner {
    private static let accessFlags: SecAccessControlCreateFlags = [.userPresence, .privateKeyUsage]
    private static func privateKeyQuery() -> [String: Any] {[
        kSecClass as String: kSecClassKey,
        kSecAttrApplicationTag as String: SEC02Identity.keyTag,
        kSecAttrKeyType as String: kSecAttrKeyTypeECSECPrimeRandom,
        kSecReturnRef as String: true
    ]}

    public static func provision_exact_fresh_human_key() throws -> String {
        var error: Unmanaged<CFError>?
        guard let access = SecAccessControlCreateWithFlags(nil, kSecAttrAccessibleWhenUnlockedThisDeviceOnly, accessFlags, &error) else { throw SEC02SecureEnclaveError.accessControl }
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
        var result: CFTypeRef?
        guard SecItemCopyMatching(privateKeyQuery() as CFDictionary, &result) == errSecSuccess,
              let key = result as! SecKey? else { throw SEC02SecureEnclaveError.keyNotFound }
        return try fingerprint(publicKey(for: key))
    }

    public static func sign_exact_fresh_human_challenge(_ challenge: Data) throws -> SEC02FreshHumanEvidenceOutputV1 {
        var result: CFTypeRef?
        guard !challenge.isEmpty, SecItemCopyMatching(privateKeyQuery() as CFDictionary, &result) == errSecSuccess,
              let key = result as! SecKey? else { throw SEC02SecureEnclaveError.keyNotFound }
        var error: Unmanaged<CFError>?
        guard let signature = SecKeyCreateSignature(key, .ecdsaSignatureMessageX962SHA256, challenge as CFData, &error) as Data? else { throw SEC02SecureEnclaveError.signing }
        return SEC02FreshHumanEvidenceOutputV1(challengeBytes: challenge, signature: signature,
            publicKeyFingerprint: try fingerprint(publicKey(for: key)), algorithm: "ECDSA_P256_SHA256_X962")
    }

    private static func publicKey(for key: SecKey) throws -> SecKey {
        guard let value = SecKeyCopyPublicKey(key) else { throw SEC02SecureEnclaveError.publicKey }; return value
    }
    private static func fingerprint(_ publicKey: SecKey) throws -> String {
        var error: Unmanaged<CFError>?
        guard let bytes = SecKeyCopyExternalRepresentation(publicKey, &error) as Data? else { throw SEC02SecureEnclaveError.representation }
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
public struct SEC02JournalProvisioningReceipt: Codable {
    public let schemaVersion: Int
    public let purpose: String
    public let provisioningReplayFingerprint: String
    public let terminalProvisioningState: String
}
