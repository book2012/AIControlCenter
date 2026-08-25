"""Pure, value-free evaluation of repository-constructed historical facts."""

from dataclasses import dataclass, field, fields
from enum import Enum

from core.secrets.mariadb_continuity_descriptors import RecoverEvidenceGate
from core.secrets.mariadb_continuity_evidence_acquisition_descriptor import (
    EvidenceAcquisitionCategory,
)
from core.secrets.mariadb_continuity_sources import (
    ContinuityEvidenceCategory,
    DataIdentityCategory,
)


REQUIRED_EVIDENCE_ACQUISITION_CATEGORIES = (
    EvidenceAcquisitionCategory.AUTH_PLUGIN_AUTHORITATIVE_EVIDENCE,
    EvidenceAcquisitionCategory.PYMYSQL_1_2_0_COMPATIBILITY_EVIDENCE,
    EvidenceAcquisitionCategory.EXPECTED_DATABASE_IDENTITY,
    EvidenceAcquisitionCategory.EXPECTED_ACCOUNT_IDENTITY,
    EvidenceAcquisitionCategory.REQUIRED_GRANTS,
    EvidenceAcquisitionCategory.ACCOUNT_BINDING,
    EvidenceAcquisitionCategory.BASELINE_BINDING,
    EvidenceAcquisitionCategory.TIMESTAMP_EVIDENCE,
    EvidenceAcquisitionCategory.IMMUTABLE_INTEGRITY_BINDING,
    EvidenceAcquisitionCategory.TRUSTED_ISSUER,
)
REQUIRED_DATA_IDENTITY_CATEGORIES = (
    DataIdentityCategory.WORDPRESS_IDENTITY,
    DataIdentityCategory.SITE_IDENTITY,
    DataIdentityCategory.APPLICATION_IDENTITY,
    DataIdentityCategory.CLOSED_SCHEMA_CHARACTERISTICS,
    DataIdentityCategory.CLOSED_TABLE_CHARACTERISTICS,
)
REQUIRED_CONTINUITY_EVIDENCE_CATEGORIES = (
    ContinuityEvidenceCategory.LOGICAL_EXPORT,
    ContinuityEvidenceCategory.RECOVERY_ARTIFACT,
    ContinuityEvidenceCategory.PERSISTENT_VOLUME_SNAPSHOT,
)


