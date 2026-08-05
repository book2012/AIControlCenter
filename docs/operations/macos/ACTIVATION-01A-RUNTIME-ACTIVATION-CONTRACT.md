# ACTIVATION-01A Runtime Activation Contract

## Status

Gate:

`ACTIVATION-01A — Architecture and Runbook Only`

This document defines the runtime activation contract only.

It does not authorize or perform activation, restart, rollback, launchd
modification, Caddy modification, public opening, Ubuntu modification or
Production authorization.

Production remains `NOT_AUTHORIZED`.

## Verified baseline

- Branch: `feature/homepage-product-management-console`
- Source/build baseline: `acd80ab9f6aeb848900e1a19e3fa3afd69face8a`
- Runtime build and smoke documentation commit:
  `180d874bcbd17f74e6b816223fe3527f36332ecf`
- Candidate Runtime: `acd80ab9f6ae`
- Active Runtime: `b9ad351a7241`
- Canonical serving target: `core.api.shadow:app`
- LaunchDaemon identity: `system/com.aicontrolcenter.api.shadow`
- Localhost listener: `127.0.0.1:18100`
- Direct localhost GET routes: HTTP `200`
- `POST /health`: HTTP `405`
- Exact smoke PID and listener cleanup: `PASS`
- Git local and remote state: synchronized
- Production authorization: `NOT_AUTHORIZED`

## Canonical document bindings

This contract extends, but does not replace:

- `docs/operations/macos/PRODUCTION-RUNTIME-BOOTSTRAP.md`
- `docs/operations/macos/LAUNCHD-SHADOW-DAEMON.md`
- `docs/deployment/M4-A1-CONTROLLED-ACTIVATION-ARCHITECTURE.md`
- `docs/operations/M4-CONTROLLED-ACTIVATION-CHECKLIST.md`
- `docs/operations/PI-009-PRODUCTION-ACTIVATION-GATE.md`
- `docs/operations/HUMAN-APPROVAL-GATES.md`

Where this document is silent, the stricter existing canonical contract
continues to apply.

## Control Plane boundary

AIControlCenter remains the sole Control Plane and owns:

- Activation governance
- Authorization validation
- Runtime identity binding
- Evidence validation
- Activation orchestration policy
- Failure and recovery decisions

The Mac mini remains the runtime host and always-on Brain.

Ubuntu remains a stateless infrastructure worker and cannot own activation,
authorization, application state, business logic, audit or governance.

OpenClaw, n8n, WordPress, WooCommerce, Caddy, APIs and the candidate runtime
cannot issue Production authorization.

## Atomic activation contract

Activation must be an explicit operation against one previously finalized
Runtime release.

Immediately before pointer replacement, the activation operation must verify:

`actual_current_runtime == authorized_expected_current_runtime`

For this candidate:

- Authorized expected current runtime: `b9ad351a7241`
- Authorized candidate runtime: `acd80ab9f6ae`

A mismatch must fail closed before mutation.

The switch must use the existing canonical same-filesystem atomic replacement
symlink rename for `runtime/current`.

The operation must not:

- Delete `runtime/current` before preparing its replacement
- Patch a finalized Runtime release
- Select the mutable repository `.venv`
- Install dependencies during activation
- Select the newest Runtime automatically
- Activate a Runtime whose source identity differs from authorization
- Continue when the expected current Runtime differs

The activation report must preserve:

- Previous Runtime target
- Candidate Runtime target
- Resulting Runtime target
- Full source commit
- Runtime metadata identity
- Source marker identity
- Activation result

## Exact service restart contract

Runtime activation and service restart remain separate operational gates.

The exact future service identity is:

`system/com.aicontrolcenter.api.shadow`

The only approved restart form for a loaded service is:

`launchctl kickstart -k system/com.aicontrolcenter.api.shadow`

ACTIVATION-01A documents this command but does not authorize its execution.

A future restart authorization must bind:

- Exact launchd domain: `system`
- Exact launchd label: `com.aicontrolcenter.api.shadow`
- Exact candidate Runtime
- Exact expected previous Runtime
- Exact source commit
- Exact operation ID
- Human approver identity
- Authorization expiry
- Single-use state

The restart operation must be attempted exactly once.

The operation must not:

- Guess a service label
- Search for a similar service
- Use `bootout`
- Use `bootstrap`
- Modify a plist
- Use `pkill`
- Use `killall`
- Restart Caddy
- Restart an unrelated service
- Retry through another restart mechanism

A failed restart must enter the fail-closed path.

## Post-activation validation

Post-activation validation must use direct localhost access before any public
opening decision.

### Runtime pointer

Verify that `runtime/current` resolves exactly to:

`acd80ab9f6ae`

Verify that the selected release contains the expected:

- Runtime metadata
- Source commit marker
- Executable Runtime Python
- Dependency identity
- Canonical application import

### Service identity

Verify:

- LaunchDaemon service:
  `system/com.aicontrolcenter.api.shadow`
- Application user: `kyouhan`
- Root application process: prohibited
- Canonical serving target: `core.api.shadow:app`
- Exactly one expected application process
- No stale smoke-owned process

### Listener identity

Verify:

- Address: `127.0.0.1`
- Port: `18100`
- Exactly one expected listener
- Listener PID matches the LaunchDaemon application PID
- No temporary smoke listener remains
- No public interface listener exists

### HTTP contract

