from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from accore.platform.foundation.identity import Identifier

from .context import SecurityContext
from .errors import AuthorizationDeniedError, SecurityConfigurationError
from .object import SecurityObjectIdentity
from .operation import SecurityOperation
from .principal import Principal, PrincipalType
from .role import Role
from .user import User


class AuthorizationOutcome(StrEnum):
    ALLOW = "allow"
    DENY = "deny"


class AuthorizationDenyReason(StrEnum):
    UNAUTHENTICATED = "unauthenticated"
    INACTIVE_PRINCIPAL = "inactive_principal"
    MISSING_PERMISSION = "missing_permission"
    CONSTRAINT_FAILED = "constraint_failed"


class AuthorizationResource(Protocol):
    @property
    def identity(self) -> Identifier: ...


@dataclass(frozen=True, slots=True)
class AuthorizationRequest:
    context: SecurityContext
    target: SecurityObjectIdentity
    operation: SecurityOperation
    resource: AuthorizationResource | None = None


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    outcome: AuthorizationOutcome
    reason: AuthorizationDenyReason | None

    def __post_init__(self) -> None:
        if self.outcome is AuthorizationOutcome.ALLOW and self.reason is not None:
            raise ValueError("Allowed authorization decision must not have a deny reason")
        if self.outcome is AuthorizationOutcome.DENY and self.reason is None:
            raise ValueError("Denied authorization decision must have a deny reason")


class SecurityAuthorizationState(Protocol):
    def user_for_principal(self, principal: Principal) -> User: ...

    def role(self, identity: Identifier) -> Role: ...


class AuthorizationService(Protocol):
    def authorize(self, request: AuthorizationRequest) -> AuthorizationDecision: ...

    def require(self, request: AuthorizationRequest) -> None: ...


@dataclass(frozen=True, slots=True)
class DefaultAuthorizationService:
    state: SecurityAuthorizationState

    def authorize(self, request: AuthorizationRequest) -> AuthorizationDecision:
        principal = request.context.principal
        if principal is None:
            return AuthorizationDecision(
                outcome=AuthorizationOutcome.DENY,
                reason=AuthorizationDenyReason.UNAUTHENTICATED,
            )

        if principal.identity_type is not PrincipalType.USER:
            raise SecurityConfigurationError(
                f"Unsupported principal type for authorization: {principal.identity_type.value}"
            )

        user = self.state.user_for_principal(principal)
        if not user.active:
            return AuthorizationDecision(
                outcome=AuthorizationOutcome.DENY,
                reason=AuthorizationDenyReason.INACTIVE_PRINCIPAL,
            )

        roles = tuple(self.state.role(role_identity) for role_identity in user.role_ids)
        permissions = tuple(
            permission
            for role in roles
            for permission in role.permissions
            if permission.target == request.target and permission.operation is request.operation
        )

        if not permissions:
            return AuthorizationDecision(
                outcome=AuthorizationOutcome.DENY,
                reason=AuthorizationDenyReason.MISSING_PERMISSION,
            )

        if any(
            all(constraint.evaluate(request) for constraint in permission.constraints)
            for permission in permissions
        ):
            return AuthorizationDecision(
                outcome=AuthorizationOutcome.ALLOW,
                reason=None,
            )

        return AuthorizationDecision(
            outcome=AuthorizationOutcome.DENY,
            reason=AuthorizationDenyReason.CONSTRAINT_FAILED,
        )

    def require(self, request: AuthorizationRequest) -> None:
        decision = self.authorize(request)
        if decision.outcome is AuthorizationOutcome.DENY:
            raise AuthorizationDeniedError(decision)
