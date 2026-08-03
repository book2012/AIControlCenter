"""Secret-safe typed failures for the controlled live boundary."""


class CommerceLiveBoundaryError(RuntimeError):
    reason_code = "commerce_live_boundary_error"

    def __init__(self, reason_code: str | None = None) -> None:
        self.reason_code = reason_code or self.reason_code
        super().__init__(self.reason_code)


class CredentialUnavailableError(CommerceLiveBoundaryError):
    reason_code = "credential_unavailable"


class TransportUnavailableError(CommerceLiveBoundaryError):
    reason_code = "transport_unavailable"


class ReconciliationError(CommerceLiveBoundaryError):
    reason_code = "response_invalid"


class ControlledPlanRejectedError(CommerceLiveBoundaryError):
    reason_code = "controlled_plan_rejected"
