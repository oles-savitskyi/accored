from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from accore.platform.foundation.identity import Identifier

from .context import SecurityContext
from .credentials import PasswordCredentials
from .principal import Principal
from .role import Role
from .session import Session
from .user import User


@dataclass(frozen=True, slots=True)
class PasswordVerifier:
    """Opaque persisted one-way password verifier representation."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Password verifier value must be non-empty")


@dataclass(frozen=True, slots=True)
class AuthenticationResult:
    """Successful authentication result."""

    principal: Principal
    session: Session | None


class AuthenticationProvider(Protocol):
    def authenticate(self, credentials: PasswordCredentials) -> AuthenticationResult: ...


class UserRepository(Protocol):
    def find_by_login(self, login: str) -> User | None: ...

    def get(self, identity: Identifier) -> User: ...


class CredentialRepository(Protocol):
    def get_password_verifier(self, user_identity: Identifier) -> PasswordVerifier: ...


class RoleRepository(Protocol):
    def get(self, identity: Identifier) -> Role: ...


class SessionStore(Protocol):
    def create(self, principal: Principal, now: datetime) -> Session: ...

    def get(self, identity: Identifier) -> Session | None: ...

    def invalidate(self, identity: Identifier) -> None: ...


class SecurityContextFactory(Protocol):
    def from_authentication(
        self,
        result: AuthenticationResult,
        request_identity: Identifier | None = None,
    ) -> SecurityContext: ...


@dataclass(frozen=True, slots=True)
class DefaultSecurityContextFactory:
    """Construct an immutable security context from authentication state."""

    def from_authentication(
        self,
        result: AuthenticationResult,
        request_identity: Identifier | None = None,
    ) -> SecurityContext:
        return SecurityContext(
            principal=result.principal,
            session=result.session,
            request_identity=request_identity,
        )