class HistoricalEvidenceFactState(str, Enum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"
    UNAVAILABLE = "UNAVAILABLE"
    UNSAFE = "UNSAFE"
    AMBIGUOUS = "AMBIGUOUS"


class OfflineHistoricalEvidenceClassification(str, Enum):
    EVIDENCE_COMPLETE = "EVIDENCE_COMPLETE"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    EVIDENCE_UNAVAILABLE = "EVIDENCE_UNAVAILABLE"
    EVIDENCE_UNSAFE = "EVIDENCE_UNSAFE"
    EVIDENCE_UNCERTAIN = "EVIDENCE_UNCERTAIN"


@dataclass(frozen=True, slots=True, init=False)
class HistoricalEvidenceDimensionFact:
    category: EvidenceAcquisitionCategory
    state: HistoricalEvidenceFactState

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("historical evidence facts are repository-constructed")


@dataclass(frozen=True, slots=True, init=False)
class DataIdentityEvidenceFact:
    category: DataIdentityCategory
    state: HistoricalEvidenceFactState

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("data identity facts are repository-constructed")


@dataclass(frozen=True, slots=True, init=False)
class ContinuityLineageEvidenceFact:
    category: ContinuityEvidenceCategory
    state: HistoricalEvidenceFactState

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("continuity lineage facts are repository-constructed")


@dataclass(frozen=True, slots=True, init=False)
class HistoricalEvidenceFact:
    """Repository-only factual input; neither a security boundary nor authority."""

    dimensions: tuple[HistoricalEvidenceDimensionFact, ...]
    data_identities: tuple[DataIdentityEvidenceFact, ...]
    continuity_lineage: tuple[ContinuityLineageEvidenceFact, ...]
    provenance_valid: bool

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("historical evidence collections are repository-constructed")


@dataclass(frozen=True, slots=True, init=False)
class OfflineEvaluation:
    classification: OfflineHistoricalEvidenceClassification
    recover_evidence_sufficient: bool = field(default=False, init=False)
    recover_evidence_gate: RecoverEvidenceGate = field(
        default=RecoverEvidenceGate.RECOVER_EVIDENCE_INSUFFICIENT, init=False
    )
    authorization: bool = field(default=False, init=False)
    authority: bool = field(default=False, init=False)
    capability: bool = field(default=False, init=False)
    production_access: bool = field(default=False, init=False)
    credential_validation: bool = field(default=False, init=False)
    controlled_execution_port_coupled: bool = field(default=False, init=False)
    mac_control_plane: bool = field(default=True, init=False)
    ubuntu_role: bool = field(default=False, init=False)
    mutation_budget: int = field(default=0, init=False)

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("offline evaluations are repository-constructed")


def _construct_fact(fact_type: type, category: Enum, state: HistoricalEvidenceFactState):
    """Repository-private synthetic factual plumbing; not a trust boundary."""
    expected = {
        HistoricalEvidenceDimensionFact: EvidenceAcquisitionCategory,
        DataIdentityEvidenceFact: DataIdentityCategory,
        ContinuityLineageEvidenceFact: ContinuityEvidenceCategory,
    }
    if fact_type not in expected or type(category) is not expected[fact_type]:
        raise TypeError("fact category has the wrong exact type")
    if type(state) is not HistoricalEvidenceFactState:
        raise TypeError("fact state has the wrong exact type")
    fact = object.__new__(fact_type)
    object.__setattr__(fact, "category", category)
    object.__setattr__(fact, "state", state)
    return fact


def _construct_historical_evidence_fact(
    dimensions: tuple[HistoricalEvidenceDimensionFact, ...],
    data_identities: tuple[DataIdentityEvidenceFact, ...],
    continuity_lineage: tuple[ContinuityLineageEvidenceFact, ...],
    provenance_valid: bool,
) -> HistoricalEvidenceFact:
    """Repository/testing plumbing only; not a security boundary or provenance proof."""
    groups = (
        (dimensions, HistoricalEvidenceDimensionFact),
        (data_identities, DataIdentityEvidenceFact),
        (continuity_lineage, ContinuityLineageEvidenceFact),
    )
    if any(type(group) is not tuple or any(type(item) is not kind for item in group) for group, kind in groups):
        raise TypeError("historical evidence groups require exact repository fact types")
    if type(provenance_valid) is not bool:
        raise TypeError("provenance_valid must be an exact repository factual boolean")
    facts = object.__new__(HistoricalEvidenceFact)
    object.__setattr__(facts, "dimensions", dimensions)
    object.__setattr__(facts, "data_identities", data_identities)
    object.__setattr__(facts, "continuity_lineage", continuity_lineage)
    object.__setattr__(facts, "provenance_valid", provenance_valid)
    return facts


def _construct_evaluation(
    classification: OfflineHistoricalEvidenceClassification,
) -> OfflineEvaluation:
    if type(classification) is not OfflineHistoricalEvidenceClassification:
        raise TypeError("classification has the wrong exact type")
    result = object.__new__(OfflineEvaluation)
    object.__setattr__(result, "classification", classification)
    for item in fields(OfflineEvaluation):
        if item.name != "classification":
            object.__setattr__(result, item.name, item.default)
    return result


def _states(
    facts: object,
    fact_type: type,
    category_type: type[Enum],
    required_categories: tuple[Enum, ...],
) -> tuple[HistoricalEvidenceFactState, ...] | None:
    if type(facts) is not tuple:
        return None
    observed: dict[Enum, HistoricalEvidenceFactState] = {}
    for fact in facts:
        if type(fact) is not fact_type:
            return None
        category, state = fact.category, fact.state
        if type(category) is not category_type or type(state) is not HistoricalEvidenceFactState:
            return None
        if category not in required_categories or category in observed:
            return None
        observed[category] = state
    return tuple(observed.get(category, HistoricalEvidenceFactState.MISSING) for category in required_categories)


def evaluate_offline_historical_evidence(facts: object) -> OfflineEvaluation:
    """Deterministically classify facts without acquiring or acting on evidence."""
    if type(facts) is not HistoricalEvidenceFact:
        return _construct_evaluation(OfflineHistoricalEvidenceClassification.EVIDENCE_UNCERTAIN)
    if type(getattr(facts, "provenance_valid", None)) is not bool:
        return _construct_evaluation(OfflineHistoricalEvidenceClassification.EVIDENCE_UNCERTAIN)
    groups = (
        _states(facts.dimensions, HistoricalEvidenceDimensionFact, EvidenceAcquisitionCategory, REQUIRED_EVIDENCE_ACQUISITION_CATEGORIES),
        _states(facts.data_identities, DataIdentityEvidenceFact, DataIdentityCategory, REQUIRED_DATA_IDENTITY_CATEGORIES),
        _states(facts.continuity_lineage, ContinuityLineageEvidenceFact, ContinuityEvidenceCategory, REQUIRED_CONTINUITY_EVIDENCE_CATEGORIES),
    )
    if any(group is None for group in groups):
        return _construct_evaluation(OfflineHistoricalEvidenceClassification.EVIDENCE_UNCERTAIN)
    states = tuple(state for group in groups for state in group)  # type: ignore[union-attr]
    if HistoricalEvidenceFactState.AMBIGUOUS in states:
        classification = OfflineHistoricalEvidenceClassification.EVIDENCE_UNCERTAIN
    elif HistoricalEvidenceFactState.UNSAFE in states:
        classification = OfflineHistoricalEvidenceClassification.EVIDENCE_UNSAFE
    elif HistoricalEvidenceFactState.UNAVAILABLE in states:
        classification = OfflineHistoricalEvidenceClassification.EVIDENCE_UNAVAILABLE
    elif HistoricalEvidenceFactState.MISSING in states or not facts.provenance_valid:
        classification = OfflineHistoricalEvidenceClassification.EVIDENCE_INCOMPLETE
    else:
        classification = OfflineHistoricalEvidenceClassification.EVIDENCE_COMPLETE
    return _construct_evaluation(classification)
