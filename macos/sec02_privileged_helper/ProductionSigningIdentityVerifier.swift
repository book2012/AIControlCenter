import Foundation
import LocalAuthentication
import Security

// Read-only Production signing identity verification. This module never creates,
// updates, deletes, exports, or uses a private key to produce a signature.

public enum SEC02ProductionCandidateState: String, Codable {
    case absent = "ABSENT"
    case exactValidDeveloperIDApplication = "EXACT_VALID_DEVELOPER_ID_APPLICATION"
    case ambiguous = "AMBIGUOUS"
    case invalid = "INVALID"
    case untrusted = "UNTRUSTED"
    case privateKeyUnavailable = "PRIVATE_KEY_UNAVAILABLE"
}

public enum SEC02ProductionReadiness: String, Codable {
    case ready = "READY"
    case notReady = "NOT_READY"
}

public struct SEC02SigningIdentityObservation {
    public let isDeveloperIDApplication: Bool
    public let certificateValid: Bool
    public let trustValid: Bool
    public let privateKeyUsable: Bool
    public let credentialTeamID: String?

    public init(isDeveloperIDApplication: Bool, certificateValid: Bool,
                trustValid: Bool, privateKeyUsable: Bool,
                credentialTeamID: String?) {
        self.isDeveloperIDApplication = isDeveloperIDApplication
        self.certificateValid = certificateValid
        self.trustValid = trustValid
        self.privateKeyUsable = privateKeyUsable
        self.credentialTeamID = credentialTeamID
    }
}

public struct SEC02ProductionSigningIdentityResultV1: Encodable, Equatable {
    public let schemaVersion = 1
    public let readiness: SEC02ProductionReadiness
    public let candidateState: SEC02ProductionCandidateState
    public let developerIDApplicationPresent: Bool
    public let privateKeyUsable: Bool
    public let authoritativeTeamID: String?
    public let certificateValid: Bool
    public let trustValid: Bool
    public let productionMutationPerformed = false
    public let keychainMutationPerformed = false
    public let signingPerformed = false

    private enum CodingKeys: String, CodingKey {
        case schemaVersion, readiness, candidateState, developerIDApplicationPresent
        case privateKeyUsable, authoritativeTeamID, certificateValid, trustValid
        case productionMutationPerformed, keychainMutationPerformed, signingPerformed
    }

    public func encode(to encoder: Encoder) throws {
        var values = encoder.container(keyedBy: CodingKeys.self)
        try values.encode(schemaVersion, forKey: .schemaVersion)
        try values.encode(readiness, forKey: .readiness)
        try values.encode(candidateState, forKey: .candidateState)
        try values.encode(developerIDApplicationPresent, forKey: .developerIDApplicationPresent)
        try values.encode(privateKeyUsable, forKey: .privateKeyUsable)
        try values.encode(authoritativeTeamID, forKey: .authoritativeTeamID)
        try values.encode(certificateValid, forKey: .certificateValid)
        try values.encode(trustValid, forKey: .trustValid)
        try values.encode(productionMutationPerformed, forKey: .productionMutationPerformed)
        try values.encode(keychainMutationPerformed, forKey: .keychainMutationPerformed)
        try values.encode(signingPerformed, forKey: .signingPerformed)
    }
}

public enum SEC02ProductionSigningIdentityVerifier {
    // Apple documents the Developer ID Application leaf and Developer ID CA
    // extension OIDs in TN3127. An OID alone is never trusted: Apple code-signing
    // trust, current validity, the issuer OID, and a usable matching private key
    // are independently required by the live adapter.
    static let developerIDApplicationOID = "1.2.840.113635.100.6.1.13"
    static let developerIDInstallerOID = "1.2.840.113635.100.6.1.14"
    static let developerIDIssuerOID = "1.2.840.113635.100.6.2.6"

    private static func validTeamID(_ value: String?) -> String? {
        guard let value, value.count == 10,
              value.unicodeScalars.allSatisfy({
                  (65...90).contains($0.value) || (48...57).contains($0.value)
              }) else { return nil }
        return value
    }

