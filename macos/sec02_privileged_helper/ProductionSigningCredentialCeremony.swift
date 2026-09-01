import Darwin
import Foundation

// Repository-level, metadata-only preparation for a future human credential
// import ceremony. This module has no Keychain, signing, identity, Team ID, or
// Production mutation authority. ProductionSigningIdentityVerifier (C4) alone
// remains the authority for a live identity and an authoritative Team ID.

public enum SEC02ProductionSigningCredentialCeremonyState: String, Codable {
    case externalCredentialRequired = "EXTERNAL_CREDENTIAL_REQUIRED"
    case localCredentialInputAbsent = "LOCAL_CREDENTIAL_INPUT_ABSENT"
    case localCredentialInputReady = "LOCAL_CREDENTIAL_INPUT_READY"
    case liveIdentityAbsent = "LIVE_IDENTITY_ABSENT"
    case liveIdentityReady = "LIVE_IDENTITY_READY"
    case notReady = "NOT_READY"
    case readyForSeparateImportCeremony = "READY_FOR_SEPARATE_IMPORT_CEREMONY"
}

public enum SEC02CredentialInputStatus: String, Codable { case absent = "ABSENT", valid = "VALID", invalid = "INVALID" }

public enum SEC02CredentialInputFailure: String, Codable {
    case explicitPathRequired = "EXPLICIT_PATH_REQUIRED"
    case pathMustBeAbsolute = "PATH_MUST_BE_ABSOLUTE"
    case pathComponentRejected = "PATH_COMPONENT_REJECTED"
    case pathDoesNotExist = "PATH_DOES_NOT_EXIST"
    case symlinkTraversalRejected = "SYMLINK_TRAVERSAL_REJECTED"
    case regularFileRequired = "REGULAR_FILE_REQUIRED"
    case invokingDarwinUserMustOwnFile = "INVOKING_DARWIN_USER_MUST_OWN_FILE"
    case groupWritable = "GROUP_WRITABLE"
    case worldWritable = "WORLD_WRITABLE"
    case unsupportedContainerSuffix = "UNSUPPORTED_CONTAINER_SUFFIX"
    case observationFailedClosed = "OBSERVATION_FAILED_CLOSED"
}

struct SEC02CredentialFileMetadata: Equatable {
    let regularFile: Bool
    let ownerUID: uid_t
    let mode: mode_t
    let device: UInt64
    let inode: UInt64
    let birthSeconds: Int64
    let birthNanoseconds: Int64

    init(regularFile: Bool, ownerUID: uid_t, mode: mode_t, device: UInt64 = 0, inode: UInt64 = 0,
         birthSeconds: Int64 = 0, birthNanoseconds: Int64 = 0) {
        self.regularFile = regularFile
        self.ownerUID = ownerUID
        self.mode = mode
        self.device = device
        self.inode = inode
        self.birthSeconds = birthSeconds
        self.birthNanoseconds = birthNanoseconds
    }
}

enum SEC02CredentialMetadataLookup: Equatable {
    case metadata(SEC02CredentialFileMetadata)
    case pathDoesNotExist
    case symlinkTraversalRejected
    case failedClosed
}

// This narrow abstraction lets focused tests model unsafe ownership and file
// modes without changing ownership of real files. The CLI always uses Darwin.
protocol SEC02CredentialMetadataInspecting {
    func inspectMetadataOnly(absolutePath: String) -> SEC02CredentialMetadataLookup
}

public struct SEC02CredentialInputObservation: Encodable, Equatable {
    public let status: SEC02CredentialInputStatus
    public let failure: SEC02CredentialInputFailure?
    public let containerSuffix: String?
    public let regularFile: Bool
    public let ownedByInvokingDarwinUser: Bool
    public let groupWritable: Bool
    public let worldWritable: Bool
    public let symlinkTraversalDetected: Bool

    static func absent(_ failure: SEC02CredentialInputFailure) -> Self {
        Self(status: .absent, failure: failure, containerSuffix: nil, regularFile: false,
             ownedByInvokingDarwinUser: false, groupWritable: false, worldWritable: false,
             symlinkTraversalDetected: false)
    }

    static func invalid(_ failure: SEC02CredentialInputFailure, suffix: String? = nil,
                        regular: Bool = false, owned: Bool = false, groupWritable: Bool = false,
                        worldWritable: Bool = false, symlink: Bool = false) -> Self {
        Self(status: .invalid, failure: failure, containerSuffix: suffix, regularFile: regular,
             ownedByInvokingDarwinUser: owned, groupWritable: groupWritable,
             worldWritable: worldWritable, symlinkTraversalDetected: symlink)
    }
}

