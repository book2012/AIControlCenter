"""Mac-only, injected one-attempt boundary prepared for future WU11 composition."""

from core.secrets.mariadb_continuity_concrete_validator import (
    ConcreteValidationResult,
    ExpectedValidationBinding,
    FixedReadOnlyQueryPlan,
    OneAttemptMariaDBDriver,
    QueryPlanState,
    decide_validation,
    is_safe_read_only_sql,
)
from core.secrets.mariadb_continuity_validation import ValidationOutcome


class MacPyMySQLContinuityValidatorAdapter:
    """Pass an opaque secret directly to one injected driver call and never retain it."""

    __slots__ = ("_driver",)

    def __init__(self, driver: OneAttemptMariaDBDriver) -> None:
        if not callable(getattr(driver, "observe_once", None)):
            raise TypeError("driver must provide observe_once")
        self._driver = driver

    def validate_once(
        self,
        binding: ExpectedValidationBinding,
        plan: FixedReadOnlyQueryPlan,
        secret: object,
    ) -> ConcreteValidationResult:
        if type(binding) is not ExpectedValidationBinding or type(plan) is not FixedReadOnlyQueryPlan:
            return ConcreteValidationResult(ValidationOutcome.MALFORMED, 0, "MALFORMED_INPUT")
        if not binding.ready or not plan.ready:
            return ConcreteValidationResult(ValidationOutcome.UNAVAILABLE, 0, "AUTHORITATIVE_BINDING_UNAVAILABLE")
        if plan.state is not QueryPlanState.READY or any(not is_safe_read_only_sql(sql) for sql in plan.statements):
            return ConcreteValidationResult(ValidationOutcome.UNSAFE, 0, "UNSAFE_QUERY_PLAN")
        try:
            observation = self._driver.observe_once(binding, plan, secret)
        except Exception:
            return ConcreteValidationResult(ValidationOutcome.UNCERTAIN, 1, "SANITIZED_DRIVER_FAILURE")
        return decide_validation(observation)
