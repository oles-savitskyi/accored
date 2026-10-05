from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from accore.platform.foundation.identity import Identifier
from accore.platform.security import (
    Permission,
    Role,
    SecurityObjectIdentity,
    SecurityOperation,
    User,
)

from .authentication import StandardPasswordHasher
from .persistence import StandardCredential

STANDARD_ADMINISTRATOR_ROLE = "standard.administrator"
STANDARD_OPERATOR_ROLE = "standard.operator"
STANDARD_AUDITOR_ROLE = "standard.auditor"

PROCESSING_INVENTORY_REBUILD = SecurityObjectIdentity(
    object_type="processing",
    object_code="inventory.rebuild",
)
REPORT_INVENTORY_BALANCE = SecurityObjectIdentity(
    object_type="report",
    object_code="inventory.balance",
)
SYSTEM_SECURITY = SecurityObjectIdentity(
    object_type="system",
    object_code="security",
)


@dataclass(frozen=True, slots=True)
class _StandardSecurityDefinitions:
    users: tuple[User, ...]
    roles: tuple[Role, ...]
    credentials: tuple[StandardCredential, ...]


def _permission(target: SecurityObjectIdentity, operation: SecurityOperation) -> Permission:
    return Permission(identity=Identifier.new(), target=target, operation=operation)


def _build_roles() -> tuple[Role, ...]:
    processing_execute = _permission(PROCESSING_INVENTORY_REBUILD, SecurityOperation.EXECUTE)
    report_read = _permission(REPORT_INVENTORY_BALANCE, SecurityOperation.READ)
    security_administer = _permission(SYSTEM_SECURITY, SecurityOperation.ADMINISTER)

    administrator = Role(
        identity=Identifier.new(),
        code=STANDARD_ADMINISTRATOR_ROLE,
        name="Standard Administrator",
        permissions=(processing_execute, report_read, security_administer),
    )
    operator = Role(
        identity=Identifier.new(),
        code=STANDARD_OPERATOR_ROLE,
        name="Standard Operator",
        permissions=(processing_execute,),
    )
    auditor = Role(
        identity=Identifier.new(),
        code=STANDARD_AUDITOR_ROLE,
        name="Standard Auditor",
        permissions=(report_read,),
    )
    return (administrator, operator, auditor)


def standard_security_roles() -> tuple[Role, ...]:
    """Return the immutable Standard MVP role definitions."""
    return _build_roles()


def standard_security_users(
    *,
    administrator_role_id: Identifier,
    operator_role_id: Identifier,
    auditor_role_id: Identifier,
) -> tuple[User, ...]:
    """Create representative Standard users for one coherent role definition set."""
    return (
        User(
            identity=Identifier.new(),
            login="administrator",
            display_name="Standard Administrator",
            email=None,
            active=True,
            role_ids=(administrator_role_id,),
        ),
        User(
            identity=Identifier.new(),
            login="operator",
            display_name="Standard Operator",
            email=None,
            active=True,
            role_ids=(operator_role_id,),
        ),
        User(
            identity=Identifier.new(),
            login="auditor",
            display_name="Standard Auditor",
            email=None,
            active=True,
            role_ids=(auditor_role_id,),
        ),
    )


def standard_security_credentials(
    *,
    users: tuple[User, ...],
    password_hasher: StandardPasswordHasher,
    initial_passwords: Mapping[str, str],
) -> tuple[StandardCredential, ...]:
    """Create immutable credential values from explicit bootstrap passwords."""
    expected_logins = {user.login for user in users}
    supplied_logins = set(initial_passwords)
    missing = expected_logins - supplied_logins
    unknown = supplied_logins - expected_logins
    if missing or unknown:
        raise ValueError(
            "Initial passwords must contain exactly the Standard user logins; "
            f"missing={sorted(missing)!r}, unknown={sorted(unknown)!r}"
        )

    return tuple(
        StandardCredential(
            user_identity=user.identity,
            verifier=password_hasher.hash(initial_passwords[user.login]),
        )
        for user in users
    )


def _standard_security_definitions(
    *,
    password_hasher: StandardPasswordHasher,
    initial_passwords: Mapping[str, str],
) -> _StandardSecurityDefinitions:
    roles = standard_security_roles()
    roles_by_code = {role.code: role for role in roles}
    users = standard_security_users(
        administrator_role_id=roles_by_code[STANDARD_ADMINISTRATOR_ROLE].identity,
        operator_role_id=roles_by_code[STANDARD_OPERATOR_ROLE].identity,
        auditor_role_id=roles_by_code[STANDARD_AUDITOR_ROLE].identity,
    )
    credentials = standard_security_credentials(
        users=users,
        password_hasher=password_hasher,
        initial_passwords=initial_passwords,
    )
    return _StandardSecurityDefinitions(users=users, roles=roles, credentials=credentials)