// This opaque, immutable value is issued only by the C5A validation boundary.
// Its caller-visible surface contains neither a path nor credential bytes. Its
// sole purpose is to bind a later C5B ceremony to C5A's already validated,
// metadata-only explicit-input decision.
public struct SEC02ValidatedCredentialInputEvidence {
    // Descriptor-bound facts from the successful C5A validation operation.
    // They are not a locator, are never encoded, and are inaccessible to C5B
    // callers. They distinguish a credential input for durable consumption.
    let c5AValidationBinding: SEC02ValidatedCredentialInputBinding
    // This is deliberately file-private: a future native importer must live
    // beside this issuer, reopen only this validated explicit input with
    // O_NOFOLLOW semantics, and revalidate its complete identity before use.
    // It is neither encoded nor logged and is not general path authority.
    fileprivate let futureImportLocator: SEC02FutureCredentialImportLocator

    fileprivate init(c5AValidationBinding: SEC02ValidatedCredentialInputBinding,
                     futureImportLocator: SEC02FutureCredentialImportLocator) {
        self.c5AValidationBinding = c5AValidationBinding
        self.futureImportLocator = futureImportLocator
    }
}

struct SEC02ValidatedCredentialInputBinding: Hashable {
    let device: UInt64
    let inode: UInt64
    let birthSeconds: Int64
    let birthNanoseconds: Int64
    let containerSuffix: String
}

// Purpose-bound, non-Encodable future-import reference. It has no public
// initializer or accessor. C5B does not use it; a future Mac-native importer
// must re-open this exact path without following links and fail closed unless
// device, inode, and Darwin birth identity still match. It never carries
// credential contents and cannot authorize a new caller-provided path.
fileprivate struct SEC02FutureCredentialImportLocator {
    let validatedExplicitPath: String
    let expectedBinding: SEC02ValidatedCredentialInputBinding
}

// C5A returns this only from actual explicit-path filesystem validation. Its
// reference has no public constructor, raw path, encoding, or logging surface.
public struct SEC02ValidatedCredentialInputValidation {
    public let observation: SEC02CredentialInputObservation
    public let validatedCredentialInput: SEC02ValidatedCredentialInputEvidence?

    fileprivate init(observation: SEC02CredentialInputObservation,
                     validatedCredentialInput: SEC02ValidatedCredentialInputEvidence?) {
        self.observation = observation
        self.validatedCredentialInput = validatedCredentialInput
    }
}

// Internal validation facts intentionally stop short of authority-bearing
// evidence. Test-only injected metadata inspectors can reach observations
// through this path, but only the public Darwin-bound issuer below converts
// successful facts into SEC02ValidatedCredentialInputEvidence.
private struct SEC02MetadataOnlyCredentialValidation {
    let observation: SEC02CredentialInputObservation
    let binding: SEC02ValidatedCredentialInputBinding?
}

public struct SEC02ProductionSigningCredentialCeremonyResultV1: Encodable, Equatable {
    public let schemaVersion = 1
    public let ceremonyState: SEC02ProductionSigningCredentialCeremonyState
    public let readiness: SEC02ProductionSigningCredentialCeremonyState
    public let credentialInput: SEC02CredentialInputObservation
    public let credentialInputDiscovered: Bool
    public let credentialInputValidated: Bool
    public let credentialImported = false
    public let productionSigningIdentityVerified = false
    public let authoritativeTeamID: String? = nil
    public let packageSigned = false
    public let smAppServiceRegistered = false
    public let productionRemediationAuthorized = false
    public let inspectionReadOnly = true
    public let filesystemDiscoveryPerformed = false
    public let credentialContentsRead = false
    public let passphraseAccepted = false
    public let subprocessInvoked = false
    public let keychainMutationPerformed = false
    public let signingPerformed = false
    public let notarizationPerformed = false
    public let productionMutationPerformed = false
    public let futureImportContract = SEC02FutureCredentialImportCeremonyContractV1()

    private enum CodingKeys: String, CodingKey {
        case schemaVersion, ceremonyState, readiness, credentialInput, credentialInputDiscovered,
             credentialInputValidated, credentialImported, productionSigningIdentityVerified,
             authoritativeTeamID, packageSigned, smAppServiceRegistered,
             productionRemediationAuthorized, inspectionReadOnly, filesystemDiscoveryPerformed,
             credentialContentsRead, passphraseAccepted, subprocessInvoked, keychainMutationPerformed,
             signingPerformed, notarizationPerformed, productionMutationPerformed, futureImportContract
    }

