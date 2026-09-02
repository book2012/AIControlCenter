import Foundation

// C6A is a read-only Mac Control Plane observation boundary. It coordinates
// already-established C5A/C5B state and delegates all live identity and Team ID
// authority to C4. It cannot import, mutate, sign, authorize, or retry.

public enum SEC02ProductionSigningCredentialAvailability: String, Codable {
    case externalCredentialRequired = "EXTERNAL_CREDENTIAL_REQUIRED"
    case localInputMetadataReady = "LOCAL_INPUT_METADATA_READY"
    case importRequired = "IMPORT_REQUIRED"
    case identityVerificationRequired = "IDENTITY_VERIFICATION_REQUIRED"
    case productionSigningIdentityVerified = "PRODUCTION_SIGNING_IDENTITY_VERIFIED"
}

public struct SEC02ProductionSigningCredentialAvailabilityResultV1: Encodable, Equatable {
    public let schemaVersion = 1
    public let availability: SEC02ProductionSigningCredentialAvailability
    public let c5AValidatedInputAvailable: Bool
    public let c5BState: SEC02CredentialImportCeremonyState?
    public let c4VerificationPerformed: Bool
    public let productionSigningIdentityVerified: Bool
    public let authoritativeTeamID: String?
    public let inspectionReadOnly = true
    public let automaticRetryPerformed = false
    public let credentialContentsRead = false
    public let passphraseHandled = false
    public let credentialImportPerformed = false
    public let keychainMutationPerformed = false
    public let signingPerformed = false
    public let notarizationPerformed = false
    public let smAppServiceRegistrationPerformed = false
    public let productionMutationPerformed = false
    public let productionAuthorityGranted = false

    private enum CodingKeys: String, CodingKey {
        case schemaVersion, availability, c5AValidatedInputAvailable, c5BState
        case c4VerificationPerformed, productionSigningIdentityVerified, authoritativeTeamID
        case inspectionReadOnly, automaticRetryPerformed, credentialContentsRead, passphraseHandled
        case credentialImportPerformed, keychainMutationPerformed, signingPerformed
        case notarizationPerformed, smAppServiceRegistrationPerformed, productionMutationPerformed
        case productionAuthorityGranted
    }

    public func encode(to encoder: Encoder) throws {
        var values = encoder.container(keyedBy: CodingKeys.self)
        try values.encode(schemaVersion, forKey: .schemaVersion)
        try values.encode(availability, forKey: .availability)
        try values.encode(c5AValidatedInputAvailable, forKey: .c5AValidatedInputAvailable)
        try values.encode(c5BState, forKey: .c5BState)
        try values.encode(c4VerificationPerformed, forKey: .c4VerificationPerformed)
        try values.encode(productionSigningIdentityVerified, forKey: .productionSigningIdentityVerified)
        if let authoritativeTeamID {
            try values.encode(authoritativeTeamID, forKey: .authoritativeTeamID)
        } else {
            try values.encodeNil(forKey: .authoritativeTeamID)
        }
        try values.encode(inspectionReadOnly, forKey: .inspectionReadOnly)
        try values.encode(automaticRetryPerformed, forKey: .automaticRetryPerformed)
        try values.encode(credentialContentsRead, forKey: .credentialContentsRead)
        try values.encode(passphraseHandled, forKey: .passphraseHandled)
        try values.encode(credentialImportPerformed, forKey: .credentialImportPerformed)
        try values.encode(keychainMutationPerformed, forKey: .keychainMutationPerformed)
        try values.encode(signingPerformed, forKey: .signingPerformed)
        try values.encode(notarizationPerformed, forKey: .notarizationPerformed)
        try values.encode(smAppServiceRegistrationPerformed, forKey: .smAppServiceRegistrationPerformed)
        try values.encode(productionMutationPerformed, forKey: .productionMutationPerformed)
        try values.encode(productionAuthorityGranted, forKey: .productionAuthorityGranted)
    }
}

public enum SEC02ProductionSigningCredentialAvailabilityObserver {
    public static func inspectReadOnly(
        validatedCredentialInput: SEC02ValidatedCredentialInputEvidence?,
        importCeremonyResult: SEC02CredentialImportCeremonyResultV1?
    ) -> SEC02ProductionSigningCredentialAvailabilityResultV1 {
        guard validatedCredentialInput != nil else {
            return result(.externalCredentialRequired, c5A: false,
                          c5B: importCeremonyResult?.ceremonyState)
        }

        guard let importCeremonyResult else {
            return result(.localInputMetadataReady, c5A: true, c5B: nil)
        }

        switch importCeremonyResult.ceremonyState {
        case .notStarted:
            return result(.localInputMetadataReady, c5A: true, c5B: .notStarted)
        case .ready:
            return result(.importRequired, c5A: true, c5B: .ready)
        case .succeededPendingC4Verification:
            // This is the sole C6A path into C4. No caller-provided inspector or
            // C4 result can enter this public API, so injected observations can
            // never mint Production identity or Team ID evidence.
            return resultFromAuthoritativeC4(
                SEC02ProductionSigningIdentityVerifier.inspectLocalKeychainReadOnly(),
                c5B: .succeededPendingC4Verification)
        case .attempting, .failedConsumed, .uncertainConsumed:
            // ATTEMPTING is not durable success. Failure and uncertainty are
            // terminal for the consumed input and never open C4 progression.
            return result(.externalCredentialRequired, c5A: true,
                          c5B: importCeremonyResult.ceremonyState)
        }
    }

    private static func resultFromAuthoritativeC4(
        _ c4: SEC02ProductionSigningIdentityResultV1,
        c5B: SEC02CredentialImportCeremonyState
    ) -> SEC02ProductionSigningCredentialAvailabilityResultV1 {
        guard c4.readiness == .ready,
              c4.candidateState == .exactValidDeveloperIDApplication,
              let teamID = c4.authoritativeTeamID else {
            return result(.identityVerificationRequired, c5A: true, c5B: c5B,
                          c4Performed: true)
        }
        return result(.productionSigningIdentityVerified, c5A: true, c5B: c5B,
                      c4Performed: true, verified: true, teamID: teamID)
    }

    private static func result(
        _ availability: SEC02ProductionSigningCredentialAvailability,
        c5A: Bool,
        c5B: SEC02CredentialImportCeremonyState?,
        c4Performed: Bool = false,
        verified: Bool = false,
        teamID: String? = nil
    ) -> SEC02ProductionSigningCredentialAvailabilityResultV1 {
        SEC02ProductionSigningCredentialAvailabilityResultV1(
            availability: availability, c5AValidatedInputAvailable: c5A,
            c5BState: c5B, c4VerificationPerformed: c4Performed,
            productionSigningIdentityVerified: verified,
            authoritativeTeamID: verified ? teamID : nil)
    }
}
