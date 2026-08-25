"""Fail-closed contracts and policy for a future concrete continuity validator."""

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Protocol

from core.secrets.mariadb_continuity_sources import (
    ContinuityEvidenceCategory,
    DataIdentityCategory,
)
from core.secrets.mariadb_continuity_validation import (
    AccountProfile,
    ContinuityBaselineProfile,
    DatabaseProfile,
    DataIdentityProfile,
    GrantsProfile,
    TargetProfile,
    ValidationOutcome,
    ValidationProfile,
)


class BindingState(str, Enum):
    COMPLETE = "COMPLETE"
    MISSING_AUTHORITATIVE_VALUES = "MISSING_AUTHORITATIVE_VALUES"


class QueryPlanState(str, Enum):
    READY = "READY"
    MISSING_AUTHORITATIVE_SQL = "MISSING_AUTHORITATIVE_SQL"
    UNSAFE = "UNSAFE"


class ObservationFact(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    MISSING = "MISSING"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True, slots=True)
class ExpectedValidationBinding:
    """Serializable expectations only; credentials are deliberately impossible to store."""

    target: TargetProfile = field(default=TargetProfile.SHOPPING_SECRET_PROVISIONING, init=False)
    account: AccountProfile = field(default=AccountProfile.SHOPPING_MARIADB_HISTORICAL_ACCOUNT, init=False)
    database: DatabaseProfile = field(default=DatabaseProfile.SHOPPING_WORDPRESS_DATABASE, init=False)
    grants: GrantsProfile = field(default=GrantsProfile.SHOPPING_WORDPRESS_REQUIRED_GRANTS, init=False)
    data_identity: DataIdentityProfile = field(default=DataIdentityProfile.SHOPPING_WORDPRESS_DATA_IDENTITY, init=False)
    continuity: ContinuityBaselineProfile = field(default=ContinuityBaselineProfile.SM_01B_02D_05_HISTORICAL_CREDENTIAL, init=False)
    validation: ValidationProfile = field(default=ValidationProfile.MARIADB_HISTORICAL_CREDENTIAL_CONTINUITY_V1, init=False)
    data_categories: tuple[DataIdentityCategory, ...] = field(default_factory=lambda: tuple(DataIdentityCategory), init=False)
    lineage_categories: tuple[ContinuityEvidenceCategory, ...] = field(default_factory=lambda: tuple(ContinuityEvidenceCategory), init=False)
    state: BindingState = field(default=BindingState.MISSING_AUTHORITATIVE_VALUES, init=False)

    @property
    def ready(self) -> bool:
        return self.state is BindingState.COMPLETE


@dataclass(frozen=True, slots=True)
class FixedReadOnlyQueryPlan:
    """Repository-owned closed plan. Canonical WU08 state contains no guessed SQL."""

    statements: tuple[str, ...] = field(default=(), init=False, repr=False)
    state: QueryPlanState = field(default=QueryPlanState.MISSING_AUTHORITATIVE_SQL, init=False)

    @property
    def ready(self) -> bool:
        return self.state is QueryPlanState.READY and bool(self.statements)


_COMMENT = re.compile(r"(?:--|#|/\*)")
_READ_ONLY_HEAD = re.compile(r"^\s*(?:SELECT|SHOW)\b", re.IGNORECASE)
_FORBIDDEN = re.compile(
    r"\b(?:SET|CREATE|ALTER|DROP|INSERT|UPDATE|DELETE|REPLACE|GRANT|REVOKE|"
    r"FLUSH|LOCK|UNLOCK|CALL|LOAD|OUTFILE|INFILE|HANDLER|DO|EXECUTE|PREPARE)\b",
    re.IGNORECASE,
)


def is_safe_read_only_sql(statement: object) -> bool:
    """Conservatively accept one SELECT/SHOW statement and reject ambiguity."""

    if type(statement) is not str or not statement.strip():
        return False
    text = statement.strip()
    if _COMMENT.search(text) or _FORBIDDEN.search(text):
        return False
    if text.endswith(";"):
        text = text[:-1].rstrip()
    if ";" in text:
        return False
    return bool(_READ_ONLY_HEAD.match(text))


