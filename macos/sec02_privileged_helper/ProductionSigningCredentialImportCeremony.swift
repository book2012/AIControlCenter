import Foundation

// C5B is a repository-only ceremony foundation. It cannot import a credential
// and it has no Production authority. C4 remains the sole authority for a
// verified Production signing identity and authoritative Team ID.

public enum SEC02CredentialImportCeremonyState: String, Codable {
    case notStarted = "NOT_STARTED"
    case ready = "READY"
    case attempting = "ATTEMPTING"
    case succeededPendingC4Verification = "SUCCEEDED_PENDING_C4_VERIFICATION"
    case failedConsumed = "FAILED_CONSUMED"
    case uncertainConsumed = "UNCERTAIN_CONSUMED"
}

enum SEC02CredentialImportAttemptOutcome: Equatable { case succeeded, failed, uncertain }
enum SEC02DurableAttemptClaim { case claimed, failedConsumed, uncertainConsumed, alreadyConsumed(SEC02CredentialImportCeremonyState) }

// Immutable, input-only durable uniqueness key. Ceremony ID is deliberately
// excluded at the type level and may be retained only as audit/context data.
// Thus a new ceremony cannot retry an already consumed validated input.
struct SEC02CredentialImportConsumptionKey: Hashable {
    let validatedCredentialInputBinding: SEC02ValidatedCredentialInputBinding

    fileprivate init(validatedCredentialInput: SEC02ValidatedCredentialInputEvidence) {
        self.validatedCredentialInputBinding = validatedCredentialInput.c5AValidationBinding
    }
}

// Purpose-bound contract. A future Production implementation must durably make
// the claim before adapter invocation and durably record a terminal outcome.
// The consumptionKey is the sole durable uniqueness key. ceremonyID is
// separate audit context and C5B intentionally ships no Production journal.
protocol SEC02ProductionCredentialAttemptConsuming {
    func claimOneAttempt(consumptionKey: SEC02CredentialImportConsumptionKey,
                         ceremonyID: String) -> SEC02DurableAttemptClaim
    func recordTerminalOutcome(
        consumptionKey: SEC02CredentialImportConsumptionKey,
        ceremonyID: String,
        outcome: SEC02CredentialImportCeremonyState
    ) -> Bool
}

// An opaque, purpose-bound token for one native credential-import operation.
// It is not credential, C4, signing, or Production-mutation authority. The
// protocol deliberately offers no secret-material or persistence surface and
// does not conform to Encodable/Codable. Only an interactive native boundary
// may issue it to the single closure it mediates.
protocol SEC02EphemeralNativeCredentialImportCapability: AnyObject {}

// A future native adapter may ask this bounded boundary to perform precisely
// one import operation while its secret stays inside the native boundary. C5B
// receives neither secret material nor a callback value representing it. The
// opaque capability exists only as the parameter of that one operation; this
// contract provides no global, thread-local, reusable-context, retry, argv,
// environment, configuration, logging, or persistence route for a secret.
protocol SEC02EphemeralInteractiveSecretAcquiring {
    func mediateOneNativeCredentialImport(
        _ operation: (any SEC02EphemeralNativeCredentialImportCapability)
            -> SEC02CredentialImportAttemptOutcome
    ) -> SEC02CredentialImportAttemptOutcome
}

protocol SEC02ProductionSigningCredentialImportAttempting {
    func attemptProductionSigningCredentialImport(
        ceremonyID: String,
        validatedCredentialInput: SEC02ValidatedCredentialInputEvidence,
        secretAcquisition: any SEC02EphemeralInteractiveSecretAcquiring
    ) -> SEC02CredentialImportAttemptOutcome
}

