import Foundation
import CryptoKit

// Repository/native foundation only. Packaging, registration, launch, XPC
// activation, Authorization Services acquisition, and mutation are absent.

@objc public protocol SEC02GovernanceRemediationXPC {
    // The request intentionally carries no path, mode, identity, command, or
    // caller-selected operation. Authority transport is not operational in 03B2.
    func restrictGovernanceDirectoryMode0755To0700(
        reply: @escaping (Bool) -> Void
    )
}

public enum SEC02NativeReadiness: String {
    case ready = "READY"
    case notReady = "NOT_READY"
    case mismatch = "MISMATCH"
}

public enum SEC02NativeValidationLevel: String {
    case sourceImplemented = "SOURCE_IMPLEMENTED"
    case typechecked = "TYPECHECKED"
    case operationallyValidated = "OPERATIONALLY_VALIDATED"
}

public struct SEC02ResolvedSigningRequirement {
    public enum Role { case client, helper }
    fileprivate let expression: String
    fileprivate let role: Role
}

@available(macOS 13.0, *)
public struct SEC02PeerSigningPolicy {
    public let clientRequirement: SEC02ResolvedSigningRequirement?
    public let helperRequirement: SEC02ResolvedSigningRequirement?

    public var readiness: SEC02NativeReadiness {
        guard let clientRequirement, clientRequirement.role == .client,
              let helperRequirement, helperRequirement.role == .helper else {
            return .notReady
        }
        return clientRequirement.expression == helperRequirement.expression ? .mismatch : .ready
    }

    public func secureIncomingConnections(on listener: NSXPCListener) -> Bool {
        guard readiness == .ready, let clientRequirement else { return false }
        listener.setConnectionCodeSigningRequirement(clientRequirement.expression)
        return true
    }

    public func secureHelperConnection(_ connection: NSXPCConnection) -> Bool {
        guard readiness == .ready, let helperRequirement else { return false }
        connection.setCodeSigningRequirement(helperRequirement.expression)
        return true
    }
}

public struct SEC02FreshHumanChallengeInputV1: Codable {
    public let schemaVersion: String
    public let purpose: String
    public let boundedMutation: String
    public let requestIdentity: String
    public let authorizationReplayKey: String
    public let nonce: String
    public let issuedAt: String
    public let expiresAt: String
}

public struct SEC02FreshHumanEvidenceOutputV1 {
    public let challengeBytes: Data
    public let signature: Data
    public let publicKeyFingerprint: String
    public let algorithm: String
}

// Future native ports only. There is intentionally no SecKey or LAContext
// implementation, reusable authentication context, or authentication-reuse knob.
public protocol SEC02SecureEnclaveUserPresenceSigning {
    func signCanonicalChallenge(_ challenge: Data) throws -> SEC02FreshHumanEvidenceOutputV1
}

public protocol SEC02P256SignatureVerifying {
    func verifyCanonicalChallenge(_ challenge: Data, signature: Data,
                                  publicKeyFingerprint: String) -> Bool
}

public struct SEC02SMAppServicePackageContract {
    public static let minimumMacOSMajor = 13
    public static let bundledLaunchDaemonDirectory = "Contents/Library/LaunchDaemons"
    public static let bundledExecutableDirectory = "Contents/MacOS"
    public static let registrationPermitted = false
}

public enum SEC02ReplayFingerprint {
    // Must match pre_bootstrap_remediation_journal.py::_REPLAY_DOMAIN byte-for-byte.
    public static let domain = Data("AIControlCenter/SEC02/pre-bootstrap-remediation/replay/v1\0".utf8)

    public static func derive(ephemeralExternalForm: Data) -> String? {
        guard !ephemeralExternalForm.isEmpty else { return nil }
        var input = Data()
        input.reserveCapacity(domain.count + ephemeralExternalForm.count)
        input.append(domain)
        input.append(ephemeralExternalForm)
        let digest = SHA256.hash(data: input)
        return digest.map { String(format: "%02x", $0) }.joined()
    }
}

// Future acquisition boundary only. No implementation exists in this WU and
// AuthorizationMakeExternalForm is never invoked by repository code or tests.
public protocol SEC02AuthorizationExternalFormAcquiring {
    func fingerprintForAuthorizationReference() throws -> String
}