@dataclass(frozen=True, slots=True)
class SanitizedValidationObservation:
    credential_authentication: ObservationFact
    database_identity: ObservationFact
    account_identity: ObservationFact
    required_grants: ObservationFact
    data_identity: tuple[tuple[DataIdentityCategory, ObservationFact], ...]
    continuity_lineage: tuple[tuple[ContinuityEvidenceCategory, ObservationFact], ...]
    continuity_baseline: ObservationFact

    def __post_init__(self) -> None:
        scalars = (
            self.credential_authentication,
            self.database_identity,
            self.account_identity,
            self.required_grants,
            self.continuity_baseline,
        )
        if any(type(value) is not ObservationFact for value in scalars):
            raise TypeError("observation facts must use ObservationFact")


@dataclass(frozen=True, slots=True)
class ConcreteValidationResult:
    outcome: ValidationOutcome
    attempted_count: int
    reason: str

    def __post_init__(self) -> None:
        if type(self.outcome) is not ValidationOutcome:
            raise TypeError("outcome must use ValidationOutcome")
        if type(self.attempted_count) is not int or self.attempted_count not in (0, 1):
            raise ValueError("attempted_count must be zero or one")
        if type(self.reason) is not str or not self.reason:
            raise TypeError("reason must be sanitized text")

    def to_projection(self) -> dict[str, object]:
        return {"outcome": self.outcome.value, "attempted_count": self.attempted_count, "reason": self.reason}


class OneAttemptMariaDBDriver(Protocol):
    def observe_once(
        self,
        binding: ExpectedValidationBinding,
        plan: FixedReadOnlyQueryPlan,
        secret: object,
    ) -> SanitizedValidationObservation: ...


def canonical_expected_validation_binding() -> ExpectedValidationBinding:
    return ExpectedValidationBinding()


def canonical_fixed_read_only_query_plan() -> FixedReadOnlyQueryPlan:
    return FixedReadOnlyQueryPlan()


def _exact_group(
    group: object, categories: tuple[Enum, ...], category_type: type[Enum]
) -> tuple[ObservationFact, ...] | None:
    if type(group) is not tuple or len(group) != len(categories):
        return None
    found: dict[Enum, ObservationFact] = {}
    for item in group:
        if type(item) is not tuple or len(item) != 2:
            return None
        category, fact = item
        if type(category) is not category_type or type(fact) is not ObservationFact:
            return None
        if category not in categories or category in found:
            return None
        found[category] = fact
    return tuple(found[category] for category in categories) if set(found) == set(categories) else None


def decide_validation(observation: object, *, attempted_count: int = 1) -> ConcreteValidationResult:
    """Apply deterministic fail-closed precedence to already-sanitized facts."""

    if attempted_count != 1 or type(observation) is not SanitizedValidationObservation:
        return ConcreteValidationResult(ValidationOutcome.MALFORMED, 0, "MALFORMED_OBSERVATION")
    data = _exact_group(observation.data_identity, tuple(DataIdentityCategory), DataIdentityCategory)
    lineage = _exact_group(observation.continuity_lineage, tuple(ContinuityEvidenceCategory), ContinuityEvidenceCategory)
    if data is None or lineage is None:
        return ConcreteValidationResult(ValidationOutcome.MALFORMED, 1, "MALFORMED_OBSERVATION")
    facts = (
        observation.credential_authentication,
        observation.database_identity,
        observation.account_identity,
        observation.required_grants,
        *data,
        *lineage,
        observation.continuity_baseline,
    )
    if ObservationFact.AMBIGUOUS in facts or ObservationFact.MISSING in facts:
        return ConcreteValidationResult(ValidationOutcome.UNCERTAIN, 1, "INCOMPLETE_OR_AMBIGUOUS_FACTS")
    if ObservationFact.MISMATCH in facts:
        return ConcreteValidationResult(ValidationOutcome.REJECTED, 1, "FACT_MISMATCH")
    if all(fact is ObservationFact.MATCH for fact in facts):
        return ConcreteValidationResult(ValidationOutcome.VALIDATED, 1, "ALL_REQUIRED_FACTS_MATCH")
    return ConcreteValidationResult(ValidationOutcome.MALFORMED, 1, "MALFORMED_OBSERVATION")
