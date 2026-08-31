import Foundation

@main
struct SEC02ProductionSigningIdentityVerifierMain {
    static func main() throws {
        guard CommandLine.arguments.count == 1 else {
            FileHandle.standardError.write(Data("usage: production-signing-identity-verifier\n".utf8))
            throw Exit.invalidArguments
        }
        let result = SEC02ProductionSigningIdentityVerifier.inspectLocalKeychainReadOnly()
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.outputFormatting = [.sortedKeys]
        FileHandle.standardOutput.write(try encoder.encode(result))
        FileHandle.standardOutput.write(Data("\n".utf8))
    }

    enum Exit: Error { case invalidArguments }
}
