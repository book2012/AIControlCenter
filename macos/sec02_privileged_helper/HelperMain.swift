import Foundation

@available(macOS 13.0, *)
private final class SEC02HelperListenerDelegate: NSObject, NSXPCListenerDelegate {
    private let signingPolicy: SEC02PeerSigningPolicy
    private let service = SEC02HelperService()

    init(signingPolicy: SEC02PeerSigningPolicy) {
        self.signingPolicy = signingPolicy
    }

    func listener(
        _ listener: NSXPCListener,
        shouldAcceptNewConnection connection: NSXPCConnection
    ) -> Bool {
        // Apply the native audit-token signing requirement before exporting any
        // interface or object. An unresolved/non-READY policy rejects every peer.
        guard signingPolicy.secureIncomingConnection(connection) else {
            return false
        }
        connection.exportedInterface = NSXPCInterface(with: SEC02PrivilegedHelperXPC.self)
        connection.exportedObject = service
        connection.resume()
        return true
    }
}

@available(macOS 13.0, *)
private final class SEC02HelperRuntime {
    private let listener: NSXPCListener
    private let delegate: SEC02HelperListenerDelegate

    init(signingPolicy: SEC02PeerSigningPolicy) {
        listener = NSXPCListener(machServiceName: SEC02Identity.machService)
        delegate = SEC02HelperListenerDelegate(signingPolicy: signingPolicy)
        listener.delegate = delegate
    }

    func run() {
        listener.resume()
        RunLoop.current.run()
    }
}

@main
struct SEC02GovernanceRemediationHelperMain {
    static func main() {
        guard #available(macOS 13.0, *) else { return }

        // Authoritative signed artifacts do not yet exist, so both requirements
        // remain unresolved and the listener rejects every incoming connection.
        let policy = SEC02PeerSigningPolicy(
            clientRequirement: nil,
            helperRequirement: nil
        )
        let runtime = SEC02HelperRuntime(signingPolicy: policy)
        runtime.run()
    }
}
