from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from accore.platform.foundation.identity import Identifier
from accore.platform.security import (
    DefaultSecurityContextFactory,
    PasswordCredentials,
    Principal,
    PrincipalType,
    User,
)
from accore.platform.security.authentication import PasswordVerifier
from accore.platform.security.errors import AuthenticationFailedError
from standard.security import (
    InMemoryCredentialRepository,
    InMemorySessionStore,
    InMemoryUserRepository,
    LocalAuthenticationProvider,
    StandardCredential,
    StandardPasswordHasher,
)


def _user(*, active: bool = True) -> User:
    return User(
        identity=Identifier.new(),
        login="alice",
        display_name="Alice",
        email="alice@example.test",
        active=active,
        role_ids=(),
    )


def _provider(user: User, password: str = "secret") -> LocalAuthenticationProvider:
    hasher = StandardPasswordHasher()
    return LocalAuthenticationProvider(
        users=InMemoryUserRepository((user,)),
        credentials=InMemoryCredentialRepository(
            (StandardCredential(user.identity, hasher.hash(password)),)
        ),
        sessions=InMemorySessionStore(lifetime=timedelta(hours=1)),
        password_hasher=hasher,
    )


def test_password_hasher_uses_a_fresh_salt_for_each_hash() -> None:
    hasher = StandardPasswordHasher()

    first = hasher.hash("secret")
    second = hasher.hash("secret")

    assert first.value != second.value
    assert hasher.verify("secret", first)
    assert hasher.verify("secret", second)


def test_password_hasher_does_not_store_cleartext_and_verifies() -> None:
    hasher = StandardPasswordHasher()
    verifier = hasher.hash("secret")

    assert verifier.value != "secret"
    assert hasher.verify("secret", verifier)
    assert not hasher.verify("wrong", verifier)


def test_local_authentication_returns_user_principal_and_session() -> None:
    user = _user()
    provider = _provider(user)

    result = provider.authenticate(PasswordCredentials(login="alice", password="secret"))

    assert result.principal.identity == user.identity
    assert result.principal.identity_type is PrincipalType.USER
    assert result.session is not None
    assert result.session.principal_identity == user.identity


def test_wrong_password_has_single_public_failure() -> None:
    provider = _provider(_user())

    with pytest.raises(AuthenticationFailedError, match="Authentication failed"):
        provider.authenticate(PasswordCredentials(login="alice", password="wrong"))


def test_unknown_login_has_single_public_failure() -> None:
    provider = _provider(_user())

    with pytest.raises(AuthenticationFailedError, match="Authentication failed"):
        provider.authenticate(PasswordCredentials(login="unknown", password="secret"))


def test_inactive_user_has_single_public_failure() -> None:
    provider = _provider(_user(active=False))

    with pytest.raises(AuthenticationFailedError, match="Authentication failed"):
        provider.authenticate(PasswordCredentials(login="alice", password="secret"))


def test_context_factory_only_constructs_snapshot() -> None:
    user = _user()
    provider = _provider(user)
    result = provider.authenticate(PasswordCredentials(login="alice", password="secret"))

    context = DefaultSecurityContextFactory().from_authentication(
        result, request_identity=Identifier.new()
    )

    assert context.principal is result.principal
    assert context.session is result.session
    assert context.request_identity is not None


def test_session_can_be_invalidated() -> None:
    user = _user()
    provider = _provider(user)
    result = provider.authenticate(PasswordCredentials(login="alice", password="secret"))
    assert result.session is not None

    provider.sessions.invalidate(result.session.identity)

    stored = provider.sessions.get(result.session.identity)
    assert stored is not None
    assert stored.state.value == "invalidated"


def test_password_verifier_rejects_empty_value() -> None:
    with pytest.raises(ValueError, match="Password verifier value must be non-empty"):
        PasswordVerifier("")


def test_session_store_expires_active_session() -> None:
    store = InMemorySessionStore(lifetime=timedelta(hours=-1))
    user = _user()
    principal = Principal(identity=user.identity, identity_type=PrincipalType.USER)
    session = store.create(principal, datetime(2026, 1, 1, tzinfo=UTC))

    stored = store.get(session.identity)

    assert stored is not None
    assert stored.state.value == "expired"
