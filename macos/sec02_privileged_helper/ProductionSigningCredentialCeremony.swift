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

    init(regularFile: Bool, ownerUID: uid_t, mode: mode_t) {
        self.regularFile = regularFile
        self.ownerUID = ownerUID
        self.mode = mode
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
                    regularFile: false, ownerUID: componentMetadata.st_uid, mode: componentMetadata.st_mode))
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
                regularFile: false, ownerUID: preopenLeafMetadata.st_uid, mode: preopenLeafMetadata.st_mode))
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
            ownerUID: descriptorMetadata.st_uid, mode: descriptorMetadata.st_mode))
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
        guard let explicitPath, !explicitPath.isEmpty else { return .absent(.explicitPathRequired) }
        guard explicitPath.hasPrefix("/") else { return .invalid(.pathMustBeAbsolute) }
        let pathComponents = explicitPath.split(separator: "/", omittingEmptySubsequences: false)
        guard !pathComponents.contains(where: { $0 == "." || $0 == ".." }) else {
            return .invalid(.pathComponentRejected)
        }
        let extensionValue = URL(fileURLWithPath: explicitPath).pathExtension
        guard extensionValue == "p12" || extensionValue == "pfx" else {
            return .invalid(.unsupportedContainerSuffix,
                            suffix: extensionValue.isEmpty ? nil : ".\(extensionValue)")
        }
        let suffix = ".\(extensionValue)"
        switch inspector.inspectMetadataOnly(absolutePath: explicitPath) {
        case .pathDoesNotExist: return .invalid(.pathDoesNotExist, suffix: suffix)
        case .symlinkTraversalRejected:
            return .invalid(.symlinkTraversalRejected, suffix: suffix, symlink: true)
        case .failedClosed: return .invalid(.observationFailedClosed, suffix: suffix)
        case let .metadata(metadata):
            guard metadata.regularFile else { return .invalid(.regularFileRequired, suffix: suffix) }
            guard metadata.ownerUID == getuid() else {
                return .invalid(.invokingDarwinUserMustOwnFile, suffix: suffix, regular: true)
            }
            let groupWritable = (metadata.mode & S_IWGRP) != 0
            guard !groupWritable else {
                return .invalid(.groupWritable, suffix: suffix, regular: true, owned: true, groupWritable: true)
            }
            let worldWritable = (metadata.mode & S_IWOTH) != 0
            guard !worldWritable else {
                return .invalid(.worldWritable, suffix: suffix, regular: true, owned: true, worldWritable: true)
            }
            return SEC02CredentialInputObservation(status: .valid, failure: nil, containerSuffix: suffix,
                regularFile: true, ownedByInvokingDarwinUser: true, groupWritable: false,
                worldWritable: false, symlinkTraversalDetected: false)
        }
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
