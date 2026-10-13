from __future__ import annotations

from enum import StrEnum

from accore.platform.foundation.errors import AcCoreError


class IntegrationErrorCategory(StrEnum):
    """Stable categories used to map Integration failures at external boundaries."""

    CONTRACT = "contract"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    EXECUTION = "execution"
    CONFLICT = "conflict"
    INTERNAL = "internal"


class IntegrationError(AcCoreError):
    """Base class for errors exposed by the Integration boundary."""

    def __init__(
        self,
        message: str,
        *,
        category: IntegrationErrorCategory = IntegrationErrorCategory.INTERNAL,
    ) -> None:
        super().__init__(message)
        self.category = category


class IntegrationContractNotFoundError(IntegrationError):
    """Raised when an Integration contract identity cannot be resolved."""

    def __init__(self, message: str) -> None:
        super().__init__(message, category=IntegrationErrorCategory.CONTRACT)


class IntegrationContractVersionError(IntegrationError):
    """Raised when a requested contract version is unsupported."""

    def __init__(self, message: str) -> None:
        super().__init__(message, category=IntegrationErrorCategory.CONTRACT)


class IntegrationContractValidationError(IntegrationError, ValueError):
    """Raised when contract metadata violates Integration invariants."""

    def __init__(self, message: str) -> None:
        super().__init__(message, category=IntegrationErrorCategory.VALIDATION)


class IntegrationRequestValidationError(IntegrationError, ValueError):
    """Raised when a request does not satisfy Integration boundary requirements."""

    def __init__(self, message: str) -> None:
        super().__init__(message, category=IntegrationErrorCategory.VALIDATION)


class IntegrationMalformedRequestError(IntegrationRequestValidationError):
    """Raised when an incoming request cannot be interpreted as a valid request."""


class IntegrationAuthenticationError(IntegrationError):
    """External Integration representation of an authentication failure."""

    def __init__(self, message: str) -> None:
        super().__init__(message, category=IntegrationErrorCategory.AUTHENTICATION)


class IntegrationAuthorizationError(IntegrationError):
    """External representation of a Phase 11 authorization denial."""

    def __init__(self, message: str) -> None:
        super().__init__(message, category=IntegrationErrorCategory.AUTHORIZATION)


class IntegrationExecutionError(IntegrationError):
    """Raised when an operation fails during execution."""

    def __init__(self, message: str) -> None:
        super().__init__(message, category=IntegrationErrorCategory.EXECUTION)


class IntegrationInternalError(IntegrationError):
    """Sanitized representation of an unexpected internal failure."""

    def __init__(self, message: str) -> None:
        super().__init__(message, category=IntegrationErrorCategory.INTERNAL)


class IntegrationConflictError(IntegrationError):
    """Raised when a request conflicts with existing Integration state."""

    def __init__(self, message: str) -> None:
        super().__init__(message, category=IntegrationErrorCategory.CONFLICT)
