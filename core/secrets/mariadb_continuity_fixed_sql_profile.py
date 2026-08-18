"""Closed operation profile for future validation, containing no SQL text."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


FIXED_SQL_TEXT_AVAILABLE = False
FIXED_SQL_TEXT_ALLOWED_NOW = False
ARBITRARY_SQL_ALLOWED = False


class FixedValidationCategory(str, Enum):
    CREDENTIAL_ACCEPTED = "CREDENTIAL_ACCEPTED"
    EXPECTED_DATABASE_IDENTITY = "EXPECTED_DATABASE_IDENTITY"
    EXPECTED_ACCOUNT_IDENTITY = "EXPECTED_ACCOUNT_IDENTITY"
    REQUIRED_GRANTS = "REQUIRED_GRANTS"
    EXPECTED_DATA_IDENTITY = "EXPECTED_DATA_IDENTITY"
    DECLARED_DATA_CONTINUITY = "DECLARED_DATA_CONTINUITY"


class FixedOperationProfile(str, Enum):
    CLOSED_MARIADB_CONTINUITY_VALIDATION = "CLOSED_MARIADB_CONTINUITY_VALIDATION"


@dataclass(frozen=True, slots=True)
class FixedSQLProfileContract:
    profile: FixedOperationProfile = field(
        default=FixedOperationProfile.CLOSED_MARIADB_CONTINUITY_VALIDATION,
        init=False,
    )
    validation_categories: tuple[FixedValidationCategory, ...] = field(
        default=tuple(FixedValidationCategory), init=False
    )
    fixed_sql_text_available: bool = field(default=False, init=False)
    fixed_sql_text_allowed_now: bool = field(default=False, init=False)
    arbitrary_sql_allowed: bool = field(default=False, init=False)
    authoritative_identity_grants_data_lineage_prerequisites_required: bool = field(default=True, init=False)

    def to_projection(self) -> dict[str, Any]:
        return {
            "profile": self.profile.value,
            "validation_categories": tuple(item.value for item in self.validation_categories),
            "fixed_sql_text_available": self.fixed_sql_text_available,
            "fixed_sql_text_allowed_now": self.fixed_sql_text_allowed_now,
            "arbitrary_sql_allowed": self.arbitrary_sql_allowed,
            "authoritative_identity_grants_data_lineage_prerequisites_required": self.authoritative_identity_grants_data_lineage_prerequisites_required,
            "authorization_authority": False,
            "capability_authority": False,
            "execution_authority": False,
            "mutation_authority": False,
            "retry_authority": False,
            "reconnect_authority": False,
            "rollback_authority": False,
            "value_free": True,
        }


def canonical_fixed_sql_profile() -> FixedSQLProfileContract:
    return FixedSQLProfileContract()
