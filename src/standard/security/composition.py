from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from accore.platform.security import (
    AuthenticationProvider,
    AuthorizationService,
    DefaultAuthorizationService,
    DefaultSecurityContextFactory,
    SecurityContextFactory,
)
from accore.platform.security.authentication import (
    RoleRepository,
    UserRepository,
)
from accore.platform.security.errors import SecurityConfigurationError
from accore.platform.security.role import Role
from accore.platform.security.user import User

from .authentication import LocalAuthenticationProvider, StandardPasswordHasher
from .authorization import InMemoryRoleRepository, StandardSecurityAuthorizationState
from .definitions import _standard_security_definitions
from .persistence import (
    InMemoryCredentialRepository,
    InMemorySessionStore,
    InMemoryUserRepository,
)


@dataclass(frozen=True, slots=True)
class StandardSecurityComposition:
    """Composed Standard authentication, authorization, and context services."""

    authentication: AuthenticationProvider
    authorization: AuthorizationService
    context_factory: SecurityContextFactory


def compose_standard_security(
    *,
    initial_passwords: Mapping[str, str],
    password_hasher: StandardPasswordHasher | None = None,
) -> StandardSecurityComposition:
    """Compose the complete Standard MVP security boundary."""
    hasher = password_hasher or StandardPasswordHasher()
    definitions = _standard_security_definitions(
        password_hasher=hasher,
        initial_passwords=initial_passwords,
    )

    users: UserRepository = InMemoryUserRepository(definitions.users)
    roles: RoleRepository = InMemoryRoleRepository(definitions.roles)
    credentials = InMemoryCredentialRepository(definitions.credentials)
    sessions = InMemorySessionStore()

    state = StandardSecurityAuthorizationState(users=users, roles=roles)
    authorization = DefaultAuthorizationService(state=state)
    authentication = LocalAuthenticationProvider(
        users=users,
        credentials=credentials,
        sessions=sessions,
        password_hasher=hasher,
    )
    context_factory = DefaultSecurityContextFactory()

    _validate_composition(definitions.users, definitions.roles)
    return StandardSecurityComposition(
        authentication=authentication,
        authorization=authorization,
        context_factory=context_factory,
    )


def _validate_composition(users: tuple[User, ...], roles: tuple[Role, ...]) -> None:
    role_ids = {role.identity for role in roles}
    for user in users:
        missing = set(user.role_ids) - role_ids
        if missing:
            raise SecurityConfigurationError(
                f"User {user.identity} references unknown roles: {sorted(map(str, missing))!r}"
            )