    public static func evaluate(_ observations: [SEC02SigningIdentityObservation])
        -> SEC02ProductionSigningIdentityResultV1 {
        guard !observations.isEmpty else { return result(.absent) }
        let app = observations.filter(\.isDeveloperIDApplication)
        guard !app.isEmpty else { return result(.invalid) }
        let acceptable = app.compactMap { candidate -> (SEC02SigningIdentityObservation, String)? in
            guard candidate.certificateValid, candidate.trustValid,
                  candidate.privateKeyUsable,
                  let teamID = validTeamID(candidate.credentialTeamID) else { return nil }
            return (candidate, teamID)
        }
        if acceptable.count > 1 { return result(.ambiguous, present: true) }
        if acceptable.isEmpty {
            if let candidate = app.first(where: {
                !$0.certificateValid || validTeamID($0.credentialTeamID) == nil
            }) {
                return result(.invalid, present: true, candidate: candidate)
            }
            if let candidate = app.first(where: { !$0.trustValid }) {
                return result(.untrusted, present: true, candidate: candidate)
            }
            return result(.privateKeyUnavailable, present: true,
                          candidate: app.first(where: { !$0.privateKeyUsable }))
        }
        let teamID = acceptable[0].1
        return SEC02ProductionSigningIdentityResultV1(
            readiness: .ready, candidateState: .exactValidDeveloperIDApplication,
            developerIDApplicationPresent: true, privateKeyUsable: true,
            authoritativeTeamID: teamID, certificateValid: true, trustValid: true)
    }

    private static func result(_ state: SEC02ProductionCandidateState,
                               present: Bool = false,
                               candidate: SEC02SigningIdentityObservation? = nil)
        -> SEC02ProductionSigningIdentityResultV1 {
        SEC02ProductionSigningIdentityResultV1(
            readiness: .notReady, candidateState: state,
            developerIDApplicationPresent: present,
            privateKeyUsable: candidate?.privateKeyUsable ?? false,
            authoritativeTeamID: nil,
            certificateValid: candidate?.certificateValid ?? false,
            trustValid: candidate?.trustValid ?? false)
    }

    public static func inspectLocalKeychainReadOnly() -> SEC02ProductionSigningIdentityResultV1 {
        evaluate(SEC02SecurityFrameworkSigningIdentityAdapter.inspectReadOnly())
    }
}

private enum SEC02DER {
    struct Node { let tag: UInt8; let content: Range<Int>; let next: Int }

    static func node(_ data: Data, at offset: Int) -> Node? {
        guard offset + 2 <= data.count else { return nil }
        let tag = data[offset]
        let first = Int(data[offset + 1])
        var header = 2
        var length = first
        if first & 0x80 != 0 {
            let count = first & 0x7f
            guard count > 0, count <= 4, offset + 2 + count <= data.count else { return nil }
            length = 0
            for index in 0..<count { length = (length << 8) | Int(data[offset + 2 + index]) }
            header += count
        }
        let start = offset + header
        guard length >= 0, start <= data.count, length <= data.count - start else { return nil }
        return Node(tag: tag, content: start..<(start + length), next: start + length)
    }

    static func oidBytes(_ dotted: String) -> Data? {
        let values = dotted.split(separator: ".").compactMap { UInt64($0) }
        guard values.count >= 2, values[0] <= 2, values[1] < 40 else { return nil }
        var bytes = [UInt8(values[0] * 40 + values[1])]
        for value in values.dropFirst(2) {
            var parts = [UInt8(value & 0x7f)]
            var remaining = value >> 7
            while remaining > 0 { parts.append(UInt8(remaining & 0x7f) | 0x80); remaining >>= 7 }
            bytes.append(contentsOf: parts.reversed())
        }
        return Data(bytes)
    }

    static func certificateExtensionOIDs(_ data: Data) -> Set<Data>? {
        guard let certificate = node(data, at: 0), certificate.tag == 0x30,
              certificate.next == data.count,
              let tbs = node(data, at: certificate.content.lowerBound), tbs.tag == 0x30 else { return nil }
        var cursor = tbs.content.lowerBound
        while cursor < tbs.content.upperBound {
            guard let item = node(data, at: cursor), item.next <= tbs.content.upperBound else { return nil }
            if item.tag == 0xa3 {
                guard let sequence = node(data, at: item.content.lowerBound), sequence.tag == 0x30,
                      sequence.next == item.content.upperBound else { return nil }
                var result = Set<Data>()
                var extensionCursor = sequence.content.lowerBound
                while extensionCursor < sequence.content.upperBound {
                    guard let entry = node(data, at: extensionCursor), entry.tag == 0x30,
                          let oid = node(data, at: entry.content.lowerBound), oid.tag == 0x06,
                          entry.next <= sequence.content.upperBound else { return nil }
                    result.insert(data.subdata(in: oid.content))
                    extensionCursor = entry.next
                }
                return extensionCursor == sequence.content.upperBound ? result : nil
            }
            cursor = item.next
        }
        return []
    }
}

