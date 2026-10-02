from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from accore.platform.foundation.identity import Identifier
from accore.platform.security.authentication import PasswordVerifier
from accore.platform.security.errors import SecurityConfigurationError
from accore.platform.security.principal import Principal
from accore.platform.security.session import Session, SessionState
from accore.platform.security.user import User


@dataclass(slots=True)
class InMemoryUserRepository:
    """In-memory Standard user repository for the MVP security boundary."""

    users: tuple[User, ...]
    _by_login: dict[str, User] = field(init=False, repr=False)
    _by_identity: dict[Identifier, User] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._by_login = {}
        self._by_identity = {}
        for user in self.users:
            if user.login in self._by_login:
                raise SecurityConfigurationError(f"Duplicate user login: {user.login}")
            if user.identity in self._by_identity:
                raise SecurityConfigurationError(f"Duplicate user identity: {user.identity}")
            self._by_login[user.login] = user
            self._by_identity[user.identity] = user

    def find_by_login(self, login: str) -> User | None:
        return self._by_login.get(login)

    def get(self, identity: Identifier) -> User:
        try:
            return self._by_identity[identity]
        except KeyError as exc:
            raise SecurityConfigurationError(f"Unknown user identity: {identity}") from exc


@dataclass(slots=True)
class InMemoryCredentialRepository:
    """In-memory Standard credential repository."""

    credentials: dict[Identifier, PasswordVerifier]

    def get_password_verifier(self, user_identity: Identifier) -> PasswordVerifier:
        try:
            return self.credentials[user_identity]
        except KeyError as exc:
            raise SecurityConfigurationError(
                f"Missing credentials for user identity: {user_identity}"
            ) from exc


@dataclass(slots=True)
class InMemorySessionStore:
    """In-memory Standard session store for the MVP."""

    lifetime: timedelta = timedelta(hours=8)
    _sessions: dict[Identifier, Session] = field(default_factory=dict, init=False, repr=False)

    def create(self, principal: Principal, now: datetime) -> Session:
        session = Session(
            identity=Identifier.new(),
            principal_identity=principal.identity,
            created_at=now,
            expires_at=now + self.lifetime,
            state=SessionState.ACTIVE,
        )
        self._sessions[session.identity] = session
        return session

    def get(self, identity: Identifier) -> Session | None:
        session = self._sessions.get(identity)
        if session is None:
            return None
        if session.state is SessionState.ACTIVE and session.expires_at <= datetime.now(
            session.expires_at.tzinfo
        ):
            expired = Session(
                identity=session.identity,
                principal_identity=session.principal_identity,
                created_at=session.created_at,
                expires_at=session.expires_at,
                state=SessionState.EXPIRED,
            )
            self._sessions[identity] = expired
            return expired
        return session

    def invalidate(self, identity: Identifier) -> None:
        session = self._sessions.get(identity)
        if session is None:
            return
        self._sessions[identity] = Session(
            identity=session.identity,
            principal_identity=session.principal_identity,
            created_at=session.created_at,
            expires_at=session.expires_at,
            state=SessionState.INVALIDATED,
        )