// The sole repository adapter: deterministic and non-mutating. It never claims
// that live credential import occurred.
struct SEC02NonMutatingCredentialImportAdapter: SEC02ProductionSigningCredentialImportAttempting {
    func attemptProductionSigningCredentialImport(
        ceremonyID: String,
        validatedCredentialInput: SEC02ValidatedCredentialInputEvidence,
        secretAcquisition: any SEC02EphemeralInteractiveSecretAcquiring
    ) -> SEC02CredentialImportAttemptOutcome { .failed }
}

public struct SEC02CredentialImportAuditEvidenceV1: Encodable, Equatable {
    public let schemaVersion = 1
    public let ceremonyID: String
    public let durableAttemptConsumed: Bool
    public let resultState: SEC02CredentialImportCeremonyState
    public let c4VerificationRequired: Bool
}

public struct SEC02CredentialImportCeremonyResultV1: Encodable, Equatable {
    public let schemaVersion = 1
    public let ceremonyID: String
    public let ceremonyState: SEC02CredentialImportCeremonyState
    public let readiness: Bool
    public let attemptConsumed: Bool
    public let credentialReuseAllowed: Bool
    public let adapterReportedSuccess: Bool
    public let liveCredentialImportVerified = false
    public let c4VerificationRequired: Bool
    public let productionSigningIdentityVerified = false
    public let authoritativeTeamID: String? = nil
    public let signedPackageReady = false
    public let keychainMutationPerformed = false
    public let signingPerformed = false
    public let notarizationPerformed = false
    public let smAppServiceAuthorityGranted = false
    public let smAppServiceRegistrationOperational = false
    public let governanceRemediationAuthorityGranted = false
    public let productionRemediationAvailable = false
    public let productionRuntimeMutationAuthorityGranted = false
    public let productionMutationPerformed = false
    public let auditEvidence: SEC02CredentialImportAuditEvidenceV1

    private enum CodingKeys: String, CodingKey {
        case schemaVersion, ceremonyID, ceremonyState, readiness, attemptConsumed,
             credentialReuseAllowed, adapterReportedSuccess, liveCredentialImportVerified,
             c4VerificationRequired, productionSigningIdentityVerified, authoritativeTeamID,
             signedPackageReady, keychainMutationPerformed, signingPerformed, notarizationPerformed,
             smAppServiceAuthorityGranted, smAppServiceRegistrationOperational,
             governanceRemediationAuthorityGranted, productionRemediationAvailable,
             productionRuntimeMutationAuthorityGranted, productionMutationPerformed, auditEvidence
    }

    public func encode(to encoder: Encoder) throws {
        var values = encoder.container(keyedBy: CodingKeys.self)
        try values.encode(schemaVersion, forKey: .schemaVersion)
        try values.encode(ceremonyID, forKey: .ceremonyID)
        try values.encode(ceremonyState, forKey: .ceremonyState)
        try values.encode(readiness, forKey: .readiness)
        try values.encode(attemptConsumed, forKey: .attemptConsumed)
        try values.encode(credentialReuseAllowed, forKey: .credentialReuseAllowed)
        try values.encode(adapterReportedSuccess, forKey: .adapterReportedSuccess)
        try values.encode(liveCredentialImportVerified, forKey: .liveCredentialImportVerified)
        try values.encode(c4VerificationRequired, forKey: .c4VerificationRequired)
        try values.encode(productionSigningIdentityVerified, forKey: .productionSigningIdentityVerified)
        try values.encodeNil(forKey: .authoritativeTeamID)
        try values.encode(signedPackageReady, forKey: .signedPackageReady)
        try values.encode(keychainMutationPerformed, forKey: .keychainMutationPerformed)
        try values.encode(signingPerformed, forKey: .signingPerformed)
        try values.encode(notarizationPerformed, forKey: .notarizationPerformed)
        try values.encode(smAppServiceAuthorityGranted, forKey: .smAppServiceAuthorityGranted)
        try values.encode(smAppServiceRegistrationOperational, forKey: .smAppServiceRegistrationOperational)
        try values.encode(governanceRemediationAuthorityGranted, forKey: .governanceRemediationAuthorityGranted)
        try values.encode(productionRemediationAvailable, forKey: .productionRemediationAvailable)
        try values.encode(productionRuntimeMutationAuthorityGranted, forKey: .productionRuntimeMutationAuthorityGranted)
        try values.encode(productionMutationPerformed, forKey: .productionMutationPerformed)
        try values.encode(auditEvidence, forKey: .auditEvidence)
    }
}

