import Foundation

// C6B is a repository-only readiness contract for a future external credential
// acquisition. It observes caller-supplied, non-secret classification facts; it
// does not inspect or acquire a credential. C4 remains the sole live identity
// and authoritative Team ID boundary after a separate C5A/C5B ceremony.

public enum SEC02ExternalCredentialClass: String, Codable {
    case developerIDApplication = "APPLE_DEVELOPER_ID_APPLICATION"
    case developerIDInstaller = "APPLE_DEVELOPER_ID_INSTALLER"
    case appleDevelopment = "APPLE_DEVELOPMENT"
    case adHoc = "AD_HOC"
    case selfSigned = "SELF_SIGNED"
    case unsupported = "UNSUPPORTED"
}

public enum SEC02ExternalCredentialAuthorityClaim: String, Codable {
    case none = "NONE"
    case c4VerificationRequired = "C4_VERIFICATION_REQUIRED"
    case inventedTeamID = "INVENTED_TEAM_ID"
    case xcodeDerived = "XCODE_DERIVED"
}

public enum SEC02ExternalCredentialAcquisitionReadiness: String, Codable {
    case candidateAbsent = "CANDIDATE_ABSENT"
    case acceptableCandidateRepresented = "ACCEPTABLE_CANDIDATE_REPRESENTED"
    case rejectedCredentialClass = "REJECTED_CREDENTIAL_CLASS"
    case matchingPrivateKeyRequired = "MATCHING_PRIVATE_KEY_REQUIRED"
    case rejectedAuthorityClaim = "REJECTED_AUTHORITY_CLAIM"
}

public struct SEC02ExternalCredentialCandidateObservation: Equatable {
    public let credentialClass: SEC02ExternalCredentialClass
    public let matchingPrivateKeyRepresented: Bool
    public let authorityClaim: SEC02ExternalCredentialAuthorityClaim

    public init(credentialClass: SEC02ExternalCredentialClass,
                matchingPrivateKeyRepresented: Bool,
                authorityClaim: SEC02ExternalCredentialAuthorityClaim) {
        self.credentialClass = credentialClass
        self.matchingPrivateKeyRepresented = matchingPrivateKeyRepresented
        self.authorityClaim = authorityClaim
    }
}

public struct SEC02ExternalCredentialAcquisitionReadinessResultV1: Encodable, Equatable {
    public let schemaVersion = 1
    public let readiness: SEC02ExternalCredentialAcquisitionReadiness
    public let candidateRepresented: Bool
    public let credentialClass: SEC02ExternalCredentialClass?
    public let developerIDApplicationRequired = true
    public let matchingPrivateKeyRequired = true
    public let matchingPrivateKeyRepresented: Bool
    public let c5ACeremonyMayEventuallyProceed: Bool
    public let c5BCeremonyMayEventuallyProceed: Bool
    public let c4VerificationRequiredAfterFutureImport = true
    public let authoritativeTeamID: String? = nil
    public let platform = "MAC_ONLY"
    public let repositoryOnly = true
    public let inspectionReadOnly = true
    public let credentialAcquired = false
    public let credentialDownloaded = false
    public let credentialContentsRead = false
    public let passphraseHandled = false
    public let credentialImported = false
    public let keychainMutationPerformed = false
    public let signingPerformed = false
    public let notarizationPerformed = false
    public let smAppServiceRegistrationPerformed = false
    public let productionMutationPerformed = false
    public let productionAuthorityGranted = false
    public let ubuntuAuthorityGranted = false

    private enum CodingKeys: String, CodingKey {
        case schemaVersion, readiness, candidateRepresented, credentialClass
        case developerIDApplicationRequired, matchingPrivateKeyRequired
        case matchingPrivateKeyRepresented, c5ACeremonyMayEventuallyProceed
        case c5BCeremonyMayEventuallyProceed, c4VerificationRequiredAfterFutureImport
        case authoritativeTeamID, platform, repositoryOnly, inspectionReadOnly
        case credentialAcquired, credentialDownloaded, credentialContentsRead, passphraseHandled
        case credentialImported, keychainMutationPerformed, signingPerformed, notarizationPerformed
        case smAppServiceRegistrationPerformed, productionMutationPerformed
        case productionAuthorityGranted, ubuntuAuthorityGranted
    }

