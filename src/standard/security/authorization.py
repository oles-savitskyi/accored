from __future__ import annotations

from dataclasses import dataclass, field

from accore.platform.foundation.identity import Identifier
from accore.platform.security import (
    Principal,
    Role,
    SecurityAuthorizationState,
    User,
)
from accore.platform.security.authentication import RoleRepository, UserRepository
from accore.platform.security.errors import SecurityConfigurationError


@dataclass(slots=True)
class InMemoryRoleRepository:
    """In-memory Standard role repository for the authorization MVP."""

    roles: tuple[Role, ...]
    _by_identity: dict[Identifier, Role] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._by_identity = {}
        for role in self.roles:
            if role.identity in self._by_identity:
                raise SecurityConfigurationError(f"Duplicate role identity: {role.identity}")
            self._by_identity[role.identity] = role

    def get(self, identity: Identifier) -> Role:
        try:
            return self._by_identity[identity]
        except KeyError as exc:
            raise SecurityConfigurationError(f"Unknown role identity: {identity}") from exc


@dataclass(frozen=True, slots=True)
class StandardSecurityAuthorizationState(SecurityAuthorizationState):
    """Adapter from Standard security repositories to the Platform state boundary."""

    users: UserRepository
    roles: RoleRepository

    def user_for_principal(self, principal: Principal) -> User:
        return self.users.get(principal.identity)

    def role(self, identity: Identifier) -> Role:
        return self.roles.get(identity)


__all__ = [
    "InMemoryRoleRepository",
    "StandardSecurityAuthorizationState",
]