public struct SEC02ProductionSigningCredentialImportCeremony {
    private let ceremonyID: String
    private let validatedCredentialInput: SEC02ValidatedCredentialInputEvidence?
    private var state: SEC02CredentialImportCeremonyState = .notStarted
    private var adapterReportedSuccess = false

    public init(ceremonyID: String, validatedCredentialInput: SEC02ValidatedCredentialInputEvidence?) {
        self.ceremonyID = ceremonyID
        self.validatedCredentialInput = validatedCredentialInput
    }

    public mutating func prepare() -> SEC02CredentialImportCeremonyResultV1 {
        guard state == .notStarted, !ceremonyID.isEmpty, validatedCredentialInput != nil else { return result() }
        state = .ready
        return result()
    }

    mutating func attempt(
        using importer: any SEC02ProductionSigningCredentialImportAttempting,
        secretAcquisition: any SEC02EphemeralInteractiveSecretAcquiring,
        durableAttemptConsumer: any SEC02ProductionCredentialAttemptConsuming
    ) -> SEC02CredentialImportCeremonyResultV1 {
        guard state == .ready, let validatedCredentialInput else { return result() }
        let consumptionKey = SEC02CredentialImportConsumptionKey(
            validatedCredentialInput: validatedCredentialInput)
        switch durableAttemptConsumer.claimOneAttempt(consumptionKey: consumptionKey, ceremonyID: ceremonyID) {
        case .claimed:
            state = .attempting
            let outcome = importer.attemptProductionSigningCredentialImport(
                ceremonyID: ceremonyID, validatedCredentialInput: validatedCredentialInput,
                secretAcquisition: secretAcquisition)
            adapterReportedSuccess = outcome == .succeeded
            let terminal: SEC02CredentialImportCeremonyState = switch outcome {
            case .succeeded: .succeededPendingC4Verification
            case .failed: .failedConsumed
            case .uncertain: .uncertainConsumed
            }
            state = durableAttemptConsumer.recordTerminalOutcome(
                consumptionKey: consumptionKey, ceremonyID: ceremonyID, outcome: terminal)
                ? terminal : .uncertainConsumed
        case .failedConsumed: state = .failedConsumed
        case .uncertainConsumed: state = .uncertainConsumed
        case let .alreadyConsumed(terminal):
            switch terminal {
            case .succeededPendingC4Verification, .failedConsumed, .uncertainConsumed:
                state = terminal
            case .notStarted, .ready, .attempting:
                state = .uncertainConsumed
            }
        }
        return result()
    }

    public func currentResult() -> SEC02CredentialImportCeremonyResultV1 { result() }

    private func result() -> SEC02CredentialImportCeremonyResultV1 {
        let consumed = state != .notStarted && state != .ready
        // C4 progression is authorized by a durable successful terminal state,
        // never merely by an in-memory adapter report. This remains correct
        // after reconstruction or observation from a new ceremony ID.
        let c4Required = state == .succeededPendingC4Verification
        let audit = SEC02CredentialImportAuditEvidenceV1(
            ceremonyID: ceremonyID, durableAttemptConsumed: consumed,
            resultState: state, c4VerificationRequired: c4Required)
        return SEC02CredentialImportCeremonyResultV1(
            ceremonyID: ceremonyID, ceremonyState: state, readiness: state == .ready,
            attemptConsumed: consumed, credentialReuseAllowed: !consumed,
            adapterReportedSuccess: adapterReportedSuccess, c4VerificationRequired: c4Required,
            auditEvidence: audit)
    }
}