    public func encode(to encoder: Encoder) throws {
        var values = encoder.container(keyedBy: CodingKeys.self)
        try values.encode(schemaVersion, forKey: .schemaVersion)
        try values.encode(ceremonyState, forKey: .ceremonyState)
        try values.encode(readiness, forKey: .readiness)
        try values.encode(credentialInput, forKey: .credentialInput)
        try values.encode(credentialInputDiscovered, forKey: .credentialInputDiscovered)
        try values.encode(credentialInputValidated, forKey: .credentialInputValidated)
        try values.encode(credentialImported, forKey: .credentialImported)
        try values.encode(productionSigningIdentityVerified, forKey: .productionSigningIdentityVerified)
        try values.encodeNil(forKey: .authoritativeTeamID)
        try values.encode(packageSigned, forKey: .packageSigned)
        try values.encode(smAppServiceRegistered, forKey: .smAppServiceRegistered)
        try values.encode(productionRemediationAuthorized, forKey: .productionRemediationAuthorized)
        try values.encode(inspectionReadOnly, forKey: .inspectionReadOnly)
        try values.encode(filesystemDiscoveryPerformed, forKey: .filesystemDiscoveryPerformed)
        try values.encode(credentialContentsRead, forKey: .credentialContentsRead)
        try values.encode(passphraseAccepted, forKey: .passphraseAccepted)
        try values.encode(subprocessInvoked, forKey: .subprocessInvoked)
        try values.encode(keychainMutationPerformed, forKey: .keychainMutationPerformed)
        try values.encode(signingPerformed, forKey: .signingPerformed)
        try values.encode(notarizationPerformed, forKey: .notarizationPerformed)
        try values.encode(productionMutationPerformed, forKey: .productionMutationPerformed)
        try values.encode(futureImportContract, forKey: .futureImportContract)
    }
}

// Contract only: implementation requires a distinct future security ceremony.
public struct SEC02FutureCredentialImportCeremonyContractV1: Encodable, Equatable {
    public let schemaVersion = 1
    public let implementationStatus = "CONTRACT_ONLY_NOT_IMPLEMENTED"
    public let platform = "MAC_ONLY"
    public let requiresSeparateExplicitHumanSecurityCeremony = true
    public let boundedCredentialImportAttempts = 1
    public let automaticRetryAllowed = false
    public let failedOrUncertainImportRequiresNewCeremony = true
    public let credentialReuseAllowedAfterFailedOrUncertainImport = false
    public let productionRuntimeMutationAuthority = false
    public let passphraseStoredInRepository = false
    public let passphraseLogged = false
    public let passphrasePersisted = false
    public let passphraseAcceptedAsCommandLineArgument = false
    public let passphraseAcceptedThroughEnvironmentVariable = false
    public let nativeMacOSSecurityBoundaryPreferred = true
    public let importSuccessEstablishesProductionSigningIdentityVerified = false
    public let subsequentC4ProductionSigningIdentityVerifierRequired = true
    public let authoritativeTeamIDSource = "C4_PRODUCTION_SIGNING_IDENTITY_VERIFIER_ONLY"
    public let productionMutationPerformed = false
}

