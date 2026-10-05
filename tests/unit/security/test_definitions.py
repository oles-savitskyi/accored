from __future__ import annotations

from accore.platform.security import SecurityOperation
from standard.security.definitions import (
    PROCESSING_INVENTORY_REBUILD,
    REPORT_INVENTORY_BALANCE,
    STANDARD_ADMINISTRATOR_ROLE,
    STANDARD_AUDITOR_ROLE,
    STANDARD_OPERATOR_ROLE,
    SYSTEM_SECURITY,
    standard_security_roles,
    standard_security_users,
)


def test_standard_roles_define_expected_permissions() -> None:
    roles = standard_security_roles()

    assert tuple(role.code for role in roles) == (
        STANDARD_ADMINISTRATOR_ROLE,
        STANDARD_OPERATOR_ROLE,
        STANDARD_AUDITOR_ROLE,
    )

    administrator, operator, auditor = roles
    assert {
        (permission.target, permission.operation) for permission in administrator.permissions
    } == {
        (PROCESSING_INVENTORY_REBUILD, SecurityOperation.EXECUTE),
        (REPORT_INVENTORY_BALANCE, SecurityOperation.READ),
        (SYSTEM_SECURITY, SecurityOperation.ADMINISTER),
    }
    assert operator.permissions[0].target == PROCESSING_INVENTORY_REBUILD
    assert auditor.permissions[0].target == REPORT_INVENTORY_BALANCE


def test_standard_users_reference_supplied_role_identities() -> None:
    roles = standard_security_roles()
    users = standard_security_users(
        administrator_role_id=roles[0].identity,
        operator_role_id=roles[1].identity,
        auditor_role_id=roles[2].identity,
    )

    assert tuple(user.login for user in users) == (
        "administrator",
        "operator",
        "auditor",
    )
    assert tuple(user.role_ids for user in users) == tuple((role.identity,) for role in roles)
