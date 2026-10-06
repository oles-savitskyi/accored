from __future__ import annotations

import pytest

from accore.platform.security import (
    AuthorizationDenyReason,
    AuthorizationRequest,
    PasswordCredentials,
    SecurityObjectIdentity,
    SecurityOperation,
)
from accore.platform.security.errors import AuthenticationFailedError
from standard.security import compose_standard_security

_PASSWORDS = {
    "administrator": "administrator-test-password",
    "operator": "operator-test-password",
    "auditor": "auditor-test-password",
}


def test_compose_standard_security_exposes_all_three_boundaries() -> None:
    security = compose_standard_security(initial_passwords=_PASSWORDS)

    assert security.authentication is not None
    assert security.authorization is not None
    assert security.context_factory is not None


def test_operator_authentication_produces_user_context() -> None:
    security = compose_standard_security(initial_passwords=_PASSWORDS)

    result = security.authentication.authenticate(
        PasswordCredentials(login="operator", password=_PASSWORDS["operator"])
    )
    context = security.context_factory.from_authentication(result)

    assert result.principal.identity_type.value == "user"
    assert result.session is not None
    assert result.principal.identity == result.session.principal_identity
    assert context.principal is result.principal
    assert context.session is result.session


def test_administrator_receives_all_standard_permissions() -> None:
    security = compose_standard_security(initial_passwords=_PASSWORDS)
    result = security.authentication.authenticate(
        PasswordCredentials(login="administrator", password=_PASSWORDS["administrator"])
    )
    context = security.context_factory.from_authentication(result)

    for target, operation in (
        (SecurityObjectIdentity("processing", "inventory.rebuild"), SecurityOperation.EXECUTE),
        (SecurityObjectIdentity("report", "inventory.balance"), SecurityOperation.READ),
        (SecurityObjectIdentity("system", "security"), SecurityOperation.ADMINISTER),
    ):
        decision = security.authorization.authorize(
            AuthorizationRequest(context=context, target=target, operation=operation)
        )
        assert decision.reason is None


def test_operator_is_allowed_to_execute_inventory_rebuild() -> None:
    security = compose_standard_security(initial_passwords=_PASSWORDS)
    result = security.authentication.authenticate(
        PasswordCredentials(login="operator", password=_PASSWORDS["operator"])
    )
    context = security.context_factory.from_authentication(result)

    decision = security.authorization.authorize(
        AuthorizationRequest(
            context=context,
            target=SecurityObjectIdentity("processing", "inventory.rebuild"),
            operation=SecurityOperation.EXECUTE,
        )
    )

    assert decision.reason is None
    assert decision.outcome.value == "allow"


def test_auditor_is_denied_inventory_rebuild() -> None:
    security = compose_standard_security(initial_passwords=_PASSWORDS)
    result = security.authentication.authenticate(
        PasswordCredentials(login="auditor", password=_PASSWORDS["auditor"])
    )
    context = security.context_factory.from_authentication(result)

    decision = security.authorization.authorize(
        AuthorizationRequest(
            context=context,
            target=SecurityObjectIdentity("processing", "inventory.rebuild"),
            operation=SecurityOperation.EXECUTE,
        )
    )

    assert decision.reason is AuthorizationDenyReason.MISSING_PERMISSION


def test_independent_security_compositions_do_not_share_session_state() -> None:
    first = compose_standard_security(initial_passwords=_PASSWORDS)
    second = compose_standard_security(initial_passwords=_PASSWORDS)

    first_result = first.authentication.authenticate(
        PasswordCredentials(login="operator", password=_PASSWORDS["operator"])
    )
    second_result = second.authentication.authenticate(
        PasswordCredentials(login="operator", password=_PASSWORDS["operator"])
    )

    assert first_result.session is not None
    assert second_result.session is not None
    assert first_result.principal.identity != second_result.principal.identity

    first.authentication.sessions.invalidate(first_result.session.identity)

    assert (
        first.authentication.sessions.get(first_result.session.identity).state.value
        == "invalidated"
    )
    assert (
        second.authentication.sessions.get(second_result.session.identity).state.value == "active"
    )


def test_authentication_failure_does_not_accept_wrong_password() -> None:
    security = compose_standard_security(initial_passwords=_PASSWORDS)

    with pytest.raises(AuthenticationFailedError):
        security.authentication.authenticate(
            PasswordCredentials(login="operator", password="wrong-password")
        )


def test_initial_passwords_must_match_standard_users() -> None:
    with pytest.raises(ValueError, match="exactly the Standard user logins"):
        compose_standard_security(initial_passwords={"operator": "only-one"})