struct SEC02DarwinCredentialMetadataInspector: SEC02CredentialMetadataInspecting {
    func inspectMetadataOnly(absolutePath: String) -> SEC02CredentialMetadataLookup {
        // lstat each supplied-path component, then bind the leaf observation to
        // an O_NOFOLLOW descriptor through descriptor-relative parent traversal.
        // No file bytes are read or hashed.
        var componentPath = ""
        let components = absolutePath.split(separator: "/", omittingEmptySubsequences: true)
        for (index, component) in components.enumerated() {
            componentPath += "/" + component
            var componentMetadata = stat()
            if lstat(componentPath, &componentMetadata) != 0 {
                return errno == ENOENT ? .pathDoesNotExist : .failedClosed
            }
            if (componentMetadata.st_mode & S_IFMT) == S_IFLNK { return .symlinkTraversalRejected }
            if index == components.count - 1 && (componentMetadata.st_mode & S_IFMT) != S_IFREG {
                return .metadata(SEC02CredentialFileMetadata(
                    regularFile: false, ownerUID: componentMetadata.st_uid, mode: componentMetadata.st_mode,
                    device: UInt64(componentMetadata.st_dev), inode: UInt64(componentMetadata.st_ino)))
            }
        }

        guard let leafName = components.last else { return .failedClosed }
        var parentDescriptor = open("/", O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC)
        guard parentDescriptor >= 0 else { return .failedClosed }
        for component in components.dropLast() {
            let nextDescriptor = openat(
                parentDescriptor, String(component), O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC)
            let traversalError = errno
            close(parentDescriptor)
            guard nextDescriptor >= 0 else {
                return traversalError == ELOOP ? .symlinkTraversalRejected : .failedClosed
            }
            parentDescriptor = nextDescriptor
        }
        defer { close(parentDescriptor) }

        var preopenLeafMetadata = stat()
        guard fstatat(parentDescriptor, String(leafName), &preopenLeafMetadata, AT_SYMLINK_NOFOLLOW) == 0
        else { return errno == ENOENT ? .pathDoesNotExist : .failedClosed }
        guard (preopenLeafMetadata.st_mode & S_IFMT) != S_IFLNK else { return .symlinkTraversalRejected }
        guard (preopenLeafMetadata.st_mode & S_IFMT) == S_IFREG else {
            return .metadata(SEC02CredentialFileMetadata(
                regularFile: false, ownerUID: preopenLeafMetadata.st_uid, mode: preopenLeafMetadata.st_mode,
                device: UInt64(preopenLeafMetadata.st_dev), inode: UInt64(preopenLeafMetadata.st_ino)))
        }

        let descriptor = openat(parentDescriptor, String(leafName), O_RDONLY | O_NOFOLLOW | O_CLOEXEC)
        guard descriptor >= 0 else {
            if errno == ELOOP { return .symlinkTraversalRejected }
            return errno == ENOENT ? .pathDoesNotExist : .failedClosed
        }
        defer { close(descriptor) }
        var descriptorMetadata = stat()
        guard fstat(descriptor, &descriptorMetadata) == 0 else { return .failedClosed }
        guard preopenLeafMetadata.st_dev == descriptorMetadata.st_dev
                && preopenLeafMetadata.st_ino == descriptorMetadata.st_ino
        else { return .failedClosed }
        // Detect replacement between descriptor binding and the final full-path
        // observation, including replacement of a parent path component.
        var leafMetadata = stat()
        guard lstat(absolutePath, &leafMetadata) == 0 else { return .failedClosed }
        guard (leafMetadata.st_mode & S_IFMT) != S_IFLNK else { return .symlinkTraversalRejected }
        guard leafMetadata.st_dev == descriptorMetadata.st_dev && leafMetadata.st_ino == descriptorMetadata.st_ino
        else { return .failedClosed }
        return .metadata(SEC02CredentialFileMetadata(
            regularFile: (descriptorMetadata.st_mode & S_IFMT) == S_IFREG,
            ownerUID: descriptorMetadata.st_uid, mode: descriptorMetadata.st_mode,
            device: UInt64(descriptorMetadata.st_dev), inode: UInt64(descriptorMetadata.st_ino),
            birthSeconds: Int64(descriptorMetadata.st_birthtimespec.tv_sec),
            birthNanoseconds: Int64(descriptorMetadata.st_birthtimespec.tv_nsec)))
    }
}

public enum SEC02ProductionSigningCredentialCeremony {
    public static func inspectExplicitPathReadOnly(_ explicitPath: String?)
        -> SEC02CredentialInputObservation {
        inspectExplicitPathReadOnly(explicitPath, inspector: SEC02DarwinCredentialMetadataInspector())
    }

    static func inspectExplicitPathReadOnly(_ explicitPath: String?,
                                            inspector: any SEC02CredentialMetadataInspecting)
        -> SEC02CredentialInputObservation {
        observedMetadataValidation(explicitPath, inspector: inspector).observation
    }

