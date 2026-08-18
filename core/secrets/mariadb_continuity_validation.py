"""Value-free MariaDB historical credential-continuity validation facts."""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.secrets.mariadb_continuity_validation_port import (
        MariaDBContinuityValidationPort,
    )


class ValidationOutcome(str, Enum):
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    UNAVAILABLE = "UNAVAILABLE"
    UNSAFE = "UNSAFE"
    MALFORMED = "MALFORMED"
    UNCERTAIN = "UNCERTAIN"


class ValidationFact(str, Enum):
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    NOT_EVALUATED = "NOT_EVALUATED"
    UNCERTAIN = "UNCERTAIN"


class ConsumerCompatibility(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"


class ValidationReasonCode(str, Enum):
    ALL_MANDATORY_FACTS_CONFIRMED = "ALL_MANDATORY_FACTS_CONFIRMED"
    CREDENTIAL_EXPLICITLY_REJECTED = "CREDENTIAL_EXPLICITLY_REJECTED"
    CAPABILITY_UNAVAILABLE_BEFORE_ATTEMPT = "CAPABILITY_UNAVAILABLE_BEFORE_ATTEMPT"
    VALIDATION_PRECONDITION_UNSAFE = "VALIDATION_PRECONDITION_UNSAFE"
    CAPABILITY_OBSERVATION_MALFORMED = "CAPABILITY_OBSERVATION_MALFORMED"
    ATTEMPT_RESULT_UNCERTAIN = "ATTEMPT_RESULT_UNCERTAIN"


class TargetProfile(str, Enum):
    SHOPPING_SECRET_PROVISIONING = "SHOPPING_SECRET_PROVISIONING"


class AccountProfile(str, Enum):
    SHOPPING_MARIADB_HISTORICAL_ACCOUNT = "SHOPPING_MARIADB_HISTORICAL_ACCOUNT"


class DatabaseProfile(str, Enum):
    SHOPPING_WORDPRESS_DATABASE = "SHOPPING_WORDPRESS_DATABASE"


class GrantsProfile(str, Enum):
    SHOPPING_WORDPRESS_REQUIRED_GRANTS = "SHOPPING_WORDPRESS_REQUIRED_GRANTS"


class DataIdentityProfile(str, Enum):
    SHOPPING_WORDPRESS_DATA_IDENTITY = "SHOPPING_WORDPRESS_DATA_IDENTITY"


class ContinuityBaselineProfile(str, Enum):
    SM_01B_02D_05_HISTORICAL_CREDENTIAL = (
        "SM_01B_02D_05_HISTORICAL_CREDENTIAL"
    )


class ValidationProfile(str, Enum):
    MARIADB_HISTORICAL_CREDENTIAL_CONTINUITY_V1 = (
        "MARIADB_HISTORICAL_CREDENTIAL_CONTINUITY_V1"
    )


@dataclass(frozen=True, slots=True)
class MariaDBContinuityValidationRequest:
    target: TargetProfile
    account_profile: AccountProfile
    database_profile: DatabaseProfile
    grants_profile: GrantsProfile
    data_identity_profile: DataIdentityProfile
    continuity_baseline_profile: ContinuityBaselineProfile
    validation_profile: ValidationProfile

    def __post_init__(self) -> None:
        expected = (
            (self.target, TargetProfile, "target"),
            (self.account_profile, AccountProfile, "account_profile"),
            (self.database_profile, DatabaseProfile, "database_profile"),
            (self.grants_profile, GrantsProfile, "grants_profile"),
            (self.data_identity_profile, DataIdentityProfile, "data_identity_profile"),
            (
                self.continuity_baseline_profile,
                ContinuityBaselineProfile,
                "continuity_baseline_profile",
            ),
            (self.validation_profile, ValidationProfile, "validation_profile"),
        )
        for value, expected_type, field_name in expected:
            if type(value) is not expected_type:
                raise TypeError(f"{field_name} must be {expected_type.__name__}")

    @classmethod
    def canonical(cls) -> "MariaDBContinuityValidationRequest":
        """Construct the sole value-free factual validation profile."""

        return cls(
            target=TargetProfile.SHOPPING_SECRET_PROVISIONING,
            account_profile=AccountProfile.SHOPPING_MARIADB_HISTORICAL_ACCOUNT,
            database_profile=DatabaseProfile.SHOPPING_WORDPRESS_DATABASE,
            grants_profile=GrantsProfile.SHOPPING_WORDPRESS_REQUIRED_GRANTS,
            data_identity_profile=DataIdentityProfile.SHOPPING_WORDPRESS_DATA_IDENTITY,
            continuity_baseline_profile=(
                ContinuityBaselineProfile.SM_01B_02D_05_HISTORICAL_CREDENTIAL
            ),
            validation_profile=(
                ValidationProfile.MARIADB_HISTORICAL_CREDENTIAL_CONTINUITY_V1
            ),
        )

    def to_projection(self) -> dict[str, str]:
        return {
            "target": self.target.value,
            "account_profile": self.account_profile.value,
            "database_profile": self.database_profile.value,
            "grants_profile": self.grants_profile.value,
            "data_identity_profile": self.data_identity_profile.value,
            "continuity_baseline_profile": self.continuity_baseline_profile.value,
            "validation_profile": self.validation_profile.value,
        }


@dataclass(frozen=True, slots=True)
class MariaDBContinuityValidationResult:
    outcome: ValidationOutcome
    attempted_count: int
    request: MariaDBContinuityValidationRequest
    credential_acceptance: ValidationFact
    expected_database_identity: ValidationFact
    expected_account_identity: ValidationFact
    required_grants: ValidationFact
    data_identity: ValidationFact
    data_continuity: ValidationFact
    consumer_compatibility: ConsumerCompatibility
    reason_code: ValidationReasonCode

    def __post_init__(self) -> None:
        if type(self.outcome) is not ValidationOutcome:
            raise TypeError("outcome must be ValidationOutcome")
        if type(self.attempted_count) is not int or self.attempted_count not in (0, 1):
            raise ValueError("attempted_count must be exactly 0 or 1")
        if type(self.request) is not MariaDBContinuityValidationRequest:
            raise TypeError("request must be MariaDBContinuityValidationRequest")
        facts = self.mandatory_facts
        if any(type(fact) is not ValidationFact for fact in facts):
            raise TypeError("validation facts must be ValidationFact")
        if self.consumer_compatibility is not ConsumerCompatibility.NOT_EVALUATED:
            raise ValueError("consumer compatibility must remain NOT_EVALUATED")
        if type(self.reason_code) is not ValidationReasonCode:
            raise TypeError("reason_code must be ValidationReasonCode")

        not_evaluated = (ValidationFact.NOT_EVALUATED,) * 6
        expected_reason = {
            ValidationOutcome.VALIDATED: ValidationReasonCode.ALL_MANDATORY_FACTS_CONFIRMED,
            ValidationOutcome.REJECTED: ValidationReasonCode.CREDENTIAL_EXPLICITLY_REJECTED,
            ValidationOutcome.UNAVAILABLE: (
                ValidationReasonCode.CAPABILITY_UNAVAILABLE_BEFORE_ATTEMPT
            ),
            ValidationOutcome.UNSAFE: ValidationReasonCode.VALIDATION_PRECONDITION_UNSAFE,
            ValidationOutcome.MALFORMED: (
                ValidationReasonCode.CAPABILITY_OBSERVATION_MALFORMED
            ),
            ValidationOutcome.UNCERTAIN: ValidationReasonCode.ATTEMPT_RESULT_UNCERTAIN,
        }[self.outcome]
        if self.reason_code is not expected_reason:
            raise ValueError("reason code contradicts outcome")
        if self.outcome is ValidationOutcome.VALIDATED:
            valid = self.attempted_count == 1 and all(
                fact is ValidationFact.CONFIRMED for fact in facts
            )
        elif self.outcome is ValidationOutcome.REJECTED:
            valid = self.attempted_count == 1 and facts == (
                ValidationFact.REJECTED,
                *not_evaluated[1:],
            )
        elif self.outcome in (
            ValidationOutcome.UNAVAILABLE,
            ValidationOutcome.UNSAFE,
            ValidationOutcome.MALFORMED,
        ):
            valid = self.attempted_count == 0 and facts == not_evaluated
        else:
            valid = (
                self.attempted_count == 1
                and ValidationFact.UNCERTAIN in facts
                and ValidationFact.REJECTED not in facts
            )
        if not valid:
            raise ValueError(f"contradictory {self.outcome.value} validation result")

    @property
    def mandatory_facts(self) -> tuple[ValidationFact, ...]:
        return (
            self.credential_acceptance,
            self.expected_database_identity,
            self.expected_account_identity,
            self.required_grants,
            self.data_identity,
            self.data_continuity,
        )

    def to_projection(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "inspection": "READ_ONLY",
            "outcome": self.outcome.value,
            "attempted_count": self.attempted_count,
            "profiles": self.request.to_projection(),
            "facts": {
                "credential_acceptance": self.credential_acceptance.value,
                "expected_database_identity": self.expected_database_identity.value,
                "expected_account_identity": self.expected_account_identity.value,
                "required_grants": self.required_grants.value,
                "data_identity": self.data_identity.value,
                "data_continuity": self.data_continuity.value,
                "consumer_compatibility": self.consumer_compatibility.value,
            },
            "reason_codes": [self.reason_code.value],
            "retry_prohibited": True,
            "mutation_authority": False,
            "authorization_authority": False,
            "value_free": True,
            "secret_values_read": False,
        }


class MariaDBContinuityValidationService:
    """Pure delegating application service; it neither mints nor uses authority."""

    def __init__(self, port: "MariaDBContinuityValidationPort") -> None:
        if not callable(getattr(port, "validate_once", None)):
            raise TypeError("port must implement MariaDBContinuityValidationPort")
        self._port = port

    def validate_once(
        self, request: MariaDBContinuityValidationRequest, capability: object
    ) -> MariaDBContinuityValidationResult:
        if type(request) is not MariaDBContinuityValidationRequest:
            raise TypeError("request must be MariaDBContinuityValidationRequest")
        result = self._port.validate_once(request, capability)
        if type(result) is not MariaDBContinuityValidationResult:
            raise TypeError("port returned an invalid result type")
        return result