    public func encode(to encoder: Encoder) throws {
        var values = encoder.container(keyedBy: CodingKeys.self)
        try values.encode(schemaVersion, forKey: .schemaVersion)
        try values.encode(readiness, forKey: .readiness)
        try values.encode(candidateRepresented, forKey: .candidateRepresented)
        try values.encode(credentialClass, forKey: .credentialClass)
        try values.encode(developerIDApplicationRequired, forKey: .developerIDApplicationRequired)
        try values.encode(matchingPrivateKeyRequired, forKey: .matchingPrivateKeyRequired)
        try values.encode(matchingPrivateKeyRepresented, forKey: .matchingPrivateKeyRepresented)
        try values.encode(c5ACeremonyMayEventuallyProceed, forKey: .c5ACeremonyMayEventuallyProceed)
        try values.encode(c5BCeremonyMayEventuallyProceed, forKey: .c5BCeremonyMayEventuallyProceed)
        try values.encode(c4VerificationRequiredAfterFutureImport, forKey: .c4VerificationRequiredAfterFutureImport)
        try values.encodeNil(forKey: .authoritativeTeamID)
        try values.encode(platform, forKey: .platform)
        try values.encode(repositoryOnly, forKey: .repositoryOnly)
        try values.encode(inspectionReadOnly, forKey: .inspectionReadOnly)
        try values.encode(credentialAcquired, forKey: .credentialAcquired)
        try values.encode(credentialDownloaded, forKey: .credentialDownloaded)
        try values.encode(credentialContentsRead, forKey: .credentialContentsRead)
        try values.encode(passphraseHandled, forKey: .passphraseHandled)
        try values.encode(credentialImported, forKey: .credentialImported)
        try values.encode(keychainMutationPerformed, forKey: .keychainMutationPerformed)
        try values.encode(signingPerformed, forKey: .signingPerformed)
        try values.encode(notarizationPerformed, forKey: .notarizationPerformed)
        try values.encode(smAppServiceRegistrationPerformed, forKey: .smAppServiceRegistrationPerformed)
        try values.encode(productionMutationPerformed, forKey: .productionMutationPerformed)
        try values.encode(productionAuthorityGranted, forKey: .productionAuthorityGranted)
        try values.encode(ubuntuAuthorityGranted, forKey: .ubuntuAuthorityGranted)
    }
}

public enum SEC02ProductionSigningExternalCredentialAcquisitionReadiness {
    public static func inspectReadOnly(_ candidate: SEC02ExternalCredentialCandidateObservation?)
        -> SEC02ExternalCredentialAcquisitionReadinessResultV1 {
        guard let candidate else { return result(.candidateAbsent) }
        guard candidate.credentialClass == .developerIDApplication else {
            return result(.rejectedCredentialClass, candidate: candidate)
        }
        guard candidate.authorityClaim == .none || candidate.authorityClaim == .c4VerificationRequired else {
            return result(.rejectedAuthorityClaim, candidate: candidate)
        }
        guard candidate.matchingPrivateKeyRepresented else {
            return result(.matchingPrivateKeyRequired, candidate: candidate)
        }
        return result(.acceptableCandidateRepresented, candidate: candidate, mayProceed: true)
    }

    private static func result(_ readiness: SEC02ExternalCredentialAcquisitionReadiness,
                               candidate: SEC02ExternalCredentialCandidateObservation? = nil,
                               mayProceed: Bool = false)
        -> SEC02ExternalCredentialAcquisitionReadinessResultV1 {
        SEC02ExternalCredentialAcquisitionReadinessResultV1(
            readiness: readiness, candidateRepresented: candidate != nil,
            credentialClass: candidate?.credentialClass,
            matchingPrivateKeyRepresented: candidate?.matchingPrivateKeyRepresented ?? false,
            c5ACeremonyMayEventuallyProceed: mayProceed,
            c5BCeremonyMayEventuallyProceed: mayProceed)
    }
}
