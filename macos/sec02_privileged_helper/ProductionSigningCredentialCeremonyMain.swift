import Foundation

@main
struct SEC02ProductionSigningCredentialCeremonyMain {
    static func main() throws {
        guard CommandLine.arguments.count == 2 else {
            FileHandle.standardError.write(Data(
                "usage: production-signing-credential-ceremony-inspect <absolute-.p12-or-.pfx-path>\n".utf8))
            throw Exit.invalidArguments
        }
        let observation = SEC02ProductionSigningCredentialCeremony.inspectExplicitPathReadOnly(
            CommandLine.arguments[1])
        let result = SEC02ProductionSigningCredentialCeremony.evaluateLocalInputOnly(observation)
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.outputFormatting = [.sortedKeys]
        FileHandle.standardOutput.write(try encoder.encode(result))
        FileHandle.standardOutput.write(Data("\n".utf8))
    }

    enum Exit: Error { case invalidArguments }
}