    private static func observedMetadataValidation(_ explicitPath: String?,
                                                    inspector: any SEC02CredentialMetadataInspecting)
        -> SEC02MetadataOnlyCredentialValidation {
        guard let explicitPath, !explicitPath.isEmpty else { return invalidValidation(.absent(.explicitPathRequired)) }
        guard explicitPath.hasPrefix("/") else { return invalidValidation(.invalid(.pathMustBeAbsolute)) }
        let pathComponents = explicitPath.split(separator: "/", omittingEmptySubsequences: false)
        guard !pathComponents.contains(where: { $0 == "." || $0 == ".." }) else {
            return invalidValidation(.invalid(.pathComponentRejected))
        }
        let extensionValue = URL(fileURLWithPath: explicitPath).pathExtension
        guard extensionValue == "p12" || extensionValue == "pfx" else {
            return invalidValidation(.invalid(.unsupportedContainerSuffix,
                suffix: extensionValue.isEmpty ? nil : ".\(extensionValue)"))
        }
        let suffix = ".\(extensionValue)"
        switch inspector.inspectMetadataOnly(absolutePath: explicitPath) {
        case .pathDoesNotExist: return invalidValidation(.invalid(.pathDoesNotExist, suffix: suffix))
        case .symlinkTraversalRejected:
            return invalidValidation(.invalid(.symlinkTraversalRejected, suffix: suffix, symlink: true))
        case .failedClosed: return invalidValidation(.invalid(.observationFailedClosed, suffix: suffix))
        case let .metadata(metadata):
            guard metadata.regularFile else { return invalidValidation(.invalid(.regularFileRequired, suffix: suffix)) }
            guard metadata.ownerUID == getuid() else {
                return invalidValidation(.invalid(.invokingDarwinUserMustOwnFile, suffix: suffix, regular: true))
            }
            let groupWritable = (metadata.mode & S_IWGRP) != 0
            guard !groupWritable else {
                return invalidValidation(.invalid(.groupWritable, suffix: suffix, regular: true, owned: true, groupWritable: true))
            }
            let worldWritable = (metadata.mode & S_IWOTH) != 0
            guard !worldWritable else {
                return invalidValidation(.invalid(.worldWritable, suffix: suffix, regular: true, owned: true, worldWritable: true))
            }
            let observation = SEC02CredentialInputObservation(status: .valid, failure: nil, containerSuffix: suffix,
                regularFile: true, ownedByInvokingDarwinUser: true, groupWritable: false,
                worldWritable: false, symlinkTraversalDetected: false)
            return SEC02MetadataOnlyCredentialValidation(observation: observation, binding:
                SEC02ValidatedCredentialInputBinding(device: metadata.device, inode: metadata.inode,
                    birthSeconds: metadata.birthSeconds, birthNanoseconds: metadata.birthNanoseconds,
                    containerSuffix: suffix))
        }
    }

    private static func invalidValidation(_ observation: SEC02CredentialInputObservation)
        -> SEC02MetadataOnlyCredentialValidation {
        SEC02MetadataOnlyCredentialValidation(observation: observation, binding: nil)
    }

    // This is the only C5A issuance path for C5B evidence. It performs the
    // same actual explicit-path validation above; metadata DTOs cannot mint a
    // reference. No credential contents are read.
    public static func validateExplicitPathForFutureImport(_ explicitPath: String?)
        -> SEC02ValidatedCredentialInputValidation {
        // This is the sole evidence issuer. There is intentionally no
        // inspector-injected overload: injected inspectors may observe only.
        let validation = observedMetadataValidation(explicitPath,
            inspector: SEC02DarwinCredentialMetadataInspector())
        guard let explicitPath, let binding = validation.binding else {
            return SEC02ValidatedCredentialInputValidation(observation: validation.observation,
                                                            validatedCredentialInput: nil)
        }
        return SEC02ValidatedCredentialInputValidation(observation: validation.observation,
            validatedCredentialInput: SEC02ValidatedCredentialInputEvidence(c5AValidationBinding: binding,
                futureImportLocator: SEC02FutureCredentialImportLocator(
                    validatedExplicitPath: explicitPath, expectedBinding: binding)))
    }

    // Local metadata is never live credential authority. This intentionally has
    // no Team ID or C4-result parameter, so callers cannot manufacture either.
    public static func evaluateLocalInputOnly(_ credentialInput: SEC02CredentialInputObservation)
        -> SEC02ProductionSigningCredentialCeremonyResultV1 {
        let state: SEC02ProductionSigningCredentialCeremonyState
        let readiness: SEC02ProductionSigningCredentialCeremonyState
        switch credentialInput.status {
        case .absent:
            state = .localCredentialInputAbsent
            readiness = .externalCredentialRequired
        case .valid:
            state = .localCredentialInputReady
            readiness = .readyForSeparateImportCeremony
        case .invalid:
            state = .notReady
            readiness = .notReady
        }
        return SEC02ProductionSigningCredentialCeremonyResultV1(
            ceremonyState: state, readiness: readiness, credentialInput: credentialInput,
            credentialInputDiscovered: credentialInput.status != .absent,
            credentialInputValidated: credentialInput.status == .valid)
    }
}
