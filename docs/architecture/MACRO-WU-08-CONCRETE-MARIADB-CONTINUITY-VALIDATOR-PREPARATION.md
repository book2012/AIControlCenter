# Macro-WU08 Concrete MariaDB Continuity Validator Preparation

## Scope and invariants

WU08 prepares repository contracts, policy, and an injectable Mac adapter only. It creates no operational composition, authorization path, production access, credential acquisition, MariaDB connection, or SQL execution. The Mac AIControlCenter remains the sole Control Plane; Ubuntu remains a stateless zero-authority infrastructure worker. Governance core, SEC-02, WU06, WU07, and `ControlledExecutionPort` semantics are unchanged. `SM_01B_02D_06_SEMANTICS_CHANGE_REQUIRED=NO`.

## Frozen separation

`ExpectedValidationBinding != FixedReadOnlyQueryPlan != CredentialBoundary != DriverInvocation != SanitizedObservation != ValidationDecision != ProductionAccess != HumanAuthorization != Authority`.

The expected binding uses existing closed repository profiles and the exact existing five `DataIdentityCategory` values and three `ContinuityEvidenceCategory` values. It remains `MISSING_AUTHORITATIVE_VALUES`. The fixed query plan remains `MISSING_AUTHORITATIVE_SQL`, because no exact authoritative SQL exists in the repository. Missing bindings fail closed; no database, account, prefix, schema, table, grant, expected value, or SQL is guessed.

The SQL policy accepts only a single syntactically unambiguous `SELECT` or `SHOW` statement and rejects comments, multiple statements, and mutation or session/control verbs. Only a future repository-owned ready plan may reach the driver.

## Secret and driver boundaries

A future secret is not a field of any request, binding, plan, observation, result, projection, audit, authorization, receipt, or mutation model. At the future operational boundary it passes opaquely and directly from the credential boundary into the injected DB driver call. The adapter never retains, serializes, logs, hashes, or includes it in exceptions. Python identity, private constructors, and frozen objects are not security boundaries.

Each invocation permits zero or exactly one driver call. There is no retry, reconnect, fallback, target discovery, candidate enumeration, alternate credential, pool, recovery, rollback, compensation, or claim recovery. Driver exceptions become the constant sanitized result `SANITIZED_DRIVER_FAILURE` before crossing the adapter boundary. PyMySQL remains pinned by the existing `PyMySQL==1.2.0` declaration; import availability alone does not establish compatibility.

## Decision semantics

The canonical outcomes are exactly `VALIDATED`, `REJECTED`, `UNAVAILABLE`, `UNSAFE`, `MALFORMED`, and `UNCERTAIN`. Malformed structure is `MALFORMED`; unavailable authoritative binding/plan is `UNAVAILABLE`; an unsafe plan is `UNSAFE`; ambiguous or missing attempted facts are `UNCERTAIN`; any mismatch is `REJECTED`. `VALIDATED` requires authentication, expected database, expected account, required grants, every one of the five data-identity categories, all three continuity/lineage categories, and the declared continuity baseline to match.

WU11 alone may provide future operational composition after separate human authorization. WU08 does not issue or consume Production authorization and does not couple to Governance `AuthorizationConsumptionPort` or `ControlledExecutionPort`.

## WU08 operational truth

```text
PRODUCTION_ACCESS_PERFORMED=false
PROTECTED_SOURCE_ACCESS_PERFORMED=false
CREDENTIAL_VALIDATION_PERFORMED=false
MARIADB_CONNECTION_PERFORMED=false
SQL_EXECUTION_PERFORMED=false
PRODUCTION_AUTHORIZATION_CONSUMED=false
PRODUCTION_VALIDATION_AVAILABLE=false
RECOVER_EVIDENCE_SUFFICIENT=false
RECOVER_EVIDENCE_GATE=RECOVER_EVIDENCE_INSUFFICIENT
```