private enum SEC02SecurityFrameworkSigningIdentityAdapter {
    private static func allCertificates() -> [SecCertificate]? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassCertificate,
            kSecReturnRef as String: true,
            kSecMatchLimit as String: kSecMatchLimitAll,
        ]
        var raw: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &raw)
        if status == errSecItemNotFound { return [] }
        guard status == errSecSuccess, let raw else { return nil }
        if CFGetTypeID(raw) == SecCertificateGetTypeID() {
            return [unsafeBitCast(raw, to: SecCertificate.self)]
        }
        guard CFGetTypeID(raw) == CFArrayGetTypeID() else { return nil }
        let values = unsafeBitCast(raw, to: CFArray.self)
        var certificates: [SecCertificate] = []
        for index in 0..<CFArrayGetCount(values) {
            let reference = unsafeBitCast(CFArrayGetValueAtIndex(values, index), to: CFTypeRef.self)
            guard CFGetTypeID(reference) == SecCertificateGetTypeID() else { return nil }
            certificates.append(unsafeBitCast(reference, to: SecCertificate.self))
        }
        return certificates
    }

    private static func identitiesByCertificate() -> [Data: SecIdentity]? {
        let authenticationContext = LAContext()
        authenticationContext.interactionNotAllowed = true
        let query: [String: Any] = [
            kSecClass as String: kSecClassIdentity,
            kSecReturnRef as String: true,
            kSecMatchLimit as String: kSecMatchLimitAll,
            kSecUseAuthenticationContext as String: authenticationContext,
        ]
        var raw: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &raw)
        if status == errSecItemNotFound { return [:] }
        guard status == errSecSuccess, let raw else { return nil }
        let identityType = SecIdentityGetTypeID()
        let identities: [SecIdentity]
        if CFGetTypeID(raw) == identityType {
            identities = [unsafeBitCast(raw, to: SecIdentity.self)]
        } else if CFGetTypeID(raw) == CFArrayGetTypeID() {
            let values = unsafeBitCast(raw, to: CFArray.self)
            var normalized: [SecIdentity] = []
            for index in 0..<CFArrayGetCount(values) {
                let reference = unsafeBitCast(CFArrayGetValueAtIndex(values, index), to: CFTypeRef.self)
                guard CFGetTypeID(reference) == identityType else { return nil }
                normalized.append(unsafeBitCast(reference, to: SecIdentity.self))
            }
            identities = normalized
        } else { return nil }
        var result: [Data: SecIdentity] = [:]
        for identity in identities {
            var certificate: SecCertificate?
            guard SecIdentityCopyCertificate(identity, &certificate) == errSecSuccess,
                  let certificate else { return nil }
            result[SecCertificateCopyData(certificate) as Data] = identity
        }
        return result
    }

    private static func extensionOIDs(_ certificate: SecCertificate) -> Set<Data>? {
        SEC02DER.certificateExtensionOIDs(SecCertificateCopyData(certificate) as Data)
    }

    private static func hasOID(_ dotted: String, in certificate: SecCertificate) -> Bool {
        guard let encoded = SEC02DER.oidBytes(dotted),
              let extensions = extensionOIDs(certificate) else { return false }
        return extensions.contains(encoded)
    }

    private static func validity(_ certificate: SecCertificate, now: Date) -> Bool {
        let keys = [kSecOIDX509V1ValidityNotBefore, kSecOIDX509V1ValidityNotAfter] as CFArray
        var error: Unmanaged<CFError>?
        guard let raw = SecCertificateCopyValues(certificate, keys, &error) as? [String: Any],
              let before = (raw[kSecOIDX509V1ValidityNotBefore as String] as? [String: Any])?[kSecPropertyKeyValue as String] as? Date,
              let after = (raw[kSecOIDX509V1ValidityNotAfter as String] as? [String: Any])?[kSecPropertyKeyValue as String] as? Date else { return false }
        return before <= now && now <= after
    }

    private static func teamID(_ certificate: SecCertificate) -> String? {
        var error: Unmanaged<CFError>?
        guard let raw = SecCertificateCopyValues(
            certificate, [kSecOIDOrganizationalUnitName] as CFArray, &error
        ) as? [String: Any],
        let property = raw[kSecOIDOrganizationalUnitName as String] as? [String: Any]
        else { return nil }
        if let value = property[kSecPropertyKeyValue as String] as? String { return value }
        if let values = property[kSecPropertyKeyValue as String] as? [[String: Any]], values.count == 1 {
            return values[0][kSecPropertyKeyValue as String] as? String
        }
        return nil
    }

    private static func trust(_ certificate: SecCertificate) -> (Bool, [SecCertificate]) {
        guard let policy = SecPolicyCreateWithProperties(kSecPolicyAppleCodeSigning, nil) else { return (false, []) }
        var optionalTrust: SecTrust?
        guard SecTrustCreateWithCertificates(certificate, policy, &optionalTrust) == errSecSuccess,
              let trust = optionalTrust else { return (false, []) }
        var error: CFError?
        let valid = SecTrustEvaluateWithError(trust, &error)
        let chain = SecTrustCopyCertificateChain(trust) as? [SecCertificate] ?? []
        return (valid, chain)
    }

    private static func privateKeyUsable(_ identity: SecIdentity?) -> Bool {
        guard let identity else { return false }
        var key: SecKey?
        guard SecIdentityCopyPrivateKey(identity, &key) == errSecSuccess, let key else { return false }
        // This is read-only capability evidence, not proof that a later package-signing
        // operation will succeed; actual signing is deferred to the signed-package milestone.
        return SecKeyIsAlgorithmSupported(key, .sign, .rsaSignatureMessagePKCS1v15SHA256)
            || SecKeyIsAlgorithmSupported(key, .sign, .ecdsaSignatureMessageX962SHA256)
    }

    static func inspectReadOnly() -> [SEC02SigningIdentityObservation] {
        let identityResult = identitiesByCertificate()
        guard let certificates = allCertificates() else {
            if let identityResult, identityResult.isEmpty { return [] }
            if identityResult == nil,
               SEC02SecurityToolZeroIdentityFallback.confirmsZeroCodeSigningIdentities() {
                return []
            }
            return [SEC02SigningIdentityObservation(isDeveloperIDApplication: false,
                certificateValid: false, trustValid: false, privateKeyUsable: false,
                credentialTeamID: nil)]
        }
        // Failure to enumerate accessible identities confers no key usability.
        // Certificate evidence remains independently inspectable and any matching
        // leaf will therefore fail closed as PRIVATE_KEY_UNAVAILABLE.
        let identities = identityResult ?? [:]
        let now = Date()
        return certificates.compactMap { certificate in
            let identity = identities[SecCertificateCopyData(certificate) as Data]
            let app = hasOID(SEC02ProductionSigningIdentityVerifier.developerIDApplicationOID,
                             in: certificate)
            // Ignore unrelated system certificates. Retain every identity so a
            // wrong signing identity is INVALID, and every Developer ID App leaf
            // so a missing private key is reported explicitly.
            guard app || identity != nil else { return nil }
            let evaluated = trust(certificate)
            let issuerIsDeveloperID = evaluated.1.count > 1 && hasOID(
                SEC02ProductionSigningIdentityVerifier.developerIDIssuerOID,
                in: evaluated.1[1])
            return SEC02SigningIdentityObservation(
                isDeveloperIDApplication: app && issuerIsDeveloperID,
                certificateValid: validity(certificate, now: now),
                trustValid: evaluated.0 && issuerIsDeveloperID,
                privateKeyUsable: app && privateKeyUsable(identity),
                credentialTeamID: app && issuerIsDeveloperID ? teamID(certificate) : nil)
        }
    }
}

// Narrow compatibility fallback for execution contexts that deny both
// Security.framework enumeration queries. It recognizes one exact, secret-free
// terminal statement and can prove only absence. Any other output is INVALID;
// it can never produce a candidate, Team ID, or READY result.
private enum SEC02SecurityToolZeroIdentityFallback {
    static func confirmsZeroCodeSigningIdentities() -> Bool {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/security")
        process.arguments = ["find-identity", "-v", "-p", "codesigning"]
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe
        do { try process.run() } catch { return false }
        process.waitUntilExit()
        guard process.terminationStatus == 0 else { return false }
        let output = pipe.fileHandleForReading.readDataToEndOfFile()
        guard let text = String(data: output, encoding: .utf8) else { return false }
        let lines = text.split(whereSeparator: \.isNewline).map {
            $0.trimmingCharacters(in: .whitespaces)
        }.filter { !$0.isEmpty }
        return lines == ["0 valid identities found"]
    }
}
