import Darwin
import Foundation


private let allowedOperations: Set<String> = [
    "governance_audit_snapshot",
    "sqlite_online_backup_verification",
]


private func fail(
    _ message: String,
    code: Int32
) -> Never {
    let document: [String: Any] = [
        "automatic_retry": false,
        "error": message,
        "result": "FAIL",
    ]

    if
        let data = try? JSONSerialization.data(
            withJSONObject: document,
            options: [.sortedKeys]
        ),
        let output = String(
            data: data,
            encoding: .utf8
        )
    {
        print(output)
    }

    exit(code)
}


let arguments = Array(
    CommandLine.arguments.dropFirst()
)

guard
    let index = arguments.firstIndex(
        of: "--operation"
    ),
    index + 1 < arguments.count
else {
    fail(
        "--operation is required",
        code: 2
    )
}

let operation = arguments[index + 1]

guard allowedOperations.contains(
    operation
) else {
    fail(
        "unsupported operation",
        code: 2
    )
}

let environment = (
    ProcessInfo.processInfo.environment
)
let repository = URL(
    fileURLWithPath: environment[
        "AICONTROLCENTER_REPOSITORY"
    ] ?? "/Users/kyouhan/AIControlCenter",
    isDirectory: true
)
let python = repository
    .appendingPathComponent(
        ".venv/bin/python"
    )

guard FileManager.default.isExecutableFile(
    atPath: python.path
) else {
    fail(
        "Python executable unavailable",
        code: 3
    )
}

let process = Process()
process.executableURL = python
process.arguments = [
    "-m",
    "core.governance.operations.scheduler",
    "--operation",
    operation,
    "--once",
    "--json",
]
process.currentDirectoryURL = repository
process.environment = environment
process.standardOutput = (
    FileHandle.standardOutput
)
process.standardError = (
    FileHandle.standardError
)

do {
    try process.run()
} catch {
    fail(
        error.localizedDescription,
        code: 4
    )
}

process.waitUntilExit()
exit(process.terminationStatus)
