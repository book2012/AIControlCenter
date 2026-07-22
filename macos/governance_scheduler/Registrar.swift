import Darwin
import Dispatch
import Foundation
import ServiceManagement


private let plistNames = [
    "com.aicontrolcenter.governance-audit-snapshot.plist",
    "com.aicontrolcenter.sqlite-online-backup-verification.plist",
]


@available(macOS 13.0, *)
private func statusName(
    _ status: SMAppService.Status
) -> String {
    switch status {
    case .notRegistered:
        return "not_registered"
    case .enabled:
        return "enabled"
    case .requiresApproval:
        return "requires_approval"
    case .notFound:
        return "not_found"
    @unknown default:
        return "unknown"
    }
}


private func printJSON(
    _ document: [String: Any]
) {
    guard
        let data = try? JSONSerialization.data(
            withJSONObject: document,
            options: [.sortedKeys]
        ),
        let output = String(
            data: data,
            encoding: .utf8
        )
    else {
        fputs(
            "{\"result\":\"FAIL\"}\n",
            stderr
        )
        return
    }

    print(output)
}


private final class ErrorBox:
    @unchecked Sendable
{
    private let lock = NSLock()
    private var storedError: Error?

    func set(
        _ error: Error?
    ) {
        lock.lock()
        storedError = error
        lock.unlock()
    }

    func get() -> Error? {
        lock.lock()
        defer {
            lock.unlock()
        }
        return storedError
    }
}


@available(macOS 13.0, *)
private func unregisterAndWait(
    _ service: SMAppService
) -> Error? {
    let semaphore = DispatchSemaphore(
        value: 0
    )
    let errorBox = ErrorBox()

    service.unregister {
        error in

        errorBox.set(error)
        semaphore.signal()
    }

    semaphore.wait()
    return errorBox.get()
}


@available(macOS 13.0, *)
private func execute() -> Int32 {
    let arguments = Array(
        CommandLine.arguments.dropFirst()
    )
    let command = (
        arguments.first ?? "status"
    )

    guard [
        "status",
        "register",
        "unregister",
    ].contains(command) else {
        printJSON([
            "error": "unsupported command",
            "result": "FAIL",
        ])
        return 2
    }

    var services: [[String: Any]] = []
    var errors: [[String: String]] = []

    for plistName in plistNames {
        let service = SMAppService.agent(
            plistName: plistName
        )

        do {
            if command == "register" {
                if (
                    service.status
                    == .notRegistered
                    || service.status
                    == .notFound
                ) {
                    try service.register()
                }
            } else if command == "unregister" {
                if (
                    service.status
                    != .notRegistered
                    && service.status
                    != .notFound
                ) {
                    if let error = unregisterAndWait(
                        service
                    ) {
                        throw error
                    }
                }
            }
        } catch {
            errors.append([
                "error": error.localizedDescription,
                "plist": plistName,
            ])
        }

        services.append([
            "plist": plistName,
            "status": statusName(
                service.status
            ),
        ])
    }

    printJSON([
        "command": command,
        "errors": errors,
        "result": (
            errors.isEmpty
            ? "PASS"
            : "FAIL"
        ),
        "services": services,
    ])

    return errors.isEmpty ? 0 : 1
}


if #available(macOS 13.0, *) {
    exit(execute())
}

printJSON([
    "error": "macOS 13 or later required",
    "result": "FAIL",
])
exit(3)
