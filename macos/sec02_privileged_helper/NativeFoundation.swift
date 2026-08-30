import Foundation

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

@available(macOS 13.0, *)
public struct SEC02PeerSigningPolicy {
    public let clientRequirement: String?
    public let helperRequirement: String?

    public var readiness: SEC02NativeReadiness {
        guard let clientRequirement, !clientRequirement.isEmpty,
              let helperRequirement, !helperRequirement.isEmpty else {
            return .notReady
        }
        return .ready
    }

    public func secureIncomingConnections(on listener: NSXPCListener) -> Bool {
        guard readiness == .ready, let clientRequirement else { return false }
        listener.setConnectionCodeSigningRequirement(clientRequirement)
        return true
    }

    public func secureHelperConnection(_ connection: NSXPCConnection) -> Bool {
        guard readiness == .ready, let helperRequirement else { return false }
        connection.setCodeSigningRequirement(helperRequirement)
        return true
    }
}

public struct SEC02SMAppServicePackageContract {
    public static let minimumMacOSMajor = 13
    public static let bundledLaunchDaemonDirectory = "Contents/Library/LaunchDaemons"
    public static let bundledExecutableDirectory = "Contents/MacOS"
    public static let registrationPermitted = false
}
