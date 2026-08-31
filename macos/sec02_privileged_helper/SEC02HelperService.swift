import Foundation

/// Exact, fail-closed implementation of the frozen privileged XPC protocol.
/// C3 exposes the process boundary but grants no mutation capability.
public final class SEC02HelperService: NSObject, SEC02PrivilegedHelperXPC {
    public func provisionPreBootstrapRemediationJournal(
        reply: @escaping (SEC02HelperStatus) -> Void
    ) {
        reply(.denied)
    }

    public func restrictGovernanceDirectoryMode0755To0700(
        reply: @escaping (SEC02HelperStatus) -> Void
    ) {
        reply(.denied)
    }
}
