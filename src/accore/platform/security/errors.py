from __future__ import annotations

from accore.platform.foundation.errors import AcCoreError


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


class SecurityInfrastructureError(SecurityError):
    """Authoritative security state cannot be evaluated safely."""


class SecurityConfigurationError(SecurityError):
    """Security configuration is invalid or inconsistent."""
