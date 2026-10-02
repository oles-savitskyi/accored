from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime

from accore.platform.security.authentication import (
    AuthenticationResult,
    CredentialRepository,
    PasswordVerifier,
    SessionStore,
    UserRepository,
)
from accore.platform.security.credentials import PasswordCredentials
from accore.platform.security.errors import AuthenticationFailedError
from accore.platform.security.principal import Principal, PrincipalType


@dataclass(frozen=True, slots=True)
class StandardPasswordHasher:
    """Standard salted scrypt password hashing boundary."""

    n: int = 2**14
    r: int = 8
    p: int = 1
    dklen: int = 32
    salt_length: int = 16

    def hash(self, password: str) -> PasswordVerifier:
        salt = secrets.token_bytes(self.salt_length)
        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=self.n,
            r=self.r,
            p=self.p,
            dklen=self.dklen,
        )
        encoded = ":".join(
            (
                "scrypt",
                str(self.n),
                str(self.r),
                str(self.p),
                base64.urlsafe_b64encode(salt).decode("ascii"),
                base64.urlsafe_b64encode(digest).decode("ascii"),
            )
        )
        return PasswordVerifier(encoded)

    def verify(self, password: str, verifier: PasswordVerifier) -> bool:
        try:
            algorithm, n_text, r_text, p_text, salt_text, digest_text = verifier.value.split(":")
            if algorithm != "scrypt":
                return False
            salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
            expected = base64.urlsafe_b64decode(digest_text.encode("ascii"))
            actual = hashlib.scrypt(
                password.encode("utf-8"),
                salt=salt,
                n=int(n_text),
                r=int(r_text),
                p=int(p_text),
                dklen=len(expected),
            )
        except ValueError, TypeError, UnicodeError:
            return False
        return hmac.compare_digest(actual, expected)


@dataclass(frozen=True, slots=True)
class LocalAuthenticationProvider:
    users: UserRepository
    credentials: CredentialRepository
    sessions: SessionStore
    password_hasher: StandardPasswordHasher

    def authenticate(self, credentials: PasswordCredentials) -> AuthenticationResult:
        user = self.users.find_by_login(credentials.login)
        if user is None or not user.active:
            raise AuthenticationFailedError("Authentication failed")

        verifier = self.credentials.get_password_verifier(user.identity)
        if not self.password_hasher.verify(credentials.password, verifier):
            raise AuthenticationFailedError("Authentication failed")

        principal = Principal(identity=user.identity, identity_type=PrincipalType.USER)
        session = self.sessions.create(principal, datetime.now(UTC))
        return AuthenticationResult(principal=principal, session=session)
