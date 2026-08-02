"""Typed ProductDraft domain failures."""


class ProductDraftError(ValueError):
    """Base class for invalid domain input."""


class InvalidTransitionError(ProductDraftError):
    pass


class RepositoryError(ProductDraftError):
    pass


class DuplicateRevisionError(RepositoryError):
    pass


class RevisionSequenceError(RepositoryError):
    pass


class RevisionChainError(RepositoryError):
    pass
