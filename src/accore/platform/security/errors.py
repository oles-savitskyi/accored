from __future__ import annotations

from typing import TYPE_CHECKING

from accore.platform.foundation.errors import AcCoreError

if TYPE_CHECKING:
    from .authorization import AuthorizationDecision


class SecurityError(AcCoreError):
    """Base security error."""


class AuthenticationError(SecurityError):
    """Base authentication error."""


class AuthenticationFailedError(AuthenticationError):
    """Credentials or identity verification failed."""


class AuthenticationConfigurationError(AuthenticationError):
    """Authentication configuration is invalid or unavailable."""


class AuthorizationDeniedError(SecurityError):
    """A protected operation was denied."""

    def __init__(self, decision: AuthorizationDecision) -> None:
        self.decision = decision

        if decision.reason is None:
            raise ValueError("AuthorizationDeniedError requires a denied decision.")

        super().__init__(f"Authorization denied: {decision.reason.value}")


class SecurityInfrastructureError(SecurityError):
    """Authoritative security state cannot be evaluated safely."""


class SecurityConfigurationError(SecurityError):
    """Security configuration is invalid or inconsistent."""