Every route in the version-controlled smoke manifest must be validated.

Required expectations:

- Every declared direct localhost GET route returns HTTP `200`
- `POST /health` returns HTTP `405`
- No unexpected redirect occurs
- No connection error occurs
- No timeout occurs
- No write method becomes exposed

### Exact cleanup

Any validation-created process must be tracked using its exact PID.

Cleanup must:

- Verify PID ownership before signaling
- Signal only the owned PID
- Confirm process exit
- Confirm listener release
- Record the result

Process-name pattern cleanup is prohibited.

## Fail-closed conditions

The activation attempt fails closed when any required condition fails,
including:

- Authorization missing, expired, reused or mismatched
- Expected current Runtime mismatch
- Candidate Runtime identity mismatch
- Source commit mismatch
- Runtime metadata failure
- Source marker failure
- Python executable failure
- Dependency validation failure
- Atomic pointer replacement failure
- Resulting pointer mismatch
- Exact service restart failure
- Process identity failure
- Listener identity failure
- Required GET route not returning HTTP `200`
- `POST /health` not returning HTTP `405`
- Exact cleanup failure
- Evidence write or validation failure
- Concurrent or unexplained Runtime mutation
- Git state contradiction

Fail-closed means:

- Do not open public access
- Do not modify Caddy
- Do not modify launchd definitions
- Do not select another Runtime automatically
- Do not retry using an alternative service operation
- Preserve all available evidence
- Mark Production authorization false
- Require human review

## Rollback boundary

The previous target recorded in the activation report is rollback evidence.

It is not rollback authorization.

Rollback must not execute automatically under ACTIVATION-01A.

A rollback requires a new and separately authorized explicit activation of the
previously validated immutable release.

The rollback authorization must bind:

- Failed operation ID
- Failed candidate Runtime
- Recorded previous Runtime
- Exact source identity of the previous Runtime
- Exact service identity
- Human rollback operator
- Independent approver where required
- New single-use authorization
- New evidence operation

If the current Runtime changed after failure, automatic recovery must not
overwrite it.

Concurrent or unexplained mutation requires human intervention.

## Evidence contract

One canonical JSON record must be produced for every future activation attempt.

Required evidence includes:

- Schema version
- Operation ID
- Gate
- Mode
- Status
- Start and completion timestamps
- Human authorization reference
- Authorization expiry and consumption state
- Git branch
- Git HEAD
- Working-tree state
- Local and remote synchronization state
- Expected current Runtime
- Actual Runtime before activation
- Candidate Runtime
- Actual Runtime after activation
- Full source commit
- Runtime metadata identity
- Source marker identity
- Repository path
- Python executable
- Python version
- Virtual environment identity
- Effective `PYTHONPATH`
- Dependency identity
- Canonical serving target
- launchd domain
- launchd label
- Restart attempt count
- Process identity result
- Listener identity result
- HTTP validation results
- Exact cleanup result
- Failure reason
- Rollback authorization state
- Supporting artifact paths and digests
- Sanitized errors

Every check must record:

- Check ID
- Expected value
- Actual value
- Result
- Blocking severity
- Timestamp
- Supporting evidence

Evidence must not contain secrets, access tokens, API keys, authorization
headers, cookies or private credentials.

Human-readable reports must be derived from canonical JSON evidence.

## Repository PYTHONPATH limitation

The Runtime Python environment and dependencies are finalized beneath the
versioned Runtime release path.

However, the current candidate application source remains coupled to the
repository through the effective `PYTHONPATH`.

The candidate is therefore not yet a completely independent immutable
application artifact.

Until this coupling is removed, Runtime identity must additionally bind:

- Repository absolute path
- Exact repository source commit
- Clean working-tree state
- Effective `PYTHONPATH`
- Exact Python executable
- Python version
- Dependency identity
- Canonical serving target

Repository mutation, relocation or source mismatch after validation must fail
closed.

Production authorization must explicitly acknowledge this limitation.

Long-term remediation requires:

- A versioned immutable application package
- An isolated release environment
- An application artifact digest
- Removal of the mutable repository root from Production `PYTHONPATH`
- Rollback independent of repository working-tree state

## Authorization boundary

ACTIVATION-01A grants no Production authorization.

A future Production activation authorization must be:

- Issued by an identified human approver
- Independent where required by policy
- Bound to one exact operation
- Bound to one exact branch and commit
- Bound to one expected current Runtime
- Bound to one candidate Runtime
- Bound to one launchd service
- Time-limited
- Single-use
- Consumed after success or failure
- Explicit about the repository `PYTHONPATH` limitation

Readiness is not authorization.

Documentation is not authorization.

Build evidence is not authorization.

An activation report is not rollback authorization.

## ACTIVATION-01A closure conditions

ACTIVATION-01A may close only when:

- This contract is reviewed
- Canonical cross-references are valid
- Atomic activation is documented
- Exact service restart is documented
- Post-activation validation is documented
- Fail-closed behavior is documented
- Rollback authorization separation is documented
- Evidence requirements are documented
- Repository `PYTHONPATH` coupling is documented
- Git documentation changes are reviewed
- Runtime mutation count remains zero
- Service restart count remains zero
- Rollback execution count remains zero
- launchd modification count remains zero
- Caddy modification count remains zero
- Ubuntu modification count remains zero
- Public opening count remains zero
- Production authorization remains false
