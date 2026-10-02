from __future__ import annotations

from datetime import UTC, datetime

import pytest

from accore.platform.foundation.identity import Identifier
from accore.platform.security import (
    Permission,
    Principal,
    PrincipalType,
    Role,
    SecurityClaim,
    SecurityContext,
    SecurityObjectIdentity,
    SecurityOperation,
    Session,
    SessionState,
    User,
)


def test_user_normalizes_role_ids_and_contains_no_credentials() -> None:
    user = User(
        identity=Identifier.new(),
        login="alice",
        display_name="Alice",
        email=None,
        active=True,
        role_ids=[Identifier.new()],
    )

    assert isinstance(user.role_ids, tuple)
    assert not hasattr(user, "password")


def test_user_rejects_empty_login() -> None:
    with pytest.raises(ValueError, match="login"):
        User(
            identity=Identifier.new(),
            login="",
            display_name="Alice",
            email=None,
            active=True,
            role_ids=(),
        )


def test_principal_is_runtime_identity_and_claims_are_immutable() -> None:
    claim = SecurityClaim("department", "inventory")
    principal = Principal(Identifier.new(), PrincipalType.USER, [claim])

    assert principal.identity_type is PrincipalType.USER
    assert principal.claims == (claim,)
    assert isinstance(principal.claims, tuple)


def test_security_context_does_not_contain_credentials_or_permissions() -> None:
    principal = Principal(Identifier.new(), PrincipalType.USER)
    context = SecurityContext(principal=principal, session=None)

    assert context.principal is principal
    assert not hasattr(context, "password")
    assert not hasattr(context, "permissions")


def test_session_is_separate_from_principal() -> None:
    principal_identity = Identifier.new()
    session = Session(
        identity=Identifier.new(),
        principal_identity=principal_identity,
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC),
        state=SessionState.ACTIVE,
    )

    assert session.principal_identity == principal_identity
    assert session.state is SessionState.ACTIVE


def test_security_object_identity_requires_type_and_code() -> None:
    with pytest.raises(ValueError, match="type"):
        SecurityObjectIdentity("", "inventory.rebuild")
    with pytest.raises(ValueError, match="code"):
        SecurityObjectIdentity("Processing", "")


def test_permission_uses_exact_target_and_operation() -> None:
    target = SecurityObjectIdentity("Processing", "inventory.rebuild")
    permission = Permission(Identifier.new(), target, SecurityOperation.EXECUTE)

    assert permission.target == target
    assert permission.operation is SecurityOperation.EXECUTE
    assert permission.constraints == ()


def test_role_normalizes_permissions_and_has_no_inheritance() -> None:
    target = SecurityObjectIdentity("Processing", "inventory.rebuild")
    permission = Permission(Identifier.new(), target, SecurityOperation.EXECUTE)
    role = Role(Identifier.new(), "operator", "Operator", [permission])

    assert role.permissions == (permission,)
    assert not hasattr(role, "parent")


def test_role_rejects_empty_code() -> None:
    with pytest.raises(ValueError, match="code"):
        Role(Identifier.new(), "", "Operator", ())


def test_security_operation_values_are_platform_defined() -> None:
    assert SecurityOperation.READ.value == "read"
    assert SecurityOperation.EXECUTE.value == "execute"
    assert SecurityOperation.ADMINISTER.value == "administer"
